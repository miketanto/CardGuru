"""Self-test for EntityAttnPolicy (encoder v6's half of the network).

WHY IT IS COMMITTED. Everything this module claims is a property of a
pooling operator, and a property is an ARGUMENT until it is a check:

  - SUM pooling separates one 2/2 from three 2/2s; MEAN does not, and
    "does not" is exact rather than approximate, which is the whole
    reason ENCODER-V6-BUILD.md §4c shouts about it.
  - the pooled embedding is permutation-invariant, so stream A's
    emission ORDER cannot change what the agent sees;
  - arm R0 (relations zeroed) degrades to plain self-attention
    NUMERICALLY, not roughly - without that, an R0-vs-v6 A/B does not
    separate "entity rows helped" from "relations helped";
  - padded entity slots change no output;
  - the wire round-trips, and a driver whose vectors mean something
    else is rejected at the handshake instead of mispredicting for a
    whole run.

None of these need the engine, training, or a single game. Run:

    python3 rl/entattn_check.py

Exit code 0 = every check passed. In the spirit of
rl/xmage-src/CombatMathCheck.java: it prints numbers, not adjectives.

WHAT THIS CANNOT SHOW (ENCODER-V6-BUILD.md §0). Nothing here is
evidence about attack- or block-optimality, which cannot move from a
state-path change, and nothing here is evidence about win rate. The
entity ROWS below are synthetic stand-ins built to §1's layout so the
network can be tested before any Java exists; the emission side and its
collision gate (§5b) are stream A's, against the real board.
"""
import json
import socket
import sys
import threading
import time

import torch

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import policy_server as ps                                  # noqa: E402

CDIM = 94                    # the v4/v5 candidate width, untouched by v6
SEEDS = 5                    # pooling/collision are properties of the
                             # operator, so they are checked over several
                             # inits rather than one lucky one
FAILURES = []
RAN = []


def check(name, ok, detail):
    print("CHECK|%-11s|%s|%s" % (name, "PASS" if ok else "FAIL", detail),
          flush=True)
    RAN.append(name)
    if not ok:
        FAILURES.append(name)


# ---------------------------------------------------------------- rows
# The 48-dim entity token of ENCODER-V6-BUILD.md §1, as a synthetic
# builder. StateEncoder.java is the authoritative emitter (stream A);
# this exists only so the network can be exercised on boards whose
# COLLISION is known by construction.
I_OCC, I_MINE, I_THEIRS, I_ZONE = 0, 1, 2, 3     # zone one-hot at 3..7
I_POW, I_TOU, I_DMG, I_REM = 8, 9, 10, 11
I_CREA, I_LAND, I_PERM, I_MV = 12, 13, 14, 15
I_TAP, I_SICK, I_ATK, I_BLK = 16, 17, 18, 19
I_KW = 24                                        # 14 keyword bits 24..37
I_LIFE, I_HAND, I_LANDS, I_UNTAP = 44, 45, 46, 47

Z_BATTLEFIELD, Z_HAND, Z_STACK, Z_GRAVE, Z_PLAYER = 0, 1, 2, 3, 4


def row():
    return [0.0] * ps.EDIM


def creature(power, toughness, mine=True, damage=0, tapped=False,
             attacking=False, flying=False, mv=2):
    r = row()
    r[I_OCC] = 1.0
    r[I_MINE if mine else I_THEIRS] = 1.0
    r[I_ZONE + Z_BATTLEFIELD] = 1.0
    r[I_POW] = power / 6.0
    r[I_TOU] = toughness / 6.0
    r[I_DMG] = damage / 6.0
    r[I_REM] = (toughness - damage) / 6.0
    r[I_CREA] = 1.0
    r[I_MV] = mv / 6.0
    r[I_TAP] = 1.0 if tapped else 0.0
    r[I_ATK] = 1.0 if attacking else 0.0
    r[I_KW] = 1.0 if flying else 0.0
    return r


def player(mine, life=20, hand=5, lands=4, untapped=4):
    r = row()
    r[I_OCC] = 1.0
    r[I_MINE if mine else I_THEIRS] = 1.0
    r[I_ZONE + Z_PLAYER] = 1.0
    r[I_LIFE] = life / 20.0
    r[I_HAND] = hand / 10.0
    r[I_LANDS] = lands / 10.0
    r[I_UNTAP] = untapped / 10.0
    return r


def globals_vec(turn=5, mine=1.0, life=20, opp_life=20):
    g = [0.0] * ps.GDIM
    g[0], g[1] = turn / 20.0, mine
    g[2], g[3] = life / 20.0, opp_life / 20.0
    return g


def board(bodies, mine=True):
    """[(p,t), ...] -> entity rows, my two players last."""
    return [creature(p, t, mine=mine) for p, t in bodies]


def trainer(r0=False, seed=0, **kw):
    """A real Trainer, so the checks run the SHIPPING pack/validate path
    rather than a test-local copy of it."""
    return ps.Trainer(None, seed, None, cdim=CDIM, arch="entattn",
                      r0=r0, **kw)


def obs_of(tr, ents, rels=(), g=None):
    return tr._entity_obs(g if g is not None else globals_vec(), ents,
                          list(rels))


def maxdiff(a, b):
    return float((a - b).abs().max())


# ------------------------------------------------------------- POOLING
def test_pooling():
    """One 2/2 versus three 2/2s. The whole point of the change.

    Also measures the MEAN-pooled counterfactual on the same net: with
    no positional encoding the three identical tokens each attend to
    three identical keys, so the encoder returns three identical rows
    and their mean is the single token's row exactly. That is the
    collision v6 exists to remove, and it is worth measuring rather
    than asserting.
    """
    sums, means = [], []
    for seed in range(SEEDS):        # a property, not a lucky init
        tr = trainer(seed=seed)
        net = tr.net
        one = obs_of(tr, board([(2, 2)]))
        three = obs_of(tr, board([(2, 2)] * 3))
        with torch.no_grad():
            s1, s3 = net.state_token(one), net.state_token(three)

            def mean_token(obs):
                x = net.ent_in(obs.e)
                y = net.ent_enc(x, mask=net.entity_bias(obs.rel, obs.mask))
                y = y * obs.mask.unsqueeze(-1)
                n = obs.mask.sum(dim=1, keepdim=True).clamp(min=1)
                return net.glob_in(obs.g) + net.pool(y.sum(dim=1) / n)

            m1, m3 = mean_token(one), mean_token(three)
        sums.append(maxdiff(s1, s3))
        means.append(maxdiff(m1, m3))
    d_sum, d_mean = min(sums), max(means)
    check("POOLING", d_sum > 1e-2,
          "sum: max|1x2/2 - 3x2/2| over %d inits, worst = %.6f "
          "(must be > 1e-2)" % (SEEDS, d_sum))
    check("MEANCOLLIDE", d_mean < 1e-5,
          "mean-pooled, same nets: worst %.9f - the collision v6 removes "
          "(reported, not required)" % d_mean)


def test_collision():
    """The six §5b boards, all count 3 / power 7 / toughness 7.

    The NETWORK half of the acceptance gate: given correct entity rows,
    six boards that are one vector under v5 must be six vectors here.
    The gate itself (§5b) is stream A's, against real emission.
    """
    boards = [[(2, 2), (2, 2), (3, 3)], [(2, 2), (3, 1), (2, 4)],
              [(2, 2), (2, 3), (3, 2)], [(3, 1), (2, 3), (2, 3)],
              [(2, 3), (3, 3), (2, 1)], [(3, 2), (2, 4), (2, 1)]]
    for b in boards:                     # the premise, checked not assumed
        assert len(b) == 3 and sum(p for p, _ in b) == 7 \
            and sum(t for _, t in b) == 7, b
    worst, scale = 1e9, 0.0
    for seed in range(SEEDS):
        tr = trainer(seed=seed)
        with torch.no_grad():
            toks = [tr.net.state_token(obs_of(tr, board(b))) for b in boards]
        worst = min([worst] + [maxdiff(toks[i], toks[j])
                               for i in range(len(toks))
                               for j in range(i + 1, len(toks))])
        scale = max(scale, max(float(t.abs().max()) for t in toks))
    # the claim is "not identical", not "well separated": at INIT the
    # separation is whatever untrained weights give, and its size means
    # nothing until something is trained. Print the scale so nobody
    # reads 0.005 as a small number or a large one by accident.
    check("COLLISION", worst > 1e-3,
          "6 boards, all 3/7/7, %d inits: closest pair differs by %.6f "
          "against token scale %.3f (v5 gives exactly 0 by construction)"
          % (SEEDS, worst, scale))


# --------------------------------------------------------- PERMUTATION
def test_permutation():
    tr = trainer()
    ents = board([(2, 2), (3, 1), (2, 4)]) \
        + board([(1, 1), (4, 4)], mine=False) \
        + [player(True), player(False)]
    # blocks / blocked_by / attacking_player, over those indices
    rels = [[3, 0, 0], [0, 3, 1], [0, 6, 2], [5, 1, 4]]
    perm = [4, 0, 6, 2, 5, 3, 1]
    pos = {old: new for new, old in enumerate(perm)}
    p_ents = [ents[o] for o in perm]
    p_rels = [[pos[s], pos[d], t] for s, d, t in rels]
    with torch.no_grad():
        a = tr.net.state_token(obs_of(tr, ents, rels))
        b = tr.net.state_token(obs_of(tr, p_ents, p_rels))
    d = maxdiff(a, b)
    check("PERMUTE", d < 1e-5,
          "7 rows shuffled + edges remapped: max diff %.3e" % d)
    # and the negative control: WITHOUT remapping the edges it must NOT
    # match, or the test would pass on a net that ignores relations
    with torch.no_grad():
        c = tr.net.state_token(obs_of(tr, p_ents, rels))
    d2 = maxdiff(a, c)
    check("PERMUTE-NEG", d2 > 1e-4,
          "same rows, edges left pointing at the old order: %.6f "
          "(must differ, else relations are inert)" % d2)


# ------------------------------------------------------------------ R0
def test_r0():
    """Arm R0 must be plain self-attention, numerically.

    Verified two ways, because §2's claim is exactly this: with no
    edges the bias is the padding_idx row, which is zero and stays zero
    under training.
    """
    tr = trainer(r0=True)
    net = tr.net
    check("R0-ZERO", float(net.rel_emb.weight[0].detach().abs().max()) == 0.0,
          "rel_emb[no-edge] = %s" % net.rel_emb.weight[0].tolist())

    # (a) a FULL board: no padding either, so "plain self-attention"
    #     means the encoder called with no mask argument at all
    rows = [(1 + i % 4, 1 + (i * 3) % 5) for i in range(ps.EMAX)]
    edges = [[0, 1, 0], [1, 0, 1], [2, 3, 2]]      # dropped by r0
    full = obs_of(tr, board(rows), rels=edges)
    with torch.no_grad():
        r0_tok = net.state_token(full)
        y = net.ent_enc(net.ent_in(full.e))            # no mask term
        want = net.glob_in(full.g) + net.pool(y.sum(dim=1))
    d_full = maxdiff(r0_tok, want)
    check("R0-NOBIAS", d_full < 1e-6,
          "%d entities, no padding: max|biased - plain| = %.3e"
          % (ps.EMAX, d_full))

    # (b) a PADDED board against the canonical padding idiom, which is
    #     what says the merged float mask is doing what a
    #     src_key_padding_mask does
    part = obs_of(tr, board([(2, 2), (3, 3), (1, 4)]) + [player(True)])
    with torch.no_grad():
        got = net.state_token(part)
        y = net.ent_enc(net.ent_in(part.e),
                        src_key_padding_mask=~part.mask)
        y = y * part.mask.unsqueeze(-1)
        want = net.glob_in(part.g) + net.pool(y.sum(dim=1))
    d_pad = maxdiff(got, want)
    check("R0-PADIDIOM", d_pad < 1e-5,
          "4 of %d slots used: max|merged mask - key_padding_mask| = "
          "%.3e" % (ps.EMAX, d_pad))

    # (c) the SAME board and the SAME weights with the edges live must
    #     NOT match, or (a) passed because the bias is inert rather than
    #     because it is zero. Only rel_emb's edge rows differ.
    live = trainer(r0=False)
    live.net.load_state_dict(net.state_dict())
    with torch.no_grad():
        live.net.rel_emb.weight[1:].normal_(0.0, 1.0)
        d_live = maxdiff(live.net.state_token(obs_of(live, board(rows),
                                                     rels=edges)), r0_tok)
    check("R0-CONTRAST", d_live > 1e-4,
          "same board, same weights, 3 edges live: %.6f (must differ)"
          % d_live)


# ------------------------------------------------------------- MASKING
def test_masking():
    """Padded slots must not change ANY output - token, logits, value."""
    tr = trainer()
    ents = board([(2, 2), (3, 1)]) + [player(True), player(False)]
    o1 = obs_of(tr, ents, [[0, 2, 4], [1, 3, 2]])
    o2 = obs_of(tr, ents, [[0, 2, 4], [1, 3, 2]])
    torch.manual_seed(11)
    o2.e[0, len(ents):] = torch.randn(ps.EMAX - len(ents), ps.EDIM) * 5
    cands = torch.randn(1, ps.MAX_K, CDIM)
    cmask = torch.zeros(1, ps.MAX_K, dtype=torch.bool)
    cmask[0, :6] = True
    with torch.no_grad():
        t1, t2 = tr.net.state_token(o1), tr.net.state_token(o2)
        l1, v1, _ = tr.net(o1, cands, cmask)
        l2, v2, _ = tr.net(o2, cands, cmask)
    d = max(maxdiff(t1, t2), maxdiff(l1[cmask], l2[cmask]), maxdiff(v1, v2))
    check("MASKING", d < 1e-6,
          "garbage in %d padded slots: max diff over token/logits/value "
          "= %.3e" % (ps.EMAX - len(ents), d))

    # an empty board must not produce NaN (all keys masked is the
    # softmax trap; the encoder keeps key 0 open and the pool drops it)
    empty = obs_of(tr, [])
    with torch.no_grad():
        te = tr.net.state_token(empty)
    check("EMPTY", bool(torch.isfinite(te).all()),
          "zero entities: finite=%s" % bool(torch.isfinite(te).all()))


# ---------------------------------------------------------- VALIDATION
def test_validation():
    """Per-consult drift the handshake cannot catch must raise, not be
    quietly coerced. Every one of these has a plausible emitter bug
    behind it."""
    tr = trainer()
    ents = board([(2, 2), (3, 3)])
    cases = [
        ("globals width", lambda: obs_of(tr, ents, g=[0.0] * (ps.GDIM - 1))),
        ("row width", lambda: obs_of(tr, [[0.0] * (ps.EDIM + 2)])),
        ("too many entities",
         lambda: obs_of(tr, board([(1, 1)] * (ps.EMAX + 1)))),
        ("edge past the board", lambda: obs_of(tr, ents, [[0, 9, 0]])),
        ("type outside RTYPES",
         lambda: obs_of(tr, ents, [[0, 1, len(ps.RTYPES)]])),
        ("non-integral edge", lambda: obs_of(tr, ents, [[0, 1.5, 0]])),
        ("malformed edge", lambda: obs_of(tr, ents, [[0, 1]])),
    ]
    served = []
    for tag, fn in cases:
        try:
            fn()
            served.append(tag)
        except ValueError:
            pass
    check("VALIDATE", not served,
          "%d bad consults all refused%s" % (len(cases),
          "" if not served else "; ACCEPTED " + str(served)))


# --------------------------------------------------------- TRAIN + CKPT
def test_train_and_ckpt(tmp="/tmp/entattn_check_ckpt.pt"):
    """A PPO update must run over EntityObs batches, and the no-edge
    bias must still be exactly zero afterwards - R0's degradation is
    structural (padding_idx) or it is not a guarantee."""
    import os
    if os.path.exists(tmp):
        os.remove(tmp)
    tr = ps.Trainer(tmp, 0, None, cdim=CDIM, arch="entattn")
    before = tr.net.pool.weight.detach().clone()
    torch.manual_seed(3)
    ents = board([(2, 2), (3, 3)]) + [player(True), player(False)]
    cands = [[float(x) for x in torch.randn(CDIM)] for _ in range(4)]
    for ep in range(ps.UPDATE_EPISODES):
        for _ in range(3):
            tr.act(None, cands, sample=True, phi=0.0,
                   ent=(globals_vec(), ents, [[0, 2, 4], [1, 3, 0]]))
        tr.end_episode(1.0 if ep % 2 else -1.0, training=True)
    moved = float((tr.net.pool.weight - before).abs().max())
    check("TRAINSTEP", tr.updates == 1 and moved > 0,
          "1 PPO update over %d episodes; pool weights moved %.3e"
          % (ps.UPDATE_EPISODES, moved))
    check("R0-STAYS0", float(tr.net.rel_emb.weight[0].abs().max()) == 0.0,
          "rel_emb[no-edge] after training = %s"
          % tr.net.rel_emb.weight[0].tolist())

    ps.Trainer(tmp, 0, None, cdim=CDIM, arch="entattn")      # must load
    bad = []
    for kw, why in ((dict(edim=64), "edim"), (dict(gdim=24), "gdim"),
                    (dict(cdim=91), "cdim"), (dict(r0=True), "r0")):
        args = dict(cdim=CDIM, arch="entattn")
        args.update(kw)
        try:
            ps.Trainer(tmp, 0, None, **args)
            bad.append(why)
        except RuntimeError:
            pass
    check("CKPTDIMS", not bad,
          "mismatched %s all refused at load%s"
          % ("edim/gdim/cdim/r0", "" if not bad else "; ACCEPTED " + str(bad)))
    os.remove(tmp)


# ------------------------------------------------------------ LOOPBACK
def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def send(sock, obj):
    sock.sendall((json.dumps(obj) + "\n").encode())


def test_loopback():
    """A real socket, a real hello, a real consult, an action index back.

    This is what makes the wire-up with stream A a ten-minute job: if
    the driver's first v6 consult fails, this check says whether the
    server or the emitter is wrong.
    """
    tr = trainer()
    port = free_port()
    threading.Thread(target=ps.serve, args=(port, tr, 2), daemon=True).start()
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close()
            break
        except OSError:
            time.sleep(0.05)

    hello = {"t": "hello", "mode": "eval", "episodes": 1, "sdim": 32,
             "cdim": CDIM, "gdim": ps.GDIM, "edim": ps.EDIM,
             "emax": ps.EMAX, "rtypes": len(ps.RTYPES)}
    ents = board([(2, 2), (3, 1)]) + board([(4, 4)], mine=False) \
        + [player(True), player(False)]
    consult = {"t": "consult", "g": globals_vec(),
               "e": ents,
               "r": [[2, 0, 1], [0, 2, 0], [1, 4, 2], [3, 0, 4]],
               "c": [[0.0] * CDIM for _ in range(5)], "phi": 120.0}

    with socket.create_connection(("127.0.0.1", port), 5) as s:
        f = s.makefile("rwb")
        send(s, hello)
        ok = json.loads(f.readline())
        send(s, consult)
        rep = json.loads(f.readline())
        send(s, {"t": "end", "r": 1.0})
        fin = json.loads(f.readline())
    good = (ok.get("ok") == 1 and isinstance(rep.get("a"), int)
            and 0 <= rep["a"] < 5 and fin.get("ok") == 1)
    check("LOOPBACK", good,
          "hello -> %s, consult(5 entities, 4 edges, 5 cands) -> %s, "
          "end -> %s" % (ok, rep, fin))

    # and the failure the handshake exists for: a driver whose vectors
    # mean something else must be REFUSED, not served
    seen = []
    old_hook = threading.excepthook
    threading.excepthook = lambda a: seen.append(a.exc_value)
    try:
        for tag, hs in (("wrong edim", dict(hello, edim=64)),
                        ("v5 driver", {"t": "hello", "mode": "eval",
                                       "sdim": 32, "cdim": CDIM}),
                        ("emax > buffer", dict(hello, emax=64)),
                        ("rtypes drift", dict(hello, rtypes=9))):
            with socket.create_connection(("127.0.0.1", port), 5) as s:
                f = s.makefile("rwb")
                send(s, hs)
                rep = json.loads(f.readline())
            time.sleep(0.2)          # let the server's banner land first
            ok = rep.get("ok") == 0 and "MISMATCH" in rep.get("err", "")
            check("HANDSHAKE", ok, "%s -> %s"
                  % (tag, " ".join(str(rep.get("err", rep)).split())))
        time.sleep(0.3)
    finally:
        threading.excepthook = old_hook
    check("HS-RAISED", len(seen) == 4,
          "%d of 4 bad handshakes also killed the connection thread"
          % len(seen))

    # a consult that skips the entity fields entirely (an arm switch
    # mid-connection) must not be silently served either
    seen2 = []
    threading.excepthook = lambda a: seen2.append(a.exc_value)
    try:
        with socket.create_connection(("127.0.0.1", port), 5) as s:
            f = s.makefile("rwb")
            send(s, hello)
            f.readline()
            send(s, {"t": "consult", "s": [0.0] * 32,
                     "c": [[0.0] * CDIM]})
            line = f.readline()
        time.sleep(0.3)
    finally:
        threading.excepthook = old_hook
    check("FLATCONSULT", line == b"" and len(seen2) == 1,
          "flat consult to an entattn server: reply=%r raised=%s"
          % (line, [type(e).__name__ for e in seen2]))

    # and an edge that points past the emitted entities - the drift the
    # handshake CANNOT catch, because it is per-consult
    seen3 = []
    threading.excepthook = lambda a: seen3.append(a.exc_value)
    try:
        with socket.create_connection(("127.0.0.1", port), 5) as s:
            f = s.makefile("rwb")
            send(s, hello)
            f.readline()
            send(s, dict(consult, r=[[0, 17, 0]]))
            line = f.readline()
        time.sleep(0.3)
    finally:
        threading.excepthook = old_hook
    check("EDGERANGE", line == b"" and len(seen3) == 1,
          "edge into a padding slot: reply=%r raised=%s" % (line, seen3))


def main():
    t0 = time.time()
    test_pooling()
    test_collision()
    test_permutation()
    test_r0()
    test_masking()
    test_validation()
    test_train_and_ckpt()
    test_loopback()
    print("ENTATTN|checks=%d|failures=%d|%.1fs"
          % (len(RAN), len(FAILURES), time.time() - t0), flush=True)
    if FAILURES:
        print("FAILED: " + ", ".join(FAILURES))
        sys.exit(1)


if __name__ == "__main__":
    main()
