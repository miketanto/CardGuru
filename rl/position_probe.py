"""Ask a trained policy what it would do in a CONSTRUCTED position.

WHY THIS EXISTS
The v2 agent declines 39% of block opportunities where correct play
declines 18%. Two readings: it learned WHEN not to block, or it learned
"don't block" and is over-applying it. Game transcripts cannot separate
those, because the positions that would separate them - block or die,
and piling is mandatory - occur rarely and never on demand.

So construct them. This builds the encoder's state and candidate vectors
directly from a described board and asks the policy server, with no
engine in the loop.

FAITHFULNESS IS THE WHOLE RISK, AND IS TESTED
The vectors here are a Python re-implementation of StateEncoder, so they
can silently drift from the Java. `--validate` replays positions taken
from real committed transcripts and checks the policy's answer matches
what the agent actually did in that game. A probe that fails validation
is measuring its own encoding bug, not the agent.

Run: python3 rl/position_probe.py --port 7995 [--validate]
"""
import argparse
import json
import socket

SDIM, CDIM = 32, 94        # encoder v2
ID_BASE = 25
FEAT_DIM = 68              # e2_features.tsv
T_PASS, T_BLOCK = 0, 5

FEATURES = {}


def load_features(path="/home/user/CardGuru/rl/e2_features.tsv"):
    with open(path) as fh:
        fh.readline()
        for line in fh:
            if "\t" not in line:
                continue
            name, vec = line.rstrip("\n").split("\t", 1)
            FEATURES[name] = [float(x) for x in vec.split(",")]


def identity(c, name):
    v = FEATURES.get(name)
    if v is None:
        c[ID_BASE + FEAT_DIM] = 1.0
    else:
        c[ID_BASE:ID_BASE + FEAT_DIM] = v


class Pos:
    """A declare-blockers position, described in plain terms."""

    def __init__(self, my_life, opp_life, attackers, blockers,
                 my_lands=5, opp_lands=5, turn=10, my_hand=2, opp_hand=2):
        self.my_life, self.opp_life = my_life, opp_life
        self.attackers = attackers          # [(name, power, toughness)]
        self.blockers = blockers            # [(name, power, toughness)]
        self.my_lands, self.opp_lands = my_lands, opp_lands
        self.turn, self.my_hand, self.opp_hand = turn, my_hand, opp_hand

    def state(self, assigned):
        """assigned: {attacker_index: [blocker indices already declared]}"""
        s = [0.0] * SDIM
        s[0] = self.my_life / 20
        s[1] = self.opp_life / 20
        s[2] = self.my_hand / 10
        s[3] = self.opp_hand / 10
        s[4] = self.my_lands / 10          # defender is untapped on their turn
        s[5] = self.my_lands / 10
        s[6] = 0.0                         # attacker tapped out to attack
        s[7] = self.opp_lands / 10
        s[8] = len(self.blockers) / 10
        s[9] = len(self.attackers) / 10
        s[10] = sum(p for _, p, _ in self.blockers) / 20
        s[11] = sum(t for _, _, t in self.blockers) / 20
        s[12] = sum(p for _, p, _ in self.attackers) / 20
        s[13] = sum(t for _, _, t in self.attackers) / 20
        s[14] = self.turn / 30
        s[15] = 0.0                        # not my turn
        s[17] = 1.0                        # combat step
        s[23] = 40 / 60                    # library, roughly mid-game
        # combat block, s[24..28]
        unblocked = [i for i in range(len(self.attackers))
                     if not assigned.get(i)]
        s[24] = len(self.attackers) / 6
        s[25] = len(unblocked) / 6
        up = sum(self.attackers[i][1] for i in unblocked)
        s[26] = up / 20
        s[27] = (self.my_life - up) / 20
        free = len(self.blockers) - sum(len(v) for v in assigned.values())
        s[28] = free / 6
        return s

    def cand_block(self, ai, bi, assigned):
        c = [0.0] * CDIM
        c[T_BLOCK] = 1.0
        an, ap, at = self.attackers[ai]
        bn, bp, bt = self.blockers[bi]
        c[7] = ap / 6
        c[8] = at / 6
        c[9] = 1.0
        already = assigned.get(ai, [])
        c[17] = len(already) / 3
        c[18] = bp / 6
        c[19] = bt / 6
        c[20] = 1.0 if bp >= at else 0.0
        c[21] = 1.0 if ap >= bt else 0.0
        apow = sum(self.blockers[x][1] for x in already)
        atou = sum(self.blockers[x][2] for x in already)
        c[22] = min(1.0, apow / max(1, at))
        c[23] = 1.0 if apow >= at else 0.0
        c[24] = 1.0 if atou >= ap else 0.0
        identity(c, an)
        return c

    def cand_pass(self):
        c = [0.0] * CDIM
        c[T_PASS] = 1.0
        return c


class Policy:
    def __init__(self, port):
        self.sock = socket.create_connection(("127.0.0.1", port))
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.f = self.sock.makefile("rwb")
        self.f.write(json.dumps({"t": "hello", "mode": "eval", "episodes": 1,
                                 "sdim": SDIM, "cdim": CDIM, "phi": 0}).encode()
                     + b"\n")
        self.f.flush()
        self.f.readline()

    def choose(self, state, cands):
        self.f.write(json.dumps({"t": "consult", "s": state, "c": cands,
                                 "phi": 0.0}).encode() + b"\n")
        self.f.flush()
        return json.loads(self.f.readline())["a"]


# --- CombatMath, Python port, so the probe prints the reference answer
# next to the policy's rather than leaving the reader to do the maths.
def _resolve(attackers, blockers, assign, life):
    dmg = akill = aval = blost = bval = 0
    for a, (an, ap, at) in enumerate(attackers):
        mine = [blockers[b] for b in range(len(blockers)) if assign[b] == a]
        if not mine:
            dmg += ap
            continue
        if sum(p for _, p, _ in mine) >= at:
            akill += 1
            aval += ap + at
        left = ap
        for bn, bp, bt in sorted(mine, key=lambda x: x[2]):
            if left >= bt:
                left -= bt
                blost += 1
                bval += bp + bt
    return dict(dmg=dmg, akill=akill, aval=aval, blost=blost, bval=bval,
                dead=dmg >= life)


def _score(o, total):
    if o["dead"]:
        return -10 ** 9
    return 2 * (total - o["dmg"]) + 3 * o["aval"] - 3 * o["bval"]


def solver_best(pos):
    import itertools
    total = sum(p for _, p, _ in pos.attackers)
    best, bs = None, -10 ** 18
    for assign in itertools.product(range(-1, len(pos.attackers)),
                                    repeat=len(pos.blockers)):
        sc = _score(_resolve(pos.attackers, pos.blockers, assign,
                             pos.my_life), total)
        if sc > bs:
            bs, best = sc, assign
    return best, bs


def run_position(pol, pos, label):
    """Replay the engine's per-blocker loop: body order, conditioned."""
    order = sorted(range(len(pos.blockers)),
                   key=lambda i: (pos.blockers[i][2], pos.blockers[i][1],
                                  pos.blockers[i][0]))
    assigned = {}
    picks = []
    for bi in order:
        cands = [pos.cand_pass()]
        idx = []
        for ai in range(len(pos.attackers)):
            cands.append(pos.cand_block(ai, bi, assigned))
            idx.append(ai)
        a = pol.choose(pos.state(assigned), cands)
        if a == 0:
            picks.append((pos.blockers[bi][0], None))
        else:
            ai = idx[a - 1]
            assigned.setdefault(ai, []).append(bi)
            picks.append((pos.blockers[bi][0], pos.attackers[ai][0]))
    print("== %s" % label)
    print("   life %d, attackers %s, blockers %s"
          % (pos.my_life,
             ", ".join("%s %d/%d" % a for a in pos.attackers),
             ", ".join("%s %d/%d" % b for b in pos.blockers)))
    for who, target in picks:
        print("     %-26s -> %s" % (who, target or "DECLINE"))
    best, bs = solver_best(pos)
    print("   solver best:")
    for bi, ai in enumerate(best):
        print("     %-26s -> %s"
              % (pos.blockers[bi][0],
                 pos.attackers[ai][0] if ai >= 0 else "DECLINE"))
    total = sum(p for _, p, _ in pos.attackers)
    got = [-1] * len(pos.blockers)
    for ai, bis in assigned.items():
        for bi in bis:
            got[bi] = ai
    gs = _score(_resolve(pos.attackers, pos.blockers, got, pos.my_life), total)
    print("   policy score %d   solver score %d   %s"
          % (gs, bs, "MATCH" if gs >= bs else "SUBOPTIMAL"))
    return assigned, picks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7995)
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    load_features()
    pol = Policy(args.port)

    if args.validate:
        # From game_v2_ck1024_vs_D0_seed6001.txt, t10: agent blocked the
        # 2/1 with Blade of the Sixth Pride and DECLINED the other two.
        run_position(pol, Pos(
            my_life=20, opp_life=17,
            attackers=[("Elite Vanguard", 2, 1)],
            blockers=[("Blade of the Sixth Pride", 3, 1),
                      ("Glory Seeker", 2, 2),
                      ("Silvercoat Lion", 2, 2)],
            turn=10), "VALIDATE t10 (expect: one block, two declines)")
        return

    # THE CONSTRUCTED TEST. Agent at 3 life, one 3/3 attacking, three 2/2s.
    #   decline everything -> 3 damage -> dead
    #   one blocker        -> survive, blocker dies (3>=2), attacker lives (2<3)
    #   TWO blockers       -> survive, attacker DIES (4>=3), one blocker dies
    # So double-blocking is strictly correct and the agent has a spare.
    run_position(pol, Pos(
        my_life=3, opp_life=12,
        attackers=[("Shu Elite Infantry", 3, 3)],
        blockers=[("Glory Seeker", 2, 2), ("Silvercoat Lion", 2, 2),
                  ("Fresh Volunteers", 2, 2)],
        turn=14), "MUST DOUBLE BLOCK (3 life, 3/3 attacker, three 2/2s)")

    # TWO attackers, BOTH needing a double block from 2/2s, one bigger.
    # Shu Elite Infantry 3/3 and Regal Unicorn 2/3 each survive a single
    # 2/2 (2 < 3) and die to two (4 >= 3). With only three blockers the
    # agent can double exactly one, so it must RANK the threats rather
    # than apply a threshold.
    run_position(pol, Pos(
        my_life=10, opp_life=12,
        attackers=[("Shu Elite Infantry", 3, 3), ("Regal Unicorn", 2, 3)],
        blockers=[("Glory Seeker", 2, 2), ("Silvercoat Lion", 2, 2),
                  ("Fresh Volunteers", 2, 2)],
        turn=14), "RANK: two attackers both needing a double, three blockers")

    # Same two attackers, but FOUR blockers - enough to double both. If
    # the policy blocks here and not with three, the failure is about
    # RANKING under scarcity; if it declines here too, the failure is
    # about COMMITTING a first blocker at all when a second is needed.
    run_position(pol, Pos(
        my_life=10, opp_life=12,
        attackers=[("Shu Elite Infantry", 3, 3), ("Regal Unicorn", 2, 3)],
        blockers=[("Glory Seeker", 2, 2), ("Silvercoat Lion", 2, 2),
                  ("Fresh Volunteers", 2, 2), ("Knight Errant", 2, 2)],
        turn=14), "RANK+1: same two attackers, FOUR blockers")

    # Control: same board, comfortable life. Blocking is now optional and
    # declining is defensible, so a difference between these two says the
    # policy is reading life rather than pattern-matching the board.
    run_position(pol, Pos(
        my_life=20, opp_life=12,
        attackers=[("Shu Elite Infantry", 3, 3)],
        blockers=[("Glory Seeker", 2, 2), ("Silvercoat Lion", 2, 2),
                  ("Fresh Volunteers", 2, 2)],
        turn=14), "CONTROL: identical board at 20 life")


if __name__ == "__main__":
    main()
