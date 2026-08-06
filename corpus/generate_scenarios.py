#!/usr/bin/env python3
"""Ontology-driven scenario generator (Phase 2a item 3).

Templates find candidate cards by mechanical-search queries over the ability
graph, then prefilter BY THE GRAPH for deterministic execution under
strict-choose mode (no targets, no may-triggers, no Count$ amounts,
unconditional triggers), and compute expectations from graph params.

Templates:
  etb_token_doubling    ETB-token trigger under Doubling Season
  dies_token_doubling   dies-token trigger, killed by Murder, under Doubling Season
  lifegain_counter      lifegain->+1/+1-counter trigger + Angel's Mercy

Expectation misses and errors are data, not failures — the run report
measures the clean-execution rate.

Usage:
  python corpus/generate_scenarios.py [N-per-template] [outdir] [template ...]
  python -m cardguru adjudicate corpus/generated/*.json
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.index import SearchIndex  # noqa: E402
from cardguru.querydsl import CardGraph  # noqa: E402

DATASET = os.environ.get("CARDGURU_DATASET", "data/dataset.jsonl.gz")
XMAGE_CARDS = os.environ.get("CARDGURU_XMAGE_CARDS", "/home/user/mse/data/xmage_cards.txt")
UNFINISHED = "research/data/xmage_unfinished.json"

BASIC = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}
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
            return None
    return (color, total) if color else None


def find_trigger(rec, mode, req_params):
    """The trigger node matching mode + exact params, or None."""
    for n in rec["nodes"]:
        if n.get("kind") != "T":
            continue
        p = n.get("params", {})
        if p.get("Mode") != mode:
            continue
        if all(p.get(k) == v for k, v in req_params.items()):
            return n
    return None


def chain_nodes(rec, trigger):
    graph = CardGraph(rec)
    ids = {trigger["id"]}
    for dst, _path in graph.reachable(trigger["id"], None):
        ids.add(dst)
    return [graph.by_id[i] for i in ids]


def chain_deterministic(nodes, trigger, extra_trigger_params=()):
    tp = trigger.get("params", {})
    if any(k in tp for k in ("CheckSVar", "Condition", "IsPresent")):
        return False
    for k in extra_trigger_params:
        if k in tp:
            return False
    for node in nodes:
        if node.get("kind") == "SVarCount":
            return False
        if BAD_PARAMS & set(node.get("params") or {}):
            return False
    return True


def no_interfering_abilities(rec, trigger):
    """The template trigger must be the card's ONLY trigger/static/replacement.
    (Discovered via Dr. Beverly Crusher: a second, static ability doubled her
    own lifegain trigger — two stack entries needing an ordering choice, and a
    +2 instead of +1 outcome. Activated abilities are fine; nobody activates
    them in these scenarios. Keywords are allowed.)"""
    for n in rec["nodes"]:
        if n is trigger or n.get("id") == trigger.get("id"):
            continue
        if n.get("kind") in ("T", "S", "R"):
            return False
    return True


def single_token_chain(nodes):
    """Exactly-one-token effect chains (TokenAmount literal 1, owner You)."""
    tokens = [n for n in nodes if n.get("api") == "Token"]
    if len(tokens) != 1:
        return False
    p = tokens[0].get("params", {})
    return p.get("TokenAmount", "1") == "1" and p.get("TokenOwner", "You") == "You"


def base_scenario(scn_id, description, template, battlefield, hand, actions, expect):
    return {
        "id": scn_id, "description": description, "template": template,
        "players": {"A": {"life": 20, "battlefield": battlefield, "hand": hand},
                    "B": {"life": 20}},
        "actions": actions,
        "stop": {"turn": 1, "phase": "END_TURN"},
        "expect": expect,
    }


def slug(name):
    return name.lower().replace(" ", "-").replace(",", "").replace("'", "")


# ------------------------------------------------------------------ templates

def gen_etb_token(idx):
    query = {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                "params": {"ValidCard": {"contains": "Card.Self"},
                                           "Destination": "Battlefield"}},
                       "to": {"api": "Token"}}}
    for hit in idx.search(query):
        rec = hit["record"]
        if "Creature" not in (rec.get("types") or ""):
            continue
        cost = parse_mono_cost(rec.get("manaCost") or "")
        if not cost or cost[1] > 6:
            continue
        trig = find_trigger(rec, "ChangesZone",
                            {"ValidCard": "Card.Self", "Destination": "Battlefield"})
        if not trig or trig.get("params", {}).get("Origin") not in (None, "Any"):
            continue
        nodes = chain_nodes(rec, trig)
        if not chain_deterministic(nodes, trig) or not single_token_chain(nodes) \
                or not no_interfering_abilities(rec, trig):
            continue
        name, (color, mv) = rec["name"], cost
        yield base_scenario(
            f"gen-etb-token-doubling-{slug(name)}",
            f"{name} ETB token trigger under Doubling Season",
            "etb_token_doubling",
            [{"card": BASIC[color], "count": mv}, {"card": "Doubling Season"}],
            [name],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": name},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "permanent_count", "player": "A", "card": name, "count": 1},
             {"check": "battlefield_count", "player": "A", "count": mv + 1 + 1 + 2}])


def gen_dies_token(idx):
    query = {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                "params": {"ValidCard": {"contains": "Card.Self"},
                                           "Origin": "Battlefield",
                                           "Destination": "Graveyard"}},
                       "to": {"api": "Token"}}}
    for hit in idx.search(query):
        rec = hit["record"]
        if "Creature" not in (rec.get("types") or ""):
            continue
        trig = find_trigger(rec, "ChangesZone",
                            {"ValidCard": "Card.Self", "Origin": "Battlefield",
                             "Destination": "Graveyard"})
        if not trig:
            continue
        nodes = chain_nodes(rec, trig)
        if not chain_deterministic(nodes, trig) or not single_token_chain(nodes) \
                or not no_interfering_abilities(rec, trig):
            continue
        name = rec["name"]
        yield base_scenario(
            f"gen-dies-token-doubling-{slug(name)}",
            f"{name} dies-token trigger (killed by Murder) under Doubling Season",
            "dies_token_doubling",
            [{"card": name}, {"card": "Doubling Season"}, {"card": "Swamp", "count": 3}],
            ["Murder"],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": "Murder"},
             {"do": "target", "player": "A", "value": name},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            # swamps + Season + 2 tokens (creature and Murder in graveyard)
            [{"check": "graveyard_count", "player": "A", "card": name, "count": 1},
             {"check": "battlefield_count", "player": "A", "count": 3 + 1 + 2}])


def gen_lifegain_counter(idx):
    query = {"chain": {"from": {"kind": "T", "mode": "LifeGained"},
                       "to": {"api": "PutCounter",
                              "params": {"CounterType": "P1P1"}}}}
    for hit in idx.search(query):
        rec = hit["record"]
        if "Creature" not in (rec.get("types") or ""):
            continue
        pt = rec.get("pt") or ""
        if "/" not in pt:
            continue
        try:
            power, tough = (int(x) for x in pt.split("/"))
        except ValueError:
            continue
        trig = find_trigger(rec, "LifeGained", {"ValidPlayer": "You"})
        if not trig:
            continue
        nodes = chain_nodes(rec, trig)
        if not chain_deterministic(nodes, trig) \
                or not no_interfering_abilities(rec, trig):
            continue
        counters = [n for n in nodes if n.get("api") == "PutCounter"]
        if len(counters) != 1:
            continue
        cp = counters[0].get("params", {})
        if cp.get("CounterType") != "P1P1" or cp.get("CounterNum", "1") != "1":
            continue
        if cp.get("Defined", "Self") != "Self":
            continue
        name = rec["name"]
        yield base_scenario(
            f"gen-lifegain-counter-{slug(name)}",
            f"{name} lifegain->counter trigger with Angel's Mercy (+7 life)",
            "lifegain_counter",
            [{"card": name}, {"card": "Plains", "count": 4}],
            ["Angel's Mercy"],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": "Angel's Mercy"},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "life", "player": "A", "value": 27},
             {"check": "power_toughness", "player": "A", "card": name,
              "power": power + 1, "toughness": tough + 1}])


TEMPLATES = {
    "etb_token_doubling": gen_etb_token,
    "dies_token_doubling": gen_dies_token,
    "lifegain_counter": gen_lifegain_counter,
}


# ------------------------------------------------------------------ main

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


def scenario_cards(scn) -> set[str]:
    names = set()
    for cfg in scn["players"].values():
        for b in cfg.get("battlefield", []):
            names.add(b["card"])
        names.update(cfg.get("hand", []))
    return names


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    outdir = sys.argv[2] if len(sys.argv) > 2 else "corpus/generated"
    wanted = sys.argv[3:] or list(TEMPLATES)
    os.makedirs(outdir, exist_ok=True)

    idx = SearchIndex.load(DATASET)
    impl = implemented_cards()
    unfin = unfinished_cards()
    basics = set(BASIC.values())

    funnel = {}
    for tname in wanted:
        candidates, kept = 0, 0
        for scn in sorted(TEMPLATES[tname](idx), key=lambda s: s["id"]):
            candidates += 1
            if kept >= n:
                continue
            cards = scenario_cards(scn) - basics
            if any(c not in impl or c in unfin for c in cards):
                continue
            with open(os.path.join(outdir, scn["id"] + ".json"), "w",
                      encoding="utf-8") as f:
                json.dump(scn, f, indent=1)
            kept += 1
        funnel[tname] = {"deterministic_candidates": candidates, "generated": kept}

    with open(os.path.join(outdir, "_funnel.json"), "w", encoding="utf-8") as f:
        json.dump(funnel, f, indent=1)
    print(json.dumps(funnel, indent=1))


if __name__ == "__main__":
    main()
