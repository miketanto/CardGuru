#!/usr/bin/env python3
"""Phase 15 A1 (rl/PHASE15-ARCH.md): is the fit data-limited or capacity-limited?

Retrain the clone, and separately the D1 critic, at 12.5 / 25 / 50 / 100 % of the
1,250 recorded games, against the SAME held-out games 13b used, and report
held-out priority top-1, held-out CE and value EV per fraction.

    python3 rl/p15_a1.py --stage policy --init INIT.pt --out DIR REC.jsonl [...]
    python3 rl/p15_a1.py --stage value  --ckpt bc.pt  --out DIR REC.jsonl [...]

Hold-out: the 13b split reproduced exactly (rl/v7_bc.py - labelled games of the
four cloned kinds, sorted, random.Random(0).shuffle, first round(0.1 n) held),
so the 100 % policy point is the 13b run's recipe on the 13b data and should
reproduce its row.  The training fractions are NESTED subsets of the remaining
training games (one Random(0) shuffle, prefixes taken), so "the last doubling"
is a doubling of the same pool rather than two unrelated samples.

policy stage = rl/v7_bc.py's recipe unchanged (fresh --cand-refers-pool init,
lr 1e-4, AdamW decay 0.01 on the heads, batch 32, clip 1.0, logit bound 5,
<= 20 epochs, early stop on held-out CE with patience 3, seed 0).  Early
stopping on the hold-out is 13b's behaviour and is kept so the 100 % point is
comparable to the published row; it is the same for every fraction, and it
makes every held-out number here mildly optimistic (stated, not corrected).

value stage = rl/p14_d1.py's N1 unchanged (the V7Policy critic of bc.pt trained
on MSE to the recorded seat's final outcome, lr 1e-4, batch 64, <= 12 epochs,
early stop on a validation split of 10 % of the TRAINING games, Random(1), so
the hold-out is never used for model selection).  EV = 1 - MSE / Var(r) on the
held-out consults, with 1,000 bootstrap resamples of held-out GAMES.

One JSON per point (a1_<stage>_<frac>.json); a point whose JSON exists is
skipped, so a killed run resumes.
"""
import argparse
import collections
import json
import os
import random
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                 # noqa: E402
import torch                       # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_policy as P              # noqa: E402
import v7_bc as BC                 # noqa: E402
import p14_d1 as D1                # noqa: E402

FRACS = [0.125, 0.25, 0.5, 1.0]


def say(*a):
    print("A1|" + "|".join(str(x) for x in a), flush=True)


def split_13b(game_keys):
    """the 13b hold-out: sorted labelled games, Random(0).shuffle, first round(0.1 n)"""
    games = sorted(game_keys)
    random.Random(0).shuffle(games)
    n_held = max(1, int(round(len(games) * 0.1)))
    return set(games[:n_held]), games[n_held:]


def nested_fractions(train_games, fracs):
    """nested prefixes of one Random(0) shuffle -> {frac: set of games}"""
    g = list(train_games)
    random.Random(0).shuffle(g)
    return {f: set(g[:max(1, int(round(len(g) * f)))]) for f in fracs}


# ------------------------------------------------------------------ policy stage
def policy_point(rows, held, train_games, args, frac):
    tr = [r for r in rows if r[0] in train_games]
    net = P.V7Policy.load(args.init, device=args.device)
    net.heads.logit_bound = args.logit_bound
    params = net.policy_parameters()
    head_ids = {id(p) for p in net.heads.parameters()}
    opt = torch.optim.AdamW(
        [{"params": [p for p in params if id(p) in head_ids], "weight_decay": args.weight_decay},
         {"params": [p for p in params if id(p) not in head_ids], "weight_decay": 0.0}], lr=args.lr)
    ea = types.SimpleNamespace(batch=args.batch, device=args.device, clip=args.clip)
    rng = random.Random(args.seed)
    net.eval()
    st = BC.run_epoch(net, held, ea)
    best = (BC.fmt(st, "all")["ce"], 0, st)
    bad = 0
    for ep in range(1, args.epochs + 1):
        t = time.time()
        net.train()
        trs = BC.fmt(BC.run_epoch(net, tr, ea, opt, rng), "all")
        net.eval()
        st = BC.run_epoch(net, held, ea)
        a = BC.fmt(st, "all")
        say(f"frac={frac}", f"epoch={ep}", f"train_ce={trs['ce']:.4f}", f"held_ce={a['ce']:.4f}",
            f"held_top1={a['top1']:.3f}", f"s={time.time() - t:.0f}")
        if a["ce"] < best[0] - 1e-4:
            best, bad = (a["ce"], ep, st), 0
        else:
            bad += 1
            if bad >= args.patience:
                say(f"frac={frac}", "early_stop", f"epoch={ep}", f"best_epoch={best[1]}")
                break
    del net, opt
    torch.cuda.empty_cache()
    out = {"frac": frac, "train_games": len(train_games), "train_consults": len(tr),
           "held_consults": len(held), "best_epoch": best[1],
           "all": BC.fmt(best[2], "all"),
           "per_kind": {k: BC.fmt(best[2], k) for k in BC.KINDS if BC.fmt(best[2], k)}}
    return out


# ------------------------------------------------------------------ value stage
def value_point(rows, r, gid, stage, ho, train_idx, val_idx, args, frac, n_games):
    a = types.SimpleNamespace(ckpt=args.ckpt, lr=args.lr_value, epochs=args.epochs_value,
                              patience=args.patience_value, batch=args.batch_value)
    net = D1.fit_n1(rows, train_idx, val_idx, a, args.device)
    pred = D1.critic_predict(net, rows, list(range(len(rows))), args.device)
    del net
    torch.cuda.empty_cache()
    rng = np.random.default_rng(0)
    res = D1.metrics(pred, r, gid, stage, ho, args.boot, rng)
    return {"frac": frac, "train_games": n_games, "train_consults": len(train_idx),
            "val_consults": len(val_idx), "held_consults": len(ho), "metrics": res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--stage", choices=["policy", "value"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--init", default="", help="policy stage: the fresh cand-refers-pool init (13b's)")
    ap.add_argument("--ckpt", default="", help="value stage: the checkpoint whose critic is trained (D1 used bc.pt)")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--fracs", default=",".join(str(f) for f in FRACS))
    # 13b's BC recipe
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--logit-bound", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=0)
    # D1's N1 recipe
    ap.add_argument("--epochs-value", type=int, default=12)
    ap.add_argument("--patience-value", type=int, default=3)
    ap.add_argument("--lr-value", type=float, default=1e-4)
    ap.add_argument("--batch-value", type=int, default=64)
    ap.add_argument("--boot", type=int, default=1000)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    fracs = [float(x) for x in args.fracs.split(",") if x]
    torch.manual_seed(args.seed)
    t0 = time.time()
    ids = V.CardIds()

    if args.stage == "policy":
        assert args.init, "--init required"
        hello, rows, drop = BC.load(args.recordings, ids, 0, set(BC.KINDS))
        held_games, train_all = split_13b(set(r[0] for r in rows))
        held = [r for r in rows if r[0] in held_games]
        say("data", f"consults={len(rows)}", f"games={len(held_games) + len(train_all)}",
            f"held_games={len(held_games)}", f"held_consults={len(held)}",
            f"dropped={dict(drop)}", f"load_s={time.time() - t0:.0f}")
        subs = nested_fractions(train_all, fracs)
        for f in fracs:
            path = os.path.join(args.out, f"a1_policy_{f}.json")
            if os.path.exists(path):
                say(f"frac={f}", "skip")
                continue
            say(f"frac={f}", "start", f"train_games={len(subs[f])}")
            out = policy_point(rows, held, subs[f], args, f)
            with open(path, "w") as fh:
                json.dump(out, fh, indent=1)
            pk = out["per_kind"].get("prio", {})
            say(f"frac={f}", "POINT", f"train_games={out['train_games']}",
                f"held_ce={out['all']['ce']:.4f}", f"held_top1={out['all']['top1']:.4f}",
                f"prio_top1={pk.get('top1', float('nan')):.4f}", f"best_epoch={out['best_epoch']}")
    else:
        assert args.ckpt, "--ckpt required"
        rows, lab_games, drop = D1.load(args.recordings, ids, set(BC.KINDS))
        held_games, _ = split_13b(lab_games)
        all_games = sorted(set(x[0] for x in rows))
        train_all = [g for g in all_games if g not in held_games]
        gindex = {g: i for i, g in enumerate(all_games)}
        gid = np.array([gindex[x[0]] for x in rows])
        stage = np.array([x[3] for x in rows])
        r = np.array([x[4] for x in rows], dtype=np.float64)
        ho = [i for i, x in enumerate(rows) if x[0] in held_games]
        say("data", f"consults={len(rows)}", f"games={len(all_games)}", f"labelled_games={len(lab_games)}",
            f"held_games={len(held_games)}", f"held_consults={len(ho)}",
            f"r_mean_held={r[ho].mean():.3f}", f"r_var_held={r[ho].var():.3f}",
            f"dropped={dict(drop)}", f"load_s={time.time() - t0:.0f}")
        subs = nested_fractions(train_all, fracs)
        for f in fracs:
            path = os.path.join(args.out, f"a1_value_{f}.json")
            if os.path.exists(path):
                say(f"frac={f}", "skip")
                continue
            g = sorted(subs[f])
            random.Random(1).shuffle(g)
            val_games = set(g[:max(1, int(round(len(g) * 0.1)))])
            tr = [i for i, x in enumerate(rows) if x[0] in subs[f] and x[0] not in val_games]
            va = [i for i, x in enumerate(rows) if x[0] in val_games]
            say(f"frac={f}", "start", f"train_games={len(subs[f])}", f"val_games={len(val_games)}")
            out = value_point(rows, r, gid, stage, ho, tr, va, args, f, len(subs[f]))
            with open(path, "w") as fh:
                json.dump(out, fh, indent=1)
            m = out["metrics"]["all"]
            say(f"frac={f}", "POINT", f"train_games={out['train_games']}", f"ev={m['ev']:.4f}",
                f"ev_ci=[{m['ev_lo']:.3f},{m['ev_hi']:.3f}]", f"auc={m['auc']:.3f}")
    say("done", f"stage={args.stage}", f"wall_s={time.time() - t0:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
