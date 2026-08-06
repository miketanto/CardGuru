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
  etb_draw              ETB draw-N trigger; expectation = hand_count
  etb_lifegain          ETB gain-N-life trigger; expectation = life total
  dies_draw             dies draw-N trigger, killed by Murder
  etb_counters          etbCounter keyword (enters with N +1/+1); expectation = P/T
  pump_spell            Giant Growth-style pump on Grizzly Bears; expectation = P/T
  burn_player           Bolt-style damage spell at player B; expectation = life
  mill_player           mill-N spell at player B with stocked library_top

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
              "UnlessCost", "Choices", "ChoiceTitle", "KWChoice",
              "DividedAsYouChoose", "ConditionCheckSVar", "ConditionPresent",
              "ConditionCompare", "ConditionDefined", "ConditionSVarCompare"}

# a trigger is only deterministic if EVERY param is a known-benign one —
# conditions ride on params we haven't seen yet (Revolt$, CheckOnTriggeredCard$,
# Kicked$ ...), so unknown params disqualify rather than pass silently
TRIGGER_PARAM_WHITELIST = {"Mode", "ValidCard", "ValidPlayer", "Origin",
                           "Destination", "Execute", "TriggerDescription",
                           "TriggerZones", "Secondary"}


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
    if any(k not in TRIGGER_PARAM_WHITELIST for k in tp):
        return False
    for k in extra_trigger_params:
        if k in tp:
            return False
    for node in nodes:
        if node.get("kind") == "SVarCount":
            return False
        if BAD_PARAMS & set(node.get("params") or {}):
            return False
        # a chained AB$ with a Cost is a pay-to-do ("you may discard: draw") -
        # optional in the engine, so not deterministic
        if node.get("id") != trigger.get("id") and "Cost" in (node.get("params") or {}):
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


def _lit_int(v, lo=0, hi=20):
    try:
        n = int(str(v))
    except (TypeError, ValueError):
        return None
    return n if lo <= n <= hi else None


def effect_nodes(nodes, trigger):
    """Chain nodes that carry an effect api (skip the trigger and K nodes)."""
    return [n for n in nodes
            if n.get("id") != trigger.get("id") and n.get("kind") != "K"
            and n.get("api")]


def _simple_etb_effect(idx, api, extra=lambda p: True):
    """Yield (rec, cost, effect_params) for creatures whose ETB trigger chain
    is exactly one <api> node with deterministic params."""
    query = {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                "params": {"ValidCard": {"contains": "Card.Self"},
                                           "Destination": "Battlefield"}},
                       "to": {"api": api}}}
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
        eff = effect_nodes(nodes, trig)
        if len(eff) != 1 or eff[0].get("api") != api:
            continue
        if not chain_deterministic(nodes, trig) \
                or not no_interfering_abilities(rec, trig):
            continue
        p = eff[0].get("params", {})
        if p.get("Defined") not in (None, "You", "Self"):
            continue
        if not extra(p):
            continue
        yield rec, cost, p


def gen_etb_draw(idx):
    for rec, (color, mv), p in _simple_etb_effect(idx, "Draw"):
        n = _lit_int(p.get("NumCards", "1"), lo=1)
        if n is None:
            continue
        name = rec["name"]
        yield base_scenario(
            f"gen-etb-draw-{slug(name)}",
            f"{name} enters and draws {n}; hand goes from 0 (cast it) to {n}",
            "etb_draw",
            [{"card": BASIC[color], "count": mv}],
            [name],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": name},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "permanent_count", "player": "A", "card": name, "count": 1},
             {"check": "hand_count", "player": "A", "count": n}])


def gen_etb_lifegain(idx):
    for rec, (color, mv), p in _simple_etb_effect(idx, "GainLife"):
        n = _lit_int(p.get("LifeAmount"), lo=1)
        if n is None:
            continue
        name = rec["name"]
        yield base_scenario(
            f"gen-etb-lifegain-{slug(name)}",
            f"{name} enters and gains {n} life",
            "etb_lifegain",
            [{"card": BASIC[color], "count": mv}],
            [name],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": name},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "permanent_count", "player": "A", "card": name, "count": 1},
             {"check": "life", "player": "A", "value": 20 + n}])


def gen_dies_draw(idx):
    query = {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                "params": {"ValidCard": {"contains": "Card.Self"},
                                           "Origin": "Battlefield",
                                           "Destination": "Graveyard"}},
                       "to": {"api": "Draw"}}}
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
        eff = effect_nodes(nodes, trig)
        if len(eff) != 1 or eff[0].get("api") != "Draw":
            continue
        if not chain_deterministic(nodes, trig) \
                or not no_interfering_abilities(rec, trig):
            continue
        p = eff[0].get("params", {})
        if p.get("Defined") not in (None, "You", "Self"):
            continue
        n = _lit_int(p.get("NumCards", "1"), lo=1)
        if n is None:
            continue
        name = rec["name"]
        yield base_scenario(
            f"gen-dies-draw-{slug(name)}",
            f"{name} killed by Murder; its dies trigger draws {n}",
            "dies_draw",
            [{"card": name}, {"card": "Swamp", "count": 3}],
            ["Murder"],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": "Murder"},
             {"do": "target", "player": "A", "value": name},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "graveyard_count", "player": "A", "card": name, "count": 1},
             {"check": "hand_count", "player": "A", "count": n}])


def gen_etb_counters(idx):
    query = {"node": {"kind": "K", "keyword": "etbCounter"}}
    for hit in idx.search(query):
        rec = hit["record"]
        if "Creature" not in (rec.get("types") or ""):
            continue
        cost = parse_mono_cost(rec.get("manaCost") or "")
        if not cost or cost[1] > 6:
            continue
        pt = rec.get("pt") or ""
        try:
            power, tough = (int(x) for x in pt.split("/"))
        except ValueError:
            continue
        # the etbCounter keyword must be the card's only non-K ability source
        if any(n.get("kind") in ("T", "S", "R") for n in rec["nodes"]):
            continue
        kws = [n for n in rec["nodes"] if n.get("kind") == "K"
               and (n.get("raw") or "").startswith("etbCounter:P1P1:")]
        if len(kws) != 1:
            continue
        parts = (kws[0].get("raw") or "").split(":")
        n = _lit_int(parts[2] if len(parts) > 2 else None, lo=1)
        if n is None or len(parts) > 3:      # conditional etbCounter has a 4th field
            continue
        name, (color, mv) = rec["name"], cost
        yield base_scenario(
            f"gen-etb-counters-{slug(name)}",
            f"{name} enters with {n} +1/+1 counters: {power}/{tough} base -> "
            f"{power + n}/{tough + n}",
            "etb_counters",
            [{"card": BASIC[color], "count": mv}],
            [name],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": name},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "power_toughness", "player": "A", "card": name,
              "power": power + n, "toughness": tough + n}])


def _single_spell_node(rec, api):
    """The card's lone spell-mode node with the given api, or None."""
    a_nodes = [n for n in rec["nodes"] if n.get("kind") == "A"]
    if len(a_nodes) != 1:
        return None
    node = a_nodes[0]
    if node.get("api") != api or node.get("apiKind") != "SP":
        return None
    if any(n.get("kind") in ("T", "S", "R") for n in rec["nodes"]):
        return None
    p = node.get("params", {})
    if "SubAbility" in p or "Execute" in p:
        return None
    if (BAD_PARAMS - {"ValidTgts", "TgtPrompt"}) & set(p):
        return None
    if "<" in str(p.get("Cost", "")):     # additional non-mana cost (Sac<...>)
        return None
    return node


def gen_pump_spell(idx):
    query = {"node": {"kind": "A", "apiKind": "SP", "api": "Pump",
                      "params": {"ValidTgts": "Creature"}}}
    for hit in idx.search(query):
        rec = hit["record"]
        cost = parse_mono_cost(rec.get("manaCost") or "")
        if not cost or cost[1] > 4:
            continue
        node = _single_spell_node(rec, "Pump")
        if node is None:
            continue
        p = node.get("params", {})
        if p.get("ValidTgts") != "Creature" or "KW" in p:
            continue
        att = _lit_int(p.get("NumAtt", "0"), lo=0)
        dfn = _lit_int(p.get("NumDef", "0"), lo=0)
        if att is None or dfn is None or (att == 0 and dfn == 0):
            continue
        name, (color, mv) = rec["name"], cost
        yield base_scenario(
            f"gen-pump-{slug(name)}",
            f"{name} (+{att}/+{dfn}) on Grizzly Bears -> {2 + att}/{2 + dfn}",
            "pump_spell",
            [{"card": "Grizzly Bears"}, {"card": BASIC[color], "count": mv}],
            [name],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": name},
             {"do": "target", "player": "A", "value": "Grizzly Bears"},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "power_toughness", "player": "A", "card": "Grizzly Bears",
              "power": 2 + att, "toughness": 2 + dfn}])


def gen_burn_player(idx):
    query = {"node": {"kind": "A", "apiKind": "SP", "api": "DealDamage"}}
    for hit in idx.search(query):
        rec = hit["record"]
        cost = parse_mono_cost(rec.get("manaCost") or "")
        if not cost or cost[1] > 4:
            continue
        node = _single_spell_node(rec, "DealDamage")
        if node is None:
            continue
        p = node.get("params", {})
        if p.get("ValidTgts") not in ("Any", "Player"):
            continue
        n = _lit_int(p.get("NumDmg"), lo=1)
        if n is None:
            continue
        name, (color, mv) = rec["name"], cost
        yield base_scenario(
            f"gen-burn-{slug(name)}",
            f"{name} deals {n} to player B: 20 -> {20 - n}",
            "burn_player",
            [{"card": BASIC[color], "count": mv}],
            [name],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": name, "target_player": "B"},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "life", "player": "B", "value": 20 - n}])


def gen_mill_player(idx):
    query = {"node": {"kind": "A", "apiKind": "SP", "api": "Mill"}}
    for hit in idx.search(query):
        rec = hit["record"]
        cost = parse_mono_cost(rec.get("manaCost") or "")
        if not cost or cost[1] > 4:
            continue
        node = _single_spell_node(rec, "Mill")
        if node is None:
            continue
        p = node.get("params", {})
        if p.get("ValidTgts") not in ("Player", "Player.Opponent"):
            continue
        n = _lit_int(p.get("NumCards"), lo=1)
        if n is None:
            continue
        name, (color, mv) = rec["name"], cost
        scn = base_scenario(
            f"gen-mill-{slug(name)}",
            f"{name} mills {n} from B's stocked library top",
            "mill_player",
            [{"card": BASIC[color], "count": mv}],
            [name],
            [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN", "player": "A",
              "card": name, "target_player": "B"},
             {"do": "wait_stack", "turn": 1, "phase": "PRECOMBAT_MAIN"}],
            [{"check": "graveyard_count", "player": "B", "card": "Plains",
              "count": n}])
        scn["players"]["B"]["library_top"] = ["Plains"] * n
        yield scn


TEMPLATES = {
    "etb_token_doubling": gen_etb_token,
    "dies_token_doubling": gen_dies_token,
    "lifegain_counter": gen_lifegain_counter,
    "etb_draw": gen_etb_draw,
    "etb_lifegain": gen_etb_lifegain,
    "dies_draw": gen_dies_draw,
    "etb_counters": gen_etb_counters,
    "pump_spell": gen_pump_spell,
    "burn_player": gen_burn_player,
    "mill_player": gen_mill_player,
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
