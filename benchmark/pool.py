#!/usr/bin/env python3
"""Pool the result sets of several compiler runs, so goldens can be densified.

The eval set judges 145 cards across 37 questions — about four per question —
while the runs that produced those verdicts disagree about thousands more that
nobody has ever looked at. A question therefore passes or fails on three cards,
which is why one card flipping moves a whole question and why seed noise
swamps every intervention measured so far.

This is standard IR pooling (TREC): run several systems, take the union of what
they return, judge that pool, and treat unjudged cards as unjudged rather than
as negatives. Cards every system agrees on carry no information about which
system is better; the CONTESTED band — returned by some systems and not others
— is where the measurement resolution actually lives, and it is what this
writes out for adjudication.

    python benchmark/pool.py benchmark/agent_runs/*_s*.json --out benchmark/pool.json

Deliberately NOT recorded in the pool file: which system returned a card, and
how many did. An adjudicator who can see the vote count ratifies the majority
instead of reading the card, and the pool would then only ever confirm what the
current compiler already does.
"""
import argparse
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru import evalset  # noqa: E402
from cardguru.index import SearchIndex  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.environ.get("CARDGURU_DATASET",
                         os.path.join(HERE, "..", "data", "dataset.jsonl.gz"))


def run_query(index, query):
    if query is None:
        return None
    try:
        return {h["record"]["name"] for h in index.search(query)}
    except Exception:
        return None


def build(index, questions, reference, run_paths):
    systems = {}
    for p in run_paths:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        name = os.path.splitext(os.path.basename(p))[0]
        systems[name] = {r["id"]: r.get("query") for r in data["rows"]}

    out = {}
    for q in questions:
        qid = q["id"]
        if not evalset.is_scorable(q):
            continue
        sets = []
        for name, queries in systems.items():
            hits = run_query(index, queries.get(qid))
            if hits is not None:
                sets.append(hits)
        ref_hits = run_query(index, reference.get(qid, {}).get("query"))
        if ref_hits is not None:
            sets.append(ref_hits)
        if not sets:
            continue

        votes = Counter()
        for s in sets:
            votes.update(s)
        n = len(sets)
        judged = set(q.get("expect_present") or []) | set(q.get("expect_absent") or [])

        # Unanimous cards tell us nothing about which system is better; a card
        # only one system returned is usually that system misfiring rather than
        # a real candidate, and adjudicating thousands of them is how this
        # exercise turns into a month. The contested band is the useful middle.
        contested = sorted(c for c, v in votes.items()
                           if 1 < v < n and c not in judged)
        singleton = sorted(c for c, v in votes.items()
                           if v == 1 and c not in judged)
        unanimous = sorted(c for c, v in votes.items()
                           if v == n and c not in judged)
        out[qid] = {
            "systems": n,
            "union": len(votes),
            "already_judged": sorted(judged),
            "contested": contested,
            "n_singleton": len(singleton),
            "n_unanimous_unjudged": len(unanimous),
            "unanimous_unjudged": unanimous,
        }
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+")
    p.add_argument("--out", default=os.path.join(HERE, "pool.json"))
    p.add_argument("--dataset", default=DATASET)
    args = p.parse_args()

    index = SearchIndex.load(args.dataset)
    questions = evalset.load_questions()
    reference = evalset.load_reference()
    pool = build(index, questions, reference, args.runs)

    print(f"{'question':<36} {'sys':>4} {'union':>7} {'contested':>10} "
          f"{'single':>7} {'unan.new':>9}")
    tc = ts = tu = 0
    for qid in sorted(pool):
        e = pool[qid]
        tc += len(e["contested"]); ts += e["n_singleton"]
        tu += e["n_unanimous_unjudged"]
        print(f"{qid:<36} {e['systems']:>4} {e['union']:>7} "
              f"{len(e['contested']):>10} {e['n_singleton']:>7} "
              f"{e['n_unanimous_unjudged']:>9}")
    print(f"\ncontested (the adjudication job) : {tc}")
    print(f"singleton (one system only)      : {ts}  -- not adjudicated")
    print(f"unanimous but unjudged           : {tu}  -- cheap consensus goldens")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(pool, f, indent=1)
    print(f"\nwrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
