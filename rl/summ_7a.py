#!/usr/bin/env python3
"""Summarise 7a arm artifacts (rl/artifacts/v7/7a/<arm>/) into the §7a table shape and
apply the pre-registered "learning" definition (V7-VALIDATION §7a):
  training win rate over the last 4 batches (128 games) above 5 % with a Wilson 95 %
  interval clear of it; census argmax-PASS fraction in [5 %, 90 %] with mean top gap
  > 0.5 nats; attacks declared > 0 in the deterministic battery.
    python3 rl/summ_7a.py A0 A1 A2 B1 ...
"""
import math
import os
import re
import sys

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "v7", "7a")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, c - h, c + h)


def kv(line):
    return dict(re.findall(r"(\w[\w()]*)=([^\s|]+)", line))


def arm(name):
    d = os.path.join(ART, name)
    tr = [kv(l) for l in open(os.path.join(d, "train_lines.txt")) if l.startswith("TRAIN|")]
    if not tr:
        return f"| {name} | (no TRAIN lines) |"
    f, l = tr[0], tr[-1]
    eps = [int(t["episodes"]) - (int(tr[i - 1]["episodes"]) if i else 0) for i, t in enumerate(tr)]
    wins = [round(float(t["batch_win_rate"]) * e) for t, e in zip(tr, eps)]
    w4, n4 = sum(wins[-4:]), sum(eps[-4:])
    p, lo, hi = wilson(w4, n4)
    cen = {}
    for line in open(os.path.join(d, "census.txt")):
        cen.update(kv(line))
    ap = cen.get("argmax_pass_when_other_exists", "?/?")
    a, b = (int(x) for x in ap.split("/")) if "/" in ap else (0, 1)
    gap = float(cen.get("mean_top_gap", "nan"))
    ent = float(cen.get("mean_entropy_nats", "nan"))
    r0 = [l for l in open(os.path.join(d, "lane.log"), errors="replace") if l.startswith("R0|") and "trained=256" in l]
    atk = kv(r0[-1]).get("attacks", "?") if r0 else "?"
    d0 = re.search(r"D0=([0-9.]+)", r0[-1]).group(1) if r0 else "?"
    learn = []
    learn.append("wins" if lo > 0.05 else "no-wins")
    learn.append("census" if 0.05 <= a / b <= 0.90 and gap > 0.5 else "no-census")
    learn.append("attacks" if atk not in ("?",) and int(atk.split("/")[0]) > 0 else "no-attacks")
    return (f"| {name} | {float(f['entropy']):.2f} → {float(l['entropy']):.2f} "
            f"| {float(f['max_logit']):.0f} → {float(l['max_logit']):.0f} "
            f"| {float(f['grad_norm']):.2f} → {float(l['grad_norm']):.2f} "
            f"| {l['chosen_types']} | {sum(wins)} | last 4: {w4}/{n4} = {p:.3f} [{lo:.3f}, {hi:.3f}] "
            f"| gap {gap:.3f}, PASS {ap} ({a / b:.2f}), ent {ent:.2f} | attacks {atk}, D0 {d0} "
            f"| {' '.join(learn)} |")


if __name__ == "__main__":
    print("| arm | entropy 1→last | max|logit| | grad norm | chosen types last (PASS/LAND/SPELL/ACT/TGT/ATK/BLK/OTH) "
          "| wins/256 | last-4-batch wins (Wilson) | census ck_256 | battery | learning? |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for a in sys.argv[1:]:
        print(arm(a))
