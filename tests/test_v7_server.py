"""Phase 4g part 2 gates (v7 plan §2): policy_server.py behind --arch v7.

Handshake: a v7 server refuses a v6 hello and a wrong card table, a v6
server refuses a wire:7 hello. Serving: fixture consults through act_v7
give in-range actions, the LSTM state advances per consult and resets at
end of episode, the buffer holds compact V7Obs. Training: UPDATE_EPISODES
completed episodes run one PPO update that moves the policy parameters
(and not the belief module), writes a checkpoint the Trainer reloads with
its dims record and V7Policy.load reads too; a disagreeing record is
refused. --frozen: no optimiser, no update, no save. Batcher: a batch of
several sessions' consults gives the same logits as one at a time.
Deck context: per-row overrides and D vectors reach the forward.
"""
import os
import sys

import pytest

torch = pytest.importorskip("torch")
HERE = os.path.dirname(os.path.abspath(__file__))
RL = os.path.join(HERE, "..", "rl")
sys.path.insert(0, RL)
import policy_server as ps          # noqa: E402
import v7_obs as V                  # noqa: E402
import v7_policy as P               # noqa: E402
import v7_deckctx as DC             # noqa: E402
import wire_fixtures as F           # noqa: E402


def _trainer(tmp_path, seed=0, frozen=False, belief=True, ckpt="v7.pt", deck_ctx=None):
    ps.DEVICE = torch.device("cpu")
    tr = ps.Trainer(str(tmp_path / ckpt), seed, None, arch="v7", card_emb="random",
                    belief=belief, frozen=frozen, deck_ctx=deck_ctx)
    tr.frozen = frozen
    # small net so the test is seconds, not minutes
    return tr


def _small(tmp_path, **kw):
    """A Trainer whose V7Policy is 2 encoder layers / 1 value layer."""
    tr = _trainer(tmp_path, **kw)
    torch.manual_seed(kw.get("seed", 0))
    net = P.V7Policy(random_table=True, layers=2, value_layers=1, belief=kw.get("belief", True),
                     frozen=kw.get("frozen", False))
    tr.net = net
    params = net.policy_parameters()
    tr.opt = torch.optim.Adam(params, lr=ps.LR) if params else None
    return tr


def _play(tr, episodes, n=6, seed=1, session=None, reward=1.0, mode="train"):
    """Drive hello/consult/end through the same calls handle() makes."""
    for ep in range(episodes):
        msgs = F.valid_stream("block", seed=seed + ep, n=n, with_opp=True)
        hello = msgs[0]
        ps.check_hello(hello, tr)
        sink = tr if session is None else session
        sink.hello, sink.n_validated, sink.hidden = hello, 0, None
        sink.deck = tr.deck_ctx.game(hello.get("v7_decks")) if tr.deck_ctx is not None else None
        for m in msgs[1:]:
            if m.get("t") == "consult":
                a = tr.act_v7(m, sample=(mode == "train"), phi=0.0, session=session)
                assert 0 <= a < len(m["v7_cand_type"])
            elif m.get("t") == "end":
                tr.end_episode(reward if ep % 2 == 0 else -reward, training=(mode == "train" and not tr.frozen),
                               session=session)


# ----------------------------------------------------------------- handshake
def test_handshake_refusals(tmp_path):
    tr = _small(tmp_path)
    hello = F.hello()
    assert ps.check_hello(hello, tr) is hello
    v6 = {k: v for k, v in hello.items() if not k.startswith("v7_") and k not in ("wire", "card_emb", "d_c")}
    with pytest.raises(RuntimeError, match="encoderV=7"):
        ps.check_hello(v6, tr)
    bad = dict(hello, v7_dims=dict(hello["v7_dims"], ent=63))
    with pytest.raises(RuntimeError, match="HANDSHAKE MISMATCH"):
        ps.check_hello(bad, tr)
    # a real table refuses a hello naming another one
    tr.net.table.version = "card_emb_v8"
    with pytest.raises(RuntimeError, match="card_emb"):
        ps.check_hello(dict(hello, card_emb="card_emb_v7"), tr)
    # a v6 server refuses a wire:7 hello
    tr6 = ps.Trainer(None, 0, None, cdim=94, arch="entattn")
    with pytest.raises(RuntimeError, match="--arch v7"):
        ps.check_hello(hello, tr6)


# ----------------------------------------------------------------- serving
def test_serve_memory_and_buffer(tmp_path):
    tr = _small(tmp_path)
    _play(tr, 1, n=5)
    # one episode of 5 consults landed as compact V7Obs entries, memory reset at end
    assert len(tr.buf) == 5 and tr.hidden is None and tr.completed == [(0, 5, 1.0)]
    obs = tr.buf[0][0]
    assert obs.edges.dtype == torch.int8 and obs.refers.dtype == torch.uint8 and obs.v6 == {}
    assert len(tr.buf[0]) == 7 and isinstance(tr.buf[0][1], int)
    # memory advances within an episode: the state after consult 2 differs from after consult 1
    msgs = F.valid_stream("block", seed=9, n=2, with_opp=True)
    tr.hello, tr.n_validated, tr.hidden = msgs[0], 0, None
    tr.act_v7(msgs[1], sample=False)
    h1 = tr.hidden[0].clone()
    tr.act_v7(msgs[3], sample=False)
    assert not torch.allclose(h1, tr.hidden[0])
    # a broken consult is refused with the wire's reason, not a tensor error
    broken = dict(msgs[1]); broken["v7_cand_type"] = broken["v7_cand_type"] + [99]
    tr.n_validated = 0
    with pytest.raises(RuntimeError, match="bad v7 consult"):
        tr.act_v7(broken, sample=False)


def test_eval_mode_is_argmax_and_stores_nothing(tmp_path):
    tr = _small(tmp_path)
    _play(tr, 1, n=4, mode="eval")
    assert tr.buf == [] and tr.completed == []


# ----------------------------------------------------------------- training
def test_update_moves_policy_not_belief_and_checkpoints(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "UPDATE_EPISODES", 3)
    tr = _small(tmp_path)
    tr.tbptt, tr.ep_batch = 3, 2          # several windows and groups on tiny episodes
    before = {n: p.detach().clone() for n, p in tr.net.named_parameters()}
    belief_names = {"belief." + n for n, _ in tr.net.belief.named_parameters()}
    _play(tr, 3, n=7)
    assert tr.updates == 1 and tr.buf == [] and tr.episodes_seen == 3
    moved = [n for n, p in tr.net.named_parameters() if not torch.equal(before[n], p)]
    assert moved and not any(n in belief_names for n in moved), (moved[:5])
    assert not any(n.startswith("table.table") for n in moved)
    # checkpoint: the Trainer reloads it with its dims record, V7Policy.load reads it too
    path = tr.ckpt
    assert os.path.exists(path)
    ck = torch.load(path, map_location="cpu", weights_only=False)
    assert ck["arch"] == "v7" and ck["dims"]["wire"] == 7 and ck["config"]["arch"] == "v7" and ck["updates"] == 1
    tr2 = ps.Trainer(path, 0, None, arch="v7", card_emb="random")
    assert tr2.updates == 1 and tr2.episodes_seen == 3
    # the reloaded state dict is the one written (the random table differs by construction)
    for n, p in tr.net.named_parameters():
        assert torch.equal(p, dict(tr2.net.named_parameters())[n])
    net3 = P.V7Policy.load(path)
    assert net3.config["layers"] == 2
    ck["dims"]["v7_dims"] = dict(ck["dims"]["v7_dims"], ent=63)
    torch.save(ck, path)
    with pytest.raises(RuntimeError, match="CHECKPOINT DIM MISMATCH"):
        ps.Trainer(path, 0, None, arch="v7", card_emb="random")
    with pytest.raises(RuntimeError, match="ckpt arch"):
        ps.Trainer(path, 0, None, cdim=94, arch="entattn")


def test_frozen_has_no_optimiser_and_never_saves(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "UPDATE_EPISODES", 2)
    tr = _small(tmp_path, frozen=True)
    assert tr.opt is None and tr.net.policy_parameters() == []
    before = {n: p.detach().clone() for n, p in tr.net.named_parameters()}
    _play(tr, 2, n=4)                    # sampled, but training=False because frozen
    assert tr.buf == [] and tr.updates == 0 and not os.path.exists(tr.ckpt)
    assert all(torch.equal(before[n], p) for n, p in tr.net.named_parameters())


def test_dump_buf_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "UPDATE_EPISODES", 2)
    dump = str(tmp_path / "buf.pt")
    monkeypatch.setenv("RL_DUMP_BUF", dump)
    tr = _small(tmp_path)
    _play(tr, 2, n=3)
    d = torch.load(dump, map_location="cpu", weights_only=False)
    assert d["arch"] == "v7" and len(d["buf"]) == 6 and d["completed"] == [(0, 3, 1.0), (3, 6, -1.0)]
    assert isinstance(d["buf"][0][0], V.V7Obs)


# ----------------------------------------------------------------- batcher
def test_batcher_matches_sequential(tmp_path):
    tr = _small(tmp_path)
    tr.net.eval()
    msgs = F.valid_stream("block", seed=3, n=3, with_opp=True)
    ids = tr.ids
    obs = [V.compact(V.parse_consult(m, ids, msgs[0])) for m in msgs if m.get("t") == "consult"]
    dev = torch.device("cpu")
    seq = [tr._v7_forward(tr.net, [o], [[]], [None], None, dev, ids.n) for o in obs]
    b = ps.InferenceBatcher(tr.net, True, None, 8, 1.0, v7=(dev, ids.n))
    reqs = [ps.InferenceRequest(o, ([], None), None, None) for o in obs]
    b.run_batch(reqs)
    for r, (lg, v, st) in zip(reqs, seq):
        K = lg.shape[1]
        assert torch.allclose(r.out[0][:, :K], lg, atol=1e-5) and torch.isinf(r.out[0][:, K:]).all()
        assert torch.allclose(r.out[1], v, atol=1e-5)
        assert torch.allclose(r.out[2][0], st[0], atol=1e-5)


# ----------------------------------------------------------------- deck context
def test_deck_context_reaches_forward(tmp_path):
    tr = _small(tmp_path)
    tr.net.eval()
    # At init every encoder block is an exact identity (zero output
    # projections), so entity content cannot reach the logits until
    # training moves them; wake the attention paths so the probe can see
    # the identity vectors at all.
    torch.manual_seed(1)
    for enc in (tr.net.enc, tr.net.critic.enc):
        for blk in enc.blocks:
            torch.nn.init.normal_(blk.att.out.weight, std=0.05)
    msgs = F.valid_stream("block", seed=5, n=1, with_opp=True)
    o = V.compact(V.parse_consult(msgs[1], tr.ids, msgs[0]))
    dev = torch.device("cpu")
    base = tr._v7_forward(tr.net, [o], [[]], [None], None, dev, tr.ids.n)
    d_c = tr.net.table.adapter.in_features
    # D vectors only: the game token changes, so the logits/value do
    g1 = DC.GameDeck(None, None, torch.randn(d_c), torch.randn(d_c))
    out1 = tr._v7_forward(tr.net, [o], [[]], [g1], None, dev, tr.ids.n)
    assert not torch.allclose(out1[1], base[1])
    # an override for every known entity id changes the forward; for an id nobody has, it does not
    known = [int(i) for i in o.ent_id.tolist() if i >= 0]
    if known:
        g2 = DC.GameDeck({i: torch.randn(d_c) for i in known}, None, torch.zeros(d_c), torch.zeros(d_c))
        out2 = tr._v7_forward(tr.net, [o], [[]], [g2], None, dev, tr.ids.n)
        assert not torch.allclose(out2[0], base[0])
    g3 = DC.GameDeck({tr.ids.n - 1: torch.randn(d_c)}, None, torch.zeros(d_c), torch.zeros(d_c))
    if (o.ent_id == tr.ids.n - 1).any() or (o.opp_hand_id == tr.ids.n - 1).any() or (o.opp_deck_id == tr.ids.n - 1).any():
        pytest.skip("fixture happens to contain the sentinel id")
    out3 = tr._v7_forward(tr.net, [o], [[]], [g3], None, dev, tr.ids.n)
    assert torch.allclose(out3[0], base[0]) and torch.allclose(out3[1], base[1])


# ----------------------------------------------------------------- the real server
def test_server_process_end_to_end(tmp_path):
    """The actual policy_server.py process behind --arch v7: hello accepted,
    a v6 hello refused with the reason on the wire, fixture consults
    answered in range, end acknowledged, checkpoint written on close."""
    import json
    import socket
    import subprocess
    import time
    port = 7900 + (os.getpid() % 90)
    ckpt = str(tmp_path / "srv.pt")
    proc = subprocess.Popen([sys.executable, os.path.join(RL, "policy_server.py"), "--arch", "v7",
                             "--card-emb", "random", "--deck-ctx", "none", "--port", str(port),
                             "--ckpt", ckpt, "--frozen"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for _ in range(600):
            try:
                s = socket.create_connection(("127.0.0.1", port), timeout=1.0)
                break
            except OSError:
                if proc.poll() is not None:
                    raise AssertionError("server died:\n" + proc.stdout.read())
                time.sleep(0.1)
        else:
            raise AssertionError("server never listened")
        f = s.makefile("rwb")

        def rpc(m):
            f.write(json.dumps(m, separators=(",", ":")).encode() + b"\n"); f.flush()
            return json.loads(f.readline())
        msgs = F.valid_stream("block", seed=11, n=4, with_opp=True)
        assert rpc(dict(msgs[0], mode="eval")) == {"ok": 1}
        n = 0
        for m in msgs[1:]:
            if m.get("t") == "consult":
                r = rpc(m)
                assert 0 <= r["a"] < len(m["v7_cand_type"]); n += 1
            elif m.get("t") == "end":
                assert rpc(m) == {"ok": 1}
        assert n == 4
        f.close(); s.close()
        # a v6 hello on a second connection is refused with the reason
        s = socket.create_connection(("127.0.0.1", port), timeout=5.0)
        f = s.makefile("rwb")
        v6 = {"t": "hello", "mode": "eval", "gdim": 16, "edim": 48, "emax": 96, "rtypes": 6, "cdim": 94}
        r = rpc(v6)
        assert r["ok"] == 0 and "encoderV=7" in r["err"]
        f.close(); s.close()
    finally:
        proc.terminate()
        try:
            out = proc.communicate(timeout=20)[0]
        except subprocess.TimeoutExpired:
            proc.kill(); out = proc.communicate()[0]
    assert "policy server on" in out and "HANDSHAKE MISMATCH" in out, out[-2000:]
    assert not os.path.exists(ckpt)          # --frozen never writes


@pytest.mark.skipif(not os.path.exists(os.path.join(RL, "artifacts", "deck_ctx_v1", "model_seed0.pt")),
                    reason="deck_ctx_v1 artifact absent")
def test_deck_ctx_artifact_loads_and_is_cached():
    dc = DC.DeckCtx(device="cpu", fingerprint=False)
    g = dc.game(F.hello()["v7_decks"])
    assert g.D_me.shape == (dc.d_c,) and g.map_me and g.map_opp
    assert dc.side([["Lightning Bolt", 4], ["Mountain", 20]]) is dc.side([("Lightning Bolt", 4), ("Mountain", 20)])
    assert dc.game(None).ctx_map is None

def test_v7_optimizer_knobs(tmp_path, monkeypatch):
    """7a arms B2/B3: --weight-decay decays the heads only (AdamW); --heads-opt sgd
    puts the heads on SGD-momentum and the rest on Adam; the checkpoint round-trips
    under the same knobs and a differently shaped optimiser state is dropped, not fatal."""
    monkeypatch.setattr(ps, "UPDATE_EPISODES", 2)
    monkeypatch.setattr(ps, "WEIGHT_DECAY", 0.01)
    tr = _small(tmp_path)
    tr.opt = ps._v7_optimizer(tr.net, tr.net.policy_parameters())
    assert isinstance(tr.opt, torch.optim.AdamW)
    head_ids = {id(p) for p in tr.net.heads.parameters()}
    heads_g = [g for g in tr.opt.param_groups if all(id(p) in head_ids for p in g["params"])]
    rest_g = [g for g in tr.opt.param_groups if not any(id(p) in head_ids for p in g["params"])]
    assert len(heads_g) == 1 and len(rest_g) == 1 and len(tr.opt.param_groups) == 2
    assert heads_g[0]["weight_decay"] == 0.01 and rest_g[0]["weight_decay"] == 0.0
    assert sum(p.numel() for p in heads_g[0]["params"]) == sum(p.numel() for p in tr.net.heads.parameters())
    monkeypatch.setattr(ps, "WEIGHT_DECAY", 0.0)
    monkeypatch.setattr(ps, "HEADS_OPT", "sgd")
    tr = _small(tmp_path)
    tr.opt = ps._v7_optimizer(tr.net, tr.net.policy_parameters())
    assert isinstance(tr.opt, ps._MultiOpt) and len(tr.opt.opts) == 2
    assert isinstance(tr.opt.opts[0], torch.optim.SGD) and isinstance(tr.opt.opts[1], torch.optim.Adam)
    before = {n: p.detach().clone() for n, p in tr.net.named_parameters()}
    _play(tr, 2, n=4)
    assert tr.updates == 1 and os.path.exists(tr.ckpt)
    moved = [n for n, p in tr.net.named_parameters() if not torch.equal(before[n], p)]
    assert any(n.startswith("heads.") for n in moved) and any(not n.startswith("heads.") for n in moved)
    tr2 = ps.Trainer(tr.ckpt, 0, None, arch="v7", card_emb="random")      # same knobs: state loads
    assert isinstance(tr2.opt, ps._MultiOpt) and tr2.opt.opts[0].state_dict()["state"]
    monkeypatch.setattr(ps, "HEADS_OPT", "adam")
    tr3 = ps.Trainer(tr.ckpt, 0, None, arch="v7", card_emb="random")      # shape changed: fresh, no raise
    assert isinstance(tr3.opt, torch.optim.Adam) and not tr3.opt.state_dict()["state"]

