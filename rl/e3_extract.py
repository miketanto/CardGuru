"""E3 feature extractor: E2 mechanical dims + a text-embedding
card-semantics channel.

Phase 8b proved the card channel is load-bearing but consumed as LOCAL
IDENTIFIERS: E2's 68 graph dims give Spell Snare and Force Spike the
*identical* vector, so no policy can tell "counter unless {1} is paid"
from "counter a mana value 2 spell". This adds a text channel that can.

Layout of every row: [ 68 E2 mechanical dims | T text dims ].
The mechanical half is copied VERBATIM out of rl/e2_features.tsv - the
E2 file is never rewritten and never re-derived, so the only difference
between the E2 and E3 channels is the appended text block.

Text channel (rl/e3_text_spike.py validated the approach):
  1. oracle text straight off the Forge cardsfolder scripts, with
     parenthetical reminder text dropped (it is keyword restatement -
     already covered by the mechanical keyword dims - and it swamps
     short rules text) and self-references folded to CARDNAME;
  2. tokens = unigrams + bigrams, with NUMERIC BUCKETING (the spike's
     finding: raw TF-IDF put Shock/Lightning Strike at .17 because it
     over-weights "2" vs "3") and mana symbols kept colored;
  3. TF-IDF (sublinear tf, min_df 5), truncated SVD to T dims,
     L2-normalized and scaled to TEXT_SCALE so the block is numerically
     comparable to the sparse binary mechanical half.
Normalization and T were chosen on the gate metrics of rl/e3_gates.py
(swept in PHASE-E3.md): reminder-stripping and CARDNAME folding both
raise analog-pair coherence, and cosines flatten out past T=32
(swap-pair mean .71 -> .62 at T=64 while Snare/Spike drifts up).
A neural sentence embedder was tried first and is unreachable from this
container (huggingface.co is denied at the egress proxy - see
rl/PHASE-E3.md); TF-IDF+SVD is the spike's validated fallback.

Run: python3 rl/e3_extract.py [--dim 40] [--out rl/e3_features.tsv]
Gates: python3 rl/e3_gates.py
"""
import argparse
import os
import re

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

REPO = "/home/user/CardGuru"
E2 = os.path.join(REPO, "rl/e2_features.tsv")
CARDSFOLDER = "/home/user/forge-src/forge-gui/res/cardsfolder"
TEXT_SCALE = 2.0          # L2 norm of the text block (mechanical ~3.3)

MANA_RE = re.compile(r"\{([^}]*)\}")
NUM_RE = re.compile(r"^\d+$")
REMINDER_RE = re.compile(r"\([^)]*\)")


def load_oracle(root):
    """name -> oracle text, straight off the Forge card scripts."""
    oracle = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            if not fn.endswith(".txt"):
                continue
            name = txt = None
            try:
                with open(os.path.join(dp, fn), encoding="utf-8",
                          errors="ignore") as fh:
                    for line in fh:
                        if line.startswith("Name:"):
                            name = line[5:].strip()
                        elif line.startswith("Oracle:"):
                            txt = line[7:].strip()
            except OSError:
                continue
            if name and txt:
                oracle[name] = txt
    return oracle


def bucket_num(n):
    """Numeric bucketing: keep small exact values (they are decisions -
    1 vs 2 damage, mana value 2 vs 3), collapse the long tail."""
    v = int(n)
    if v <= 4:
        return f"n{v}"
    if v <= 6:
        return "n5_6"
    if v <= 10:
        return "n7_10"
    return "nbig"


def normalize(name, text):
    """Drop reminder text; fold the card's own name (and, for the
    "Name, Title" legendary form, its short name) to CARDNAME so
    self-references stop acting as card-unique identifier tokens."""
    t = REMINDER_RE.sub(" ", text)
    for face in name.split(" // "):
        if not face:
            continue
        t = t.replace(face, " CARDNAME ")
        if "," in face:
            short = face.split(",")[0]
            if len(short) > 3:
                t = t.replace(short, " CARDNAME ")
    return t


def toks(text):
    t = text.lower().replace("\\n", " ")
    # mana symbols keep their color; generic/X collapse to one token each
    def _sym(m):
        s = m.group(1).lower()
        if s.isdigit():
            return " symgen "
        return " sym" + re.sub(r"[^a-z0-9]", "", s) + " "
    t = MANA_RE.sub(_sym, t)
    words = re.findall(r"[a-z0-9']+", t)
    words = [bucket_num(w) if NUM_RE.match(w) else w for w in words]
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]


def text_for(name, oracle):
    """Oracle text for an E2 row name. Multi-face rows are registered
    under each face name and the 'A // B' join (e2_extract.py); the join
    gets the concatenation, matching the union taken on the graph side."""
    if name in oracle:
        return normalize(name, oracle[name])
    if " // " in name:
        parts = [normalize(f, oracle[f]) for f in name.split(" // ")
                 if f in oracle]
        if parts:
            return " ".join(parts)
    return ""


def load_e2(path):
    names, mech = [], []
    with open(path, encoding="utf-8") as f:
        dim = int(f.readline().strip())
        for line in f:
            if not line.strip():
                continue
            n, _, v = line.rstrip("\n").partition("\t")
            names.append(n)
            mech.append(v)
    return dim, names, mech


def embed(texts, dim, seed=0):
    """TF-IDF -> truncated SVD -> L2-normalized, sign-canonicalized."""
    vec = TfidfVectorizer(analyzer=lambda t: toks(t), min_df=5,
                          sublinear_tf=True, dtype=np.float32)
    X = vec.fit_transform(texts)
    svd = TruncatedSVD(n_components=dim, algorithm="randomized",
                       n_iter=7, random_state=seed)
    Z = svd.fit_transform(X)
    # SVD signs are arbitrary; pin them so reruns are byte-identical
    for j in range(Z.shape[1]):
        col = svd.components_[j]
        if col[np.argmax(np.abs(col))] < 0:
            Z[:, j] *= -1.0
    norms = np.linalg.norm(Z, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (Z / norms) * TEXT_SCALE, X.shape[1], svd.explained_variance_ratio_.sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dim", type=int, default=32, help="text dims (32-48)")
    ap.add_argument("--out", default=os.path.join(REPO, "rl/e3_features.tsv"))
    ap.add_argument("--cardsfolder", default=CARDSFOLDER)
    args = ap.parse_args()

    mech_dim, names, mech = load_e2(E2)
    oracle = load_oracle(args.cardsfolder)
    texts = [text_for(n, oracle) for n in names]
    hits = sum(1 for t in texts if t)
    print(f"E2 rows {len(names)} dim {mech_dim}; oracle cards {len(oracle)}; "
          f"text matched {hits} ({hits / len(names):.1%})")

    Z, vocab, evr = embed(texts, args.dim)
    Z[[i for i, t in enumerate(texts) if not t]] = 0.0   # no text -> silent
    print(f"vocab {vocab} -> {args.dim} dims, explained variance {evr:.3f}")

    with open(args.out, "w", encoding="utf-8") as out:
        out.write(f"{mech_dim + args.dim}\n")
        for i, n in enumerate(names):
            out.write(n + "\t" + mech[i] + ","
                      + ",".join("%.5g" % x for x in Z[i]) + "\n")
    print(f"wrote {len(names)} names dim={mech_dim + args.dim} -> {args.out}")


if __name__ == "__main__":
    main()
