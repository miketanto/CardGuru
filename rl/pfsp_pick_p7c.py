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
    ap.add_argument("--floor", type=float, default=0.02,
                    help="per-row floor weight (7b/7c semantics)")
    # Phase 10: a per-ROW floor is a per-POOL floor in disguise. 7b's
    # .02 was set against a ~25-row pool of mirror snapshots; the
    # flagship pool has 44 rows spanning 46-1182 Elo, so the floor
    # contributes .88 of total weight - which swamps the Gaussian
    # exactly when the agent is weakest (50% of picks are floor-driven
    # at Elo 199, 2% at Elo 1000). That inverts the whole point of
    # optimistic selection: the weaker the agent, the more of its games
    # go to opponents it cannot learn anything from. --floor-total
    # fixes the floor's SHARE of the mass instead, so nothing is ever
    # retired but nothing is ever swamped either. Unset = 7b/7c
    # behaviour, so those lanes still reproduce.
    ap.add_argument("--floor-total", type=float, default=None,
                    help="total floor mass, spread across rows "
                         "(overrides --floor)")
    # Phase 7c: guarantee the curriculum actually gets played. Without a
    # floor on archetype mass, PFSP can park on the mirror rows whenever
    # they happen to sit closer to the agent's rating - and then the
    # experiment silently becomes the mirror run it is supposed to be
    # compared against.
    ap.add_argument("--archetype-share", type=float, default=0.5,
                    help="fraction of chunks forced onto non-mirror decks")
    ap.add_argument("--mirror-deck", default="BenchDimir.dck")
    # Phase 10: the driver's candidate encoding is global per JVM, so a
    # served opponent must share the agent's encoding family (an
    # e0/cdim38 net cannot seat in a cdim91 league). Scripted rows are
    # unaffected - they read no features.
    ap.add_argument("--arches", default="attn,lstmattn")
    args = ap.parse_args()

    allowed = set(args.arches.split(","))
    rows = []
    for line in open(args.pool):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, kind, deck, elo = line.split("|")
        if kind.startswith("rl:"):
            arch, ckpt = kind.split(":", 2)[1:]
            if arch not in allowed:
                continue
            if not os.path.exists(ckpt):
                continue          # snapshot row written before the copy
        rows.append((name, kind, deck, float(elo)))
    if not rows:
        raise SystemExit("pfsp_p7c: empty pool")

    # two independent streams: the gate decides mirror-vs-archetype and
    # must not shift when the pool grows, so it gets its own seed rather
    # than consuming a draw from the selection stream.
    gate = random.Random(args.chunk * 7919 + 13)
    rng = random.Random(args.chunk * 9973 + 7)
    arche = [r for r in rows if r[2] != args.mirror_deck]
    if arche and gate.random() < args.archetype_share:
        rows = arche

    target = args.self_elo + args.optimism
    floor = (args.floor_total / len(rows) if args.floor_total is not None
             else args.floor)
    weights = [math.exp(-((e - target) ** 2) / (2 * args.sigma ** 2))
               + floor for _, _, _, e in rows]
    pick = rng.choices(range(len(rows)), weights=weights, k=1)[0]
    name, kind, deck, elo = rows[pick]
    print(f"{kind}|{deck}|{name}|{elo:.0f}")


if __name__ == "__main__":
    main()
