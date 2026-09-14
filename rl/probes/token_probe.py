#!/usr/bin/env python3
"""Phase 9 / P4 - linear probes on the entity tokens (rl/PHASE9-PROBES.md).

For every battlefield creature row of the recorded consults, three feature
views: `raw` = the 64-float wire row (WIRE-V7 §2d, the control: what the input
exposes), `build` = the builder token (card embedding + row through the zone
MLP, before the encoder), `enc` = the encoder output token for that entity,
per subject.  Labels from the cards_v1 corpus (kw_* graph features, printed
P/T): has-flying, has-lifelink, has-first-strike, any-keyword, power bucket,
toughness bucket.  L2 logistic probe (class-balanced), 5-fold GroupKFold over
CONSULTS, balanced accuracy on the out-of-fold predictions with a bootstrap
95 % CI over consults.

Usage (WSL):
  python3 rl/probes/token_probe.py --ckpt init=... --ckpt C1s0=... --out rl/artifacts/v7/9 REC.jsonl ...
"""
import argparse
import collections
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RL = os.path.dirname(HERE)
sys.path.insert(0, RL)
sys.path.insert(0, HERE)
import torch                      # noqa: E402
import v7_obs as V                # noqa: E402
import v7_policy as P             # noqa: E402
import cardswap as C              # noqa: E402  (corpus loader, consult loader, KEYWORDS)
from sklearn.linear_model import LogisticRegression          # noqa: E402
from sklearn.model_selection import GroupKFold               # noqa: E402
from sklearn.preprocessing import StandardScaler             # noqa: E402
from sklearn.metrics import balanced_accuracy_score          # noqa: E402

GRAPH = json.load(open(os.path.join(C.CARDS, "index.json")))["graph_features"]
KW_COLS = {k: GRAPH.index("kw_" + k.replace(" ", "_")) for k in C.KW_LOWER if "kw_" + k.replace(" ", "_") in GRAPH}


def labels_for(name, F):
    f = F.get(name)
    if f is None:
        return None
    g = f.get("graph") or []
    if len(g) != len(GRAPH):
        return None
    kw = {k: int(g[i] > 0.5) for k, i in KW_COLS.items()}
    pw, tg = C._int(f.get("power")), C._int(f.get("toughness"))
    if pw is None or tg is None:
        return None
    bucket = lambda x: 0 if x <= 1 else (1 if x == 2 else (2 if x == 3 else 3))   # noqa: E731
    return {"flying": kw.get("flying", 0), "lifelink": kw.get("lifelink", 0), "first_strike": kw.get("first strike", 0),
            "any_keyword": int(any(kw.values())), "power_bucket": bucket(pw), "toughness_bucket": bucket(tg)}


def boot_bacc(y, yhat, groups, reps=2000, seed=0):
    y, yhat, groups = np.asarray(y), np.asarray(yhat), np.asarray(groups)
    uniq = np.unique(groups)
    idx_by = {g: np.nonzero(groups == g)[0] for g in uniq}
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(reps):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        sel = np.concatenate([idx_by[g] for g in pick])
        if len(np.unique(y[sel])) < 2:
            continue
        vals.append(balanced_accuracy_score(y[sel], yhat[sel]))
    lo, hi = np.percentile(vals, [2.5, 97.5]) if vals else (float("nan"), float("nan"))
    return float(balanced_accuracy_score(y, yhat)), float(lo), float(hi)


def probe(X, y, groups, seed=0):
    """Out-of-fold predictions of an L2 logistic probe, 5-fold GroupKFold over consults."""
    X = np.asarray(X, dtype=np.float64); y = np.asarray(y); groups = np.asarray(groups)
    yhat = np.zeros_like(y)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        if len(np.unique(y[tr])) < 2:
            yhat[te] = y[tr][0]; continue
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000)
        clf.fit(sc.transform(X[tr]), y[tr])
        yhat[te] = clf.predict(sc.transform(X[te]))
    return yhat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", required=True, help="name=path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--max-rows", type=int, default=20000, help="subsample battlefield rows (deterministic) to bound probe time")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    paths = [q for p in args.recordings for q in sorted(glob.glob(p))] or args.recordings
    F, O = C.load_corpus()
    ids = V.CardIds()
    hello, msgs = C.load_consults(paths)
    obs = [V.parse_consult(m, ids, hello) for m in msgs]
    # rows: (consult idx, entity idx, labels)
    rows = []
    skipped = collections.Counter()
    for ci, o in enumerate(obs):
        for i in range(o.ent.shape[0]):
            r = o.ent[i]
            if r[0] < 0.5 or r[29] < 0.5:
                continue
            lab = labels_for(o.ent_name[i], F)
            if lab is None:
                skipped[o.ent_name[i]] += 1; continue
            rows.append((ci, i, lab))
    rng = np.random.default_rng(0)
    if len(rows) > args.max_rows:
        keep = sorted(rng.choice(len(rows), size=args.max_rows, replace=False).tolist())
        rows = [rows[j] for j in keep]
    groups = [ci for ci, i, lab in rows]
    names = collections.Counter(obs[ci].ent_name[i] for ci, i, lab in rows)
    print("P4|rows=%d|consults=%d|distinct_cards=%d|skipped=%s" % (len(rows), len(set(groups)), len(names),
                                                                 ",".join("%s:%d" % kv for kv in skipped.most_common(5))))
    print("P4|cards|" + "|".join("%s=%d" % kv for kv in names.most_common(40)))
    LABELS = ["flying", "lifelink", "first_strike", "any_keyword", "power_bucket", "toughness_bucket"]
    Y = {lab: np.array([r[2][lab] for r in rows]) for lab in LABELS}
    for lab in LABELS:
        cnt = collections.Counter(Y[lab].tolist())
        print("P4|label|%s|%s" % (lab, dict(sorted(cnt.items()))))
    # feature views
    views = {}
    views["raw"] = np.stack([obs[ci].ent[i].numpy() for ci, i, lab in rows])
    by_consult = collections.defaultdict(list)
    for j, (ci, i, lab) in enumerate(rows):
        by_consult[ci].append((j, i))
    consult_ids = sorted(by_consult)

    def extract(net, which):
        out = np.zeros((len(rows), 256), dtype=np.float32)
        for s in range(0, len(consult_ids), 32):
            cis = consult_ids[s:s + 32]
            b = V.collate([obs[ci] for ci in cis])
            b = {k: (v.to(args.device) if torch.is_tensor(v) else v) for k, v in b.items()}
            with torch.no_grad():
                toks = net.build(b)
                if which == "build":
                    ent = toks["ent"]
                else:
                    toks = net.belief.attach(toks, net.belief(toks))
                    ent = net.enc(toks, ent_raw=b["ent"])["ent"]
            ent = ent.float().cpu().numpy()
            for bi, ci in enumerate(cis):
                for j, i in by_consult[ci]:
                    out[j] = ent[bi, i]
        return out

    lines = []
    subjects = []
    for spec in args.ckpt:
        name, path = spec.split("=", 1)
        net = P.V7Policy.load(path, device=args.device).eval()
        if name == args.ckpt[0].split("=", 1)[0]:
            views["build:" + name] = extract(net, "build")
        views["enc:" + name] = extract(net, "enc")
        subjects.append(name)
        del net
    results = {}
    for view, X in views.items():
        for lab in LABELS:
            y = Y[lab]
            if len(np.unique(y)) < 2:
                lines.append("P4|%s|%s|not testable (one class: %s)" % (view, lab, dict(collections.Counter(y.tolist()))))
                print(lines[-1]); continue
            yhat = probe(X, y, groups)
            m, lo, hi = boot_bacc(y, yhat, groups)
            results[(view, lab)] = (m, lo, hi)
            lines.append("P4|%s|%s|bacc=%.3f [%.3f,%.3f]|n=%d|classes=%d" % (view, lab, m, lo, hi, len(y), len(np.unique(y))))
            print(lines[-1])
    # readings vs init (enc view)
    if "init" in subjects:
        for name in subjects:
            if name == "init":
                continue
            for lab in LABELS:
                a = results.get(("enc:" + name, lab)); b0 = results.get(("enc:init", lab))
                if a is None or b0 is None:
                    continue
                rd = "sharpens" if a[1] > b0[2] else ("erases" if a[2] < b0[1] else "preserves")
                lines.append("P4|reading|%s|%s|%s|trained=%.3f [%.3f,%.3f]|init=%.3f [%.3f,%.3f]" % (name, lab, rd, *a, *b0))
                print(lines[-1])
    with open(os.path.join(args.out, "token_probe_summary.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
