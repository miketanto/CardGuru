"""§5b's collision gate, on REAL emission.

ENCODER-V6-BUILD.md §5b asks whether boards that are ONE vector under
the v1-v5 encoder are distinct vectors under v6. `entattn_check.py`
answers the network half of that on synthetic rows; this answers it on
positions the engine actually produced, which is the question that
matters, because the collision rate is a property of the card pool and
the emitter rather than of the pooling operator.

Input: the JSONL written by -Drl.entityDump=<file> (StateEncoder), one
line per consult: {"g":[...],"e":[[...]],"r":[[s,d,t]],"v5":[...]}.

    python3 rl/entity_gate.py                    # committed fixture
    python3 rl/entity_gate.py /tmp/v6_gate.jsonl  # a fresh dump

The fixture is 1983 consults from 40 rung-0 W0Base games
(rl/artifacts/v6/), committed gzipped so this gate re-runs anywhere
torch does - the engine takes 15 minutes to rebuild and the gate
should not be hostage to it.

WHAT IT MEASURES
  1. v5 collision groups: sets of positions whose v5 state vector is
     byte-identical. This is the baseline harm, measured on this run's
     positions rather than quoted from §6c.
  2. Within each group, whether the ENTITY ROWS differ - i.e. whether
     the emitter carries information v5 threw away.
  3. Whether EntityAttnPolicy then maps those rows to different state
     embeddings. A separation that exists in the rows but vanishes in
     the pool would be the pooling bug this whole effort exists to
     avoid, and it is checked rather than assumed.

WHAT IT IS NOT. Not a win rate, not an audit number, and not evidence
about attack- or block-optimality, which §0 says cannot move from a
state-path change. It is a statement about what the agent can SEE.
"""
import argparse
import gzip
import json
import os
import sys

import torch

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import policy_server as ps                                  # noqa: E402


DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "artifacts/v6/gate_positions_W0Base_40g.jsonl.gz")


def load(path):
    out, bad = [], []
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as f:
        for n, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                bad.append((n, str(exc)))
    if bad:
        # a live driver can leave the last line half-written; anything
        # EARLIER than that is a real corruption and is not skipped
        # quietly, because a gate that silently drops its input is
        # measuring whatever survived
        print("GATE|skipped_unparseable_lines=%d|%s"
              % (len(bad), "; ".join("line %d: %s" % b for b in bad[:3])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump", nargs="?", default=DEFAULT,
                    help="entity dump (.jsonl or .jsonl.gz). Defaults to "
                         "the committed 40-game W0Base fixture, so the "
                         "gate is runnable with torch alone - no engine, "
                         "no Java, no rebuild.")
    ap.add_argument("--emax", type=int, default=ps.EMAX)
    ap.add_argument("--tol", type=float, default=1e-4,
                    help="two embeddings closer than this count as one")
    args = ap.parse_args()

    rows = load(args.dump)
    if not rows:
        print("GATE|FAIL|empty dump")
        sys.exit(1)

    tr = ps.Trainer(None, 0, None, cdim=94, arch="entattn", emax=args.emax)
    net = tr.net

    # 1. group by the v5 vector
    groups = {}
    for r in rows:
        groups.setdefault(tuple(r["v5"]), []).append(r)
    multi = {k: v for k, v in groups.items() if len(v) > 1}

    # 2. within a group, how many DISTINCT entity emissions are there?
    #    (sorted rows, so a permutation is not counted as a difference -
    #    the pool is order-invariant and calling a reorder a "separation"
    #    would be cheating)
    def board_key(r):
        return tuple(sorted(tuple(row) for row in r["e"]))

    collided = separated_rows = 0
    pairs = []
    for key, members in multi.items():
        boards = {}
        for m in members:
            boards.setdefault(board_key(m), m)
        if len(boards) > 1:
            collided += 1
            separated_rows += 1
            vs = list(boards.values())
            for i in range(len(vs)):
                for j in range(i + 1, len(vs)):
                    pairs.append((vs[i], vs[j]))

    print("GATE|positions=%d|distinct_v5=%d|v5_groups_with_2plus=%d"
          % (len(rows), len(groups), len(multi)))
    print("GATE|v5_groups_hiding_different_boards=%d|pairs=%d"
          % (collided, len(pairs)))

    if not pairs:
        # Not a pass and not a failure: this run's positions never
        # produced two different boards with the same v5 vector, so the
        # gate had nothing to test. Say that, rather than printing PASS.
        print("GATE|INCONCLUSIVE|no v5 collision between DIFFERENT boards "
              "in this dump - collect more positions (longer games, a "
              "trained agent, more episodes) before reading anything")
        sys.exit(2)

    # 3. do the embeddings separate?
    def embed(r):
        obs = tr._entity_obs(r["g"], r["e"], r["r"])
        with torch.no_grad():
            return net.state_token(obs)

    worst = None
    fails = 0
    for a, b in pairs:
        d = float((embed(a) - embed(b)).abs().max())
        worst = d if worst is None else min(worst, d)
        if d < args.tol:
            fails += 1
    print("GATE|embedding_separation|pairs=%d|closest=%.6f|below_tol=%d"
          % (len(pairs), worst, fails))
    if fails:
        print("GATE|FAIL|%d v5-identical pairs are still identical under v6"
              % fails)
        sys.exit(1)
    print("GATE|PASS|every v5-identical pair with different boards is a "
          "different v6 embedding")


if __name__ == "__main__":
    main()
