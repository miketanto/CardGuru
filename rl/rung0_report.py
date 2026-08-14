"""Rung 0: pool the seeds and report them honestly.

Two reasons this exists rather than reading the lane's own log lines.

1. THE LANE'S INLINE BAND IS WRONG AT THE EDGES. `rung0_lane.sh` prints
   a Wald interval, 1.96*sqrt(p(1-p)/n), which collapses to +-0.000 when
   a checkpoint goes 0/200 or 200/200. The untrained baseline does
   exactly that, so the log's first row claims zero uncertainty about a
   result it has no right to be certain of. This uses a WILSON score
   interval, which stays finite at p=0 and p=1 (0/200 -> upper bound
   ~.019, not 0).

2. PER-SEED ROWS ARE NOT THE RESULT. Every claim in this project that
   compared two separately-trained nets at 1-2 seeds turned out
   provisional - E3 beat E2 by +.175 on seed 0 and +.020 on seed 1, and
   its faeries result reversed outright between them. So the headline
   has to be the pooled number with its band, and the between-seed
   SPREAD has to be printed next to it: a mean that hides a .30 range is
   not a finding.

Run: python3 rl/rung0_report.py [--base W0Base] [--root /tmp]
"""
import argparse
import glob
import math
import os
import re

LABELS = ["D0", "D1", "TWIN"]


def wilson(k, n, z=1.96):
    """95% score interval. Finite at k=0 and k=n, unlike Wald."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def read_probe(path):
    """-> (wins, episodes); draws count as half a win, as Elo does."""
    try:
        text = open(path).read()
    except OSError:
        return None
    def f(k):
        m = re.search(r"\b%s=([0-9.]+)" % k, text)
        return float(m.group(1)) if m else None
    n, w, d = f("episodes"), f("wins"), f("draws")
    if n is None or w is None:
        return None
    return (w + 0.5 * (d or 0.0), int(n))


def fmt(k, n):
    if n == 0:
        return "%-16s" % "-"
    p, lo, hi = wilson(k, n)
    return "%.3f [%.3f,%.3f]" % (p, lo, hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="W0Base")
    ap.add_argument("--root", default="/tmp")
    args = ap.parse_args()

    # "_s*" also matches the sweep's own _sweep.log/_sweep.out, which
    # silently inflated the seed count in the header; require a digit and
    # a directory.
    seeds = sorted(d for d in glob.glob(os.path.join(
        args.root, "rl_rung0_%s_s[0-9]*" % args.base)) if os.path.isdir(d))
    if not seeds:
        print("no seed directories under %s for %s" % (args.root, args.base))
        return

    # checkpoint -> label -> [(k, n) per seed]
    curve = {}
    for d in seeds:
        for path in glob.glob(os.path.join(d, "probe_*_*.txt")):
            m = re.match(r"probe_(\w+)_(\d+)\.txt$", os.path.basename(path))
            if not m:
                continue
            label, tr = m.group(1), int(m.group(2))
            got = read_probe(path)
            if got:
                curve.setdefault(tr, {}).setdefault(label, []).append(got)

    print("=== %s — learning curve, pooled over %d seed(s), "
          "Wilson 95%%" % (args.base, len(seeds)))
    print("%8s  %-22s %-22s %-22s %s"
          % ("trained", "vs D0", "vs D1", "vs TWIN (transfer)", "D0-TWIN"))
    for tr in sorted(curve):
        row, gap = [], ""
        for label in LABELS:
            pairs = curve[tr].get(label, [])
            row.append(fmt(sum(k for k, _ in pairs), sum(n for _, n in pairs)))
        d0, tw = curve[tr].get("D0", []), curve[tr].get("TWIN", [])
        if d0 and tw:
            a = sum(k for k, _ in d0) / max(1, sum(n for _, n in d0))
            b = sum(k for k, _ in tw) / max(1, sum(n for _, n in tw))
            gap = "%+.3f" % (a - b)
        print("%8d  %-22s %-22s %-22s %s" % (tr, row[0], row[1], row[2], gap))

    # between-seed spread at the final checkpoint: a pooled mean that
    # hides a wide range is not a finding
    final = max(curve) if curve else None
    if final is not None and len(seeds) > 1:
        print()
        print("=== between-seed spread at trained=%d" % final)
        for label in LABELS:
            ps = [k / n for k, n in curve[final].get(label, []) if n]
            if len(ps) > 1:
                print("  %-5s n=%d  min %.3f  max %.3f  range %.3f  "
                      "mean %.3f" % (label, len(ps), min(ps), max(ps),
                                     max(ps) - min(ps), sum(ps) / len(ps)))

    # the held-out instrument, pooled across seeds
    cp = [read_probe(os.path.join(d, "probe_CP7_final.txt")) for d in seeds]
    cp = [c for c in cp if c]
    if cp:
        k, n = sum(a for a, _ in cp), sum(b for _, b in cp)
        print()
        print("=== vs CP7 (held out, never trained against), %d seed(s), "
              "%d games" % (len(cp), n))
        print("  pooled %s" % fmt(k, n))
        print("  per-seed: %s"
              % ", ".join("%.2f" % (a / b) for a, b in cp if b))
        print("  reference: PHASE12-XMAGE-AI.md has ck_6144 at .28 and "
              "p10_final at .22, 50 games each (+-.13)")


if __name__ == "__main__":
    main()
