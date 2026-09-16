package org.mage.test.benchmark.rl;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Exact solver for a subgame, by REPLAY.
 *
 * A subgame terminates on its own (small libraries; deck-out is a real
 * rule), so the tree is finite and the value of a position is just
 * "does A win", with no evaluator anywhere. The solver enumerates it by
 * running the game from the start with a prefix of choices; when a
 * decision arrives past the end of the prefix the seats record how many
 * options it had, and each extension is a fresh replay.
 *
 * Values are BINARY, which makes alpha-beta degenerate into a
 * short-circuit: an A node stops at the first winning child, a B node at
 * the first losing one. That is what keeps an exhaustive solve cheap.
 *
 * Honest naming: this IS optimal play for this subgame under the real
 * rules, within two stated limits - the seats only ever choose attacks
 * and blocks (priority always passes, so no rung with castable cards can
 * use this as written), and the block option space is a superset that
 * maps illegal assignments onto their legal projection, so distinct
 * indices can denote the same block.
 */
public final class SubgameSolver {

    public long replays = 0;
    public long nodes = 0;
    public long cap = Long.getLong("subgame.replayCap", 200000L);
    public boolean capHit = false;
    /**
     * A replay cap is not a time budget. Replay cost is per-DECISION,
     * and a stalled board - nothing can profitably attack, nothing dies -
     * runs to stopOnTurn every replay, so the same 8,000 replays cost
     * seconds on one board and many minutes on another. Measured: one
     * shard sat on a single board for over five minutes while its
     * siblings cleared a dozen. The wall-clock budget is what actually
     * bounds a generation run; 0 disables it.
     */
    public long budgetNanos = Long.getLong("subgame.solveSecs", 90L) * 1_000_000_000L;
    private long startNanos = System.nanoTime();

    /** Set when it was the clock, not the replay cap, that stopped the
     *  solve - the two are different budgets and a board that ran out of
     *  time should not be reported as a board that ran out of tree. */
    public boolean budgetHit = false;

    private boolean outOfBudget() {
        if (replays >= cap) {
            return true;
        }
        if (budgetNanos > 0 && System.nanoTime() - startNanos > budgetNanos) {
            budgetHit = true;
            return true;
        }
        return false;
    }
    /** Replays that ended with nobody winning - a subgame that did not
     *  terminate is a design violation, so these are counted, not hidden. */
    public long noWinner = 0;

    private final SubgameRunner.Spec spec;

    public SubgameSolver(SubgameRunner.Spec spec) {
        this.spec = spec;
    }

    public static final class Node {
        public int value;              // 1 = A wins, 0 = A does not
        public String seat;            // who chose here, null at a leaf
        public String kind;            // "atk" or "blk"
        public int options;
        public List<Integer> best = new ArrayList<>();   // choices achieving value
    }

    /** Solve the position reached by `prefix`. */
    public Node solve(int[] prefix) {
        nodes++;
        SubgameRunner.Result r = SubgameRunner.scripted(spec, prefix);
        replays++;
        if (r.winner == null) {
            noWinner++;
        }
        Node n = new Node();
        if (!r.frontierHit) {
            n.value = "A".equals(r.winner) ? 1 : 0;
            return n;
        }
        n.seat = r.frontierSeat;
        n.kind = r.frontierKind;
        n.options = r.frontierOptions;
        boolean maximizing = "A".equals(n.seat);
        int best = maximizing ? 0 : 1;
        for (int i = 0; i < n.options; i++) {
            if (outOfBudget()) {
                capHit = true;
                break;
            }
            int[] next = Arrays.copyOf(prefix, prefix.length + 1);
            next[prefix.length] = i;
            int v = solve(next).value;
            if (maximizing ? v > best : v < best) {
                best = v;
                n.best.clear();
                n.best.add(i);
                break;          // binary values: first optimum is enough
            }
            if (v == best) {
                n.best.add(i);
            }
        }
        n.value = best;
        return n;
    }

    /** Every choice at the root that preserves the root's value, with the
     *  short-circuit disabled so the full optimal set is known - that is
     *  what the uniqueness gate needs. */
    public List<Integer> optimalRootChoices(Node root) {
        List<Integer> out = new ArrayList<>();
        if (root.seat == null) {
            return out;
        }
        for (int i = 0; i < root.options; i++) {
            if (outOfBudget()) {
                capHit = true;
                break;
            }
            Node child = solve(new int[]{i});
            if (child.value == root.value) {
                out.add(i);
            }
        }
        return out;
    }

    public static void main(String[] args) {
        mage.cards.repository.CardScanner.scan();
        String small = args.length > 0 ? args[0] : "Silvercoat Lion";
        String big = args.length > 1 ? args[1] : "Trokin High Guard";
        int fillerDelta = args.length > 2 ? Integer.parseInt(args[2]) : 0;
        SubgameRunner.Spec spec = SubgameRunner.t1Hold(small, big);
        // gate 1: same instance with N more filler in BOTH libraries. If
        // the optimal action moves, the family is measuring the deck-out
        // clock rather than the concept.
        spec.a.filler += fillerDelta;
        spec.b.filler += fillerDelta;

        long t0 = System.nanoTime();
        SubgameSolver s = new SubgameSolver(spec);
        Node root = s.solve(new int[0]);
        long tSolve = System.nanoTime() - t0;

        List<Integer> opt = s.optimalRootChoices(root);
        double secs = (System.nanoTime() - t0) / 1e9;

        System.out.println("SOLVE|" + spec.name
                + "|fillerDelta=" + fillerDelta
                + "|value=" + root.value
                + "|rootSeat=" + root.seat
                + "|rootKind=" + root.kind
                + "|rootOptions=" + root.options
                + "|optimalRoot=" + opt
                + "|unique=" + (opt.size() == 1)
                + "|replays=" + s.replays
                + "|noWinner=" + s.noWinner
                + "|capHit=" + s.capHit
                + "|solveSecs=" + String.format("%.1f", tSolve / 1e9)
                + "|totalSecs=" + String.format("%.1f", secs));
    }
}
