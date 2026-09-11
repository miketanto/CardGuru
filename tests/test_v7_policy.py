"""Phase 4g gates (v7 plan §2): the assembled v7 policy runs on fixtures,
checkpoints round-trip with a dims record, a disagreeing dims record is
refused, --frozen leaves no trainable parameter."""
import os
import sys

import pytest

torch = pytest.importorskip("torch")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rl"))
import v7_obs as V          # noqa: E402
import v7_policy as P       # noqa: E402
import wire_fixtures as F   # noqa: E402


def _batch(n=4, seed=61):
    ids = V.CardIds()
    msgs = F.valid_stream("block", seed=seed, n=n, with_opp=True)
    hello = V.check_hello_v7(msgs[0], "card_emb_v8")
    obs = [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"]
    return hello, V.collate(obs)


def test_forward_and_counts():
    torch.manual_seed(0)
    net = P.V7Policy(random_table=True, layers=2, value_layers=1).eval()
    hello, b = _batch()
    with torch.no_grad():
        logits, value, game_vec, state = net(b)
    B, K = b["cand"].shape[:2]
    assert logits.shape == (B, K) and value.shape == (B,) and game_vec.shape == (B, 256)
    assert torch.isfinite(logits[b["cand_mask"]]).all() and torch.isinf(logits[~b["cand_mask"]]).all()
    counts = P.count_params(net)
    assert counts["policy_trainable"] > 0 and counts["belief"] > 0
    assert not any(id(p) in {id(q) for q in net.belief.parameters()} for p in net.policy_parameters())


def test_checkpoint_round_trip_and_dims_refusal(tmp_path):
    torch.manual_seed(0)
    net = P.V7Policy(random_table=True, layers=2, value_layers=1).eval()
    hello, b = _batch()
    with torch.no_grad():
        ref, _, _, _ = net(b)
    path = str(tmp_path / "v7.pt")
    net.save(path, episodes=7)
    ck = torch.load(path, map_location="cpu", weights_only=False)
    assert ck["dims"]["wire"] == 7 and ck["dims"]["card_emb"] == "random" and ck["episodes"] == 7
    # the random table is not reproducible from disk by design; load must still refuse a bad dims record
    ck["dims"]["v7_dims"] = dict(ck["dims"]["v7_dims"], ent=63)
    bad = str(tmp_path / "bad.pt")
    torch.save(ck, bad)
    with pytest.raises(ValueError, match="dims record"):
        P.V7Policy.load(bad)


def test_frozen_has_no_trainable_parameters():
    net = P.V7Policy(random_table=True, layers=1, value_layers=1, frozen=True)
    assert all(not p.requires_grad for p in net.parameters())
    assert net.policy_parameters() == []
