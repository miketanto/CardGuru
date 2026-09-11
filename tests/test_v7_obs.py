"""Phase 4a gate (v7 plan §2): fixtures parse into V7Obs; every malformed
fixture is refused with the reason; collation pads and masks consistently."""
import glob
import json
import os
import sys

import pytest

torch = pytest.importorskip("torch")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rl"))
import v7_obs as V          # noqa: E402
import wire_validate as W   # noqa: E402

FIX = os.path.join(HERE, "..", "rl", "fixtures", "v7")
pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(FIX, "valid_spell.jsonl")), reason="fixtures not generated")


def _stream(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


@pytest.fixture(scope="module")
def ids():
    return V.CardIds()


@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(FIX, "valid_*.jsonl"))))
def test_valid_fixtures_parse(path, ids):
    msgs = _stream(path)
    hello = V.check_hello_v7(msgs[0], "card_emb_v8")
    obs = [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"]
    assert len(obs) == 20
    for o in obs:
        T = o.n_tokens
        assert o.edges.shape == (T, T) and o.refers.shape[1] == T
        assert (o.ent_id >= 0).float().mean() > 0.95            # real names resolve
        assert o.game.shape == (W.DIMS["game"],) and o.players.shape == (2, W.DIMS["player"])
        nonpass = o.cand_type != 0
        assert (o.refers[nonpass].sum(1) > 0).all()             # refers coverage on non-PASS


@pytest.mark.parametrize("path", sorted(p for p in glob.glob(os.path.join(FIX, "broken_*.jsonl")) if "reply" not in p))
def test_broken_fixtures_refused(path, ids):
    msgs = _stream(path)
    with pytest.raises(ValueError):
        hello = V.check_hello_v7(msgs[0], "card_emb_v8")
        for m in msgs:
            if m.get("t") == "consult":
                V.parse_consult(m, ids, hello)


def test_collate_pads_and_masks(ids):
    msgs = _stream(os.path.join(FIX, "valid_block.jsonl"))
    hello = V.check_hello_v7(msgs[0], "card_emb_v8")
    obs = [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"][:4]
    b = V.collate(obs)
    B, N = b["ent"].shape[:2]
    assert B == 4 and b["tok_mask"].shape == (4, 3 + N)
    for i, o in enumerate(obs):
        assert b["ent_mask"][i].sum() == o.ent.shape[0]
        assert b["cand_mask"][i].sum() == o.cand.shape[0]
        assert b["tok_mask"][i].sum() == o.n_tokens
        assert torch.equal(b["edges"][i, :o.n_tokens, :o.n_tokens], o.edges)
        assert b["edges"][i, o.n_tokens:].sum() == 0 and b["refers"][i, :, o.n_tokens:].sum() == 0


def test_card_emb_mismatch_refused():
    msgs = _stream(os.path.join(FIX, "valid_pass.jsonl"))
    with pytest.raises(ValueError, match="card_emb"):
        V.check_hello_v7(msgs[0], "card_emb_v99")
