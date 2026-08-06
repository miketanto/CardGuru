"""Draw a stratified, seeded sample from the frozen RulesGuru corpus for a
dev-probe evaluation run, and record the drawn IDs as BURNED (consumed):
burned questions are excluded from any future final benchmark scoring.

Held-out discipline: this script writes the sampled questions (text, cards,
official answers) to a work file consumed by evaluation agents. The
orchestrating developer reads only aggregate results, and no development
tuning may reference individual sampled questions.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = os.path.join(HERE, "rulesguru", "rulesguru_full.json")
FROZEN = os.path.join(HERE, "rulesguru", "FROZEN.sha256")
ADDR = os.path.join(ROOT, "research", "data", "rulesguru_addressability.json")
BURNED = os.path.join(HERE, "rulesguru_burned_ids.json")

STRATA = {"0": 4, "1": 8, "2": 6, "3": 4, "Corner Case": 2}   # n=24
SEED = 42


def main(out_path: str):
    want = open(FROZEN, encoding="utf-8").read().split()[0]
    h = hashlib.sha256(open(CORPUS, "rb").read()).hexdigest()
    if h != want:
        sys.exit("FROZEN.sha256 mismatch - refusing to sample")

    addr = {q["id"]: q for q in json.load(open(ADDR, encoding="utf-8"))["per_question"]}
    burned = set(json.load(open(BURNED, encoding="utf-8"))["ids"]) \
        if os.path.exists(BURNED) else set()

    questions = json.load(open(CORPUS, encoding="utf-8"))
    pools = {k: [] for k in STRATA}
    for q in questions:
        a = addr.get(q["id"])
        if not a or a["status"] != "engine_ready" or q["id"] in burned:
            continue
        lvl = str(q.get("level"))
        if lvl in pools:
            pools[lvl].append(q)

    rng = random.Random(SEED)
    sample = []
    for lvl, n in STRATA.items():
        pool = sorted(pools[lvl], key=lambda q: q["id"])
        sample += rng.sample(pool, min(n, len(pool)))

    work = [{
        "id": q["id"], "level": str(q.get("level")), "tags": q.get("tags"),
        "question": q.get("questionSimple"),
        "cards": [{"name": c["name"], "manaCost": c.get("manaCost"),
                   "type": c.get("type"), "text": c.get("rulesText") or c.get("text"),
                   "power": c.get("power"), "toughness": c.get("toughness")}
                  for c in q.get("includedCards") or []],
        "official_answer": q.get("answerSimple"),
        "cited_rules": q.get("citedRules"),
    } for q in sample]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(work, f, indent=1)
    ids = sorted(q["id"] for q in sample)
    json.dump({"note": "IDs consumed by dev-probe runs; excluded from final eval",
               "ids": sorted(burned | set(ids))},
              open(BURNED, "w", encoding="utf-8"), indent=1)
    by_level = {k: sum(1 for w in work if w["level"] == k) for k in STRATA}
    print(f"sampled {len(work)} engine-ready questions (levels: {by_level})")
    print(f"ids burned: {ids}")
    print(f"work file: {out_path}")


if __name__ == "__main__":
    main(sys.argv[1])
