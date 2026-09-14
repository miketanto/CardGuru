#!/usr/bin/env python3
"""Phase 9 / P3 - instant-speed play, a behaviour counter (rl/PHASE9-PROBES.md).

Over recordings that carry the seat's chosen action (a teacher `y` on the
consult, or the {"a":k} reply line that follows it), every SPELL choice whose
referent entity is an instant (v7_ent field 31) or has flash (keyword bit
34+8) is an "instant-speed-capable cast"; it was cast AT INSTANT SPEED if the
consult's game token says the seat is not the active player, or the step is
not a main phase, or the stack is non-empty (in response).  The opponent's
casts are read from `v7_opp_actions` (type one-hot cast, consult age 0 =
since the seat's previous consult) with the same rule applied to the consult
they are first reported in.  Wilson 95 % intervals.

  python3 rl/probes/instant_speed.py --out rl/artifacts/v7/9 name=REC.jsonl[,REC2.jsonl] ...
"""
import argparse
import glob
import json
import math
import os
import sys

STEP_MAIN1, STEP_MAIN2 = 4, 8


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def instant_speed(game):
    active = game[1] > 0.5
    main = game[2 + STEP_MAIN1] > 0.5 or game[2 + STEP_MAIN2] > 0.5
    stack = game[11] > 0.01
    return (not active) or (not main) or stack


def opp_instant_speed(game):
    """The opponent's spell is on the stack at this consult: instant speed if it is MY turn,
    or a non-main step, or it sits on top of something else (stack depth >= 2)."""
    active = game[1] > 0.5
    main = game[2 + STEP_MAIN1] > 0.5 or game[2 + STEP_MAIN2] > 0.5
    return active or (not main) or game[11] > 0.3


def is_instantish(ent_row):
    return ent_row[31] > 0.5 or ent_row[34 + 8] > 0.5          # instant type flag, flash bit


def scan(paths):
    """-> dict with counts for the seat and for the opponent."""
    seat = dict(casts=0, inst=0, inst_speed=0, held_windows=0, games=0, consults=0, by_card={})
    opp = dict(casts=0, inst=0, inst_speed=0, unreadable=0, by_card={})
    last = None
    for p in paths:
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            if m.get("t") == "consult" and "v7_ent" in m:
                seat["consults"] += 1
                last = m
                # opponent's casts first reported here
                for oa, refs in zip(m.get("v7_opp_actions", []), m.get("v7_opp_action_refers", [])):
                    if oa[0] > 0.5 and oa[7] < 0.075:                 # cast, first report (consult age 1 = 0.05)
                        opp["casts"] += 1
                        rows = [m["v7_ent"][r - 3] for r in refs if r >= 3 and r - 3 < len(m["v7_ent"])]
                        if rows and is_instantish(rows[0]):
                            opp["inst"] += 1
                            nm = m["v7_ent_name"][refs[0] - 3]
                            opp["by_card"].setdefault(nm, [0, 0, 0])
                            opp["by_card"][nm][0] += 1
                            if rows[0][2] < 0.5:                       # already resolved: timing not readable
                                opp["unreadable"] += 1; opp["by_card"][nm][2] += 1
                            elif opp_instant_speed(m["v7_game"]):
                                opp["inst_speed"] += 1; opp["by_card"][nm][1] += 1
                # a window where an instant was castable (the seat could have held or fired)
                ct = m["v7_cand_type"]
                if any(t == 2 and m["v7_cand_refers"][k] and is_instantish(m["v7_ent"][m["v7_cand_refers"][k][0] - 3])
                       for k, t in enumerate(ct)):
                    seat["held_windows"] += 1
                y = m.get("y")
                if y is not None:
                    _count_choice(seat, m, y); last = None
            elif "a" in m and last is not None:
                _count_choice(seat, last, m["a"]); last = None
            elif m.get("t") == "end":
                seat["games"] += 1
    return seat, opp


COUNTERSPELLS = {"We Say Thee Nay!", "Spell Pierce", "Spell Snare"}     # legal only with a spell on the stack: timing is forced


def _count_choice(seat, m, a):
    ct = m["v7_cand_type"]
    if a is None or a < 0 or a >= len(ct) or ct[a] != 2:
        return
    refs = m["v7_cand_refers"][a]
    if not refs:
        return
    row = m["v7_ent"][refs[0] - 3]
    seat["casts"] += 1
    if is_instantish(row):
        seat["inst"] += 1
        nm = m["v7_ent_name"][refs[0] - 3]
        seat["by_card"].setdefault(nm, [0, 0])
        seat["by_card"][nm][0] += 1
        free = nm not in COUNTERSPELLS
        if free:
            seat["inst_free"] = seat.get("inst_free", 0) + 1
        if instant_speed(m["v7_game"]):
            seat["inst_speed"] += 1; seat["by_card"][nm][1] += 1
            if free:
                seat["inst_speed_free"] = seat.get("inst_speed_free", 0) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="+", help="name=glob[,glob]")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lines = []
    for spec in args.sets:
        name, pats = spec.split("=", 1)
        paths = [q for p in pats.split(",") for q in sorted(glob.glob(p))]
        seat, opp = scan(paths)
        p, lo, hi = wilson(seat["inst_speed"], seat["inst"])
        pf, lof, hif = wilson(seat.get("inst_speed_free", 0), seat.get("inst_free", 0))
        lines.append("P3|%s|seat|games=%d|consults=%d|casts=%d|instant_casts=%d|at_instant_speed=%d|frac=%.3f [%.3f,%.3f]|excluding counterspells: %d/%d frac=%.3f [%.3f,%.3f]|windows_with_instant_castable=%d|by_card=%s" % (
            name, seat["games"], seat["consults"], seat["casts"], seat["inst"], seat["inst_speed"], p, lo, hi,
            seat.get("inst_speed_free", 0), seat.get("inst_free", 0), pf, lof, hif, seat["held_windows"],
            ";".join("%s %d/%d" % (k, v[1], v[0]) for k, v in sorted(seat["by_card"].items()))))
        readable = opp["inst"] - opp["unreadable"]
        p, lo, hi = wilson(opp["inst_speed"], readable)
        lines.append("P3|%s|opponent(heuristic)|casts=%d|instant_casts=%d|timing_readable(on stack at first report)=%d|at_instant_speed=%d|frac=%.3f [%.3f,%.3f]|by_card(inst_speed/readable/unreadable)=%s" % (
            name, opp["casts"], opp["inst"], readable, opp["inst_speed"], p, lo, hi,
            ";".join("%s %d/%d/%d" % (k, v[1], v[0] - v[2], v[2]) for k, v in sorted(opp["by_card"].items()))))
    for ln in lines:
        print(ln)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "instant_speed_summary.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
