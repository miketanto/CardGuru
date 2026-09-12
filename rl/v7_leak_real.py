#!/usr/bin/env python3
"""Gate 3d, server side: the leak gate (rl/probes/leak.py levels 1-3) on REAL
recorded consults from a -Drl.encoderV=7 -Drl.oracle=true driver.

    python3 rl/v7_leak_real.py RECORDING.jsonl [--layers 2] [--limit 200]

Hidden channel: "oe" (v6 critic rows) and "v7_oe_hand" (the true opponent
hand, WIRE §4).  Level 1: the policy-path parse (V7Obs tensors) is identical
with and without the hidden keys.  Level 2: the policy logits are
bit-identical when the hidden content is swapped for different hidden
content - on a net whose encoder has been woken (random output projections;
at init the encoder is an identity and every logit is equal, so a level-2
pass on an unwoken net would be vacuous).  Level 3: the critic's value moves
under the same swap, so the channel is live.

The tracker tokens (v7_opp_*) are NOT hidden keys: they are on the policy
path by design.  What this gate proves about them is that the policy path
contains nothing that changes with the true hand; that the tracker itself
does not read the true hand is the 3d consistency check
(rl/wire_check_3d.py: known ⊆ truth) plus construction.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "probes"))
import torch                       # noqa: E402
import v7_obs as V                 # noqa: E402
import v7_net as N                 # noqa: E402
import v7_encoder as E             # noqa: E402
import v7_heads as H               # noqa: E402
import v7_value as VT              # noqa: E402
import leak as Lk                  # noqa: E402

HIDDEN = ["oe", "v7_oe_hand"]


def wake(enc, gen):
    for blk in enc.blocks:
        for lin in (blk.att.out, blk.ffn[-1]):
            with torch.no_grad():
                lin.weight.copy_(torch.randn(lin.weight.shape, generator=gen, dtype=lin.weight.dtype) * 0.05)
    return enc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recording")
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    hello, msgs = None, []
    names = set()
    for raw in open(args.recording, "rb"):
        if not raw.strip():
            continue
        m = json.loads(raw)
        if m.get("t") == "hello":
            hello = m
        elif m.get("t") == "consult" and "v7_oe_hand" in m:
            msgs.append(m)
            names.update(m.get("v7_ent_name", []))
            names.update(m.get("v7_oe_hand", []))
    if hello is None or not msgs:
        print("LEAK3D|no oracle-labelled consults in", args.recording)
        return 2
    msgs = msgs[:args.limit]
    names = sorted(names)

    torch.manual_seed(0)
    gen = torch.Generator().manual_seed(5)
    table = N.CardTable(random=True).double()
    build = N.TokenBuilders(table).double().eval()
    enc = wake(E.StateGraphEncoder(layers=args.layers).double().eval(), gen)
    heads = H.V7Heads().double().eval()
    critic = VT.ValueTrunk(table, layers=args.layers).double().eval()
    wake(critic.enc, gen)
    with torch.no_grad():
        critic.oe_mlp.body[-1].weight.copy_(torch.randn(critic.oe_mlp.body[-1].weight.shape, generator=gen, dtype=torch.float64) * 0.1)
        critic.true_hand_mlp.body[-1].weight.copy_(torch.randn(critic.true_hand_mlp.body[-1].weight.shape, generator=gen, dtype=torch.float64) * 0.1)
    ids = V.CardIds()

    def batch(m):
        o = V.parse_consult(m, ids, hello)
        b = V.collate([o])
        return o, {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}

    def parse(m):
        o = V.parse_consult(m, ids, hello)
        b = V.collate([o])
        return {k: v.tolist() for k, v in b.items()}

    def logits(m):
        _, b = batch(m)
        with torch.no_grad():
            lg, _, _ = heads(enc(build(b)))
        return lg[0][torch.isfinite(lg[0])].tolist()

    def critic_value(m):
        _, b = batch(m)
        oe_rows = m.get("oe") or [[0.0] * VT.OE_DIM]
        oe = torch.tensor(oe_rows, dtype=torch.float64).unsqueeze(0)
        oe_mask = torch.ones(1, oe.shape[1], dtype=torch.bool)
        th = torch.tensor([[ids.resolve(n) for n in m["v7_oe_hand"]]], dtype=torch.long) if m["v7_oe_hand"] else None
        with torch.no_grad():
            return critic(b, (oe, oe_mask), th).item()

    def swap(m):
        g = random.Random(hash(json.dumps(m["v7_game"])) & 0xFFFF)
        n_oe = len(m.get("oe") or []) + 1
        m["oe"] = [[g.random() for _ in range(VT.OE_DIM)] for _ in range(n_oe)]
        m["v7_oe_hand"] = [g.choice(names) for _ in range(len(m["v7_oe_hand"]) + 1)]
        return m

    report = Lk.LeakGate(HIDDEN, parse, logits, critic_value).run(msgs, swap)
    for i, lvl in enumerate(report["levels"], 1):
        print(f"LEAK3D|level{i}|pass={lvl['pass']}|" + "|".join(f"{k}={v}" for k, v in lvl.items() if k != "pass"))
    print(f"LEAK3D|consults={len(msgs)}|pass={report['pass']}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
