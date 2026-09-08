#!/usr/bin/env python3
"""Aggregate the families A/B across seeds, and say whether it moved.

Reads the per-run JSON that `eval_compile.py --json-out` writes and prints the
two things `docs/handoff.md` §4b says to look at: the per-seed spread (because
a one-seed comparison of this harness is worthless) and golden recall (which is
over 107 cards rather than 37 all-or-nothing verdicts, so it is the more stable
metric). The paired sign test is over question x seed pairs where the two arms
disagree.

    python benchmark/ab_families.py benchmark/agent_runs/*.json
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict


def load(paths):
    runs = {}
    for p in paths:
        with open(p, encoding="utf-8") as f:
            runs[os.path.splitext(os.path.basename(p))[0]] = json.load(f)
    return runs


def arm_of(name):
    return "families" if name.startswith("fam") else "control"


def sign_test(wins, losses):
    """One-sided binomial P(X >= wins) under p=0.5, ties discarded."""
    n = wins + losses
    if not n:
        return 1.0
    return sum(math.comb(n, k) for k in range(wins, n + 1)) / 2 ** n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    runs = load(args.runs)
    by_arm = defaultdict(list)
    for name, data in sorted(runs.items()):
        by_arm[arm_of(name)].append((name, data))

    print(f"{'run':<12} {'arm':<9} {'pass/37':>8} {'recall':>8} {'absent':>8} "
          f"{'zero':>5} {'jaccard':>8}")
    for arm in ("control", "families"):
        for name, d in by_arm[arm]:
            a = d["aggregate"]
            print(f"{name:<12} {arm:<9} {a['passed']:>8} "
                  f"{a['recall']*100:>7.1f}% {a['absent_rate']*100:>7.1f}% "
                  f"{a['zero_hit']:>5} {a['mean_overlap']:>8.3f}")

    print()
    summary = {}
    for arm in ("control", "families"):
        ps = [d["aggregate"]["passed"] for _n, d in by_arm[arm]]
        rs = [d["aggregate"]["recall"] for _n, d in by_arm[arm]]
        js = [d["aggregate"]["mean_overlap"] for _n, d in by_arm[arm]]
        summary[arm] = {
            "seeds": len(ps),
            "pass_mean": sum(ps) / len(ps), "pass_seeds": ps,
            "pass_spread": max(ps) - min(ps),
            "recall_mean": sum(rs) / len(rs), "recall_seeds": rs,
            "jaccard_mean": sum(js) / len(js),
        }
        s = summary[arm]
        print(f"{arm:<9} pass {s['pass_mean']:>5.1f} {tuple(ps)}  "
              f"spread={s['pass_spread']}   recall {s['recall_mean']*100:>5.1f}% "
              f"  jaccard {s['jaccard_mean']:.3f}")

    d_pass = summary["families"]["pass_mean"] - summary["control"]["pass_mean"]
    d_rec = (summary["families"]["recall_mean"]
             - summary["control"]["recall_mean"]) * 100
    print(f"\ndelta      pass {d_pass:+.1f} questions   recall {d_rec:+.1f}pp")
    worst_spread = max(summary[a]["pass_spread"] for a in summary)
    if abs(d_pass) <= worst_spread:
        print(f"           NOTE: |delta| <= the within-arm seed spread "
              f"({worst_spread}). Read recall, not pass count.")

    # -- paired, per question x seed -------------------------------------
    ctl = {n: {r["id"]: r for r in d["rows"]} for n, d in by_arm["control"]}
    fam = {n: {r["id"]: r for r in d["rows"]} for n, d in by_arm["families"]}
    pairs = list(zip(sorted(ctl), sorted(fam)))

    wins = losses = 0
    per_q = defaultdict(lambda: {"win": 0, "loss": 0, "tie": 0})
    for cn, fn in pairs:
        for qid, crow in ctl[cn].items():
            frow = fam[fn].get(qid)
            if frow is None or not crow.get("scorable", True):
                continue
            c, f = crow["passed"], frow["passed"]
            if c == f:
                per_q[qid]["tie"] += 1
            elif f and not c:
                wins += 1
                per_q[qid]["win"] += 1
            else:
                losses += 1
                per_q[qid]["loss"] += 1

    p = sign_test(wins, losses)
    print(f"\npaired over {len(pairs)} seed-pairs x scorable questions: "
          f"{wins} win / {losses} loss  (sign test one-sided p={p:.3f})")

    moved = {q: v for q, v in per_q.items() if v["win"] or v["loss"]}
    if moved:
        print("\nquestions that moved:")
        for q, v in sorted(moved.items(), key=lambda kv: -(kv[1]["win"] - kv[1]["loss"])):
            print(f"  {v['win']:+d}/-{v['loss']}  {q}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump({"summary": summary,
                       "paired": {"wins": wins, "losses": losses, "p": p},
                       "per_question": dict(per_q),
                       "runs": {n: d["aggregate"] for n, d in runs.items()}},
                      f, indent=1)
        print(f"\nwrote {args.json_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
