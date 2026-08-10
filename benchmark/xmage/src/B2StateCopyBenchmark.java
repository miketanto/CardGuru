package org.mage.test.benchmark;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.GameState;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.ArrayList;
import java.util.List;

/**
 * B2: GameState.copy() and GameState.restore() cost across board sizes
 * {5, 20, 50, 100} permanents, with and without a populated graveyard.
 * The engine's own rollback path (bookmarkState/restoreState) uses
 * exactly this machinery, and the AI relies on it for simulation - if
 * copy is much cheaper than B1 setup, environment resets should come
 * from a snapshot pool, not scenario reconstruction.
 */
public class B2StateCopyBenchmark extends CardTestPlayerBase {

    private static final int WARMUP = 10;
    private static final int RUNS = 30;

    private void buildBoard(int permanents, boolean graveyard) throws Exception {
        reset();
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", permanents / 2);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", permanents - permanents / 2);
        if (graveyard) {
            addCard(Zone.GRAVEYARD, playerA, "Lightning Bolt", 15);
            addCard(Zone.GRAVEYARD, playerB, "Grizzly Bears", 15);
        }
        setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
        execute();
    }

    private void benchOne(String label, int permanents, boolean graveyard) throws Exception {
        buildBoard(permanents, graveyard);
        List<Double> copyT = new ArrayList<>();
        List<Double> restoreT = new ArrayList<>();
        GameState snapshot = currentGame.getState().copy();
        for (int i = 0; i < WARMUP + RUNS; i++) {
            long t0 = System.nanoTime();
            GameState c = currentGame.getState().copy();
            long t1 = System.nanoTime();
            if (i >= WARMUP) {
                copyT.add((t1 - t0) / 1e6);
            }
            if (c == null) {
                throw new IllegalStateException("copy returned null");
            }
        }
        for (int i = 0; i < WARMUP + RUNS; i++) {
            long t0 = System.nanoTime();
            currentGame.getState().restore(snapshot);
            long t1 = System.nanoTime();
            if (i >= WARMUP) {
                restoreT.add((t1 - t0) / 1e6);
            }
        }
        System.out.println(BenchStats.report("B2.copy." + label, copyT));
        System.out.println(BenchStats.report("B2.restore." + label, restoreT));
    }

    @Test
    public void benchStateCopy() throws Exception {
        for (int n : new int[]{5, 20, 50, 100}) {
            benchOne("permanents=" + n, n, false);
        }
        benchOne("permanents=50.graveyard=30", 50, true);
    }
}
