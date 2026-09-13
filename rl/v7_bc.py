#!/usr/bin/env python3
"""7d piece (2): behaviour cloning of the CP7 teacher on the v7 wire.

    python3 rl/v7_bc.py --init INIT.pt --out bc.pt [--device cuda] REC.jsonl [REC.jsonl ...]

Input: recordings written by the echo server from an rl.agent=cp7 driver job
(rl/xmage-src/CP7TeacherPlayer.java): consult lines that carry "y" (the index
of the candidate CP7 acted on; 0 = passed; -1 = outside the set) and one
{"t":"end"} line per game.  Consults with y < 0 (or y >= k) are dropped and
counted.  Hold-out: 10 % of GAMES (split by episode, never by consult), for
early stopping on held-out cross-entropy.

Model: the lane's v7 checkpoint format (P10INIT init.pt in, bc.pt out with
the same keys: net / opt=None / episodes=0 / updates=0 / arch / dims /
config), loaded and scored exactly as rl/v7_init_logits.py does - every
consult with a FRESH heads state (memoryless; the lane's within-game LSTM
state is not trained here), no deck context (the hello carries none).
Loss: cross-entropy over the candidate logits with the label; AdamW with the
decay on the heads only (the B2/C1 optimiser shape); grad-norm clip 1.0.
Prints per epoch train / held-out CE, held-out top-1 agreement and type
agreement (argmax type == label type); the label type census; and, at the
end, the census commands to run on bc.pt.
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
import torch                      # noqa: E402
import torch.nn.functional as F   # noqa: E402
import v7_obs as V                # noqa: E402
import v7_policy as P             # noqa: E402

TYPES = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]


def load(paths, ids, limit):
    """-> hello, list of (game_key, obs, y, cand_types), drop counters"""
    hello = None
    rows = []
    drop = collections.Counter()
    for p in paths:
        ep = 0
        with open(p, "rb") as fh:
            for raw in fh:
                if not raw.strip():
                    continue
                m = json.loads(raw)
                t = m.get("t")
                if t == "hello":
                    hello = hello or m
                elif t == "end":
                    ep += 1
                elif t == "consult" and "v7_ent" in m:
                    if "y" not in m:
                        drop["no_label"] += 1
                        continue
                    y = int(m["y"])
                    k = len(m["v7_cand_type"])
                    if y < 0:
                        drop["outside"] += 1
                        continue
                    if y >= k:
                        drop["y_ge_k"] += 1
                        continue
                    try:
                        obs = V.compact(V.parse_consult(m, ids, hello))
                    except ValueError as exc:
                        drop["bad_consult"] += 1
                        if drop["bad_consult"] <= 3:
                            print(f"BC|bad_consult|{exc}", flush=True)
                        continue
                    rows.append(((os.path.basename(p), ep), obs, y, list(m["v7_cand_type"])))
                    if limit and len(rows) >= limit:
                        return hello, rows, drop
    return hello, rows, drop


def batches(rows, size, shuffle, rng):
    idx = list(range(len(rows)))
    if shuffle:
        rng.shuffle(idx)
    for s in range(0, len(idx), size):
        yield [rows[i] for i in idx[s:s + size]]


def run_epoch(net, rows, args, opt=None, rng=None):
    """-> mean CE, top-1 agreement, type agreement, n"""
    ce_sum = 0.0
    top1 = typ1 = n = 0
    for chunk in batches(rows, args.batch, opt is not None, rng):
        b = V.collate([r[1] for r in chunk])
        b = {k: (v.to(args.device) if torch.is_tensor(v) else v) for k, v in b.items()}
        y = torch.tensor([r[2] for r in chunk], dtype=torch.long, device=args.device)
        with torch.set_grad_enabled(opt is not None):
            lg, _, _, _ = net(b, with_value=False)
            lg = lg.float()
            loss = F.cross_entropy(lg, y)
            if opt is not None:
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.policy_parameters(), args.clip)
                opt.step()
        ce_sum += float(loss) * len(chunk)
        am = lg.argmax(1).cpu()
        for i, r in enumerate(chunk):
            a = int(am[i])
            top1 += int(a == r[2])
            typ1 += int(r[3][a] == r[3][r[2]])
        n += len(chunk)
    return ce_sum / max(1, n), top1 / max(1, n), typ1 / max(1, n), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--init", required=True, help="P10INIT-style v7 init.pt (or any lane checkpoint)")
    ap.add_argument("--out", required=True, help="bc.pt, the lane checkpoint format")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--patience", type=int, default=3, help="epochs without a held-out CE improvement before stopping")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=0.01, help="AdamW decay on the heads (B2/C1 shape)")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--holdout", type=float, default=0.1, help="fraction of GAMES held out")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="cap on labelled consults loaded (0 = all)")
    ap.add_argument("--logit-bound", type=float, default=5.0, help="written into config and applied while training (the lane's --logit-bound)")
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)

    ids = V.CardIds()
    t0 = time.time()
    hello, rows, drop = load(args.recordings, ids, args.limit)
    if hello is None or not rows:
        print("BC|FAILED|no hello or no labelled consults", flush=True)
        return 1
    games = sorted(set(r[0] for r in rows))
    rng.shuffle(games)
    n_held = max(1, int(round(len(games) * args.holdout)))
    held_games = set(games[:n_held])
    train = [r for r in rows if r[0] not in held_games]
    held = [r for r in rows if r[0] in held_games]
    lab = collections.Counter(TYPES[r[3][r[2]]] for r in rows)
    print(f"BC|data|files={len(args.recordings)}|labelled={len(rows)}|games={len(games)}|held_games={n_held}"
          f"|train={len(train)}|held={len(held)}|dropped={dict(drop)}|load_s={time.time() - t0:.0f}", flush=True)
    print("BC|labels|" + "|".join(f"{k}={lab[k]}" for k in TYPES if lab[k]), flush=True)
    avail = collections.Counter()
    for r in rows:
        for ty in set(r[3]):
            avail[TYPES[ty]] += 1
    print("BC|offered|" + "|".join(f"{k}={avail[k]}" for k in TYPES if avail[k]), flush=True)

    net = P.V7Policy.load(args.init, device=args.device)
    net.heads.logit_bound = args.logit_bound
    params = net.policy_parameters()
    head_ids = {id(p) for p in net.heads.parameters()}
    heads = [p for p in params if id(p) in head_ids]
    rest = [p for p in params if id(p) not in head_ids]
    opt = torch.optim.AdamW([{"params": heads, "weight_decay": args.weight_decay},
                             {"params": rest, "weight_decay": 0.0}], lr=args.lr)
    init_ep = torch.load(args.init, map_location="cpu", weights_only=False).get("episodes", 0)

    net.eval()
    ce0, t10, ty0, _ = run_epoch(net, held, args)
    print(f"BC|epoch=0|held_ce={ce0:.4f}|held_top1={t10:.3f}|held_type1={ty0:.3f}|init_episodes={init_ep}", flush=True)
    best = (ce0, 0, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}, t10, ty0)
    bad = 0
    for ep in range(1, args.epochs + 1):
        te = time.time()
        net.train()
        tr_ce, tr_top1, tr_ty, _ = run_epoch(net, train, args, opt, rng)
        net.eval()
        h_ce, h_top1, h_ty, _ = run_epoch(net, held, args)
        print(f"BC|epoch={ep}|train_ce={tr_ce:.4f}|train_top1={tr_top1:.3f}|held_ce={h_ce:.4f}"
              f"|held_top1={h_top1:.3f}|held_type1={h_ty:.3f}|s={time.time() - te:.0f}", flush=True)
        if h_ce < best[0] - 1e-4:
            best = (h_ce, ep, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}, h_top1, h_ty)
            bad = 0
        else:
            bad += 1
            if bad >= args.patience:
                print(f"BC|early_stop|epoch={ep}|best_epoch={best[1]}", flush=True)
                break
    net.load_state_dict(best[2])
    cfg = dict(net.config)
    cfg["logit_bound"] = args.logit_bound
    blob = {"net": {k: v.cpu() for k, v in net.state_dict().items()}, "opt": None,
            "episodes": 0, "updates": 0, "arch": "v7", "dims": net.dims(), "config": cfg,
            "bc": {"init": os.path.abspath(args.init), "recordings": [os.path.abspath(p) for p in args.recordings],
                   "labelled": len(rows), "games": len(games), "held_games": n_held,
                   "best_epoch": best[1], "held_ce": best[0], "held_top1": best[3], "held_type1": best[4],
                   "lr": args.lr, "weight_decay": args.weight_decay, "batch": args.batch, "seed": args.seed}}
    tmp = args.out + ".tmp"
    torch.save(blob, tmp)
    os.replace(tmp, args.out)
    print(f"BC|saved={args.out}|best_epoch={best[1]}|held_ce={best[0]:.4f}|held_top1={best[3]:.3f}"
          f"|held_type1={best[4]:.3f}|wall_s={time.time() - t0:.0f}", flush=True)
    rec = " ".join(os.path.join(HERE, "artifacts", "v7", "wire3a", f"7c_W0Base_{s}.jsonl") for s in ("p1", "p99", "sf"))
    print("BC|census|python3 rl/v7_init_logits.py --ckpt %s --logit-bound %g --device cpu --limit 1500 %s" % (args.out, args.logit_bound, rec))
    print("BC|census|python3 rl/v7_land_census.py --ckpt %s --logit-bound %g --device cpu %s" % (args.out, args.logit_bound, rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
