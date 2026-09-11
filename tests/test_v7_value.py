"""Phase 4e gate (v7 plan §2): the leak gate, levels 1-3 (rl/probes/leak.py),
on the v7 policy path vs the value trunk for the privileged channel
(`oe` rows and the true opponent hand)."""
import json
import os
import random
import sys

import pytest

torch = pytest.importorskip("torch")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rl"))
sys.path.insert(0, os.path.join(HERE, "..", "rl", "probes"))
import v7_obs as V          # noqa: E402
import v7_net as N          # noqa: E402
import v7_encoder as E      # noqa: E402
import v7_heads as H        # noqa: E402
import v7_value as VT       # noqa: E402
import wire_fixtures as F   # noqa: E402
import leak as Lk           # noqa: E402

HIDDEN = ["oe", "v7_oe_hand"]


def _msgs(n=12, seed=21):
    g = random.Random(seed)
    stream = F.valid_stream("spell", seed=seed, n=n, with_opp=True)
    out = []
    for m in stream:
        if m.get("t") != "consult":
            continue
        # privileged content: v6 oracle rows (M x 48) and the true opponent hand (names)
        m["oe"] = [[g.random() for _ in range(VT.OE_DIM)] for _ in range(g.randint(1, 5))]
        m["v7_oe_hand"] = [g.choice(F.NAMES) for _ in range(g.randint(0, 6))]
        out.append(m)
    return stream[0], out


def _swap(msg):
    g = random.Random(hash(json.dumps(msg["v7_game"])) & 0xFFFF)
    msg["oe"] = [[g.random() for _ in range(VT.OE_DIM)] for _ in range(len(msg["oe"]) + 1)]
    msg["v7_oe_hand"] = [g.choice(F.NAMES) for _ in range(len(msg["v7_oe_hand"]) + 1)]
    return msg


def _wake(enc, gen):
    for blk in enc.blocks:
        for lin in (blk.att.out, blk.ffn[-1]):
            with torch.no_grad():
                lin.weight.copy_(torch.randn(lin.weight.shape, generator=gen, dtype=lin.weight.dtype) * 0.05)
    return enc


@pytest.fixture(scope="module")
def nets():
    torch.manual_seed(0)
    gen = torch.Generator().manual_seed(5)
    table = N.CardTable(random=True).double()
    build = N.TokenBuilders(table).double().eval()
    enc = _wake(E.StateGraphEncoder(layers=2).double().eval(), gen)
    heads = H.V7Heads().double().eval()
    critic = VT.ValueTrunk(table, layers=2).double().eval()
    _wake(critic.enc, gen)
    with torch.no_grad():                                          # wake the value head's privileged inputs
        critic.oe_mlp.body[-1].weight.copy_(torch.randn(critic.oe_mlp.body[-1].weight.shape, generator=gen, dtype=torch.float64) * 0.1)
        critic.true_hand_mlp.body[-1].weight.copy_(torch.randn(critic.true_hand_mlp.body[-1].weight.shape, generator=gen, dtype=torch.float64) * 0.1)
    ids = V.CardIds()
    return ids, build, enc, heads, critic


def _batch(msg, hello, ids):
    o = V.parse_consult(msg, ids, hello)
    b = V.collate([o])
    return o, {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}


def test_leak_gate_levels_1_to_3(nets):
    ids, build, enc, heads, critic = nets
    hello, msgs = _msgs()

    def parse(m):                                                   # level 1: what the policy path receives
        o = V.parse_consult(m, ids, hello)
        b = V.collate([o])
        return {k: v.tolist() for k, v in b.items()}                # V7Obs tensors only; o.v6 (oe) is not among them

    def logits(m):                                                  # level 2
        o, b = _batch(m, hello, ids)
        with torch.no_grad():
            lg, _, _ = heads(enc(build(b)))
        return lg[0][torch.isfinite(lg[0])].tolist()

    def critic_value(m):                                            # level 3
        o, b = _batch(m, hello, ids)
        oe = torch.tensor(m["oe"], dtype=torch.float64).unsqueeze(0)
        oe_mask = torch.ones(1, oe.shape[1], dtype=torch.bool)
        th = torch.tensor([[ids.resolve(n) for n in m["v7_oe_hand"]]], dtype=torch.long) if m["v7_oe_hand"] else None
        with torch.no_grad():
            return critic(b, (oe, oe_mask), th).item()

    report = Lk.LeakGate(HIDDEN, parse, logits, critic_value).run(msgs, _swap)
    print(report)
    assert report["levels"][0]["pass"], report["levels"][0]
    assert report["levels"][1]["pass"], report["levels"][1]         # policy logits bit-identical under the swap
    assert report["levels"][2]["pass"], report["levels"][2]         # the critic moves under the swap
    assert report["pass"]


def test_planted_leak_is_refused(nets):
    """If the policy path read the privileged rows, the gate must say so."""
    ids, build, enc, heads, critic = nets
    hello, msgs = _msgs()

    def parse(m):
        return {"legal": V.parse_consult(m, ids, hello).ent.tolist()}

    def leaky_logits(m):
        o, b = _batch(m, hello, ids)
        with torch.no_grad():
            lg, _, _ = heads(enc(build(b)))
        lg = lg[0][torch.isfinite(lg[0])].clone()
        lg[0] += 0.1 * sum(r[0] for r in m["oe"])                  # the planted leak
        return lg.tolist()

    report = Lk.LeakGate(HIDDEN, parse, leaky_logits).run(msgs, _swap)
    assert not report["levels"][1]["pass"] and report["levels"][1]["max_abs_dlogit"] > 1e-3
