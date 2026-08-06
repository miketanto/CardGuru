#!/usr/bin/env python3
"""Run the mechanical-search benchmark and emit benchmark/report.md.

For each entry: run the DSL query, check declared goldens, and (when a
baseline_regex is given) compare against an oracle-text regex search — the
stand-in for the best Scryfall `o:` query a competent user would write.

Exit code 1 if any golden fails.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cardguru.index import SearchIndex  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.environ.get("CARDGURU_DATASET", os.path.join(HERE, "..", "data", "dataset.jsonl.gz"))


def oracle_matches(records, pattern):
    rx = re.compile(pattern, re.IGNORECASE | re.DOTALL)
    return {r["name"] for r in records
            if r.get("oracle") and rx.search(r["oracle"].replace("\\n", "\n"))}


def main():
    with open(os.path.join(HERE, "benchmark.json"), encoding="utf-8") as f:
        entries = json.load(f)

    t0 = time.time()
    idx = SearchIndex.load(DATASET)
    load_s = time.time() - t0

    lines = ["# Mechanical-search benchmark report", "",
             f"Dataset: `{os.path.basename(DATASET)}` "
             f"({len(idx.records)} faces, pin `{getattr(idx, 'meta', {}).get('source_pin', '?')[:12]}`), "
             f"index load {load_s:.1f}s.", "",
             "Baseline = best-effort oracle-text regex (stand-in for Scryfall `o:` search).",
             ""]
    failures = []
    summary_rows = []

    for e in entries:
        t0 = time.time()
        hits = {h["record"]["name"] for h in idx.search(e["query"])}
        dt = time.time() - t0

        missing = [n for n in e.get("expect_present", []) if n not in hits]
        spurious = [n for n in e.get("expect_absent", []) if n in hits]
        ok = not missing and not spurious
        if not ok:
            failures.append((e["id"], missing, spurious))

        lines.append(f"## {e['id']}  {'✅' if ok else '❌'}")
        lines.append("")
        lines.append(f"*{e['description']}*")
        lines.append("")
        lines.append(f"- structural hits: **{len(hits)}** ({dt*1000:.0f} ms)")
        lines.append(f"- goldens: present {len(e.get('expect_present', []))-len(missing)}"
                     f"/{len(e.get('expect_present', []))}, "
                     f"absent-respected {len(e.get('expect_absent', []))-len(spurious)}"
                     f"/{len(e.get('expect_absent', []))}")
        if missing:
            lines.append(f"- MISSING expected: {missing}")
        if spurious:
            lines.append(f"- SPURIOUS (expected absent): {spurious}")
        sample = sorted(hits)[:8]
        lines.append(f"- sample: {', '.join(sample)}")

        if e.get("baseline_regex"):
            base = oracle_matches(idx.records, e["baseline_regex"])
            both = hits & base
            s_only = hits - base
            r_only = base - hits
            lines.append(f"- baseline regex `{e['baseline_regex']}`: {len(base)} hits — "
                         f"agree {len(both)}, structural-only {len(s_only)}, regex-only {len(r_only)}")
            if s_only:
                lines.append(f"  - regex misses (structural found): {sorted(s_only)[:5]}")
            if r_only:
                lines.append(f"  - regex extras (structural rejected): {sorted(r_only)[:5]}")
        lines.append("")
        summary_rows.append((e["id"], len(hits), ok))

    lines.insert(4, "")
    lines.insert(5, "| query | hits | goldens |")
    lines.insert(6, "|---|---|---|")
    for i, (qid, n, ok) in enumerate(summary_rows):
        lines.insert(7 + i, f"| {qid} | {n} | {'pass' if ok else 'FAIL'} |")

    report = os.path.join(HERE, "report.md")
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {report}")
    if failures:
        print("GOLDEN FAILURES:")
        for qid, missing, spurious in failures:
            print(f"  {qid}: missing={missing} spurious={spurious}")
        sys.exit(1)
    print(f"all {len(entries)} queries passed goldens")


if __name__ == "__main__":
    main()
