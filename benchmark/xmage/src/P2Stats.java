package org.mage.test.benchmark;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/**
 * Online aggregators for Phase 2 decision-density instrumentation.
 * All static: one game at a time per JVM, reset between runs.
 */
public final class P2Stats {

    private P2Stats() {
    }

    // window accounting
    public static long windows = 0;             // every priority window offered
    public static long consults = 0;            // windows where the policy ran
    public static long windowsK0 = 0;           // k == 0 (pass forced)
    public static long windowsK1 = 0;           // k == 1
    public static long windowsK2plus = 0;       // k >= 2
    public static long actsAtK1 = 0;            // acted when k == 1
    public static long actsAtK2plus = 0;        // acted when k >= 2
    public static long yieldSkipped = 0;        // windows auto-passed by a yield

    // act-rate by step (step name -> [windows with k>=1, acts])
    public static final Map<String, long[]> BY_STEP = new TreeMap<>();

    // consecutive-pass run lengths (consulted windows only), capped bucket
    public static final long[] RUN_LENGTH_HIST = new long[257];
    private static int currentRun = 0;

    // sub-action callback counts per action taken, capped bucket
    public static final long[] CALLBACK_HIST = new long[33];
    public static int maxCallbacksSeen = 0;

    public static void reset() {
        windows = consults = windowsK0 = windowsK1 = windowsK2plus = 0;
        actsAtK1 = actsAtK2plus = yieldSkipped = 0;
        BY_STEP.clear();
        java.util.Arrays.fill(RUN_LENGTH_HIST, 0);
        java.util.Arrays.fill(CALLBACK_HIST, 0);
        maxCallbacksSeen = 0;
        currentRun = 0;
    }

    public static void recordWindow(int k, boolean acted, String step) {
        windows++;
        consults++;
        if (k == 0) {
            windowsK0++;
        } else {
            if (k == 1) {
                windowsK1++;
                if (acted) {
                    actsAtK1++;
                }
            } else {
                windowsK2plus++;
                if (acted) {
                    actsAtK2plus++;
                }
            }
            long[] row = BY_STEP.computeIfAbsent(step, s -> new long[2]);
            row[0]++;
            if (acted) {
                row[1]++;
            }
        }
        if (acted) {
            RUN_LENGTH_HIST[Math.min(currentRun, RUN_LENGTH_HIST.length - 1)]++;
            currentRun = 0;
        } else {
            currentRun++;
        }
    }

    public static void recordYieldSkip() {
        windows++;
        yieldSkipped++;
        currentRun++;
    }

    public static void recordActionCallbacks(int n) {
        CALLBACK_HIST[Math.min(n, CALLBACK_HIST.length - 1)]++;
        maxCallbacksSeen = Math.max(maxCallbacksSeen, n);
    }

    public static List<String> report(String label, int games, double totalSec) {
        List<String> out = new ArrayList<>();
        long kGE1 = windowsK1 + windowsK2plus;
        long acts = actsAtK1 + actsAtK2plus;
        out.add(String.format(Locale.ROOT,
                "BENCH|P2.%s.windows|games=%d|windows=%d|consults=%d|yield_skipped=%d|k0=%d|k1=%d|k2plus=%d",
                label, games, windows, consults, yieldSkipped,
                windowsK0, windowsK1, windowsK2plus));
        out.add(String.format(Locale.ROOT,
                "BENCH|P2.%s.act_rate|acts=%d|act_rate_kGE1_pct=%.1f|act_rate_k1_pct=%.1f|act_rate_k2plus_pct=%.1f",
                label, acts,
                100.0 * acts / Math.max(1, kGE1),
                100.0 * actsAtK1 / Math.max(1, windowsK1),
                100.0 * actsAtK2plus / Math.max(1, windowsK2plus)));
        // regimes: no_gate/k0_gate are meaningful on a per-window run
        // (consults==windows); actual_consults is the yield-run number
        out.add(String.format(Locale.ROOT,
                "BENCH|P2.%s.consults_per_game|no_gate=%.1f|k0_gate=%.1f|actual_consults=%.1f|actions_per_game=%.1f|games_per_sec=%.3f",
                label,
                (double) windows / games,
                (double) kGE1 / games,
                (double) consults / games,
                (double) acts / games,
                games / totalSec));
        StringBuilder steps = new StringBuilder("BENCH|P2." + label + ".by_step");
        for (Map.Entry<String, long[]> e : BY_STEP.entrySet()) {
            steps.append(String.format(Locale.ROOT, "|%s=%d/%d",
                    e.getKey().replace(' ', '_'), e.getValue()[1], e.getValue()[0]));
        }
        out.add(steps.toString());
        out.add(histLine("P2." + label + ".run_length", RUN_LENGTH_HIST));
        out.add(histLine("P2." + label + ".callbacks_per_action", CALLBACK_HIST));
        out.add(String.format(Locale.ROOT,
                "BENCH|P2.%s.callbacks_max|max=%d", label, maxCallbacksSeen));
        return out;
    }

    private static String histLine(String label, long[] hist) {
        StringBuilder sb = new StringBuilder("BENCH|" + label);
        for (int i = 0; i < hist.length; i++) {
            if (hist[i] > 0) {
                sb.append(String.format(Locale.ROOT, "|b%d=%d", i, hist[i]));
            }
        }
        return sb.toString();
    }
}
