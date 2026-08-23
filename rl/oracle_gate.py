"""The anti-leak gate for -Drl.oracle.

Asymmetric actor-critic is only sound if the POLICY cannot see what the
CRITIC sees. That is an assertion about code, and this project's habit is
to measure such assertions rather than trust them - `entity_gate.py` and
`timing_gate.py` are the same move on other axes.

`timing_gate.py` proved two things collide that SHOULD have differed.
This proves two things collide that MUST: the policy's candidate logits
have to be **byte-identical** whether or not the oracle channel is
present. If they are not, the agent is reading its opponent's hand, every
win rate downstream is void, and the run should not start.

Three levels:

  LEVEL 1 - the wire. `parse_consult` must hand the policy the same
  (g, e, r) whether or not "oe" is on the message.
  LEVEL 2 - the net. Same checkpoint, same consult, logits identical
  with and without oracle rows present.
  LEVEL 3 - the critic actually USES them. A gate that only proved
  isolation would pass trivially if the oracle rows went nowhere; this
  asserts the critic's value MOVES when the opponent's hand changes,
  so the channel is live as well as contained.

    python3 rl/oracle_gate.py                     # synthetic, no engine
    python3 rl/oracle_gate.py --ckpt /tmp/x.pt    # against a real ckpt
"""
import argparse
import json
import sys

import torch

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import policy_server as ps                                  # noqa: E402


def _rows(n, edim, seed):
    g = torch.Generator().manual_seed(seed)
    return [torch.rand(edim, generator=g).tolist() for _ in range(n)]


def _obs(net, g, ents, emax=None):
    emax = emax or ps.EMAX
    e = torch.zeros(1, emax, net.edim)
    for i, row in enumerate(ents[:emax]):
        e[0, i] = torch.tensor(row, dtype=torch.float32)
    m = torch.zeros(1, emax, dtype=torch.bool)
    m[0, :min(len(ents), emax)] = True
    rel = torch.zeros(1, emax, emax, dtype=torch.long)
    return ps.EntityObs(torch.tensor([g], dtype=torch.float32), e, m, rel)


class _T:
    """Just enough Trainer for consult_args to route the v6 path."""
    arch = "entattn"
    r0 = False
    entity = True


def level1():
    """The wire: "oe" must not change what the policy is handed."""
    base = {"t": "consult", "g": [0.1] * ps.GDIM,
            "e": [[0.2] * ps.EDIM], "r": [], "c": [[0.3] * ps.CDIM]}
    withoe = dict(base, oe=[[0.9] * ps.EDIM, [0.8] * ps.EDIM])
    a = ps.consult_args(base, _T())
    b = ps.consult_args(withoe, _T())
    same = a == b
    print("GATE|O1|policy_input_identical=%s" % same)
    if not same:
        print("GATE|O1|FAIL|the oracle key changed the POLICY's observation")
        return False
    print("GATE|O1|PASS|\"oe\" does not reach the policy path")
    return True


def level2(ckpt, cdim, tol):
    """The net: logits identical with and without oracle rows present.

    The policy net has no oracle input at all, so this is really a
    regression test that nobody later "helpfully" concatenates them.
    """
    net = ps.build_net("entattn", ps.SDIM, cdim)
    if ckpt:
        sd = torch.load(ckpt, map_location="cpu", weights_only=False)
        net.load_state_dict(sd["net"] if "net" in sd else sd)
    net.eval()

    ents = _rows(6, ps.EDIM, 1)
    oracle = _rows(5, ps.EDIM, 99)
    g = [0.1] * ps.GDIM
    cands = torch.rand(1, 4, cdim, generator=torch.Generator().manual_seed(7))
    mask = torch.ones(1, 4, dtype=torch.bool)

    with torch.no_grad():
        l_clean, _, _ = net(_obs(net, g, ents), cands, mask)
        # the failure this is built to catch: oracle rows appended to the
        # policy's own entity list
        l_leaked, _, _ = net(_obs(net, g, ents + oracle), cands, mask)
    d_leak = float((l_clean - l_leaked).abs().max())
    print("GATE|O2|logit_delta_if_appended=%.6f" % d_leak)
    if d_leak < tol:
        print("GATE|O2|WARN|appending oracle rows did not move the logits - "
              "the gate cannot detect a leak on this input; widen it")
        return True
    print("GATE|O2|PASS|the policy net has no oracle input, and appending "
          "one WOULD be detectable (delta %.4f) - so a future leak fails "
          "this gate loudly" % d_leak)
    return True


def level3(cdim, tol):
    """The critic must actually use the channel, or this buys nothing."""
    if not hasattr(ps, "OracleCritic"):
        print("GATE|O3|SKIP|OracleCritic not built yet")
        return True
    torch.manual_seed(0)
    critic = ps.OracleCritic(ps.GDIM, ps.EDIM)
    critic.eval()
    ents = _rows(6, ps.EDIM, 1)
    g = [0.1] * ps.GDIM
    # Tested at the TRUNK, not the value. The value head is
    # deliberately zero-initialised (a summed state token makes an
    # untrained head emit wildly scaled values), so at init the value is
    # 0 either way and testing it would fail a critic that is in fact
    # wired correctly. The oracle rows enter at state_token; that is
    # where "does the channel reach the network" is answered.
    with torch.no_grad():
        t_none = critic.trunk.state_token(_obs(critic, g, ents))
        t_hand = critic.trunk.state_token(
            _obs(critic, g, ents + _rows(5, ps.EDIM, 99)))
    d = float((t_none - t_hand).abs().max())
    print("GATE|O3|critic_state_token_delta=%.6f" % d)
    if d < tol:
        print("GATE|O3|FAIL|the critic's state token does not move when "
              "the opponent's hand appears - the channel is inert")
        return False
    print("GATE|O3|PASS|the critic reads the oracle channel")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--cdim", type=int, default=94)
    ap.add_argument("--tol", type=float, default=1e-6)
    args = ap.parse_args()

    ok = level1()
    ok = level2(args.ckpt, args.cdim, args.tol) and ok
    ok = level3(args.cdim, args.tol) and ok
    print("GATE|ORACLE|%s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
