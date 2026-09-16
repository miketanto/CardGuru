#!/usr/bin/env python3
"""Phase 15 diagnostic: are the frozen clones sitting at the logit bound?

    python3 rl/p15_sat.py --ckpt NAME=path [--ckpt NAME=path ...] REC.jsonl [...]

A DIAGNOSTIC, never a bar, and it trains nothing. `v7_heads.V7Heads` applies
`logits = B * tanh(logits / B)` with B = `logit_bound` (5 in every lane checkpoint
since 7a). A head whose RAW logits are far outside +/-B is saturated, and its
gradient through the tanh is ~1 - tanh^2 ~ 0 - which would freeze training exactly
as rl/artifacts/v7/15/a4/bc_W0Base.log and bc_W1Fly.log show (train CE identical to
four decimals from epoch 2, every held-out metric unchanged), while the joint clone
on the same recipe trained normally for eight epochs.

Raw logits are obtained without touching the model source: `heads.logit_bound = 0`
makes the head return the pre-tanh values (the bound is applied only when > 0).

Reported per checkpoint, over REAL candidates of held-out consults: the share of
|raw logit| >= the checkpoint's own bound, >= 10, >= 20, the max, the mean, and the
same for the per-consult TOP logit only (the one the argmax rides on).
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                 # noqa: E402
import torch                       # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_policy as P              # noqa: E402
import v7_bc as BC                 # noqa: E402


def say(*a):
    print("SAT|" + "|".join(str(x) for x in a), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", required=True, help="name=path")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-consults", type=int, default=4000)
    ap.add_argument("--holdout", type=float, default=0.1)
    args = ap.parse_args()
    ids = V.CardIds()
    hello, rows, drop = BC.load(args.recordings, ids, 0, set(BC.KINDS))
    games = sorted(set(r[0] for r in rows))
    random.Random(0).shuffle(games)
    held = set(games[:max(1, int(round(len(games) * args.holdout)))])
    rows = [r for r in rows if r[0] in held][:args.max_consults]
    say("data", f"held_consults={len(rows)}", f"held_games={len(held)}")

    for spec in args.ckpt:
        name, path = spec.split("=", 1)
        if not os.path.exists(path):
            say(name, "MISSING", path)
            continue
        net = P.V7Policy.load(path, device=args.device)
        bound = float(net.heads.logit_bound)
        net.heads.logit_bound = 0.0          # raw, pre-tanh
        net.eval()
        allv, topv = [], []
        with torch.no_grad():
            for s in range(0, len(rows), args.batch):
                chunk = rows[s:s + args.batch]
                b = {k: (v.to(args.device) if torch.is_tensor(v) else v)
                     for k, v in V.collate([r[1] for r in chunk]).items()}
                lg, _, _, _ = net(b, with_value=False)
                lg = lg.float().cpu()
                for i, r in enumerate(chunk):
                    k = len(r[3])
                    v = lg[i, :k]
                    v = v[torch.isfinite(v)]
                    if not len(v):
                        continue
                    allv.append(v.abs().numpy())
                    topv.append(float(v.max().abs()))
        del net
        torch.cuda.empty_cache()
        a = np.concatenate(allv) if allv else np.zeros(1)
        t = np.array(topv) if topv else np.zeros(1)
        say(name, f"bound={bound:g}", f"n_logits={len(a)}", f"mean_abs={a.mean():.3f}",
            f"max_abs={a.max():.2f}",
            f"share_ge_bound={float((a >= bound).mean()):.4f}" if bound > 0 else "share_ge_bound=na",
            f"share_ge_10={float((a >= 10).mean()):.4f}",
            f"share_ge_20={float((a >= 20).mean()):.4f}")
        say(name, "top_logit_only", f"n={len(t)}", f"mean_abs={t.mean():.3f}",
            f"max_abs={t.max():.2f}",
            f"share_ge_bound={float((t >= bound).mean()):.4f}" if bound > 0 else "share_ge_bound=na",
            f"share_ge_10={float((t >= 10).mean()):.4f}",
            f"share_ge_20={float((t >= 20).mean()):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
