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
