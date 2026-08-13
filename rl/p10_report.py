"""Phase 10: turn the flagship lane's log lines into the report tables.

Reads $OUT/elo_curve.txt (P7ELO|), $OUT/matrix.txt (P10MATRIX|),
$OUT/gate_log.txt (P10GATE|) and, if given, the lane log (P7| chunk
lines) for the realized opponent and agent-deck mix.

Run: python3 rl/p10_report.py --out /tmp/rl_p10_flagship_s0 \
        [--lane-log /tmp/rl_p10_flagship_s0/lane.log]
"""
import argparse
import os
import re
from collections import defaultdict, OrderedDict

# 7c deck power (D0 piloting the deck vs D0 piloting BenchDimir), used to
# normalise the matrix: residual = win_rate - (1 - power), i.e. how much
# the agent beats what deck power alone predicts for its seat.
POWER = {}


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


def load(path, prefix):
    rows = []
    if os.path.exists(path):
        for line in open(path):
            if line.startswith(prefix):
                rows.append(parse_kv(line))
    return rows


def load_powers(seedfile):
    """Recover deck power from the seed pool's Elo (the inverse of the
    mapping p10_pool_calib.sh used), so the matrix can be normalised
    exactly the way 7c normalised its own."""
    if not os.path.exists(seedfile):
        return
    for line in open(seedfile):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, kind, deck, elo = line.split("|")
        if kind != "heuristic" or deck == "BenchDimir.dck":
            continue
        e = float(elo)
        POWER[os.path.splitext(deck)[0]] = 1 / (1 + 10 ** (-(e - 1000) / 400))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/rl_p10_flagship_s0")
    ap.add_argument("--lane-log", default=None)
    ap.add_argument("--seed-pool",
                    default="/home/user/CardGuru/rl/p10_pool_seed.tsv")
    args = ap.parse_args()
    load_powers(args.seed_pool)

    curve = load(os.path.join(args.out, "elo_curve.txt"), "P7ELO|")
    matrix = load(os.path.join(args.out, "matrix.txt"), "P10MATRIX|")
    gates = load(os.path.join(args.out, "gate_log.txt"), "P10GATE|")

    cur = OrderedDict()
    for r in curve:
        cur[int(r["trained"])] = r
    curve = [cur[k] for k in sorted(cur)]

    print("## Mirror growth curve (agent on BenchDimir, 100g vs each anchor,")
    print("## sequential, seed 950000)\n")
    print("| trained | Elo | vs D0 | vs D1 | vs D1h | blocks | block opps |"
          " block rate | flashThreats | oppTurn casts |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in curve:
        bd, bo = num(r.get("blocks"), 0), num(r.get("blockOpps"), 0)
        rate = f"{bd / bo:.2f}" if bo else "-"
        print(f"| {r['trained']} | {r.get('elo','?')} | {r.get('d0','?')} | "
              f"{r.get('d1','?')} | {r.get('d1h','?')} | {bd:.0f} | {bo:.0f} | "
              f"{rate} | {num(r.get('flashThreats'),0):.0f} | "
              f"{num(r.get('oppTurn'),0):.0f} |")

    cells, blocks = defaultdict(dict), defaultdict(dict)
    checkpoints, order = [], []
    for r in matrix:
        t, a = int(r["trained"]), r["deck"]
        if t not in checkpoints:
            checkpoints.append(t)
        if a not in order:
            order.append(a)
        cells[a][t] = r.get("win_rate", "NA")
        blocks[a][t] = (num(r.get("blocks"), 0), num(r.get("blockOpps"), 0))
    checkpoints.sort()

    if checkpoints:
        head = " | ".join(str(c) for c in checkpoints)
        print("\n## Robustness matrix (100g vs D0 piloting each deck, agent on")
        print("## BenchDimir, sequential, seed 951000)\n")
        print(f"| deck | power | {head} | final residual |")
        print("|---" * (len(checkpoints) + 3) + "|")
        for a in order:
            row = " | ".join(str(cells[a].get(c, "-")) for c in checkpoints)
            p = POWER.get(a)
            last = num(cells[a].get(checkpoints[-1]))
            resid = (f"{last - (1 - p):+.2f}"
                     if p is not None and last is not None else "-")
            print(f"| {a} | {p:.2f} | {row} | {resid} |" if p is not None
                  else f"| {a} | - | {row} | {resid} |")
        print("\nResidual = win_rate - (1 - power): performance beyond what")
        print("deck power alone predicts for the agent's seat (7c protocol).")

        print("\n## Blocking by deck (blocks declared / opportunities)\n")
        print(f"| deck | {head} |")
        print("|---" * (len(checkpoints) + 1) + "|")
        for a in order:
            parts = []
            for c in checkpoints:
                bd, bo = blocks[a].get(c, (None, None))
                parts.append(f"{bd:.0f}/{bo:.0f}" if bo is not None else "-")
            print(f"| {a} | {' | '.join(parts)} |")

    if gates:
        print("\n## Champion gate (50g h2h vs the reigning champion)\n")
        print("| trained | champion | score | wins | draws | verdict | pool Elo |")
        print("|---|---|---|---|---|---|---|")
        for r in gates:
            print(f"| {r['trained']} | {r.get('champion','?')} | "
                  f"{r.get('score','?')} | {r.get('wins','?')} | "
                  f"{r.get('draws','?')} | {r.get('verdict','?')} | "
                  f"{r.get('pool_elo','-')} |")
        promo = sum(1 for r in gates if r.get("verdict") == "PROMOTED")
        print(f"\n{promo}/{len(gates)} snapshots promoted into the pool.")

    if args.lane_log and os.path.exists(args.lane_log):
        mix, adeck = defaultdict(int), defaultdict(int)
        total = 0
        for line in open(args.lane_log):
            m = re.match(r"P7\|s\d+\|trained=\d+\|opp=([^|]+)\|deck=([^|]+)"
                         r"\|agentDeck=([^|\n]+)", line)
            if m:
                mix[(m.group(1), m.group(2))] += 1
                adeck[m.group(3)] += 1
                total += 1
        if total:
            print("\n## Realized opponent mix (64-episode chunks)\n")
            print("| opponent | deck | chunks | share |")
            print("|---|---|---|---|")
            for (name, deck), n in sorted(mix.items(), key=lambda kv: -kv[1]):
                print(f"| {name} | {deck} | {n} | {n / total:.1%} |")
            arche = sum(n for (_, d), n in mix.items() if d != "BenchDimir.dck")
            print(f"\nNon-mirror opponent chunks: {arche}/{total} "
                  f"({arche / total:.1%}).")
            print("\n## Realized agent-deck rotation (chunks per deck list)\n")
            print("| agent deck list | chunks |")
            print("|---|---|")
            for lst, n in sorted(adeck.items(), key=lambda kv: -kv[1]):
                print(f"| {lst} | {n} |")


if __name__ == "__main__":
    main()
