"""Phase 7c: optimistic Elo-based opponent selection over rows that
carry a DECK as well as a kind.

Same weighting as rl/pfsp_pick.py (Phase 7b):

   w = exp(-((elo_opp - (elo_self + optimism))^2) / (2 sigma^2)) + floor

so mass sits on opponents slightly ABOVE the agent's current rating,
with a floor so nothing is ever fully retired. Deterministic per chunk,
so a restarted lane repeats the same pick.

Pool rows: name|kind|deck|elo
  kind = heuristic | search | searchhold      (scripted seat, any deck)
       = rl:<arch>:<ckpt>                     (a served policy seat)

The curriculum gate lives in the LANE, not here: the lane appends an
archetype's rows to the pool file only once that archetype has been
introduced, so this picker simply samples whatever is currently in the
file.

Prints "kind|deck|name|elo".
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
    # Phase 7c: guarantee the curriculum actually gets played. Without a
    # floor on archetype mass, PFSP can park on the mirror rows whenever
    # they happen to sit closer to the agent's rating - and then the
    # experiment silently becomes the mirror run it is supposed to be
    # compared against.
    ap.add_argument("--archetype-share", type=float, default=0.5,
                    help="fraction of chunks forced onto non-mirror decks")
    ap.add_argument("--mirror-deck", default="BenchDimir.dck")
    args = ap.parse_args()

    rows = []
    for line in open(args.pool):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, kind, deck, elo = line.split("|")
        if kind.startswith("rl:"):
            ckpt = kind.split(":", 2)[2]
            if not os.path.exists(ckpt):
                continue          # snapshot row written before the copy
        rows.append((name, kind, deck, float(elo)))
    if not rows:
        raise SystemExit("pfsp_p7c: empty pool")

    rng = random.Random(args.chunk * 9973 + 7)
    arche = [r for r in rows if r[2] != args.mirror_deck]
    # forced-archetype chunks use a separate deterministic draw so that
    # adding a new archetype does not reshuffle the mirror chunk picks
    if arche and rng.random() < args.archetype_share:
        rows = arche

    target = args.self_elo + args.optimism
    weights = [math.exp(-((e - target) ** 2) / (2 * args.sigma ** 2))
               + args.floor for _, _, _, e in rows]
    pick = rng.choices(range(len(rows)), weights=weights, k=1)[0]
    name, kind, deck, elo = rows[pick]
    print(f"{kind}|{deck}|{name}|{elo:.0f}")


if __name__ == "__main__":
    main()
