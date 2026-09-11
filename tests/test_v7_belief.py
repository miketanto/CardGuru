"""Phase 4f gates (v7 plan §2): with --belief off the net is bit-identical to
the 4e net; the belief loss never reaches a policy parameter (stop-gradient);
the leak gate still passes with belief features on; the module can beat the
uniform-over-remaining baseline on a planted synthetic labelling."""
import glob
import json
import os
import random
import sys

import pytest

torch = pytest.importorskip("torch")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rl"))
import v7_obs as V          # noqa: E402
import v7_net as N          # noqa: E402
import v7_encoder as E      # noqa: E402
import v7_heads as H        # noqa: E402
import v7_belief as BL      # noqa: E402
import wire_fixtures as F   # noqa: E402


def _batch(n=16, seed=31):
    ids = V.CardIds()
    msgs = F.valid_stream("attack", seed=seed, n=n, with_opp=True)
    hello = V.check_hello_v7(msgs[0], "card_emb_v8")
    obs = [V.parse_consult(m, ids, hello) for m in msgs if m.get("t") == "consult"]
    b = V.collate(obs)
    return obs, {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}


def _wake(enc, gen):
    for blk in enc.blocks:
        for lin in (blk.att.out, blk.ffn[-1]):
            with torch.no_grad():
                lin.weight.copy_(torch.randn(lin.weight.shape, generator=gen, dtype=lin.weight.dtype) * 0.05)
    return enc


@pytest.fixture(scope="module")
def nets():
    torch.manual_seed(0)
    gen = torch.Generator().manual_seed(6)
    build = N.TokenBuilders(N.CardTable(random=True)).double().eval()
    enc = _wake(E.StateGraphEncoder(layers=2).double().eval(), gen)
    heads = H.V7Heads().double().eval()
    belief = BL.BeliefModule().double().eval()
    with torch.no_grad():                                     # wake the (zero-init) feature maps
        belief.hand_feat.weight.copy_(torch.randn(belief.hand_feat.weight.shape, generator=gen, dtype=torch.float64) * 0.05)
        belief.deck_feat.weight.copy_(torch.randn(belief.deck_feat.weight.shape, generator=gen, dtype=torch.float64) * 0.5)
    return build, enc, heads, belief


def test_belief_off_is_bit_identical(nets):
    build, enc, heads, belief = nets
    obs, b = _batch()
    with torch.no_grad():
        toks = build(b)
        ref, _, _ = heads(enc(toks))
        belief.off = True
        out = belief(toks)
        lg_off, _, _ = heads(enc(belief.attach(toks, out)))
        belief.off = False
        lg_on, _, _ = heads(enc(belief.attach(toks, out)))
    assert torch.equal(lg_off, ref)
    fin = torch.isfinite(ref)
    assert (lg_on[fin] - ref[fin]).abs().max().item() > 1e-9      # the features reach the policy when on


def test_stop_gradient_into_builders(nets):
    build, enc, heads, belief = nets
    obs, b = _batch()
    build.train(); belief.train()
    for p in build.parameters():
        p.grad = None
    toks = build(b)
    out = belief(toks)
    B, Hh, D = out["pointer"].shape
    slot_t = torch.where(b["opp_hand_mask"], torch.zeros(B, Hh, dtype=torch.long), torch.full((B, Hh), -1))
    hand_t = torch.zeros(B, D, dtype=torch.float64); hand_t[:, 0] = 1.0
    draw_t = torch.zeros(B, dtype=torch.long)
    loss = belief.loss(out, slot_t, hand_t, draw_t, b["opp_hand_mask"], b["opp_deck_mask"])
    loss.backward()
    assert all(p.grad is None or p.grad.abs().sum() == 0 for p in build.parameters())
    assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in belief.parameters())
    build.eval(); belief.eval()


def test_leak_gate_with_belief_on(nets):
    """Belief features are computed from legal tokens only, so the policy logits
    stay bit-identical under a swap of the privileged content."""
    build, enc, heads, belief = nets
    ids = V.CardIds()
    msgs = F.valid_stream("spell", seed=41, n=8, with_opp=True)
    hello = msgs[0]

    def logits(m):
        o = V.parse_consult(m, ids, hello)
        b = V.collate([o]); b = {k: (v.double() if v.dtype == torch.float32 else v) for k, v in b.items()}
        with torch.no_grad():
            toks = build(b)
            lg, _, _ = heads(enc(belief.attach(toks, belief(toks))))
        return lg[0][torch.isfinite(lg[0])].tolist()

    for m in msgs:
        if m.get("t") == "consult":
            m["oe"] = [[0.5] * 48]; m["v7_oe_hand"] = ["Counterspell"]
            a = logits(m)
            m["oe"] = [[0.1] * 48, [0.9] * 48]; m["v7_oe_hand"] = ["Lightning Bolt", "Island"]
            assert a == logits(m)


def test_beats_uniform_baseline_on_planted_labels(nets):
    """Train the module for a few steps on a synthetic rule (the true slot card is
    the remaining-deck token with the largest first feature); held-out
    log-likelihood must beat uniform-over-remaining."""
    build, enc, heads, belief = nets
    torch.manual_seed(1)
    obs, b = _batch(n=48, seed=51)
    with torch.no_grad():
        toks = build(b)
    B, Hh = b["opp_hand_mask"].shape
    D = b["opp_deck_mask"].shape[1]
    score = b["opp_deck"][..., 0].masked_fill(~b["opp_deck_mask"], -1.0)
    slot_t = torch.where(b["opp_hand_mask"], score.argmax(1, keepdim=True).expand(B, Hh), torch.full((B, Hh), -1))
    hand_t = torch.nn.functional.one_hot(score.argmax(1), D).to(torch.float64)
    draw_t = score.argmax(1)
    tr, te = slice(0, 36), slice(36, 48)
    def sub(x, s): return x[s]
    tt = {k: sub(v, tr) for k, v in toks.items() if torch.is_tensor(v)}
    te_t = {k: sub(v, te) for k, v in toks.items() if torch.is_tensor(v)}
    bl = BL.BeliefModule(d=256, layers=1).double()
    opt = torch.optim.Adam(bl.parameters(), lr=3e-4)
    for _ in range(150):
        out = bl(tt)
        loss = bl.loss(out, slot_t[tr], hand_t[tr], draw_t[tr], b["opp_hand_mask"][tr], b["opp_deck_mask"][tr])
        opt.zero_grad(); loss.backward(); opt.step()
    bl.eval()
    with torch.no_grad():
        out = bl(te_t)
        lp = (out["pointer"] + 1e-9).log()
        ok = (slot_t[te] >= 0) & b["opp_hand_mask"][te]
        ll = lp.gather(2, slot_t[te].clamp(min=0).unsqueeze(-1)).squeeze(-1)[ok].mean()
        base = BL.BeliefModule.baseline_loglik(b["opp_deck_mask"][te], slot_t[te], b["opp_hand_mask"][te])
    print(f"held-out log-lik {ll.item():.3f} vs uniform {base.item():.3f}")
    assert ll.item() > base.item() + 0.3
