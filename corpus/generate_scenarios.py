#!/usr/bin/env python3
"""Ontology-driven scenario generator (Phase 2a item 3).

Template implemented: **ETB-token trigger under a token-doubling replacement**
(Doubling Season). Candidate cards are found by a mechanical-search query over
the ability graph, then *prefiltered by the same graph* to maximize
deterministic execution under strict-choose mode:

  - trigger chain reaches api=Token with a literal TokenAmount (default 1)
  - no targeting params (ValidTgts/TgtPrompt) anywhere in the chain
  - no Optional/OptionalDecider (may-triggers need scripted choices)
  - no Count$ nodes in the chain (dynamic amounts)
  - creature, mono-colored simple mana cost, castable off basics
  - implemented in XMage (xmage_cards.txt) and not on an 'unfinished' list

Each scenario: player A has basics + Doubling Season, casts the creature,
and we expect battlefield = lands + Season + creature + 2x tokens.
Expectation misses and errors are data, not failures — the run report
measures the clean-execution rate (the choice-explosion number from
plan/uncertainties.md #4).

Usage:
  python corpus/generate_scenarios.py [N] [outdir]     # default 12 corpus/generated
  python -m cardguru adjudicate corpus/generated/*.json
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.index import SearchIndex  # noqa: E402
from cardguru.querydsl import CardGraph, evaluate  # noqa: E402

DATASET = os.environ.get("CARDGURU_DATASET", "data/dataset.jsonl.gz")
XMAGE_CARDS = os.environ.get("CARDGURU_XMAGE_CARDS", "/home/user/mse/data/xmage_cards.txt")
UNFINISHED = "research/data/xmage_unfinished.json"

BASIC = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}

ETB_TOKEN_QUERY = {
    "chain": {
        "from": {"kind": "T", "mode": "ChangesZone",
                 "params": {"ValidCard": {"contains": "Card.Self"},
                            "Destination": "Battlefield"}},
        "to": {"api": "Token"},
    }
}

BAD_PARAMS = {"ValidTgts", "TgtPrompt", "Optional", "OptionalDecider", "TargetMin",
              "UnlessCost", "Choices", "ChoiceTitle"}


def parse_mono_cost(mana_cost: str):
    """'2 G G' -> ('G', 4); None if not simple mono-colored."""
    if not mana_cost or mana_cost == "no cost":
        return None
    color, total = None, 0
    for tok in mana_cost.split():
        if tok.isdigit():
            total += int(tok)
        elif tok in BASIC:
            if color and tok != color:
                return None
            color = tok
            total += 1
        else:
            return None   # X, hybrid, phyrexian, snow...
    return (color, total) if color else None


def chain_is_simple(rec: dict) -> bool:
    """True if every node reachable from the ETB trigger is deterministic."""
    graph = CardGraph(rec)
    for n in rec["nodes"]:
        if n.get("kind") != "T" or n.get("params", {}).get("Mode") != "ChangesZone":
            continue
        tp = n.get("params", {})
        # trigger must be an unconditional ETB-from-anywhere on the card itself
        # (e.g. Archfiend's Vessel triggers only from the graveyard — casting
        # from hand makes no token, so the naive expectation would be wrong)
        if tp.get("Origin") not in (None, "Any"):
            return False
        if tp.get("ValidCard") != "Card.Self":
            return False
        if "CheckSVar" in tp or "Condition" in tp or "IsPresent" in tp:
            return False
        ids = {n["id"]}
        for dst, _path in graph.reachable(n["id"], None):
            ids.add(dst)
        for nid in ids:
            node = graph.by_id[nid]
            if node.get("kind") == "SVarCount":
                return False
            params = node.get("params") or {}
            if BAD_PARAMS & set(params):
                return False
            if node.get("api") == "Token":
                if params.get("TokenAmount", "1") != "1":
                    return False
                if params.get("TokenOwner", "You") != "You":
                    return False
    return True


def implemented_cards() -> set[str]:
    names = set()
    with open(XMAGE_CARDS, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                names.add(parts[1])
    return names


def unfinished_cards() -> set[str]:
    with open(UNFINISHED, encoding="utf-8") as f:
        data = json.load(f)
    out = set()
    for cards in data["sets"].values():
        out.update(cards)
    return out


def make_scenario(name: str, color: str, cost: int) -> dict:
    land = BASIC[color]
    # battlefield = lands + Doubling Season + creature + 2 tokens
    expected = cost + 1 + 1 + 2
    return {
        "id": "gen-etb-token-doubling-" + name.lower().replace(" ", "-")
              .replace(",", "").replace("'", ""),
        "description": f"{name} ETB token trigger under Doubling Season "
                       "(expect doubled token)",
        "template": "etb_token_doubling",
        "players": {
            "A": {"life": 20,
                  "battlefield": [{"card": land, "count": cost},
                                  {"card": "Doubling Season"}],
                  "hand": [name]},
            "B": {"life": 20},
        },
        "actions": [
            {"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN",
             "player": "A", "card": name},
            {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"},
        ],
        "stop": {"turn": 1, "phase": "END_TURN"},
        "expect": [
            {"check": "permanent_count", "player": "A", "card": name, "count": 1},
            {"check": "battlefield_count", "player": "A", "count": expected},
        ],
    }


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    outdir = sys.argv[2] if len(sys.argv) > 2 else "corpus/generated"
    os.makedirs(outdir, exist_ok=True)

    idx = SearchIndex.load(DATASET)
    impl = implemented_cards()
    unfin = unfinished_cards()

    stats = {"query_hits": 0, "creature": 0, "mono_castable": 0,
             "simple_chain": 0, "xmage_implemented": 0, "generated": 0}
    chosen = []
    for hit in idx.search(ETB_TOKEN_QUERY):
        rec = hit["record"]
        stats["query_hits"] += 1
        name = rec["name"]
        if "Creature" not in (rec.get("types") or ""):
            continue
        stats["creature"] += 1
        cost = parse_mono_cost(rec.get("manaCost") or "")
        if not cost or cost[1] > 6:
            continue
        stats["mono_castable"] += 1
        if not chain_is_simple(rec):
            continue
        stats["simple_chain"] += 1
        if name not in impl or name in unfin:
            continue
        stats["xmage_implemented"] += 1
        chosen.append((name, cost))

    chosen.sort()
    for name, (color, cost) in chosen[:n]:
        scn = make_scenario(name, color, cost)
        with open(os.path.join(outdir, scn["id"] + ".json"), "w",
                  encoding="utf-8") as f:
            json.dump(scn, f, indent=1)
        stats["generated"] += 1

    with open(os.path.join(outdir, "_funnel.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    print(json.dumps(stats, indent=1))
    print("candidates:", [c[0] for c in chosen[:n]])


if __name__ == "__main__":
    main()
