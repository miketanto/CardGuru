#!/usr/bin/env python3
"""Phase 15 A3 (rl/PHASE15-ARCH.md): the remedy test - re-clone with an auxiliary loss
that makes every entity token predict its own card's 68 `e2_features`.

RUN THIS ONLY IF A2 READS "discards". It is written ahead of that reading so the remedy
can start immediately; writing it costs nothing and decides nothing.

    python3 rl/p15_a3.py --init INIT.pt --out bc_aux.pt REC.jsonl [...]

Everything is 13b's recipe, unchanged and deliberately so (the A3 bar compares against
13b's priority top-1 of 0.876): the same fresh `--cand-refers-pool` init, lr 1e-4, AdamW
decay 0.01 on the heads, batch 32, grad clip 1.0, logit bound 5, <= 20 epochs, early stop
on held-out CE with patience 3, seed 0, 10 % of GAMES held out by the 13b rule, the same
four decision kinds, the same memoryless per-consult scoring.  `rl/v7_bc.py` itself is NOT
touched: it is what run_15a2.sh and the ladder call, and 13b must stay reproducible.

THE ONE ADDITION, stated in advance (rl/PHASE15-ARCH.md A3): a linear head on each encoded
ENTITY token predicts that entity's 68 e2_features row (BCE-with-logits, masked to entities
whose card id and name resolve), added to the candidate cross-entropy with **weight 0.1**.
The weight was fixed in the runbook before any A3 data existed and is not tuned here.

Reported per kind: held-out CE, exact top-1, class top-1, type agreement - the same table
13b and A1 report, so the A3 readings can be made directly:
  * "the remedy works" if A2's probe 1 on this checkpoint recovers to >= 0.90 of the frozen
    embedding's score AND held-out priority top-1 drops by <= 0.02 from 0.876;
  * otherwise report what it cost.
The probe half of that reading is made by re-running rl/p15_a2.py against this checkpoint;
this script only produces the checkpoint and the agreement table.
"""
import argparse
import collections
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                 # noqa: E402
import torch                       # noqa: E402
import torch.nn as nn              # noqa: E402
import torch.nn.functional as F    # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_policy as P              # noqa: E402
import v7_bc as BC                 # noqa: E402
from p15_a2 import load_targets, norm   # noqa: E402


def say(*a):
    print("A3|" + "|".join(str(x) for x in a), flush=True)


def aux_targets(rows, e2):
    """per row: (entity index -> 68-vector) as a dense [N, 68] array + mask [N]"""
    out = []
    for r in rows:
        names = r[1].ent_name
        n = len(names)
        t = np.zeros((n, 68), dtype=np.float32)
        m = np.zeros(n, dtype=bool)
        for j, nm in enumerate(names):
            v = e2.get(norm(nm))
            if v is not None and v.shape[0] == 68:
                t[j] = v
                m[j] = True
        out.append((t, m))
    return out


def forward_with_ent(net, b):
    """V7Policy.forward's own path, but also returning the encoded entity tokens."""
    toks = net.build(b)
    bel = net.belief(toks)
    toks = net.belief.attach(toks, bel)
    enc = net.enc(toks, ent_raw=b["ent"])
    logits, _, _ = net.heads(enc, None)
    return logits, enc["ent"]


def run_epoch(net, head, rows, aux, args, opt=None, rng=None):
    st = collections.defaultdict(lambda: [0.0, 0, 0, 0, 0])
    auxsum, auxn = 0.0, 0
    idx = list(range(len(rows)))
    if opt is not None and rng is not None:
        rng.shuffle(idx)
    for s in range(0, len(idx), args.batch):
        chunk_i = idx[s:s + args.batch]
        chunk = [rows[i] for i in chunk_i]
        b = V.collate([r[1] for r in chunk])
        b = {k: (v.to(args.device) if torch.is_tensor(v) else v) for k, v in b.items()}
        y = torch.tensor([r[2] for r in chunk], dtype=torch.long, device=args.device)
        with torch.set_grad_enabled(opt is not None):
            lg, ent = forward_with_ent(net, b)
            lg = lg.float()
            per = F.cross_entropy(lg, y, reduction="none")
            loss = per.mean()
            N = ent.shape[1]
            tt = torch.zeros(len(chunk), N, 68, device=args.device)
            mm = torch.zeros(len(chunk), N, dtype=torch.bool, device=args.device)
            for i, gi in enumerate(chunk_i):
                t, m = aux[gi]
                k = min(len(m), N)
                if k:
                    tt[i, :k] = torch.from_numpy(t[:k]).to(args.device)
                    mm[i, :k] = torch.from_numpy(m[:k]).to(args.device)
            if mm.any():
                pred = head(ent.float())[mm]
                a_loss = F.binary_cross_entropy_with_logits(pred, tt[mm])
                loss = loss + args.aux_weight * a_loss
                auxsum += float(a_loss) * int(mm.sum())
                auxn += int(mm.sum())
            if opt is not None:
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(list(net.policy_parameters()) + list(head.parameters()), args.clip)
                opt.step()
        am = lg.argmax(1).cpu()
        per = per.detach().cpu()
        for i, r in enumerate(chunk):
            a, yy = int(am[i]), r[2]
            for key in (r[4], "all"):
                v = st[key]
                v[0] += float(per[i]); v[1] += int(a == yy)
                v[2] += int(a < len(r[5]) and r[5][a] == r[5][yy])
                v[3] += int(a < len(r[3]) and r[3][a] == r[3][yy])
                v[4] += 1
    return st, (auxsum / auxn if auxn else float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--init", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--aux-weight", type=float, default=0.1, help="fixed in the runbook before any A3 data")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--holdout", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--kinds", default=",".join(BC.KINDS))
    ap.add_argument("--logit-bound", type=float, default=5.0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    kinds = [k for k in args.kinds.split(",") if k]
    t0 = time.time()
    ids = V.CardIds()
    e2, dim, _ = load_targets()

    hello, rows, drop = BC.load(args.recordings, ids, 0, set(kinds))
    games = sorted(set(r[0] for r in rows))
    rng.shuffle(games)
    n_held = max(1, int(round(len(games) * args.holdout)))
    held_games = set(games[:n_held])
    train = [r for r in rows if r[0] not in held_games]
    held = [r for r in rows if r[0] in held_games]
    say("data", f"labelled={len(rows)}", f"games={len(games)}", f"held_games={n_held}",
        f"train={len(train)}", f"held={len(held)}", f"aux_weight={args.aux_weight}",
        f"e2_dim={dim}", f"load_s={time.time() - t0:.0f}")
    aux_tr, aux_he = aux_targets(train, e2), aux_targets(held, e2)
    cov = float(np.mean([m.mean() for _, m in aux_tr if len(m)]))
    say("aux_coverage", f"entities_with_e2_row={cov:.3f}")

    net = P.V7Policy.load(args.init, device=args.device)
    net.heads.logit_bound = args.logit_bound
    head = nn.Linear(net.build.d, 68).to(args.device)
    params = net.policy_parameters()
    head_ids = {id(p) for p in net.heads.parameters()}
    opt = torch.optim.AdamW(
        [{"params": [p for p in params if id(p) in head_ids], "weight_decay": args.weight_decay},
         {"params": [p for p in params if id(p) not in head_ids], "weight_decay": 0.0},
         {"params": list(head.parameters()), "weight_decay": 0.0}], lr=args.lr)

    def report(ep, st, extra=""):
        a = BC.fmt(st, "all")
        say(f"epoch={ep}", f"held_ce={a['ce']:.4f}", f"held_top1={a['top1']:.4f}",
            f"held_cls1={a['cls1']:.4f}", f"held_type1={a['type1']:.4f}{extra}")
        for k in kinds:
            f = BC.fmt(st, k)
            if f:
                say(f"epoch={ep}", f"kind={k}", f"n={f['n']}", f"held_ce={f['ce']:.4f}",
                    f"top1={f['top1']:.4f}", f"cls1={f['cls1']:.4f}")
        return a

    net.eval(); head.eval()
    st0, ax0 = run_epoch(net, head, held, aux_he, args)
    a0 = report(0, st0, f"|aux_bce={ax0:.4f}")
    best = (a0["ce"], 0, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}, st0)
    bad = 0
    for ep in range(1, args.epochs + 1):
        te = time.time()
        net.train(); head.train()
        tr_st, tr_ax = run_epoch(net, head, train, aux_tr, args, opt, rng)
        net.eval(); head.eval()
        st, ax = run_epoch(net, head, held, aux_he, args)
        a = report(ep, st, f"|train_ce={BC.fmt(tr_st, 'all')['ce']:.4f}|train_aux={tr_ax:.4f}"
                           f"|held_aux={ax:.4f}|s={time.time() - te:.0f}")
        if a["ce"] < best[0] - 1e-4:
            best = (a["ce"], ep, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}, st)
            bad = 0
        else:
            bad += 1
            if bad >= args.patience:
                say("early_stop", f"epoch={ep}", f"best_epoch={best[1]}")
                break
    net.load_state_dict(best[2])
    cfg = dict(net.config)
    cfg["logit_bound"] = args.logit_bound
    per_kind = {k: BC.fmt(best[3], k) for k in kinds if BC.fmt(best[3], k)}
    ab = BC.fmt(best[3], "all")
    blob = {"net": {k: v.cpu() for k, v in net.state_dict().items()}, "opt": None,
            "episodes": 0, "updates": 0, "arch": "v7", "dims": net.dims(), "config": cfg,
            "bc": {"init": os.path.abspath(args.init), "aux_weight": args.aux_weight,
                   "labelled": len(rows), "games": len(games), "held_games": n_held, "kinds": kinds,
                   "best_epoch": best[1], "held_ce": best[0], "held_top1": ab["top1"],
                   "held_cls1": ab["cls1"], "held_type1": ab["type1"], "per_kind": per_kind,
                   "lr": args.lr, "batch": args.batch, "seed": args.seed}}
    tmp = args.out + ".tmp"
    torch.save(blob, tmp)
    os.replace(tmp, args.out)
    say("saved", args.out, f"best_epoch={best[1]}", f"held_ce={best[0]:.4f}",
        f"held_top1={ab['top1']:.4f}")
    prio = per_kind.get("prio", {}).get("top1")
    if prio is not None:
        say("A3_agreement_clause", f"priority_top1={prio:.4f}", "vs_13b=0.876",
            f"drop={0.876 - prio:+.4f}", "bar=drop <= 0.02")
    say("done", f"wall_s={time.time() - t0:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
