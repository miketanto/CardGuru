"""E3 acceptance gates - run BEFORE any training on the E3 channel.

Three gates, all from rl/CHECKPOINT-PHASE10.md 4.3 and the spike:

  G1 SEPARATION   Spell Snare / Force Spike are the SAME vector in E2
                  (d=0, so no policy can play them differently) and are
                  functionally different cards. In E3 they must be
                  distinguishable: out of the near-duplicate cosine band
                  that true analogs occupy, and separated by more than
                  one mechanical-dim flip in the full vector - while
                  still ranking as less alike than the average analog.
  G2 SWAP PAIRS   the 16 (out, in) pairs of P8SwapInteraction /
                  Threats / Mixed (rl/p8_swap_pick.py output, tabled in
                  PHASE8-TRANSFER.md) carried perfect zero-shot
                  transfer at E2 d=0-4. They must stay close in E3:
                  every pair clearly above the unrelated-card baseline,
                  as a group well above it.
  G3 CLASSES      the spike's pair table: synonyms ~1, near-identical
                  burn high (this is what numeric bucketing buys),
                  cross-class pairs low, and no global collapse.

Thresholds are referenced to two measured baselines rather than picked
free-hand: RANDOM (mean cosine of unrelated cards) is the floor, and
the near-duplicate band (Cancel/Counterspell, Murder/Doom Blade,
Shock/Lightning Strike, all >= .89) is the ceiling.

Run: python3 rl/e3_gates.py [--feat rl/e3_features.tsv] [--mech 68]
Exit status 0 iff every gate passes.
"""
import argparse
import os
import random

import numpy as np

REPO = "/home/user/CardGuru"

# PHASE8-TRANSFER.md milestone 1 tables: (out, in, E2 mismatch count)
SWAP_PAIRS = [
    ("Bitter Triumph", "Go for the Throat", 0),
    ("Requiting Hex", "Cut Down", 2),
    ("Shoot the Sheriff", "Eliminate", 0),
    ("Spell Snare", "Dispel", 0),
    ("We Say Thee Nay!", "Don't Make a Sound", 0),
    ("Spell Pierce", "Stubborn Denial", 0),
    ("Floodpits Drowner", "Zephyr Sentinel", 4),
    ("The Wondrous Wasp", "Plumecreed Escort", 1),
    ("Spyglass Siren", "Faerie Seer", 2),
    ("Elektra, Daughter of the Hand", "Fathom Fleet Cutthroat", 0),
    ("Bitter Triumph", "Easy Prey", 0),
    ("Shoot the Sheriff", "Cradle to Grave", 0),
    ("We Say Thee Nay!", "Clash of Wills", 0),
    ("Spell Pierce", "Concerted Defense", 0),
    ("Spyglass Siren", "Faerie Miscreant", 2),
    ("Elektra, Daughter of the Hand", "Ravenous Chupacabra", 0),
]

CLASS_PAIRS = [
    ("Cancel", "Counterspell", "hi", "true synonyms"),
    ("Shock", "Lightning Strike", "hi", "near-identical burn (bucketing)"),
    ("Murder", "Doom Blade", "hi", "one restriction apart"),
    ("Spell Snare", "Essence Scatter", "mid", "same family, diff condition"),
    ("Murder", "Shock", "lo", "different removal classes"),
    ("Spell Snare", "Murder", "lo", "counter vs removal"),
]
HI, MID_LO, MID_HI, LO = 0.70, 0.25, 0.85, 0.40

DUP_BAND = 0.85      # G1: Snare/Spike must fall below the near-duplicate band
MIN_SEP = 1.00       # G1: and be >= one binary mechanical dim flip apart
SWAP_MEAN = 0.60     # G2: analogs as a group
RAND_MULT = 2.0      # G2: every analog pair >= 2x the unrelated baseline


def load(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        dim = int(f.readline().strip())
        for line in f:
            if not line.strip():
                continue
            n, _, v = line.rstrip("\n").partition("\t")
            rows[n] = np.fromstring(v, sep=",", dtype=np.float64)
    return dim, rows


def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feat", default=os.path.join(REPO, "rl/e3_features.tsv"))
    ap.add_argument("--mech", type=int, default=68, help="mechanical dims")
    args = ap.parse_args()

    dim, rows = load(args.feat)
    M = args.mech
    print(f"{args.feat}: {len(rows)} rows, dim {dim} "
          f"(mechanical {M} + text {dim - M})\n")

    def txt(n):
        return rows[n][M:]

    def full(n):
        return rows[n]

    def have(*ns):
        return all(n in rows for n in ns)

    ok = True

    # ---- baseline: what "unrelated" looks like in this space ----------
    rng = random.Random(3)
    live = [n for n in rows if np.any(txt(n))]
    samp = [cos(txt(rng.choice(live)), txt(rng.choice(live)))
            for _ in range(4000)]
    rand_mean, p95 = float(np.mean(samp)), float(np.percentile(samp, 95))
    print(f"BASELINE  unrelated-card text cosine: mean {rand_mean:.3f}, "
          f"p95 {p95:.3f}   ({len(live)} rows with text)\n")

    # ---- G1 separation -----------------------------------------------
    print("G1 SEPARATION  Spell Snare / Force Spike")
    if not have("Spell Snare", "Force Spike"):
        print("  MISSING card rows"); return 1
    mech_d = float(np.linalg.norm(full("Spell Snare")[:M] - full("Force Spike")[:M]))
    txt_c = cos(txt("Spell Snare"), txt("Force Spike"))
    full_d = float(np.linalg.norm(full("Spell Snare") - full("Force Spike")))
    print(f"  E2 mechanical distance   {mech_d:.3f}   (0 = indistinguishable)")
    print(f"  E3 text cosine           {txt_c:.3f}")
    print(f"  E3 full-vector distance  {full_d:.3f}")

    # ---- G2 swap pairs -----------------------------------------------
    print("\nG2 SWAP PAIRS  (must stay close; E2 d = mismatch count / 68)")
    print(f"  {'pair':<52} {'E2 d':>5} {'txtcos':>7} {'E3 dist':>8}")
    swap_cos, swap_d, missing = [], [], []
    for a, b, d in SWAP_PAIRS:
        if not have(a, b):
            missing.append((a, b))
            continue
        c = cos(txt(a), txt(b))
        fd = float(np.linalg.norm(full(a) - full(b)))
        swap_cos.append(c)
        swap_d.append(fd)
        print(f"  {a + ' / ' + b:<52} {d:>5} {c:>7.3f} {fd:>8.3f}")
    for a, b in missing:
        print(f"  {a + ' / ' + b:<52}  MISSING")
    floor = RAND_MULT * rand_mean
    swap_mean = float(np.mean(swap_cos))
    g2 = bool(swap_cos) and not missing and min(swap_cos) >= floor \
        and swap_mean >= SWAP_MEAN
    print(f"  min {min(swap_cos):.3f}  mean {swap_mean:.3f}  "
          f"max E3 dist {max(swap_d):.3f}   -> {'PASS' if g2 else 'FAIL'}"
          f"  (gate: every pair >= {RAND_MULT:g}x unrelated = {floor:.3f}, "
          f"mean >= {SWAP_MEAN})")
    ok &= g2

    g1 = mech_d == 0.0 and txt_c <= DUP_BAND and full_d >= MIN_SEP \
        and txt_c < swap_mean
    print(f"\nG1 verdict: text cos {txt_c:.3f} <= near-duplicate band "
          f"{DUP_BAND} and < analog mean {swap_mean:.3f}; E3 distance "
          f"{full_d:.3f} >= {MIN_SEP:.2f} (one mechanical dim flip), from "
          f"E2 {mech_d:.3f}  -> {'PASS' if g1 else 'FAIL'}")
    ok &= g1

    # ---- G3 class structure ------------------------------------------
    print("\nG3 CLASS STRUCTURE  (text cosine)")
    print(f"  {'pair':<44} {'cos':>6}  {'want':<12} note")
    for a, b, want, note in CLASS_PAIRS:
        if not have(a, b):
            print(f"  {a + ' / ' + b:<44}  MISSING")
            ok = False
            continue
        c = cos(txt(a), txt(b))
        good = (c >= HI if want == "hi" else
                c <= LO if want == "lo" else MID_LO <= c <= MID_HI)
        ok &= good
        band = {"hi": f">= {HI}", "lo": f"<= {LO}",
                "mid": f"{MID_LO}-{MID_HI}"}[want]
        print(f"  {a + ' / ' + b:<44} {c:>6.3f}  {band:<12} "
              f"{'ok ' if good else 'BAD'} {note}")

    # no-collapse check: unrelated cards must not all look alike
    collapse_ok = rand_mean < 0.25 and p95 < 0.75
    ok &= collapse_ok
    print(f"\n  unrelated-pair cosine: mean {rand_mean:.3f}, p95 {p95:.3f}  "
          f"-> {'PASS' if collapse_ok else 'FAIL'} (no collapse)")

    print(f"\nALL GATES: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
