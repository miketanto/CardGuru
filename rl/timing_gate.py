"""HANDOFF-STACK-TIMING.md §2a's collision gate, on the TIMING axis.

`entity_gate.py` asks whether boards that were one vector under v5 are
distinct vectors under v6. This asks the same question one axis over:
**is the same card, castable in my own main phase and in the opponent's
declare-attackers step, the same candidate vector?** If it is, the
candidate channel carries no timing information at all.

Two levels, because one of them alone would overclaim.

  LEVEL A - the candidate rows. Group real emission by card name, split
  by step, and report the minimum within-card cross-step distance. This
  is the test §2a specifies.

  LEVEL B - everything downstream. A collision in LEVEL A does NOT by
  itself mean the policy cannot represent a timing decision, because
  the candidate row is not the whole observation: the v6 globals carry
  the step (g[1] active-player, g[2..7] the step one-hot, with
  DECLARE_ATTACKERS its own bucket g[3]), the state token is
  glob_in(g) + pool(entities), and every candidate attends to that
  token before it is scored. So LEVEL B measures whether the step
  actually moves a candidate's LOGIT, which is the question "can it
  represent a timing decision" really asks.

Reporting A without B would repeat the error the ground rules exist to
prevent: stating a conclusion the number cannot support.

    python3 rl/timing_gate.py                      # LEVEL B only (no engine)
    python3 rl/timing_gate.py /tmp/cand_dump.jsonl # both levels

Input for LEVEL A is the JSONL written by -Drl.candDump (RLPlayer), one
line per priority consult:
    {"site","turn","step","active","names":[...],"cands":[[...]],"state":[...]}

WHAT IT IS NOT. Not a win rate, not evidence about attack- or
block-optimality, and not a claim that any particular policy DOES use
the step - only about what it CAN see and CAN score.
"""
import argparse
import gzip
import json
import os
import sys

import torch

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import policy_server as ps                                  # noqa: E402


# PhaseStep.toString() is a DISPLAY name ("Declare Attackers"), not the
# enum constant, so both spellings are accepted rather than one guessed.
MAIN_STEPS = {"PRECOMBAT_MAIN", "POSTCOMBAT_MAIN",
              "Precombat Main", "Postcombat Main"}
# the step §2a names. DECLARE_BLOCKERS is kept separate rather than
# folded in: it is a different decision (the attack is already known)
# and folding it would inflate the pair count with easier pairs.
ATK_STEPS = {"DECLARE_ATTACKERS", "Declare Attackers"}


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
        # EARLIER than that is real corruption and is not skipped
        # quietly, for the reason entity_gate.py gives
        print("GATE|skipped_unparseable_lines=%d|%s"
              % (len(bad), "; ".join("line %d: %s" % b for b in bad[:3])))
    return out


def bucket(row):
    """own-main / opp-declare-attackers / None, from one consult."""
    step, active = row.get("step"), row.get("active")
    if active == 1 and step in MAIN_STEPS:
        return "own_main"
    if active == 0 and step in ATK_STEPS:
        return "opp_declare_attackers"
    return None


def level_a_wide(rows, tol):
    """The same question, on every step a card was actually offered in.

    The §2a pair (own main vs opp declare-attackers) is the sharpest
    form of the question but the rarest in real emission: the agent
    reaches an opponent declare-attackers window with something castable
    about once in a hundred windows, so a dump large enough to catch a
    given REMOVAL SPELL there is expensive. This asks the weaker-looking
    but far better-powered version - is a card's candidate row the same
    in EVERY step it was offered in? - and gets Cruel Cut, the card the
    ladder rung is built around, into the answer.

    A card with N>1 steps and exactly 1 distinct row is step-invariant
    on the evidence. Distinct rows are reported rather than asserted
    away: a creature whose power changed would legitimately emit two.
    """
    per = {}
    for r in rows:
        if r.get("site") != "prio":
            continue
        key = ("own" if r["active"] == 1 else "opp") + " " + r["step"]
        for name, cand in zip(r["names"], r["cands"]):
            if name == "PASS":
                continue
            per.setdefault(name, {}).setdefault(key, set()).add(tuple(cand))

    multi = {k: v for k, v in per.items() if len(v) > 1}
    print("GATE|AW|cards=%d|cards_seen_in_2plus_steps=%d" % (len(per), len(multi)))
    invariant = 0
    for name, steps in sorted(multi.items()):
        rowset = set().union(*steps.values())
        flag = "STEP-INVARIANT" if len(rowset) == 1 else "varies"
        if len(rowset) == 1:
            invariant += 1
        print("GATE|AW|card=%-20s|steps=%-3d|distinct_rows=%d|%s"
              % (name[:20], len(steps), len(rowset), flag))
    if multi:
        print("GATE|AW|step_invariant=%d/%d cards" % (invariant, len(multi)))
    return invariant, len(multi)


def _census(rows):
    """How often does an instant-speed window even EXIST?

    LEVEL A can only compare cards it saw at both steps, so the number
    of opponent-turn declare-attackers windows that carried anything
    castable is the ceiling on its evidence - and a finding in its own
    right. k=0 windows never reach a consult, so dumpCands alone cannot
    see them.
    """
    win = [r for r in rows if r.get("site") == "window"]
    if not win:
        return
    atk = [r for r in win if r["active"] == 0 and r["step"] in ATK_STEPS]
    if not atk:
        return
    live = [r for r in atk if r["k"] > 0]
    held = [r for r in atk if r["holds_instant"] == 1]
    print("GATE|WINDOWS|priority_windows=%d|opp_declare_attackers=%d|"
          "with_castable=%d (%.1f%%)|holding_an_instant=%d (%.1f%%)"
          % (len(win), len(atk), len(live), 100.0 * len(live) / len(atk),
             len(held), 100.0 * len(held) / len(atk)))
    print("GATE|WINDOWS|held an instant but could not cast it: %d/%d - "
          "the gap is MANA, not the encoder"
          % (len(held) - len([r for r in live if r["holds_instant"] == 1]),
             len(held)))


def level_a(rows, tol):
    """The §2a test: same card, two steps, are the rows distinct?"""
    # card name -> bucket -> set of candidate rows seen for that card
    seen = {}
    n_used = 0
    for r in rows:
        if r.get("site") != "prio":
            continue            # window-census lines carry no candidates
        b = bucket(r)
        if b is None:
            continue
        n_used += 1
        for name, cand in zip(r["names"], r["cands"]):
            if name == "PASS":
                continue            # not a card; its row is blank(T_PASS)
            seen.setdefault(name, {}).setdefault(b, set()).add(tuple(cand))

    _census(rows)
    both = {k: v for k, v in seen.items() if len(v) == 2}
    print("GATE|A|consults=%d|in_scope=%d|cards=%d|cards_in_both_steps=%d"
          % (len(rows), n_used, len(seen), len(both)))

    if not both:
        # Not a pass and not a failure: this dump never showed one card
        # at both steps, so the gate had nothing to compare. Say that
        # rather than printing a verdict.
        print("GATE|A|INCONCLUSIVE|no card appeared as a candidate in BOTH "
              "own-main and opp-declare-attackers in this dump - collect "
              "more (an instant deck, more games, a policy that reaches "
              "opponent-turn priority) before reading anything")
        return None

    worst, worst_card, pairs, collided = None, None, 0, 0
    for name, buckets in sorted(both.items()):
        a = [torch.tensor(x) for x in buckets["own_main"]]
        b = [torch.tensor(x) for x in buckets["opp_declare_attackers"]]
        best = None
        for x in a:
            for y in b:
                pairs += 1
                d = float((x - y).abs().max())
                best = d if best is None else min(best, d)
        if best is not None and best < tol:
            collided += 1
        print("GATE|A|card=%-24s|own_main_rows=%d|opp_atk_rows=%d|min_dist=%.6f"
              % (name[:24], len(a), len(b), best))
        if worst is None or best < worst:
            worst, worst_card = best, name

    print("GATE|A|pairs=%d|min_cross_step_distance=%.6f|on=%s|colliding_cards=%d/%d"
          % (pairs, worst, worst_card, collided, len(both)))
    if collided:
        print("GATE|A|COLLIDE|%d/%d cards have a byte-identical candidate row "
              "in own-main and opp-declare-attackers - the candidate channel "
              "carries NO timing information" % (collided, len(both)))
    else:
        print("GATE|A|PASS|every card's candidate row differs across the "
              "two steps")
    return worst


def _obs(net, g, ents, rels, emax=None):
    """globals + entity rows + edge list -> a batch-1 EntityObs."""
    emax = emax or ps.EMAX
    e = torch.zeros(1, emax, net.edim)
    for i, row in enumerate(ents):
        e[0, i] = torch.tensor(row, dtype=torch.float32)
    m = torch.zeros(1, emax, dtype=torch.bool)
    m[0, :len(ents)] = True
    rel = torch.zeros(1, emax, emax, dtype=torch.long)
    for s, d, t in rels:
        rel[0, s, d] = t + 1
    return ps.EntityObs(torch.tensor([g], dtype=torch.float32), e, m, rel)


def _globals(step, gdim=ps.GDIM):
    """A v6 globals vector at one step, everything else held equal.

    Mirrors StateEncoder.encodeGlobals: g[1] active-player, g[2] main,
    g[3] DECLARE_ATTACKERS. Only those channels differ between the two
    calls, which is what makes this a controlled comparison.
    """
    g = [0.0] * gdim
    g[0] = 5 / 30.0            # turn 5
    if step == "own_main":
        g[1], g[2] = 1.0, 1.0
    elif step == "opp_declare_attackers":
        g[1], g[3] = 0.0, 1.0
    else:
        raise ValueError(step)
    g[8], g[9] = 1.0, 1.0      # both at 20 life
    g[10] = 40 / 60.0
    return g


def level_b(seeds, cdim, tol):
    """Does the STEP move a candidate's logit, holding all else equal?

    The decision §2a is about is "cast this instant now, or hold it",
    which is the sign of logit(spell) - logit(PASS). So that difference,
    not a raw logit, is what gets measured.

    A random-init net is the right instrument here: the question is
    whether the architecture ROUTES the step to the score at all. A
    trained net could hide a live path behind learned indifference, and
    would answer a different question (does THIS policy use it).
    """
    # one creature each side, so the board is not degenerate
    def ent(mine, power, tough):
        r = [0.0] * ps.EDIM
        r[0] = 1.0
        r[1 if mine else 2] = 1.0
        r[44], r[45] = power / 6.0, tough / 6.0
        return r

    ents = [ent(True, 2, 2), ent(False, 2, 1)]
    rels = []

    # candidates: PASS, and an instant that is a legal play in both
    # steps. Both rows are step-invariant by construction - that is
    # LEVEL A's finding - so any logit movement comes from the state.
    def cand(kind):
        c = [0.0] * cdim
        if kind == "pass":
            c[0] = 1.0
        else:
            c[2] = 1.0             # T_SPELL
            c[6] = 2 / 6.0         # {1}{B}
            c[10] = 1.0            # isInstant
            c[20] = 1.0            # a name-hash bucket
        return c

    cands = [cand("pass"), cand("instant")]

    gaps, per_seed, board = [], [], []
    for s in seeds:
        torch.manual_seed(s)
        net = ps.build_net("entattn", ps.SDIM, cdim)
        net.eval()
        ct = torch.tensor([cands], dtype=torch.float32)
        mask = torch.ones(1, len(cands), dtype=torch.bool)

        out = {}
        for step in ("own_main", "opp_declare_attackers"):
            obs = _obs(net, _globals(step), ents, rels)
            with torch.no_grad():
                logits, _, _ = net(obs, ct, mask)
            out[step] = float(logits[0, 1] - logits[0, 0])   # spell - PASS

        # SCALE REFERENCE. A nonzero delta proves a live path, but not
        # that the path is a strong one, and "nonzero" alone invites
        # reading 0.01 as meaningful. So the same margin is measured
        # under a BOARD change of comparable crudeness - one extra enemy
        # creature - and the two are printed together. Neither number
        # bounds what training can reach; they say what the untrained
        # net's sensitivities look like relative to each other.
        obs2 = _obs(net, _globals("own_main"),
                    ents + [ent(False, 3, 3)], rels)
        with torch.no_grad():
            l2, _, _ = net(obs2, ct, mask)
        board_gap = abs(float(l2[0, 1] - l2[0, 0]) - out["own_main"])

        gap = abs(out["own_main"] - out["opp_declare_attackers"])
        board.append(board_gap)
        gaps.append(gap)
        per_seed.append((s, out["own_main"],
                         out["opp_declare_attackers"], gap))

    for s, a, b, gap in per_seed:
        print("GATE|B|seed=%d|cast_minus_pass own_main=%+.5f "
              "opp_atk=%+.5f|delta=%.5f" % (s, a, b, gap))

    lo, hi = min(gaps), max(gaps)
    bl, bh = min(board), max(board)
    print("GATE|B|scale_reference|one_extra_enemy_creature moves the same "
          "margin by %.6f-%.6f, vs %.6f-%.6f for the step"
          % (bl, bh, lo, hi))
    dead = sum(1 for g in gaps if g < tol)
    print("GATE|B|seeds=%d|delta_min=%.6f|delta_max=%.6f|below_tol=%d"
          % (len(gaps), lo, hi, dead))
    if dead == len(gaps):
        print("GATE|B|FAIL|the step never moves the cast-vs-hold margin - "
              "the observation cannot express a timing decision")
        return lo, False
    print("GATE|B|PASS|the step moves the cast-vs-hold margin at every "
          "seed - the step reaches the candidate logits through the "
          "state token, so a timing decision IS representable")
    return lo, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dump", nargs="?", default=None,
                    help="candidate dump from -Drl.candDump (.jsonl[.gz]). "
                         "Omit to run LEVEL B only, which needs torch "
                         "alone - no engine, no Java, no rebuild.")
    ap.add_argument("--tol", type=float, default=1e-6,
                    help="two rows closer than this count as one")
    ap.add_argument("--cdim", type=int, default=None,
                    help="candidate width; inferred from the dump if given")
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    a_min = None
    cdim = args.cdim
    if args.dump:
        if not os.path.exists(args.dump):
            print("GATE|FAIL|no such dump: %s" % args.dump)
            sys.exit(1)
        rows = load(args.dump)
        if not rows:
            print("GATE|FAIL|empty dump")
            sys.exit(1)
        if cdim is None:
            cdim = next(len(r["cands"][0]) for r in rows if r.get("cands"))
        a_min = level_a(rows, args.tol)
        level_a_wide(rows, args.tol)
    else:
        print("GATE|A|SKIPPED|no candidate dump given - run the engine with "
              "-Drl.candDump=<file> to measure LEVEL A on real emission")
        cdim = cdim or ps.CDIM

    print("GATE|B|cdim=%d" % cdim)
    _, expressible = level_b(range(args.seeds), cdim, args.tol)

    # the joint reading, stated here so it cannot be quoted half-way
    print("GATE|VERDICT|level_a_min=%s|expressible=%s"
          % ("n/a" if a_min is None else "%.6f" % a_min, expressible))
    if a_min is not None and a_min < args.tol and expressible:
        print("GATE|VERDICT|The candidate channel is timing-blind (LEVEL A "
              "distance 0) but the observation is NOT: the step reaches the "
              "logits through the state token (LEVEL B). §2a's collision "
              "holds; its 'no amount of training can learn the difference' "
              "does NOT follow.")
        sys.exit(3)          # distinct from 0/1: collided, still expressible
    if a_min is not None and a_min < args.tol:
        print("GATE|VERDICT|FAIL|collided AND not expressible - §2a's "
              "stop condition is met")
        sys.exit(1)


if __name__ == "__main__":
    main()
