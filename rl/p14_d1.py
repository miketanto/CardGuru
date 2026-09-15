#!/usr/bin/env python3
"""Phase 14 D1 (rl/PHASE14-DIAG.md): can the network predict game outcomes from what it sees?

    python3 rl/p14_d1.py --ckpt rl/artifacts/v7/13/bc/bc.pt --out rl/artifacts/v7/14/d1 REC.jsonl [...]

Data: every consult with a v7 state in the 13a recordings (labelled or not) gets the recorded seat's
final outcome r (the game's {"t":"end","r":...}) as its target.  Hold-out: the SAME 10 % of games as
13b (rl/v7_bc.py: games with >= 1 labelled consult of the cloned kinds, sorted, random.Random(0).shuffle,
first round(0.1 n) held).  Early stopping never sees the hold-out: a validation split of 10 % of the
TRAINING games (random.Random(1)) decides it.

Models:
  N1  the v7 network from bc.pt; its critic (rl/v7_value.py ValueTrunk: its own token builders, its own
      4-layer encoder and value MLP, sharing only the card table with the policy - the value path the
      lane's policy_server.py trains, called without privileged rows because the recordings carry none)
      trained on MSE to r.  bc.pt's critic was never trained by BC (v7_bc.py runs with_value=False), so N1
      starts from the fresh P10INIT critic.
  N2  the clone's own representation, frozen: the game vector the policy heads return
      (V7Policy.forward -> game_vec, fresh heads state per consult as in v7_bc.py), from an untouched load of
      bc.pt, with a value MLP of the critic's shape (LayerNorm, Linear, GELU, Linear) trained on top.
  B0  logistic regression on scalars read from the same consults (v7_game / v7_players, StateEncoder.v7Game
      / v7Player): life me/opp, hand size me/opp, lands me/opp, non-land permanents me/opp (the observation
      has no creature count; permanents - lands stands in), global turn, my-turn flag.  E[r] = 2 p - 1.

Readings on held-out games: EV = 1 - MSE / Var(r) and AUC of the sign (r = 0 excluded), overall and by
own-turn stage (own turn = ceil(global turn / 2): early <= 6, mid 7-12, late >= 13); 95 % intervals from
1,000 bootstrap resamples of held-out GAMES (consults of one game move together).
"""
import argparse
import collections
import json
import math
import os
import random
import resource
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
from v7_bc import kind_of, KINDS   # noqa: E402

B0_NAMES = ["life_me", "life_opp", "hand_me", "hand_opp", "lands_me", "lands_opp",
            "nonland_perm_me", "nonland_perm_opp", "turn", "my_turn"]
STAGES = ["early", "mid", "late"]


def say(*a):
    print("D1|" + "|".join(str(x) for x in a), flush=True)


def b0_feats(m):
    g = m["v7_game"]
    me, op = m["v7_players"][0], m["v7_players"][1]
    T = int(round(g[0] * 30))
    f = [me[0] * 20, op[0] * 20, me[2] * 10, op[2] * 10, me[13] * 10, op[13] * 10,
         me[15] * 20 - me[13] * 10, op[15] * 20 - op[13] * 10, T, g[1]]
    return f, T


def stage_of(T):
    own = (T + 1) // 2
    return 0 if own <= 6 else (1 if own <= 12 else 2)


def load(paths, ids, kinds):
    hello = None
    rows = []          # [game_key, obs, b0, stage, r]
    lab_games = set()
    drop = collections.Counter()
    for p in paths:
        ep = 0
        pend = []
        hello_f = None
        with open(p, "rb") as fh:
            for raw in fh:
                if not raw.strip():
                    continue
                m = json.loads(raw)
                t = m.get("t")
                if t == "hello":
                    hello = hello or m
                    hello_f = hello_f or m
                elif t == "end":
                    r = float(m.get("r", 0.0))
                    for x in pend:
                        x[4] = r
                    rows.extend(pend)
                    pend = []
                    ep += 1
                elif t == "consult" and "v7_ent" in m:
                    key = (os.path.basename(p), ep)
                    if "y" in m:
                        y = int(m["y"])
                        ct = m["v7_cand_type"]
                        if 0 <= y < len(ct) and kind_of(ct) in kinds:
                            lab_games.add(key)
                    try:
                        obs = V.compact(V.parse_consult(m, ids, hello_f or hello))
                    except ValueError:
                        drop["bad_consult"] += 1
                        continue
                    f, T = b0_feats(m)
                    pend.append([key, obs, f, stage_of(T), None])
        drop["unfinished_game_consults"] += len(pend)
    return rows, lab_games, drop


def ev(pred, r):
    v = r.var()
    return float(1.0 - ((pred - r) ** 2).mean() / v) if v > 1e-12 else float("nan")


def auc(s, y):
    m = y != 0
    s, pos = s[m], y[m] > 0
    n1 = int(pos.sum())
    n0 = len(pos) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ss = s[order]
    _, inv, counts = np.unique(ss, return_inverse=True, return_counts=True)
    csum = np.cumsum(counts)
    avg = csum - (counts - 1) / 2.0
    ranks = np.empty(len(s))
    ranks[order] = avg[inv]
    return float((ranks[pos].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


# ---------------------------------------------------------------- N1 / N2 helpers
def to_dev(b, dev):
    return {k: (v.to(dev) if torch.is_tensor(v) else v) for k, v in b.items()}


def batches(idx, size, shuffle, rng):
    idx = list(idx)
    if shuffle:
        rng.shuffle(idx)
    for s in range(0, len(idx), size):
        yield idx[s:s + size]


def critic_predict(net, rows, idx, dev, bs=128):
    net.eval()
    out = np.zeros(len(idx), dtype=np.float64)
    with torch.no_grad():
        pos = 0
        for ch in batches(idx, bs, False, None):
            b = to_dev(V.collate([rows[i][1] for i in ch]), dev)
            v = net.critic(b).float().cpu().numpy()
            out[pos:pos + len(ch)] = v
            pos += len(ch)
    return out


def fit_n1(rows, tr, va, args, dev):
    net = P.V7Policy.load(args.ckpt, device=dev)
    params = [p for p in net.critic.parameters() if p.requires_grad]
    say("N1", "params", sum(p.numel() for p in params))
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)
    rng = random.Random(2)
    r_all = np.array([x[4] for x in rows])
    best = (float("inf"), 0, None)
    bad = 0
    for ep in range(1, args.epochs + 1):
        t0 = time.time()
        net.train()
        tl, tn = 0.0, 0
        for ch in batches(tr, args.batch, True, rng):
            b = to_dev(V.collate([rows[i][1] for i in ch]), dev)
            y = torch.tensor([rows[i][4] for i in ch], dtype=torch.float32, device=dev)
            v = net.critic(b).float()
            loss = F.mse_loss(v, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            tl += float(loss) * len(ch)
            tn += len(ch)
        pv = critic_predict(net, rows, va, dev)
        vm = float(((pv - r_all[va]) ** 2).mean())
        say("N1", f"epoch={ep}", f"train_mse={tl / tn:.4f}", f"val_mse={vm:.4f}",
            f"val_ev={ev(pv, r_all[va]):.4f}", f"s={time.time() - t0:.0f}")
        if vm < best[0] - 1e-4:
            best = (vm, ep, {k: v.detach().cpu().clone() for k, v in net.critic.state_dict().items()})
            bad = 0
        else:
            bad += 1
            if bad >= args.patience:
                say("N1", "early_stop", f"epoch={ep}", f"best_epoch={best[1]}")
                break
    net.critic.load_state_dict(best[2])
    say("N1", "best_epoch", best[1], f"val_mse={best[0]:.4f}")
    return net


def game_vectors(rows, args, dev):
    net = P.V7Policy.load(args.ckpt, device=dev)
    net.eval()
    out = []
    with torch.no_grad():
        for ch in batches(range(len(rows)), 128, False, None):
            b = to_dev(V.collate([rows[i][1] for i in ch]), dev)
            _, _, gv, _ = net(b, with_value=False)
            out.append(gv.reshape(len(ch), -1).float().cpu())
    del net
    torch.cuda.empty_cache()
    return torch.cat(out)


def fit_mlp(X, r, tr, va, dev, lr=1e-3, epochs=300, patience=15, bs=256):
    D = X.shape[1]
    torch.manual_seed(0)
    head = nn.Sequential(nn.LayerNorm(D), nn.Linear(D, D), nn.GELU(), nn.Linear(D, 1)).to(dev)
    opt = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=0.01)
    Xd, rd = X.to(dev), torch.tensor(r, dtype=torch.float32, device=dev)
    tri = torch.tensor(tr, device=dev)
    vai = torch.tensor(va, device=dev)
    best = (float("inf"), 0, None)
    bad = 0
    g = torch.Generator(device="cpu").manual_seed(3)
    for ep in range(1, epochs + 1):
        head.train()
        perm = tri[torch.randperm(len(tri), generator=g).to(dev)]
        for s in range(0, len(perm), bs):
            i = perm[s:s + bs]
            loss = F.mse_loss(head(Xd[i]).squeeze(-1), rd[i])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
        head.eval()
        with torch.no_grad():
            vm = float(F.mse_loss(head(Xd[vai]).squeeze(-1), rd[vai]))
        if vm < best[0] - 1e-5:
            best = (vm, ep, {k: v.detach().clone() for k, v in head.state_dict().items()})
            bad = 0
        else:
            bad += 1
            if bad >= patience:
                break
    head.load_state_dict(best[2])
    head.eval()
    with torch.no_grad():
        pred = head(Xd).squeeze(-1).cpu().numpy().astype(np.float64)
    say("N2", "best_epoch", best[1], f"val_mse={best[0]:.4f}", f"dim={D}")
    return pred


def fit_b0(F0, r, tr, va):
    X = torch.tensor(F0, dtype=torch.float64)
    mu, sd = X[tr].mean(0), X[tr].std(0).clamp_min(1e-6)
    Z = (X - mu) / sd
    y = torch.tensor((r + 1) / 2, dtype=torch.float64)
    w = torch.zeros(Z.shape[1], dtype=torch.float64, requires_grad=True)
    c = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, c], lr=1, max_iter=500, line_search_fn="strong_wolfe")
    tri = torch.tensor(tr)

    def closure():
        opt.zero_grad()
        z = Z[tri] @ w + c
        loss = F.binary_cross_entropy_with_logits(z, y[tri]) + 1e-4 * (w ** 2).sum()
        loss.backward()
        return loss
    opt.step(closure)
    with torch.no_grad():
        p = torch.sigmoid(Z @ w + c).numpy()
    say("B0", "coef_std", ",".join(f"{n}={float(v):+.3f}" for n, v in zip(B0_NAMES, w.detach())),
        f"intercept={float(c):+.3f}")
    return 2 * p - 1


# ---------------------------------------------------------------- report
def metrics(pred, r, gid, stage, idx, boot, rng):
    """point + bootstrap over games for overall and each stage"""
    idx = np.asarray(idx)
    games = np.unique(gid[idx])
    by_game = {g: idx[gid[idx] == g] for g in games}
    parts = {"all": None, "early": 0, "mid": 1, "late": 2}
    res = {}
    for name, st in parts.items():
        def calc(ix):
            if st is not None:
                ix = ix[stage[ix] == st]
            if len(ix) < 2:
                return float("nan"), float("nan"), 0
            return ev(pred[ix], r[ix]), auc(pred[ix], r[ix]), len(ix)
        e, a, n = calc(idx)
        es, as_ = [], []
        for _ in range(boot):
            pick = rng.choice(games, size=len(games), replace=True)
            ix = np.concatenate([by_game[g] for g in pick])
            be, ba, _ = calc(ix)
            es.append(be)
            as_.append(ba)
        es, as_ = np.array(es), np.array(as_)
        ng = len(np.unique(gid[idx][stage[idx] == st])) if st is not None else len(games)
        res[name] = {"n": n, "games": int(ng), "ev": e, "ev_lo": float(np.nanpercentile(es, 2.5)),
                     "ev_hi": float(np.nanpercentile(es, 97.5)), "auc": a,
                     "auc_lo": float(np.nanpercentile(as_, 2.5)), "auc_hi": float(np.nanpercentile(as_, 97.5))}
    return res


def paired_diff(pa, pb, r, gid, idx, boot, rng):
    idx = np.asarray(idx)
    games = np.unique(gid[idx])
    by_game = {g: idx[gid[idx] == g] for g in games}
    d0 = ev(pa[idx], r[idx]) - ev(pb[idx], r[idx])
    ds = []
    for _ in range(boot):
        ix = np.concatenate([by_game[g] for g in rng.choice(games, size=len(games), replace=True)])
        ds.append(ev(pa[ix], r[ix]) - ev(pb[ix], r[ix]))
    return d0, float(np.nanpercentile(ds, 2.5)), float(np.nanpercentile(ds, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--patience", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--skip-n1", action="store_true", help="smoke only")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    torch.manual_seed(0)
    dev = args.device
    t0 = time.time()
    ids = V.CardIds()
    rows, lab_games, drop = load(args.recordings, ids, set(KINDS))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    # the 13b split, reproduced exactly (v7_bc.py: sorted labelled games, Random(seed 0).shuffle, first round(0.1 n))
    games = sorted(lab_games)
    rng0 = random.Random(0)
    rng0.shuffle(games)
    n_held = max(1, int(round(len(games) * 0.1)))
    held_games = set(games[:n_held])
    train_games = sorted(set(x[0] for x in rows) - held_games)
    rng1 = random.Random(1)
    rng1.shuffle(train_games)
    val_games = set(train_games[:max(1, int(round(len(train_games) * 0.1)))])
    gkeys = sorted(set(x[0] for x in rows))
    gindex = {g: i for i, g in enumerate(gkeys)}
    gid = np.array([gindex[x[0]] for x in rows])
    stage = np.array([x[3] for x in rows])
    r = np.array([x[4] for x in rows], dtype=np.float64)
    ho = [i for i, x in enumerate(rows) if x[0] in held_games]
    va = [i for i, x in enumerate(rows) if x[0] in val_games]
    tr = [i for i, x in enumerate(rows) if x[0] not in held_games and x[0] not in val_games]
    say("data", f"files={len(args.recordings)}", f"consults={len(rows)}", f"games={len(gkeys)}",
        f"labelled_games={len(lab_games)}", f"held_games={n_held}", f"val_games={len(val_games)}",
        f"train={len(tr)}", f"val={len(va)}", f"held={len(ho)}", f"dropped={dict(drop)}",
        f"load_s={time.time() - t0:.0f}", f"rss_mb={rss:.0f}")
    say("data", "r_mean_held=%.3f" % r[ho].mean(), "r_var_held=%.3f" % r[ho].var(),
        "draws_held=%d" % int((r[ho] == 0).sum()),
        "stage_mix_held=" + ",".join(f"{s}:{int((stage[ho] == k).sum())}" for k, s in enumerate(STAGES)))

    preds = {}
    F0 = np.array([x[2] for x in rows], dtype=np.float64)
    preds["B0"] = fit_b0(F0, r, tr, va)
    t1 = time.time()
    X = game_vectors(rows, args, dev)
    say("N2", f"game_vec_s={time.time() - t1:.0f}")
    preds["N2"] = fit_mlp(X, r, tr, va, dev)
    del X
    if not args.skip_n1:
        net = fit_n1(rows, tr, va, args, dev)
        preds["N1"] = critic_predict(net, rows, list(range(len(rows))), dev)
        del net

    rng = np.random.default_rng(0)
    out = {"n_consults": len(rows), "held_games": n_held, "b0_features": B0_NAMES, "models": {}}
    for name in ("N1", "N2", "B0"):
        if name not in preds:
            continue
        res = metrics(preds[name], r, gid, stage, ho, args.boot, rng)
        out["models"][name] = res
        for part, v in res.items():
            say("held", f"model={name}", f"stage={part}", f"n={v['n']}", f"games={v['games']}",
                f"ev={v['ev']:.3f}", f"ev_ci=[{v['ev_lo']:.3f},{v['ev_hi']:.3f}]",
                f"auc={v['auc']:.3f}", f"auc_ci=[{v['auc_lo']:.3f},{v['auc_hi']:.3f}]")
    for a, b in (("N1", "B0"), ("N2", "B0"), ("N1", "N2")):
        if a in preds and b in preds:
            d, lo, hi = paired_diff(preds[a], preds[b], r, gid, ho, args.boot, rng)
            out.setdefault("diffs", {})[f"{a}-{b}"] = {"ev_diff": d, "lo": lo, "hi": hi}
            say("diff", f"{a}-{b}", f"ev_diff={d:+.3f}", f"ci=[{lo:+.3f},{hi:+.3f}]")
    if "N1" in preds:
        e1 = out["models"]["N1"]["all"]["ev"]
        eb = out["models"]["B0"]["all"]["ev"]
        if e1 >= 0.35 and e1 - eb >= 0.05:
            rd = "predicts"
        elif e1 <= 0.25:
            rd = "barely_predicts"
        else:
            rd = "partial"
        out["reading"] = rd
        say("reading", rd, f"N1_ev={e1:.3f}", f"B0_ev={eb:.3f}", f"N1-B0={e1 - eb:+.3f}",
            "B0>=N1" if eb >= e1 else "N1>B0")
    with open(os.path.join(args.out, "d1.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    say("done", f"wall_s={time.time() - t0:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
