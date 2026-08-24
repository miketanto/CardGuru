"""M2 kill criterion: rerun the adversarial slice against the oracle-derived graph.

research/graph-vs-flat-ablation.md pre-committed the test that decides whether
the ability-graph layer earns its complexity. This script reuses it to decide
something else: whether an *oracle-derived* graph is a genuine second derivation
of the same structure, or only a fallback for unscripted cards.

The queries are the ones the agent compiled for the original ablation
(research/data/ablation_adversarial.json), used verbatim. Nothing is rewritten
to suit the grammar -- if the oracle graph cannot answer the Forge-vocabulary
query, that is the finding.

Reported per question:
  witness found / foil rejected  -- the ablation's own pass criteria
  hits                           -- result-set size on each graph
  recall_of_forge_hits           -- |oracle ∩ forge| / |forge|, i.e. how much of
                                    the Forge-derived answer the grammar recovers
  jaccard                        -- set agreement between the two derivations

Usage:
    python3 research/scripts/m2_adversarial_rerun.py <forge.jsonl.gz> <oracle.jsonl.gz> [out.json]
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
sys.path.insert(0, os.path.abspath(ROOT))

from cardguru.index import SearchIndex  # noqa: E402

ABLATION = os.path.join(ROOT, "research", "data", "ablation_adversarial.json")
QUESTIONS = os.path.join(ROOT, "eval", "nl_questions_adversarial.json")


def hits(index: SearchIndex, query: dict) -> set[str]:
    out = set()
    for r in index.search(query):
        nm = r["record"].get("canonicalName") or r["record"].get("name")
        if nm:
            out.add(nm)
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    with open(ABLATION, encoding="utf-8") as f:
        ablation = json.load(f)
    with open(QUESTIONS, encoding="utf-8") as f:
        questions = {q["id"]: q for q in json.load(f)["questions"]}

    forge = SearchIndex.load(argv[1])
    oracle = SearchIndex.load(argv[2])

    rows = []
    for qid in sorted(ablation):
        spec = ablation[qid]
        q = spec.get("agent_query")
        meta = questions.get(qid, {})
        f_hits, o_hits = hits(forge, q), hits(oracle, q)
        witness = set(meta.get("witness") or [])
        foil = set(meta.get("absent") or [])
        inter = f_hits & o_hits
        rows.append({
            "id": qid,
            "question": meta.get("q"),
            "forge": {
                "hits": len(f_hits),
                "witness_found": bool(witness & f_hits),
                "foil_rejected": not (foil & f_hits),
            },
            "oracle": {
                "hits": len(o_hits),
                "witness_found": bool(witness & o_hits),
                "foil_rejected": not (foil & o_hits),
            },
            "recall_of_forge_hits_pct": round(100 * len(inter) / len(f_hits), 1)
            if f_hits else None,
            "jaccard_pct": round(100 * len(inter) / len(f_hits | o_hits), 1)
            if (f_hits | o_hits) else None,
        })

    passed = sum(1 for r in rows
                 if r["oracle"]["witness_found"] and r["oracle"]["foil_rejected"])
    report = {
        "questions": len(rows),
        "oracle_witness_and_foil_passed": passed,
        "forge_witness_and_foil_passed": sum(
            1 for r in rows
            if r["forge"]["witness_found"] and r["forge"]["foil_rejected"]),
        "rows": rows,
    }
    text = json.dumps(report, indent=1)
    print(text)
    if len(argv) > 3:
        with open(argv[3], "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\n-> {argv[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
