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
    if "/" in pt:
        try:
            toughness = int(pt.split("/")[1])
        except ValueError:
            pass
    colors = {c for c in (rec.get("manaCost") or "") if c in COLOR_LETTERS}
    types = rec.get("types") or ""
    token_scripts = []
    for n in rec.get("nodes", []):
        ts = (n.get("params") or {}).get("TokenScript")
        if ts:
            token_scripts += [t.strip() for t in ts.split(",")]
    return {
        "name": rec.get("name"),
        "types": types,
        "is_creature": "Creature" in types,
        "is_land": "Land" in types,
        "pt_is_cda": "*" in pt,
        "token_scripts": token_scripts,
        "toughness": toughness,
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
    "bounce_target": {"node": {"api": "ChangeZone",
                               "params": {"Origin": "Battlefield",
                                          "Destination": "Hand",
                                          "ValidTgts": {"contains": "Creature"}}}},
    "destroy_all": {"node": {"api": "DestroyAll",
                             "params": {"ValidCards": {"contains": "Creature"}}}},
}

TARGETED = {"destroy_target", "exile_target", "damage_target", "minus_toughness",
            "bounce_target"}


def evaluate_answer(klass: str, answer_rec: dict, node_params: dict,
                    profile: dict) -> dict:
    """Verdict for one answer card vs the threat. works: True/False/None
    (None = conditional); reasons are machine-readable strings."""
    reasons = []
    works = True

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

    if klass == "edict_sacrifice":
        works = None if works else works
        reasons.append("conditional: opponent chooses; dodges hexproof/indestructible")

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
    tgt = {"regex": "|".join(tgt_words)}
    queries = {}
    for klass, q in ANSWER_QUERIES.items():
        creature_only = klass in ("damage_target", "minus_toughness",
                                  "edict_sacrifice", "destroy_all")
        if creature_only and not profile["is_creature"]:
            continue
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
            node = next(
                (n for n in rec["nodes"]
                 if (qnode.get("api") is not None
                     and n.get("api") == qnode["api"])
                 or (qnode.get("api") is None and qnode.get("mode") is not None
                     and (n.get("mode") == qnode["mode"]
                          or (n.get("params") or {}).get("Mode") == qnode["mode"]))),
                None)
            verdict = evaluate_answer(klass, rec, (node or {}).get("params", {}),
                                      profile)
            rows.append({"card": rec["name"], "manaCost": rec.get("manaCost"),
                         **verdict})
        rows.sort(key=lambda r: (r["works"] is not True, r["works"] is None,
                                 len(r.get("manaCost") or "zzzz"), r["card"]))
        out["classes"][klass] = {
            "total": len(rows),
            "working": sum(1 for r in rows if r["works"] is True),
            "top": rows[:limit_per_class],
        }
    return out
