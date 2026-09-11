"""Phase 4b gate (v7 plan §2): token-builder shape tests and the faithfulness
probe after L3 — every planted input field must be linearly recoverable
from the builder outputs (rl/probes/faithfulness.py), on fixtures."""
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
import wire_validate as W   # noqa: E402

FIX = os.path.join(HERE, "..", "rl", "fixtures", "v7")
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(FIX, "valid_spell.jsonl")), reason="fixtures not generated")


def _obs(paths, ids, n_per=20):
    out = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            msgs = [json.loads(l) for l in f if l.strip()]
        hello = V.check_hello_v7(msgs[0], "card_emb_v8")
        out += [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"][:n_per]
    return out


@pytest.fixture(scope="module")
def batch():
    ids = V.CardIds()
    obs = _obs(sorted(glob.glob(os.path.join(FIX, "valid_*.jsonl"))), ids)
    return obs, V.collate(obs)


def test_shapes_random_table(batch):
    obs, b = batch
    build = N.TokenBuilders(N.CardTable(random=True)).eval()
    with torch.no_grad():
        t = build(b)
    B, K = b["cand"].shape[:2]
    Nn = b["ent"].shape[1]
    assert t["game"].shape == (B, 1, N.D_TOK) and t["players"].shape == (B, 2, N.D_TOK)
    assert t["ent"].shape == (B, Nn, N.D_TOK) and t["cand"].shape == (B, K, N.D_TOK)
    seq, mask = build.all_tokens(t)
    assert seq.shape == (B, 3 + Nn, N.D_TOK) and mask.shape == (B, 3 + Nn)
    assert (t["ent"][~b["ent_mask"]] == 0).all() and (t["cand"][~b["cand_mask"]] == 0).all()
    assert torch.isfinite(seq).all()


def test_real_table_identity_adapter_starts_as_identity():
    tab = N.CardTable("card_emb_v8")
    ids = torch.tensor([0, 5, -1])
    c, unk = tab(ids)
    assert torch.allclose(c[0], tab.table[0]) and torch.allclose(c[1], tab.table[5])
    assert unk.squeeze(-1).tolist() == [0.0, 0.0, 1.0] and (c[2] == 0).all()


def test_faithfulness_after_L3(batch):
    """Linear readout on the entity tokens recovers planted fields (zone, mine,
    tapped, power, mv) and on candidate tokens the candidate type; grouped by
    consult."""
    import faithfulness as Fp
    obs, b = batch
    torch.manual_seed(0)
    build = N.TokenBuilders(N.CardTable(random=True)).eval()
    with torch.no_grad():
        t = build(b)
    X, Y, G = [], [], []
    for i, o in enumerate(obs):
        n = o.ent.shape[0]
        X.append(t["ent"][i, :n].numpy())
        f = o.ent.numpy()
        Y.append(np.stack([f[:, :7].argmax(1), f[:, 7], f[:, 22], f[:, 10], f[:, 17]], 1))
        G.append(np.full(n, i))
    res = Fp.probe(np.concatenate(X), np.concatenate(Y), np.concatenate(G),
                   ["cat", "binary", "binary", "real", "real"], thresholds={3: 0.9, 4: 0.9})
    print(Fp.table(res, ["zone", "mine", "tapped", "power", "mv"]))
    assert all(r["pass"] for r in res.values()), res
    Xc, Yc, Gc = [], [], []
    for i, o in enumerate(obs):
        k = o.cand.shape[0]
        Xc.append(t["cand"][i, :k].numpy()); Yc.append(o.cand_type.numpy()[:, None]); Gc.append(np.full(k, i))
    res_c = Fp.probe(np.concatenate(Xc), np.concatenate(Yc), np.concatenate(Gc), ["cat"])
    assert res_c[0]["pass"], res_c
