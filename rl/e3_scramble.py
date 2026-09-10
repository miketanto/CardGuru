"""E3 block-wise feature corruption - the Phase 8b scramble, per channel.

rl/p8b_scramble.py corrupts a whole feature row, which answers "is the
card channel read?" but cannot say WHICH half is read. E3 rows are
[68 mechanical | 32 text], so this writes one corrupted TSV per block:

  text_scrambled  text block permuted across cards, mechanical intact
  text_zeroed     text block zeroed, mechanical intact
  mech_scrambled  mechanical block permuted, text intact (positive
                  control: 8b measured -.38 for this channel)
  all_scrambled   whole row permuted (the exact 8b protocol)

Same fixed-seed no-fixed-point permutation as 8b, so a card never keeps
its own block.

Run: python3 rl/e3_scramble.py [--feat rl/e3_features.tsv]
     [--mech 68] [--outdir /tmp/rl_e3_ablate]
"""
import argparse
import os
import random


def load(path):
    names, vals = [], []
    with open(path, encoding="utf-8") as f:
        dim = int(f.readline().strip())
        for line in f:
            if not line.strip():
                continue
            n, _, v = line.rstrip("\n").partition("\t")
            names.append(n)
            vals.append(v.split(","))
    return dim, names, vals


def permutation(n, seed=88):
    rng = random.Random(seed)
    idx = list(range(n))
    rng.shuffle(idx)
    for i in range(n):            # cheap swap-fix: no card keeps its own
        if idx[i] == i:
            j = (i + 1) % n
            idx[i], idx[j] = idx[j], idx[i]
    return idx


def write(path, dim, names, rows):
    with open(path, "w", encoding="utf-8") as out:
        out.write(f"{dim}\n")
        for n, r in zip(names, rows):
            out.write(n + "\t" + ",".join(r) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feat", default="/home/user/CardGuru/rl/e3_features.tsv")
    ap.add_argument("--mech", type=int, default=68)
    ap.add_argument("--outdir", default="/tmp/rl_e3_ablate")
    args = ap.parse_args()

    dim, names, vals = load(args.feat)
    m = args.mech
    os.makedirs(args.outdir, exist_ok=True)
    idx = permutation(len(vals))
    zeros = ["0"] * (dim - m)

    variants = {
        "text_scrambled": [vals[i][:m] + vals[j][m:]
                           for i, j in enumerate(idx)],
        "text_zeroed": [v[:m] + zeros for v in vals],
        "mech_scrambled": [vals[j][:m] + vals[i][m:]
                           for i, j in enumerate(idx)],
        "all_scrambled": [vals[j] for j in idx],
    }
    for tag, rows in variants.items():
        p = os.path.join(args.outdir, f"e3_{tag}.tsv")
        write(p, dim, names, rows)
        print(f"wrote {len(rows)} rows -> {p}")


if __name__ == "__main__":
    main()
