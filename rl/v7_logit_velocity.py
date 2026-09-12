#!/usr/bin/env python3
"""7a pre-registration diagnostic: how fast do the v7 policy's logits move per
Adam step, on real consults, under the loss the 5d run actually produced
(every game lost: advantage -1 on every sampled action)?

    python3 rl/v7_logit_velocity.py --ckpt /tmp/rl_5d_v7/init.pt REC.jsonl ... [--lrs 3e-5,1e-4,3e-4] [--steps 8]

Per lr, from the same init: `steps` on-policy steps, each = sample an action per
consult from the current policy on a fixed real batch, loss = mean log p(a)
(the policy-gradient loss with A = -1; the PPO ratio is 1 at the first epoch so
this is its first-epoch gradient), one Adam step over policy_parameters().
Reported per step: mean top-1 - top-2 logit gap, mean P(PASS), mean entropy,
max |logit|.  Pre-registered reading: if the gap grows by >= 1 nat per step at
3e-4 and by < 0.1 at 3e-5 the collapse mechanism is Adam step-size x parameter
count (lr-fixable, bounded by a lane arm at the lower lr); if the gap grows at
every lr at a rate proportional to lr but P(PASS) falls to ~0 within the same
number of steps at every lr, the PASS-row-constant structure is the driver and
lr only slows it.  What this cannot show: that a lower-lr lane learns anything.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import torch                      # noqa: E402
import v7_obs as V                # noqa: E402
import v7_policy as P             # noqa: E402


def load(paths, limit):
    hello, msgs = None, []
    for p in paths:
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            if m.get("t") == "hello":
                hello = hello or m
            elif m.get("t") == "consult" and "v7_ent" in m and len(m["v7_cand"]) > 1:
                msgs.append(m)
    return hello, msgs[:limit]


def stats(lg, types):
    gaps, ppass, ents, mx = [], [], [], 0.0
    for i in range(lg.shape[0]):
        row = lg[i][:len(types[i])]
        pr = torch.softmax(row, 0)
        s = row.sort(descending=True).values
        gaps.append(float(s[0] - s[1])); ents.append(float(-(pr * (pr + 1e-12).log()).sum()))
        ppass.append(float(pr[[k for k, t in enumerate(types[i]) if t == 0]].sum()))
        mx = max(mx, float(row.abs().max()))
    n = len(gaps)
    return sum(gaps) / n, sum(ppass) / n, sum(ents) / n, mx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recordings", nargs="+")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--lrs", default="3e-5,1e-4,3e-4")
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    hello, msgs = load(args.recordings, args.batch)
    ids = V.CardIds()
    obs = [V.parse_consult(m, ids, hello) for m in msgs]
    types = [m["v7_cand_type"] for m in msgs]
    b = V.collate(obs)
    b = {k: (v.to(args.device) if torch.is_tensor(v) else v) for k, v in b.items()}
    print(f"VELOCITY|consults={len(obs)}|device={args.device}|steps={args.steps}")
    for lr in [float(x) for x in args.lrs.split(",")]:
        torch.manual_seed(0)
        net = P.V7Policy.load(args.ckpt, device=args.device).train()
        opt = torch.optim.Adam(net.policy_parameters(), lr=lr)
        line = []
        for step in range(args.steps + 1):
            lg, _, _, _ = net(b, with_value=False)
            g, pp, en, mx = stats(lg.detach().float().cpu(), types)
            line.append(f"s{step}:gap={g:.2f},P(PASS)={pp:.2f},H={en:.2f},max|l|={mx:.1f}")
            if step == args.steps:
                break
            dist = torch.distributions.Categorical(logits=lg)
            a = dist.sample()
            loss = dist.log_prob(a).mean()               # A = -1 on every sampled action
            opt.zero_grad(); loss.backward()
            gn = torch.nn.utils.clip_grad_norm_(net.policy_parameters(), 1e9).item()
            opt.step()
            line[-1] += f",gradnorm={gn:.2f}"
        print(f"VELOCITY|lr={lr:g}|" + "|".join(line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
