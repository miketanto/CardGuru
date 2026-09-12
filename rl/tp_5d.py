#!/usr/bin/env python3
"""5d: THROUGHPUT-LOCAL.md §2 quantities from one lane arm's output directory.

    python3 rl/tp_5d.py rl/artifacts/v7/5d/v6 rl/artifacts/v7/5d/v7

train.csv cols: 1 time, 2 updates, 3 episodes_seen, 4 stored consults (steps),
5 batch_win_rate, 6 value_ev, 7 critic_ev, 8 oracle_cover, 9 update_s.
eps/s = (eps_row8 - eps_row1) / (t_row8 - t_row1); update ms per stored consult
= sum(update_s rows 2-8) / sum(consults rows 2-8); play s = window - sum(update_s
rows 2-8); play consults/s = sum(consults rows 2-8) / play s.
"""
import os
import re
import sys


def arm(d):
    rows = [l.strip().split(",") for l in open(os.path.join(d, "train.csv")) if l.strip()]
    rows = [r for r in rows if len(r) >= 9]
    out = {"rows": len(rows)}
    if len(rows) >= 2:
        r1, rN = rows[0], rows[-1]
        t = float(rN[0]) - float(r1[0]); eps = int(rN[2]) - int(r1[2])
        ups = [float(r[8]) for r in rows[1:]]; cons = [int(r[3]) for r in rows[1:]]
        out.update(window_s=t, episodes=eps, eps_per_s=eps / t if t else None,
                   update_s_mean=sum(float(r[8]) for r in rows) / len(rows), update_s_max=max(float(r[8]) for r in rows),
                   consults_stored=sum(cons), update_ms_per_consult=1000 * sum(ups) / max(1, sum(cons)),
                   update_share=sum(ups) / t if t else None,
                   play_s=t - sum(ups), play_consults_per_s=sum(cons) / (t - sum(ups)) if t - sum(ups) > 0 else None,
                   consults_per_ep=sum(cons) / max(1, eps))
    mem = os.path.join(d, "mem.log")
    if os.path.exists(mem):
        pk = {"used": 0, "jvm": 0, "srv": 0, "gpu": 0}
        for l in open(mem):
            for k in pk:
                m = re.search(rf"{k}=(\d+)", l)
                if m:
                    pk[k] = max(pk[k], int(m.group(1)))
        out.update({f"peak_{k}_mb": v for k, v in pk.items()})
    log = os.path.join(d, "server_all.log")
    if os.path.exists(log):
        lock = [l for l in open(log, errors="replace") if l.startswith("RLLOCK|")]
        out["rllock_last"] = lock[-1].strip()[:200] if lock else None
        out["train_lines"] = sum(1 for l in open(log, errors="replace") if l.startswith("TRAIN|"))
    lane = os.path.join(d, "lane.log")
    if os.path.exists(lane):
        L = open(lane, errors="replace").read()
        out["r0_done"] = "R0_DONE" in L; out["r0_failed"] = "R0_FAILED" in L
        m = re.search(r"ck_eps=(\d+)", L.split("R0_DONE")[0][-2000:] if "R0_DONE" in L else L)
        out["ck_eps_last"] = m.group(1) if m else None
        m = re.search(r"turns=([\d.]+)", L)
        out["turns_probe0"] = m.group(1) if m else None
    dt = os.path.join(d, "driver_tail.txt")
    if os.path.exists(dt):
        out["driver_tail"] = [l.strip()[:220] for l in open(dt)]
    return out


def main():
    for d in sys.argv[1:]:
        print(f"=== {d}")
        for k, v in arm(d).items():
            print(f"  {k}: {v:.4g}" if isinstance(v, float) else f"  {k}: {v}")


if __name__ == "__main__":
    main()
