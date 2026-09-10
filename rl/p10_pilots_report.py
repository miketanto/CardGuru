"""Phase 10 (4.4): turn the upper-bound pilot lanes' elo_curve.txt files
into the markdown tables PHASE10-PILOTS-2.md reports.

  python3 rl/p10_pilots_report.py skies redrush ramp

Reads /tmp/rl_p10_pilot_<name>/elo_curve.txt (override the root with
P10_ROOT) and prints, per pilot, the rating curve and the champion
match, with Wilson 95% intervals so the .07-at-100g caveat from
CHECKPOINT-PHASE10.md section 6 is carried in the numbers themselves.
"""
import math
import os
import sys

# p7c_pilot_calib.sh, 100g: D0(deck) vs D0(BenchDimir). dimir .58 is the
# same-deck seat baseline, i.e. what "no deck advantage" actually reads.
POWER = {"skies": 0.71, "redrush": 0.64, "ramp": 0.60, "dimir": 0.58}
SEAT = 0.58
ROOT = os.environ.get("P10_ROOT", "/tmp")


def wilson(wins, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def lg(x):
    x = min(max(x, 0.01), 0.99)
    return 400.0 * math.log10(x / (1 - x))


def parse(path):
    rows = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        kind, rest = line.split("|", 1)
        d = dict(kv.split("=", 1) for kv in rest.split("|") if "=" in kv)
        rows.append((kind, d))
    return rows


def main():
    names = sys.argv[1:] or ["skies", "redrush", "ramp"]
    champs = []
    for name in names:
        path = f"{ROOT}/rl_p10_pilot_{name}/elo_curve.txt"
        if not os.path.exists(path):
            print(f"<!-- no curve for {name} -->\n")
            continue
        power = POWER.get(name, SEAT)
        print(f"### {name} (deck power {power:.2f})\n")
        print("| trained | vs D0-BenchDimir | 95% CI | norm Elo | "
              "blocks/opps | stalls |")
        print("|---|---|---|---|---|---|")
        seen = set()
        for kind, d in parse(path):
            if kind != "P10ELO" or d["trained"] in seen:
                continue
            seen.add(d["trained"])
            wr = float(d["vs_D0_dimir"])
            lo, hi = wilson(round(wr * 100), 100)
            print(f"| {d['trained']} | {wr:.2f} | {lo:.2f}-{hi:.2f} | "
                  f"{d['norm_elo']} | {d.get('blocks', '0')}/"
                  f"{d.get('blockOpps', '0')} | {d.get('stalls', '0')} |")
        # deck-power reference row: what a D0-grade pilot of this deck scores
        print(f"\nD0-grade pilot of this deck scores {power:.2f} "
              f"(norm Elo {round(1000 + lg(power) - lg(power) + lg(SEAT))}"
              f" = 1000 by construction); the residual above {power:.2f} is "
              "pilot skill the 7c matrix could not supply.\n")
        for kind, d in parse(path):
            if kind == "P10CHAMP":
                champs.append((name, d))
    if champs:
        print("## 200g vs the project champion (ck_6144, BenchDimir)\n")
        print("| pilot | deck | win rate | 95% CI | wins | draws | stalls |")
        print("|---|---|---|---|---|---|---|")
        for name, d in champs:
            n = int(d["games"])
            w = int(float(d.get("wins", 0)))
            wr = float(d["vs_ck6144"])
            lo, hi = wilson(w, n)
            print(f"| {name} | {d['deck']} | {wr:.3f} | {lo:.2f}-{hi:.2f} | "
                  f"{w} | {d.get('draws', '0')} | {d.get('stalls', '0')} |")


if __name__ == "__main__":
    main()
