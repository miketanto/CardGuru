#!/usr/bin/env python3
"""Phase 15 A4L (rl/PHASE15-ARCH.md): per-rung transfer evaluation on the curriculum ladder.

    python3 rl/p15_a4.py --rung W1Fly --aspect-cards "Leonin Skyhunter" \
        --ckpt ZERO=.../bc_W0Base.pt --ckpt RUNG=.../bc_W1Fly.pt --ckpt JOINT=.../bc_W0Base+W1Fly.pt \
        --out DIR REC.jsonl [...]

Scores every checkpoint on the rung's OWN held-out games (its recordings, games sorted,
random.Random(0).shuffle, first 10 % held - the 13b split rule applied per rung), and
splits every held-out consult into the two populations A4L fixes in advance:

  ASPECT  the rung's new card is in the agent's hand, or on either battlefield, or is
          the referent of a candidate in that consult
  SHARED  everything else

Reported per checkpoint x population x decision kind: exact top-1, class top-1, type
agreement, the COPY CEILING of that population (the label is one index among identical
candidates - v7_bc.ceilings), the ceiling fraction, and that population's TRIVIAL
PREDICTOR.  The trivial predictor is the best single fixed index rule among {index 0,
last index, the modal label index} chosen per kind on the rung's TRAINING games and then
applied unchanged to the held-out population, so it is never fitted on what it is
compared against.

Scoring is memoryless per consult (fresh heads state), exactly as rl/v7_bc.py and
rl/v7_init_logits.py do, so these numbers are comparable with the 13b table.
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
import v7_obs as V                 # noqa: E402
import v7_policy as P              # noqa: E402
import v7_bc as BC                 # noqa: E402


def say(*a):
    print("A4|" + "|".join(str(x) for x in a), flush=True)


def norm(s):
    import unicodedata
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


def is_aspect(obs, aspect):
    """A4L's split, fixed before any data: the rung's new card in hand, on either
    battlefield, or as the referent of a candidate in this consult."""
    names = [norm(n) for n in obs.ent_name]
    hit = [j for j, n in enumerate(names) if n in aspect]
    if not hit:
        return False
    ent = obs.ent
    ref = obs.refers
    for j in hit:
        if j >= ent.shape[0]:
            continue
        row = ent[j]
        if row[0] > 0.5:                      # zone one-hot 0 = battlefield (either side)
            return True
        if row[1] > 0.5 and row[7] > 0.5:     # hand AND mine
            return True
        t = 3 + j                              # token index of this entity
        if ref.shape[1] > t and float(ref[:, t].sum()) > 0:
            return True
    return False


def predict(net, rows, device, batch=32):
    """-> arrays exact / cls / typ per row, in order"""
    ex, cl, ty = [], [], []
    net.eval()
    with torch.no_grad():
        for s in range(0, len(rows), batch):
            chunk = rows[s:s + batch]
            b = {k: (v.to(device) if torch.is_tensor(v) else v)
                 for k, v in V.collate([r[1] for r in chunk]).items()}
            lg, _, _, _ = net(b, with_value=False)
            am = lg.float().argmax(1).cpu().numpy()
            for i, r in enumerate(chunk):
                a, y = int(am[i]), r[2]
                ex.append(a == y)
                cl.append(a < len(r[5]) and r[5][a] == r[5][y])
                ty.append(a < len(r[3]) and r[3][a] == r[3][y])
    return np.array(ex), np.array(cl), np.array(ty)


def trivial_rules(train_rows):
    """per kind, the best fixed index rule chosen on TRAINING rows only"""
    by = collections.defaultdict(list)
    for r in train_rows:
        by[r[4]].append(r)
    rules = {}
    for k, rr in by.items():
        modal = collections.Counter(r[2] for r in rr).most_common(1)[0][0]
        cand = {"first": lambda r: 0, "last": lambda r: len(r[3]) - 1, f"pos{modal}": lambda r, m=modal: m}
        best, bestname = -1.0, None
        for name, fn in cand.items():
            acc = float(np.mean([fn(r) == r[2] for r in rr]))
            if acc > best:
                best, bestname = acc, name
        rules[k] = (bestname, cand[bestname], best)
    return rules


def apply_trivial(rules, rows):
    out = {}
    by = collections.defaultdict(list)
    for r in rows:
        by[r[4]].append(r)
    for k, rr in by.items():
        if k not in rules:
            continue
        name, fn, tracc = rules[k]
        out[k] = {"rule": name, "train_acc": tracc, "n": len(rr),
                  "acc": float(np.mean([fn(r) == r[2] for r in rr]))}
    if rows:
        allacc, n = 0.0, 0
        for k, v in out.items():
            allacc += v["acc"] * v["n"]
            n += v["n"]
        out["all"] = {"rule": "per-kind", "n": n, "acc": allacc / n if n else float("nan")}
    return out


def agg(rows, mask, ex, cl, ty):
    """per kind + all, over the rows selected by mask"""
    idx = np.nonzero(mask)[0]
    out = {}
    groups = collections.defaultdict(list)
    for i in idx:
        groups[rows[i][4]].append(i)
        groups["all"].append(i)
    ceil_all = BC.ceilings([rows[i] for i in idx]) if len(idx) else {}
    pooled_n = sum(v[0] for v in ceil_all.values())
    pooled_ceiling = (sum(v[0] * v[2] for v in ceil_all.values()) / pooled_n) if pooled_n else float("nan")
    for k, ii in groups.items():
        ii = np.array(ii)
        c = ceil_all.get(k)
        ceiling = c[2] if c else (pooled_ceiling if k == "all" else float("nan"))
        t1 = float(ex[ii].mean())
        out[k] = {"n": int(len(ii)), "top1": t1, "cls1": float(cl[ii].mean()),
                  "type1": float(ty[ii].mean()), "ceiling": float(ceiling),
                  "frac_of_ceiling": float(t1 / ceiling) if ceiling and ceiling == ceiling else float("nan")}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--rung", required=True)
    ap.add_argument("--aspect-cards", default="", help="comma-separated card names added at this rung")
    ap.add_argument("--ckpt", action="append", required=True, help="name=path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--holdout", type=float, default=0.1)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    aspect = set(norm(x) for x in args.aspect_cards.split(",") if x.strip())
    ids = V.CardIds()
    hello, rows, drop = BC.load(args.recordings, ids, 0, set(BC.KINDS))
    games = sorted(set(r[0] for r in rows))
    random.Random(0).shuffle(games)
    n_held = max(1, int(round(len(games) * args.holdout)))
    held_games = set(games[:n_held])
    held = [r for r in rows if r[0] in held_games]
    train = [r for r in rows if r[0] not in held_games]
    asp = np.array([is_aspect(r[1], aspect) for r in held])
    say("data", f"rung={args.rung}", f"consults={len(rows)}", f"games={len(games)}",
        f"held_games={n_held}", f"held={len(held)}", f"aspect={int(asp.sum())}",
        f"shared={int((~asp).sum())}", f"aspect_cards={sorted(aspect)}",
        f"dropped={dict(drop)}", f"load_s={time.time() - t0:.0f}")

    rules = trivial_rules(train)
    triv = {"all": apply_trivial(rules, held),
            "aspect": apply_trivial(rules, [r for r, a in zip(held, asp) if a]),
            "shared": apply_trivial(rules, [r for r, a in zip(held, asp) if not a])}
    for pop, v in triv.items():
        if "all" in v:
            say("trivial", f"pop={pop}", f"n={v['all']['n']}", f"acc={v['all']['acc']:.4f}",
                "rules=" + ",".join(f"{k}:{x['rule']}" for k, x in v.items() if k != "all"))

    out = {"rung": args.rung, "aspect_cards": sorted(aspect), "games": len(games),
           "held_games": n_held, "held_consults": len(held), "n_aspect": int(asp.sum()),
           "n_shared": int((~asp).sum()), "trivial": triv, "models": {}}
    for spec in args.ckpt:
        name, path = spec.split("=", 1)
        if not os.path.exists(path):
            say(name, "MISSING", path)
            continue
        net = P.V7Policy.load(path, device=args.device)
        ex, cl, ty = predict(net, held, args.device, args.batch)
        del net
        torch.cuda.empty_cache()
        res = {"all": agg(held, np.ones(len(held), bool), ex, cl, ty),
               "aspect": agg(held, asp, ex, cl, ty),
               "shared": agg(held, ~asp, ex, cl, ty)}
        out["models"][name] = res
        for pop in ("all", "aspect", "shared"):
            a = res[pop].get("all")
            if a:
                say(name, f"pop={pop}", f"n={a['n']}", f"top1={a['top1']:.4f}",
                    f"ceiling={a['ceiling']:.4f}", f"frac={a['frac_of_ceiling']:.4f}",
                    f"cls1={a['cls1']:.4f}", f"type1={a['type1']:.4f}")
            for k in BC.KINDS:
                kk = res[pop].get(k)
                if kk:
                    say(name, f"pop={pop}", f"kind={k}", f"n={kk['n']}", f"top1={kk['top1']:.4f}",
                        f"ceiling={kk['ceiling']:.4f}")
    with open(os.path.join(args.out, f"a4_{args.rung}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    say("done", f"rung={args.rung}", f"wall_s={time.time() - t0:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
