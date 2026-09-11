"""Phase 1b (v7 plan §2): text<->structure contrastive pretraining of the
card embedder, then export of `rl/artifacts/card_emb_v1/`.

  emb.pt      FloatTensor [N, d_c]  e_card for every face id of cards_v1
  model.pt    state_dict + config + training args + data fingerprint
  index.json  {version, cards_version, n, d_c, split, args, final metrics}
  train.log   one line per epoch: loss, retrieval@1/@10 on train and held-out
  README.md   the contract for consumers (written by export)

Held-out cards (split.json, 10 %) never enter the contrastive batches;
their retrieval numbers are the generalisation readout that 1d's probes
extend.  Two seeds are expected to be run (1d: determinism gate).

Run (WSL, GPU) — v2 defaults (--positives same --distill 1.0); v1 was --positives struct --distill 0:
    python3 rl/cardemb/train_contrastive.py --epochs 8 --batch 256 --seed 0
      [--out rl/artifacts/card_emb_v1] [--limit N for smoke tests]
"""
import argparse
import json
import math
import os
import random
import sys
import time

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

import data as D                                   # noqa: E402
from model import CardEmbedder, supcon_loss, masked_infonce, relational_distill, retrieval_at_k   # noqa: E402
import tree as T                                   # noqa: E402


def struct_keys(records, trees=None):
    """One integer per distinct structure: (graph, printed) vector, plus the
    canonical ability-tree key when the tree channel is on (v5)."""
    seen = {}
    keys = []
    for i, r in enumerate(records):
        k = (tuple(r.graph), tuple(r.printed), trees[i]["key"] if trees is not None else None)
        keys.append(seen.setdefault(k, len(seen)))
    return torch.tensor(keys), len(seen)


def tree_batch(trees, recs, device):
    if trees is None:
        return None
    t = T.collate_trees([trees[r.id] for r in recs])
    return {k: v.to(device) for k, v in t.items()}


@torch.no_grad()
def evaluate(model, records, keys, batch, device, n_max=4096, seed=0, trees=None):
    model.eval()
    g = random.Random(seed)
    idx = list(range(len(records)))
    if len(idx) > n_max:
        idx = g.sample(idx, n_max)
    zts, zss = [], []
    for i in range(0, len(idx), batch):
        b = [records[j] for j in idx[i:i + batch]]
        texts, printed, graph = D.to_tensors(b)
        _, zt, zs, _ = model(texts, graph.to(device), printed.to(device), tree_batch(trees, b, device))
        zts.append(zt)
        zss.append(zs)
    zt, zs = torch.cat(zts), torch.cat(zss)
    k = keys[idx].to(device)
    return {"r@1": retrieval_at_k(zt, zs, k, 1), "r@10": retrieval_at_k(zt, zs, k, 10),
            "loss": supcon_loss(zt, zs, k, model.tau).item(), "n": len(idx)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "rl", "artifacts", "card_emb_v2"))
    ap.add_argument("--positives", choices=["same", "struct"], default="same",
                    help="v2: same card only, identical-structure cards masked from the denominator; struct = v1 supcon")
    ap.add_argument("--distill", type=float, default=1.0,
                    help="weight of the relational distillation to the frozen pretrained text geometry (0 = off, v1)")
    ap.add_argument("--cards", default=D.CARDS_V1)
    ap.add_argument("--text-model", default="sentence-transformers/all-MiniLM-L6-v2")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--lr-text", type=float, default=3e-5)
    ap.add_argument("--lr-head", type=float, default=1e-3)
    ap.add_argument("--tau", type=float, default=0.05)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0, help="smoke: train on the first N cards")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--tree", action="store_true",
                    help="v5: add the ability-tree encoder (rl/cardemb/tree.py) to the structure view")
    ap.add_argument("--fuse", choices=["linear", "blocks"], default="linear",
                    help="v6: 'blocks' = e_card as [text 48 | tree 32 | bag 16 | printed 32], each slice LayerNormed")
    ap.add_argument("--aux", type=float, default=0.0,
                    help="v6: weight of the reconstruction losses (tree slice -> 68 readout, printed slice -> 83 printed)")
    ap.add_argument("--piece-dropout", type=float, default=0.0, help="v6: dropout on tree param pieces")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    log = open(os.path.join(args.out, f"train_seed{args.seed}.log"), "a", encoding="utf-8")

    def say(msg):
        line = time.strftime("%H:%M:%S ") + msg
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    records, names = D.load_cards(args.cards)
    split_path = os.path.join(args.out, "split.json")
    if os.path.exists(split_path):
        held = set(json.load(open(split_path))["heldout_ids"])
    else:
        held = set(D.write_split(records, split_path)["heldout_ids"])
    train = [r for r in records if r.id not in held]
    heldout = [r for r in records if r.id in held]
    if args.limit:
        train = train[:args.limit]
        heldout = heldout[:max(64, args.limit // 10)]
    trees = T.build_trees(args.cards, tokenscripts_dir=os.environ.get("CARDGURU_TOKENSCRIPTS")) if args.tree else None
    keys_all, n_keys = struct_keys(records, trees)
    say(f"cards={len(records)} train={len(train)} heldout={len(heldout)} distinct_struct={n_keys} "
        f"tree={args.tree} device={args.device} seed={args.seed} text_model={args.text_model}")

    model = CardEmbedder(text_model=args.text_model, graph_dim=len(records[0].graph),
                        printed_dim=D.PRINTED_DIM, tau=args.tau, tree=args.tree,
                        fuse=args.fuse, piece_dropout=args.piece_dropout).to(args.device)
    text_params = list(model.text.parameters())
    text_ids = {id(p) for p in text_params}
    head_params = [p for p in model.parameters() if id(p) not in text_ids]
    opt = torch.optim.AdamW([{"params": text_params, "lr": args.lr_text},
                             {"params": head_params, "lr": args.lr_head}], weight_decay=0.01)
    steps_per_epoch = math.ceil(len(train) / args.batch)
    total = steps_per_epoch * args.epochs
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / max(1, int(0.05 * total)))
        * 0.5 * (1 + math.cos(math.pi * min(1.0, s / max(1, total)))))
    scaler = torch.amp.GradScaler("cuda", enabled=(args.device == "cuda"))
    n_params = sum(p.numel() for p in model.parameters())
    say(f"params={n_params} steps/epoch={steps_per_epoch} total_steps={total}")

    anchor = None
    if args.distill > 0:
        apath = os.path.join(args.out, "text_anchor.pt")
        if os.path.exists(apath):
            anchor = torch.load(apath)
        else:
            model.eval()
            chunks = []
            with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=(args.device == "cuda")):
                for i in range(0, len(records), 512):
                    chunks.append(model.pooled_pretrained([r.text for r in records[i:i + 512]], args.max_len).float().cpu())
            anchor = torch.cat(chunks)
            torch.save(anchor, apath)
            say(f"text anchor computed from the pretrained encoder: {tuple(anchor.shape)}")
        anchor = anchor.to(args.device)

    train_keys = keys_all[[r.id for r in train]]
    held_keys = keys_all[[r.id for r in heldout]]
    step = 0
    for epoch in range(args.epochs):
        model.train()
        order = list(range(len(train)))
        random.shuffle(order)
        t0, run, run_c, run_d, run_a = time.time(), 0.0, 0.0, 0.0, 0.0
        for i in range(0, len(order), args.batch):
            bi = order[i:i + args.batch]
            b = [train[j] for j in bi]
            texts, printed, graph = D.to_tensors(b)
            k = torch.tensor([train_keys[j].item() for j in bi], device=args.device)
            with torch.autocast("cuda", dtype=torch.float16, enabled=(args.device == "cuda")):
                _, zt, zs, ht = model(texts, graph.to(args.device), printed.to(args.device),
                                      tree_batch(trees, b, args.device))
            if args.positives == "same":
                loss_c = masked_infonce(zt.float(), zs.float(), k, model.tau)
            else:
                loss_c = supcon_loss(zt.float(), zs.float(), k, model.tau)
            loss_d = torch.zeros((), device=args.device)
            if anchor is not None:
                ids = torch.tensor([b_.id for b_ in b], device=args.device)
                loss_d = relational_distill(ht.float(), anchor[ids])
            loss_a = torch.zeros((), device=args.device)
            if args.aux > 0 and model.last_rec is not None:
                r_hat, p_hat, t_hat, b_hat = model.last_rec
                mse = torch.nn.functional.mse_loss
                loss_a = (mse(r_hat.float(), graph.to(args.device)) + mse(p_hat.float(), printed.to(args.device))
                          + mse(b_hat.float(), graph.to(args.device)))
                if anchor is not None:                       # v7: text slice decodes the frozen pretrained embedding
                    loss_a = loss_a + mse(t_hat.float(), anchor[ids] / anchor[ids].norm(dim=-1, keepdim=True).clamp(min=1e-6))
            loss = loss_c + args.distill * loss_d + args.aux * loss_a
            run_c += loss_c.item(); run_d += loss_d.item(); run_a += loss_a.item()
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt)
            scaler.update()
            sched.step()
            run += loss.item()
            step += 1
        tr = evaluate(model, train, train_keys, args.batch, args.device, seed=args.seed, trees=trees)
        ho = evaluate(model, heldout, held_keys, args.batch, args.device, seed=args.seed, trees=trees)
        say(f"epoch={epoch + 1}/{args.epochs} train_loss={run / steps_per_epoch:.4f} "
            f"(infonce={run_c / steps_per_epoch:.4f} distill={run_d / steps_per_epoch:.4f} aux={run_a / steps_per_epoch:.4f}) "
            f"train_r@1={tr['r@1']:.3f} train_r@10={tr['r@10']:.3f} "
            f"held_loss={ho['loss']:.4f} held_r@1={ho['r@1']:.3f} held_r@10={ho['r@10']:.3f} "
            f"{time.time() - t0:.0f}s")
        torch.save({"state_dict": model.state_dict(), "config": model.config, "args": vars(args),
                    "epoch": epoch + 1}, os.path.join(args.out, f"ckpt_seed{args.seed}.pt"))

    if args.no_export:
        return
    # --- export e_card for every face id
    model.eval()
    embs = []
    with torch.no_grad():
        for i in range(0, len(records), args.batch):
            b = records[i:i + args.batch]
            texts, printed, graph = D.to_tensors(b)
            embs.append(model.embed(texts, graph.to(args.device), printed.to(args.device),
                                    tree_batch(trees, b, args.device)).float().cpu())
    emb = torch.cat(embs)
    suffix = f"_seed{args.seed}" if args.seed != 0 else ""
    torch.save(emb, os.path.join(args.out, f"emb{suffix}.pt"))
    torch.save({"state_dict": model.state_dict(), "config": model.config, "args": vars(args)},
               os.path.join(args.out, f"model{suffix}.pt"))
    final = {"train": tr, "heldout": ho}
    cards_meta = json.load(open(os.path.join(args.cards, "index.json")))
    json.dump({"version": os.path.basename(os.path.normpath(args.out)), "cards_version": cards_meta["version"],
               "cards_pin": cards_meta.get("source_pin"), "n": emb.shape[0], "d_c": emb.shape[1],
               "seed": args.seed, "args": vars(args), "final": final, "split": "split.json",
               "row_i_is": "cards_v1 face id i (index.json names -> id)"},
              open(os.path.join(args.out, f"index{suffix}.json"), "w"), indent=1)
    say(f"exported emb{suffix}.pt {tuple(emb.shape)} final={final}")


if __name__ == "__main__":
    main()
