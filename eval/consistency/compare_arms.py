"""Compare C3 ablation arms against the C0 baseline.

Arms (identical questions, identical harness, one variable — the prompt's vocabulary):
  baseline  param_keys[:100], frequency-ranked          (production today)
  B         all 1,206 param keys                        (visibility hypothesis)
  C         param_keys[:100] + mined per-API param table (disambiguation hypothesis)

Beyond PC/agreement, this reports DEAD-BRANCH RATE: the fraction of leaf subqueries
that match nothing on their own. That metric exists because of the I11 dissection —
a wrong param name inside an {"any": [...]} makes its branch match zero cards while
the sibling branch carries the result, so the query validates, returns plenty of
hits, finds the witness, and is still silently broken. No signal the compiler
currently has can see it; this one can.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cardguru.index import SearchIndex          # noqa: E402
from cardguru.querydsl import CardGraph, evaluate  # noqa: E402


def leaves(q):
    """Yield leaf subqueries (node/chain/keyword/card) of a query tree."""
    if not isinstance(q, dict) or len(q) != 1:
        return
    (op, arg), = q.items()
    if op in ("all", "any"):
        for sub in (arg or []):
            yield from leaves(sub)
    elif op == "not":
        yield from leaves(arg)
    else:
        yield q


def run(idx, q):
    try:
        return {i for i in idx.candidates(q) if evaluate(q, CardGraph(idx.records[i]))[0]}
    except Exception:
        return None


def arm_stats(idx, path, witness_map):
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    n_leaf = n_dead = 0
    per_intent = {}
    for r in rows:
        q = r.get("query")
        if q is None:
            continue
        iid = r["qid"].split(".")[0]
        for leaf in leaves(q):
            hits = run(idx, leaf)
            if hits is None:
                continue
            n_leaf += 1
            if not hits:
                n_dead += 1
        full = run(idx, q)
        if full is None:
            continue
        w = witness_map.get(iid) or set()
        per_intent.setdefault(iid, []).append(
            {"size": len(full), "witness": bool(full & w) if w else None, "set": full})
    return {"rows": len(rows), "leaves": n_leaf, "dead": n_dead,
            "dead_rate": (n_dead / n_leaf) if n_leaf else None,
            "per_intent": per_intent}


def jac(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 1.0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/dataset.jsonl.gz")
    ap.add_argument("--intents", default="eval/nl_consistency_intents.json")
    ap.add_argument("--arms", nargs="+", required=True,
                    help="NAME=path/to/recorded.jsonl")
    args = ap.parse_args(argv)

    idx = SearchIndex.load(args.dataset)
    names = {}
    for i, r in enumerate(idx.records):
        names.setdefault((r.get("name") or "").strip().lower(), set()).add(i)
    spec = json.load(open(args.intents, encoding="utf-8"))
    wmap = {it["id"]: {j for c in (it.get("witness") or [])
                       for j in names.get(c.strip().lower(), set())}
            for it in spec["intents"]}

    print(f"{'arm':10}{'rows':>6}{'leaves':>8}{'dead':>6}{'dead%':>8}"
          f"{'PC':>8}{'agree@wit':>11}")
    for a in args.arms:
        name, path = a.split("=", 1)
        st = arm_stats(idx, path, wmap)
        pcs, ags = [], []
        for iid, entries in st["per_intent"].items():
            sets = [e["set"] for e in entries]
            if len(sets) >= 2:
                vals = [jac(sets[i], sets[j])
                        for i in range(len(sets)) for j in range(i + 1, len(sets))]
                pcs.append(sum(vals) / len(vals))
            ws = [e["witness"] for e in entries if e["witness"] is not None]
            if ws:
                ags.append(sum(ws) / len(ws))
        pc = sum(pcs) / len(pcs) if pcs else float("nan")
        ag = sum(ags) / len(ags) if ags else float("nan")
        print(f"{name:10}{st['rows']:>6}{st['leaves']:>8}{st['dead']:>6}"
              f"{st['dead_rate']*100:>7.1f}%{pc:>8.3f}{ag:>11.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
