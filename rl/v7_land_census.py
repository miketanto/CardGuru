#!/usr/bin/env python3
"""Land census of a v7 checkpoint on real consults (7c): on every consult that offers
a LAND candidate, P(any LAND) and whether the argmax is a LAND, grouped by the
number of lands the agent controls (WIRE 2c player token idx 13, x10). Answers
"is the third land a rank problem or a probability problem".
--type SPELL (Phase 8, Dimir): the same census over consults that offer a SPELL
candidate - P(any SPELL) and argmax-SPELL by lands in play = P(cast) by lands. Lines
are then tagged SPELLCENSUS with argmax_spell / p_spell_mean; LAND output is unchanged.
    python3 rl/v7_land_census.py --ckpt CK [--ckpt CK2] [--logit-bound 5] [--device cpu] REC.jsonl ...
Prints one LANDCENSUS line per checkpoint per lands-in-play bucket:
  LANDCENSUS|ckpt=..|lands=N|consults=n|argmax_land=k|p_land_mean=..|p_pass_mean=..|other_types=..
plus a pooled line for lands>=3.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import torch                      # noqa: E402
import v7_obs as V                # noqa: E402
import v7_policy as P             # noqa: E402

C_LAND = 1
TYPE_IDX = {"PASS": 0, "LAND": 1, "SPELL": 2, "ACTIVATE": 3, "TARGET": 4, "ATTACK": 5, "BLOCK": 6, "OTHER": 7}
TYPES = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]


def load(paths, limit, ctype=C_LAND):
    hello, msgs = None, []
    for p in paths:
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            if m.get("t") == "hello":
                hello = hello or m
            elif m.get("t") == "consult" and "v7_ent" in m and ctype in m["v7_cand_type"]:
                msgs.append(m)
    return hello, msgs[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--limit", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--logit-bound", type=float, default=None)
    ap.add_argument("--type", default="LAND", choices=sorted(TYPE_IDX), help="candidate type censused (default LAND)")
    args = ap.parse_args()
    CT = TYPE_IDX[args.type]; tag = args.type + "CENSUS"; low = args.type.lower()
    hello, msgs = load(args.recordings, args.limit, CT)
    ids = V.CardIds()
    obs = [V.parse_consult(m, ids, hello) for m in msgs]
    types = [m["v7_cand_type"] for m in msgs]
    lands = [int(round(m["v7_players"][0][13] * 10)) for m in msgs]
    print(f"{tag}|consults_with_{low}={len(msgs)}|files={len(args.recordings)}")
    for ck in args.ckpt:
        net = P.V7Policy.load(ck, device=args.device).eval()
        if args.logit_bound is not None:
            net.heads.logit_bound = args.logit_bound
        rows = collections.defaultdict(lambda: {"n": 0, "am": 0, "pl": 0.0, "pp": 0.0, "oth": collections.Counter()})
        for s in range(0, len(obs), args.batch):
            b = V.collate(obs[s:s + args.batch])
            b = {k: (v.to(args.device) if torch.is_tensor(v) else v) for k, v in b.items()}
            with torch.no_grad():
                lg, _, _, _ = net(b, with_value=False)
            lg = lg.float().cpu()
            for i in range(lg.shape[0]):
                t = types[s + i]; row = lg[i][:len(t)]
                pr = torch.softmax(row, 0)
                r = rows[lands[s + i]]
                r["n"] += 1
                r["am"] += int(t[int(row.argmax())] == CT)
                r["pl"] += float(pr[[k for k, ty in enumerate(t) if ty == CT]].sum())
                r["pp"] += float(pr[[k for k, ty in enumerate(t) if ty == 0]].sum()) if 0 in t else 0.0
                r["oth"].update(TYPES[ty] for ty in set(t) if ty not in (0, CT))
        name = os.path.basename(os.path.dirname(ck)) + "/" + os.path.basename(ck)
        pooled = {"n": 0, "am": 0, "pl": 0.0, "pp": 0.0}
        for L in sorted(rows):
            r = rows[L]
            print(f"{tag}|ckpt={name}|lands={L}|consults={r['n']}|argmax_{low}={r['am']}"
                  f"|p_{low}_mean={r['pl'] / r['n']:.3f}|p_pass_mean={r['pp'] / r['n']:.3f}"
                  f"|other_types={dict(r['oth'])}")
            if L >= 3:
                for k in pooled:
                    pooled[k] += r[k]
        if pooled["n"]:
            print(f"{tag}|ckpt={name}|lands>=3|consults={pooled['n']}|argmax_{low}={pooled['am']}"
                  f"|argmax_{low}_frac={pooled['am'] / pooled['n']:.3f}|p_{low}_mean={pooled['pl'] / pooled['n']:.3f}")


if __name__ == "__main__":
    main()
