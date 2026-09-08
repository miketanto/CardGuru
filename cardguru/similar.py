"""Card-anchored search: "cards like Reprieve".

This is a different question type from everything else here, and the compiler
could not answer it because nothing in the pipeline ever *looks at the card*.
Asked for "cards like Reprieve" it produced a query from the model's memory of
the name — kept `Destination: Hand`, dropped `Origin: Stack`, and returned all
2,027 bounce spells in the game instead of the 32 that bounce a spell off the
stack. Reprieve is a soft counter; the answer was a pile of Unsummons.

The fix is to resolve the named card first and derive its signature from its
actual graph. Which params belong in that signature comes from the mined
shapes (cardguru.shapes): the VALUE-discriminating ones. Those are exactly the
params that are present on nearly every node of a facet — so presence says
nothing — while their value splits the space completely. `Destination` is on
almost every ChangeZone node; Hand vs Battlefield vs Exile is the whole
difference between a bounce spell, a reanimation spell, and removal.
"""
from __future__ import annotations

import difflib
import json

from .shapes import load as load_shapes

# A signature of everything is a signature of nothing: past a handful of
# params the query matches only the card itself.
MAX_PARAMS_PER_NODE = 3
MAX_NODES = 2

# Selectivity is the right ranking signal but fails at BOTH extremes.
# Too broad: the generic "when this enters" trigger is on 4,471 cards and says
# nothing. Too narrow: Aven Interrupter's rarest spec is `Attributes: Plotted`
# (5 cards) — a rider, not an identity — and pairing it with anything yields
# zero. So prefer specs inside a usefulness band, most selective first.
BAND_MIN = 10
BAND_MAX_FRACTION = 0.10
# Pure bookkeeping: present on thousands of cards, never what a card "is".
BOOKKEEPING_APIS = {"Cleanup", "StoreSVar", "Branch", "Repeat", "RepeatEach"}


def _facet(node: dict) -> tuple[str, str] | None:
    p = node.get("params") or {}
    if node.get("api"):
        return "api", node["api"]
    mode = p.get("Mode") or node.get("mode")
    return ("mode", mode) if mode else None


def _node_signature(node: dict, shapes: dict) -> dict | None:
    """The distinguishing part of one node: its facet plus the params whose
    VALUE carries meaning."""
    facet = _facet(node)
    if not facet:
        return None
    kind, name = facet
    info = (shapes.get(kind, {}) or {}).get(name) or {}
    value_params = info.get("values") or {}
    params = node.get("params") or {}

    keep = {}
    for k in params:
        if k not in value_params:
            continue
        v = str(params[k])
        # Only keep a value the miner actually saw as a recurring one; a
        # bespoke selector string would match this card and nothing else.
        if v in value_params[k]:
            keep[k] = v
        if len(keep) >= MAX_PARAMS_PER_NODE:
            break

    spec = {kind if kind == "api" else "mode": name}
    if keep:
        spec["params"] = keep
    return spec


def signature(record: dict, shapes: dict, index=None) -> dict | None:
    """A DSL query capturing what makes this card what it is.

    Nodes are ranked by SELECTIVITY — how few cards the spec matches — not by
    how many params survived. Ranking by param count is backwards: the generic
    "when this enters the battlefield" trigger carries three value-matching
    params (Origin=Any, Destination=Battlefield, ValidCard=Card.Self) and sits
    on 4,471 cards, while Spellstutter Sprite's actual identity is a param-less
    `api: Counter` on 514. Param count rewarded the most common values in the
    game; selectivity rewards information.

    Without an index we fall back to param count, which is weak but ordered.
    """
    specs = [s for s in (_node_signature(n, shapes)
                         for n in record.get("nodes") or []) if s]
    if not specs:
        return None

    # De-duplicate: a card often repeats the same shape across sub-abilities.
    seen, unique = set(), []
    for spec in specs:
        key = json.dumps(spec, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(spec)
    specs = unique

    specs = [s for s in specs if s.get("api") not in BOOKKEEPING_APIS]
    if not specs:
        return None
    if index is None:
        specs.sort(key=lambda s: -len(s.get("params") or {}))
        specs = specs[:MAX_NODES]
        return ({"node": specs[0]} if len(specs) == 1
                else {"all": [{"node": s} for s in specs]})

    corpus = len(index.records)
    band_max = max(BAND_MIN + 1, int(corpus * BAND_MAX_FRACTION))

    def count(q):
        try:
            return sum(1 for _ in index.search(q))
        except Exception:
            return 10 ** 9

    scored = [(count({"node": s}), s) for s in specs]
    # In-band first (ascending: most selective wins), then everything else.
    in_band = sorted((c, s) for c, s in scored if BAND_MIN <= c <= band_max)
    out_band = sorted((c, s) for c, s in scored if not (BAND_MIN <= c <= band_max))
    ordered = [s for _c, s in in_band] + [s for _c, s in out_band]

    # Greedy: add a spec only if the combination still matches something other
    # than the card itself. Guarantees a non-empty, progressively tighter query.
    chosen, self_name = [], record.get("name")
    for spec in ordered:
        candidate = chosen + [spec]
        q = ({"node": candidate[0]} if len(candidate) == 1
             else {"all": [{"node": x} for x in candidate]})
        others = sum(1 for h in index.search(q)
                     if h["record"].get("name") != self_name)
        if others:
            chosen = candidate
        if len(chosen) >= MAX_NODES:
            break
    if not chosen:
        chosen = ordered[:1]
    return ({"node": chosen[0]} if len(chosen) == 1
            else {"all": [{"node": s} for s in chosen]})


# Below this similarity a "close match" is a guess, not a correction.
FUZZY_CUTOFF = 0.82


def find(index, name: str, fuzzy: bool = True) -> tuple[dict | None, bool]:
    """Resolve a card name. Returns (record, was_exact).

    Fuzzy matching exists because the failure mode without it is the worst
    one available: "cards like aven interruptor" (the card is Interrupter)
    found nothing, fell through to the NL compiler, and confidently answered
    a different question with 756 cards. A near-miss name must correct itself
    and say so, not silently become another query.
    """
    target = name.strip().lower()
    by_lower = {}
    for rec in index.records:
        nm = (rec.get("name") or "").lower()
        if nm and nm not in by_lower:
            by_lower[nm] = rec
    if target in by_lower:
        return by_lower[target], True
    if not fuzzy:
        return None, False
    close = difflib.get_close_matches(target, by_lower, n=1, cutoff=FUZZY_CUTOFF)
    return (by_lower[close[0]], False) if close else (None, False)


def abilities(index, record: dict, shapes: dict) -> list[dict]:
    """The card's candidate signatures, with how many cards each reaches.

    A multi-ability card is genuinely ambiguous: Aven Interrupter both exiles
    a spell off the stack AND taxes opponents, and "cards like it" could
    reasonably mean either. Rather than pick silently, expose the options.
    """
    specs, seen = [], set()
    for node in record.get("nodes") or []:
        spec = _node_signature(node, shapes)
        if not spec or spec.get("api") in BOOKKEEPING_APIS:
            continue
        key = json.dumps(spec, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        n = sum(1 for h in index.search({"node": spec})
                if h["record"].get("name") != record.get("name"))
        specs.append({"spec": spec, "reaches": n})
    return sorted(specs, key=lambda r: r["reaches"])


def similar(index, name: str, shapes_path: str = None, limit: int = None,
            ability: int = None):
    """Return (record, query, hits). Raises SystemExit with a usable message
    rather than an empty result when the inputs aren't there."""
    shapes = load_shapes(shapes_path or "data/shapes.json")
    if not shapes:
        raise SystemExit("no data/shapes.json — run `python -m cardguru shapes` "
                         "first (similarity is derived from the mined shapes)")
    rec, exact = find(index, name)
    if rec is None:
        raise SystemExit(f"no card named {name!r} in the dataset")
    opts = abilities(index, rec, shapes)
    if ability is not None:
        if not 1 <= ability <= len(opts):
            raise SystemExit(f"{rec['name']} has {len(opts)} abilities to match "
                             f"on; --ability must be 1..{len(opts)}")
        query = {"node": opts[ability - 1]["spec"]}
    else:
        query = signature(rec, shapes, index=index)
    if query is None:
        raise SystemExit(f"{rec['name']} has no structured abilities to match on")
    # "Cards like X" never means X itself.
    hits = [h["record"] for h in index.search(query)
            if h["record"].get("name") != rec.get("name")]
    return rec, query, (hits[:limit] if limit else hits), exact, opts
