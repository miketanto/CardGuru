"""Phase 10 (4.4) opponent selection for the upper-bound archetype pilots.

Phase 7b optimistic weighting (rl/pfsp_pick.py) over rows that carry a
deck (rl/pfsp_pick_p7c.py), with two changes the pilot lanes need:

1. FIELD SHARE. The pool has two families: the mirror family (rows whose
   deck is the agent's own archetype -- the lane's own snapshots) and
   the FIELD (rows on BenchDimir: D0/D1/D1h + the project champions),
   which is what these pilots are being trained to pressure. A
   from-random-init net rates ~46, so pure optimistic weighting would
   put ~all mass on its own snapshots for thousands of episodes, and a
   snapshot pool of argmax-mode random-init nets is nearly passive: the
   sampling seat beats it 64-0 and learns almost nothing. Phase 7b's
   scratch line avoided this by rotating a real external opponent into
   1 chunk in 4; --field-share (default .25) reproduces that cadence
   deterministically, and the Gaussian takes over on its own once the
   agent's rating reaches the field.

2. NEAREST-ABOVE FALLBACK. exp(-(800^2)/(2*150^2)) underflows to 0, so
   with a flat floor every distant row is equally likely -- an
   episode-0 agent forced into the field would face ck_6144 as often as
   D0. When every weight in the chosen family has underflowed, fall
   back to the single row closest to the optimism target, which walks
   the field D0 -> D1/D1h -> champions as the pilot improves.

Rows: name|kind|deck|elo, kind = heuristic | search | searchhold |
rl:<arch>:<ckpt>. Deterministic per chunk, so a restarted lane repeats
its picks. Prints "kind|deck|name|elo".
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
    ap.add_argument("--agent-deck", required=True,
                    help="the pilot's own deck; rows on it are the mirror "
                         "family, every other row is the field")
    ap.add_argument("--optimism", type=float, default=100.0)
    ap.add_argument("--sigma", type=float, default=150.0)
    ap.add_argument("--floor", type=float, default=0.02)
    ap.add_argument("--field-share", type=float, default=0.25)
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
        raise SystemExit("p10_pick: empty pool")

    # independent streams: the family gate must not shift when the pool
    # grows, so it does not consume a draw from the selection stream.
    gate = random.Random(args.chunk * 7919 + 13)
    rng = random.Random(args.chunk * 9973 + 7)
    field = [r for r in rows if r[2] != args.agent_deck]
    mirror = [r for r in rows if r[2] == args.agent_deck]
    if field and mirror:
        rows = field if gate.random() < args.field_share else mirror
    elif field:
        rows = field

    target = args.self_elo + args.optimism
    weights = [math.exp(-((e - target) ** 2) / (2 * args.sigma ** 2))
               for _, _, _, e in rows]
    if max(weights) <= 0.0:
        # every row is far away: take the one nearest the target rather
        # than a floor-driven coin flip over the whole field
        pick = min(range(len(rows)), key=lambda i: abs(rows[i][3] - target))
    else:
        weights = [w + args.floor for w in weights]
        pick = rng.choices(range(len(rows)), weights=weights, k=1)[0]
    name, kind, deck, elo = rows[pick]
    print(f"{kind}|{deck}|{name}|{elo:.0f}")


if __name__ == "__main__":
    main()
