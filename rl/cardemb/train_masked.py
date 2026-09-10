"""Phase 1c / 2b (v7 plan §2): masked-card-in-deck pretraining of the deck
context (L1) over the decklist corpus, on top of the FROZEN card embedder.

Only runs if 0c is GO (>= 3,000 clean constructed lists).  For each deck
in a batch, 15 % of its distinct cards (at least one) are replaced by a
learned [MASK] row; DeckContext produces c'_i; a bilinear head scores
c'_i against the e_card table restricted to the training vocabulary
(cards that appear in any training list) and cross-entropy recovers the
masked card.  Copy counts stay visible (they are a feature of L1 by
design; a 4-of tells you "staple", not which staple).

Gate (plan §2, 1c/2b): held-out masked top-1 / top-10 accuracy against
the frequency baselines (global most-frequent card; most-frequent card
per format).  Numbers go to rl/artifacts/deck_ctx_v1/index.json and
rl/V7-VALIDATION.md.

Run (WSL, GPU):
    python3 rl/cardemb/train_masked.py --epochs 20 [--seed 0]
"""
import argparse
import json
import os
import random
import sys
import time
from collections import Counter

import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "rl", "deckctx"))
import data as X                                   # noqa: E402  (deckctx/data.py)
from model import DeckContext                      # noqa: E402


class MaskedHead(nn.Module):
    def __init__(self, d_c, table):
        super().__init__()
        self.register_buffer("table", table)       # [V, d_c] frozen e_card of the vocab
        self.proj = nn.Linear(d_c, d_c)
        self.bias = nn.Parameter(torch.zeros(table.shape[0]))

    def forward(self, c):                          # c: [M, d_c] -> logits [M, V]
        return self.proj(c) @ self.table.t() + self.bias


def prepare(corpus, names, emb, by_name, cache):
    """Per-deck tensors with fingerprint bias, cached to disk (fingerprints are slow)."""
    if os.path.exists(cache):
        cached = torch.load(cache)
        if len(cached) == len(corpus) and cached[0]["ids"].tolist() == corpus.ids(0) and cached[-1]["ids"].tolist() == corpus.ids(len(corpus) - 1):
            return cached
        print("  decks_cache.pt does not match the corpus; rebuilding", flush=True)
    out = []
    t0 = time.time()
    for i in range(len(corpus)):
        E, counts, bias, mask, kept = X.deck_tensors(corpus.decklist(i), names, emb, by_name, ids=corpus.ids(i))
        out.append({"ids": torch.tensor(kept, dtype=torch.long), "counts": counts, "bias": bias,
                    "format": corpus.rows[i]["format"], "split": corpus.rows[i]["split"]})
        if (i + 1) % 1000 == 0:
            print(f"  prepared {i + 1}/{len(corpus)} {time.time() - t0:.0f}s", flush=True)
    torch.save(out, cache)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "rl", "artifacts", "deck_ctx_v1"))
    ap.add_argument("--emb", default="emb.pt")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--mask-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    log = open(os.path.join(args.out, f"train_masked_seed{args.seed}.log"), "a", encoding="utf-8")

    def say(msg):
        line = time.strftime("%H:%M:%S ") + msg
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    names = X.load_names()
    emb = torch.load(args.emb).float() if os.path.isabs(args.emb) else X.load_emb(fname=args.emb)
    corpus = X.Corpus()
    by_name = X.load_by_name()
    decks = prepare(corpus, names, emb, by_name, os.path.join(args.out, "decks_cache.pt"))
    train = [d for d in decks if d["split"] == "train" and len(d["ids"]) >= 8]
    held = [d for d in decks if d["split"] == "heldout" and len(d["ids"]) >= 8]
    if args.limit:
        train, held = train[:args.limit], held[:max(32, args.limit // 10)]
    vocab = sorted({int(i) for d in train for i in d["ids"].tolist()})
    v_index = {cid: k for k, cid in enumerate(vocab)}
    freq = Counter(int(i) for d in train for i in d["ids"].tolist())
    freq_fmt = {}
    for d in train:
        freq_fmt.setdefault(d["format"], Counter()).update(int(i) for i in d["ids"].tolist())
    top_global = [c for c, _ in freq.most_common(10)]
    top_fmt = {f: [c for c, _ in cnt.most_common(10)] for f, cnt in freq_fmt.items()}
    say(f"decks train={len(train)} heldout={len(held)} vocab={len(vocab)} device={args.device} seed={args.seed}")

    d_c = emb.shape[1]
    model = DeckContext(d_c=d_c).to(args.device)
    head = MaskedHead(d_c, emb[torch.tensor(vocab)]).to(args.device)
    mask_row = nn.Parameter(torch.zeros(d_c, device=args.device))
    params = list(model.parameters()) + list(head.parameters()) + [mask_row]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)

    def batch_of(items, g):
        Es, tgt_pos, tgts = [], [], []
        for b, d in enumerate(items):
            n = len(d["ids"])
            k = max(1, int(round(args.mask_frac * n)))
            pos = g.sample(range(n), k)
            E = emb[d["ids"]].clone()
            for p in pos:
                E[p] = 0.0
                tgt_pos.append((b, p))
                tgts.append(v_index.get(int(d["ids"][p]), -1))
            Es.append((E, d["counts"], d["bias"], torch.ones(n, dtype=torch.bool), pos))
        E, counts, bias, mask = X.collate([e[:4] for e in Es])
        E = E.to(args.device)
        for b, e in enumerate(Es):
            for p in e[4]:
                E[b, p] = mask_row
        return E, counts.to(args.device), bias.to(args.device), mask.to(args.device), tgt_pos, torch.tensor(tgts, device=args.device)

    def run_eval(items, g):
        model.eval(); head.eval()
        hit1 = hit10 = base1 = base10 = fb1 = fb10 = n = 0
        with torch.no_grad():
            for i in range(0, len(items), args.batch):
                chunk = items[i:i + args.batch]
                E, counts, bias, mask, tp, tg = batch_of(chunk, g)
                c, _ = model(E, counts, bias, mask)
                logits = head(torch.stack([c[b, p] for b, p in tp]))
                top = logits.topk(10, dim=1).indices
                for r, (b, p) in enumerate(tp):
                    t = int(tg[r])
                    if t < 0:
                        continue
                    n += 1
                    hit1 += int(top[r, 0] == t); hit10 += int((top[r] == t).any())
                    cid = vocab[t]
                    base1 += int(top_global[0] == cid); base10 += int(cid in top_global)
                    tf = top_fmt.get(chunk[b]["format"], top_global)
                    fb1 += int(tf[0] == cid); fb10 += int(cid in tf)
        model.train(); head.train()
        return {"n": n, "top1": hit1 / max(1, n), "top10": hit10 / max(1, n),
                "freq_top1": base1 / max(1, n), "freq_top10": base10 / max(1, n),
                "freq_fmt_top1": fb1 / max(1, n), "freq_fmt_top10": fb10 / max(1, n)}

    g_eval = random.Random(1234)
    for epoch in range(args.epochs):
        g = random.Random(args.seed * 1000 + epoch)
        order = list(range(len(train)))
        g.shuffle(order)
        t0, run, steps = time.time(), 0.0, 0
        for i in range(0, len(order), args.batch):
            items = [train[j] for j in order[i:i + args.batch]]
            E, counts, bias, mask, tp, tg = batch_of(items, g)
            c, _ = model(E, counts, bias, mask)
            logits = head(torch.stack([c[b, p] for b, p in tp]))
            keep = tg >= 0
            loss = F.cross_entropy(logits[keep], tg[keep])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            run += loss.item(); steps += 1
        ho = run_eval(held, random.Random(1234))
        say(f"epoch={epoch + 1}/{args.epochs} loss={run / max(1, steps):.4f} held_top1={ho['top1']:.3f} "
            f"held_top10={ho['top10']:.3f} freq_top1={ho['freq_top1']:.3f} freq_fmt_top1={ho['freq_fmt_top1']:.3f} "
            f"freq_fmt_top10={ho['freq_fmt_top10']:.3f} n={ho['n']} {time.time() - t0:.0f}s")
    tr = run_eval(train[:2000], random.Random(1234))
    ho = run_eval(held, random.Random(1234))
    torch.save({"model": model.state_dict(), "head": head.state_dict(), "mask_row": mask_row.detach().cpu(),
                "vocab": vocab, "config": model.config, "args": vars(args)},
               os.path.join(args.out, f"model_seed{args.seed}.pt"))
    json.dump({"version": "deck_ctx_v1", "card_emb": args.emb, "seed": args.seed, "args": vars(args),
               "n_train": len(train), "n_heldout": len(held), "vocab": len(vocab),
               "final": {"train": tr, "heldout": ho}},
              open(os.path.join(args.out, f"index_seed{args.seed}.json"), "w"), indent=1)
    say(f"final heldout={ho} train={tr}")


if __name__ == "__main__":
    main()
