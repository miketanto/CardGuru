"""Phase 6: logistic-MLE Elo fit over the tournament match matrix.

Input rows (TSV): A  B  winsA  draws  games   (A was the agent seat).
Draws count as half a win for each side. The scripted-vs-scripted 500g
calibrations are appended as high-precision rows so the anchors are
mutually consistent. D0 is pinned at 1000; scale is the standard
400/ln(10).

Run: python3 rl/elo_fit.py [--matches /tmp/rl_elo/matches.tsv]
"""
import argparse
import math
from collections import defaultdict

# scripted-vs-scripted, 500g each (PHASE5-V3 / PHASE5-C4, v3 instruments,
# BenchDimir, seed 960000): winner, loser, wins, games
CALIBRATIONS = [
    ("D1", "D0", 307, 500),      # .614
    ("D1h", "D0", 298, 500),     # .596
    ("D1h", "D1", 252, 500),     # .504
]

SCALE = 400 / math.log(10)


def fit(rows, anchor="D0", iters=2000, lr=0.02):
    names = sorted({r[0] for r in rows} | {r[1] for r in rows})
    rating = {n: 0.0 for n in names}
    for _ in range(iters):
        grad = defaultdict(float)
        for a, b, wa, n in rows:
            pa = 1 / (1 + math.exp(-(rating[a] - rating[b])))
            g = (wa - n * pa)
            grad[a] += g
            grad[b] -= g
        for n in names:
            rating[n] += lr * grad[n] / 50
        rating = {n: r - rating[anchor] for n, r in rating.items()}
    return {n: 1000 + SCALE * r for n, r in rating.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", default="/tmp/rl_elo/matches.tsv")
    args = ap.parse_args()

    rows = []
    for line in open(args.matches):
        a, b, w, d, g = line.strip().split("\t")
        rows.append((a, b, float(w) + float(d) / 2, float(g)))
    for a, b, w, g in CALIBRATIONS:
        rows.append((a, b, float(w), float(g)))

    ratings = fit(rows)
    print(f"{'agent':>12} {'Elo':>7}")
    for n, r in sorted(ratings.items(), key=lambda kv: -kv[1]):
        print(f"{n:>12} {r:7.0f}")


if __name__ == "__main__":
    main()
