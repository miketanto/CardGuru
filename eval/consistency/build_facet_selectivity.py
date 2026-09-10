"""Mine how many card faces each hook/role facet actually matches.

`build_system_prompt` annotates every advertised facet with this count, because
the names badly understate their breadth. `reanimator` reads like a precise
"graveyard -> battlefield" predicate; it matches 1,227 faces including
graveyard-to-HAND cards, 15x the precise node query. Advertising the facets
without their selectivity measurably regressed precision on the consistency
benchmark (eval/consistency/C0-v2-results.md).

Single pass over the pool — detect every facet per record, rather than one full
scan per facet, which is ~50x slower and times out.

Usage: python eval/consistency/build_facet_selectivity.py [--dataset PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cardguru.deck import detect_roles          # noqa: E402
from cardguru.index import SearchIndex          # noqa: E402
from cardguru.recommend import HOOKS, detect_hooks  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=os.environ.get("CARDGURU_DATASET",
                                                        "data/dataset.jsonl.gz"))
    ap.add_argument("--out", default="research/data/facet_selectivity.json")
    args = ap.parse_args(argv)

    idx = SearchIndex.load(args.dataset)
    hooks = {h: 0 for h in HOOKS}
    roles: dict[str, int] = {}
    for rec in idx.records:
        for h in detect_hooks(rec):
            if h in hooks:
                hooks[h] += 1
        for role, kind in (detect_roles(rec) or {}).items():
            roles[role] = roles.get(role, 0) + 1
            roles[f"{role}:{kind}"] = roles.get(f"{role}:{kind}", 0) + 1

    out = {"pool": len(idx.records), "hooks": hooks, "roles": roles}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)

    top = sorted(hooks.items(), key=lambda t: -t[1])
    print(f"pool {out['pool']} faces -> {args.out}")
    print("broadest facets:")
    for h, c in top[:5]:
        print(f"  {h:28} {c:>6}  {c / out['pool'] * 100:>5.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
