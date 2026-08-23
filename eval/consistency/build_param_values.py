"""Mine the VALUE space of each parameter, not just the parameter names.

The full-vocabulary fix told the compiler which parameter names exist. It still
had to guess what those parameters CONTAIN, so it fell back on `true` ("this key
exists") and loose `icontains` matches. That is the same failure one level down:
`{"ValidPlayers": true}` matches every mass-damage ability that touches players,
including "each player" effects, so "damage to each opponent" returned Anger of
the Gods.

A parameter is worth advertising when a handful of values covers most of its
uses — `Defined` has 279 distinct values but its top five cover 69%, and
`Destination` has 16 values covering 97%. Showing those lets the compiler anchor
exactly (`"Defined": "Player.Opponent"`) instead of substring-guessing.

Usage: python eval/consistency/build_param_values.py [--dataset PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cardguru.index import SearchIndex  # noqa: E402

MIN_USES = 200      # ignore long-tail parameters
TOP_K = 12          # values listed per parameter
MIN_COVERAGE = 0.55  # top-K must explain this share of uses to be worth listing
MAX_VALUE_LEN = 40   # skip free-text values (SpellDescription, Cost expressions)


def mine(records):
    vals = defaultdict(Counter)
    for rec in records:
        for n in rec["nodes"]:
            for k, v in (n.get("params") or {}).items():
                if isinstance(v, str) and 0 < len(v) <= MAX_VALUE_LEN:
                    vals[k][v] += 1

    out = {}
    for k, c in vals.items():
        total = sum(c.values())
        if total < MIN_USES:
            continue
        top = c.most_common(TOP_K)
        coverage = sum(n for _, n in top) / total
        if coverage < MIN_COVERAGE:
            continue
        out[k] = {"uses": total, "distinct": len(c),
                  "coverage": round(coverage, 3),
                  "values": [v for v, _ in top]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=os.environ.get("CARDGURU_DATASET",
                                                        "data/dataset.jsonl.gz"))
    ap.add_argument("--out", default="research/data/param_values.json")
    args = ap.parse_args(argv)

    idx = SearchIndex.load(args.dataset)
    out = mine(idx.records)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"pool": len(idx.records), "params": out}, f, indent=1)

    print(f"{len(out)} parameters have an enumerable value space -> {args.out}")
    for k in ("Defined", "Destination", "Origin", "ValidPlayers", "Event"):
        if k in out:
            d = out[k]
            print(f"  {k:14} {d['uses']:>6} uses, {d['distinct']:>4} distinct, "
                  f"top-{TOP_K} covers {d['coverage']*100:.0f}%")
            print(f"                 {', '.join(d['values'][:6])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
