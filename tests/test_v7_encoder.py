"""Phase 4c gates (v7 plan §2): permutation invariance, masking, zero-edge arm
equals plain attention exactly, faithfulness probe after L4."""
import glob
import json
import os
import sys

import numpy as np
import pytest

torch = pytest.importorskip("torch")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rl"))
sys.path.insert(0, os.path.join(HERE, "..", "rl", "probes"))
import v7_obs as V          # noqa: E402
import v7_net as N          # noqa: E402
import v7_encoder as E      # noqa: E402

FIX = os.path.join(HERE, "..", "rl", "fixtures", "v7")
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(FIX, "valid_block.jsonl")), reason="fixtures not generated")


def _obs(paths, ids, n_per=6):
    out = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            msgs = [json.loads(l) for l in f if l.strip()]
        hello = V.check_hello_v7(msgs[0], "card_emb_v8")
        out += [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"][:n_per]
    return out


def _wake(enc, gen):
    """Un-zero the zero-initialised output layers so attention and FFN paths are exercised."""
    for blk in enc.blocks:
        for lin in (blk.att.out, blk.ffn[-1]):
            with torch.no_grad():
                lin.weight.copy_(torch.randn(lin.weight.shape, generator=gen, dtype=lin.weight.dtype) * 0.05)
        with torch.no_grad():
            blk.att.bias_rows.copy_(torch.randn(blk.att.bias_rows.shape, generator=gen, dtype=blk.att.bias_rows.dtype))
    return enc


@pytest.fixture(scope="module")
def setup():
    torch.manual_seed(0)
    ids = V.CardIds()
    obs = _obs(sorted(glob.glob(os.path.join(FIX, "valid_*.jsonl"))), ids)
    b = V.collate(obs)
    build = N.TokenBuilders(N.CardTable(random=True)).double().eval()
    b64 = {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}
    with torch.no_grad():
        toks = build(b64)
    return obs, b64, toks


def test_zero_edge_arm_equals_plain_attention_exactly(setup):
    obs, b, toks = setup
    gen = torch.Generator().manual_seed(1)
    enc = _wake(E.StateGraphEncoder(layers=2).double().eval(), gen)
    t0 = dict(toks)
    t0["edges"] = torch.zeros_like(toks["edges"]); t0["refers"] = torch.zeros_like(toks["refers"])
    t0["opp_act_refers"] = torch.zeros_like(toks["opp_act_refers"])
    with torch.no_grad():
        a = enc(t0)["seq"]
        enc.use_edges = False
        p = enc(t0)["seq"]
        enc.use_edges = True
        w = enc(toks)["seq"]
    assert torch.equal(a, p)                                   # bit-identical: the no-edge row is a fixed zero
    assert (w - a).abs().max().item() > 1e-6                   # and the edges do something when present


def test_permutation_equivariance(setup):
    obs, b, toks = setup
    gen = torch.Generator().manual_seed(2)
    enc = _wake(E.StateGraphEncoder(layers=2).double().eval(), gen)
    with torch.no_grad():
        ref = enc(toks)
    B, Nn = toks["ent"].shape[:2]
    K = toks["cand"].shape[1]
    tp = dict(toks)
    for key in ("ent", "cand", "ent_mask", "cand_mask", "edges", "refers", "opp_act_refers"):
        tp[key] = toks[key].clone()
    perms_e, perms_c = [], []
    for i in range(B):
        n = int(toks["ent_mask"][i].sum()); k = int(toks["cand_mask"][i].sum())
        pe = torch.cat([torch.randperm(n, generator=gen), torch.arange(n, Nn)])
        pc = torch.cat([torch.randperm(k, generator=gen), torch.arange(k, K)])
        perms_e.append(pe); perms_c.append(pc)
        tp["ent"][i] = toks["ent"][i][pe]; tp["ent_mask"][i] = toks["ent_mask"][i][pe]
        tp["cand"][i] = toks["cand"][i][pc]; tp["cand_mask"][i] = toks["cand_mask"][i][pc]
        full = torch.cat([torch.arange(3), 3 + pe])                        # wire token space: 0..2 fixed
        tp["edges"][i] = toks["edges"][i][full][:, full]
        tp["refers"][i] = toks["refers"][i][pc][:, full]
        tp["opp_act_refers"][i] = toks["opp_act_refers"][i][:, full]
    with torch.no_grad():
        out = enc(tp)
    for i in range(B):
        assert (out["ent"][i] - ref["ent"][i][perms_e[i]]).abs().max().item() <= 1e-6
        assert (out["cand"][i] - ref["cand"][i][perms_c[i]]).abs().max().item() <= 1e-6
        assert (out["game"][i] - ref["game"][i]).abs().max().item() <= 1e-6


def test_padding_does_not_change_real_tokens(setup):
    obs, b, toks = setup
    gen = torch.Generator().manual_seed(3)
    enc = _wake(E.StateGraphEncoder(layers=2).double().eval(), gen)
    with torch.no_grad():
        ref = enc(toks)
    pad = 5
    B, Nn, d = toks["ent"].shape
    tp = dict(toks)
    tp["ent"] = torch.cat([toks["ent"], torch.zeros(B, pad, d, dtype=toks["ent"].dtype)], 1)
    tp["ent_mask"] = torch.cat([toks["ent_mask"], torch.zeros(B, pad, dtype=torch.bool)], 1)
    T = toks["edges"].shape[1]
    edges = torch.zeros(B, T + pad, T + pad, dtype=torch.long); edges[:, :T, :T] = toks["edges"]; tp["edges"] = edges
    ref_ = torch.zeros(B, toks["refers"].shape[1], T + pad, dtype=toks["refers"].dtype); ref_[:, :, :T] = toks["refers"]; tp["refers"] = ref_
    ar = torch.zeros(B, toks["opp_act_refers"].shape[1], T + pad, dtype=toks["opp_act_refers"].dtype); ar[:, :, :T] = toks["opp_act_refers"]; tp["opp_act_refers"] = ar
    with torch.no_grad():
        out = enc(tp)
    assert (out["ent"][:, :Nn] - ref["ent"]).abs().max().item() <= 1e-6
    assert (out["cand"] - ref["cand"]).abs().max().item() <= 1e-6
    assert (out["ent"][:, Nn:] == 0).all()


def test_faithfulness_after_L4_at_init():
    """Same data volume as the 4b probe (140 consults); the untrained encoder is the
    identity by construction, so this must reproduce the 4b numbers."""
    import faithfulness as Fp
    torch.manual_seed(0)
    ids = V.CardIds()
    obs = _obs(sorted(glob.glob(os.path.join(FIX, "valid_*.jsonl"))), ids, n_per=20)
    b = V.collate(obs)
    build = N.TokenBuilders(N.CardTable(random=True)).eval()
    enc = E.StateGraphEncoder().eval()                         # untrained: identity by construction
    with torch.no_grad():
        toks = build(b)
        out = enc(toks, ent_raw=b["ent"])
        assert torch.allclose(out["ent"], toks["ent"])          # identity at init, as documented
    X, Y, G = [], [], []
    for i, o in enumerate(obs):
        n = o.ent.shape[0]
        X.append(out["ent"][i, :n].numpy()); f = o.ent.numpy()
        Y.append(np.stack([f[:, :7].argmax(1), f[:, 7], f[:, 22], f[:, 10], f[:, 17]], 1)); G.append(np.full(n, i))
    res = Fp.probe(np.concatenate(X), np.concatenate(Y), np.concatenate(G),
                   ["cat", "binary", "binary", "real", "real"], thresholds={3: 0.9, 4: 0.9})
    print(Fp.table(res, ["zone", "mine", "tapped", "power", "mv"]))
    assert all(r["pass"] for r in res.values()), res
