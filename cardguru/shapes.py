"""Mine param-shape clusters: what a mode/api actually MEANS, not just that it exists.

The ontology lists 1,206 param keys as a flat frequency table and 138 static
modes as another. It never says which params co-occur with which mode, so a
compiler reading it knows `OnlySorcerySpeed` and `CantBeCast` are both real
tokens and nothing about the fact that together they mean "sorcery speed only".

That gap is why one mode reads as one concept when it is really several:

    CantBeCast   Caster                    63   who is prohibited
                 (bare)                    16   nobody may cast X
                 Caster+NumLimitEachTurn   14   one spell per turn
                 Caster+Condition           9   only during your turn
                 Origin                     6   can't cast from a zone
                 OnlySorcerySpeed           3   sorcery speed only

Those are six different cards to a player. Querying the mode alone conflates
them; the discriminating param is where the meaning lives.

This is DERIVED, not written. A new set's mechanics appear the next time the
dataset is rebuilt, with nobody editing a prompt.
"""
from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

from . import dataset as ds

# Prose and structural keys carry no discriminating meaning: they are either
# free text or present on essentially every node of a kind.
NOISE_PARAMS = {
    "Description", "SpellDescription", "StackDescription", "TriggerDescription",
    "AbilityDescription", "Mode", "DB", "AB", "SP", "SubAbility", "Execute",
    "References", "TgtPrompt", "AILogic", "AI", "Announce", "Defined",
}

# A param on nearly every instance of a mode splits nothing — ValidCard is on
# 130 of 139 CantBeCast nodes and tells the compiler nothing about which kind
# of prohibition it is looking at.
UBIQUITY_CUTOFF = 0.90

MAX_SHAPES = 12          # per mode/api, most common first
MAX_EXAMPLES = 3
MAX_VALUES = 6           # per value-discriminating param


def _facets(rec: dict):
    """Yield (facet_kind, facet_name, params) for every node worth clustering."""
    for n in rec.get("nodes") or []:
        p = n.get("params") or {}
        mode = p.get("Mode") or n.get("mode")
        if mode:
            yield "mode", mode, p
        api = n.get("api")
        if api:
            yield "api", api, p


def mine(dataset_path: str, min_total: int = 8) -> dict:
    """Cluster each mode/api by which discriminating params co-occur with it."""
    meta, records = ds.load(dataset_path)

    totals = Counter()                                   # (kind, name) -> nodes
    param_hits = defaultdict(Counter)                    # (kind, name) -> param -> n
    value_hits = defaultdict(lambda: defaultdict(Counter))   # -> param -> value -> n
    rows = defaultdict(list)                             # (kind, name) -> [(params, card)]
    faces = 0

    for rec in records:
        faces += 1
        name = rec.get("name")
        for kind, facet, params in _facets(rec):
            key = (kind, facet)
            totals[key] += 1
            keys = {k for k in params if k not in NOISE_PARAMS}
            for k in keys:
                param_hits[key][k] += 1
                v = str(params[k])
                if len(v) <= 40:          # skip long generated selectors
                    value_hits[key][k][v] += 1
            rows[key].append((keys, name))

    out = {"mode": {}, "api": {}}
    for key, total in totals.items():
        if total < min_total:
            continue
        kind, facet = key
        # Discriminating by PRESENCE: the param is on some nodes but not all.
        discriminating = {k for k, c in param_hits[key].items()
                          if c / total < UBIQUITY_CUTOFF}
        # Discriminating by VALUE: the param is on nearly every node, so
        # presence says nothing — but its value splits the space completely.
        # Destination is on ~all ChangeZone nodes, yet Hand / Battlefield /
        # Exile are different cards. Missing this is why a query for "like
        # Reprieve" (Origin=Stack) matched all 2,027 bounce spells.
        by_value = {}
        for k, c in param_hits[key].items():
            if c / total < UBIQUITY_CUTOFF:
                continue
            vals = value_hits[key][k]
            if len(vals) >= 2 and vals.most_common(1)[0][1] / c < UBIQUITY_CUTOFF:
                by_value[k] = [v for v, _n in vals.most_common(MAX_VALUES)]
        if not discriminating and not by_value:
            continue
        shapes = Counter()
        examples = defaultdict(list)
        for keys, card in rows[key]:
            sig = tuple(sorted(keys & discriminating))
            shapes[sig] += 1
            if card and len(examples[sig]) < MAX_EXAMPLES and card not in examples[sig]:
                examples[sig].append(card)
        # A facet with one presence-shape and no value split isn't overloaded.
        if len(shapes) < 2 and not by_value:
            continue
        out[kind][facet] = {
            "total": total,
            "shapes": [{"params": list(sig), "n": n, "examples": examples[sig]}
                       for sig, n in shapes.most_common(MAX_SHAPES)],
            # Params worth putting in a card's signature: either presence- or
            # value-discriminating.
            "key_params": sorted(discriminating | set(by_value)),
            "values": by_value,
        }

    out["_meta"] = {
        "forge_pin": meta.get("source_pin"),
        "faces": faces,
        "modes": len(out["mode"]),
        "apis": len(out["api"]),
        "note": "Derived from the dataset. Regenerate on every Forge bump; "
                "never hand-edit.",
    }
    return out


def overloaded(shapes: dict, kind: str = "mode", top: int = 20) -> list[tuple]:
    """Facets whose meaning is most split across param shapes — i.e. where
    querying the bare mode/api conflates the most distinct concepts."""
    scored = []
    for facet, info in shapes.get(kind, {}).items():
        # Count shapes that are individually meaningful (not a long tail of 1s).
        real = [s for s in info["shapes"] if s["n"] >= 3]
        if len(real) >= 2:
            scored.append((facet, len(real), info["total"]))
    return sorted(scored, key=lambda t: (-t[1], -t[2]))[:top]


def render_facet(shapes: dict, kind: str, facet: str) -> list[str]:
    info = shapes.get(kind, {}).get(facet)
    if not info:
        return [f"{facet}: not overloaded (single shape) or below the frequency floor"]
    lines = [f"{facet}  ({info['total']} nodes)"]
    for s in info["shapes"]:
        params = "+".join(s["params"]) or "(bare)"
        lines.append(f"   {s['n']:5}  {params:<44} e.g. {', '.join(s['examples'][:2])}")
    return lines


def digest(shapes: dict, kinds=("mode",), max_shapes: int = MAX_SHAPES,
           examples: int = 0) -> str:
    """A compact, prompt-sized rendering of the overloaded facets.

    The full artifact is ~94k tokens — 24x the current system prompt and a
    non-starter. Only the *overloaded* facets carry information a compiler
    lacks (a facet with one shape means exactly what its name says), and the
    param names alone do the discriminating work, so examples are optional.

    Do NOT truncate to the most common shapes. The rare ones are the most
    discriminating: OnlySorcerySpeed is 3 of 139 CantBeCast nodes and is the
    entire answer to "can't cast at instant speed". Cutting to the top 4 by
    frequency dropped it and the compiler guessed a param that doesn't exist.
    """
    lines = []
    for kind in kinds:
        for facet, _n, _total in overloaded(shapes, kind, top=10 ** 6):
            info = shapes[kind][facet]
            parts = []
            for s in info["shapes"][:max_shapes]:
                params = "+".join(s["params"]) or "(bare)"
                ex = (f" ({s['examples'][0]})"
                      if examples and s.get("examples") else "")
                parts.append(f"{params}:{s['n']}{ex}")
            lines.append(f"{facet}: " + "; ".join(parts))
    return "\n".join(lines)


def load(path: str = "data/shapes.json") -> dict | None:
    """Read the mined artifact, or None if it hasn't been built. Callers
    degrade to the old behaviour rather than failing."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def build(dataset_path: str, out_path: str, min_total: int = 8) -> dict:
    shapes = mine(dataset_path, min_total=min_total)
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(shapes, f, indent=1, ensure_ascii=False)
        f.write("\n")
    shapes["_meta"]["bytes"] = os.path.getsize(out_path)
    return shapes
