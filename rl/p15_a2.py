#!/usr/bin/env python3
"""Phase 15 A2 probe 1 / probe 3 (rl/PHASE15-ARCH.md): does the policy network keep
card identity?

Freeze the encoder; take the ENTITY TOKEN of every card in the recorded seat's hand
(zone one-hot = hand, mine = 1, not face-down, card id resolved) and linear-probe the
card's mechanical facts from it: the 68 `rl/e2_features.tsv` columns, the five colour
bits, and mana value / power / toughness.  Fit on training games, score on held-out
games (the 13b split when the recordings are the 13a set).

    python3 rl/p15_a2.py --ckpt BC=.../bc.pt --ckpt RAND=.../bc_random.pt \
        --out DIR REC.jsonl [...]

Controls, both on exactly the same entity instances and the same split:
  EMB   the frozen card_emb_v8 row itself (128-d, pre-adapter) - the CEILING: what a
        linear probe recovers from the embedding the encoder was handed.
  RAND  a clone trained with card_emb="random" (V7Policy(random_table=True)) - the
        card-blind FLOOR.  Note what that table is: 1,000 random rows and ids are
        clamped, so every card id >= 1000 lands on the same zero row; the fraction of
        probed entities that keep a distinct row is reported as `rand_distinct_frac`.

SCORE (fixed here, before any A2 data): the probe score is the MACRO ACCURACY over
informative binary columns - the 68 e2 columns plus 5 colour bits, keeping only the
columns that carry both classes in the training AND the held-out entity sets, so a
column that is constant cannot inflate the mean.  The column set depends only on the
targets, never on the model, so BC / EMB / RAND are scored on the same columns.  R^2
for mana value, power and toughness is reported beside it and is NOT the gate.

Probe 3 populations, reported separately with the same fitted probe:
  all        every probed entity
  unseen_id  entities whose card id is in card_emb_v8/split.json (the 10 % held out
             before the embedding was trained)
  off_deck   entities whose card never appears in the --baseline-deck recordings
             (pass --baseline-names to name that population, e.g. BenchDimir's cards)

One JSON (a2_probe1.json) plus A2| lines.  Resumable at the level of the caller.
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

COLOURS = ["W", "U", "B", "R", "G"]
NUM = ["mv", "power", "toughness"]


def say(*a):
    print("A2|" + "|".join(str(x) for x in a), flush=True)


def norm(name):
    import unicodedata
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower().strip()


def load_targets():
    """normalised card name -> (68 e2 bits, 5 colour bits, [mv, power, toughness], has_num mask)"""
    e2 = {}
    with open(os.path.join(HERE, "e2_features.tsv"), encoding="utf-8") as fh:
        dim = int(fh.readline().strip())
        for line in fh:
            if "\t" not in line:
                continue
            nm, vec = line.rstrip("\n").split("\t", 1)
            v = np.fromstring(vec, sep=",", dtype=np.float32)
            if v.shape[0] == dim:
                e2[norm(nm)] = v
    import gzip
    fields = {}
    with gzip.open(os.path.join(HERE, "artifacts", "cards_v1", "fields.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            o = json.loads(line)
            if o.get("kind") != "card":
                continue
            k = norm(o["name"])
            if k in fields:
                continue
            col = np.array([1.0 if c in (o.get("colors") or "") else 0.0 for c in COLOURS], dtype=np.float32)
            def num(x):
                try:
                    return float(x)
                except (TypeError, ValueError):
                    return np.nan
            fields[k] = (col, np.array([num(o.get("mv")), num(o.get("power")), num(o.get("toughness"))],
                                       dtype=np.float32))
    return e2, dim, fields


def collect(net, rows, args, ids_split, base_names):
    """-> dict of arrays: X (token), E (frozen emb row), Y bits, Ynum, game, unseen_id, off_deck"""
    e2, dim, fields = load_targets()
    dev = args.device
    X, E, YB, YN, G, UN, OFF, NAMES = [], [], [], [], [], [], [], []
    net.eval()
    with torch.no_grad():
        for s in range(0, len(rows), args.batch):
            chunk = rows[s:s + args.batch]
            b = {k: (v.to(dev) if torch.is_tensor(v) else v)
                 for k, v in V.collate([r[1] for r in chunk]).items()}
            toks = net.build(b)
            bel = net.belief(toks)
            toks = net.belief.attach(toks, bel)
            enc = net.enc(toks, ent_raw=b["ent"])
            ent = enc["ent"].float().cpu().numpy()                     # [B, N, d]
            raw = b["ent"].float().cpu().numpy()
            eid = b["ent_id"].cpu().numpy()
            for i, r in enumerate(chunk):
                names = r[1].ent_name
                for j in range(min(len(names), raw.shape[1])):
                    if raw[i, j, 1] < 0.5 or raw[i, j, 7] < 0.5 or raw[i, j, 8] > 0.5:
                        continue                                        # hand, mine, face-up only
                    cid = int(eid[i, j])
                    k = norm(names[j])
                    if cid < 0 or k not in e2 or k not in fields:
                        continue
                    col, num = fields[k]
                    X.append(ent[i, j])
                    E.append(net.table.table[cid].float().cpu().numpy())
                    YB.append(np.concatenate([e2[k], col]))
                    YN.append(num)
                    G.append(r[0])
                    UN.append(1.0 if cid in ids_split else 0.0)
                    OFF.append(0.0 if k in base_names else 1.0)
                    NAMES.append(k)
                    if args.max_entities and len(X) >= args.max_entities:
                        break
            if args.max_entities and len(X) >= args.max_entities:
                break
    return (np.array(X, dtype=np.float64), np.array(E, dtype=np.float64), np.array(YB, dtype=np.float64),
            np.array(YN, dtype=np.float64), G, np.array(UN), np.array(OFF), NAMES, dim)


def ridge(Xtr, Ytr, lam=1.0):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd = np.where(sd < 1e-8, 1.0, sd)
    Z = np.concatenate([(Xtr - mu) / sd, np.ones((len(Xtr), 1))], 1)
    A = Z.T @ Z + lam * np.eye(Z.shape[1])
    W = np.linalg.solve(A, Z.T @ Ytr)
    return (mu, sd, W)


def apply_ridge(model, X):
    mu, sd, W = model
    Z = np.concatenate([(X - mu) / sd, np.ones((len(X), 1))], 1)
    return Z @ W


def score(model, X, YB, YN, cols, num_ok):
    """macro accuracy on `cols`, R^2 per numeric target"""
    out = {}
    if len(X) < 5:
        return {"n": len(X), "macro_acc": float("nan"), "r2": {k: float("nan") for k in NUM}}
    pb = apply_ridge(model[0], X)
    acc = [(float(((pb[:, c] > 0.5) == (YB[:, c] > 0.5)).mean())) for c in cols]
    pn = apply_ridge(model[1], X)
    r2 = {}
    for t, name in enumerate(NUM):
        m = num_ok[:, t]
        if m.sum() < 5:
            r2[name] = float("nan")
            continue
        y = YN[m, t]
        v = y.var()
        r2[name] = float(1 - ((pn[m, t] - y) ** 2).mean() / v) if v > 1e-9 else float("nan")
    out = {"n": int(len(X)), "macro_acc": float(np.mean(acc)), "n_cols": len(cols), "r2": r2}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", required=True, help="name=path (BC, RAND, ...)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-entities", type=int, default=60000)
    ap.add_argument("--max-consults", type=int, default=0, help="0 = all")
    ap.add_argument("--baseline-names", default="", help="deck file whose card names define the 'seen' population")
    ap.add_argument("--tag", default="probe1")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    ids = V.CardIds()

    split = json.load(open(os.path.join(HERE, "artifacts", "card_emb_v8", "split.json")))
    heldout_ids = set(int(x) for x in split["heldout_ids"])
    base_names = set()
    if args.baseline_names:
        for line in open(args.baseline_names, encoding="utf-8"):
            if line.startswith("NAME:") or not line.strip():
                continue
            parts = line.strip().split("]", 1)
            if len(parts) == 2:
                base_names.add(norm(parts[1]))
    say("setup", f"heldout_card_ids={len(heldout_ids)}", f"baseline_names={len(base_names)}")

    hello, rows, drop = BC.load(args.recordings, ids, args.max_consults, set(BC.KINDS))
    held_games, _ = None, None
    games = sorted(set(r[0] for r in rows))
    random.Random(0).shuffle(games)
    n_held = max(1, int(round(len(games) * 0.1)))
    held_games = set(games[:n_held])
    say("data", f"consults={len(rows)}", f"games={len(games)}", f"held_games={n_held}",
        f"load_s={time.time() - t0:.0f}")

    out = {"tag": args.tag, "recordings": [os.path.basename(p) for p in args.recordings],
           "games": len(games), "held_games": n_held, "models": {}}
    shared = {}
    for spec in args.ckpt:
        name, path = spec.split("=", 1)
        net = P.V7Policy.load(path, device=args.device)
        X, E, YB, YN, G, UN, OFF, NAMES, dim = collect(net, rows, args, heldout_ids, base_names)
        del net
        torch.cuda.empty_cache()
        if not len(X):
            say(name, "no entities"); continue
        tr = np.array([g not in held_games for g in G])
        te = ~tr
        num_ok = np.isfinite(YN)
        if "cols" not in shared:
            cols = [c for c in range(YB.shape[1])
                    if 0 < YB[tr, c].sum() < tr.sum() and 0 < YB[te, c].sum() < te.sum()]
            shared["cols"] = cols
            shared["counts"] = {"entities": int(len(X)), "train": int(tr.sum()), "held": int(te.sum()),
                                "unseen_id": int(UN[te].sum()), "off_deck": int(OFF[te].sum()),
                                "distinct_names": len(set(NAMES)), "e2_dim": dim}
            say("entities", json.dumps(shared["counts"]), f"informative_cols={len(cols)}")
        cols = shared["cols"]
        res = {}
        for key, Xs in (("TOKEN", X), ("EMB", E)):
            mb = ridge(Xs[tr], YB[tr])
            yn = np.nan_to_num(YN[tr], nan=0.0)
            mn = ridge(Xs[tr], yn)
            for pop, mask in (("all", te), ("unseen_id", te & (UN > 0.5)), ("off_deck", te & (OFF > 0.5))):
                s = score((mb, mn), Xs[mask], YB[mask], YN[mask], cols, num_ok[mask])
                res[f"{key}_{pop}"] = s
                say(name, key, pop, f"n={s['n']}", f"macro_acc={s['macro_acc']:.4f}",
                    "r2=" + ",".join(f"{k}:{v:.3f}" for k, v in s["r2"].items()))
            if key == "EMB" and "EMB" in out["models"]:
                break
        out["models"][name] = res
        if "EMB" not in out["models"]:
            out["models"]["EMB"] = {k[4:]: v for k, v in res.items() if k.startswith("EMB_")}
    out["counts"] = shared.get("counts", {})
    out["informative_cols"] = len(shared.get("cols", []))
    with open(os.path.join(args.out, f"a2_{args.tag}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    say("done", f"wall_s={time.time() - t0:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
