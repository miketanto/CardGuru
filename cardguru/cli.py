"""CardGuru CLI.

  python -m cardguru build  --cardsfolder PATH [--canonical INDEX.json] [--pin SHA] [--out data/dataset.jsonl.gz]
  python -m cardguru search QUERY.json [--dataset PATH] [--limit N] [--explain] [--json]
  python -m cardguru show   "Card Name" [--dataset PATH]
  python -m cardguru stats  [--dataset PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from . import dataset as ds
from .index import SearchIndex, explain

DEFAULT_DATASET = "data/dataset.jsonl.gz"


def cmd_build(args):
    t0 = time.time()
    stats = ds.build(args.cardsfolder, args.out, canonical_index=args.canonical,
                     source_pin=args.pin)
    stats["seconds"] = round(time.time() - t0, 1)
    print(json.dumps(stats, indent=1))


def cmd_search(args):
    with open(args.query, encoding="utf-8") as f:
        spec = json.load(f)
    query = spec["query"] if isinstance(spec, dict) and "query" in spec else spec
    t0 = time.time()
    idx = SearchIndex.load(args.dataset)
    t_load = time.time() - t0
    t0 = time.time()
    hits = list(idx.search(query, limit=args.limit))
    t_search = time.time() - t0
    if args.json:
        out = [{"name": h["record"]["name"], "evidence": h["evidence"]} for h in hits]
        json.dump(out, sys.stdout, indent=1)
        print()
    else:
        if isinstance(spec, dict) and spec.get("description"):
            print(f"# {spec['description']}")
        for h in hits:
            rec = h["record"]
            print(f"{rec['name']}  [{rec.get('types','')}]")
            if args.explain:
                for line in explain(rec, h["evidence"]):
                    print(f"    {line}")
        print(f"-- {len(hits)} faces matched "
              f"(load {t_load:.1f}s, search {t_search:.2f}s)", file=sys.stderr)


def cmd_show(args):
    idx = SearchIndex.load(args.dataset)
    name = args.name.lower()
    for rec in idx.records:
        if (rec.get("name") or "").lower() == name:
            json.dump(rec, sys.stdout, indent=1)
            print()
            return
    print(f"not found: {args.name}", file=sys.stderr)
    sys.exit(1)


def cmd_stats(args):
    idx = SearchIndex.load(args.dataset)
    recs = idx.records
    n_matched = sum(1 for r in recs if r.get("canonicalName"))
    print(json.dumps({
        "meta": getattr(idx, "meta", {}),
        "faces": len(recs),
        "canonical_matched": n_matched,
        "postings_tokens": len(idx.postings),
    }, indent=1))


def main(argv=None):
    p = argparse.ArgumentParser(prog="cardguru")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="parse cardsfolder into a dataset")
    b.add_argument("--cardsfolder", required=True)
    b.add_argument("--canonical", help="canonical card index.json for the name join")
    b.add_argument("--pin", help="source commit/version pin recorded in the dataset")
    b.add_argument("--out", default=DEFAULT_DATASET)
    b.set_defaults(fn=cmd_build)

    s = sub.add_parser("search", help="run a DSL query")
    s.add_argument("query", help="query JSON file")
    s.add_argument("--dataset", default=DEFAULT_DATASET)
    s.add_argument("--limit", type=int)
    s.add_argument("--explain", action="store_true", help="show why each card matched")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_search)

    sh = sub.add_parser("show", help="dump one card's graph record")
    sh.add_argument("name")
    sh.add_argument("--dataset", default=DEFAULT_DATASET)
    sh.set_defaults(fn=cmd_show)

    st = sub.add_parser("stats", help="dataset statistics")
    st.add_argument("--dataset", default=DEFAULT_DATASET)
    st.set_defaults(fn=cmd_stats)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
