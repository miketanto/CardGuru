#!/usr/bin/env python3
"""Phase 13a: per-decision-kind counters of CP7-teacher recordings.

    python3 rl/rec13_summary.py REC.jsonl [REC.jsonl ...]

Kind of a consult, from its candidate types (the wire carries no site):
  prio   - any LAND / SPELL / ACTIVATE candidate (index 0 is PASS)
  target - every candidate TARGET
  attack - any ATTACK candidate (the empty subset is typed PASS)
  block  - any BLOCK candidate (the no-block assignment is typed PASS)
  trivial- PASS-only (a joint consult whose only option is the empty one)
Prints one line per kind: consults, labelled (y >= 0), y = -1, labelled
fraction (-1 excluded from the numerator), the pre-registered 0.9 gate,
mean k, and for prio the label type census; games from the {"t":"end"}
lines.
"""
import collections
import json
import sys

TYPES = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]


def kind_of(ct):
    s = set(ct)
    if s & {1, 2, 3}:
        return "prio"
    if s == {4}:
        return "target"
    if 5 in s:
        return "attack"
    if 6 in s:
        return "block"
    if s == {0}:
        return "trivial"
    return "other"


def main(paths):
    n = collections.Counter()
    lab = collections.Counter()
    neg = collections.Counter()
    nolab = collections.Counter()
    ksum = collections.Counter()
    prio_lab = collections.Counter()
    games = 0
    for p in paths:
        with open(p, "rb") as fh:
            for raw in fh:
                if b'"t":"end"' in raw:
                    games += 1
                    continue
                if b'"t":"consult"' not in raw:
                    continue
                m = json.loads(raw)
                ct = m.get("v7_cand_type")
                if ct is None:
                    continue
                k = kind_of(ct)
                n[k] += 1
                ksum[k] += len(ct)
                if "y" not in m:
                    nolab[k] += 1
                    continue
                y = int(m["y"])
                if 0 <= y < len(ct):
                    lab[k] += 1
                    if k == "prio":
                        prio_lab[TYPES[ct[y]]] += 1
                else:
                    neg[k] += 1
    tot = sum(n.values())
    tl = sum(lab.values())
    print(f"REC13SUM|files={len(paths)}|games={games}|consults={tot}|labelled={tl}"
          f"|per_game={tot / max(1, games):.1f}")
    for k in ("prio", "target", "attack", "block", "trivial", "other"):
        if not n[k]:
            continue
        f = lab[k] / n[k]
        extra = ""
        if k == "prio":
            extra = "|labels=" + ",".join(f"{t}:{prio_lab[t]}" for t in TYPES if prio_lab[t])
        print(f"REC13SUM|kind={k}|consults={n[k]}|labelled={lab[k]}|y_neg={neg[k]}|no_y={nolab[k]}"
              f"|frac={f:.3f}|gate={'pass' if f >= 0.9 else 'FAIL'}|mean_k={ksum[k] / n[k]:.2f}{extra}")


if __name__ == "__main__":
    main(sys.argv[1:])
