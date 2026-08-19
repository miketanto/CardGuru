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
T_PASS, T_ATTACK, T_BLOCK = 0, 4, 5

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

    def cand_attack(self, bi):
        """My creature bi considering an attack. Note what is NOT here:
        nothing about which of my other creatures have already been
        declared. selectAttackers has no equivalent of c[17..24] - the
        attack decision is even less conditioned than the block one."""
        c = [0.0] * CDIM
        c[T_ATTACK] = 1.0
        n, p, t = self.blockers[bi]
        c[7] = p / 6
        c[8] = t / 6
        c[9] = 1.0
        identity(c, n)
        return c

    def attack_state(self, declared, encv=2):
        """My declare-attackers step. `declared` is how many attackers I
        have already declared this combat.

        THE COMBAT CHANNELS DEPEND ON THE ENCODER VERSION and this used
        to be wrong for v3+. s[24..27] count attackers the agent does NOT
        control (the v3 controller fix); on my own turn nothing of theirs
        is attacking, so those channels are ZERO and stay zero however
        many attackers I declare. Modelling them as `declared / 6` is the
        v2 controller-blind reading, which is what this method did for
        every arm - so the earlier attack-probe runs against v4 fed it a
        state its own encoder would never produce.

        s[28] (free blockers) is untapped creatures of mine. Attacking
        taps them, but the CONSULT happens before the declaration, so at
        the moment of decision the count is my whole board minus what is
        already declared."""
        s = self.state({})
        s[15] = 1.0                 # my turn
        s[16] = 0.0
        if encv >= 3:
            s[24] = s[25] = s[26] = 0.0
            s[27] = self.my_life / 20
        else:
            s[24] = declared / 6
            s[25] = declared / 6
            s[26] = 0.0
            s[27] = self.my_life / 20
        s[28] = (len(self.blockers) - declared) / 6
        return s

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
        # toughness ascending, then VALUE DESCENDING. Sorting on toughness
        # alone is stable, so among equally-fragile blockers the one
        # earliest in the list died - which let the defender pick the
        # cheaper casualty by list order, a choice the attacking player
        # actually makes. Matches CombatMath.resolve; -Drl.legacyTieBreak
        # is the Java-side switch back and this port does not carry it,
        # so a probe against a legacy-tie-break run is not comparable.
        for bn, bp, bt in sorted(mine, key=lambda x: (x[2], -(x[1] + x[2]))):
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


def cand_assignment(pos, assign):
    """v4 candidate: the assignment described by its OUTCOME only."""
    c = [0.0] * CDIM
    c[T_BLOCK] = 1.0
    o = _resolve(pos.attackers, pos.blockers, assign, pos.my_life)
    used = sum(1 for a in assign if a >= 0)
    c[6] = o["dmg"] / 20
    c[7] = o["akill"] / 6
    c[8] = o["aval"] / 20
    c[9] = o["blost"] / 6
    c[10] = o["bval"] / 20
    c[11] = 1.0 if o["dead"] else 0.0
    c[12] = used / 6
    c[13] = (pos.my_life - o["dmg"]) / 20
    return c


def _resolve_detail(attackers, blockers, assign, life):
    """_resolve plus which blockers died - the attack side needs the
    defender's SURVIVORS to price the swing back."""
    o = _resolve(attackers, blockers, assign, life)
    died = [False] * len(blockers)
    for a in range(len(attackers)):
        idx = [b for b in range(len(blockers)) if assign[b] == a]
        if not idx:
            continue
        left = attackers[a][1]
        for b in sorted(idx, key=lambda i: (blockers[i][2],
                                            -(blockers[i][1] + blockers[i][2]))):
            if left >= blockers[b][2]:
                left -= blockers[b][2]
                died[b] = True
    return o, died


def _best_defense(sub, theirs, opp_life):
    """The defender's best reply to attack subset `sub`, by _score."""
    import itertools
    total = sum(p for _, p, _ in sub)
    best, bs = tuple([-1] * len(theirs)), -10 ** 18
    if not sub or not theirs:
        return best, bs
    for assign in itertools.product(range(-1, len(sub)), repeat=len(theirs)):
        sc = _score(_resolve(sub, theirs, assign, opp_life), total)
        if sc > bs:
            bs, best = sc, assign
    return best, bs


def _attacker_score(o):
    if o["dead"]:
        return 10 ** 9                       # lethal
    return 2 * o["dmg"] + 3 * o["bval"] - 3 * o["aval"]


def _crack_back(survivors, retained_bodies):
    powers = sorted((p for _, p, _ in survivors), reverse=True)
    return sum(powers[retained_bodies:])


def _evaluate(mine, mask, theirs, my_life, opp_life):
    """One attack subset under the defender's best reply. Mirrors
    CombatMath.evaluate; the two must agree or the probe is measuring
    its own port."""
    sub = [mine[i] for i in range(len(mine)) if mask[i]]
    home = [mine[i] for i in range(len(mine)) if not mask[i]]
    reply, _ = _best_defense(sub, theirs, opp_life)
    o, died = _resolve_detail(sub, theirs, reply, opp_life)
    survivors = [theirs[i] for i in range(len(theirs)) if not died[i]]
    op = dict(mask=mask, used=len(sub), o=o, reply=reply,
              retained_bodies=len(home),
              retained_power=sum(p for _, p, _ in home),
              retained_tough=sum(t for _, _, t in home))
    op["crack"] = _crack_back(survivors, op["retained_bodies"])
    op["score"] = _attacker_score(o)
    if o["dead"]:
        op["score_ca"] = 10 ** 9
    elif op["crack"] >= my_life:
        op["score_ca"] = -10 ** 9
    else:
        op["score_ca"] = op["score"] - 2 * op["crack"]
    return op


def _best_attack(mine, theirs, my_life, opp_life):
    """All distinct attack subsets, valued under a best-replying
    defender. Deduped by BODY MULTISET before the inner search, which is
    exact: minimax value reads nothing but power and toughness."""
    seen, options = set(), []
    for code in range(1 << len(mine)):
        mask = [(code >> i) & 1 == 1 for i in range(len(mine))]
        sig = tuple(sorted((mine[i][1], mine[i][2])
                           for i in range(len(mine)) if mask[i]))
        if sig in seen:
            continue
        seen.add(sig)
        options.append(_evaluate(mine, mask, theirs, my_life, opp_life))
    best = max(options, key=lambda x: x["score"])
    best_ca = max(options, key=lambda x: x["score_ca"])
    return options, best, best_ca


def _pareto_attacks(options, max_cands=64):
    """Four objectives, the fourth on purpose: see jointAttacks. Dropping
    RETAINED POWER would delete every hold-back option from the list,
    because under a one-combat outcome holding a creature is dominated by
    attacking with it - the filter would decide the question."""
    kept, seen = [], set()
    for o1 in options:
        dominated = False
        for o2 in options:
            if o2 is o1:
                continue
            ge = (o2["o"]["dmg"] >= o1["o"]["dmg"]
                  and o2["o"]["bval"] >= o1["o"]["bval"]
                  and o2["o"]["aval"] <= o1["o"]["aval"]
                  and o2["retained_power"] >= o1["retained_power"]
                  and o2["retained_bodies"] >= o1["retained_bodies"])
            gt = (o2["o"]["dmg"] > o1["o"]["dmg"]
                  or o2["o"]["bval"] > o1["o"]["bval"]
                  or o2["o"]["aval"] < o1["o"]["aval"]
                  or o2["retained_power"] > o1["retained_power"]
                  or o2["retained_bodies"] > o1["retained_bodies"])
            if ge and gt:
                dominated = True
                break
        if dominated:
            continue
        key = (o1["o"]["dmg"], o1["o"]["blost"], o1["o"]["bval"],
               o1["o"]["akill"], o1["o"]["aval"], o1["used"],
               o1["retained_power"], o1["crack"])
        if key in seen:
            continue
        seen.add(key)
        kept.append(o1)
        if len(kept) >= max_cands:
            break
    return kept


def cand_attack_set(op, my_life, opp_life):
    """v5 candidate: the subset described by its value under the
    defender's best reply. Mirrors StateEncoder.forAttackSet."""
    c = [0.0] * CDIM
    c[T_ATTACK] = 1.0
    o = op["o"]
    c[6] = o["dmg"] / 20
    c[7] = o["blost"] / 6
    c[8] = o["bval"] / 20
    c[9] = o["akill"] / 6
    c[10] = o["aval"] / 20
    c[11] = 1.0 if o["dead"] else 0.0
    c[12] = op["used"] / 6
    c[13] = (opp_life - o["dmg"]) / 20
    c[14] = op["retained_bodies"] / 6
    c[15] = op["retained_power"] / 20
    c[16] = op["retained_tough"] / 20
    c[17] = op["crack"] / 20
    c[18] = (my_life - op["crack"]) / 20
    return c


def _names(pos, mask):
    got = [pos.blockers[i][0] for i in range(len(pos.blockers)) if mask[i]]
    return " + ".join(got) if got else "(none)"


def attack_coverage(pos, label):
    """MECHANISM CHECK, no policy involved. Does the joint candidate list
    still CONTAIN the reference-best subset after dedupe and Pareto?

    This is the one attack claim available without training a net: the
    per-creature decomposition cannot express "these three attack
    together" as a single choice, and this says whether the replacement
    can. It says nothing about whether a policy picks it."""
    mine, theirs = pos.blockers, pos.attackers
    options, best, best_ca = _best_attack(mine, theirs, pos.my_life,
                                          pos.opp_life)
    kept = _pareto_attacks(options)
    in_list = any(k["mask"] == best["mask"] for k in kept)
    print("== COVERAGE %s" % label)
    print("   %d subsets -> %d distinct -> %d after Pareto"
          % (1 << len(mine), len(options), len(kept)))
    print("   reference best: %s (score %d)"
          % (_names(pos, best["mask"]), best["score"]))
    print("   reference best (CA): %s (score %d)"
          % (_names(pos, best_ca["mask"]), best_ca["score_ca"]))
    print("   best subset survives the filter: %s" % ("YES" if in_list else "NO"))
    return in_list


def run_attacks_v5(pol, pos, label, encv=5):
    """One joint decision over attack subsets - mirrors
    RLPlayer.jointAttacks, including candidate order."""
    mine, theirs = pos.blockers, pos.attackers
    options, best, best_ca = _best_attack(mine, theirs, pos.my_life,
                                          pos.opp_life)
    kept = _pareto_attacks(options)
    cands = [cand_attack_set(k, pos.my_life, pos.opp_life) for k in kept]
    pick = pol.choose(pos.attack_state(0, encv=encv), cands)
    chosen = kept[pick] if 0 <= pick < len(kept) else None
    print("== %s   [%d distinct subsets, %d after Pareto]"
          % (label, len(options), len(kept)))
    print("   my creatures %s   vs their %s"
          % (", ".join("%s %d/%d" % b for b in mine),
             ", ".join("%s %d/%d" % a for a in theirs)))
    if chosen is None:
        print("   policy returned an out-of-range candidate index")
        return 0
    print("   policy attacks: %s" % _names(pos, chosen["mask"]))
    print("   reference     : %s" % _names(pos, best["mask"]))
    print("   policy score %d   reference %d   %s"
          % (chosen["score"], best["score"],
             "MATCH" if chosen["score"] >= best["score"] else "SUBOPTIMAL"))
    print("   CA: policy %d   reference %s (%d)"
          % (chosen["score_ca"], _names(pos, best_ca["mask"]),
             best_ca["score_ca"]))
    return chosen["used"]


def run_position_v4(pol, pos, label):
    """One joint decision over outcome-deduped complete assignments -
    mirrors RLPlayer.jointBlocks, including insertion order."""
    import itertools
    seen, options = {}, []
    for assign in itertools.product(range(-1, len(pos.attackers)),
                                    repeat=len(pos.blockers)):
        o = _resolve(pos.attackers, pos.blockers, assign, pos.my_life)
        used = sum(1 for a in assign if a >= 0)
        key = (o["dmg"], o["akill"], o["aval"], o["blost"], o["bval"], used)
        if key in seen:
            continue
        seen[key] = assign
        options.append(assign)
    cands = [cand_assignment(pos, a) for a in options]
    pick = pol.choose(pos.state({}), cands)
    chosen = options[pick] if 0 <= pick < len(options) else [-1] * len(pos.blockers)
    print("== %s   [%d distinct outcomes]" % (label, len(options)))
    print("   life %d, attackers %s, blockers %s"
          % (pos.my_life,
             ", ".join("%s %d/%d" % a for a in pos.attackers),
             ", ".join("%s %d/%d" % b for b in pos.blockers)))
    for bi, ai in enumerate(chosen):
        print("     %-26s -> %s" % (pos.blockers[bi][0],
                                    pos.attackers[ai][0] if ai >= 0 else "DECLINE"))
    best, bs = solver_best(pos)
    total = sum(p for _, p, _ in pos.attackers)
    gs = _score(_resolve(pos.attackers, pos.blockers, chosen, pos.my_life), total)
    print("   policy score %d   solver score %d   %s"
          % (gs, bs, "MATCH" if gs >= bs else "SUBOPTIMAL"))


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


def run_attacks(pol, pos, label, encv=2):
    """Replay selectAttackers: one binary choice per creature, name order
    (RLPlayer sorts attackers by name in every encoder version below v5)."""
    order = sorted(range(len(pos.blockers)), key=lambda i: pos.blockers[i][0])
    declared = 0
    print("== %s" % label)
    print("   my creatures %s   vs their %s"
          % (", ".join("%s %d/%d" % b for b in pos.blockers),
             ", ".join("%s %d/%d" % a for a in pos.attackers)))
    for bi in order:
        a = pol.choose(pos.attack_state(declared, encv=encv),
                       [pos.cand_pass(), pos.cand_attack(bi)])
        if a == 1:
            declared += 1
        print("     %-26s -> %s" % (pos.blockers[bi][0],
                                    "ATTACK" if a == 1 else "hold"))
    return declared


def attack_positions():
    """The attack battery. `blockers` is MY board and `attackers` is
    THEIRS here - Pos was written for a defensive position and
    run_attacks keeps its convention rather than duplicating the class.

    Four positions, chosen so that both ways a fix can fail are visible.
    COMMIT is the one a per-creature decomposition provably cannot solve.
    ALPHA33, HOLD and LETHAL are controls: an agent that has simply
    learned "attack with everything" passes COMMIT and LETHAL and fails
    the other two, and attack-optimality alone would not tell the two
    apart.

    READ ALPHA33 BEFORE TRUSTING ANY OF THEM. The handoff describes
    exactly that position - three 2/2s into one 3/3 - as one where
    attacking with all three is right. Under the evaluator actually used
    here it is not: the 3/3 eats a 2/2 and survives, so the alpha strike
    deals 4 and loses a body, scoring -4 against 0 for holding, because
    attackerScore mirrors defenderScore and prices material at 3 a point
    against damage at 2. Neither the handoff nor this file settles which
    is right - a one-combat evaluator cannot price a race - but the
    disagreement has to be visible rather than buried in a battery that
    silently scores the handoff's position as a failure.
    """
    return [
        # COMMITMENT, the attack-side mirror of the double block. Three
        # 2/2s into one 3/1. Attacking with ONE is worth exactly what
        # holding is worth (it is blocked, both die, nothing connects);
        # the gain only exists once the others join, and it rises with
        # each one: hold 0, one 0, two +4, all three +8. So no creature
        # has a marginal reason to go first, which is precisely what an
        # independent yes/no per creature cannot express, and precisely
        # what one decision over subsets can.
        (Pos(my_life=15, opp_life=10,
             attackers=[("Blade of the Sixth Pride", 3, 1)],
             blockers=[("Glory Seeker", 2, 2), ("Silvercoat Lion", 2, 2),
                       ("Fresh Volunteers", 2, 2)],
             turn=14),
         "COMMIT: three 2/2s into one 3/1 (all three = +8, any one = 0)"),

        # THE HANDOFF'S POSITION, kept verbatim and scored honestly. See
        # the docstring: the reference says hold, at -4 for the alpha
        # strike. Reported, not fixed.
        (Pos(my_life=15, opp_life=10,
             attackers=[("Shu Elite Infantry", 3, 3)],
             blockers=[("Glory Seeker", 2, 2), ("Silvercoat Lion", 2, 2),
                       ("Fresh Volunteers", 2, 2)],
             turn=14),
         "ALPHA33: three 2/2s into one 3/3 (reference says HOLD, -4)"),

        # THE OVERSHOOT CONTROL. One 2/2 into two untapped 3/3s at equal
        # life: whatever attacks is blocked, dies and deals nothing, and
        # it is also the only blocker I have. Both references say hold.
        (Pos(my_life=20, opp_life=20,
             attackers=[("Shu Elite Infantry", 3, 3),
                        ("Knight of the Keep", 3, 3)],
             blockers=[("Glory Seeker", 2, 2)],
             turn=8),
         "HOLD: one 2/2 into two 3/3s (attacking is strictly bad)"),

        # LETHAL ON BOARD. They are at 4 with nothing untapped; two 2/2s
        # is already exactly lethal. Nothing subtle is being asked - it is
        # the position where holding costs the whole game, and
        # auditAttacks scores it in its own category (MISSED LETHAL)
        # rather than as a score gap.
        (Pos(my_life=9, opp_life=4,
             attackers=[],
             blockers=[("Glory Seeker", 2, 2), ("Silvercoat Lion", 2, 2),
                       ("Fresh Volunteers", 2, 2)],
             turn=16),
         "LETHAL: three 2/2s, they are at 4 with no untapped blocker"),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7995)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--v4", action="store_true",
                    help="joint assignment: one decision per combat")
    ap.add_argument("--v5", action="store_true",
                    help="v4 plus joint ATTACKS: one decision per combat "
                         "over attack subsets")
    ap.add_argument("--coverage", action="store_true",
                    help="mechanism check only, no policy server needed: "
                         "does the joint candidate list still contain the "
                         "reference-best attack subset")
    args = ap.parse_args()
    load_features()
    if args.coverage:
        ok = True
        for pos, label in attack_positions():
            ok &= attack_coverage(pos, label)
            print()
        print("COVERAGE|all_reference_subsets_survive_filter=%s"
              % ("YES" if ok else "NO"))
        return
    pol = Policy(args.port)
    if args.v4 or args.v5:
        globals()["run_position"] = run_position_v4
    if args.v5:
        globals()["run_attacks"] = run_attacks_v5

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

    # The encoder version decides the STATE the probe builds, not just
    # which code path runs: below v3 the agent's own attackers register
    # in s[24..27] and above it they do not. Passing the arm through is
    # what keeps the probe faithful to the net it is questioning.
    encv = 5 if args.v5 else (4 if args.v4 else 2)
    for pos, label in attack_positions():
        run_attacks(pol, pos, label, encv=encv)
        print()

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
