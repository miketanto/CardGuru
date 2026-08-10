package org.mage.test.benchmark;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.GameState;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.ArrayList;
import java.util.List;

/**
 * Phase 2: how does stepping cost scale with the things real decks have?
 *
 * Axes (each timed as: reset + build board + run turn 1 through turn 3
 * END_TURN with no actions, so the measured quantity is stepping through
 * 3 turns of phases with state-based checks and layer recomputation):
 *   - board size: vanilla creatures {5, 20, 50, 100}
 *   - layer load: continuous effects (Glorious Anthem) {0, 5, 20} over 20 vanillas
 *   - trigger fan-out: Soul Warden count {0, 5, 20}, with 3 scripted
 *     creature casts so each cast fires N triggers
 *   - stack churn: sequential Lightning Bolt casts {0, 3, 10}
 * Each config also reports GameState.copy() cost on the built board.
 */
public class B5ComplexityBenchmark extends CardTestPlayerBase {

    private static final int WARMUP = 5;
    private static final int RUNS = 20;

    private double copyCost() {
        List<Double> t = new ArrayList<>();
        for (int i = 0; i < 15; i++) {
            long t0 = System.nanoTime();
            GameState c = currentGame.getState().copy();
            long t1 = System.nanoTime();
            if (i >= 5) {
                t.add((t1 - t0) / 1e6);
            }
            if (c == null) {
                throw new IllegalStateException();
            }
        }
        double[] s = t.stream().mapToDouble(Double::doubleValue).sorted().toArray();
        return BenchStats.pct(s, 50);
    }

    private interface Builder {
        void build() throws Exception;
    }

    private void bench(String label, Builder builder) throws Exception {
        List<Double> stepT = new ArrayList<>();
        double copyMs = 0;
        for (int i = 0; i < WARMUP + RUNS; i++) {
            long t0 = System.nanoTime();
            reset();
            builder.build();
            setStopAt(3, PhaseStep.END_TURN);
            execute();
            long t1 = System.nanoTime();
            if (i >= WARMUP) {
                stepT.add((t1 - t0) / 1e6);
            }
            if (i == WARMUP + RUNS - 1) {
                copyMs = copyCost();
            }
        }
        System.out.println(BenchStats.report("B5.turns3." + label, stepT));
        System.out.println(String.format(java.util.Locale.ROOT,
                "BENCH|B5.copy_after.%s|median_ms=%.4f", label, copyMs));
    }

    @Test
    public void benchComplexity() throws Exception {
        for (int n : new int[]{5, 20, 50, 100}) {
            final int nn = n;
            bench("board=" + n, () -> {
                addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", nn / 2);
                addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", nn - nn / 2);
            });
        }
        for (int n : new int[]{0, 5, 20}) {
            final int nn = n;
            bench("anthems=" + n, () -> {
                addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", 10);
                addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 10);
                if (nn > 0) {
                    addCard(Zone.BATTLEFIELD, playerA, "Glorious Anthem", nn / 2);
                    addCard(Zone.BATTLEFIELD, playerB, "Glorious Anthem", nn - nn / 2);
                }
            });
        }
        for (int n : new int[]{0, 5, 20}) {
            final int nn = n;
            bench("wardens=" + n + ".casts=3", () -> {
                if (nn > 0) {
                    addCard(Zone.BATTLEFIELD, playerA, "Soul Warden", nn);
                }
                addCard(Zone.BATTLEFIELD, playerA, "Forest", 6);
                addCard(Zone.HAND, playerA, "Grizzly Bears", 3);
                // turns 1 and 3 are playerA's turns (turn 2 is playerB's);
                // second same-phase creature cast must wait for the first to
                // resolve (sorcery timing) - hence waitStackResolved=true
                castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Grizzly Bears", true);
                castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Grizzly Bears");
                castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Grizzly Bears");
            });
        }
        for (int n : new int[]{0, 3, 10}) {
            final int nn = n;
            bench("bolt_churn=" + n, () -> {
                addCard(Zone.BATTLEFIELD, playerA, "Mountain", 12);
                if (nn > 0) {
                    addCard(Zone.HAND, playerA, "Lightning Bolt", nn);
                    for (int c = 0; c < nn; c++) {
                        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA,
                                "Lightning Bolt", playerB);
                    }
                }
            });
        }
    }
}
