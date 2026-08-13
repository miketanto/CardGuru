"""Render rl/e3_ablate.sh output as the PHASE-E3 verification table.

Two readouts per condition:

  win rate    with a 95% CI on the DIFFERENCE from baseline (200g:
              ~+-.10, so only large effects are claimable);
  behaviour   how far the play itself moved - mean relative change over
              turns / actions / consults / blocks / flash casts.

The behavioural readout needs a NULL to be worth anything. Two are
available and both must be passed in: a baseline REPLICATE (same
config, fresh JVM) and `ablate_top` on a deck where the known-top dims
are provably always zero, which is an input-identical no-op. XMage is
not bit-deterministic across processes, so anything at or below the
null band is jitter, not evidence of a read.

A null file must come from the SAME deck as the results it calibrates
(the counters are per-deck); for a second deck, measure the band once
and pass it with --band.

Run: python3 rl/e3_ablate_report.py [results.txt] [--null null.txt ...]
                                    [--band 0.010]
"""
import math
import sys

BEHAV = ["turns", "actions", "consults", "blocks", "flash"]


def parse(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("E3ABL|"):
            continue
        d = {}
        for part in line.strip().split("|")[1:]:
            k, _, v = part.partition("=")
            d[k] = v
        rows.append(d)
    return rows


def baseline_of(rows):
    return next((r for r in rows if r["case"] == "baseline"
                 and r["opp"] == "heuristic"), None)


def behaviour_distance(row, base):
    """mean |relative change| over the behavioural counters"""
    ds = []
    for k in BEHAV:
        try:
            a, b = float(row[k]), float(base[k])
        except (KeyError, ValueError):
            continue
        if b:
            ds.append(abs(a - b) / b)
    return sum(ds) / len(ds) if ds else 0.0


def main():
    args = sys.argv[1:]
    fixed_band = None
    if "--band" in args:
        i = args.index("--band")
        fixed_band = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    nulls = []
    if "--null" in args:
        i = args.index("--null")
        nulls = args[i + 1:]
        args = args[:i]
    path = args[0] if args else "/tmp/rl_e3_ablate/results.txt"

    rows = parse(path)
    base = baseline_of(rows)
    if base is None:
        print("no baseline row")
        return 1
    bwr, n = float(base["win_rate"]), int(base["games"])

    null_d = []
    for p in nulls:
        for r in parse(p):
            if r["opp"] == "heuristic":
                null_d.append((p.split("/")[-2] + ":" + r["case"],
                               behaviour_distance(r, base)))
    band = max((d for _, d in null_d), default=0.0)
    if fixed_band is not None:
        band = fixed_band
        null_d.append(("--band (measured on another deck)", fixed_band))

    print(f"{'case':<16} {'opp':<10} {'win':>6} {'delta':>7} {'+-95%':>7} "
          f"{'behav':>7}  verdict")
    for r in rows:
        wr, m = float(r["win_rate"]), int(r["games"])
        d = wr - bwr
        se = math.sqrt(bwr * (1 - bwr) / n + wr * (1 - wr) / m)
        bd = behaviour_distance(r, base)
        if r is base:
            verdict = "reference"
        else:
            sig = abs(d) > 1.96 * se
            verdict = ("win rate DOWN" if sig and d < 0 else
                       "win rate UP" if sig else "win rate flat")
            verdict += ", behaviour " + ("moved" if bd > band else "within null")
        print(f"{r['case']:<16} {r['opp']:<10} {wr:>6.3f} {d:>+7.3f} "
              f"{1.96 * se:>7.3f} {bd:>7.3f}  {verdict}")

    if null_d:
        print("\nnull conditions (no input actually changed) - the jitter band:")
        for name, d in null_d:
            print(f"  {name:<40} behav {d:.3f}")
        print(f"  band = {band:.3f}")

    print("\nknown-top visibility (group 1 fires only when something "
          "filters the library):")
    for r in rows:
        ew, kt = int(r["encodeWindows"]), int(r["knownTop"])
        print(f"  {r['case']:<16} {r['opp']:<10} knownTop {kt:>6} / "
              f"{ew:>6} windows ({100.0 * kt / max(ew, 1):.2f}%)  "
              f"seenRecorded {r['seenRecorded']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
