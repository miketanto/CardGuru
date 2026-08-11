package org.mage.test.benchmark.rl;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * IPC V1: synchronous newline-delimited JSON over localhost TCP.
 * One consult = one round trip. Kept dependency-free (hand-rolled JSON:
 * the payload is floats and ints only).
 *
 * Protocol (one JSON object per line):
 *   -> {"t":"consult","s":[...],"c":[[...],...][,"phi":<f>]}  <- {"a":<idx>}
 *   -> {"t":"end","r":<reward>}                               <- {"ok":1}
 * The optional phi field (C2a) carries the raw GameStateEvaluator2 score
 * for potential-based shaping; hello advertises it via "phi":1.
 * The Python side owns trajectories, training, and eval bookkeeping.
 */
public class SocketPolicyClient implements PolicyClient {

    private final Socket socket;
    private final OutputStream out;
    private final BufferedReader in;
    private final StringBuilder sb = new StringBuilder(1 << 14);

    public long roundTrips = 0;
    public long roundTripNanos = 0;

    public SocketPolicyClient(int port, String mode, int episodes) throws IOException {
        socket = new Socket("127.0.0.1", port);
        socket.setTcpNoDelay(true);
        out = socket.getOutputStream();
        in = new BufferedReader(new InputStreamReader(
                socket.getInputStream(), StandardCharsets.UTF_8));
        out.write(String.format(Locale.ROOT,
                "{\"t\":\"hello\",\"mode\":\"%s\",\"episodes\":%d,\"sdim\":%d,\"cdim\":%d,\"phi\":%d}%n",
                mode, episodes, StateEncoder.STATE_DIM, StateEncoder.CAND_DIM,
                Boolean.getBoolean("rl.phi") ? 1 : 0)
                .getBytes(StandardCharsets.UTF_8));
        out.flush();
        in.readLine();
    }

    private void floats(float[] v) {
        sb.append('[');
        for (int i = 0; i < v.length; i++) {
            if (i > 0) {
                sb.append(',');
            }
            // 4 decimals is plenty for normalized features and keeps lines short
            sb.append(String.format(Locale.ROOT, "%.4f", v[i]));
        }
        sb.append(']');
    }

    @Override
    public int choose(float[] state, float[][] candidates) {
        return choose(state, candidates, 0f);
    }

    @Override
    public int choose(float[] state, float[][] candidates, float phi) {
        try {
            sb.setLength(0);
            sb.append("{\"t\":\"consult\",\"s\":");
            floats(state);
            sb.append(",\"c\":[");
            for (int i = 0; i < candidates.length; i++) {
                if (i > 0) {
                    sb.append(',');
                }
                floats(candidates[i]);
            }
            sb.append(']');
            if (phi != 0f) {
                sb.append(",\"phi\":")
                        .append(String.format(Locale.ROOT, "%.1f", phi));
            }
            sb.append("}\n");
            long t0 = System.nanoTime();
            out.write(sb.toString().getBytes(StandardCharsets.UTF_8));
            out.flush();
            String line = in.readLine();
            roundTripNanos += System.nanoTime() - t0;
            roundTrips++;
            int p = line.indexOf(':');
            return Integer.parseInt(
                    line.substring(p + 1, line.indexOf('}')).trim());
        } catch (IOException e) {
            throw new RuntimeException("policy IPC failed", e);
        }
    }

    @Override
    public void episodeEnd(float reward) {
        try {
            out.write(String.format(Locale.ROOT, "{\"t\":\"end\",\"r\":%.1f}%n", reward)
                    .getBytes(StandardCharsets.UTF_8));
            out.flush();
            in.readLine();
        } catch (IOException e) {
            throw new RuntimeException("policy IPC failed", e);
        }
    }

    @Override
    public void close() {
        try {
            socket.close();
        } catch (IOException ignored) {
        }
    }
}
