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
    return {
        "name": rec.get("name"),
        "types": rec.get("types") or "",
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


ANSWER_QUERIES = {
    "destroy_target": {"node": {"api": "Destroy",
                                "params": {"ValidTgts": {"contains": "Creature"}}}},
    "exile_target": {"node": {"api": "ChangeZone",
                              "params": {"Origin": "Battlefield",
                                         "Destination": "Exile",
                                         "ValidTgts": {"contains": "Creature"}}}},
    "damage_target": {"node": {"api": "DealDamage",
                               "params": {"ValidTgts": {"contains": "Creature"}}}},
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

    if klass == "bounce_target" and works:
        reasons.append("temporary: returns to hand, not permanent removal")

    return {"works": works, "reasons": reasons or ["no blocking ability found"]}


def find_answers(idx, threat_rec: dict, colors: set[str] | None = None,
                 limit_per_class: int = 8) -> dict:
    profile = threat_profile(threat_rec)
    out = {"threat": profile, "classes": {}}
    for klass, query in ANSWER_QUERIES.items():
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
            node = next((n for n in rec["nodes"]
                         if n.get("api") == query["node"]["api"]), None)
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
