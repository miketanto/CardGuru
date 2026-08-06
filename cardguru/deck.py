"""Decklist parsing + Commander deck analysis.

`parse_decklist` accepts the common text formats:
    1 Sol Ring          |  1x Sol Ring       |  Sol Ring
    (MTGO/Arena-style "1 Sol Ring (C21) 263" set/number suffixes are dropped)
Blank lines and lines starting with // or # are ignored; a "Sideboard" header
ends mainboard parsing.

`analyze_deck` produces the hook coverage matrix: which of the commander's
synergy hooks each deck card feeds (via the hook's complement queries), where
the deck is thin, and which cards connect to nothing (candidate cuts).
"""
from __future__ import annotations

import re

from .querydsl import CardGraph, evaluate
from .recommend import HOOKS, detect_hooks

_LINE = re.compile(r"^\s*(?:(\d+)\s*x?\s+)?(.+?)\s*(?:\((\w+)\)\s*[\w-]*)?\s*$")


def parse_decklist(text: str) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("//", "#")):
            continue
        if line.lower().rstrip(":") in ("sideboard", "maybeboard", "commander"):
            break
        m = _LINE.match(line)
        if not m:
            continue
        count = int(m.group(1) or 1)
        name = m.group(2).strip()
        if name:
            out.append((name, count))
    return out


def _matches(rec: dict, query: dict) -> bool:
    ok, _evidence = evaluate(query, CardGraph(rec))
    return ok


def cross_synergy(by_name: dict, commander_rec: dict,
                  decklist: list[tuple[str, int]], max_edges: int = 400) -> dict:
    """Deck-internal synergy graph: EVERY deck card (commander included) gets
    hook detection, and each hooked card's complement queries are tested
    against the other deck cards. An edge (src)-[hook/class]->(dst) means
    dst's structure feeds src's hook — with the machine-readable WHY."""
    cards = [(commander_rec["name"], commander_rec)]
    for name, _count in decklist:
        rec = by_name.get(name)
        if rec is not None and name != commander_rec["name"]:
            cards.append((name, rec))

    edges = []
    for src_name, src_rec in cards:
        for hook in detect_hooks(src_rec):
            cfg = HOOKS[hook]
            for cname, query in cfg["complements"].items():
                for dst_name, dst_rec in cards:
                    if dst_name == src_name:
                        continue
                    if _matches(dst_rec, query):
                        edges.append({
                            "src": src_name, "hook": hook, "class": cname,
                            "dst": dst_name,
                            "why": f"{src_name} {cfg['describe']}; "
                                   f"{dst_name} matches its '{cname}' complement"})
                        if len(edges) >= max_edges:
                            break

    degree: dict[str, int] = {}
    for e in edges:
        degree[e["src"]] = degree.get(e["src"], 0) + 1
        degree[e["dst"]] = degree.get(e["dst"], 0) + 1
    core = sorted(degree.items(), key=lambda kv: -kv[1])
    isolated = [n for n, _r in cards if n not in degree]
    return {"edges": edges, "engine_core": core[:10], "isolated": isolated,
            "n_cards": len(cards), "n_edges": len(edges)}


COLOR_LETTERS = set("WUBRG")

# conventional Commander deckbuilding quotas (widely used template numbers)
ROLE_QUOTAS = {"ramp": 10, "card_draw": 10, "targeted_removal": 8, "sweepers": 3}

_ROLE_QUERIES = {
    "ramp": {"any": [
        {"node": {"kind": "A", "apiKind": "AB", "api": {"any": ["Mana", "ManaReflected"]},
                  "params": {"Cost": {"contains": "T"}}}},
        {"node": {"api": "ChangeZone",
                  "params": {"Origin": "Library", "Destination": "Battlefield",
                             "ChangeType": {"regex": "Land|Plains|Island|Swamp|Mountain|Forest"}}}}]},
    "card_draw": {"node": {"api": "Draw",
                           "params": {"NumCards": {"regex": "^[2-9X]"}}}},
    "targeted_removal": {"any": [
        {"node": {"api": "Destroy", "params": {"ValidTgts": {"regex": "Creature|Permanent"}}}},
        {"node": {"api": "ChangeZone",
                  "params": {"Origin": "Battlefield", "Destination": "Exile",
                             "ValidTgts": {"regex": "Creature|Permanent"}}}}]},
    "sweepers": {"node": {"api": {"any": ["DestroyAll", "DamageAll"]},
                          "params": {"ValidCards": {"contains": "Creature"}}}},
}


def mana_value(mana_cost: str | None) -> int | None:
    if not mana_cost or mana_cost == "no cost":
        return None
    mv = 0
    for tok in mana_cost.split():
        if tok.isdigit():
            mv += int(tok)
        elif tok == "X":
            continue
        else:
            mv += 1          # colored or hybrid symbol
    return mv


def deck_shape(by_name: dict, commander_rec: dict,
               decklist: list[tuple[str, int]]) -> dict:
    """Mana curve, color-pip demand vs mana sources, and role quotas —
    everything a deck doctor can compute without play data."""
    curve: dict[int, int] = {}
    pips: dict[str, int] = {c: 0 for c in COLOR_LETTERS}
    sources: dict[str, int] = {c: 0 for c in COLOR_LETTERS}
    roles: dict[str, list[str]] = {r: [] for r in _ROLE_QUERIES}
    n_lands = 0

    for name, count in decklist:
        rec = by_name.get(name)
        if rec is None:
            continue
        types = rec.get("types") or ""
        if "Land" in types:
            n_lands += count
            oracle = (rec.get("oracle") or "")
            for c, word in (("W", "{W}"), ("U", "{U}"), ("B", "{B}"),
                            ("R", "{R}"), ("G", "{G}")):
                if word in oracle or "any color" in oracle:
                    sources[c] += count
            continue
        mv = mana_value(rec.get("manaCost"))
        if mv is not None:
            bucket = min(mv, 7)
            curve[bucket] = curve.get(bucket, 0) + count
        for sym in (rec.get("manaCost") or "").split():
            if sym in COLOR_LETTERS:
                pips[sym] += count
        for role, query in _ROLE_QUERIES.items():
            if _matches(rec, query):
                roles[role].append(name)

    flags = []
    nonland = sum(curve.values())
    heavy = sum(v for k, v in curve.items() if k >= 5)
    if nonland and heavy / nonland > 0.30:
        flags.append(f"top-heavy curve: {heavy}/{nonland} nonland spells at MV 5+")
    for c in COLOR_LETTERS:
        if pips[c] >= 8 and sources[c] < pips[c]:
            flags.append(f"{c}: {pips[c]} pips but only {sources[c]} producing lands")
    for role, quota in ROLE_QUOTAS.items():
        if len(roles[role]) < quota:
            flags.append(f"{role}: {len(roles[role])}/{quota} "
                         f"(template suggests ~{quota})")

    return {"curve": dict(sorted(curve.items())), "lands": n_lands,
            "pips": {c: v for c, v in pips.items() if v},
            "sources": {c: v for c, v in sources.items() if v},
            "roles": {r: sorted(v) for r, v in roles.items()},
            "flags": flags}


def suggest(idx, by_name: dict, commander_rec: dict,
            decklist: list[tuple[str, int]], ci_by_name: dict,
            printings_by_name: dict | None = None, top_n: int = 15,
            shape: dict | None = None) -> dict:
    """Ranked recommendations: candidates come from the complement queries of
    every hook present in the deck (commander included); each candidate is
    scored by how many synergy edges it would add to THIS deck (provider side:
    deck hooks it feeds; consumer side: deck cards feeding its own hooks).
    With `shape` (from deck_shape), the score is adjusted for deck needs:
    +25% per deficient role the candidate fills, -25% when the candidate sits
    in an already-fat part of the curve. Ties break on reprint count (staple
    proxy) then lower mana value."""
    from .recommend import color_identity_ok

    printings_by_name = printings_by_name or {}
    commander_ci = set(ci_by_name.get(commander_rec["name"]) or "")
    deck_names = {commander_rec["name"]} | {n for n, _c in decklist}
    deck_recs = [(n, by_name[n]) for n in deck_names if n in by_name]

    # hook sources in the deck: (card, hook) pairs
    deck_hooks = [(name, h) for name, rec in deck_recs for h in detect_hooks(rec)]

    # provider side: candidates matching any deck hook's complement queries
    provider_edges: dict[str, list[str]] = {}
    for src_name, hook in deck_hooks:
        for cname, query in HOOKS[hook]["complements"].items():
            for hit in idx.search(query):
                rec = hit["record"]
                cand = rec["name"]
                if cand in deck_names:
                    continue
                if not color_identity_ok(ci_by_name.get(cand), commander_ci):
                    continue
                provider_edges.setdefault(cand, []).append(
                    f"feeds {src_name}'s {hook} ({cname})")

    # consumer side: does the deck feed the candidate's own hooks?
    scores = []
    for cand, why in provider_edges.items():
        rec = by_name.get(cand)
        if rec is None:
            continue
        consumer = 0
        for hook in detect_hooks(rec):
            for cname, query in HOOKS[hook]["complements"].items():
                consumer += sum(1 for _dn, drec in deck_recs if _matches(drec, query))
        edges = len(why) + consumer
        score = float(edges)
        adjustments = []
        if shape:
            deficient = {r for r, quota in ROLE_QUOTAS.items()
                         if len(shape["roles"].get(r, [])) < quota}
            filled = [r for r in deficient
                      if _matches(rec, _ROLE_QUERIES[r])]
            for r in filled:
                score *= 1.25
                adjustments.append(f"+25% fills {r}")
            mv = mana_value(rec.get("manaCost"))
            curve = shape.get("curve", {})
            nonland = sum(curve.values()) or 1
            if mv is not None and curve.get(min(mv, 7), 0) / nonland > 0.25:
                score *= 0.75
                adjustments.append(f"-25% curve already fat at MV {min(mv, 7)}")
        scores.append({
            "card": cand, "edges": edges, "score": round(score, 1),
            "provider_edges": len(why), "consumer_edges": consumer,
            "adjustments": adjustments,
            "printings": len(printings_by_name.get(cand) or []),
            "mv": rec.get("manaCost"),
            "why": why[:4]})
    scores.sort(key=lambda s: (-s["score"], -s["printings"], str(s["mv"] or "z")))
    return {"commander": commander_rec["name"],
            "deck_hooks": sorted({h for _n, h in deck_hooks}),
            "suggestions": scores[:top_n],
            "candidates_considered": len(scores)}


def analyze_deck(idx, commander_rec: dict, decklist: list[tuple[str, int]]) -> dict:
    by_name = {}
    for r in idx.records:
        by_name.setdefault(r.get("name"), r)

    hooks = detect_hooks(commander_rec)
    matrix: dict[str, dict] = {
        h: {"why": f"{commander_rec['name']} {HOOKS[h]['describe']}",
            "classes": {c: [] for c in HOOKS[h]["complements"]}}
        for h in hooks}
    unknown, unconnected = [], []

    for name, _count in decklist:
        rec = by_name.get(name)
        if rec is None:
            unknown.append(name)
            continue
        connected = False
        for h in hooks:
            for cname, query in HOOKS[h]["complements"].items():
                if _matches(rec, query):
                    matrix[h]["classes"][cname].append(name)
                    connected = True
        if not connected:
            unconnected.append(name)

    coverage = {}
    for h in hooks:
        classes = matrix[h]["classes"]
        n = len({card for cards in classes.values() for card in cards})
        coverage[h] = {"cards_feeding_hook": n,
                       "thin": n < 5,
                       "classes": {c: sorted(set(v)) for c, v in classes.items()}}
    return {
        "commander": commander_rec["name"],
        "hooks": hooks,
        "matrix": {h: {"why": matrix[h]["why"], **coverage[h]} for h in hooks},
        "unconnected": unconnected,
        "unknown_cards": unknown,
        "deck_size": sum(c for _n, c in decklist),
    }
