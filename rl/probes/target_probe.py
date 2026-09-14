#!/usr/bin/env python3
"""Phase 9 / P2 - removal targeting (rl/PHASE9-PROBES.md).

Every recorded TARGET consult with k >= 2 legal CREATURE targets (WIRE §2f
TARGET afterstate: is-creature at cand[11], power cand[12]*6, toughness
cand[13]*6, mine cand[14]).  For each subject the consult is rescored with
the memoryless path (rl/probes/cardswap.score) and the argmax over the
creature TARGET candidates is read; the recorded seat's own choice (the
{"a":k} reply, when present) is a further row.  Reported: P(picks a
largest-power target) against the per-consult chance level (#largest / k),
bootstrap 95 % CI over consults of the difference; P(picks an opponent's
creature) when both sides are offered; and the equal-P/T-different-text
subset (n) with P(picks the keyworded one).

  python3 rl/probes/target_probe.py --ckpt init=... --ckpt C1s0=... --ckpt DIM=... --out rl/artifacts/v7/9 REC.jsonl ...
"""
import argparse
import collections
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RL = os.path.dirname(HERE)
sys.path.insert(0, RL)
sys.path.insert(0, HERE)
import torch                      # noqa: E402
import v7_obs as V                # noqa: E402
import v7_policy as P             # noqa: E402
import cardswap as C              # noqa: E402


def load_with_choices(paths):
    """consult messages with the seat's chosen index attached as m['_a'] (or None)."""
    hello, msgs = None, []
    last = None
    for p in paths:
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            if m.get("t") == "hello":
                hello = hello or m
            elif m.get("t") == "consult" and "v7_ent" in m:
                m["_file"] = os.path.basename(p); m["_a"] = m.get("y"); msgs.append(m); last = m
            elif "a" in m and last is not None:
                if "rec_" in os.path.basename(p):          # a policy's own replies; the echo sets' {"a":k} are not a policy
                    last["_a"] = m["a"]
                last = None
    return hello, msgs


def creature_targets(m):
    ct, cd = m["v7_cand_type"], m["v7_cand"]
    return [k for k, t in enumerate(ct) if t == 4 and cd[k][11] > 0.5]


def boot_diff(vals, chance, reps=2000, seed=0):
    vals, chance = np.asarray(vals, float), np.asarray(chance, float)
    rng = np.random.default_rng(seed)
    d = []
    for _ in range(reps):
        i = rng.integers(0, len(vals), len(vals))
        d.append(vals[i].mean() - chance[i].mean())
    lo, hi = np.percentile(d, [2.5, 97.5])
    return float(vals.mean()), float(chance.mean()), float(lo), float(hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", default=[], help="name=path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    paths = [q for p in args.recordings for q in sorted(glob.glob(p))] or args.recordings
    F, O = C.load_corpus()
    ids = V.CardIds()
    hello, msgs = load_with_choices(paths)
    sel = [(m, creature_targets(m)) for m in msgs]
    sel = [(m, ks) for m, ks in sel if len(ks) >= 2]
    obs = [V.parse_consult(m, ids, hello) for m, ks in sel]
    lines = ["P2|consults_with_k>=2_creature_targets=%d|files=%d|by_file=%s" % (
        len(sel), len(paths), ",".join("%s:%d" % kv for kv in collections.Counter(m["_file"] for m, ks in sel).most_common()))]
    # per consult: powers, sides, names, equal-PT-different-text pairs
    info = []
    for m, ks in sel:
        cd = m["v7_cand"]
        pw = [round(cd[k][12] * 6) for k in ks]
        tg = [round(cd[k][13] * 6) for k in ks]
        mine = [cd[k][14] > 0.5 for k in ks]
        names = [m["v7_ent_name"][m["v7_cand_refers"][k][0] - 3] if m["v7_cand_refers"][k] else "?" for k in ks]
        mx = max(pw)
        largest = {k for k, p in zip(ks, pw) if p == mx}
        both_sides = any(mine) and not all(mine)
        # equal P/T, different text: the pair (a, b) with keyworded a vs non-keyworded b
        eq = None
        for i in range(len(ks)):
            for j in range(len(ks)):
                if i == j or (pw[i], tg[i]) != (pw[j], tg[j]) or names[i] == names[j]:
                    continue
                ki = C.kw_only(O.get(names[i], "")); kj = C.kw_only(O.get(names[j], ""))
                gi = F.get(names[i], {}).get("graph") or []; gj = F.get(names[j], {}).get("graph") or []
                kwi = any(C._graph_kw(gi, k) for k in C.KW_LOWER); kwj = any(C._graph_kw(gj, k) for k in C.KW_LOWER)
                if kwi and not kwj and O.get(names[i], "") != O.get(names[j], ""):
                    eq = (ks[i], ks[j]); break
            if eq:
                break
        info.append(dict(ks=ks, largest=largest, chance=len(largest) / len(ks), both=both_sides,
                         opp=[k for k, mn in zip(ks, mine) if not mn], eq=eq, names=names, pw=pw, tg=tg))
    lines.append("P2|equal_PT_different_text_subset|n=%d" % sum(1 for x in info if x["eq"]))

    def report(name, picks):
        hit = [float(p in x["largest"]) for p, x in zip(picks, info) if p is not None]
        ch = [x["chance"] for p, x in zip(picks, info) if p is not None]
        m, c, lo, hi = boot_diff(hit, ch)
        side = [float(p in x["opp"]) for p, x in zip(picks, info) if p is not None and x["both"]]
        eqh = [float(p == x["eq"][0]) for p, x in zip(picks, info) if p is not None and x["eq"] and p in x["eq"]]
        reading = "size-aware" if lo > 0 else ("size-averse" if hi < 0 else "not size-aware (interval covers 0)")
        lines.append("P2|%s|n=%d|P(largest)=%.3f|chance=%.3f|diff=%.3f [%.3f,%.3f]|%s|P(opp side | both offered)=%s (n=%d)|equal-PT: picks keyworded %s (n=%d)" % (
            name, len(hit), m, c, m - c, lo, hi, reading,
            "%.3f" % float(np.mean(side)) if side else "nan", len(side),
            "%.2f" % float(np.mean(eqh)) if eqh else "nan", len(eqh)))

    # the recorded seat's own choices
    own = [m["_a"] if (m["_a"] is not None and m["_a"] in ks) else None for m, ks in sel]
    if any(p is not None for p in own):
        report("recorded_seat", own)
    for spec in args.ckpt:
        name, path = spec.split("=", 1)
        net = P.V7Policy.load(path, device=args.device).eval()
        base = C.score(net, obs, args.device, bound=5.0)
        picks = []
        for (pb, ab, lb, rb), x in zip(base, info):
            ks = x["ks"]
            picks.append(max(ks, key=lambda k: float(lb[k])))
        report(name, picks)
        del net
    for ln in lines:
        print(ln)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "target_probe_summary.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
