"""E2 feature extractor: CardGuru Forge graph -> per-card mechanical
feature vectors for the RL encoder ablation (TASKC-SPEC.md).

Emits a TSV (first line = dim, then "<card name>\t<v1,v2,...>") consumed
by StateEncoder via -Drl.cardFeatures. Every feature is a pure readout
of the ability graph - no text embeddings, no learned components - so
the E0-vs-E2 ablation isolates the graph's contribution.

Multi-face cards (transform/Room/MDFC): faces are separate dataset
records sharing "file"; features are the UNION across faces, registered
under every face name plus the "A // B" joined name (XMage reports Rooms
either way). Tokens are not cards and stay unknown-flagged - documented.

Run: python3 rl/e2_extract.py [--out rl/e2_features.tsv]
"""
import argparse
import gzip
import json
import re
from collections import defaultdict

from cardguru.answers import ANSWER_QUERIES, threat_profile
from cardguru.querydsl import CardGraph, evaluate

DATASET = "/home/user/CardGuru/data/dataset.jsonl.gz"

ANSWER_KEYS = sorted(ANSWER_QUERIES)          # 9 answer classes
EFFECT_APIS = ["DealDamage", "Counter", "Destroy", "ChangeZone", "Pump",
               "Draw", "Discard", "Token", "PutCounter", "GainLife",
               "LoseLife", "Sacrifice", "Mill", "Scry", "Mana",
               "DestroyAll", "DamageAll", "PumpAll", "Animate", "Dig"]
KEYWORDS = ["Flying", "Haste", "Deathtouch", "Lifelink", "First Strike",
            "Double Strike", "Trample", "Vigilance", "Flash", "Menace",
            "Reach", "Defender", "Ward", "Hexproof", "Shroud",
            "Protection", "Prowess", "Ninjutsu"]

FEATURES = (
    ["ans_" + k for k in ANSWER_KEYS]
    + ["api_" + a for a in EFFECT_APIS]
    + ["kw_" + k.lower().replace(" ", "_") for k in KEYWORDS]
    + ["trig_etb", "trig_death", "trig_attacks", "trig_spellcast",
       "trig_damage", "trig_phase",
       "has_static", "has_replacement", "has_activated",
       "tgt_creature", "tgt_player_or_any", "tgt_spell",
       "num_dmg", "pump_att_pos", "pump_def_neg",
       "type_land", "type_planeswalker", "type_enchantment",
       "type_artifact", "recursive", "multi_face"]
)
DIM = len(FEATURES)
IDX = {f: i for i, f in enumerate(FEATURES)}


def face_vector(rec):
    v = [0.0] * DIM
    g = CardGraph(rec)
    for k in ANSWER_KEYS:
        ok, _ = evaluate(ANSWER_QUERIES[k], g)
        if ok:
            v[IDX["ans_" + k]] = 1.0
    kws = set()
    for n in rec.get("nodes", []):
        kind = n.get("kind")
        p = n.get("params") or {}
        api = n.get("api")
        if api in EFFECT_APIS:
            v[IDX["api_" + api]] = 1.0
        if kind == "K":
            kws.add((n.get("raw") or n.get("keyword") or "").split(":")[0].strip())
        if kind == "A":
            v[IDX["has_activated"]] = 1.0
        if kind == "S":
            v[IDX["has_static"]] = 1.0
        if kind == "R":
            v[IDX["has_replacement"]] = 1.0
        if kind == "T":
            mode = p.get("Mode") or n.get("mode")
            if mode == "ChangesZone":
                if p.get("Destination") == "Battlefield":
                    v[IDX["trig_etb"]] = 1.0
                if p.get("Origin") == "Battlefield" \
                        and p.get("Destination") == "Graveyard":
                    v[IDX["trig_death"]] = 1.0
            elif mode == "Attacks":
                v[IDX["trig_attacks"]] = 1.0
            elif mode == "SpellCast":
                v[IDX["trig_spellcast"]] = 1.0
            elif mode in ("DamageDone", "DamageDoneOnce"):
                v[IDX["trig_damage"]] = 1.0
            elif mode == "Phase":
                v[IDX["trig_phase"]] = 1.0
        tgts = str(p.get("ValidTgts") or "")
        if "Creature" in tgts:
            v[IDX["tgt_creature"]] = 1.0
        if "Player" in tgts or "Any" in tgts or "Opponent" in tgts:
            v[IDX["tgt_player_or_any"]] = 1.0
        if "Spell" in str(p.get("TargetType") or "") or api == "Counter":
            v[IDX["tgt_spell"]] = 1.0
        if p.get("NumDmg"):
            try:
                v[IDX["num_dmg"]] = max(v[IDX["num_dmg"]],
                                        min(float(p["NumDmg"]), 6.0) / 6.0)
            except ValueError:
                v[IDX["num_dmg"]] = 0.5      # X or SVar-driven damage
        if api in ("Pump", "PumpAll"):
            att, deff = str(p.get("NumAtt") or ""), str(p.get("NumDef") or "")
            if att.startswith("+") or re.match(r"^\d", att):
                v[IDX["pump_att_pos"]] = 1.0
            if deff.startswith("-"):
                v[IDX["pump_def_neg"]] = 1.0
    for k in KEYWORDS:
        if k in kws:
            v[IDX["kw_" + k.lower().replace(" ", "_")]] = 1.0
    types = rec.get("types") or ""
    for t, f in [("Land", "type_land"), ("Planeswalker", "type_planeswalker"),
                 ("Enchantment", "type_enchantment"), ("Artifact", "type_artifact")]:
        if t in types:
            v[IDX["type_" + f.split("_", 1)[1]]] = 1.0
    try:
        if threat_profile(rec).get("recursive"):
            v[IDX["recursive"]] = 1.0
    except Exception:
        pass
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/home/user/CardGuru/rl/e2_features.tsv")
    args = ap.parse_args()

    by_file = defaultdict(list)
    with gzip.open(DATASET, "rt", encoding="utf-8") as f:
        f.readline()                    # meta
        for line in f:
            rec = json.loads(line)
            by_file[rec.get("file") or rec["name"]].append(rec)

    rows = {}
    for faces in by_file.values():
        faces.sort(key=lambda r: r.get("faceIndex") or 0)
        vecs = [face_vector(r) for r in faces]
        union = [max(col) for col in zip(*vecs)]
        if len(faces) > 1:
            union[IDX["multi_face"]] = 1.0
        for r in faces:
            rows[r["name"]] = union
        if len(faces) > 1:
            rows[" // ".join(r["name"] for r in faces)] = union

    with open(args.out, "w", encoding="utf-8") as out:
        out.write(f"{DIM}\n")
        for name in sorted(rows):
            out.write(name + "\t"
                      + ",".join("%g" % x for x in rows[name]) + "\n")
    nz = sum(1 for v in rows.values() if any(v))
    print(f"wrote {len(rows)} names dim={DIM} nonzero={nz} -> {args.out}")


if __name__ == "__main__":
    main()
