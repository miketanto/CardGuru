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
        Outcome o = new Outcome();
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
            }
            mine.sort(Comparator.comparingInt(b -> b.toughness));
            int left = atk.power;
            for (Body b : mine) {
                if (left >= b.toughness) {
                    left -= b.toughness;
                    o.blockersLost++;
                    o.blockerValueLost += b.value();
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

    public static List<Body> bodies(List<Permanent> ps) {
        List<Body> out = new ArrayList<>(ps.size());
        for (Permanent p : ps) {
            out.add(Body.of(p));
        }
        return out;
    }
}
