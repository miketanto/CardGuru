#!/usr/bin/env python3
"""Summarise C1-style lane runs (rl/artifacts/v7/7c1/s<seed>/ or a live /tmp/rl_7c1_s<seed>/)
against the pre-registered C1 readings (V7-VALIDATION "C1 pre-registration").

Usage:  python3 rl/summ_7c1.py rl/artifacts/v7/7c1/s0 rl/artifacts/v7/7c1/s1 ...
        python3 rl/summ_7c1.py /tmp/rl_7c1_s0            (live: reads lane.log + server*.log)

Per seed: battery levels per 512-point (Wilson), sampled last-4-batch rate per 512-point,
KL-stopped fraction, census per ck (argmax-PASS, gap, entropy, P(land) at >=3 lands),
attackBudgetHit per battery; then the four readings. Pooled battery over seeds whose
2048 row exists ("pool only finished seeds").
"""
import glob
import math
import os
import re
import sys


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {k / n:.3f} [{lo:.3f}, {hi:.3f}]" if n else "-"


def read_lines(d, names):
    dirs = d.split(":")
    out = []
    for dd in dirs:
      for n in names:
        for f in sorted(glob.glob(os.path.join(dd, n))):
            with open(f, encoding="utf-8", errors="replace") as fh:
                out.extend(fh.read().splitlines())
    return out


def kv(line):
    return dict(m for m in re.findall(r"([A-Za-z_()|]+)=([^ |]+)", line))


def seed_summary(d):
    lane = read_lines(d, ["lane.log", "battery.txt"])
    train = read_lines(d, ["train_lines.txt", "server_all.log", "server.log"])
    census = read_lines(d, ["census_all.txt", "census_*.txt"])
    probes = read_lines(d, ["probe_*.txt"])
    seen = set()
    rows = {}
    for ln in lane:
        m = re.match(r"R0\|(\S+?)\|s(\d+)\|trained=(\d+)\|", ln)
        if not m or ln in seen:
            continue
        seen.add(ln)
        eps = int(m.group(3))
        r = {}
        for opp in ("D0", "D1", "TWIN"):
            mm = re.search(opp + r"=([0-9.]+) \[([0-9.]+),([0-9.]+)\]", ln)
            if mm:
                r[opp] = (float(mm.group(1)), float(mm.group(2)), float(mm.group(3)))
        mm = re.search(r"turns=([0-9.]+)", ln)
        r["turns"] = mm.group(1) if mm else "-"
        rows[eps] = r
    games = 100
    # sampled curve: batches of 32, TRAIN lines in order (dedupe by update id)
    upd = {}
    kl_stop = kl_n = 0
    for ln in train:
        if ln.startswith("TRAIN|"):
            m = re.search(r"update=(\d+) episodes=(\d+) batch_eps=(\d+) .*batch_win_rate=([0-9.]+)", ln)
            if m:
                u = int(m.group(1))
                if u not in upd:
                    b = int(m.group(3))
                    upd[u] = (int(m.group(2)), round(float(m.group(4)) * b), b,
                              float(re.search(r"entropy=([0-9.]+)", ln).group(1)),
                              float(re.search(r"max_logit=([0-9.]+)", ln).group(1)))
        elif ln.startswith("KL|"):
            m = re.search(r"update=(\d+)", ln)
            key = ("kl", m.group(1) if m else ln)
            if key in seen:
                continue          # train_lines.txt duplicates server_all.log
            seen.add(key)
            kl_n += 1
            kl_stop += "stopped=1" in ln
    curve = {}
    for point in (512, 1024, 1536, 2048):
        us = [u for u in sorted(upd) if upd[u][0] <= point and upd[u][0] > point - 128]
        if len(us) == 4:
            k = sum(upd[u][1] for u in us)
            n = sum(upd[u][2] for u in us)
            curve[point] = (k, n, min(upd[u][3] for u in us), max(upd[u][4] for u in us))
    cens = {}
    for ln in census:
        m = re.match(r"(?:ck_(\d+) )?INITLOGITS\|ckpt=(?:.*?ck_)?(\d+)\.pt.*argmax_pass_when_other_exists=(\d+)/(\d+)\|mean_entropy_nats=([0-9.]+)\|mean_top_gap=([0-9.]+)", ln)
        if m:
            ck = int(m.group(1) or m.group(2))
            cens.setdefault(ck, {}).update(pass_k=int(m.group(3)), pass_n=int(m.group(4)),
                                           ent=float(m.group(5)), gap=float(m.group(6)))
        m = re.search(r"ck_(\d+)\.pt\|lands>=3\|consults=(\d+)\|argmax_land=(\d+)\|argmax_land_frac=([0-9.]+)\|p_land_mean=([0-9.]+)", ln)
        if m:
            cens.setdefault(int(m.group(1)), {}).update(pland=float(m.group(5)), aland=float(m.group(4)))
    hits = {}
    for f in sorted(sum((glob.glob(os.path.join(dd, "probe_*_*.txt")) for dd in d.split(":")), [])):
        m = re.match(r"probe_(\w+)_(\d+)\.txt", os.path.basename(f))
        with open(f, encoding="utf-8", errors="replace") as fh:
            mm = re.search(r"attackBudgetHit=(\d+)", fh.read())
        if m and mm:
            hits[(int(m.group(2)), m.group(1))] = int(mm.group(1))
    for ln in read_lines(d, ["budget_hits.txt"]):
        m = re.match(r"\s*(\d+) attackBudgetHit=(\d+)", ln)
        if m:
            hits[("count", int(m.group(2)))] = int(m.group(1))
    return dict(rows=rows, curve=curve, kl=(kl_stop, kl_n), cens=cens, hits=hits, games=games, upd=upd)


def main(dirs):
    pooled = {}
    for d in dirs:
        s = seed_summary(d)
        print(f"\n=== {d}  (updates seen: {len(s['upd'])}, KL stopped {s['kl'][0]}/{s['kl'][1]})")
        print("| point | D0 | D1 | TWIN | turns | sampled last-4 | entropy min | max|logit| | argmax-PASS | gap | ent | P(land)>=3 | budget hits D0/D1/TWIN |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for p in (0, 512, 1024, 1536, 2048):
            r = s["rows"].get(p, {})
            c = s["curve"].get(p)
            ce = s["cens"].get(p, {})
            def lv(o):
                return f"{r[o][0]:.2f} [{r[o][1]:.3f},{r[o][2]:.3f}]" if o in r else "-"
            print(f"| {p} | {lv('D0')} | {lv('D1')} | {lv('TWIN')} | {r.get('turns', '-')} | "
                  f"{fmt(c[0], c[1]) if c else '-'} | {c[2]:.2f} | {c[3]:.2f} | " if c else
                  f"| {p} | {lv('D0')} | {lv('D1')} | {lv('TWIN')} | {r.get('turns', '-')} | - | - | - | ", end="")
            print(f"{ce['pass_k']}/{ce['pass_n']} ({ce['pass_k'] / ce['pass_n']:.2f}) | {ce['gap']:.2f} | {ce['ent']:.2f} | " if 'pass_k' in ce else "- | - | - | ", end="")
            print(f"{ce['pland']:.2f} | " if 'pland' in ce else "- | ", end="")
            print("/".join(str(s['hits'].get((p, o), '-')) for o in ("D0", "D1", "TWIN")) + " |")
        # readings
        c = s["curve"]
        if 512 in c and 2048 in c:
            lo_last, _ = wilson(c[2048][0], c[2048][1])
            _, hi_first = wilson(c[512][0], c[512][1])
            rising = all(c[a][0] / c[a][1] <= c[b][0] / c[b][1] for a, b in ((512, 1024), (1024, 1536), (1536, 2048)))
            print(f"reading TRAINS (sampled): last clear of first = {lo_last > hi_first}; monotone = {rising}; "
                  f"D0 2048 vs 512: {s['rows'].get(2048, {}).get('D0', '-')} vs {s['rows'].get(512, {}).get('D0', '-')}")
        if 2048 in s["cens"] and "pland" in s["cens"][2048]:
            print(f"reading THIRD LAND: P(land)>=3 at ck_2048 = {s['cens'][2048]['pland']:.2f} (bar 0.5) -> {s['cens'][2048]['pland'] >= 0.5}")
        bad = [p for p, ce in s["cens"].items() if 'pass_k' in ce and not (0.05 <= ce['pass_k'] / ce['pass_n'] <= 0.9 and ce['gap'] > 0.5 and ce['ent'] > 0.3)]
        lg = [p for p, cc in c.items() if cc[3] >= 5.0]
        print(f"reading NOT COLLAPSED: census clauses fail at {bad or 'none'}; max|logit| at the bound at points {lg or 'none'}")
        print(f"reading KL BUDGET: stopped {s['kl'][0]}/{s['kl'][1]} = {(s['kl'][0] / s['kl'][1]) if s['kl'][1] else 0:.2f}" + ("  (0 -> flag inert)" if s['kl'][1] and not s['kl'][0] else ""))
        if 2048 in s["rows"]:
            for o in ("D0", "D1", "TWIN"):
                if o in s["rows"][2048]:
                    pooled.setdefault(o, [0, 0])
                    pooled[o][0] += round(s["rows"][2048][o][0] * s["games"])
                    pooled[o][1] += s["games"]
    if pooled:
        print("\n=== pooled at 2048 over finished seeds:", ", ".join(f"{o} {fmt(*pooled[o])}" for o in pooled))
    else:
        print("\n(no seed has a 2048 row yet: nothing pooled)")


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(glob.glob("rl/artifacts/v7/7c1/s*")))
