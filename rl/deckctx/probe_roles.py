"""Phase 2c (v7 plan §2): role probe on c'_i.

PRE-REGISTERED 2026-09-10 17:25, before any deck-context model had been
trained.  A linear head must read, off c'_i (DeckContext output, frozen),
the fingerprint's own per-card role labels on HELD-OUT decks:

    wincon   nodes[name]["wincon"]                     balanced acc >= 0.85
    answer   nodes[name]["interaction"] non-empty      balanced acc >= 0.80
    enabler  card is the enabler side of >= 1 edge     balanced acc >= 0.70

The same probe on raw e_card is reported as the reference (what the
context adds is the difference, not a gate).  Probes are fit on train-
split decks, scored on held-out decks; one card can appear in many decks
and labels are per (deck, card).  Nothing here writes to the model.

Run: python3 rl/deckctx/probe_roles.py [--model rl/artifacts/deck_ctx_v1/model_seed0.pt | --identity]
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
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)
import data as X                                   # noqa: E402
from model import DeckContext                      # noqa: E402
from cardguru.dataset import norm_name             # noqa: E402
from cardguru.fingerprint import build_fingerprint  # noqa: E402

TH = {"wincon": 0.85, "answer": 0.80, "enabler": 0.70}


def labels_for(decklist, by_name):
    recs = {n: (by_name.get(n) or by_name.get(norm_name(n))) for n, _ in decklist}
    fp = build_fingerprint({n: r for n, r in recs.items() if r}, [(n, int(c)) for n, c in decklist])
    enablers = {e["enabler"] for e in fp.get("edges", [])}
    out = {}
    for n, _ in decklist:
        node = fp["nodes"].get(n)
        if node is None:                       # basic lands / unknown: no label
            continue
        out[n] = {"wincon": int(bool(node.get("wincon"))),
                  "answer": int(bool(node.get("interaction"))),
                  "enabler": int(n in enablers)}
    return out


def bal_acc(y, p):
    y, p = np.asarray(y), np.asarray(p)
    tpr = (p[y == 1] == 1).mean() if (y == 1).any() else 0.0
    tnr = (p[y == 0] == 0).mean() if (y == 0).any() else 0.0
    return float(0.5 * (tpr + tnr))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", default=os.path.join(REPO, "rl", "artifacts", "deck_ctx_v1"))
    ap.add_argument("--model", default="model_seed0.pt")
    ap.add_argument("--identity", action="store_true", help="probe the identity-initialised module (2b no-corpus fallback)")
    ap.add_argument("--emb", default="emb.pt")
    ap.add_argument("--max-decks", type=int, default=3000)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    names = X.load_names()
    emb = torch.load(args.emb).float() if os.path.isabs(args.emb) else X.load_emb(fname=args.emb)
    by_name = X.load_by_name()
    corpus = X.Corpus()
    model = DeckContext(d_c=emb.shape[1]).to(args.device).eval()
    if args.identity:
        model.identity_init()
        tag = "identity"
    else:
        ck = torch.load(os.path.join(args.art, args.model), map_location=args.device)
        model.load_state_dict(ck["model"])
        tag = args.model

    g = random.Random(0)
    rows = {"train": [], "heldout": []}
    idx = list(range(len(corpus)))
    g.shuffle(idx)
    for i in idx:
        r = corpus.rows[i]
        if len(rows[r["split"]]) >= (args.max_decks if r["split"] == "train" else args.max_decks // 4):
            continue
        dl = corpus.decklist(i)
        lab = labels_for(dl, by_name)
        E, counts, bias, mask, kept = X.deck_tensors(dl, names, emb, by_name, ids=corpus.ids(i))
        kept_names = [n for (n, _), cid in zip(dl, corpus.ids(i)) if cid >= 0]
        with torch.no_grad():
            c, _ = model(E.unsqueeze(0).to(args.device), counts.unsqueeze(0).to(args.device),
                         bias.unsqueeze(0).to(args.device), mask.unsqueeze(0).to(args.device))
        c = c[0].cpu()
        for k, n in enumerate(kept_names):
            if n in lab:
                rows[r["split"]].append((c[k].numpy(), E[k].numpy(), lab[n]))

    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    res = {"model": tag, "n_train": len(rows["train"]), "n_heldout": len(rows["heldout"]), "thresholds": TH}
    Xc_tr = np.stack([r[0] for r in rows["train"]]); Xc_te = np.stack([r[0] for r in rows["heldout"]])
    Xe_tr = np.stack([r[1] for r in rows["train"]]); Xe_te = np.stack([r[1] for r in rows["heldout"]])
    table = ["| label | held-out pos/neg | c'ᵢ probe bal-acc | e_card probe bal-acc | threshold | result |", "|---|---|---|---|---|---|"]
    all_pass = True
    for lab in ("wincon", "answer", "enabler"):
        y_tr = np.array([r[2][lab] for r in rows["train"]]); y_te = np.array([r[2][lab] for r in rows["heldout"]])
        out = {}
        for key, (A, B) in (("ctx", (Xc_tr, Xc_te)), ("ecard", (Xe_tr, Xe_te))):
            sc = StandardScaler().fit(A)
            clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(sc.transform(A), y_tr)
            out[key] = bal_acc(y_te, clf.predict(sc.transform(B)))
        ok = out["ctx"] >= TH[lab]
        all_pass &= ok
        res[lab] = {**out, "pos": int(y_te.sum()), "neg": int((y_te == 0).sum()), "pass": ok}
        table.append(f"| {lab} | {int(y_te.sum())}/{int((y_te == 0).sum())} | {out['ctx']:.3f} | {out['ecard']:.3f} | ≥ {TH[lab]} | {'pass' if ok else '**FAIL**'} |")
    res["pass"] = bool(all_pass)
    json.dump(res, open(os.path.join(args.art, f"probe_roles_{tag.replace('.pt', '')}.json"), "w"), indent=1)
    print("\n".join(table))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
