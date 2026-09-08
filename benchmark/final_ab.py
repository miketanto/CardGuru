#!/usr/bin/env python3
"""The powered families A/B: 7 seeds per arm, scored on the pooled goldens.

`research/families.md` measured the intervention at 3 seeds and could not call
it. `research/benchmark-density.md` then showed the benchmark itself was the
limit and put a number on the fix: 7 seeds per arm. This runs that test.

Two things are done differently from `ab_families.py`:

* **An exact permutation test, not a t-test.** With 7+7 seeds there are only
  C(14,7)=3432 relabelings, so the null distribution can be enumerated
  completely. That needs no normality assumption, which is worth having when
  n=7 and the arm distributions are visibly skewed.

* **A pool-coverage check.** The dense goldens were adjudicated from a pool
  built out of six runs. The eight added here did not contribute to it, so
  cards they find that nobody judged are invisible. That is the standard TREC
  pool-bias problem and it can only be waved away if it lands on both arms
  equally — so it is measured rather than assumed.

    python benchmark/final_ab.py --questions benchmark/candidate_questions.dense.json
"""
import argparse
import itertools
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import evalset  # noqa: E402
from cardguru.index import SearchIndex  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.environ.get("CARDGURU_DATASET",
                         os.path.join(HERE, "..", "data", "dataset.jsonl.gz"))
SEEDS = (1, 2, 3, 4, 5, 6, 7)


def permutation_p(a, b):
    """Exact two-sided p for a difference in means, over every relabeling."""
    obs = abs(statistics.mean(b) - statistics.mean(a))
    pool = list(a) + list(b)
    n = len(a)
    hits = total = 0
    for combo in itertools.combinations(range(len(pool)), n):
        left = [pool[i] for i in combo]
        right = [pool[i] for i in range(len(pool)) if i not in combo]
        total += 1
        if abs(statistics.mean(right) - statistics.mean(left)) >= obs - 1e-12:
            hits += 1
    return hits / total


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--questions", required=True)
    p.add_argument("--dataset", default=DATASET)
    p.add_argument("--json-out", default=None)
    args = p.parse_args()

    index = SearchIndex.load(args.dataset)
    questions = evalset.load_questions(args.questions)
    qs = {q["id"]: q for q in questions if evalset.is_scorable(q)}
    judged = {qid: set(q.get("expect_present") or [])
              | set(q.get("expect_absent") or [])
              | set(q.get("unclear") or []) for qid, q in qs.items()}

    arms = {"control": [f"off_s{s}" for s in SEEDS],
            "families": [f"fam2_s{s}" for s in SEEDS]}

    recall, passed, coverage, per_q = {}, {}, {}, {}
    for arm, runs in arms.items():
        for name in runs:
            path = os.path.join(HERE, "agent_runs", f"{name}.json")
            with open(path, encoding="utf-8") as f:
                rows = json.load(f)["rows"]
            queries = {r["id"]: r.get("query") for r in rows}
            scored, unjudged, returned = [], 0, 0
            for qid, q in qs.items():
                query = queries.get(qid)
                try:
                    hits = ({h["record"]["name"] for h in index.search(query)}
                            if query is not None else set())
                    ok = query is not None
                except Exception:
                    hits, ok = set(), False
                returned += len(hits)
                unjudged += len(hits - judged[qid])
                row = evalset.score_one(q, hits, compiled=ok)
                scored.append(row)
                per_q.setdefault(qid, {}).setdefault(arm, []).append(row["passed"])
            agg = evalset.aggregate(scored)
            recall.setdefault(arm, []).append(agg["recall"])
            passed.setdefault(arm, []).append(agg["passed"])
            coverage[name] = 1 - (unjudged / returned) if returned else 1.0

    print(f"=== POOL COVERAGE (fraction of returned cards that are judged)")
    for arm, runs in arms.items():
        cov = [coverage[n] for n in runs]
        contributed = "contributed to pool" if True else ""
        print(f"  {arm:<9} {[f'{c*100:.1f}' for c in cov]}   "
              f"mean {statistics.mean(cov)*100:.1f}%")
    gap_cov = abs(statistics.mean([coverage[n] for n in arms['families']])
                  - statistics.mean([coverage[n] for n in arms['control']]))
    print(f"  arm difference {gap_cov*100:.1f}pp "
          f"-- pool bias is only benign if this is small")

    print(f"\n=== RESULTS ({len(SEEDS)} seeds per arm, "
          f"{os.path.basename(args.questions)})")
    out = {}
    for metric, data in (("golden recall", recall), ("questions passed", passed)):
        a, b = data["control"], data["families"]
        pv = permutation_p(a, b)
        scale = 100 if metric == "golden recall" else 1
        unit = "pp" if metric == "golden recall" else " questions"
        print(f"\n  {metric}")
        print(f"    control   mean {statistics.mean(a)*scale:6.2f}   "
              f"sd {statistics.stdev(a)*scale:5.2f}   "
              f"{[round(x*scale,1) for x in a]}")
        print(f"    families  mean {statistics.mean(b)*scale:6.2f}   "
              f"sd {statistics.stdev(b)*scale:5.2f}   "
              f"{[round(x*scale,1) for x in b]}")
        print(f"    gap {(statistics.mean(b)-statistics.mean(a))*scale:+.2f}{unit}"
              f"   exact permutation p = {pv:.4f}"
              f"   {'SIGNIFICANT' if pv < 0.05 else 'not significant'} at 0.05")
        out[metric] = {"control": a, "families": b, "p": pv}

    print(f"\n=== PER-QUESTION (pass rate out of {len(SEEDS)} seeds)")
    moved = []
    for qid, arms_q in sorted(per_q.items()):
        c = sum(arms_q["control"]); f = sum(arms_q["families"])
        if c != f:
            moved.append((f - c, qid, c, f))
    for d, qid, c, f in sorted(moved, key=lambda t: -t[0]):
        print(f"  {d:+d}  {qid:<36} control {c}/7  families {f}/7")
    if not moved:
        print("  (no question changed its pass count)")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"metrics": out, "coverage": coverage,
                       "per_question": {k: v for k, v in per_q.items()}},
                      f, indent=1)
        print(f"\nwrote {args.json_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
