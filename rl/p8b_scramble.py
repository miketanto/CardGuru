"""Phase 8b step 1: feature-scramble diagnostic TSVs.

Does a trained attn policy actually READ the card-feature channel?
Two eval-time corruptions of rl/e2_features.tsv:

  scrambled — every card name gets a DIFFERENT card's feature vector
              (fixed-seed derangement-ish permutation over all rows);
  zeroed    — every card name maps to the all-zero vector (the
              unknown-card flag pattern).

If attn_desp's win rate on its training deck barely moves under these,
the card channel is not load-bearing and Phase 8's transfer null is
explained at the mechanism level.

Run: python3 rl/p8b_scramble.py   (writes /tmp/rl_p8b/e2_scrambled.tsv
     and /tmp/rl_p8b/e2_zeroed.tsv)
"""
import os
import random

SRC = "/home/user/CardGuru/rl/e2_features.tsv"
OUTDIR = "/tmp/rl_p8b"


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    names, vecs = [], []
    with open(SRC) as f:
        dim = f.readline().strip()
        for line in f:
            n, _, v = line.rstrip("\n").partition("\t")
            names.append(n)
            vecs.append(v)

    rng = random.Random(88)
    idx = list(range(len(vecs)))
    rng.shuffle(idx)
    # guarantee no fixed points (cheap swap-fix pass)
    for i in range(len(idx)):
        if idx[i] == i:
            j = (i + 1) % len(idx)
            idx[i], idx[j] = idx[j], idx[i]
    with open(os.path.join(OUTDIR, "e2_scrambled.tsv"), "w") as out:
        out.write(dim + "\n")
        for i, n in enumerate(names):
            out.write(n + "\t" + vecs[idx[i]] + "\n")

    zero = ",".join(["0"] * int(dim))
    with open(os.path.join(OUTDIR, "e2_zeroed.tsv"), "w") as out:
        out.write(dim + "\n")
        for n in names:
            out.write(n + "\t" + zero + "\n")
    print(f"wrote {len(names)} rows x2 -> {OUTDIR}")


if __name__ == "__main__":
    main()
