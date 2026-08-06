#!/usr/bin/env python3
"""Build the Forge-ontology -> Comprehensive Rules mapping table.

Three vocabularies, three strategies:
- Keywords (K:): auto-join against CR 702 ("Keyword Abilities") and 701
  ("Keyword Actions") subsection titles by normalized name. This covers the
  bulk by instance count; Forge-internal pseudo-keywords stay unmapped.
- Effect APIs (SP$/AB$/DB$): auto-join against 701 titles where the name
  matches (Destroy, Discard, Mill, Scry...), plus a hand table for the top
  APIs whose names are Forge-internal (ChangeZone, Pump, Token...).
- Trigger modes / replacement events: hand table for the top entries.

Coverage is reported *instance-weighted* (by ontology frequency counts):
mapping the top-50 tokens covers most instances; the long tail is
explicitly marked unmapped rather than guessed.

Usage: python rules/map_ontology.py  ->  research/data/cr_mapping.json
"""
from __future__ import annotations

import json
import re

ONTOLOGY = "research/data/ontology.json"
CR = "research/data/cr_rules.json"
OUT = "research/data/cr_mapping.json"

# Forge-internal API name -> CR rule (the real intellectual work, top-frequency-first)
API_HAND = {
    "ChangeZone": "400",        # Zones (movement between zones)
    "Pump": "613.4",            # power/toughness-changing continuous effects (layer 7)
    "Draw": "121",              # Drawing a Card
    "Token": "111",             # Tokens
    "PutCounter": "122",        # Counters
    "DealDamage": "120",        # Damage
    "Mana": "106",              # Mana
    "Effect": "611",            # one-shot creating a continuous effect
    "GainLife": "119",        # gaining life
    "LoseLife": "119",        # losing life
    "Tap": "701.26",            # Tap and Untap (hand-checked against parsed titles)
    "Untap": "701.26",
    "PumpAll": "613.4",
    "ChangeZoneAll": "400",
    "Draw": "121",
    "SetState": "701",          # transform/flip etc. (approximate)
    "Dig": "401",               # Library
    "DigUntil": "401",
    "Play": "601",              # Casting Spells
    "Cleanup": None,            # Forge bookkeeping, no CR concept
    "Animate": "613.3",         # type-changing continuous effects (layer 4)
    "AnimateAll": "613.3",
    "GainControl": "613.2",     # control-changing effects (layer 2)
    "Repeat": None,             # Forge control flow
    "RepeatEach": None,
    "Charm": "601.2b",          # modal spells (choosing modes)
    "ChooseCard": None,
    "CopyPermanent": "707",     # Copying Objects
    "CopySpellAbility": "707.10",
    "ReplaceToken": "614",      # replacement effects
    "ReplaceCounter": "614",
    "MakeCard": "111",          # conjure — digital; nearest is tokens/cards
    "ManaReflected": "106",
    "AddTurn": "500.7",         # extra turns
    "RollDice": "706",          # dice rolling (hand-check number)
    "Vote": "701",
    "Branch": None,             # Forge control flow
    "ImmediateTrigger": "603",  # triggered abilities
    "DelayedTrigger": "603.7",
    "Debuff": "613.4",
    "FlipACoin": "705",         # coin flipping (hand-check)
    "Venture": "701.49",
}

TRIGGER_HAND = {
    "ChangesZone": "603.6",       # zone-change triggers (incl. ETB/dies)
    "ChangesZoneAll": "603.6",
    "Phase": "603.1",             # turn-based triggers (beginning of phase/step)
    "Attacks": "508",             # Declare Attackers Step
    "AttackersDeclared": "508",
    "AttackerBlocked": "509",
    "Blocks": "509",              # Declare Blockers Step
    "SpellCast": "601",           # Casting Spells
    "SpellCastOrCopy": "601",
    "DamageDone": "120",
    "DamageDoneOnce": "120",
    "DamageAll": "120",
    "LifeGained": "119",
    "LifeLost": "119",
    "Drawn": "121",
    "Discarded": "701.9",
    "Sacrificed": "701.21",
    "CounterAdded": "122",
    "CounterRemoved": "122",
    "Taps": "701.26",
    "Untaps": "701.26",
    "TurnFaceUp": "708",          # face-down spells and permanents
    "BecomesTarget": "115",       # targets (hand-check number)
    "Destroyed": "701.8",
    "Shuffled": "701.24",
    "SearchedLibrary": "701.23",
    "TokenCreated": "111",
    "Transformed": "701.27",
    "PlanarDice": "901",          # planechase
}

REPLACEMENT_HAND = {
    "Moved": "614",
    "DamageDone": "614",          # prevention effects overlap; hand-check
    "Untap": "614",
    "Counter": "614",
    "Draw": "614.11",
    "CreateToken": "614",
    "AddCounter": "614",
    "GainLife": "614",
    "BeginPhase": "614",
    "GameLoss": "104",
    "ProduceMana": "106.7",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def main():
    onto = json.load(open(ONTOLOGY, encoding="utf-8"))
    cr = json.load(open(CR, encoding="utf-8"))
    rules = cr["rules"]

    # title index over 701.x / 702.x subsections
    titles = {}
    for num, r in rules.items():
        if "title" in r and re.match(r"^70[12]\.\d+$", num):
            titles[norm(r["title"])] = num

    def rule_title(num):
        r = rules.get(num) or {}
        return r.get("title") or (r.get("text", "")[:60])

    mapping = {"keywords": {}, "apis": {}, "trigger_modes": {},
               "replacement_events": {}}
    cov = {}

    # ---- keywords: auto-join on 702/701 titles
    mapped_inst = total_inst = 0
    for kw, count in onto["keywords"].items():
        total_inst += count
        num = titles.get(norm(kw))
        if num:
            mapping["keywords"][kw] = {"rule": num, "title": rule_title(num),
                                       "method": "auto"}
            mapped_inst += count
    cov["keywords"] = {"mapped_tokens": len(mapping["keywords"]),
                       "total_tokens": len(onto["keywords"]),
                       "instance_pct": round(100 * mapped_inst / total_inst, 1)}

    # ---- APIs: hand table + auto-join on 701 titles
    mapped_inst = total_inst = 0
    for api, count in onto["api"].items():
        total_inst += count
        num = titles.get(norm(api)) or API_HAND.get(api)
        if num:
            mapping["apis"][api] = {
                "rule": num, "title": rule_title(num),
                "method": "hand" if api in API_HAND else "auto"}
            mapped_inst += count
        elif api in API_HAND:   # explicit None: Forge-internal bookkeeping
            mapping["apis"][api] = {"rule": None, "title": "engine bookkeeping",
                                    "method": "hand"}
            mapped_inst += count
    cov["apis"] = {"mapped_tokens": len(mapping["apis"]),
                   "total_tokens": len(onto["api"]),
                   "instance_pct": round(100 * mapped_inst / total_inst, 1)}

    # ---- trigger modes / replacement events: hand tables
    for key, table, src in (("trigger_modes", TRIGGER_HAND, onto["trigger_modes"]),
                            ("replacement_events", REPLACEMENT_HAND,
                             onto["replacement_events"])):
        mapped_inst = total_inst = 0
        for tok, count in src.items():
            total_inst += count
            if tok in table:
                num = table[tok]
                mapping[key][tok] = {"rule": num, "title": rule_title(num),
                                     "method": "hand"}
                mapped_inst += count
        cov[key] = {"mapped_tokens": len(mapping[key]),
                    "total_tokens": len(src),
                    "instance_pct": round(100 * mapped_inst / total_inst, 1)}

    out = {"cr_effective": cr["effective"], "coverage": cov, "mapping": mapping}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(cov, indent=1))


if __name__ == "__main__":
    main()
