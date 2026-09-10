"""Audit every mode/event production against the text of the cards it should match.

Cycle 4 found a failure class the earlier cycles had not: a production authored
from a Forge mode's *name* rather than from any card's wording.
`AttackersDeclared` was written as `attackers are declared`, which matches
nothing -- 233 cards, zero hits, and no measurement caught it because aggregate
recall averaged it away.

This audits the whole table the same way, mechanically:

  for each mode M in the production tables:
      take the dev-half faces where Forge assigns M
      take the oracle line most likely to BE that ability
      report how many the production matches, and -- for the misses -- the
      most distinctive phrases in the text, so the repair is written from
      the cards rather than from the mode name

Dev half only: this is production development, and the holdout must stay clean.

Usage:
    python3 research/scripts/m3_production_audit.py <forge.jsonl.gz> [out.json]
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m0_oracle_segment import oracle_lines  # noqa: E402
from m1_effect_verbs import split_of  # noqa: E402
from m3_modes_events import (  # noqa: E402
    REPLACEMENT_EVENTS, STATIC_MODES, TRIGGER_MODES, event_clause,
)

STOP = set("""a an the of to and or that this it its is are with for on in you your as at
be by if would may can't cant not each any all one two from into onto when whenever
target creature player card cards spell spells permanent permanents battlefield
graveyard library hand up other another their his her them they""".split())


def load(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        f.readline()
        for line in f:
            yield json.loads(line)


def phrases(text: str, n: int = 3):
    toks = [t for t in re.findall(r"[a-z']+", text.lower())]
    for i in range(len(toks) - n + 1):
        gram = toks[i:i + n]
        if all(g in STOP for g in gram):
            continue
        yield " ".join(gram)


def audit(records, table, kind_filter, mode_of, line_pick):
    """Return per-mode match stats for one production table."""
    by_mode = collections.defaultdict(list)
    for rec in records:
        if split_of(rec) != "dev":
            continue
        lines = oracle_lines(rec.get("oracle") or "")
        if not lines:
            continue
        for n in rec["nodes"]:
            if n.get("kind") != kind_filter:
                continue
            m = mode_of(n)
            if m:
                by_mode[m].append((rec.get("name"), lines))

    compiled = [(k, re.compile(p, re.I)) for k, p in table]
    out = []
    for mode, entries in sorted(by_mode.items(), key=lambda kv: -len(kv[1])):
        rx = dict(compiled).get(mode)
        if rx is None:
            out.append({"mode": mode, "cards": len(entries),
                        "status": "no production", "match_pct": None})
            continue
        hit = 0
        miss_text = []
        for _nm, lines in entries:
            cand = [line_pick(l) for l in lines]
            if any(rx.search(c) for c in cand):
                hit += 1
            elif len(miss_text) < 400:
                miss_text.extend(cand)
        pct = round(100 * hit / len(entries), 1)
        row = {"mode": mode, "cards": len(entries), "matched": hit,
               "match_pct": pct,
               "status": "OK" if pct >= 60 else ("DEAD" if pct < 5 else "WEAK")}
        if pct < 60:
            counts = collections.Counter()
            for t in miss_text:
                counts.update(set(phrases(t)))
            row["top_phrases_in_misses"] = [
                {"phrase": p, "n": c} for p, c in counts.most_common(8)]
        out.append(row)
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    records = list(load(argv[1]))
    report = {
        "trigger_modes": audit(
            records, TRIGGER_MODES, "T",
            lambda n: n.get("mode"), event_clause),
        "static_modes": audit(
            records, STATIC_MODES, "S",
            lambda n: n.get("mode"), lambda l: l),
        "replacement_events": audit(
            records, REPLACEMENT_EVENTS, "R",
            lambda n: (n.get("params") or {}).get("Event"), lambda l: l),
    }
    dead = [r for tbl in report.values() for r in tbl
            if r.get("status") in ("DEAD", "WEAK") and r["cards"] >= 20]
    report["needs_repair"] = sorted(
        [{k: v for k, v in r.items() if k != "top_phrases_in_misses"}
         for r in dead], key=lambda r: -r["cards"])
    text = json.dumps(report, indent=1)
    if len(argv) > 2:
        with open(argv[2], "w", encoding="utf-8") as f:
            f.write(text + "\n")
    for tbl_name, tbl in report.items():
        if tbl_name == "needs_repair":
            continue
        print(f"\n=== {tbl_name} ===")
        for r in tbl:
            if r["cards"] < 15:
                continue
            print(f'  {r["status"]:5} {str(r["match_pct"]):>6}%  {r["cards"]:5} cards  {r["mode"]}')
    print(f'\nneeds repair (>=20 cards): {len(report["needs_repair"])}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
