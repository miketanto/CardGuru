#!/usr/bin/env python3
"""5d follow-up (pre-registered in the §5d results): what does a v7 checkpoint's
policy do on REAL consults?  Argmax candidate-type histogram, P(PASS), entropy,
top-1/top-2 logit gap - per checkpoint, over recorded 5b consults.

    python3 rl/v7_init_logits.py --ckpt /tmp/rl_5d_v7/init.pt --ckpt /tmp/rl_5d_v7/ck_256.pt REC.jsonl ...

Each consult is scored with a fresh LSTM state (no within-game memory), so the
numbers are the memoryless policy's; the lane's within-game state can only
move them, not create a PASS bias at init.  Types: PASS LAND SPELL ACTIVATE
TARGET ATTACK BLOCK OTHER (WIRE §2f).
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

TYPES = ["PASS", "LAND", "SPELL", "ACTIVATE", "TARGET", "ATTACK", "BLOCK", "OTHER"]


def load(paths, limit):
    hello, msgs = None, []
    for p in paths:
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            if m.get("t") == "hello":
                hello = hello or m
            elif m.get("t") == "consult" and "v7_ent" in m:
                msgs.append(m)
    return hello, msgs[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", action="append", required=True)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()
    hello, msgs = load(args.recordings, args.limit)
    ids = V.CardIds()
    obs = [V.parse_consult(m, ids, hello) for m in msgs]
    types = [m["v7_cand_type"] for m in msgs]
    print(f"INITLOGITS|consults={len(obs)}|files={len(args.recordings)}|device={args.device}")
    for ck in args.ckpt:
        net = P.V7Policy.load(ck, device=args.device).eval()
        ep = torch.load(ck, map_location="cpu", weights_only=False).get("episodes", 0)
        am = collections.Counter(); avail = collections.Counter(); pass_when_other = 0; n_other = 0
        ent_sum = gap_sum = ppass_sum = 0.0; n = 0
        for s in range(0, len(obs), args.batch):
            b = V.collate(obs[s:s + args.batch])
            b = {k: (v.to(args.device) if torch.is_tensor(v) else v) for k, v in b.items()}
            with torch.no_grad():
                lg, _, _, _ = net(b, with_value=False)
            lg = lg.float().cpu()
            for i in range(lg.shape[0]):
                t = types[s + i]; row = lg[i][:len(t)]
                pr = torch.softmax(row, 0)
                a = int(row.argmax()); am[TYPES[t[a]]] += 1
                for ty in set(t):
                    avail[TYPES[ty]] += 1
                ent_sum += float(-(pr * (pr + 1e-12).log()).sum()); n += 1
                srt = row.sort(descending=True).values
                gap_sum += float(srt[0] - srt[1]) if len(t) > 1 else 0.0
                ppass_sum += float(pr[[k for k, ty in enumerate(t) if ty == 0]].sum()) if 0 in t else 0.0
                if any(ty != 0 for ty in t):
                    n_other += 1; pass_when_other += int(t[a] == 0)
        print(f"INITLOGITS|ckpt={os.path.basename(ck)}|episodes={ep}|argmax_pass_when_other_exists={pass_when_other}/{n_other}"
              f"|mean_entropy_nats={ent_sum / n:.3f}|mean_top_gap={gap_sum / n:.3f}|mean_P(PASS)={ppass_sum / n:.3f}")
        print("INITLOGITS|argmax_type|" + "|".join(f"{k}={am[k]}/{avail[k]}" for k in TYPES if avail[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
