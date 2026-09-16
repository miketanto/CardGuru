#!/usr/bin/env python3
"""Phase 15 A0 (rl/PHASE15-ARCH.md): can the network fit at all?

A deliberate memorisation task on a tiny slice of the 13a recordings: 2,000
labelled consults from 40 games, no weight decay, no early stop, 40 epochs,
and separately the value head on those same 40 games' outcomes.

    python3 rl/p15_a0.py --init rl/artifacts/v7/13/init_on_s13.pt \
        --out rl/artifacts/v7/15/a0 REC.jsonl [...]

Pass (pre-registered): training top-1 >= 0.99 AND training value EV >= 0.95.
Fail = the plumbing is broken (masking, the frozen-table adapter, gradients
reaching the card path) and the phase stops.

Reuses rl/v7_bc.py (load / run_epoch / ceilings: the same parse, the same
memoryless scoring, the same candidate cross-entropy as 13b) and the value
path rl/p14_d1.py trains (V7Policy.critic on MSE to the recorded seat's
final outcome).  Nothing here holds anything out: this measures reachability
of a fit, not generalisation.
"""
import argparse
import json
import os
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                 # noqa: E402
import torch                       # noqa: E402
import torch.nn.functional as F    # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_policy as P              # noqa: E402
import v7_bc as BC                 # noqa: E402
import p14_d1 as D1                # noqa: E402


def say(*a):
    print("A0|" + "|".join(str(x) for x in a), flush=True)


def card_path_grads(net):
    """grad norms on the pieces A0 exists to check: the frozen table's adapter and
    the Phase 10 candidate-to-card pool."""
    out = {}
    for name, mod in (("adapter", net.table.adapter),
                      ("cand_ref", getattr(net.build, "cand_ref", None)),
                      ("zone_mlp0", net.build.zone_mlps[0]),
                      ("pointer", net.heads.pointer)):
        if mod is None:
            out[name] = None
            continue
        g = [p.grad for p in mod.parameters() if p.grad is not None]
        out[name] = float(torch.sqrt(sum((x.float() ** 2).sum() for x in g))) if g else 0.0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--init", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--games", type=int, default=40)
    ap.add_argument("--consults", type=int, default=2000)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--logit-bound", type=float, default=5.0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    torch.manual_seed(args.seed)
    dev = args.device
    t0 = time.time()
    ids = V.CardIds()

    # ---- policy slice: the first --games games, capped at --consults labelled rows
    hello, rows, drop = BC.load(args.recordings, ids, 0, set(BC.KINDS))
    # games are taken round-robin over the given files, so a slice of two lanes
    # (CP7 vs the heuristic / CP7 mirror) carries both outcome populations
    per_file = {}
    for r in rows:
        per_file.setdefault(r[0][0], [])
        if r[0] not in per_file[r[0][0]]:
            per_file[r[0][0]].append(r[0])
    files = sorted(per_file)
    quota = -(-args.games // len(files))
    games = set()
    for f in files:
        for g in per_file[f][:quota]:
            if len(games) < args.games:
                games.add(g)
    keep = []
    for r in rows:
        if r[0] in games:
            keep.append(r)
            if len(keep) >= args.consults:
                break
    say("data", f"files={len(args.recordings)}", f"games={len(games)}", f"consults={len(keep)}",
        f"dropped={dict(drop)}", f"load_s={time.time() - t0:.0f}")
    for k, (n, cef, t1c, ncls) in sorted(BC.ceilings(keep).items()):
        say("ceiling", f"kind={k}", f"n={n}", f"ce_floor={cef:.4f}", f"top1_ceiling={t1c:.3f}")

    net = P.V7Policy.load(args.init, device=dev)
    net.heads.logit_bound = args.logit_bound
    params = net.policy_parameters()
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)     # no weight decay, as pre-registered
    say("net", f"cand_refers_pool={net.config.get('cand_refers_pool', False)}",
        f"policy_params={sum(p.numel() for p in params)}")
    ea = types.SimpleNamespace(batch=args.batch, device=dev, clip=args.clip)
    rng = __import__("random").Random(args.seed)

    grads = None
    for ep in range(1, args.epochs + 1):
        te = time.time()
        net.train()
        tr = BC.fmt(BC.run_epoch(net, keep, ea, opt, rng), "all")
        if ep == 1:
            grads = card_path_grads(net)
            say("grad_after_first_epoch", json.dumps(grads))
        if ep % 5 == 0 or ep == 1 or ep == args.epochs:
            say(f"epoch={ep}", f"train_ce={tr['ce']:.4f}", f"train_top1={tr['top1']:.3f}",
                f"s={time.time() - te:.0f}")
    net.eval()
    fin = BC.fmt(BC.run_epoch(net, keep, ea), "all")
    per_kind = {k: BC.fmt(BC.run_epoch(net, [r for r in keep if r[4] == k], ea), "all")
                for k in sorted(set(r[4] for r in keep))}
    say("policy_final", f"n={fin['n']}", f"ce={fin['ce']:.4f}", f"top1={fin['top1']:.4f}",
        f"cls1={fin['cls1']:.4f}", f"type1={fin['type1']:.4f}")
    for k, f in per_kind.items():
        say("policy_final", f"kind={k}", f"n={f['n']}", f"ce={f['ce']:.4f}", f"top1={f['top1']:.4f}")
    del opt
    torch.cuda.empty_cache()

    # ---- value head on the SAME 40 games' outcomes
    vrows, lab_games, vdrop = D1.load(args.recordings, ids, set(BC.KINDS))
    vrows = [x for x in vrows if x[0] in games]
    r = np.array([x[4] for x in vrows], dtype=np.float64)
    say("value_data", f"consults={len(vrows)}", f"games={len(set(x[0] for x in vrows))}",
        f"r_mean={r.mean():.3f}", f"r_var={r.var():.4f}", f"dropped={dict(vdrop)}")
    vnet = P.V7Policy.load(args.init, device=dev)
    vparams = [p for p in vnet.critic.parameters() if p.requires_grad]
    vopt = torch.optim.AdamW(vparams, lr=args.lr, weight_decay=0.0)
    vrng = __import__("random").Random(args.seed)
    idx = list(range(len(vrows)))
    for ep in range(1, args.epochs + 1):
        te = time.time()
        vnet.train()
        tl, tn = 0.0, 0
        for ch in D1.batches(idx, args.batch, True, vrng):
            b = D1.to_dev(V.collate([vrows[i][1] for i in ch]), dev)
            y = torch.tensor([vrows[i][4] for i in ch], dtype=torch.float32, device=dev)
            v = vnet.critic(b).float()
            loss = F.mse_loss(v, y)
            vopt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(vparams, 1.0)
            vopt.step()
            tl += float(loss) * len(ch)
            tn += len(ch)
        if ep % 5 == 0 or ep == 1 or ep == args.epochs:
            say(f"value_epoch={ep}", f"train_mse={tl / tn:.4f}", f"s={time.time() - te:.0f}")
    pv = D1.critic_predict(vnet, vrows, idx, dev)
    vev = D1.ev(pv, r)
    say("value_final", f"n={len(vrows)}", f"mse={float(((pv - r) ** 2).mean()):.4f}", f"ev={vev:.4f}")

    top1 = fin["top1"]
    reading = "pass" if (top1 >= 0.99 and vev >= 0.95) else "fail"
    say("READING", reading, f"train_top1={top1:.4f}", f"train_value_ev={vev:.4f}",
        "bar=top1>=0.99 and value_ev>=0.95")
    with open(os.path.join(args.out, "a0.json"), "w") as fh:
        json.dump({"games": len(games), "consults": len(keep), "epochs": args.epochs,
                   "policy": fin, "per_kind": per_kind, "value_consults": len(vrows),
                   "value_ev": vev, "value_mse": float(((pv - r) ** 2).mean()),
                   "grad_after_first_epoch": grads, "reading": reading}, fh, indent=1)
    say("done", f"wall_s={time.time() - t0:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
