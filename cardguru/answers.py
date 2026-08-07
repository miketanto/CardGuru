"""Sideboard/meta answer finder: which removal actually beats a given threat.

The point of the ability graph here: an answer isn't an answer unless it gets
past the threat's protections. Text search can list 'destroy target creature'
cards; the graph can also read the THREAT (hexproof, ward, indestructible,
protection, toughness) and the ANSWER (targeted vs not, damage amount,
destroy vs exile vs sacrifice vs -X/-X) and compute whether they connect.

Every verdict carries a machine-readable reason, and any verdict can be
turned into a scenario JSON for engine verification.
"""
from __future__ import annotations

import re

COLOR_LETTERS = set("WUBRG")

# ------------------------------------------------------------ threat profile


def threat_profile(rec: dict) -> dict:
    # keywords live as K nodes in the ability graph
    raw_kws = [n.get("raw", n.get("keyword", ""))
               for n in rec.get("nodes", []) if n.get("kind") == "K"]
    kws = {k.split(":")[0].strip() for k in raw_kws}
    prot = [k for k in raw_kws if k.startswith("Protection")]
    ward = [k for k in raw_kws if k.startswith("Ward")]
    pt = rec.get("pt") or ""
    toughness = None
    power = None
    if "/" in pt:
        try:
            toughness = int(pt.split("/")[1])
        except ValueError:
            pass
        try:
            power = int(pt.split("/")[0])
        except ValueError:
            pass
    colors = {c for c in (rec.get("manaCost") or "") if c in COLOR_LETTERS}
    types = rec.get("types") or ""
    token_scripts = []
    for n in rec.get("nodes", []):
        ts = (n.get("params") or {}).get("TokenScript")
        if ts:
            token_scripts += [t.strip() for t in ts.split(",")]
    # recursion: a death trigger that returns the card itself to the
    # battlefield (Enduring cycle), or Persist/Undying - destroy/damage
    # answers only rent the removal; exile owns it
    by_id = {n.get("id"): n for n in rec.get("nodes", [])}
    recursive = bool({"Persist", "Undying"} & kws)
    for n in rec.get("nodes", []):
        p = n.get("params") or {}
        if (n.get("kind") == "T" and p.get("Mode") == "ChangesZone"
                and p.get("Origin") == "Battlefield"
                and p.get("Destination") == "Graveyard"
                and "Self" in str(p.get("ValidCard", ""))):
            chained = by_id.get(p.get("Execute"))
            if chained is not None and chained.get("api") == "ChangeZone" \
                    and (chained.get("params") or {}).get("Destination") \
                    == "Battlefield":
                recursive = True
    # self-shape-shifting: a conditional static the card puts on ITSELF
    # (Kaito: during your turn, a 3/4 hexproof Ninja that stops being a
    # planeswalker) makes the targeted window PHASE-DEPENDENT
    self_statics = []
    for n in rec.get("nodes", []):
        p = n.get("params") or {}
        if p.get("Mode") == "Continuous" and "Self" in str(p.get("Affected", "")):
            g_kws = [k.strip() for k in str(p.get("AddKeyword", "")).split("&")
                     if k.strip()]
            g_types = [t.strip() for t in str(p.get("AddType", "")).split("&")
                       if t.strip()]
            if g_kws or g_types:
                self_statics.append({
                    "condition": p.get("Condition"),
                    "keywords": g_kws, "types": g_types,
                    "removes_types": p.get("RemoveCardTypes") == "True"})
    mc = rec.get("manaCost")
    mv = None
    if mc and mc != "no cost":
        mv = sum(int(t) if t.isdigit() else (0 if t == "X" else 1)
                 for t in mc.split())
    uncounterable = any(
        n.get("kind") == "R"
        and (n.get("params") or {}).get("Event") == "Counter"
        and (n.get("params") or {}).get("Layer") == "CantHappen"
        and "Self" in str((n.get("params") or {}).get("ValidCard", ""))
        for n in rec.get("nodes", []))
    return {
        "name": rec.get("name"),
        "types": types,
        "mv": mv,
        "uncounterable": uncounterable,
        "recursive": recursive,
        "self_statics": self_statics,
        "is_creature": "Creature" in types,
        "is_land": "Land" in types,
        "pt_is_cda": "*" in pt,
        "token_scripts": token_scripts,
        "toughness": toughness,
        "power": power,
        "keywords": kws,
        "colors": colors,
        "hexproof": "Hexproof" in kws,
        "shroud": "Shroud" in kws,
        "indestructible": "Indestructible" in kws,
        "ward": ward[0] if ward else None,
        "protection": prot,          # e.g. ["Protection:Card.Red:red"]
    }


def _protected_from_color(profile, spell_colors: set[str]) -> bool:
    for p in profile["protection"]:
        low = p.lower()
        for c, word in (("W", "white"), ("U", "blue"), ("B", "black"),
                        ("R", "red"), ("G", "green")):
            if c in spell_colors and word in low:
                return True
        if "everything" in low or "allcolors" in low.replace(" ", ""):
            return True
    return False


# ------------------------------------------------------------ answer classes

def _lit(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def load_token_scripts(path=None):
    """Parse Forge tokenscripts into records keyed by script name."""
    import os
    from .forge_parser import parse_file
    path = path or os.environ.get(
        "CARDGURU_TOKENSCRIPTS",
        "/home/user/forge-src/forge-gui/res/tokenscripts")
    out = {}
    if not os.path.isdir(path):
        return out
    for fn in os.listdir(path):
        if fn.endswith(".txt"):
            try:
                faces = parse_file(os.path.join(path, fn), relroot=path)
                if faces:
                    out[fn[:-4]] = faces[0].to_record()
            except Exception:
                pass
    return out


def token_is_ability_defined(tok_rec: dict) -> bool:
    """True for tokens like the Urza's Saga Construct: 0/0 base whose size is
    granted by its own static ability — remove abilities and it dies to SBAs."""
    if (tok_rec.get("pt") or "") != "0/0":
        return False
    for n in tok_rec.get("nodes", []):
        p = n.get("params") or {}
        if p.get("Mode") == "Continuous" and "AddPower" in p:
            return True
    return False


def ability_dependence(profile: dict, token_scripts: dict) -> list[str]:
    """Why ability-removal answers this threat (empty list = it doesn't)."""
    reasons = []
    if profile["pt_is_cda"]:
        reasons.append("its power/toughness is defined by its own ability")
    for ts in profile["token_scripts"]:
        rec = token_scripts.get(ts)
        if rec and token_is_ability_defined(rec):
            reasons.append(
                f"the {rec.get('name')}s it creates are base 0/0 and get "
                "+X/+X from their own static ability - remove abilities and "
                "they die as 0/0s (CR 704.5f)")
    return reasons


ABILITY_REMOVAL_QUERY = {"node": {"mode": "Continuous",
                                  "params": {"RemoveAllAbilities": "True",
                                             "Affected": {"contains": "Creature"}}}}

ANSWER_QUERIES = {
    "destroy_target": {"node": {"api": "Destroy",
                                "params": {"ValidTgts": {"contains": "Creature"}}}},
    "exile_target": {"node": {"api": "ChangeZone",
                              "params": {"Origin": "Battlefield",
                                         "Destination": "Exile",
                                         "ValidTgts": {"contains": "Creature"}}}},
    "damage_target": {"node": {"api": "DealDamage",
                               "params": {"ValidTgts": {"regex": "Creature|Any"}}}},
    "minus_toughness": {"node": {"api": "Pump",
                                 "params": {"ValidTgts": {"contains": "Creature"},
                                            "NumDef": {"regex": "^-"}}}},
    "edict_sacrifice": {"node": {"api": "Sacrifice",
                                 "params": {"ValidTgts": {"contains": "Player"}}}},
    "edict_sacrifice_mass": {"node": {"api": "Sacrifice",
                                      "params": {"Defined": {"contains": "Opponent"},
                                                 "SacValid": {"regex": "."}}}},
    "bounce_target": {"node": {"api": "ChangeZone",
                               "params": {"Origin": "Battlefield",
                                          "Destination": "Hand",
                                          "ValidTgts": {"contains": "Creature"}}}},
    "destroy_all": {"node": {"api": "DestroyAll",
                             "params": {"ValidCards": {"contains": "Creature"}}}},
    "counter_spell": {"node": {"apiKind": "SP", "api": "Counter",
                               "params": {"TargetType": {"contains": "Spell"}}}},
}

TARGETED = {"destroy_target", "exile_target", "damage_target", "minus_toughness",
            "bounce_target"}


_COLOR_WORDS = {"White": "W", "Blue": "U", "Black": "B",
                "Red": "R", "Green": "G"}
_TYPE_WORDS = {"Creature", "Artifact", "Enchantment", "Instant", "Sorcery",
               "Planeswalker", "Battle", "Kicked", "Legendary"}


def _counter_target_legal(tgts: str, profile: dict):
    """Can this counterspell's ValidTgts legally target the threat AS A SPELL
    on the stack? True/False/None (None = condition we can't evaluate)."""
    import re
    types = profile.get("types") or ""
    mv = profile.get("mv")
    saw_unknown = False
    for alt in tgts.split(","):
        parts = alt.strip().split(".")
        base = parts[0]
        if base not in ("Card", "Spell") and base not in types:
            continue
        ok = True
        unknown = False
        for cond in parts[1:]:
            m = re.match(r"cmc(GE|LE|EQ)(\d+)$", cond)
            if m:
                if mv is None:
                    ok = False
                    break
                op, n = m.group(1), int(m.group(2))
                if (op == "GE" and mv < n) or (op == "LE" and mv > n) \
                        or (op == "EQ" and mv != n):
                    ok = False
                    break
                continue
            if cond.startswith("non"):
                word = cond[3:]
                if word in _COLOR_WORDS:
                    if _COLOR_WORDS[word] in profile["colors"]:
                        ok = False
                        break
                elif word in _TYPE_WORDS:
                    if word in types:
                        ok = False
                        break
                else:
                    unknown = True
                continue
            if cond in _COLOR_WORDS:
                if _COLOR_WORDS[cond] not in profile["colors"]:
                    ok = False
                    break
                continue
            if cond in _TYPE_WORDS:
                if cond not in types:
                    ok = False
                    break
                continue
            if cond in ("YouDontCtrl", "OppCtrl"):
                continue                       # true for an opposing spell
            unknown = True                     # e.g. Kicked, targetsYou
        if ok and not unknown:
            return True
        if ok and unknown:
            saw_unknown = True
    return None if saw_unknown else False


# restrictions that depend on game state at cast time, not on the card
_SITUATIONAL = {"attacking", "blocking", "blocked", "unblocked", "tapped",
                "untapped", "enchanted", "equipped", "attackedThisTurn",
                "attackingYou", "blockingOrBlockedBy", "wasDealtDamageThisTurn"}


def _battlefield_target_legal(tgts: str, profile: dict):
    """Can this removal spell's ValidTgts legally target the threat ON THE
    BATTLEFIELD? True/False/None. Colors and protection are checked by the
    caller; unknown restriction vocabulary degrades to None (conditional),
    never to a confident verdict."""
    types = profile.get("types") or ""
    type_words = set(types.split())
    kws = profile.get("keywords") or set()
    verdicts = []
    for alt in str(tgts).split(","):
        alt = alt.strip()
        if not alt:
            continue
        parts = alt.split(".", 1)
        base = parts[0]
        if base in ("Creature", "Artifact", "Enchantment", "Planeswalker",
                    "Land", "Battle"):
            if base not in type_words:
                verdicts.append(False)
                continue
        elif base not in ("Card", "Permanent", "Any"):
            verdicts.append(None)          # unknown head word
            continue
        ok = True
        # restrictions after the head are AND-joined with '+' (or '.')
        conds = re.split(r"[+.]", parts[1]) if len(parts) > 1 else []
        for cond in conds:
            m = re.match(r"(power|toughness|cmc)(GE|LE|EQ)(\d+)$", cond)
            if m:
                stat = {"power": profile.get("power"),
                        "toughness": profile.get("toughness"),
                        "cmc": profile.get("mv")}[m.group(1)]
                if stat is None:
                    ok = None if ok is not False else ok
                    continue
                op, n = m.group(2), int(m.group(3))
                if (op == "GE" and stat < n) or (op == "LE" and stat > n) \
                        or (op == "EQ" and stat != n):
                    ok = False
                    break
                continue
            if cond in _SITUATIONAL:
                ok = None if ok is not False else ok
                continue
            if cond == "withFlying":
                if "Flying" not in kws:
                    ok = False
                    break
                continue
            if cond == "withoutFlying":
                if "Flying" in kws:
                    ok = False
                    break
                continue
            if cond in ("nonToken", "YouDontCtrl", "OppCtrl"):
                continue                   # true for an opposing real card
            if cond == "YouCtrl":
                ok = False
                break
            if cond.startswith("non"):
                word = cond[3:]
                if word in _COLOR_WORDS:
                    continue               # colors checked by the caller
                if word in _TYPE_WORDS or word in ("Land", "Token"):
                    if word in type_words:
                        ok = False
                        break
                    continue
                ok = None if ok is not False else ok
                continue
            if cond in _COLOR_WORDS:
                continue                   # colors checked by the caller
            if cond in _TYPE_WORDS or (cond.isalpha() and cond[:1].isupper()):
                # card type, supertype, or subtype word (Zombie, Defender...)
                if cond in type_words or cond in kws:
                    continue
                if cond[:1].isupper() and cond in types:
                    continue
                # looks like a subtype the threat lacks - but unknown words
                # could be mechanic vocabulary, so degrade, don't exclude
                ok = None if ok is not False else ok
                continue
            ok = None if ok is not False else ok
        verdicts.append(ok)
    if True in verdicts:
        return True
    if None in verdicts:
        return None
    return False if verdicts else True


def evaluate_answer(klass: str, answer_rec: dict, node_params: dict,
                    profile: dict) -> dict:
    """Verdict for one answer card vs the threat. works: True/False/None
    (None = conditional); reasons are machine-readable strings."""
    reasons = []
    works = True

    if klass == "counter_spell":
        if profile.get("uncounterable"):
            return {"works": False,
                    "reasons": ["threat spell can't be countered"]}
        tgts = str(node_params.get("ValidTgts", "Card"))
        legal = _counter_target_legal(tgts, profile)
        if legal is False:
            return {"works": False,
                    "reasons": [f"targeting-illegal: counter hits only "
                                f"'{tgts}'"]}
        if legal is None:
            return {"works": None,
                    "reasons": [f"conditional: targeting restriction "
                                f"'{tgts}' not fully evaluated"]}
        if "UnlessCost" in node_params:
            return {"works": None,
                    "reasons": [f"soft counter: resolves unless controller "
                                f"pays {node_params['UnlessCost']}"]}
        return {"works": True,
                "reasons": ["counters the threat on the stack "
                            "(before any on-battlefield protection applies)"]}

    if klass in TARGETED:
        if profile["shroud"]:
            return {"works": False, "reasons": ["threat has shroud: can't be targeted"]}
        if profile["hexproof"]:
            return {"works": False,
                    "reasons": ["threat has hexproof: opponents can't target it"]}
        tgts = str(node_params.get("ValidTgts", ""))
        for c, word in (("W", "White"), ("U", "Blue"), ("B", "Black"),
                        ("R", "Red"), ("G", "Green")):
            if f"non{word}" in tgts and c in profile["colors"]:
                return {"works": False,
                        "reasons": [f"can only target non{word.lower()} - "
                                    f"threat is {word.lower()}"]}
        # positive color restriction ("Permanent.Red") the threat doesn't meet
        stripped = tgts
        for word in ("nonWhite", "nonBlue", "nonBlack", "nonRed", "nonGreen"):
            stripped = stripped.replace(word, "")
        for c, word in (("W", "White"), ("U", "Blue"), ("B", "Black"),
                        ("R", "Red"), ("G", "Green")):
            if word in stripped and c not in profile["colors"]:
                return {"works": False,
                        "reasons": [f"can only target {word.lower()} - "
                                    f"threat isn't {word.lower()}"]}
        shifters = [g for g in profile.get("self_statics", [])
                    if g.get("condition") == "PlayerTurn"
                    and (g["keywords"] or g["types"])]
        if shifters:
            # the card is a different object on each player's turn: evaluate
            # the targeting window per phase (Kaito: hexproof creature on the
            # controller's turn, plain planeswalker on yours)
            g = shifters[0]
            base_types = profile["types"]
            if g["removes_types"]:
                kept = [w for w in base_types.split()
                        if w not in ("Creature", "Artifact", "Enchantment",
                                     "Planeswalker", "Land", "Battle")]
                ctrl_types = " ".join(kept + g["types"])
            else:
                ctrl_types = base_types + " " + " ".join(g["types"])
            ctrl_prof = dict(profile, types=ctrl_types,
                             keywords=set(profile.get("keywords") or set())
                             | set(g["keywords"]))
            ctrl_open = _battlefield_target_legal(tgts, ctrl_prof)
            if {"Hexproof", "Shroud"} & set(g["keywords"]):
                ctrl_open = False
            your_open = _battlefield_target_legal(tgts, profile)
            grant_desc = " ".join(g["types"]) + (
                " with " + "/".join(g["keywords"]) if g["keywords"] else "")
            base_card_type = next(
                (w for w in base_types.split()
                 if w in ("Creature", "Artifact", "Enchantment",
                          "Planeswalker", "Land", "Battle")), base_types)
            if ctrl_open is False and your_open is False:
                return {"works": False, "reasons": [
                    f"no open targeting window: on its controller's turn it "
                    f"is a {grant_desc} (closed to '{tgts}'), on yours it is "
                    f"a {base_card_type} that '{tgts}' can't target"]}
            if your_open and ctrl_open is False:
                reasons.append(
                    f"timing: target it on YOUR turn only - on its "
                    f"controller's turn it is a {grant_desc}")
            elif ctrl_open and your_open is False:
                works = None
                reasons.append(
                    f"conditional: only targetable on its controller's turn, "
                    f"when it is a {grant_desc}")
        else:
            legal = _battlefield_target_legal(tgts, profile)
            if legal is False:
                return {"works": False,
                        "reasons": [f"targeting-illegal: hits only '{tgts}'"]}
            if legal is None:
                works = None
                reasons.append(f"conditional: targeting restriction '{tgts}' "
                               "not fully evaluated")
        if any(str(k).startswith("Condition") for k in node_params):
            works = None
            reasons.append("conditional: effect checks a condition on "
                           "resolution (not evaluated)")
        spell_colors = {c for c in (answer_rec.get("manaCost") or "")
                        if c in COLOR_LETTERS}
        if _protected_from_color(profile, spell_colors):
            return {"works": False,
                    "reasons": [f"threat protection blocks {''.join(sorted(spell_colors))} spell"]}
        if profile["ward"]:
            works = None
            reasons.append(f"conditional: must pay {profile['ward']}")

    if klass in ("destroy_target", "destroy_all") and profile["indestructible"]:
        return {"works": False, "reasons": ["threat is indestructible: destroy fails"]}

    if klass == "damage_target":
        if profile["indestructible"]:
            return {"works": False,
                    "reasons": ["threat is indestructible: lethal damage won't destroy it"]}
        dmg = _lit(node_params.get("NumDmg"))
        if profile["toughness"] is not None:
            if dmg is None:
                works = None
                reasons.append("conditional: damage amount is variable")
            elif dmg < profile["toughness"]:
                return {"works": False,
                        "reasons": [f"{dmg} damage < toughness {profile['toughness']}"]}
            else:
                reasons.append(f"{dmg} damage >= toughness {profile['toughness']}")

    if klass == "minus_toughness":
        shrink = _lit(str(node_params.get("NumDef", "")).lstrip("-"))
        if profile["toughness"] is not None and shrink is not None:
            if shrink < profile["toughness"]:
                return {"works": False,
                        "reasons": [f"-{shrink} toughness < {profile['toughness']}"]}
            reasons.append(f"-{shrink} toughness kills through indestructible")

    if klass in ("edict_sacrifice", "edict_sacrifice_mass"):
        sv = str(node_params.get("SacValid", ""))
        head = sv.split(".")[0] if sv else ""
        card_types = {"Creature", "Artifact", "Enchantment", "Planeswalker",
                      "Land", "Battle"}
        if head in card_types:
            base_has = head in (profile.get("types") or "")
            granted_has = any(head in g.get("types", [])
                              for g in profile.get("self_statics", []))
            if not base_has and not granted_has:
                return {"works": False,
                        "reasons": [f"this mode sacrifices a {head.lower()} - "
                                    "the threat never is one"]}
            if not base_has and granted_has:
                works = None
                reasons.append(f"conditional: only a {head.lower()} during "
                               "its controller's turn - resolve the edict then")
        works = None if works else works
        reasons.append("conditional: opponent chooses among their "
                       f"{head.lower() + 's' if head else 'permanents'}; "
                       "dodges hexproof/indestructible")
        if any(g.get("condition") for g in profile.get("self_statics", [])):
            reasons.append("never targets, so phase-shifting and "
                           "granted hexproof are irrelevant")

    if klass == "ability_removal":
        dep = profile.get("ability_dependent", ["removes abilities"])
        if "SetPower" in node_params or "SetToughness" in node_params:
            # e.g. Witness Protection: abilities gone but base P/T is set too,
            # so an ability-defined 0/0 survives at the new size instead of dying
            return {"works": None, "reasons": dep + [
                "conditional: also sets base power/toughness "
                f"({node_params.get('SetPower', '?')}/"
                f"{node_params.get('SetToughness', '?')}) - the token is "
                "neutralized but does not die"]}
        scope = str(node_params.get("Affected", ""))
        if "EnchantedBy" in scope or "AttachedBy" in scope:
            return {"works": True, "reasons": dep + [
                "single-target: only hits one token at a time"]}
        return {"works": True, "reasons": dep}

    if klass == "bounce_target" and works:
        reasons.append("temporary: returns to hand, not permanent removal")

    # recursive threats: death-based removal only rents the answer
    if profile.get("recursive") and works is True:
        if klass in ("destroy_target", "destroy_all", "damage_target",
                     "minus_toughness", "edict_sacrifice"):
            if "ReplaceDyingDefined" in node_params:
                reasons.append("exile rider: denies its return-from-death "
                               "trigger (would-die is replaced by exile)")
            else:
                works = None
                reasons.append("conditional: threat returns when it dies - "
                               "prefer an exile effect")
        elif klass == "exile_target":
            reasons.append("exile: denies its return-from-death trigger")

    return {"works": works, "reasons": reasons or ["no blocking ability found"]}


def _class_queries(profile: dict) -> dict:
    """Type-aware answer classes: a land threat needs land/permanent removal;
    creature-only classes (damage, -X/-X, edicts, creature sweepers) only
    apply to creatures."""
    import copy
    tgt_words = ["Permanent"]
    if profile["is_creature"]:
        tgt_words.append("Creature")
    if profile["is_land"]:
        tgt_words.append("Land")
    if "Planeswalker" in (profile.get("types") or ""):
        tgt_words.append("Planeswalker")
    # a phase-shifter's granted types open those target classes on-turn
    for g in profile.get("self_statics", []):
        for t in g.get("types", []):
            if t in ("Creature", "Artifact", "Enchantment") \
                    and t not in tgt_words:
                tgt_words.append(t)
    tgt = {"regex": "|".join(tgt_words)}
    queries = {}
    # a phase-shifter that becomes a creature (Kaito) is edict-able and,
    # as a planeswalker, sac-a-planeswalker-able: edicts never target, so
    # they apply to whatever the card is when the sacrifice resolves
    creaturish = profile["is_creature"] or any(
        "Creature" in g.get("types", [])
        for g in profile.get("self_statics", []))
    edictable = creaturish or "Planeswalker" in (profile.get("types") or "")
    for klass, q in ANSWER_QUERIES.items():
        creature_only = klass in ("damage_target", "minus_toughness",
                                  "edict_sacrifice", "destroy_all")
        if klass in ("edict_sacrifice", "edict_sacrifice_mass"):
            if not edictable:
                continue
        elif creature_only and not profile["is_creature"]:
            continue
        if klass == "counter_spell" and profile["is_land"]:
            continue                       # lands are played, never cast
        q2 = copy.deepcopy(q)
        params = q2["node"]["params"]
        for key in ("ValidTgts", "ValidCards"):
            if key in params:
                params[key] = tgt if not creature_only else params[key]
        queries[klass] = q2
    return queries


def answer_density(decklist: list[tuple[str, int]], answer_names: set[str],
                   threat_turn: int, iterations: int = 5000,
                   on_play: bool = False, seed: int = 11) -> dict:
    """Meta Lab x goldfish synthesis: the probability of actually HOLDING a
    working answer when the threat arrives. Deals the real list; draws 7 plus
    one per turn (on the draw by default - answering is reactive)."""
    import random
    pool = []
    for name, count in decklist:
        pool += [name] * count
    rng = random.Random(seed)
    turns = threat_turn + 2
    have_by_turn = [0] * (turns + 1)
    for _ in range(iterations):
        deck = pool[:]
        rng.shuffle(deck)
        for t in range(1, turns + 1):
            n_seen = 7 + t - (1 if on_play else 0)
            if any(c in answer_names for c in deck[:n_seen]):
                for tt in range(t, turns + 1):
                    have_by_turn[tt] += 1
                break
    n = float(iterations)
    return {"iterations": iterations, "threat_turn": threat_turn,
            "answers_in_deck": sorted(answer_names),
            "p_have_answer_by_turn": {t: round(100 * have_by_turn[t] / n, 1)
                                      for t in range(1, turns + 1)}}


def find_answers(idx, threat_rec: dict, colors: set[str] | None = None,
                 limit_per_class: int = 8, token_scripts: dict | None = None) -> dict:
    profile = threat_profile(threat_rec)
    out = {"threat": profile, "classes": {}}
    queries = _class_queries(profile)
    dep = ability_dependence(profile, token_scripts or {})
    if dep:
        queries["ability_removal"] = ABILITY_REMOVAL_QUERY
        profile["ability_dependent"] = dep
    for klass, query in queries.items():
        rows = []
        for hit in idx.search(query):
            rec = hit["record"]
            if rec["name"] == profile["name"]:
                continue
            if colors is not None:
                card_colors = {c for c in (rec.get("manaCost") or "")
                               if c in COLOR_LETTERS}
                if not card_colors <= colors:
                    continue
            qnode = query["node"]
            cand = [n for n in rec["nodes"]
                    if (qnode.get("api") is not None
                        and n.get("api") == qnode["api"])
                    or (qnode.get("api") is None and qnode.get("mode") is not None
                        and (n.get("mode") == qnode["mode"]
                             or (n.get("params") or {}).get("Mode") == qnode["mode"]))]
            # modal cards (Charms, Sheoldred's Edict) carry several nodes of
            # the same api: the card is as good as its BEST mode
            rank = {True: 0, None: 1, False: 2}
            verdict = min(
                (evaluate_answer(klass, rec, (n or {}).get("params", {}), profile)
                 for n in cand or [{}]),
                key=lambda v: rank[v["works"]])
            rows.append({"card": rec["name"], "manaCost": rec.get("manaCost"),
                         **verdict})
        rows.sort(key=lambda r: ({True: 0, None: 1, False: 2}[r["works"]],
                                 len(r.get("manaCost") or "zzzz"), r["card"]))
        out["classes"][klass] = {
            "total": len(rows),
            "working": sum(1 for r in rows if r["works"] is True),
            "top": rows[:limit_per_class],
        }
    return out
