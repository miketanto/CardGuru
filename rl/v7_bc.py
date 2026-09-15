#!/usr/bin/env python3
"""7d piece (2) + Phase 13b: behaviour cloning of the CP7 teacher on the v7 wire.

    python3 rl/v7_bc.py --init INIT.pt --out bc.pt [--device cuda] [--kinds prio,target,attack,block]
        REC.jsonl [REC.jsonl ...]

Input: recordings written by the echo server from an rl.agent=cp7 driver job
(rl/xmage-src/CP7TeacherPlayer.java): consult lines that carry "y" (the index
of the candidate CP7 chose; -1 = outside the set) and one {"t":"end"} line per
game.  Consults with y < 0 (or y >= k) are dropped and counted.  Hold-out: 10 %
of GAMES (split by episode, never by consult), for early stopping on held-out
cross-entropy.

Decision KIND of a consult (13b; the wire carries no site), from its candidate
types: prio (any LAND/SPELL/ACTIVATE; index 0 is PASS), target (all TARGET),
attack (any ATTACK; the empty subset is typed PASS), block (any BLOCK), trivial
(PASS-only joint consult, k = 1).  --kinds restricts training to the listed
kinds (a kind that fails the 13a labelled-fraction gate is not cloned); trivial
consults carry no gradient and are dropped.

Model: the lane's v7 checkpoint format (init.pt in, bc.pt out with the same
keys: net / opt=None / episodes=0 / updates=0 / arch / dims / config), loaded
and scored exactly as rl/v7_init_logits.py does - every consult with a FRESH
heads state (memoryless), no deck context.  Loss: cross-entropy over the
candidate logits with the label; AdamW with the decay on the heads only;
grad-norm clip 1.0.

Reported per kind (13b): held-out CE, top-1 (exact index), class top-1 (the
argmax's class = the label's class; class = (type, afterstate row, referent
card names), the key of policy_server._argmax_classes), type agreement; and
the COPY CEILING the Phase 7d way: the label is one index among identical
candidates, so the best reachable exact top-1 is the fraction of consults
whose label is the first index of its class, and the CE floor is the mean
log(#copies of the labelled class).
"""
import argparse
import collections
import json
import math
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
KINDS = ["prio", "target", "attack", "block"]


def kind_of(ct):
    s = set(ct)
    if s & {1, 2, 3}:
        return "prio"
    if s == {4}:
        return "target"
    if 5 in s:
        return "attack"
    if 6 in s:
        return "block"
    if s == {0}:
        return "trivial"
    return "other"


def class_ids(m):
    """per candidate: class index under policy_server._argmax_classes' key"""
    t = m["v7_cand_type"]
    rows = m["v7_cand"]
    refs = m.get("v7_cand_refers") or [[] for _ in t]
    names = m.get("v7_ent_name") or []
    keys = {}
    out = []
    for k in range(len(t)):
        nm = tuple((names[r - 3] if 0 <= r - 3 < len(names) else r) for r in refs[k])
        key = (t[k], tuple(round(float(x), 4) for x in rows[k]), nm)
        out.append(keys.setdefault(key, len(keys)))
    return out


def load(paths, ids, limit, kinds):
    """-> hello, list of rows, drop counters.  row = (game_key, obs, y, cand_types, kind, cls)"""
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
                    ct = list(m["v7_cand_type"])
                    k = len(ct)
                    if y < 0:
                        drop["outside"] += 1
                        continue
                    if y >= k:
                        drop["y_ge_k"] += 1
                        continue
                    kind = kind_of(ct)
                    if kind not in kinds:
                        drop["kind_" + kind] += 1
                        continue
                    try:
                        obs = V.compact(V.parse_consult(m, ids, hello))
                    except ValueError as exc:
                        drop["bad_consult"] += 1
                        if drop["bad_consult"] <= 3:
                            print(f"BC|bad_consult|{exc}", flush=True)
                        continue
                    rows.append(((os.path.basename(p), ep), obs, y, ct, kind, class_ids(m)))
                    if limit and len(rows) >= limit:
                        return hello, rows, drop
    return hello, rows, drop


def ceilings(rows):
    """per kind: n, CE floor (mean log #copies of the label's class), exact top-1 ceiling
    (label is the first index of its class), mean classes per consult"""
    acc = collections.defaultdict(lambda: [0, 0.0, 0, 0])
    for r in rows:
        y, cls = r[2], r[5]
        c = cls[y]
        a = acc[r[4]]
        a[0] += 1
        a[1] += math.log(sum(1 for x in cls if x == c))
        a[2] += int(cls.index(c) == y)
        a[3] += len(set(cls))
    return {k: (v[0], v[1] / v[0], v[2] / v[0], v[3] / v[0]) for k, v in acc.items()}


def batches(rows, size, shuffle, rng):
    idx = list(range(len(rows)))
    if shuffle:
        rng.shuffle(idx)
    for s in range(0, len(idx), size):
        yield [rows[i] for i in idx[s:s + size]]


def run_epoch(net, rows, args, opt=None, rng=None):
    """-> {kind or 'all': [ce_sum, top1, cls1, typ1, n]}"""
    st = collections.defaultdict(lambda: [0.0, 0, 0, 0, 0])
    for chunk in batches(rows, args.batch, opt is not None, rng):
        b = V.collate([r[1] for r in chunk])
        b = {k: (v.to(args.device) if torch.is_tensor(v) else v) for k, v in b.items()}
        y = torch.tensor([r[2] for r in chunk], dtype=torch.long, device=args.device)
        with torch.set_grad_enabled(opt is not None):
            lg, _, _, _ = net(b, with_value=False)
            lg = lg.float()
            per = F.cross_entropy(lg, y, reduction="none")
            loss = per.mean()
            if opt is not None:
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(net.policy_parameters(), args.clip)
                opt.step()
        am = lg.argmax(1).cpu()
        per = per.detach().cpu()
        for i, r in enumerate(chunk):
            a = int(am[i])
            yy = r[2]
            for key in (r[4], "all"):
                s = st[key]
                s[0] += float(per[i])
                s[1] += int(a == yy)
                s[2] += int(a < len(r[5]) and r[5][a] == r[5][yy])
                s[3] += int(a < len(r[3]) and r[3][a] == r[3][yy])
                s[4] += 1
    return st


def fmt(st, key):
    s = st.get(key)
    if not s or not s[4]:
        return None
    n = s[4]
    return {"n": n, "ce": s[0] / n, "top1": s[1] / n, "cls1": s[2] / n, "type1": s[3] / n}


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
    ap.add_argument("--kinds", default=",".join(KINDS), help="decision kinds to clone (13b)")
    ap.add_argument("--logit-bound", type=float, default=5.0, help="written into config and applied while training (the lane's --logit-bound)")
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    kinds = [k for k in args.kinds.split(",") if k]

    ids = V.CardIds()
    t0 = time.time()
    hello, rows, drop = load(args.recordings, ids, args.limit, set(kinds))
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
    kc = collections.Counter(r[4] for r in rows)
    print(f"BC|data|files={len(args.recordings)}|labelled={len(rows)}|games={len(games)}|held_games={n_held}"
          f"|train={len(train)}|held={len(held)}|kinds=" + ",".join(f"{k}:{kc[k]}" for k in kinds)
          + f"|dropped={dict(drop)}|load_s={time.time() - t0:.0f}", flush=True)
    print("BC|labels|" + "|".join(f"{k}={lab[k]}" for k in TYPES if lab[k]), flush=True)
    for part, rr in (("all", rows), ("held", held)):
        for k, (n, cef, t1c, ncls) in sorted(ceilings(rr).items()):
            print(f"BC|ceiling|{part}|kind={k}|n={n}|ce_floor={cef:.4f}|top1_ceiling={t1c:.3f}"
                  f"|classes_per_consult={ncls:.2f}", flush=True)

    net = P.V7Policy.load(args.init, device=args.device)
    net.heads.logit_bound = args.logit_bound
    params = net.policy_parameters()
    head_ids = {id(p) for p in net.heads.parameters()}
    heads = [p for p in params if id(p) in head_ids]
    rest = [p for p in params if id(p) not in head_ids]
    opt = torch.optim.AdamW([{"params": heads, "weight_decay": args.weight_decay},
                             {"params": rest, "weight_decay": 0.0}], lr=args.lr)
    init_ep = torch.load(args.init, map_location="cpu", weights_only=False).get("episodes", 0)
    print(f"BC|net|cand_refers_pool={net.config.get('cand_refers_pool', False)}|init_episodes={init_ep}", flush=True)

    def report(ep, st, extra=""):
        a = fmt(st, "all")
        print(f"BC|epoch={ep}|held_ce={a['ce']:.4f}|held_top1={a['top1']:.3f}|held_cls1={a['cls1']:.3f}"
              f"|held_type1={a['type1']:.3f}{extra}", flush=True)
        for k in kinds:
            f = fmt(st, k)
            if f:
                print(f"BC|epoch={ep}|kind={k}|n={f['n']}|held_ce={f['ce']:.4f}|top1={f['top1']:.3f}"
                      f"|cls1={f['cls1']:.3f}|type1={f['type1']:.3f}", flush=True)
        return a

    net.eval()
    st0 = run_epoch(net, held, args)
    a0 = report(0, st0)
    best = (a0["ce"], 0, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}, st0)
    bad = 0
    for ep in range(1, args.epochs + 1):
        te = time.time()
        net.train()
        tr = fmt(run_epoch(net, train, args, opt, rng), "all")
        net.eval()
        st = run_epoch(net, held, args)
        a = report(ep, st, f"|train_ce={tr['ce']:.4f}|train_top1={tr['top1']:.3f}|s={time.time() - te:.0f}")
        if a["ce"] < best[0] - 1e-4:
            best = (a["ce"], ep, {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}, st)
            bad = 0
        else:
            bad += 1
            if bad >= args.patience:
                print(f"BC|early_stop|epoch={ep}|best_epoch={best[1]}", flush=True)
                break
    net.load_state_dict(best[2])
    cfg = dict(net.config)
    cfg["logit_bound"] = args.logit_bound
    per_kind = {k: fmt(best[3], k) for k in kinds if fmt(best[3], k)}
    ab = fmt(best[3], "all")
    blob = {"net": {k: v.cpu() for k, v in net.state_dict().items()}, "opt": None,
            "episodes": 0, "updates": 0, "arch": "v7", "dims": net.dims(), "config": cfg,
            "bc": {"init": os.path.abspath(args.init), "recordings": [os.path.abspath(p) for p in args.recordings],
                   "labelled": len(rows), "games": len(games), "held_games": n_held, "kinds": kinds,
                   "best_epoch": best[1], "held_ce": best[0], "held_top1": ab["top1"], "held_type1": ab["type1"],
                   "held_cls1": ab["cls1"], "per_kind": per_kind,
                   "lr": args.lr, "weight_decay": args.weight_decay, "batch": args.batch, "seed": args.seed}}
    tmp = args.out + ".tmp"
    torch.save(blob, tmp)
    os.replace(tmp, args.out)
    print(f"BC|saved={args.out}|best_epoch={best[1]}|held_ce={best[0]:.4f}|held_top1={ab['top1']:.3f}"
          f"|held_cls1={ab['cls1']:.3f}|held_type1={ab['type1']:.3f}|wall_s={time.time() - t0:.0f}", flush=True)
    for k, f in per_kind.items():
        print(f"BC|best|kind={k}|n={f['n']}|held_ce={f['ce']:.4f}|top1={f['top1']:.3f}|cls1={f['cls1']:.3f}"
              f"|type1={f['type1']:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
