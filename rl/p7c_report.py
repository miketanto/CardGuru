"""Phase 7c: turn the lane's log lines into the markdown tables the
deliverable needs (growth curve, robustness matrix, blocking counter).

Reads $OUT/elo_curve.txt (P7CELO| lines) and $OUT/matrix.txt
(P7CMATRIX| lines) and prints three tables plus the realized opponent
mix if a lane log is supplied.

Run: python3 rl/p7c_report.py [--out /tmp/rl_p7c_lstmattn_s0] [--lane-log FILE]
"""
import argparse
import os
import re
from collections import defaultdict, OrderedDict


def parse_kv(line):
    d = {}
    for part in line.strip().split("|")[1:]:
        if "=" in part:
            k, v = part.split("=", 1)
            d[k] = v
    return d


def num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/rl_p7c_lstmattn_s0")
    ap.add_argument("--lane-log", default=None)
    args = ap.parse_args()

    curve, matrix = [], []
    cf = os.path.join(args.out, "elo_curve.txt")
    mf = os.path.join(args.out, "matrix.txt")
    if os.path.exists(cf):
        for line in open(cf):
            if line.startswith("P7CELO|"):
                curve.append(parse_kv(line))
    if os.path.exists(mf):
        for line in open(mf):
            if line.startswith("P7CMATRIX|"):
                matrix.append(parse_kv(line))

    # de-duplicate on trained (a resumed lane can re-emit a row)
    cur = OrderedDict()
    for r in curve:
        cur[int(r["trained"])] = r
    curve = [cur[k] for k in sorted(cur)]

    print("## Mirror growth curve (BenchDimir, 100g vs each anchor)\n")
    print("| trained | Elo | vs D0 | vs D1 | vs D1h | blocks/100g | block opps | block rate |")
    print("|---|---|---|---|---|---|---|---|")
    for r in curve:
        bd, bo = num(r.get("blocks"), 0), num(r.get("blockOpps"), 0)
        rate = f"{bd / bo:.2f}" if bo else "-"
        print(f"| {r['trained']} | {r.get('elo','?')} | {r.get('d0','?')} | "
              f"{r.get('d1','?')} | {r.get('d1h','?')} | {bd:.0f} | {bo:.0f} | {rate} |")

    # robustness matrix: rows = archetype, cols = trained
    cells = defaultdict(dict)
    blocks = defaultdict(dict)
    checkpoints, order = [], []
    for r in matrix:
        t = int(r["trained"])
        a = r["archetype"]
        if t not in checkpoints:
            checkpoints.append(t)
        if a not in order:
            order.append(a)
        cells[a][t] = r.get("win_rate", "NA")
        bd, bo = num(r.get("blocks"), 0), num(r.get("blockOpps"), 0)
        blocks[a][t] = (bd, bo)
    checkpoints.sort()

    if checkpoints:
        print("\n## Robustness matrix (100g vs D0 piloting each archetype)\n")
        head = " | ".join(str(c) for c in checkpoints)
        print(f"| archetype | {head} |")
        print("|---" * (len(checkpoints) + 1) + "|")
        for a in order:
            row = " | ".join(str(cells[a].get(c, "-")) for c in checkpoints)
            print(f"| {a} | {row} |")

        print("\n## Blocking counter by archetype (blocks / opportunities)\n")
        print(f"| archetype | {head} |")
        print("|---" * (len(checkpoints) + 1) + "|")
        for a in order:
            parts = []
            for c in checkpoints:
                bd, bo = blocks[a].get(c, (None, None))
                parts.append(f"{bd:.0f}/{bo:.0f}" if bo is not None else "-")
            print(f"| {a} | {' | '.join(parts)} |")

    if args.lane_log and os.path.exists(args.lane_log):
        mix = defaultdict(int)
        total = 0
        for line in open(args.lane_log):
            m = re.match(r"P7C\|s\d+\|trained=\d+\|opp=([^|]+)\|deck=([^|]+)\|", line)
            if m:
                mix[(m.group(1), m.group(2))] += 1
                total += 1
        if total:
            print("\n## Realized opponent mix (64-episode chunks)\n")
            print("| opponent | deck | chunks | share |")
            print("|---|---|---|---|")
            for (name, deck), n in sorted(mix.items(), key=lambda kv: -kv[1]):
                print(f"| {name} | {deck} | {n} | {n / total:.1%} |")
            arche = sum(n for (_, d), n in mix.items() if d != "BenchDimir.dck")
            print(f"\nArchetype chunks: {arche}/{total} ({arche / total:.1%}); "
                  f"mirror chunks: {total - arche}/{total}.")


if __name__ == "__main__":
    main()
