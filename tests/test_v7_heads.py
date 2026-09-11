"""Phase 4d gates (v7 plan §2): logits invariant to padding; candidate-count
probe from the game token; the LSTM carries a planted bit across consults."""
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
import v7_heads as H        # noqa: E402

FIX = os.path.join(HERE, "..", "rl", "fixtures", "v7")
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(FIX, "valid_block.jsonl")), reason="fixtures not generated")


def _obs(n_per):
    ids = V.CardIds()
    out = []
    for p in sorted(glob.glob(os.path.join(FIX, "valid_*.jsonl"))):
        with open(p, encoding="utf-8") as f:
            msgs = [json.loads(l) for l in f if l.strip()]
        hello = V.check_hello_v7(msgs[0], "card_emb_v8")
        out += [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"][:n_per]
    return out


def _gen_obs(n_per, seed=11):
    """More consults than the committed fixtures hold, generated in memory with
    the same generator (probes over 256-d vectors need hundreds of samples)."""
    import wire_fixtures as F
    ids = V.CardIds()
    out = []
    for i, d in enumerate(F.DECISIONS):
        msgs = F.valid_stream(d, seed=seed + i, n=n_per, with_opp=(i >= 4))
        hello = V.check_hello_v7(msgs[0], "card_emb_v8")
        out += [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"]
    return out


def _wake(enc, gen):
    for blk in enc.blocks:
        for lin in (blk.att.out, blk.ffn[-1]):
            with torch.no_grad():
                lin.weight.copy_(torch.randn(lin.weight.shape, generator=gen, dtype=lin.weight.dtype) * 0.05)
    return enc


@pytest.fixture(scope="module")
def stack():
    torch.manual_seed(0)
    gen = torch.Generator().manual_seed(4)
    obs = _obs(20)
    b = V.collate(obs)
    b = {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}
    build = N.TokenBuilders(N.CardTable(random=True)).double().eval()
    enc = _wake(E.StateGraphEncoder(layers=2).double().eval(), gen)
    heads = H.V7Heads().double().eval()
    return obs, b, build, enc, heads


def test_logits_invariant_to_padding(stack):
    obs, b, build, enc, heads = stack
    with torch.no_grad():
        ref, _, _ = heads(enc(build(b)))
    pad = 4
    bp = dict(b)
    B, K, w = b["cand"].shape
    bp["cand"] = torch.cat([b["cand"], torch.zeros(B, pad, w, dtype=b["cand"].dtype)], 1)
    bp["cand_type"] = torch.cat([b["cand_type"], torch.zeros(B, pad, dtype=torch.long)], 1)
    bp["cand_mask"] = torch.cat([b["cand_mask"], torch.zeros(B, pad, dtype=torch.bool)], 1)
    bp["refers"] = torch.cat([b["refers"], torch.zeros(B, pad, b["refers"].shape[2], dtype=b["refers"].dtype)], 1)
    Nn, T = b["ent"].shape[1], b["edges"].shape[1]
    bp["ent"] = torch.cat([b["ent"], torch.zeros(B, pad, b["ent"].shape[2], dtype=b["ent"].dtype)], 1)
    bp["ent_id"] = torch.cat([b["ent_id"], torch.full((B, pad), -1, dtype=torch.long)], 1)
    bp["ent_mask"] = torch.cat([b["ent_mask"], torch.zeros(B, pad, dtype=torch.bool)], 1)
    e = torch.zeros(B, T + pad, T + pad, dtype=torch.long); e[:, :T, :T] = b["edges"]; bp["edges"] = e
    bp["tok_mask"] = torch.cat([b["tok_mask"], torch.zeros(B, pad, dtype=torch.bool)], 1)
    r = torch.zeros(B, K + pad, T + pad, dtype=b["refers"].dtype); r[:, :K, :T] = b["refers"]; bp["refers"] = r
    a = torch.zeros(B, b["opp_act_refers"].shape[1], T + pad, dtype=b["opp_act_refers"].dtype); a[:, :, :T] = b["opp_act_refers"]; bp["opp_act_refers"] = a
    with torch.no_grad():
        out, _, _ = heads(enc(build(bp)))
    real = b["cand_mask"]
    assert (out[:, :K][real] - ref[real]).abs().max().item() <= 1e-6
    assert torch.isinf(ref[~real]).all() and torch.isinf(out[:, :K][~real]).all()
    assert torch.isinf(out[:, K:]).all() and (out[:, K:] < 0).all()
    lp = H.V7Heads.log_probs(out)
    assert torch.allclose(lp[:, :K].exp().sum(1), torch.ones(B, dtype=lp.dtype))


@pytest.fixture(scope="module")
def big():
    obs, b, build, enc, heads = None, None, None, None, None
    torch.manual_seed(0)
    gen = torch.Generator().manual_seed(4)
    obs = _gen_obs(100)                                             # 700 consults
    b = V.collate(obs)
    b = {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}
    build = N.TokenBuilders(N.CardTable(random=True)).double().eval()
    enc = E.StateGraphEncoder(layers=2).double().eval()            # untrained: identity (architecture at init)
    heads = H.V7Heads().double().eval()
    return obs, b, build, enc, heads


def test_candidate_count_readable_from_game_token(big):
    import faithfulness as Fp
    obs, b, build, enc, heads = big
    with torch.no_grad():
        _, game_vec, _ = heads(enc(build(b)))
    y = np.array([o.cand.shape[0] for o in obs], dtype=float)[:, None]
    res = Fp.probe(game_vec.numpy(), y, np.arange(len(obs)), ["real"], thresholds={0: 0.9})
    assert res[0]["pass"], res


def test_lstm_carries_information_across_consults(big):
    """A planted bit in the game vector at consult t must be linearly recoverable
    from the memory-conditioned game vector at t+1 with a different consult."""
    obs, b, build, enc, heads = big
    gen = torch.Generator().manual_seed(9)
    with torch.no_grad():                                                     # wake the memory path
        heads.game_out.weight.copy_(torch.randn(heads.game_out.weight.shape, generator=gen, dtype=torch.float64) * 0.1)
    with torch.no_grad():
        e = enc(build(b))
        B = e["game"].shape[0]
        bits = torch.randint(0, 2, (B,), generator=gen).double()
        e1 = dict(e); e1["game"] = e["game"].clone()
        e1["game"][:, 0, :16] = e1["game"][:, 0, :16] + 3.0 * bits[:, None]   # plant a bit at t (16 dims)
        _, _, st = heads(e1)
        e2 = dict(e); e2["game"] = e["game"].roll(1, 0)                          # a different consult at t+1
        _, game_next, _ = heads(e2, st)
        _, game_next_nomem, _ = heads(e2, None)
    X = torch.cat([game_next, game_next_nomem]).numpy()
    y = torch.cat([bits, torch.full_like(bits, float("nan"))]).numpy()[:, None]
    import faithfulness as Fp
    res = Fp.probe(X, y, np.arange(2 * B), ["binary"], thresholds={0: 0.9})
    assert res[0]["pass"], res
    assert (game_next - game_next_nomem).abs().max().item() > 1e-6
