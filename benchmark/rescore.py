#!/usr/bin/env python3
"""Re-score finished runs under a different golden set, to measure the
BENCHMARK rather than the compiler.

The queries are already on disk, so swapping the goldens and re-executing costs
nothing and changes only the instrument. That is the whole point: if densified
goldens are worth the adjudication, the same six runs must become easier to
tell apart afterwards.

    python benchmark/rescore.py benchmark/agent_runs/*_s*.json \\
        --questions benchmark/candidate_questions.dense.json \\
        --baseline  benchmark/candidate_questions.json

What it reports, and why each number is the one that matters:

  discrimination  questions whose verdict is not identical across every run.
                  A question all runs pass, or all runs fail, contributes
                  nothing to a comparison no matter how many seeds are added.
                  Note this is computed on the all-or-nothing pass metric, so
                  it gets WORSE as goldens are added: needing 8 of 8 cards is
                  strictly harder than 3 of 3. Read it as dynamic range of the
                  pass metric, not as instrument quality.
  recall sd       spread of golden recall across seeds within an arm.
  SEEDS NEEDED    the headline. Seeds per arm required for the observed
                  arm-to-arm gap to clear ~2.8 x sd x sqrt(2/n). Raw sd is the
                  wrong figure of merit on its own: a golden set that doubles
                  both the signal and the noise leaves this unchanged, and one
                  that triples the signal while doubling the noise improves it
                  even though sd went UP. Fewer seeds is a better instrument.
"""
import argparse
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


def hits_for(index, query):
    if query is None:
        return set(), False
    try:
        return {h["record"]["name"] for h in index.search(query)}, True
    except Exception:
        return set(), False


def score(index, runs, questions):
    qs = {q["id"]: q for q in questions}
    out = {}
    for name, queries in runs.items():
        rows = []
        for qid, query in queries.items():
            q = qs.get(qid)
            if q is None or not evalset.is_scorable(q):
                continue
            hits, ok = hits_for(index, query)
            rows.append(evalset.score_one(q, hits, compiled=ok))
        out[name] = rows
    return out


def report(label, scored):
    per_q = {}
    recalls, passes = [], []
    for name, rows in sorted(scored.items()):
        agg = evalset.aggregate(rows)
        recalls.append((name, agg["recall"]))
        passes.append((name, agg["passed"]))
        for r in rows:
            per_q.setdefault(r["id"], []).append(r["passed"])

    n_q = len(per_q)
    discriminating = [q for q, v in per_q.items() if len(set(v)) > 1]
    always_pass = [q for q, v in per_q.items() if all(v)]
    always_fail = [q for q, v in per_q.items() if not any(v)]

    arms = {}
    for name, rec in recalls:
        arms.setdefault("families" if name.startswith("fam") else "control",
                        []).append(rec)

    print(f"\n===== {label}")
    print(f"  scorable questions   {n_q}")
    print(f"  golden cards         "
          f"{sum(r['present_total'] for r in next(iter(scored.values())))} present")
    print(f"  DISCRIMINATING       {len(discriminating)} "
          f"({len(discriminating)/n_q*100:.0f}% of questions)   "
          f"always-pass {len(always_pass)}  always-fail {len(always_fail)}")
    for arm, rs in sorted(arms.items()):
        sd = statistics.stdev(rs) if len(rs) > 1 else 0.0
        print(f"  {arm:<9} recall {statistics.mean(rs)*100:>5.1f}%  "
              f"seeds {[f'{r*100:.1f}' for r in rs]}  sd {sd*100:.2f}pp")

    need = float("nan")
    if len(arms) == 2 and all(len(v) > 1 for v in arms.values()):
        (a1, r1), (a2, r2) = sorted(arms.items())
        gap = abs(statistics.mean(r2) - statistics.mean(r1))
        pooled = math.sqrt((statistics.variance(r1) + statistics.variance(r2)) / 2)
        # smallest n with 2.8 * pooled * sqrt(2/n) <= gap
        need = 2 * (2.8 * pooled / gap) ** 2 if gap else float("inf")
        print(f"  arm gap    {gap*100:+.1f}pp   pooled sd {pooled*100:.2f}pp")
        print(f"  SEEDS NEEDED PER ARM to call it: {math.ceil(need):>3}"
              f"   (have {len(r1)})")
    return {"discriminating": len(discriminating), "n_q": n_q,
            "arms": {a: [r for r in rs] for a, rs in arms.items()},
            "seeds_needed": need,
            "discriminating_ids": sorted(discriminating)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+")
    p.add_argument("--questions", required=True)
    p.add_argument("--baseline", default=None,
                   help="second golden set to compare against")
    p.add_argument("--dataset", default=DATASET)
    args = p.parse_args()

    index = SearchIndex.load(args.dataset)
    runs = {}
    for path in args.runs:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        runs[os.path.splitext(os.path.basename(path))[0]] = {
            r["id"]: r.get("query") for r in data["rows"]}

    results = {}
    if args.baseline:
        results["baseline"] = report(
            f"BASELINE goldens  ({os.path.basename(args.baseline)})",
            score(index, runs, evalset.load_questions(args.baseline)))
    results["dense"] = report(
        f"DENSE goldens  ({os.path.basename(args.questions)})",
        score(index, runs, evalset.load_questions(args.questions)))

    if "baseline" in results:
        b, d = results["baseline"], results["dense"]
        print(f"\n===== instrument delta")
        print(f"  discriminating questions  {b['discriminating']} -> "
              f"{d['discriminating']}  ({d['discriminating']-b['discriminating']:+d})")
        for arm in sorted(d["arms"]):
            if len(d["arms"][arm]) < 2:
                continue
            sb = statistics.stdev(b["arms"][arm]) * 100
            sd_ = statistics.stdev(d["arms"][arm]) * 100
            print(f"  {arm:<9} recall sd {sb:.2f}pp -> {sd_:.2f}pp")
        print(f"  SEEDS NEEDED PER ARM   {math.ceil(b['seeds_needed']):>3} -> "
              f"{math.ceil(d['seeds_needed']):>3}"
              f"   <- the figure of merit")
        gained = set(d["discriminating_ids"]) - set(b["discriminating_ids"])
        lost = set(b["discriminating_ids"]) - set(d["discriminating_ids"])
        if gained:
            print(f"  newly discriminating: {sorted(gained)}")
        if lost:
            print(f"  no longer discriminating: {sorted(lost)}")


if __name__ == "__main__":
    main()
