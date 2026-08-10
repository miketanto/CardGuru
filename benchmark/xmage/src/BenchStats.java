package org.mage.test.benchmark;

import java.util.Arrays;
import java.util.List;
import java.util.Locale;

/**
 * Distribution reporting for benchmarks: median/p95/stddev over a sample
 * list, emitted as grep-able BENCH| lines on stdout (surefire captures
 * stdout into the .txt report, which the collector parses).
 */
public final class BenchStats {

    private BenchStats() {
    }

    public static String report(String label, List<Double> samplesMs) {
        double[] s = samplesMs.stream().mapToDouble(Double::doubleValue).sorted().toArray();
        double mean = Arrays.stream(s).average().orElse(Double.NaN);
        double sd = Math.sqrt(Arrays.stream(s).map(x -> (x - mean) * (x - mean)).average().orElse(0));
        return String.format(Locale.ROOT,
                "BENCH|%s|n=%d|median_ms=%.4f|p95_ms=%.4f|stddev_ms=%.4f|mean_ms=%.4f|min_ms=%.4f|max_ms=%.4f",
                label, s.length, pct(s, 50), pct(s, 95), sd, mean,
                s.length > 0 ? s[0] : Double.NaN,
                s.length > 0 ? s[s.length - 1] : Double.NaN);
    }

    public static double pct(double[] sorted, double p) {
        if (sorted.length == 0) {
            return Double.NaN;
        }
        int idx = (int) Math.ceil(p / 100.0 * sorted.length) - 1;
        return sorted[Math.max(0, Math.min(sorted.length - 1, idx))];
    }
}
