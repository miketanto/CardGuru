"""Phase 7b: optimistic Elo-based opponent selection (PFSP flavor).

Pool file rows: name|arch|ckpt|elo. The pick is a weighted sample with
   w = exp(-((elo_opp - (elo_self + optimism))^2) / (2 sigma^2)) + floor
i.e. mass centers on opponents slightly ABOVE the agent's current
rating ("optimistic": always be punching up, but within reach), with a
floor so no pool member is ever fully retired. Deterministic per chunk
so a restarted lane repeats the same pick.

Prints "ckpt|arch|name".
"""
import argparse
import math
import os
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True)
    ap.add_argument("--self-elo", type=float, required=True)
    ap.add_argument("--chunk", type=int, required=True)
    ap.add_argument("--optimism", type=float, default=100.0)
    ap.add_argument("--sigma", type=float, default=150.0)
    ap.add_argument("--floor", type=float, default=0.02)
    args = ap.parse_args()

    rows = []
    for line in open(args.pool):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, arch, ckpt, elo = line.split("|")
        if not os.path.exists(ckpt):
            continue                     # snapshot row written before copy
        rows.append((name, arch, ckpt, float(elo)))
    if not rows:
        raise SystemExit("pfsp: empty pool")

    target = args.self_elo + args.optimism
    weights = [math.exp(-((e - target) ** 2) / (2 * args.sigma ** 2))
               + args.floor for _, _, _, e in rows]
    rng = random.Random(args.chunk * 9973 + 7)
    pick = rng.choices(range(len(rows)), weights=weights, k=1)[0]
    name, arch, ckpt, _ = rows[pick]
    print(f"{ckpt}|{arch}|{name}")


if __name__ == "__main__":
    main()
