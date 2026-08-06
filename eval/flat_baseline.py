"""Flat-RAG baseline: BM25 retrieval over oracle text + type line.

This is the "raw RAG" arm of the graph-vs-flat ablation (plan/eval.md §D):
a standard lexical retriever over exactly the card text a text-RAG system
would embed/index, with the usual normalizations (lowercase, mana/tap symbol
expansion, light stemming of plurals). No graph, no ontology.
"""
from __future__ import annotations

import gzip
import json
import math
import re
from collections import Counter, defaultdict

SYMBOLS = {"{t}": "tap", "{q}": "untap", "{w}": "white", "{u}": "blue",
           "{b}": "black", "{r}": "red", "{g}": "green", "{c}": "colorless",
           "{x}": "x"}

STOP = {"a", "an", "the", "of", "to", "and", "or", "that", "this", "it", "its",
        "is", "are", "with", "for", "on", "in", "you", "your", "as", "at",
        "be", "by", "if", "would", "may", "cards", "card", "spells", "spell"}


def tokenize(text: str) -> list[str]:
    text = text.lower()
    for sym, word in SYMBOLS.items():
        text = text.replace(sym, " " + word + " ")
    toks = re.findall(r"[a-z0-9+/']+", text)
    out = []
    for t in toks:
        if t in STOP:
            continue
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]                      # cheap plural stem
        out.append(t)
    return out


class BM25:
    def __init__(self, docs: dict[str, str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = {}
        self.df = Counter()
        self.dl = {}
        for name, text in docs.items():
            toks = tokenize(text)
            self.tf[name] = Counter(toks)
            self.dl[name] = len(toks) or 1
            for t in set(toks):
                self.df[t] += 1
        self.n = len(docs)
        self.avgdl = sum(self.dl.values()) / max(1, self.n)

    def search(self, query: str, k: int = 30) -> list[tuple[str, float]]:
        q = tokenize(query)
        scores = defaultdict(float)
        for t in q:
            df = self.df.get(t)
            if not df:
                continue
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            for name, tf in self.tf.items():
                f = tf.get(t)
                if not f:
                    continue
                dl = self.dl[name]
                scores[name] += idf * f * (self.k1 + 1) / (
                    f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return sorted(scores.items(), key=lambda kv: -kv[1])[:k]


def load_docs(dataset_path: str = "data/dataset.jsonl.gz") -> dict[str, str]:
    docs = {}
    with gzip.open(dataset_path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            name = r.get("name")
            if not name or name in docs:
                continue
            docs[name] = f"{r.get('types') or ''}\n{r.get('oracle') or ''}"
    return docs


if __name__ == "__main__":
    import sys
    bm = BM25(load_docs())
    for name, score in bm.search(" ".join(sys.argv[1:]) or "destroy target creature", 15):
        print(f"{score:7.2f}  {name}")
