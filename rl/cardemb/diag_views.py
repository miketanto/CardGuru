"""Per-view diagnostic for a trained card embedder: which view carries which
gate?  For a given artifact (model.pt), computes for every face:

  ht      text view (fine-tuned, before the contrastive head)
  hs      structure view (bag + printed [+ tree]) before the contrastive head
  tree    the tree encoder's output alone (if the model has one)
  e       e_card (the fused vector, what gates.py scores)

and reports, for each view: the mv / colour probe accuracy (G1-style,
held-out), Spell Snare -> Force Spike rank, and the 16 swap pairs'
directed ranks (how many within 500, median).  Reads only; writes
diag_views.json next to the model.  Diagnostic, not a gate.
"""
import argparse
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data as D                                        # noqa: E402
import tree as T                                        # noqa: E402
from model import CardEmbedder                          # noqa: E402
from gates import SWAP_PAIRS, lookup, bucket, probe_multiclass, probe_binary   # noqa: E402


def ranks(En, a, b):
    s = En @ En[a]
    s[a] = -2
    return int((s > s[b]).sum().item()) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--model", default="model.pt")
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    recs, names = D.load_cards()
    ck = torch.load(os.path.join(args.art, args.model), map_location="cpu")
    cfg = ck["config"]
    model = CardEmbedder(**{k: v for k, v in cfg.items() if k in ("text_model", "graph_dim", "printed_dim", "d_t", "d_g", "d_p", "d_c", "d_z", "tau", "tree", "d_tree", "fuse", "piece_dropout")})
    model.load_state_dict(ck["state_dict"])
    model.to(args.device).eval()
    trees = T.build_trees(tokenscripts_dir=os.environ.get("CARDGURU_TOKENSCRIPTS")) if cfg.get("tree") else None

    views = {"text": [], "struct": [], "e": []}
    if trees is not None:
        views["tree"] = []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=(args.device == "cuda")):
        for i in range(0, len(recs), args.batch):
            b = recs[i:i + args.batch]
            texts, printed, graph = D.to_tensors(b)
            tb = None
            if trees is not None:
                tb = {k: v.to(args.device) for k, v in T.collate_trees([trees[r.id] for r in b]).items()}
            ht = model.encode_text(texts)
            hs = model.encode_struct(graph.to(args.device), printed.to(args.device), tb)
            e = model.fuse_blocks(ht, hs)[0] if getattr(model, "fuse_mode", "linear") == "blocks" else model.norm(model.fuse(torch.cat([ht, hs], -1)))
            views["text"].append(ht.float().cpu()); views["struct"].append(hs.float().cpu()); views["e"].append(e.float().cpu())
            if trees is not None:
                views["tree"].append(model.tree_enc(tb).float().cpu())
    views = {k: torch.cat(v) for k, v in views.items()}

    held = set(json.load(open(os.path.join(args.art, "split.json")))["heldout_ids"])
    tr = np.array([r.id for r in recs if r.id not in held]); te = np.array([r.id for r in recs if r.id in held])
    y_mv = np.array([bucket(r.fields.get("mv"), D.MV_MAX) for r in recs])
    y_R = np.array([1 if "R" in (r.fields.get("colors") or "") else 0 for r in recs])
    ss, fs = lookup(names, "Spell Snare"), lookup(names, "Force Spike")
    out = {}
    rows = ["| view | dim | mv probe acc | colour R probe acc | Snare→Spike rank | swap pairs within 500 | swap median rank |", "|---|---|---|---|---|---|---|"]
    for name, V in views.items():
        X = V.numpy()
        _, mv_acc = probe_multiclass(X[tr], y_mv[tr], X[te], y_mv[te])
        r_acc = probe_binary(X[tr], y_R[tr], X[te], y_R[te])["acc"]
        En = V / V.norm(dim=1, keepdim=True).clamp(min=1e-6)
        rk = ranks(En, ss, fs)
        prs = []
        for a, b_ in SWAP_PAIRS:
            ia, ib = lookup(names, a), lookup(names, b_)
            prs.append((ranks(En, ia, ib), ranks(En, ib, ia)))
        within = sum(1 for p in prs if max(p) <= 500)
        med = float(np.median([r for p in prs for r in p]))
        out[name] = {"dim": V.shape[1], "mv_acc": mv_acc, "colorR_acc": r_acc, "snare_spike_rank": rk,
                     "swap_within500": within, "swap_median_rank": med, "swap_ranks": prs}
        rows.append(f"| {name} | {V.shape[1]} | {mv_acc:.3f} | {r_acc:.3f} | {rk} | {within}/16 | {med:.0f} |")
    json.dump(out, open(os.path.join(args.art, "diag_views.json"), "w"), indent=1)
    print("\n".join(rows))
    for name in out:
        worst = sorted(zip(SWAP_PAIRS, out[name]["swap_ranks"]), key=lambda x: -max(x[1]))[:3]
        print(f"{name}: worst pairs " + "; ".join(f"{a} / {b}: {r}" for (a, b), r in worst))


if __name__ == "__main__":
    main()
