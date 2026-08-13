"""E3 feasibility spike: text-vectorized card semantics.

Verdict (2026-08-13, Forge cardsfolder HEAD, 33,308 cards): even
stdlib TF-IDF over oracle text separates Spell Snare/Force Spike
(E2 distance 0 -> cosine .26) while keeping Cancel/Counterspell at
1.00 and removal/counter classes ~orthogonal. Session C should:
  1. bucket numeric tokens (damage, MV thresholds) - Shock/Lightning
     Strike at .17 shows raw TF-IDF over-weights short-text diffs;
  2. SVD to 32-48 dims, append to E2's 91 mechanical dims;
  3. try a neural sentence embedder first, keep TF-IDF+SVD as the
     validated offline fallback;
  4. gate on: Snare/Spike separated, P8 swap pairs stay close,
     class structure preserved.
Group 1 (known-top-of-library, hand differential) remains hand-built
STATE features - embeddings cannot encode what was seen.

Run: python3 rl/e3_text_spike.py [forge-src-root]
"""
import collections
import math
import os
import re
import sys

ROOT = (sys.argv[1] if len(sys.argv) > 1 else "/home/user/forge-src") \
    + "/forge-gui/res/cardsfolder"


def load_oracle(root):
    oracle = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if not fn.endswith(".txt"):
                continue
            name = txt = None
            try:
                for line in open(os.path.join(dp, fn), encoding="utf-8",
                                 errors="ignore"):
                    if line.startswith("Name:"):
                        name = line[5:].strip()
                    elif line.startswith("Oracle:"):
                        txt = line[7:].strip()
            except OSError:
                continue
            if name and txt:
                oracle[name] = txt
    return oracle


def toks(t):
    t = t.lower()
    t = re.sub(r"\{[^}]*\}", " MANASYM ", t)
    words = re.findall(r"[a-z0-9']+|MANASYM", t)
    return list(words) + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def main():
    oracle = load_oracle(ROOT)
    print(len(oracle), "cards with oracle text")
    df = collections.Counter()
    docs = {}
    for n, t in oracle.items():
        docs[n] = collections.Counter(toks(t))
        for w in set(docs[n]):
            df[w] += 1
    big_n = len(docs)

    def vec(n):
        return {w: c * math.log(big_n / (1 + df[w]))
                for w, c in docs[n].items()}

    def cos(a, b):
        va, vb = vec(a), vec(b)
        dot = sum(va[w] * vb.get(w, 0) for w in va)
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        return dot / (na * nb) if na and nb else 0.0

    pairs = [
        ("Spell Snare", "Force Spike", "MUST SEPARATE (E2 dist 0)"),
        ("Cancel", "Counterspell", "true synonyms ~1.0"),
        ("Shock", "Lightning Strike", "near-identical burn"),
        ("Murder", "Doom Blade", "one restriction apart"),
        ("Spell Snare", "Essence Scatter", "same family, diff condition"),
        ("Murder", "Shock", "different removal classes"),
        ("Spell Snare", "Murder", "counter vs removal - far"),
    ]
    print(f"{'pair':<40} {'cosine':>7}  expectation")
    for a, b, note in pairs:
        if a in oracle and b in oracle:
            print(f"{a + ' / ' + b:<40} {cos(a, b):>7.3f}  {note}")
        else:
            print(f"{a + ' / ' + b:<40} MISSING")


if __name__ == "__main__":
    main()
