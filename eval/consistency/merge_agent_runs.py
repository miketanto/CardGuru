"""Merge agent-as-compiler outputs into the harness's recorded-JSONL format.

Agent outputs are named out_<RUNG>_s<SAMPLE>.jsonl and carry {qid, question, query}.
The harness keys on (question, sample), so this flattens them and reports coverage
gaps rather than letting a partial run masquerade as a complete one.

Usage: python eval/consistency/merge_agent_runs.py [--dir DIR] [--out PATH]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import defaultdict

PAT = re.compile(r"out_(P\d)_s(\d+)\.jsonl$")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="eval/consistency/agent_run")
    ap.add_argument("--out", default="eval/consistency/recorded.jsonl")
    ap.add_argument("--intents", default="eval/nl_consistency_intents.json")
    args = ap.parse_args(argv)

    spec = json.load(open(args.intents, encoding="utf-8"))
    laddered = [i for i in spec["intents"] if len(i.get("paraphrases") or {}) == 5]
    expected = {f"{i['id']}.{r}": i["paraphrases"][r]
                for i in laddered for r in ("P1", "P2", "P3", "P4", "P5")}

    rows, seen = [], defaultdict(set)
    per_file = {}
    for path in sorted(glob.glob(os.path.join(args.dir, "out_*.jsonl"))):
        m = PAT.search(path)
        if not m:
            continue
        rung, sample = m.group(1), int(m.group(2))
        n = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                qid = r.get("qid", "")
                q = expected.get(qid)
                if q is None:
                    print(f"  !! {os.path.basename(path)}: unknown qid {qid!r}, skipped")
                    continue
                if r.get("question") and r["question"].strip() != q.strip():
                    print(f"  !! {qid}: question text drifted from the frozen batch, "
                          f"using frozen text")
                rows.append({"question": q, "sample": sample,
                             "query": r.get("query"),
                             "errors": list(r.get("errors") or []),
                             "qid": qid})
                seen[qid].add(sample)
                n += 1
        per_file[os.path.basename(path)] = n

    samples = sorted({r["sample"] for r in rows})
    missing = [(qid, s) for qid in expected for s in samples if s not in seen[qid]]

    with open(args.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    for k, v in sorted(per_file.items()):
        print(f"  {k}: {v}")
    print(f"merged {len(rows)} compilations over samples {samples} -> {args.out}")
    print(f"coverage: {len(seen)}/{len(expected)} qids; missing (qid,sample) pairs: {len(missing)}")
    for m in missing[:10]:
        print("   missing", m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
