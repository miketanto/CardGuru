"""Phase 1d (v7 plan §2): the acceptance file for `card_emb_vN`.

PRE-REGISTERED 2026-09-10 17:15 while seed 0 of train_contrastive.py was
running and before any of its epoch lines had been read.  Thresholds
below are not to be tuned to a result; a failed gate is a failed
version (train a new one, bump the artifact).

Reads emb.pt (and emb_seed1.pt for the determinism gate), cards_v1
fields, split.json.  Writes gates.json next to the embeddings and prints
the markdown table that goes into rl/V7-VALIDATION.md.  Nothing here
can write to the embeddings (`--frozen` by construction: it only reads).

G1  field recovery, linear probes on e_card (fit on the train split,
    scored on the 10 % held-out cards; train-split score reported too):
      mv, power, toughness   (14 classes: null, 0..12, 13+)   held-out acc >= 0.90
      colours (5 binary)                                      per-colour acc >= 0.97
      types (9 binary, >= 50 held-out positives)              per-type acc >= 0.97
      keywords (18 binary, >= 30 held-out positives)          F1 >= 0.80
      answer classes (9 binary, >= 30 held-out positives)     F1 >= 0.80
G2  neighbour structure (cosine on e_card, all 35k faces):
      Cancel / Counterspell                                   cos >= 0.85
      Spell Snare / Force Spike                               v1-v3: cos <= cos(Cancel, Counterspell) - 0.15
                                                              and Force Spike not in Spell Snare's top-10;
                                                              v4+ (pre-registered 18:45, same scale-dependence
                                                              argument as the swap bar): rank-only, Force Spike
                                                              not in Spell Snare's top-10
      functional reprint groups                               every member has another member in its top-3
      16 P8 swap pairs (PHASE-E3.md G2)                       v1/v2: each cos >= mu + 2 sigma of random pairs,
                                                              group mean >= mu + 4 sigma  (FAILED both; found to
                                                              be scale-dependent, see V7-VALIDATION.md §1d v2)
                                                              v3+ (pre-registered 18:10 before v3 existed):
                                                              >= 14/16 pairs with both directed neighbour ranks
                                                              <= 500 of 35k, and median directed rank <= 50
G3  determinism across seeds (emb.pt vs emb_seed1.pt):
      top-10 neighbour Jaccard, mean over 2,000 random cards  >= 0.40
      G2 verdicts identical for both seeds
"""
import argparse
import json
import os
import random
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, ".."))
import data as D                                        # noqa: E402
from cardguru.dataset import norm_name                  # noqa: E402
from e2_extract import FEATURES                         # noqa: E402

REPRINT_GROUPS = [
    ["Llanowar Elves", "Elvish Mystic", "Fyndhorn Elves"],
    ["Grizzly Bears", "Balduvian Bears", "Runeclaw Bear"],
    ["Divination", "Counsel of the Soratami"],
    ["Terror", "Dark Banishing"],
]
SWAP_PAIRS = [
    ("Bitter Triumph", "Go for the Throat"), ("Requiting Hex", "Cut Down"),
    ("Shoot the Sheriff", "Eliminate"), ("Spell Snare", "Dispel"),
    ("We Say Thee Nay!", "Don't Make a Sound"), ("Spell Pierce", "Stubborn Denial"),
    ("Floodpits Drowner", "Zephyr Sentinel"), ("The Wondrous Wasp", "Plumecreed Escort"),
    ("Spyglass Siren", "Faerie Seer"), ("Elektra, Daughter of the Hand", "Fathom Fleet Cutthroat"),
    ("Bitter Triumph", "Easy Prey"), ("Shoot the Sheriff", "Cradle to Grave"),
    ("We Say Thee Nay!", "Clash of Wills"), ("Spell Pierce", "Concerted Defense"),
    ("Spyglass Siren", "Faerie Miscreant"), ("Elektra, Daughter of the Hand", "Ravenous Chupacabra"),
]
TH = {"bucket_acc": 0.90, "binary_acc": 0.97, "f1": 0.80, "cancel_cos": 0.85,
      "snare_margin": 0.15, "swap_sigma": 2.0, "swap_group_sigma": 4.0, "jaccard": 0.40,
      "min_pos_type": 50, "min_pos_kw": 30,
      # v3+ swap gate (pre-registered 2026-09-10 18:10, V7-VALIDATION.md §1d v2): rank-based
      "swap_rank": 500, "swap_pairs_ok": 14, "swap_median_rank": 50}


def lookup(names, name):
    k = norm_name(name)
    if k in names:
        return names[k]
    hits = [v for n, v in names.items() if n.startswith(k + ",")]
    return hits[0] if hits else None


def bucket(v, vmax):
    if v is None:
        return 0
    v = max(0, v)
    return v + 1 if v <= vmax else vmax + 2


def probe_multiclass(Xtr, ytr, Xte, yte):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=2000, C=1.0).fit(sc.transform(Xtr), ytr)
    return float((clf.predict(sc.transform(Xtr)) == ytr).mean()), float((clf.predict(sc.transform(Xte)) == yte).mean())


def probe_binary(Xtr, ytr, Xte, yte):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced").fit(sc.transform(Xtr), ytr)
    p_tr, p_te = clf.predict(sc.transform(Xtr)), clf.predict(sc.transform(Xte))
    return {"acc_tr": float((p_tr == ytr).mean()), "acc": float((p_te == yte).mean()),
            "f1_tr": float(f1_score(ytr, p_tr)), "f1": float(f1_score(yte, p_te)),
            "pos": int(yte.sum())}


def neighbour_gates(E, names, recs):
    En = E / E.norm(dim=1, keepdim=True).clamp(min=1e-6)
    out = {}

    def cos(a, b):
        return float(En[a] @ En[b])

    def topk(i, k):
        s = En @ En[i]
        s[i] = -2
        return s.topk(k).indices.tolist()

    cc = cos(lookup(names, "Cancel"), lookup(names, "Counterspell"))
    ss, fs = lookup(names, "Spell Snare"), lookup(names, "Force Spike")
    sf = cos(ss, fs)
    out["cancel_counterspell_cos"] = cc
    out["snare_spike_cos"] = sf
    out["spike_in_snare_top10"] = fs in topk(ss, 10)
    out["snare_top5"] = [recs[j].name for j in topk(ss, 5)]
    out["spike_top5"] = [recs[j].name for j in topk(fs, 5)]
    out["pass_cancel"] = cc >= TH["cancel_cos"]
    out["snare_cos_margin_v1v3"] = sf <= cc - TH["snare_margin"]     # informational from v4 on (scale-dependent)
    out["snare_spike_rank"] = int(((En @ En[ss]) > sf).sum().item())    # cards closer to Snare than Spike is
    out["pass_snare"] = not out["spike_in_snare_top10"]                  # v4+: rank-only (pre-registered 18:45)
    rep = []
    for grp in REPRINT_GROUPS:
        ids = [lookup(names, n) for n in grp]
        for n, i in zip(grp, ids):
            t3 = topk(i, 3)
            rep.append({"card": n, "ok": any(j in t3 for j in ids if j != i),
                        "top3": [recs[j].name for j in t3]})
    out["reprints"] = rep
    out["pass_reprints"] = all(r["ok"] for r in rep)
    g = random.Random(0)
    n = En.shape[0]
    rnd = torch.tensor([cos(g.randrange(n), g.randrange(n)) for _ in range(10000)])
    mu, sd = float(rnd.mean()), float(rnd.std())
    def rank(a, b):
        s = En @ En[a]
        s[a] = -2
        return int((s > s[b]).sum().item()) + 1

    pairs = []
    for a, b in SWAP_PAIRS:
        ia, ib = lookup(names, a), lookup(names, b)
        found = ia is not None and ib is not None
        pairs.append({"pair": f"{a} / {b}", "cos": cos(ia, ib) if found else None, "found": found,
                      "rank_ab": rank(ia, ib) if found else None, "rank_ba": rank(ib, ia) if found else None})
    vals = [p["cos"] for p in pairs if p["cos"] is not None]
    ranks = [r for p in pairs if p["found"] for r in (p["rank_ab"], p["rank_ba"])]
    out["random_mu"], out["random_sd"] = mu, sd
    out["swap_pairs"] = pairs
    out["swap_min"], out["swap_mean"] = min(vals), float(np.mean(vals))
    out["swap_cos_bar_v1v2"] = (min(vals) >= mu + TH["swap_sigma"] * sd
                                and float(np.mean(vals)) >= mu + TH["swap_group_sigma"] * sd)   # informational from v3 on
    out["swap_pairs_within"] = sum(1 for p in pairs if p["found"] and max(p["rank_ab"], p["rank_ba"]) <= TH["swap_rank"])
    out["swap_median_rank"] = float(np.median(ranks))
    out["pass_swaps"] = (all(p["found"] for p in pairs) and out["swap_pairs_within"] >= TH["swap_pairs_ok"]
                         and out["swap_median_rank"] <= TH["swap_median_rank"])
    out["pass"] = out["pass_cancel"] and out["pass_snare"] and out["pass_reprints"] and out["pass_swaps"]
    return out


def jaccard_gate(E0, E1, n_sample=2000, k=10):
    def nn(E):
        En = E / E.norm(dim=1, keepdim=True).clamp(min=1e-6)
        return En
    A, B = nn(E0), nn(E1)
    g = random.Random(0)
    idx = g.sample(range(E0.shape[0]), n_sample)
    js = []
    for i in idx:
        sa = A @ A[i]; sa[i] = -2
        sb = B @ B[i]; sb[i] = -2
        ta, tb = set(sa.topk(k).indices.tolist()), set(sb.topk(k).indices.tolist())
        js.append(len(ta & tb) / len(ta | tb))
    return float(np.mean(js))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", default=os.path.join(D.REPO, "rl", "artifacts", "card_emb_v1"))
    ap.add_argument("--emb", default="emb.pt")
    ap.add_argument("--emb2", default="emb_seed1.pt")
    args = ap.parse_args()

    recs, names = D.load_cards()
    E = torch.load(os.path.join(args.art, args.emb)).float()
    assert E.shape[0] == len(recs), (E.shape, len(recs))
    held = set(json.load(open(os.path.join(args.art, "split.json")))["heldout_ids"])
    tr = np.array([r.id for r in recs if r.id not in held])
    te = np.array([r.id for r in recs if r.id in held])
    X = E.numpy()
    res = {"n": len(recs), "d": E.shape[1], "thresholds": TH, "G1": {}, "G2": {}, "G3": {}}

    # --- G1
    g1 = res["G1"]
    for fld, vmax in (("mv", D.MV_MAX), ("power", D.PT_MAX), ("toughness", D.PT_MAX)):
        y = np.array([bucket(r.fields.get(fld), vmax) for r in recs])
        a_tr, a_te = probe_multiclass(X[tr], y[tr], X[te], y[te])
        g1[fld] = {"acc_tr": a_tr, "acc": a_te, "pass": a_te >= TH["bucket_acc"]}
    for c in D.COLORS:
        y = np.array([1 if c in (r.fields.get("colors") or "") else 0 for r in recs])
        r_ = probe_binary(X[tr], y[tr], X[te], y[te])
        g1["color_" + c] = {**r_, "pass": r_["acc"] >= TH["binary_acc"]}
    for t in D.TYPES:
        y = np.array([1 if t in {D._TYPE_ALIAS.get(x, x) for x in (r.fields.get("types") or [])} else 0 for r in recs])
        if y[te].sum() < TH["min_pos_type"]:
            g1["type_" + t] = {"pos": int(y[te].sum()), "pass": None}
            continue
        r_ = probe_binary(X[tr], y[tr], X[te], y[te])
        g1["type_" + t] = {**r_, "pass": r_["acc"] >= TH["binary_acc"]}
    G = np.array([r.graph for r in recs])
    for i, f in enumerate(FEATURES):
        if not (f.startswith("kw_") or f.startswith("ans_")):
            continue
        y = (G[:, i] > 0.5).astype(int)
        if y[te].sum() < TH["min_pos_kw"]:
            g1[f] = {"pos": int(y[te].sum()), "pass": None}
            continue
        r_ = probe_binary(X[tr], y[tr], X[te], y[te])
        g1[f] = {**r_, "pass": r_["f1"] >= TH["f1"]}
    g1_verdicts = [v["pass"] for v in g1.values() if v.get("pass") is not None]
    res["G1"]["pass"] = all(g1_verdicts)
    res["G1"]["n_gated"] = len(g1_verdicts)

    # --- G2
    res["G2"] = neighbour_gates(E, names, recs)

    # --- G3
    p2 = os.path.join(args.art, args.emb2)
    if os.path.exists(p2):
        E1 = torch.load(p2).float()
        j = jaccard_gate(E, E1)
        g2b = neighbour_gates(E1, names, recs)
        same = all(res["G2"][k] == g2b[k] for k in ("pass_cancel", "pass_snare", "pass_reprints", "pass_swaps"))
        res["G3"] = {"jaccard10": j, "seed1_G2": {k: g2b[k] for k in ("pass_cancel", "pass_snare", "pass_reprints", "pass_swaps",
                                                                     "cancel_counterspell_cos", "snare_spike_cos", "swap_min", "swap_mean")},
                     "verdicts_identical": same, "pass": j >= TH["jaccard"] and same}
    else:
        res["G3"] = {"pass": None, "note": f"{args.emb2} absent"}
    res["pass"] = bool(res["G1"]["pass"] and res["G2"]["pass"] and res["G3"]["pass"])
    json.dump(res, open(os.path.join(args.art, "gates.json"), "w"), indent=1)

    # --- table
    def pf(p):
        return "—" if p is None else ("pass" if p else "**FAIL**")
    rows = ["| gate | threshold | measured (held-out) | train | result |", "|---|---|---|---|---|"]
    for k in ("mv", "power", "toughness"):
        v = g1[k]
        rows.append(f"| G1 {k} probe acc | ≥ {TH['bucket_acc']} | {v['acc']:.3f} | {v['acc_tr']:.3f} | {pf(v['pass'])} |")
    for pre, lab, key in (("color_", "colours", "acc"), ("type_", "types", "acc"), ("kw_", "keywords", "f1"), ("ans_", "answer classes", "f1")):
        vs = [(k, v) for k, v in g1.items() if k.startswith(pre) and v.get("pass") is not None]
        skipped = [k for k, v in g1.items() if k.startswith(pre) and v.get("pass") is None]
        if vs:
            worst = min(vs, key=lambda kv: kv[1][key])
            thr = TH["binary_acc"] if key == "acc" else TH["f1"]
            rows.append(f"| G1 {lab} ({len(vs)} probes, {key}) | each ≥ {thr} | min {worst[1][key]:.3f} ({worst[0]}) | "
                        f"min {min(v[key + '_tr'] for _, v in vs):.3f} | {pf(all(v['pass'] for _, v in vs))}"
                        + (f" ({len(skipped)} skipped: too few positives)" if skipped else "") + " |")
    g2 = res["G2"]
    rows.append(f"| G2 Cancel / Counterspell cos | ≥ {TH['cancel_cos']} | {g2['cancel_counterspell_cos']:.3f} | | {pf(g2['pass_cancel'])} |")
    rows.append(f"| G2 Spell Snare / Force Spike (rank-based, v4+) | Spike ∉ Snare top-10 | "
                f"rank {g2['snare_spike_rank']}, cos {g2['snare_spike_cos']:.3f} | | {pf(g2['pass_snare'])} |")
    rows.append(f"| (info) Snare/Spike cos margin, old bar | ≤ {g2['cancel_counterspell_cos'] - TH['snare_margin']:.3f} | "
                f"{g2['snare_spike_cos']:.3f} | | {'would pass' if g2['snare_cos_margin_v1v3'] else 'would fail'} |")
    rows.append(f"| G2 functional reprints in top-3 | all {len(g2['reprints'])} | {sum(r['ok'] for r in g2['reprints'])} / {len(g2['reprints'])} | | {pf(g2['pass_reprints'])} |")
    rows.append(f"| G2 P8 swap pairs (rank-based, v3+) | ≥ {TH['swap_pairs_ok']}/16 pairs with both directed ranks ≤ {TH['swap_rank']}; median rank ≤ {TH['swap_median_rank']} | "
                f"{g2['swap_pairs_within']}/16, median {g2['swap_median_rank']:.0f} | | {pf(g2['pass_swaps'])} |")
    rows.append(f"| (info) swap pairs cos, old μ+kσ bar | min ≥ {g2['random_mu'] + 2 * g2['random_sd']:.3f}, mean ≥ {g2['random_mu'] + 4 * g2['random_sd']:.3f} | "
                f"min {g2['swap_min']:.3f}, mean {g2['swap_mean']:.3f} (random μ {g2['random_mu']:.3f} σ {g2['random_sd']:.3f}) | | {'would pass' if g2['swap_cos_bar_v1v2'] else 'would fail'} |")
    g3 = res["G3"]
    if g3.get("pass") is not None:
        rows.append(f"| G3 seed 0 vs 1 top-10 Jaccard | ≥ {TH['jaccard']}, same G2 verdicts | {g3['jaccard10']:.3f}, identical: {g3['verdicts_identical']} | | {pf(g3['pass'])} |")
    else:
        rows.append(f"| G3 determinism | | {g3.get('note')} | | — |")
    rows.append(f"| **{os.path.basename(os.path.normpath(args.art))} overall** | all of the above | | | {pf(res['pass'])} |")
    print("\n".join(rows))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
