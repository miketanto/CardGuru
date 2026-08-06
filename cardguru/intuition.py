"""Strategic intuition, derived structurally.

Two mechanisms, one framework:

1. AXIS MATCHING (the "High Noon vs Izzet Prowess" intuition): a deck's
   payoffs scale on specific EVENT AXES (casting spells, creatures entering,
   creatures dying, activating abilities...). The ontology encodes hate for
   each axis in machine-readable form (CantBeCast+NumLimitEachTurn,
   DisableTriggers+ValidMode, CantBeActivated, CantGainLife...). A good
   sideboard card is one whose restricted event IS the opposing deck's
   scaling axis. That's a join over the same Mode vocabulary on both sides.

2. ANSWER WINDOWS (the "only counters or kill-the-target beat Tinker"
   intuition): a threat's node kinds define where it can be interacted with
   at all - one-shot spells only exist on the stack; static abilities have
   no stack window; activated abilities can be shut off wholesale; fetched
   outputs are answerable even when their source is not.
"""
from __future__ import annotations

from .querydsl import CardGraph, evaluate


def _matches(rec: dict, query: dict) -> bool:
    ok, _ev = evaluate(query, CardGraph(rec))
    return ok


def _nodes(rec):
    return rec.get("nodes") or []


def _p(n):
    return n.get("params") or {}


# --------------------------------------------------------------- event axes
#
# axis -> signal (does this deck card scale on the axis?) and hate queries
# (structural searches for cards that throttle the axis).

def _sig_cast(rec):
    return any(n.get("kind") == "T"
               and _p(n).get("Mode") in ("SpellCast", "SpellCastOrCopy")
               for n in _nodes(rec))


def _sig_etb(rec):
    for n in _nodes(rec):
        p = _p(n)
        if n.get("kind") == "T" and p.get("Mode") == "ChangesZone" \
                and p.get("Destination") == "Battlefield":
            return True
    return False


def _sig_death(rec):
    for n in _nodes(rec):
        p = _p(n)
        if n.get("kind") == "T" and p.get("Mode") in ("ChangesZone", "ChangesZoneAll") \
                and p.get("Origin") in ("Battlefield", None) \
                and p.get("Destination") == "Graveyard":
            return True
    return False


def _sig_graveyard(rec):
    return any(n.get("api") in ("ChangeZone", "ChangeZoneAll")
               and _p(n).get("Origin") == "Graveyard" for n in _nodes(rec))


def _sig_activated(rec):
    types = rec.get("types") or ""
    if "Creature" not in types and "Artifact" not in types:
        return False
    return any(n.get("kind") == "A" and n.get("apiKind") == "AB"
               and "T" != str(_p(n).get("Cost", "")).strip()  # not just a tap-land
               for n in _nodes(rec))


def _sig_search(rec):
    return any(n.get("api") == "ChangeZone" and _p(n).get("Origin") == "Library"
               for n in _nodes(rec))


def _sig_lifegain(rec):
    return any(n.get("api") == "GainLife" for n in _nodes(rec)) or any(
        n.get("kind") == "T" and _p(n).get("Mode") == "LifeGained"
        for n in _nodes(rec))


def _sig_counters(rec):
    return any(n.get("api") in ("PutCounter", "Proliferate") for n in _nodes(rec))


def _sig_draw(rec):
    return any(n.get("kind") == "T" and _p(n).get("Mode") == "Drawn"
               for n in _nodes(rec))


def _sig_attack(rec):
    return any(n.get("kind") == "T" and "Attack" in str(_p(n).get("Mode", ""))
               for n in _nodes(rec))


AXES = {
    "casting_spells": {
        "describe": "scales with spells cast per turn",
        "signal": _sig_cast,
        "hate": {
            "cast_rate_caps": {"node": {"kind": "S", "mode": "CantBeCast",
                                        "params": {"NumLimitEachTurn": True}}},
            "noncreature_taxes": {"node": {"kind": "S", "mode": "RaiseCost",
                                           "params": {"ValidCard": {"regex": "Instant|Sorcery|nonCreature"}}}},
        }},
    "creatures_entering": {
        "describe": "scales with creatures/permanents entering the battlefield",
        "signal": _sig_etb,
        "hate": {
            "trigger_disablers": {"node": {"kind": "S", "mode": "DisableTriggers",
                                           "params": {"ValidMode": {"contains": "ChangesZone"}}}},
        }},
    "creatures_dying": {
        "describe": "scales with creatures dying",
        "signal": _sig_death,
        "hate": {
            # ValidCard "Card" = replaces the event for EVERYTHING (Rest in
            # Peace-style hate), not a card's own value replacement
            "death_replacement": {"node": {"kind": "R",
                                           "params": {"Event": "Moved",
                                                      "Destination": "Graveyard",
                                                      "ValidCard": "Card",
                                                      "ReplaceWith": True}}},
        }},
    "graveyard_resource": {
        "describe": "uses the graveyard as a resource",
        "signal": _sig_graveyard,
        "hate": {
            "graveyard_exile": {"node": {"api": "ChangeZoneAll",
                                         "params": {"Origin": "Graveyard",
                                                    "Destination": "Exile"}}},
            "graveyard_replacement": {"node": {"kind": "R",
                                               "params": {"Event": "Moved",
                                                          "Destination": "Graveyard",
                                                          "ValidCard": "Card",
                                                          "ReplaceWith": True}}},
        }},
    "activated_abilities": {
        "describe": "relies on activated abilities of creatures/artifacts",
        "signal": _sig_activated,
        "hate": {
            "activation_locks": {"node": {"kind": "S", "mode": "CantBeActivated",
                                          "params": {"ValidCard": {"regex": "Creature|Artifact"}}}},
        }},
    "library_search": {
        "describe": "searches the library",
        "signal": _sig_search,
        "hate": {
            "search_hate": {"node": {"params": {"AddKeyword": {"contains": "LimitSearchLibrary"}}}},
        }},
    "lifegain": {
        "describe": "gains and leverages life",
        "signal": _sig_lifegain,
        "hate": {
            "lifegain_locks": {"node": {"kind": "S", "mode": "CantGainLife"}},
        }},
    "counters": {
        "describe": "accumulates counters",
        "signal": _sig_counters,
        "hate": {
            "counter_locks": {"node": {"kind": "S", "mode": "CantPutCounter"}},
        }},
    "extra_draws": {
        "describe": "draws extra cards / punishes draws",
        "signal": _sig_draw,
        "hate": {
            "draw_caps": {"node": {"kind": "S", "mode": "CantDraw",
                                   "params": {"DrawLimit": True}}},
        }},
    "attacking": {
        "describe": "scales with attacking",
        "signal": _sig_attack,
        "hate": {
            "attack_locks": {"node": {"kind": "S", "mode": {"any": ["CantAttack", "CantAttackUnless"]}}},
            "fogs": {"node": {"api": "Fog"}},
        }},
}


def axis_profile(by_name: dict, commander_rec: dict,
                 decklist: list[tuple[str, int]]) -> list[dict]:
    """Which event axes does this deck scale on, and how hard?"""
    cards = [commander_rec] + [by_name[n] for n, _c in decklist if n in by_name]
    rows = []
    for axis, cfg in AXES.items():
        hits = sorted({r["name"] for r in cards if cfg["signal"](r)})
        if hits:
            rows.append({"axis": axis, "describe": cfg["describe"],
                         "count": len(hits), "cards": hits})
    rows.sort(key=lambda r: -r["count"])
    return rows


def hate_for_axes(idx, profile: list[dict], my_colors: set[str] | None,
                  min_signal: int = 4, top_per_class: int = 8) -> list[dict]:
    """The High Noon derivation: for each axis the deck leans on, find cards
    whose machine-readable restriction throttles exactly that axis."""
    out = []
    for row in profile:
        if row["count"] < min_signal:
            continue
        classes = {}
        for cname, query in AXES[row["axis"]]["hate"].items():
            names = []
            for hit in idx.search(query):
                rec = hit["record"]
                if my_colors is not None:
                    cc = {c for c in (rec.get("manaCost") or "") if c in "WUBRG"}
                    if not cc <= my_colors:
                        continue
                names.append(rec["name"])
            classes[cname] = {"total": len(set(names)),
                              "top": sorted(set(names))[:top_per_class]}
        out.append({"axis": row["axis"],
                    "why": f"deck has {row['count']} cards that "
                           f"{AXES[row['axis']]['describe']} "
                           f"(e.g. {', '.join(row['cards'][:4])})",
                    "hate": classes})
    return out


# ----------------------------------------------------------- answer windows

def answer_windows(rec: dict) -> dict:
    """Where can this threat be interacted with at all? Derived from node
    kinds: the Tinker intuition ('counter it or kill what it fetches - you
    can never remove the sorcery itself') falls out structurally."""
    types = rec.get("types") or ""
    is_permanent = any(t in types for t in
                       ("Creature", "Artifact", "Enchantment", "Planeswalker",
                        "Land", "Battle"))
    windows, closed = [], []

    a_sp = [n for n in _nodes(rec) if n.get("kind") == "A"
            and n.get("apiKind") == "SP"]
    a_ab = [n for n in _nodes(rec) if n.get("kind") == "A"
            and n.get("apiKind") == "AB"]
    triggers = [n for n in _nodes(rec) if n.get("kind") == "T"]
    statics = [n for n in _nodes(rec) if n.get("kind") == "S"]

    if a_sp or is_permanent:
        windows.append({"window": "stack", "answer": "counterspells",
                        "reason": "it must be cast, so it exists on the stack once"})
    if is_permanent:
        windows.append({"window": "permanent", "answer": "removal",
                        "reason": "it is a permanent on the battlefield"})
    else:
        closed.append({"window": "permanent",
                       "reason": "never a permanent - removal cannot touch "
                                 "the source after it resolves"})
    if a_ab:
        windows.append({"window": "activation", "answer":
                        "activation locks (CantBeActivated) or instant-speed "
                        "removal in response",
                        "reason": "its value flows through activated abilities"})
    if triggers:
        windows.append({"window": "trigger", "answer":
                        "stifle effects / trigger disablers (DisableTriggers)",
                        "reason": "its value flows through triggered abilities"})
    if statics and not triggers and not a_ab and is_permanent:
        windows.append({"window": "static-only", "answer":
                        "remove the source - statics never use the stack",
                        "reason": "a static ability offers no stack window"})

    # outputs: what does resolving it leave behind?
    outputs = []
    for n in _nodes(rec):
        p = _p(n)
        if p.get("Destination") == "Battlefield" and n.get("api") in \
                ("ChangeZone", "ChangeZoneAll"):
            what = p.get("ChangeType") or p.get("Defined") or "permanents"
            outputs.append(str(what))
        if n.get("api") == "Token":
            outputs.append("tokens")
    if outputs:
        windows.append({"window": "output", "answer": "answer what it leaves behind",
                        "reason": f"resolving it puts {', '.join(sorted(set(outputs))[:3])} "
                                  "onto the battlefield - those ARE removable"})
    if any(n.get("api") == "ChangeZone" and _p(n).get("Origin") == "Library"
           for n in _nodes(rec)):
        windows.append({"window": "preempt", "answer":
                        "search hate (LimitSearchLibrary / can't-search effects)",
                        "reason": "it searches the library"})
    return {"card": rec.get("name"), "windows": windows, "closed": closed}
