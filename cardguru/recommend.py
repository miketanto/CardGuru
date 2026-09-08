"""Commander deck recommendation engine.

The recommendation logic is mechanical, not co-occurrence-based: detect what
a commander DOES from its ability graph ("synergy hooks"), then run
complement queries for cards whose graphs connect to those hooks — token
makers pair with token payoffs, lifegain sources with lifegain triggers,
death triggers with sacrifice outlets. Every recommendation carries a
machine-readable WHY (hook + matched structure), and color identity comes
from the canonical card index.

Hook detectors are node-scans over a single card's graph; complement queries
run over the whole index. Both sides speak the same graph vocabulary.
"""
from __future__ import annotations

CI_ORDER = "wubrg"


# --------------------------------------------------------- detector helpers

def _nodes(rec):
    return rec.get("nodes") or []


def _params(n):
    return n.get("params") or {}


def has_api(rec, *apis):
    return any(n.get("api") in apis for n in _nodes(rec))


def has_trigger(rec, mode, **contains):
    for n in _nodes(rec):
        if n.get("kind") != "T":
            continue
        p = _params(n)
        if p.get("Mode") != mode:
            continue
        if all(want.lower() in str(p.get(key, "")).lower()
               for key, want in contains.items()):
            return True
    return False


def has_keyword(rec, *kws):
    for n in _nodes(rec):
        if n.get("kind") == "K":
            raw = (n.get("raw") or n.get("keyword") or "")
            if any(raw.split(":")[0].strip() == k for k in kws):
                return True
    return False


def _cost(n):
    return str(_params(n).get("Cost", ""))


# --------------------------------------------------------------- hook defs
#
# hook -> describe, detect(rec), complements {class: query DSL}
# Complement queries are deliberately structural: they match what a card DOES.

def _detect_disrupts_spells(rec):
    """Interferes with an opponent's spell while it is on the stack, or taxes
    what they can cast.

    This is a *functional* class with no single structural signature — Forge
    expresses it at least four unrelated ways, and new sets keep adding more
    (Airbend arrived with the Avatar set). Enumerating them in an LLM prompt
    doesn't survive the next set; one detector does.

        api Counter                        classic counterspells       (514)
        api Airbend                        exile a spell, recastable    (13)
        ChangeZone off the Stack           "exile target spell"          (9)
        static RaiseCost vs an Opponent    tax effects                  (90)

    Aven Interrupter is the case that motivated this: it disrupts twice (an
    ETB that exiles a spell, plus an opponent-facing RaiseCost static) and
    matches none of the above except through this hook.
    """
    for n in _nodes(rec):
        p = _params(n)
        if n.get("api") in ("Counter", "Airbend"):
            return True
        if n.get("api") == "ChangeZone" and (
                p.get("TargetType") == "Spell"
                or "Stack" in str(p.get("Origin", ""))
                or "Stack" in str(p.get("TgtZone", ""))):
            return True
        # A cost-raiser only counts as disruption when aimed at an opponent —
        # plenty of statics raise costs for everyone or for the controller.
        if n.get("kind") == "S" and p.get("Mode") == "RaiseCost" \
                and "Opponent" in str(p.get("Activator", "")):
            return True
    return False


def _detect_makes_tokens(rec):
    return has_api(rec, "Token")


def _detect_gains_life(rec):
    return has_api(rec, "GainLife") or has_keyword(rec, "Lifelink")


def _detect_cares_about_death(rec):
    for n in _nodes(rec):
        p = _params(n)
        if n.get("kind") == "T" and p.get("Mode") == "ChangesZone" \
                and p.get("Origin") == "Battlefield" \
                and p.get("Destination") == "Graveyard" \
                and p.get("ValidCard") != "Card.Self":
            return True
    return any(n.get("kind") == "R" and _params(n).get("Event") == "Moved"
               for n in _nodes(rec))


def _detect_puts_counters(rec):
    return has_api(rec, "PutCounter", "Proliferate")


def _detect_amplifies_etb_triggers(rec):
    """Yarok/Panharmonicon-style: ETB triggers trigger an additional time."""
    return any(_params(n).get("Mode") == "Panharmonicon"
               and _params(n).get("Destination") == "Battlefield"
               and "Attack" not in str(_params(n).get("ValidMode", ""))
               for n in _nodes(rec))


def _detect_sac_outlet(rec):
    return any("Sac<" in _cost(n) and "Creature" in _cost(n) for n in _nodes(rec))


def _detect_amplifies_death(rec):
    return any(_params(n).get("Mode") == "Panharmonicon"
               and _params(n).get("Origin") == "Battlefield"
               and _params(n).get("Destination") == "Graveyard"
               for n in _nodes(rec))


def _detect_buffs_tokens(rec):
    for n in _nodes(rec):
        p = _params(n)
        if p.get("Mode") == "Continuous" and "Creature.token" in str(p.get("Affected", "")) \
                and ("AddKeyword" in p or "AddPower" in p):
            return True
    return False


def _detect_spellslinger(rec):
    return has_trigger(rec, "SpellCast", ValidCard="Instant") \
        or has_trigger(rec, "SpellCast", ValidCard="Sorcery") \
        or has_trigger(rec, "SpellCastOrCopy")


def _detect_landfall(rec):
    """Any trigger watching Land zone-changes (ETB landfall, Gitrog-style
    lands-to-graveyard), or an extra-land-drop static."""
    for n in _nodes(rec):
        p = _params(n)
        if n.get("kind") == "T" and p.get("Mode") in ("ChangesZone", "ChangesZoneAll") \
                and "Land" in str(p.get("ValidCard", "") or p.get("ValidCards", "")):
            return True
    return any("AdjustLandPlays" in _params(n) for n in _nodes(rec))


def _detect_reanimator(rec):
    """Recurs cards from graveyards: to the battlefield (Reanimate, and
    Living Death's mass ChangeZoneAll via exile) or to hand (Genesis)."""
    # returns executed by a SELF trigger (Enduring-cycle death triggers)
    # are recursion, not a reanimator wanting fodder in graveyards
    self_exec = {_params(t).get("Execute") for t in _nodes(rec)
                 if t.get("kind") == "T"
                 and "Self" in str(_params(t).get("ValidCard", ""))}
    for n in _nodes(rec):
        p = _params(n)
        if n.get("id") in self_exec or "Self" in str(p.get("Defined", "")):
            continue
        if n.get("api") in ("ChangeZone", "ChangeZoneAll") \
                and p.get("Origin") == "Graveyard" \
                and p.get("Destination") in ("Battlefield", "Hand", "Exile"):
            # Graveyard->Exile only counts when a later node returns to play
            # (the Living Death two-step); plain graveyard hate doesn't
            if p.get("Destination") == "Exile":
                if any(_params(m).get("Destination") == "Battlefield"
                       for m in _nodes(rec)):
                    return True
                continue
            return True
    return False


def _detect_self_mill(rec):
    for n in _nodes(rec):
        p = _params(n)
        if n.get("api") == "Mill":
            d = str(p.get("Defined", "You"))
            if d in ("You", "Self", "Player.You"):
                return True
        # entomb/Buried Alive: tutor cards directly to the graveyard
        if n.get("api") == "ChangeZone" and p.get("Origin") == "Library" \
                and p.get("Destination") == "Graveyard":
            return True
    return False


def _detect_discard_matters(rec):
    return has_trigger(rec, "Discarded")


def _detect_draw_matters(rec):
    return has_trigger(rec, "Drawn")


def _detect_attacks_matter(rec):
    return has_trigger(rec, "Attacks") or has_trigger(rec, "AttackersDeclared") \
        or has_trigger(rec, "AttackersDeclaredOneTarget")


def _detect_combat_damage_matters(rec):
    """Saboteur/pillage triggers: combat damage to a player pays off."""
    for n in _nodes(rec):
        p = _params(n)
        if n.get("kind") == "T" and p.get("Mode") in ("DamageDone", "DamageDoneOnce") \
                and p.get("CombatDamage") == "True" \
                and "Player" in str(p.get("ValidTarget", "")):
            src = str(p.get("ValidSource", ""))
            if "YouCtrl" in src or "Card.Self" in src:
                return True
    return False


def _detect_disruptive_etb(rec):
    """Tempo creatures: an ETB trigger whose effect disrupts the OPPONENT
    (Deep-Cavern Bat hand exile, Tishana's Tidebinder ability counter,
    Floodpits Drowner tap-stun) rather than generating own-side value."""
    if "Creature" not in (rec.get("types") or ""):
        return False
    has_etb = any(n.get("kind") == "T"
                  and _params(n).get("Mode") == "ChangesZone"
                  and _params(n).get("Destination") == "Battlefield"
                  and "Card.Self" in str(_params(n).get("ValidCard", ""))
                  for n in _nodes(rec))
    if not has_etb:
        return False
    for n in _nodes(rec):
        p = _params(n)
        if n.get("api") == "Counter":
            return True
        if n.get("api") in ("Tap", "TapAll") and "Opp" in str(p.get("ValidTgts", "")):
            return True
        blob = str(p.get("ValidTgts", "")) + str(p.get("Defined", ""))
        if n.get("api") in ("Discard", "ChangeZone", "RevealHand", "PeekAndReveal") \
                and "Opp" in blob:
            return True
    return False


def _detect_creatures_entering_matter(rec):
    """Battledriver/Cathars' Crusade/Impact Tremors: triggers when your
    (other) creatures enter the battlefield."""
    for n in _nodes(rec):
        p = _params(n)
        if n.get("kind") == "T" and p.get("Mode") == "ChangesZone" \
                and p.get("Destination") == "Battlefield":
            v = str(p.get("ValidCard", ""))
            if "Creature" in v and "YouCtrl" in v and "Card.Self" not in v:
                return True
    return False


def _detect_lifedrain(rec):
    for n in _nodes(rec):
        if n.get("api") == "LoseLife" \
                and "Opponent" in str(_params(n).get("Defined", "")):
            return True
    return False


def _detect_artifacts_matter(rec):
    if has_trigger(rec, "ChangesZone", ValidCard="Artifact",
                   Destination="Battlefield") \
            or has_trigger(rec, "SpellCast", ValidCard="Artifact"):
        return True
    for n in _nodes(rec):
        p = _params(n)
        if "Artifact" in str(p.get("Affected", "")) and p.get("Mode") == "Continuous":
            return True
        if "Artifact" in _cost(n):          # tapXType<1/Artifact>, Sac<1/Artifact>...
            return True
        if "construct" in str(p.get("TokenScript", "")).lower():
            return True
    return False


def _detect_enchantments_matter(rec):
    return has_trigger(rec, "ChangesZone", ValidCard="Enchantment",
                       Destination="Battlefield") \
        or has_trigger(rec, "SpellCast", ValidCard="Enchantment") \
        or any("Enchantment" in str(_params(n).get("Affected", ""))
               and _params(n).get("Mode") == "Continuous" for n in _nodes(rec))


def _detect_tribal_lord(rec):
    for n in _nodes(rec):
        p = _params(n)
        if p.get("Mode") == "Continuous" and "AddPower" in p:
            aff = str(p.get("Affected", ""))
            if "Creature." in aff and ".token" not in aff and "YouCtrl" in aff:
                return True
    return False


def _detect_blink(rec):
    """Exile-from-battlefield plus a return-to-battlefield node in the same
    graph (the flicker round-trip)."""
    exiles = any(n.get("api") == "ChangeZone"
                 and _params(n).get("Origin") == "Battlefield"
                 and _params(n).get("Destination") == "Exile"
                 for n in _nodes(rec))
    returns = any(_params(n).get("Destination") == "Battlefield"
                  and _params(n).get("Origin") in ("Exile", "All", None)
                  and n.get("api") == "ChangeZone"
                  for n in _nodes(rec))
    return exiles and returns


def _detect_copies_things(rec):
    return has_api(rec, "CopyPermanent", "CopySpellAbility")


def _detect_plays_from_graveyard(rec):
    """Muldrotha-style: a Continuous MayPlay static whose affected zone is
    the graveyard."""
    return any(_params(n).get("Mode") == "Continuous"
               and _params(n).get("MayPlay") == "True"
               and _params(n).get("AffectedZone") == "Graveyard"
               for n in _nodes(rec))


def _detect_amplifies_attack_triggers(rec):
    """Isshin-style: Panharmonicon static over attack trigger modes."""
    return any(_params(n).get("Mode") == "Panharmonicon"
               and "Attack" in str(_params(n).get("ValidMode", ""))
               for n in _nodes(rec))


def _detect_untaps_things(rec):
    return has_api(rec, "Untap", "UntapAll")


def _detect_amplifies_mana(rec):
    """Mana multipliers: a TapsForMana trigger that adds extra mana
    (Badgermole Cub, Zendikar Resurgent family). Multiplicative acceleration
    - scales with every source the deck already has."""
    has_taps_trigger = any(n.get("kind") == "T"
                           and _params(n).get("Mode") == "TapsForMana"
                           for n in _nodes(rec))
    return has_taps_trigger and has_api(rec, "Mana", "ManaReflected")


def _detect_equipment_matters(rec):
    if has_trigger(rec, "Attached") or "Equipment" in str(rec.get("types") or ""):
        return True
    # Equipment referenced anywhere in the graph (count SVars, Affected,
    # cost reductions) marks an equipment payoff like Wyleth
    return any("Equipment" in str(_params(n)) for n in _nodes(rec))


_DEATH_TRIGGER_Q = {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                       "params": {"Origin": "Battlefield",
                                                  "Destination": "Graveyard"}},
                              "to": {}}}
_SAC_OUTLET_Q = {"node": {"kind": "A", "apiKind": "AB",
                          "params": {"Cost": {"regex": r"Sac<[0-9X]+/Creature"}}}}
_TOKEN_MAKER_Q = {"chain": {"from": {"kind": {"any": ["A", "T"]}},
                            "to": {"api": "Token"}}}
_REANIMATE_Q = {"node": {"api": "ChangeZone",
                         "params": {"Origin": "Graveyard",
                                    "Destination": "Battlefield"}}}
_SELF_MILL_Q = {"node": {"api": "Mill"}}

HOOKS = {
    "disrupts_spells": {
        "describe": "interferes with opponents' spells (counter, exile off the "
                    "stack, or tax)",
        "detect": _detect_disrupts_spells,
        # Deliberately no complements. Every other hook here names a real
        # synergy — token-doubling genuinely pays off token-making. Nothing
        # "pays off" holding counterspells; disruption is a role you fill, not
        # an engine you build around. Inventing complements to fill the slot
        # put 13 spurious enabler->payoff edges into the deck-fingerprint graph
        # and made a 2-card disruption package outrank the actual game plan.
        # This hook exists as a *search facet* only.
        "complements": {}},
    "makes_tokens": {
        "describe": "creates tokens",
        "detect": _detect_makes_tokens,
        "complements": {
            "token_payoffs": {"chain": {"from": {"kind": "T", "mode": "TokenCreated"},
                                        "to": {}}},
            "token_doubling": {"chain": {"from": {"kind": "R",
                                                  "params": {"Event": "CreateToken"}},
                                         "to": {"api": "ReplaceToken"}}},
            "anthems": {"node": {"mode": "Continuous",
                                 "params": {"AddPower": True,
                                            "Affected": {"contains": "Creature.YouCtrl"}}}},
        }},
    "gains_life": {
        "describe": "gains life",
        "detect": _detect_gains_life,
        "complements": {
            "lifegain_payoffs": {"chain": {"from": {"kind": "T", "mode": "LifeGained"},
                                           "to": {}}},
            "lifegain_doubling": {"chain": {"from": {"kind": "R",
                                                     "params": {"Event": "GainLife"}},
                                            "to": {}}},
        }},
    "cares_about_death": {
        "describe": "triggers on creatures dying",
        "detect": _detect_cares_about_death,
        "complements": {
            "sac_outlets": _SAC_OUTLET_Q,
            "token_fodder": {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                                "params": {"Destination": "Battlefield"}},
                                       "to": {"api": "Token"}}},
        }},
    "puts_counters": {
        "describe": "puts +1/+1 counters",
        "detect": _detect_puts_counters,
        "complements": {
            "proliferate": {"node": {"api": "Proliferate"}},
            "counter_doubling": {"chain": {"from": {"kind": "R",
                                                    "params": {"Event": "AddCounter"}},
                                           "to": {"api": "ReplaceCounter"}}},
            "counter_payoffs": {"node": {"mode": "Continuous",
                                         "params": {"Affected": {"contains": "counter"}}}},
        }},
    "sac_outlet": {
        "describe": "sacrifices creatures as a cost",
        "detect": _detect_sac_outlet,
        "complements": {
            "death_triggers": _DEATH_TRIGGER_Q,
            "token_makers": _TOKEN_MAKER_Q,
        }},
    "amplifies_death_triggers": {
        "describe": "makes dies-triggers trigger an additional time",
        "detect": _detect_amplifies_death,
        "complements": {
            "death_triggers": _DEATH_TRIGGER_Q,
            "sac_outlets": _SAC_OUTLET_Q,
        }},
    "buffs_tokens": {
        "describe": "grants abilities to your creature tokens",
        "detect": _detect_buffs_tokens,
        "complements": {
            "token_makers": _TOKEN_MAKER_Q,
        }},
    "spellslinger": {
        "describe": "triggers whenever you cast instants/sorceries",
        "detect": _detect_spellslinger,
        "complements": {
            "cheap_cantrips": {"all": [
                {"card": {"types": {"regex": "Instant|Sorcery"}}},
                {"node": {"apiKind": "SP", "api": "Draw"}}]},
            "spell_copiers": {"node": {"api": "CopySpellAbility"}},
            "cost_reducers": {"node": {"kind": "S", "mode": "ReduceCost",
                                       "params": {"ValidCard": {"regex": "Instant|Sorcery"}}}},
        }},
    "landfall": {
        "describe": "triggers when lands enter under your control",
        "detect": _detect_landfall,
        "complements": {
            "extra_land_drops": {"node": {"mode": "Continuous",
                                          "params": {"AdjustLandPlays": True}}},
            "land_fetch": {"node": {"api": "ChangeZone",
                                    "params": {"Origin": "Library",
                                               "Destination": "Battlefield",
                                               "ChangeType": {"regex": "Land|Plains|Island|Swamp|Mountain|Forest"}}}},
            "land_recursion": {"node": {"api": "ChangeZone",
                                        "params": {"Origin": "Graveyard",
                                                   "ChangeType": {"contains": "Land"}}}},
        }},
    "reanimator": {
        "describe": "returns creatures from graveyards to the battlefield",
        "detect": _detect_reanimator,
        "complements": {
            "self_mill": _SELF_MILL_Q,
            "big_etb_creatures": {"all": [
                {"card": {"types": {"contains": "Creature"}}},
                {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                    "params": {"ValidCard": {"contains": "Card.Self"},
                                               "Destination": "Battlefield"}},
                           "to": {}}}]},
            "discard_outlets": {"node": {"kind": "A",
                                         "params": {"Cost": {"contains": "Discard"}}}},
        }},
    "self_mill": {
        "describe": "puts cards from your library into your graveyard",
        "detect": _detect_self_mill,
        "complements": {
            "graveyard_casting": {"node": {"mode": "Continuous",
                                           "params": {"MayPlay": True,
                                                      "Affected": {"contains": "Graveyard"}}}},
            "reanimation": _REANIMATE_Q,
            "graveyard_size_payoffs": {"node": {"params": {"Defined": {"contains": "Graveyard"}}}},
        }},
    "discard_matters": {
        "describe": "triggers when cards are discarded",
        "detect": _detect_discard_matters,
        "complements": {
            "discard_outlets": {"node": {"kind": "A",
                                         "params": {"Cost": {"contains": "Discard"}}}},
            "mass_discard": {"node": {"api": "Discard",
                                      "params": {"Mode": {"contains": "Hand"}}}},
        }},
    "draw_matters": {
        "describe": "triggers on card draws",
        "detect": _detect_draw_matters,
        "complements": {
            "extra_draw": {"node": {"api": "Draw",
                                    "params": {"NumCards": {"regex": "^[2-9]"}}}},
            "wheel_effects": {"chain": {"from": {"kind": "A", "api": "Discard",
                                                 "params": {"Mode": "Hand"}},
                                        "to": {"api": "Draw"}}},
        }},
    "attacks_matter": {
        "describe": "triggers on attacking",
        "detect": _detect_attacks_matter,
        "complements": {
            "extra_combats": {"node": {"api": "AddPhase"}},
            "haste_enablers": {"node": {"mode": "Continuous",
                                        "params": {"AddKeyword": {"contains": "Haste"},
                                                   "Affected": {"contains": "Creature.YouCtrl"}}}},
            "attack_triggers": {"chain": {"from": {"kind": "T",
                                                   "mode": {"any": ["Attacks", "AttackersDeclared",
                                                                    "AttackersDeclaredOneTarget"]}},
                                          "to": {}}},
        }},
    "combat_damage_matters": {
        "describe": "pays off combat damage to players",
        "detect": _detect_combat_damage_matters,
        "complements": {
            "extra_combats": {"node": {"api": "AddPhase"}},
            "haste_enablers": {"node": {"mode": "Continuous",
                                        "params": {"AddKeyword": {"contains": "Haste"},
                                                   "Affected": {"contains": "Creature.YouCtrl"}}}},
            "evasion_grants": {"node": {"mode": "Continuous",
                                        "params": {"AddKeyword": {"regex": "Flying|Menace|Trample|Fear|Intimidate|Shadow"},
                                                   "Affected": {"contains": "Creature.YouCtrl"}}}},
            # the FUEL: evasive bodies that actually connect for the trigger
            "evasive_attackers": {"all": [
                {"card": {"types": {"contains": "Creature"}}},
                {"any": [{"keyword": "Flying"}, {"keyword": "Menace"},
                         {"keyword": "Fear"}, {"keyword": "Shadow"},
                         {"keyword": "Intimidate"},
                         {"node": {"kind": "S", "mode": "CantBlockBy"}}]}]},
        }},
    "disruptive_etb": {
        "describe": "disrupts the opponent as it enters (tempo creature)",
        "detect": _detect_disruptive_etb,
        "complements": {
            "blink_flicker": {"node": {"api": "ChangeZone",
                                       "params": {"Origin": "Battlefield",
                                                  "Destination": "Exile"}}},
            "self_bounce": {"node": {"api": "ChangeZone",
                                     "params": {"Origin": "Battlefield",
                                                "Destination": "Hand"}}},
            "etb_doubling": {"node": {"kind": "S",
                                      "params": {"Mode": "Panharmonicon",
                                                 "Destination": "Battlefield"}}},
        }},
    "creatures_entering_matter": {
        "describe": "triggers when your creatures enter the battlefield",
        "detect": _detect_creatures_entering_matter,
        "complements": {
            "token_makers": _TOKEN_MAKER_Q,
            "mass_creature_spells": {"node": {"apiKind": "SP", "api": "Token",
                                              "params": {"TokenAmount": {"regex": "^[2-9X]"}}}},
        }},
    "lifedrain": {
        "describe": "drains opponents' life",
        "detect": _detect_lifedrain,
        "complements": {
            "drain_amplifiers": {"node": {"mode": "Continuous",
                                          "params": {"Affected": {"contains": "Opponent"}}}},
            "lifegain_payoffs": {"chain": {"from": {"kind": "T", "mode": "LifeGained"},
                                           "to": {}}},
        }},
    "artifacts_matter": {
        "describe": "cares about artifacts",
        "detect": _detect_artifacts_matter,
        "complements": {
            "artifact_token_makers": {"node": {"params": {"TokenScript": {"regex": "treasure|clue|food|construct|thopter|servo"}}}},
            "affinity_payoffs": {"node": {"params": {"Defined": {"contains": "Artifact"}}}},
            "artifact_etb_triggers": {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                                         "params": {"ValidCard": {"contains": "Artifact"},
                                                                    "Destination": "Battlefield"}},
                                                "to": {}}},
        }},
    "enchantments_matter": {
        "describe": "cares about enchantments",
        "detect": _detect_enchantments_matter,
        "complements": {
            "enchantment_etb_triggers": {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                                            "params": {"ValidCard": {"contains": "Enchantment"},
                                                                       "Destination": "Battlefield"}},
                                                   "to": {}}},
            "auras": {"card": {"types": {"contains": "Aura"}}},
        }},
    "tribal_lord": {
        "describe": "pumps your creatures of a type",
        "detect": _detect_tribal_lord,
        "complements": {
            "token_makers": _TOKEN_MAKER_Q,
            "anthem_stacking": {"node": {"mode": "Continuous",
                                         "params": {"AddPower": True,
                                                    "Affected": {"contains": "Creature.YouCtrl"}}}},
        }},
    "blink": {
        "describe": "exiles and returns permanents (flicker)",
        "detect": _detect_blink,
        "complements": {
            "etb_value_creatures": {"all": [
                {"card": {"types": {"contains": "Creature"}}},
                {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                    "params": {"ValidCard": {"contains": "Card.Self"},
                                               "Destination": "Battlefield"}},
                           "to": {}}}]},
            "etb_doubling": {"node": {"kind": "S",
                                      "params": {"Mode": "Panharmonicon",
                                                 "Destination": "Battlefield"}}},
        }},
    "copies_things": {
        "describe": "copies spells or permanents",
        "detect": _detect_copies_things,
        "complements": {
            "etb_value_creatures": {"all": [
                {"card": {"types": {"contains": "Creature"}}},
                {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                    "params": {"ValidCard": {"contains": "Card.Self"},
                                               "Destination": "Battlefield"}},
                           "to": {}}}]},
            "big_spells": {"all": [
                {"card": {"types": {"regex": "Instant|Sorcery"}}},
                {"node": {"api": {"any": ["Draw", "DealDamage", "Token"]}}}]},
        }},
    "amplifies_mana": {
        "describe": "multiplies mana production",
        "detect": _detect_amplifies_mana,
        "complements": {
            "mana_dorks": {"all": [
                {"card": {"types": {"contains": "Creature"}}},
                {"node": {"kind": "A", "apiKind": "AB", "api": "Mana",
                          "params": {"Cost": {"contains": "T"}}}}]},
            "land_animators": {"node": {"api": {"any": ["Earthbend", "Animate",
                                                        "AnimateAll"]}}},
            "big_spells": {"card": {"manaCost": {"regex": "^[5-9]"}}},
        }},
    "untapper": {
        "describe": "untaps permanents",
        "detect": _detect_untaps_things,
        "complements": {
            "big_mana_rocks": {"node": {"kind": "A", "apiKind": "AB", "api": "Mana",
                                        "params": {"Cost": {"contains": "T"},
                                                   "Amount": {"regex": "^[2-9]"}}}},
            "tap_ability_creatures": {"all": [
                {"card": {"types": {"contains": "Creature"}}},
                {"node": {"kind": "A", "apiKind": "AB",
                          "params": {"Cost": {"regex": "(^|\\s)T($|\\s)"}}}}]},
        }},
    "plays_from_graveyard": {
        "describe": "lets you play cards from your graveyard",
        "detect": _detect_plays_from_graveyard,
        "complements": {
            "self_mill": _SELF_MILL_Q,
            "sac_outlets": _SAC_OUTLET_Q,
            "permanent_value_etbs": {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                                        "params": {"ValidCard": {"contains": "Card.Self"},
                                                                   "Destination": "Battlefield"}},
                                               "to": {}}},
        }},
    "amplifies_etb_triggers": {
        "describe": "makes enters-the-battlefield triggers trigger an additional time",
        "detect": _detect_amplifies_etb_triggers,
        "complements": {
            "etb_value_creatures": {"all": [
                {"card": {"types": {"contains": "Creature"}}},
                {"chain": {"from": {"kind": "T", "mode": "ChangesZone",
                                    "params": {"ValidCard": {"contains": "Card.Self"},
                                               "Destination": "Battlefield"}},
                           "to": {}}}]},
            "blink_enablers": {"node": {"api": "ChangeZone",
                                        "params": {"Origin": "Battlefield",
                                                   "Destination": "Exile"}}},
        }},
    "amplifies_attack_triggers": {
        "describe": "makes attack triggers trigger an additional time",
        "detect": _detect_amplifies_attack_triggers,
        "complements": {
            "attack_triggers": {"chain": {"from": {"kind": "T", "mode": "Attacks"},
                                          "to": {}}},
            "extra_combats": {"node": {"api": "AddPhase"}},
            "haste_enablers": {"node": {"mode": "Continuous",
                                        "params": {"AddKeyword": {"contains": "Haste"},
                                                   "Affected": {"contains": "Creature.YouCtrl"}}}},
        }},
    "equipment_matters": {
        "describe": "cares about Equipment",
        "detect": _detect_equipment_matters,
        "complements": {
            "equipment": {"card": {"types": {"contains": "Equipment"}}},
            "equip_cost_reduction": {"node": {"kind": "S", "mode": "ReduceCost",
                                              "params": {"ValidCard": {"contains": "Equipment"}}}},
        }},
}


def detect_hooks(rec: dict) -> list[str]:
    return [name for name, cfg in HOOKS.items() if cfg["detect"](rec)]


def color_identity_ok(ci: str | None, commander_ci: set[str]) -> bool:
    if ci is None:
        return False
    return set(ci) <= commander_ci


def recommend(idx, commander_rec: dict, ci_by_name: dict,
              limit_per_class: int = 8) -> dict:
    name = commander_rec["name"]
    commander_ci = set(ci_by_name.get(name) or "")
    hooks = detect_hooks(commander_rec)
    out = {"commander": name, "color_identity": "".join(
        c for c in CI_ORDER if c in commander_ci), "hooks": {}}
    for hook in hooks:
        cfg = HOOKS[hook]
        classes = {}
        for cname, query in cfg["complements"].items():
            rows = []
            for hit in idx.search(query):
                rec = hit["record"]
                if rec["name"] == name:
                    continue
                if not color_identity_ok(ci_by_name.get(rec["name"]), commander_ci):
                    continue
                rows.append(rec["name"])
            seen, unique = set(), []
            for r in rows:
                if r not in seen:
                    seen.add(r)
                    unique.append(r)
            classes[cname] = {"total": len(unique),
                              "top": sorted(unique)[:limit_per_class]}
        out["hooks"][hook] = {"why": f"{name} {cfg['describe']}",
                              "complements": classes}
    return out


# gate-passed induced concepts (see cardguru/induction.py) load as data
from .induction import load_induced_hooks as _load_induced  # noqa: E402
_load_induced()
