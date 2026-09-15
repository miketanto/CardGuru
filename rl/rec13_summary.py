#!/usr/bin/env python3
"""Phase 13a: per-decision-kind counters of CP7-teacher recordings.

    python3 rl/rec13_summary.py REC.jsonl [REC.jsonl ...]

Two views:
  REC13GATE - the pre-registered 13a gate per DECISION KIND, from the teacher's own
      Java counters in each job's <tag>.probe.txt (the seat knows which site it
      labelled): prio = teacherPrioConsults, labelled = consults - teacherOutside;
      target = teacherTgtConsults / teacherTgtLabelled; attack = teacherAtkConsults /
      (Exact + Alias); block = teacherBlkConsults / (Exact + Alias).  gate = pass when
      the labelled fraction (-1 excluded from the numerator) >= 0.9.
  REC13SUM  - the wire view by CANDIDATE TYPES (what BC's --kinds filter sees):
      prio (any LAND/SPELL/ACTIVATE), target (all TARGET), attack (any ATTACK),
      block (any BLOCK), trivial (PASS-only joint consult, k = 1: attack or block
      consults with a single option; not separable by type).  Its fraction is
      printed as gate_types= and is NOT the gate (correction 2026-09-15: the first
      version gated on this view, where PASS-only block consults fall under trivial
      and the block fraction reads low).
"""
import collections
import json
import os
import re
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


def probe_counters(path):
    """last value of every teacher* counter in <tag>.probe.txt"""
    pr = path[:-len(".jsonl")] + ".probe.txt" if path.endswith(".jsonl") else path + ".probe.txt"
    v = {}
    if os.path.exists(pr):
        for k, x in re.findall(r"(teacher[A-Za-z]+)=(\d+)", open(pr, errors="replace").read()):
            v[k] = int(x)
    return v


def main(paths):
    n = collections.Counter()
    lab = collections.Counter()
    neg = collections.Counter()
    nolab = collections.Counter()
    ksum = collections.Counter()
    prio_lab = collections.Counter()
    games = 0
    tc = collections.Counter()
    missing = 0
    for p in paths:
        c = probe_counters(p)
        if not c:
            missing += 1
        tc.update(c)
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
          f"|per_game={tot / max(1, games):.1f}|probes_missing={missing}")
    gate = {
        "prio": (tc["teacherPrioConsults"], tc["teacherPrioConsults"] - tc["teacherOutside"]),
        "target": (tc["teacherTgtConsults"], tc["teacherTgtLabelled"]),
        "attack": (tc["teacherAtkConsults"], tc["teacherAtkExact"] + tc["teacherAtkAlias"]),
        "block": (tc["teacherBlkConsults"], tc["teacherBlkExact"] + tc["teacherBlkAlias"]),
    }
    for k, (c, l) in gate.items():
        if not c:
            print(f"REC13GATE|kind={k}|consults=0|gate=FAIL|note=no counters")
            continue
        f = l / c
        extra = ""
        if k in ("attack", "block"):
            pre = "Atk" if k == "attack" else "Blk"
            extra = f"|exact={tc['teacher' + pre + 'Exact']}|alias={tc['teacher' + pre + 'Alias']}|miss={tc['teacher' + pre + 'Miss']}"
        print(f"REC13GATE|kind={k}|consults={c}|labelled={l}|frac={f:.3f}|gate={'pass' if f >= 0.9 else 'FAIL'}{extra}")
    for k in ("prio", "target", "attack", "block", "trivial", "other"):
        if not n[k]:
            continue
        f = lab[k] / n[k]
        extra = ""
        if k == "prio":
            extra = "|labels=" + ",".join(f"{t}:{prio_lab[t]}" for t in TYPES if prio_lab[t])
        print(f"REC13SUM|types={k}|consults={n[k]}|labelled={lab[k]}|y_neg={neg[k]}|no_y={nolab[k]}"
              f"|frac={f:.3f}|gate_types={'pass' if f >= 0.9 else 'fail'}|mean_k={ksum[k] / n[k]:.2f}{extra}")


if __name__ == "__main__":
    main(sys.argv[1:])
