"""Phase 2 (v7 plan §2): decklist -> DeckContext inputs.

deck_tensors(decklist, ...) builds, for one deck, the (E, counts, bias,
mask) tuple DeckContext consumes:

  E       [N, d_c]  e_card rows from rl/artifacts/card_emb_v1/emb.pt
                    (cards_v1 face ids; unresolved names are dropped)
  counts  [N]       copies of each distinct card
  bias    [N, N]    enabler(row) -> payoff(col) weight from
                    cardguru.fingerprint.build_fingerprint (the same
                    edges Meta Lab / the answer-finder use), 0 elsewhere
  mask    [N]       all True (padding is added by `collate`)

`collate(list of tuples)` pads to the longest deck.  `Corpus` wraps
rl/artifacts/decklists_v1/decklists.jsonl.gz (built by
rl/decklists/build_corpus.py) for 2b/1c masked-card pretraining.

The fingerprint needs the Forge records (data/dataset.jsonl.gz, the
same file cards_v1 was built from); `load_by_name` builds that map once.
"""
import gzip
import json
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)
from cardguru.dataset import load as load_dataset, norm_name     # noqa: E402
from cardguru.fingerprint import build_fingerprint               # noqa: E402

CARDS_V1 = os.path.join(REPO, "rl", "artifacts", "cards_v1")
CARD_EMB = os.path.join(REPO, "rl", "artifacts", "card_emb_v1")
DECKLISTS = os.path.join(REPO, "rl", "artifacts", "decklists_v1", "decklists.jsonl.gz")


def load_by_name(dataset_path=os.path.join(REPO, "data", "dataset.jsonl.gz")):
    """Forge record per card name (first face wins), keyed by exact and by normalised name."""
    _, recs = load_dataset(dataset_path)
    by = {}
    for r in recs:
        by.setdefault(r.get("name"), r)
        by.setdefault(norm_name(r.get("name") or ""), r)
    return by


def load_names(cards_dir=CARDS_V1):
    return json.load(open(os.path.join(cards_dir, "index.json"), encoding="utf-8"))["names"]


def load_emb(emb_dir=CARD_EMB, fname="emb.pt"):
    return torch.load(os.path.join(emb_dir, fname)).float()


def fingerprint_bias(decklist, by_name):
    """[N, N] enabler->payoff weights for a decklist of (name, count), rows in decklist order."""
    n = len(decklist)
    pos = {name: i for i, (name, _) in enumerate(decklist)}
    bias = torch.zeros(n, n)
    if not by_name:
        return bias
    lst = [(name, int(c)) for name, c in decklist]
    fp = build_fingerprint({name: by_name.get(name) or by_name.get(norm_name(name)) for name, _ in lst
                            if by_name.get(name) or by_name.get(norm_name(name))}, lst)
    for e in fp.get("edges", []):
        i, j = pos.get(e["enabler"]), pos.get(e["payoff"])
        if i is not None and j is not None:
            bias[i, j] = max(bias[i, j].item(), float(e.get("weight", 1)))
    return bias


def deck_tensors(decklist, names, emb, by_name=None, ids=None):
    """decklist: [(name, count)].  ids: optional precomputed cards_v1 ids (same order),
    -1 for unresolved.  Returns (E, counts, bias, mask, kept_ids)."""
    if ids is None:
        ids = [names.get(norm_name(n), -1) for n, _ in decklist]
    keep = [k for k, i in enumerate(ids) if i >= 0]
    dl = [decklist[k] for k in keep]
    kept = [ids[k] for k in keep]
    E = emb[torch.tensor(kept, dtype=torch.long)] if kept else emb[:0]
    counts = torch.tensor([int(c) for _, c in dl], dtype=torch.long)
    bias = fingerprint_bias(dl, by_name) if by_name is not None else torch.zeros(len(dl), len(dl))
    mask = torch.ones(len(dl), dtype=torch.bool)
    return E, counts, bias, mask, kept


def collate(items):
    """items: list of (E, counts, bias, mask[, ...]) -> padded batch tensors."""
    N = max(x[0].shape[0] for x in items)
    d = items[0][0].shape[1]
    B = len(items)
    E = torch.zeros(B, N, d)
    counts = torch.zeros(B, N, dtype=torch.long)
    bias = torch.zeros(B, N, N)
    mask = torch.zeros(B, N, dtype=torch.bool)
    for b, x in enumerate(items):
        n = x[0].shape[0]
        E[b, :n] = x[0]; counts[b, :n] = x[1]; bias[b, :n, :n] = x[2]; mask[b, :n] = True
    return E, counts, bias, mask


class Corpus:
    """decklists_v1 rows (clean constructed lists by default) with cached ids."""

    def __init__(self, path=DECKLISTS, split=None, clean_only=True):
        self.rows = []
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if clean_only and not r.get("clean"):
                    continue
                if split and r.get("split") != split:
                    continue
                self.rows.append(r)

    def __len__(self):
        return len(self.rows)

    def decklist(self, i):
        return [(n, q) for n, q in self.rows[i]["main_names"]]

    def ids(self, i):
        return [cid for cid, _ in self.rows[i]["main"]]
