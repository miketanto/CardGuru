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
