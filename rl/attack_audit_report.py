"""Read one attack-audit probe file and report it honestly.

Wilson intervals, never Wald: rung0_lane.sh's inline band collapses to
+-0.000 at p=0 and p=1, and an attack rate of 0/N is exactly the shape
this instrument was built to catch. rung0_report.py already carries the
same wilson(); this file is the attack-side equivalent for a single probe
rather than a pooled learning curve.

WHAT EACH ROW CANNOT SUPPORT is printed with the row, not left to the
reader, because the reference here is myopic in a known direction.

Run: python3 rl/attack_audit_report.py <probe.txt> [--label ...]
"""
import argparse
import math
import re
import sys


def wilson(k, n, z=1.96):
    """95% score interval. Finite at k=0 and k=n, unlike Wald."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def rate(label, k, n, note=""):
    p, lo, hi = wilson(k, n)
    return "  %-26s %5d/%-5d  %.3f [%.3f,%.3f]%s" % (
        label, k, n, p, lo, hi, ("   " + note) if note else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    text = open(args.path).read()

    def f(key, default=0.0):
        m = re.search(r"\b%s=([0-9.]+)" % re.escape(key), text)
        return float(m.group(1)) if m else default

    eps = int(f("episodes"))
    combats = int(f("attackCombats"))
    choice = int(f("attackCombatsChoice"))
    opt = int(f("attackOptimal"))
    optc = int(f("attackOptimalChoice"))
    optca = int(f("attackOptimalCA"))
    declared = int(f("attacksDeclared"))
    opps = int(f("attackOpportunities"))

    print("=== attack audit — %s" % (args.label or args.path))
    print("  %d episodes, win_rate %.3f, %.1f turns/ep"
          % (eps, f("win_rate"), f("turns_per_ep")))
    if combats == 0:
        print("  no attack combats recorded — was -Drl.attackAudit set?")
        return
    print()
    print(rate("attack rate", declared, opps,
               "creatures sent / could have attacked"))
    print(rate("attack-optimality", opt, combats,
               "UPPER BOUND: includes no-choice combats"))
    print(rate("  ...where a choice existed", optc, choice,
               "the honest one"))
    print(rate("attack-optimality (CA)", optca, combats,
               "reference charges for the crack-back"))
    print()
    print("  score gap (myopic)         %d over %d combats" %
          (int(f("attackScoreGap")), combats))
    print("  score gap (CA)             %d" % int(f("attackScoreGapCA")))
    print("  missed lethal              %d   (own category, never a gap)"
          % int(f("attackLethalMissed")))
    print("  errors UNDER / OVER        %d / %d   (sent fewer / more than ref)"
          % (int(f("attackUnder")), int(f("attackOver"))))
    print("  truncated subsets/replies  %d / %d"
          % (int(f("attackTruncated")), int(f("attackReplyTruncated"))))
    print("  combats with no choice     %d   (MATCH there is the position's)"
          % (combats - choice))
    print()
    ms = f("attackSearchMs")
    ams = f("attackAuditMs")
    print("  cost: policy search %.0f ms total, %.2f ms/combat; "
          "audit %.0f ms (instrument, not play)"
          % (ms, ms / max(1, combats), ams))
    print("  nodes: %.0fk resolve() calls, %.0f per combat"
          % (f("attackSearchKNodes"), f("attackSearchKNodes") * 1000
             / max(1, combats)))
    print()
    print("  READ WITH: the reference is one combat deep and prices at zero")
    print("  the fact that an attacker cannot block next turn, so it")
    print("  over-credits attacking. A rise in attack-optimality alongside")
    print("  a rise in attack rate is partly tautological; the CA row and")
    print("  the UNDER/OVER split are what separate them.")


if __name__ == "__main__":
    sys.exit(main())
