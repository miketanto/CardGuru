package org.mage.test.benchmark.rl;

import mage.game.Game;
import mage.game.permanent.Permanent;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Exact combat resolution and best-assignment search for the no-instants
 * rungs of the curriculum ladder.
 *
 * WHY THIS EXISTS
 * At rungs 0-3 there are no instants and no replacement effects, so the
 * result of a combat is a DETERMINISTIC FUNCTION of the block
 * assignment. That makes two things possible that are not possible on a
 * real deck:
 *
 *   1. afterstate features - hand the policy the board that RESULTS from
 *      a block instead of the stat lines it would have to do arithmetic
 *      on (the classical afterstate formulation; see
 *      rl/COMBAT-LITERATURE.md);
 *   2. a best-assignment reference, so "how far from optimal does this
 *      agent block" becomes measurable instead of anecdotal.
 *
 * HONEST NAMING. This is NOT a game-theoretic oracle. It is optimal for
 * the CURRENT COMBAT under the evaluator in defenderScore(), one combat
 * deep, with no lookahead past damage. A block that is correct this turn
 * can still be strategically wrong. Anything reported from it must say
 * "best by this evaluator", never "optimal play".
 *
 * SCOPE. Vanilla bodies only: no first strike, deathtouch, trample,
 * flying or menace. Rung 1 introduces exactly those, and each one needs
 * an explicit change here - resolve() will silently give wrong answers
 * for them, so RUNG1 decks must not use this until it is extended.
 */
public final class CombatMath {

    private CombatMath() {
    }

    /** Read once at class-init: resolve() is the hot loop of every search
     *  in this file and a property read per call would be felt. */
    private static final boolean LEGACY_TIE =
            Boolean.getBoolean("rl.legacyTieBreak");

    /** One creature reduced to what combat actually depends on. */
    public static final class Body {
        public final int power;
        public final int toughness;
        public final String name;

        public Body(int power, int toughness, String name) {
            this.power = power;
            this.toughness = toughness;
            this.name = name;
        }

        public static Body of(Permanent p) {
            return new Body(p.getPower().getValue(),
                    p.getToughness().getValue(), p.getName());
        }

        int value() {           // material worth, deliberately crude
            return power + toughness;
        }
    }

    /** What a combat did, from the defender's point of view. */
    public static final class Outcome {
        public int damageTaken;
        public int attackersKilled;
        public int attackerValueKilled;
        public int blockersLost;
        public int blockerValueLost;
        public boolean defenderDies;
    }

    /**
     * Resolve one combat. assign[i] is the index of the attacker that
     * blocker i is assigned to, or -1 for "does not block".
     *
     * The attacking player chooses how to split a blocked attacker's
     * damage among its blockers, so the defender must assume the WORST:
     * damage is assigned to kill as many blockers as possible, smallest
     * toughness first. Assuming anything friendlier would make the
     * reference optimistic and the measurement useless.
     */
    public static Outcome resolve(List<Body> attackers, List<Body> blockers,
                                  int[] assign, int defenderLife) {
        return resolve(attackers, blockers, assign, defenderLife, null);
    }

    /**
     * Which bodies died, for callers that need the AFTERSTATE rather than
     * the totals - the attack side needs it to know what the defender has
     * left to swing back with.
     *
     * Opt-in via a caller-allocated Detail because resolve() is the hot
     * loop of every search here: best() runs it (A+1)^B times and
     * bestAttack() runs THAT once per subset, so allocating two boolean
     * arrays per call would put millions of short-lived objects through
     * the nursery per combat. Callers that want detail run one extra
     * resolve on the one assignment they kept.
     */
    public static final class Detail {
        public boolean[] attackerDied;
        public boolean[] blockerDied;
    }

    public static Outcome resolve(List<Body> attackers, List<Body> blockers,
                                  int[] assign, int defenderLife, Detail d) {
        Outcome o = new Outcome();
        if (d != null) {
            d.attackerDied = new boolean[attackers.size()];
            d.blockerDied = new boolean[blockers.size()];
        }
        for (int a = 0; a < attackers.size(); a++) {
            Body atk = attackers.get(a);
            List<Body> mine = new ArrayList<>();
            for (int b = 0; b < blockers.size(); b++) {
                if (assign[b] == a) {
                    mine.add(blockers.get(b));
                }
            }
            if (mine.isEmpty()) {
                o.damageTaken += atk.power;
                continue;
            }
            int blockPower = 0;
            for (Body b : mine) {
                blockPower += b.power;
            }
            if (blockPower >= atk.toughness) {
                o.attackersKilled++;
                o.attackerValueKilled += atk.value();
                if (d != null) {
                    d.attackerDied[a] = true;
                }
            }
            // TIE-BREAK, and it is not cosmetic. Sorting by toughness
            // alone is a STABLE sort, so among equally-fragile blockers
            // the one earliest in the caller's list dies - and RLPlayer
            // hands blockers over sorted by (toughness, power), so the
            // cheapest body died and the defender collected the
            // friendliest reading of a choice that is not theirs to
            // make. The attacking player assigns combat damage; facing
            // a 2/1 and a 3/1 they kill the 3/1. The search then
            // exploited it: brute force preferred assignments that were
            // better only by list order, scoring 20 where the same
            // assignment with the two 2/1s swapped scored 17.
            //
            // Killing as many as possible stays primary (unchanged);
            // value descending breaks the tie. That is strictly
            // worse-or-equal for the defender, i.e. it can only make the
            // reference harder to match, never easier - the direction
            // this file's own contract demands.
            //
            // -Drl.legacyTieBreak=true restores the old behaviour, so
            // the size of the re-baseline against every previously
            // reported block-optimality number is measurable from one
            // build rather than argued about.
            if (LEGACY_TIE) {
                mine.sort(Comparator.comparingInt(b -> b.toughness));
            } else {
                mine.sort(Comparator.comparingInt((Body b) -> b.toughness)
                        .thenComparingInt(b -> -b.value()));
            }
            int left = atk.power;
            for (Body b : mine) {
                if (left >= b.toughness) {
                    left -= b.toughness;
                    o.blockersLost++;
                    o.blockerValueLost += b.value();
                    if (d != null) {
                        // mine was sorted, so find this body's index among
                        // the blockers assigned here that is not yet marked
                        for (int bi = 0; bi < blockers.size(); bi++) {
                            if (assign[bi] == a && !d.blockerDied[bi]
                                    && blockers.get(bi) == b) {
                                d.blockerDied[bi] = true;
                                break;
                            }
                        }
                    }
                }
            }
        }
        o.defenderDies = o.damageTaken >= defenderLife;
        return o;
    }

    /**
     * Defender's score for an outcome. Surviving dominates everything;
     * below that it is material traded plus damage avoided.
     */
    public static int defenderScore(Outcome o, int totalAttackPower) {
        if (o.defenderDies) {
            return Integer.MIN_VALUE / 2;
        }
        int damagePrevented = totalAttackPower - o.damageTaken;
        return 2 * damagePrevented + 3 * o.attackerValueKilled
                - 3 * o.blockerValueLost;
    }

    /** Search result: the assignment and what it scored. */
    public static final class Best {
        public int[] assign;
        public int score;
        public Outcome outcome;
        public long considered;
        public boolean exhaustive;
    }

    /**
     * Brute-force the best assignment. (A+1)^B, so it is capped: above
     * the cap the search is truncated and `exhaustive` comes back false,
     * which callers MUST report rather than quietly treat as optimal.
     */
    public static Best best(List<Body> attackers, List<Body> blockers,
                            int defenderLife, long cap) {
        int A = attackers.size();
        int B = blockers.size();
        int totalPower = 0;
        for (Body a : attackers) {
            totalPower += a.power;
        }
        Best best = new Best();
        best.assign = new int[B];
        java.util.Arrays.fill(best.assign, -1);
        best.outcome = resolve(attackers, blockers, best.assign, defenderLife);
        best.score = defenderScore(best.outcome, totalPower);
        best.exhaustive = true;
        if (B == 0 || A == 0) {
            return best;
        }
        long space = 1;
        for (int i = 0; i < B; i++) {
            space *= (A + 1);
            if (space > cap) {
                best.exhaustive = false;
                break;
            }
        }
        long limit = best.exhaustive ? space : cap;
        int[] assign = new int[B];
        for (long code = 0; code < limit; code++) {
            long c = code;
            for (int b = 0; b < B; b++) {
                assign[b] = (int) (c % (A + 1)) - 1;
                c /= (A + 1);
            }
            Outcome o = resolve(attackers, blockers, assign, defenderLife);
            int s = defenderScore(o, totalPower);
            best.considered++;
            if (s > best.score) {
                best.score = s;
                best.assign = assign.clone();
                best.outcome = o;
            }
        }
        return best;
    }

    // ================================================================
    // THE ATTACK SIDE
    //
    // Blocks resolve deterministically: resolve() answers "what happens
    // if these blockers block these attackers" and that is the whole
    // question. Attacking is not that question. An attack subset has no
    // outcome until the DEFENDER answers it, so valuing one requires a
    // model of what they will do.
    //
    // The model used here is MINIMAX ONE PLY: the defender replies with
    // best() under defenderScore(), i.e. the reply that is best for them
    // by the same evaluator this file already uses for blocking. That
    // choice is deliberate and it is not free:
    //
    //   - it inherits every limitation of defenderScore, including that
    //     defenderScore has NO TERM FOR BLOCKERS USED, so among replies
    //     that score equally the reference may pile blockers. Ties break
    //     toward the lowest enumeration code, which is the all-decline
    //     assignment, so the bias is toward UNDER-blocking replies;
    //   - it costs 2^A x (|S|+1)^B resolves per combat before dedupe;
    //   - and it assumes the defender is a perfect one-combat solver,
    //     which the actual D0 opponent is not. Against a weaker defender
    //     this reference UNDERSTATES how good an attack is.
    //
    // Anything reported from this must say "best by this evaluator under
    // a best-replying defender", never "optimal attack".
    // ================================================================

    /**
     * best(), but enumerating only CANONICAL assignments: blockers that
     * are the same body are interchangeable, so within a group of
     * identical bodies only non-decreasing attacker-index sequences are
     * enumerated. Exact - resolve() reads nothing but power and
     * toughness, so two assignments that differ by a permutation within
     * such a group resolve identically.
     *
     * WHY IT EXISTS. The attack side calls this once per subset, so the
     * defender's reply search is the inner loop of an outer loop. At the
     * raw (A+1)^B it truncated on 15 of 79 combats of a five-game probe
     * even at a 200k cap, and that truncation is BIASED, not noisy:
     * best() enumerates codes from zero and code zero is all-decline, so
     * a cut search systematically under-blocks and the reference comes
     * back too easy to match. On the rung-0 decks, where a board is
     * typically eight creatures across three distinct bodies, this
     * collapses 5^8 = 390k to about 47k.
     *
     * DELIBERATELY NOT WIRED INTO best(). auditBlocks and rl.solverBlocks
     * call best(), and every block-optimality number this project has
     * reported came from it; making the block reference stronger would
     * re-baseline all of them. That is a separate, deliberate change.
     * The two references therefore differ, and any table putting block-
     * optimality next to attack-optimality has to say so.
     */
    public static Best bestDeduped(List<Body> attackers, List<Body> blockers,
                                   int defenderLife, long cap) {
        int A = attackers.size();
        int B = blockers.size();
        int totalPower = 0;
        for (Body a : attackers) {
            totalPower += a.power;
        }
        Best best = new Best();
        best.assign = new int[B];
        java.util.Arrays.fill(best.assign, -1);
        best.outcome = resolve(attackers, blockers, best.assign, defenderLife);
        best.score = defenderScore(best.outcome, totalPower);
        best.exhaustive = true;
        if (B == 0 || A == 0) {
            return best;
        }
        // group blocker indices by body; identical bodies share a group
        List<List<Integer>> groups = new ArrayList<>();
        List<String> keys = new ArrayList<>();
        for (int b = 0; b < B; b++) {
            String k = blockers.get(b).power + "/" + blockers.get(b).toughness;
            int g = keys.indexOf(k);
            if (g < 0) {
                keys.add(k);
                groups.add(new ArrayList<Integer>());
                g = groups.size() - 1;
            }
            groups.get(g).add(b);
        }
        enumerate(attackers, blockers, groups, 0, 0, -1, new int[B],
                  defenderLife, totalPower, best, cap);
        return best;
    }

    /** Recursive canonical enumeration; `floor` is the non-decreasing
     *  bound inside the current group of identical bodies. */
    private static void enumerate(List<Body> attackers, List<Body> blockers,
                                  List<List<Integer>> groups, int gi, int pos,
                                  int floor, int[] assign, int defenderLife,
                                  int totalPower, Best best, long cap) {
        if (best.considered > cap) {
            best.exhaustive = false;
            return;
        }
        if (gi >= groups.size()) {
            Outcome o = resolve(attackers, blockers, assign, defenderLife);
            int sc = defenderScore(o, totalPower);
            best.considered++;
            if (sc > best.score) {
                best.score = sc;
                best.assign = assign.clone();
                best.outcome = o;
            }
            return;
        }
        List<Integer> g = groups.get(gi);
        if (pos >= g.size()) {
            enumerate(attackers, blockers, groups, gi + 1, 0, -1, assign,
                      defenderLife, totalPower, best, cap);
            return;
        }
        // floor starts at -1 for each group, so "does not block" is the
        // first value of the non-decreasing sequence, not a special case
        for (int a = floor; a < attackers.size(); a++) {
            assign[g.get(pos)] = a;
            enumerate(attackers, blockers, groups, gi, pos + 1, a, assign,
                      defenderLife, totalPower, best, cap);
            if (best.considered > cap) {
                return;
            }
        }
        assign[g.get(pos)] = -1;      // restore for the caller's next value
    }

    /**
     * Attacker's score for an outcome. Mirror of defenderScore, read from
     * the other seat: `damageTaken` is damage DEALT, `blockerValueLost`
     * is THEIR material, `attackerValueKilled` is MINE.
     *
     * WHAT THIS CANNOT SEE, and it is the whole reason the attack audit
     * needs a second opinion: a creature that attacks is tapped through
     * the opponent's entire next turn, so attacking costs defence. This
     * function is one combat deep and prices that at zero. Its bias
     * therefore runs TOWARD attacking - the same direction as any fix
     * that makes an agent attack more, which is exactly why
     * attackerScoreCA exists below.
     */
    public static int attackerScore(Outcome o) {
        if (o.defenderDies) {
            return Integer.MAX_VALUE / 2;      // lethal ends the game
        }
        return 2 * o.damageTaken + 3 * o.blockerValueLost
                - 3 * o.attackerValueKilled;
    }

    /**
     * Damage the opponent's surviving creatures get through NEXT turn if
     * every creature I leave untapped blocks one of them and eats it
     * whole. Their k biggest attackers are absorbed by my k retained
     * bodies; the rest connects.
     *
     * Crude on purpose: it is a SENSITIVITY CHECK on attackerScore, not a
     * second reference. It over-credits my retained blockers (a 1/1 does
     * not really absorb a 5/5 for free) and it ignores what my blockers
     * kill, so it is a LOWER bound on the crack-back and an upper bound
     * on my defence.
     */
    public static int crackBack(List<Body> theirSurvivors, int myRetainedBodies) {
        List<Integer> powers = new ArrayList<>();
        for (Body b : theirSurvivors) {
            powers.add(b.power);
        }
        powers.sort(Comparator.reverseOrder());
        int through = 0;
        for (int i = myRetainedBodies; i < powers.size(); i++) {
            through += powers.get(i);
        }
        return through;
    }

    /**
     * attackerScore minus what the swing back costs. Weighted 2 per point
     * of damage taken, matching the 2 per point dealt in attackerScore,
     * and dying to the crack-back is a loss sentinel the way defenderDies
     * is in defenderScore.
     */
    public static int attackerScoreCA(Outcome o, int myLifeAfter, int crackBack) {
        if (o.defenderDies) {
            return Integer.MAX_VALUE / 2;      // I win first; nothing swings back
        }
        if (crackBack >= myLifeAfter) {
            return Integer.MIN_VALUE / 2;      // lethal crack-back
        }
        return attackerScore(o) - 2 * crackBack;
    }

    /** One attack subset, valued under the defender's best reply. */
    public static final class AttackOption {
        public boolean[] attack;        // over the attacker's creature list
        public int attackersUsed;
        public Outcome outcome;         // under the reply below
        public int[] reply;             // defender's best block assignment
        public boolean replyExhaustive;
        public int score;               // attackerScore
        public int scoreCA;             // attackerScoreCA
        public int retainedBodies;      // untapped creatures left at home
        public int retainedPower;
        public int retainedToughness;
        public int crackBack;
        public long considered;         // resolve() calls this option cost
    }

    /**
     * Value ONE attack subset under the defender's best reply. Shared by
     * the search and by the audit, so the assignment the policy made and
     * the assignment the reference prefers are scored by identical code -
     * an audit that scores the two sides through different paths measures
     * the difference between the paths.
     */
    public static AttackOption evaluate(List<Body> mine, boolean[] attack,
                                        List<Body> theirs, int myLife,
                                        int oppLife, long replyCap) {
        AttackOption op = new AttackOption();
        op.attack = attack;
        List<Body> sub = new ArrayList<>();
        for (int i = 0; i < mine.size(); i++) {
            if (attack[i]) {
                sub.add(mine.get(i));
            } else {
                op.retainedBodies++;
                op.retainedPower += mine.get(i).power;
                op.retainedToughness += mine.get(i).toughness;
            }
        }
        op.attackersUsed = sub.size();
        Best reply = bestDeduped(sub, theirs, oppLife, replyCap);
        op.considered = reply.considered + 1;
        op.reply = reply.assign;
        op.replyExhaustive = reply.exhaustive;
        Detail d = new Detail();
        op.outcome = resolve(sub, theirs, reply.assign, oppLife, d);
        op.score = attackerScore(op.outcome);
        List<Body> survivors = new ArrayList<>();
        for (int i = 0; i < theirs.size(); i++) {
            if (!d.blockerDied[i]) {
                survivors.add(theirs.get(i));
            }
        }
        op.crackBack = crackBack(survivors, op.retainedBodies);
        op.scoreCA = attackerScoreCA(op.outcome, myLife, op.crackBack);
        return op;
    }

    /** Search result over attack subsets. */
    public static final class BestAttack {
        public AttackOption best;              // by attackerScore
        public AttackOption bestCA;            // by attackerScoreCA
        public List<AttackOption> options;     // one per DISTINCT body multiset
        public long considered;                // resolve() calls
        public boolean exhaustive;             // subset enumeration complete
        public boolean replyExhaustive;        // every inner reply complete
        /** rl.attackTotalCap hit: later subsets priced under a 200-leaf
         *  reply cap (7c: a wide board took 4096 x 200k resolves per consult) */
        public boolean budgetHit;
    }

    /**
     * Enumerate attack subsets, value each under the defender's best
     * reply, and return them all (the policy needs the list; the audit
     * needs the argmax).
     *
     * DEDUPE BY BODY MULTISET, BEFORE the inner search. Two subsets made
     * of the same power/toughness multiset have identical minimax value -
     * resolve() reads nothing else - so this is exact, not a heuristic,
     * and it is the difference between 64 and 32 inner searches on the
     * 6-creature board in the committed replay.
     *
     * Caps: `subsetCap` bounds 2^A, `replyCap` bounds each inner best().
     * Both truncations are reported, separately, and neither is silent.
     */
    public static BestAttack bestAttack(List<Body> mine, List<Body> theirs,
                                        int myLife, int oppLife,
                                        long subsetCap, long replyCap) {
        int A = mine.size();
        BestAttack out = new BestAttack();
        out.options = new ArrayList<>();
        out.exhaustive = true;
        out.replyExhaustive = true;
        long space = 1L << Math.min(A, 62);
        if (A >= 62 || space > subsetCap) {
            space = subsetCap;
            out.exhaustive = false;
        }
        java.util.Set<String> seen = new java.util.HashSet<>();
        // Total leaf budget across ALL subsets: subsetCap x replyCap is 8e8
        // resolves on a wide board (the 7c hang, minutes per consult). Once
        // the budget is spent the remaining subsets keep their place in the
        // option list (the candidate SET never changes) but are priced under
        // a 200-leaf reply cap; budgetHit reports it, RLPlayer counts it.
        long totalCap = Long.getLong("rl.attackTotalCap", 2000000L);
        for (long mask = 0; mask < space; mask++) {
            List<String> sig = new ArrayList<>();
            for (int i = 0; i < A; i++) {
                if ((mask & (1L << i)) != 0) {
                    sig.add(mine.get(i).power + "/" + mine.get(i).toughness);
                }
            }
            sig.sort(null);
            if (!seen.add(sig.toString())) {
                continue;
            }
            boolean[] attack = new boolean[A];
            for (int i = 0; i < A; i++) {
                attack[i] = (mask & (1L << i)) != 0;
            }
            long rc = replyCap;
            if (out.considered > totalCap) {
                rc = Math.min(replyCap, 200L);
                out.budgetHit = true;
            }
            AttackOption op = evaluate(mine, attack, theirs, myLife, oppLife,
                    rc);
            out.considered += op.considered;
            out.replyExhaustive &= op.replyExhaustive;
            out.options.add(op);
            if (out.best == null || op.score > out.best.score) {
                out.best = op;
            }
            if (out.bestCA == null || op.scoreCA > out.bestCA.scoreCA) {
                out.bestCA = op;
            }
        }
        return out;
    }

    /** "Foot Soldiers 2/4 + Shu Elite Infantry 3/3" / "(none)" */
    public static String subsetStr(List<Body> mine, boolean[] attack) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < mine.size(); i++) {
            if (attack == null || i >= attack.length || !attack[i]) {
                continue;
            }
            if (sb.length() > 0) {
                sb.append(" + ");
            }
            sb.append(mine.get(i).name).append(' ').append(mine.get(i).power)
                    .append('/').append(mine.get(i).toughness);
        }
        return sb.length() == 0 ? "(none)" : sb.toString();
    }

    /** Print a score without letting a sentinel reach the reader raw. */
    public static String scoreStr(int score) {
        if (score >= Integer.MAX_VALUE / 4) {
            return "LETHAL";
        }
        if (score <= Integer.MIN_VALUE / 4) {
            return "SUICIDE";
        }
        return Integer.toString(score);
    }

    public static List<Body> bodies(List<Permanent> ps) {
        List<Body> out = new ArrayList<>(ps.size());
        for (Permanent p : ps) {
            out.add(Body.of(p));
        }
        return out;
    }
}
