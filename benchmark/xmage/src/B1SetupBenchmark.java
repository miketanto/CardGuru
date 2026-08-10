package org.mage.test.benchmark;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.ArrayList;
import java.util.List;

/**
 * B1: scenario setup cost - fresh game object through addCard x N and
 * execute() on a board of vanilla creatures that does nothing.
 * Sweeps N in {2, 8, 20, 50}. Also reports the reset()-only cost
 * (game + deck construction) so setup can be decomposed.
 */
public class B1SetupBenchmark extends CardTestPlayerBase {

    private static final int WARMUP = 5;
    private static final int RUNS = 30;

    @Test
    public void benchScenarioSetup() throws Exception {
        // reset-only baseline: game object + deck load, no board, no run
        List<Double> resetOnly = new ArrayList<>();
        for (int i = 0; i < WARMUP + RUNS; i++) {
            long t0 = System.nanoTime();
            reset();
            long t1 = System.nanoTime();
            if (i >= WARMUP) {
                resetOnly.add((t1 - t0) / 1e6);
            }
        }
        System.out.println(BenchStats.report("B1.reset_only", resetOnly));

        for (int n : new int[]{2, 8, 20, 50}) {
            List<Double> full = new ArrayList<>();
            List<Double> execOnly = new ArrayList<>();
            for (int i = 0; i < WARMUP + RUNS; i++) {
                long t0 = System.nanoTime();
                reset();
                addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", n / 2);
                addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", n - n / 2);
                setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
                long t1 = System.nanoTime();
                execute();
                long t2 = System.nanoTime();
                if (i >= WARMUP) {
                    full.add((t2 - t0) / 1e6);
                    execOnly.add((t2 - t1) / 1e6);
                }
            }
            System.out.println(BenchStats.report("B1.setup_full.permanents=" + n, full));
            System.out.println(BenchStats.report("B1.execute_only.permanents=" + n, execOnly));
        }
    }
}
