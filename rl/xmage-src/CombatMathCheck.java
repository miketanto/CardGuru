package org.mage.test.benchmark.rl;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Self-test for the two searches the attack audit rests on.
 *
 * WHY IT IS COMMITTED. bestDeduped() is an optimisation with a
 * correctness ARGUMENT behind it - identical bodies are interchangeable,
 * so only non-decreasing assignments within a group of identical bodies
 * need enumerating - and an argument is not a check. If it is wrong it
 * does not crash; it silently returns a weaker reference, and every
 * attack-optimality number reported from it is inflated by exactly the
 * amount the search missed. So it is checked against the brute force it
 * replaces, on random boards, and the check is a file rather than
 * something that happened once in a shell.
 *
 * Run (classpath from the persistent driver's cache):
 *   java -cp "$(cat /tmp/rl_p9/cp.txt):Mage.Tests/target/test-classes" \
 *        org.mage.test.benchmark.rl.CombatMathCheck [trials]
 */
public final class CombatMathCheck {

    private static List<CombatMath.Body> board(Random r, int n) {
        List<CombatMath.Body> out = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            // deliberately a SMALL body pool: duplicates are the case
            // bestDeduped exists for, so they must be common here
            int p = 1 + r.nextInt(3);
            int t = 1 + r.nextInt(3);
            out.add(new CombatMath.Body(p, t, "c" + i));
        }
        return out;
    }

    public static void main(String[] args) {
        int trials = args.length > 0 ? Integer.parseInt(args[0]) : 2000;
        Random r = new Random(7);
        int mismatches = 0, checked = 0;
        for (int i = 0; i < trials; i++) {
            int A = 1 + r.nextInt(4);
            int B = 1 + r.nextInt(5);
            int life = 1 + r.nextInt(20);
            List<CombatMath.Body> atk = board(r, A);
            List<CombatMath.Body> blk = board(r, B);
            CombatMath.Best brute = CombatMath.best(atk, blk, life, 10000000L);
            CombatMath.Best dedup = CombatMath.bestDeduped(atk, blk, life, 10000000L);
            if (!brute.exhaustive || !dedup.exhaustive) {
                continue;             // not a comparison of two full searches
            }
            checked++;
            if (brute.score != dedup.score) {
                mismatches++;
                if (mismatches <= 5) {
                    System.out.println("MISMATCH A=" + A + " B=" + B
                            + " life=" + life + " brute=" + brute.score
                            + " dedup=" + dedup.score);
                }
            }
            // the deduped search must also be no more expensive
            if (dedup.considered > brute.considered) {
                System.out.println("WARN: dedup considered more ("
                        + dedup.considered + " vs " + brute.considered + ")");
            }
        }
        System.out.println("CHECK|bestDeduped|trials=" + checked
                + "|mismatches=" + mismatches);
        // A second property: evaluate() must agree with resolve() on the
        // subset it says it played, i.e. the audit and the policy cannot
        // be scoring different things.
        int bad = 0;
        for (int i = 0; i < 200; i++) {
            int A = 1 + r.nextInt(4);
            int B = r.nextInt(4);
            List<CombatMath.Body> mine = board(r, A);
            List<CombatMath.Body> theirs = board(r, B);
            boolean[] mask = new boolean[A];
            for (int j = 0; j < A; j++) {
                mask[j] = r.nextBoolean();
            }
            CombatMath.AttackOption op = CombatMath.evaluate(
                    mine, mask, theirs, 20, 20, 1000000L);
            int used = 0;
            for (int j = 0; j < A; j++) {
                if (mask[j]) {
                    used++;
                }
            }
            if (op.attackersUsed != used
                    || op.retainedBodies != A - used) {
                bad++;
            }
        }
        System.out.println("CHECK|evaluate|mismatches=" + bad);
        if (mismatches > 0 || bad > 0) {
            System.exit(1);
        }
    }
}
