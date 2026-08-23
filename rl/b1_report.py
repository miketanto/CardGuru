"""Read a rung-0 arm's probe files and print the B1 timing A/B rows.

    python3 rl/b1_report.py /tmp/rl_b1fast /tmp/rl_b1narrow

Pools D0 and TWIN. `rung0_lane.sh BASE BASE` puts the same deck in both
slots, so TWIN is a SECOND SAMPLE OF D0 and not a second matchup -
DIMIR-V6-2K-RESULT.md §0 - and pooling to n=200 is the only honest use
of it. They are never printed as agreement.

Wilson, not Wald: Wald reports 0.000 half-width at p=0, which made every
untrained row in the old lane logs claim certainty about 0/100.

THE COUNTERS ARE GATED. EpisodeRunner emits the instant block only
`if (instantCasts > 0)` and the whole tgt* block only
`if (targetCreatureChoices > 0)`, so on a policy that never casts its
removal the keys are ABSENT rather than zero. Absent is reported as 0
with a marker, because "no key" and "the instrument is broken" look the
same to a grep and are not the same thing.
"""
import math
import os
import re
import sys


def field(path, key):
    """key=value out of a probe file; None if the key is absent."""
    try:
        txt = open(path).read()
    except OSError:
        return None
    m = re.search(r"\b%s=([0-9.]+)" % re.escape(key), txt)
    return m.group(1) if m else None


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def ckpts(out):
    seen = set()
    for f in os.listdir(out):
        m = re.match(r"probe_D0_(\d+)\.txt$", f)
        if m:
            seen.add(int(m.group(1)))
    return sorted(seen)


def arm(out):
    name = os.path.basename(out)
    print("\n=== %s ===" % name)
    print("%-7s %-22s %-22s %-9s %-9s %s"
          % ("trained", "D0+TWIN pooled n=200", "D1 n=100",
             "instCast", "tgtChoice", "under/over"))
    for tr in ckpts(out):
        d0 = field("%s/probe_D0_%d.txt" % (out, tr), "win_rate")
        tw = field("%s/probe_TWIN_%d.txt" % (out, tr), "win_rate")
        d1 = field("%s/probe_D1_%d.txt" % (out, tr), "win_rate")
        if d0 is None:
            continue
        k = round(float(d0) * 100) + (round(float(tw) * 100) if tw else 0)
        n = 100 + (100 if tw else 0)
        p, lo, hi = wilson(k, n)
        if d1 is not None:
            p1, l1, h1 = wilson(round(float(d1) * 100), 100)
            d1s = "%.3f [%.3f,%.3f]" % (p1, l1, h1)
        else:
            d1s = "-"

        # summed over the three probes, so the census has the same
        # denominator as the pooled win rate
        ic = tc = 0
        miss_ic = miss_tc = True
        for lbl in ("D0", "D1", "TWIN"):
            f = "%s/probe_%s_%d.txt" % (out, lbl, tr)
            v = field(f, "instCasts")
            if v is not None:
                ic += int(float(v))
                miss_ic = False
            v = field(f, "tgtChoices")
            if v is not None:
                tc += int(float(v))
                miss_tc = False
        u = field("%s/probe_D0_%d.txt" % (out, tr), "attackUnder") or "0"
        o = field("%s/probe_D0_%d.txt" % (out, tr), "attackOver") or "0"

        print("%-7d %-22s %-22s %-9s %-9s %s/%s"
              % (tr, "%.3f [%.3f,%.3f]" % (p, lo, hi), d1s,
                 "%d%s" % (ic, "*" if miss_ic else ""),
                 "%d%s" % (tc, "*" if miss_tc else ""),
                 int(float(u)), int(float(o))))

    # the target-by-power census, where there is one
    for tr in ckpts(out):
        f = "%s/probe_D0_%d.txt" % (out, tr)
        if field(f, "tgtChoices") is None:
            continue
        chose = [int(float(field(f, "tgtChose_p%d" % p) or 0)) for p in range(7)]
        legal = [int(float(field(f, "tgtLegal_p%d" % p) or 0)) for p in range(7)]
        print("  tgt-by-power @%d  chose %s" % (tr, chose))
        print("  %-16s legal %s" % ("", legal))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for out in sys.argv[1:]:
        if os.path.isdir(out):
            arm(out)
        else:
            print("missing: %s" % out)
    print("\n* = key ABSENT from every probe (EpisodeRunner gates the "
          "block on >0), i.e. the count is genuinely zero")


if __name__ == "__main__":
    main()
