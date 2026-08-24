"""M3: trigger modes, replacement events, static modes, and chain edges.

M2's emitter stopped at ability kinds, effect APIs, costs and target
restrictions. It emitted no `mode` field and no `R` nodes, which is why a02 and
a03 returned zero hits -- two whole node classes were missing, not two card-
specific gaps.

## The build rule, stated before any production was written

Coverage is decided by **frequency rank**, the order
research/phase1-cardscripts.md §2 already established ("a CR-mapping effort that
covers only the top ~50 APIs and ~30 trigger modes already covers the
overwhelming majority of ability instances"). For M3:

    top 10 trigger modes        (of 137)
    top 10 replacement events   (of  34)
    top 15 static modes         (of  81)

Nothing is included because a particular question needs it, and nothing is
excluded because a particular question needs it. Where that rule lands is where
it lands -- `Panharmonicon` is rank 14 of 81 static modes and is therefore in
scope; `ReplaceToken` is rank 95 of 191 APIs and is therefore out of scope, so
any question depending on it will still fail. That is the rule doing its job,
not a result being engineered.

This module was written against the dev half of M1's split, with no adversarial
question inspected while writing it.
"""
from __future__ import annotations

import re

# --- trigger modes (top 10 by frequency) --------------------------------------
# ChangesZone 7508, Phase 2359, Attacks 1598, SpellCast 1399, DamageDone 871,
# AttackersDeclared 239, DamageDoneOnce 204, Drawn 149, ChaosEnsues 139,
# AttackerBlocked 127

TRIGGER_MODES = [
    ("Phase",             r"^at the (?:beginning|end) of\b|^at end of turn\b"),
    ("ChaosEnsues",       r"\bchaos ensues\b"),
    # Authored from card text, not from the mode name: no card says
    # "attackers are declared". The player-level attack event reads
    # "Whenever you attack", "Whenever you attack with one or more ...",
    # "Whenever one or more creatures you control attack".
    ("AttackersDeclared", r"\bwhenever you attack\b"
                          r"|\bone or more creatures?[^,]{0,30}\battacks?\b"
                          r"|\bwhenever a player attacks\b"),
    ("AttackerBlocked",   r"\bbecomes? blocked\b"),
    ("Attacks",           r"\battacks?\b"),
    ("SpellCast",         r"\bcasts?\b[^,]{0,40}\bspell\b|\byou cast\b"),
    ("DamageDone",        r"\bdeals?\b[^,]{0,30}\bdamage\b"),
    # Safe to broaden now that modes match the event clause only:
    # "draw your second card each turn" is the dominant missed wording.
    ("Drawn",             r"\bdraws?\b[^,]{0,25}\bcards?\b"),
    ("ChangesZone",       r"\benters?\b|\bdies\b|\bleaves? the battlefield\b"
                          r"|\bis put into\b|\bput into a graveyard\b"),
]

# --- replacement events (top 10 by frequency) ---------------------------------
# Moved 957, DamageDone 218, Untap 155, Counter 117, Draw 37, CreateToken 32,
# AddCounter 32, GainLife 21, BeginPhase 21, GameLoss 19

REPLACEMENT_EVENTS = [
    ("Untap",       r"\bdoesn'?t untap\b|\bdon'?t untap\b"),
    # Forge's R:Event$ Counter is uncounterability -- "this spell can't be
    # countered" -- not a "would be countered" replacement.
    ("Counter",     r"\bcan'?t be countered\b"),
    ("Draw",        r"\bif\b[^.]{0,40}\bwould draw\b"),
    ("CreateToken", r"\bwould (?:create|put)\b[^.]{0,40}\btokens?\b"),
    ("AddCounter",  r"\bwould (?:have|get|be put)\b[^.]{0,50}\bcounters?\b"
                    r"|\bwould put\b[^.]{0,40}\bcounters?\b"),
    ("GainLife",    r"\bif\b[^.]{0,40}\bwould gain\b[^.]{0,20}\blife\b"),
    ("GameLoss",    r"\bwould lose the game\b"),
    ("BeginPhase",  r"\bwould begin\b[^.]{0,20}\b(?:step|phase)\b"),
    ("DamageDone",  r"\bwould (?:be )?deal\w*\b[^.]{0,40}\bdamage\b"
                    r"|\bprevent\b[^.]{0,40}\bdamage\b"),
    # Moved is the catch-all zone-change replacement and by far the largest,
    # but a bare 'enters' is usually an ordinary static or trigger. A Moved
    # replacement needs the replacement construction itself: 'enters tapped',
    # 'enters with', 'as X enters', or a 'would be put into' clause.
    # 'As X enters, choose ...' is a Forge static, not a Moved replacement,
    # so it is deliberately absent here.
    ("Moved",       r"\benters?\b[^.]{0,40}\b(?:tapped|under the control)\b"
                    r"|\bwould be put into\b|\bwould die\b|\bwould enter\b"),
]

ZONE_WORDS = [
    ("Graveyard",   r"\bgraveyard\b"),
    ("Battlefield", r"\bbattlefield\b|\benters?\b"),
    ("Exile",       r"\bexiled?\b"),
    ("Hand",        r"\bhand\b"),
    ("Library",     r"\blibrary\b"),
    ("Stack",       r"\bspell\b"),
]

# --- static modes (top 15 by frequency) ---------------------------------------
# Continuous 4803, ReduceCost 526, CantBlockBy 363, AlternativeCost 148,
# CantBlock 139, CantAttack 120, CantBeCast 101, MustAttack 101, RaiseCost 95,
# 'CantAttack,CantBlock' 58, CastWithFlash 57, MinMaxBlocker 43,
# OptionalCost 40, Panharmonicon 38, CantBeActivated 33

STATIC_MODES = [
    ("Panharmonicon",   r"\btriggers? an additional time\b"
                        r"|\btrigger an additional time\b"),
    # 'except by' / 'can block only' were tried once before the emitter took
    # its kind from M0's classifier and cost 5 points of static-mode precision.
    # Re-tried after that change and audited from card text: the misses are
    # dominated by exactly these two wordings, so they are back in.
    ("CantBlockBy",     r"\bcan'?t be blocked by\b"
                        r"|\bcan'?t be blocked except by\b"
                        r"|\bcan block only\b"),
    ("MinMaxBlocker",   r"\bcan'?t be blocked by more than\b|\bmust be blocked by\b"),
    ("CantBeActivated", r"\bcan'?t be activated\b"),
    # Active voice dominates: "Your opponents can't cast spells", not
    # "can't be cast".
    ("CantBeCast",      r"\bcan'?t be cast\b|\bcan'?t cast\b"),
    ("CastWithFlash",   r"\bas though it had flash\b|\bas though they had flash\b"),
    ("ReduceCost",      r"\bcosts?\b[^.]{0,25}\bless to cast\b"),
    ("RaiseCost",       r"\bcosts?\b[^.]{0,25}\bmore to cast\b"),
    ("AlternativeCost", r"\brather than pay\b[^.]{0,30}\bmana cost\b"),
    ("OptionalCost",    r"\bas an additional cost\b"),
    ("MustAttack",      r"\battacks? each combat if able\b"),
    ("CantAttack,CantBlock", r"\bcan'?t attack or block\b"),
    ("CantAttack",      r"\bcan'?t attack\b"),
    ("CantBlock",       r"\bcan'?t block\b"),
]

_COMPILED = {
    "trigger": [(k, re.compile(p, re.I)) for k, p in TRIGGER_MODES],
    "replacement": [(k, re.compile(p, re.I)) for k, p in REPLACEMENT_EVENTS],
    "static": [(k, re.compile(p, re.I)) for k, p in STATIC_MODES],
    "zone": [(k, re.compile(p, re.I)) for k, p in ZONE_WORDS],
}

# 'Whenever a creature dies' -> Origin Battlefield, Destination Graveyard.
DIES_RE = re.compile(r"\bdies\b|\bput into a graveyard from the battlefield\b", re.I)
ENTERS_RE = re.compile(r"\benters?\b", re.I)


# A triggered ability's mode is decided by its EVENT clause, which ends at the
# first comma: 'Whenever X deals combat damage to a player, draw a card' is a
# DamageDone trigger, not a Drawn one. Matching against the whole line let the
# effect half vote on the mode, which is what made Drawn fire 721 times against
# Forge's 145.
EVENT_CLAUSE_RE = re.compile(r"^[^,]{0,160}")


def event_clause(line: str) -> str:
    m = EVENT_CLAUSE_RE.match(line)
    return m.group(0) if m else line


def trigger_mode(line: str) -> str | None:
    """Forge T:Mode$ for a triggered-ability line."""
    event = event_clause(line)
    for mode, rx in _COMPILED["trigger"]:
        if rx.search(event):
            return mode
    # Fall back to the whole line only if the event clause named nothing.
    for mode, rx in _COMPILED["trigger"]:
        if rx.search(line):
            return mode
    return None


def replacement_event(line: str) -> tuple[str, dict] | None:
    """Forge R:Event$ plus any Origin/Destination params."""
    for event, rx in _COMPILED["replacement"]:
        if rx.search(line):
            params = {}
            if event == "Moved":
                if DIES_RE.search(line):
                    params["Origin"] = "Battlefield"
                    params["Destination"] = "Graveyard"
                elif ENTERS_RE.search(line):
                    params["Destination"] = "Battlefield"
                else:
                    for zone, zrx in _COMPILED["zone"]:
                        if zrx.search(line):
                            params["Destination"] = zone
                            break
            return event, params
    return None


def static_mode(line: str) -> tuple[str, dict]:
    """Forge S:Mode$ for a static-ability line. Continuous is the default."""
    for mode, rx in _COMPILED["static"]:
        if rx.search(line):
            params = {}
            if mode == "Panharmonicon":
                # Which triggers does it amplify? Intrinsic to the mode: the
                # static is meaningless without naming the event it doubles.
                if DIES_RE.search(line):
                    params["Origin"] = "Battlefield"
                    params["Destination"] = "Graveyard"
                elif ENTERS_RE.search(line):
                    params["Destination"] = "Battlefield"
            return mode, params
    return "Continuous", {}


# --- chain edges --------------------------------------------------------------

# 'then draw a card', 'if you do, ...', '... instead' continue the same ability
# chain rather than starting a new one.
CHAIN_SPLIT_RE = re.compile(
    r"(?:\.\s+|,\s*)(?:then\b|if you do\b|if that happens\b)", re.I)
INSTEAD_RE = re.compile(r"\binstead\b", re.I)


def chain_edge_type(segment: str, is_replacement: bool) -> str:
    if is_replacement and INSTEAD_RE.search(segment):
        return "ReplaceWith"
    return "SubAbility"
