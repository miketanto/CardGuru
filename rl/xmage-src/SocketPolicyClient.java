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
        String hello = String.format(Locale.ROOT,
                "{\"t\":\"hello\",\"mode\":\"%s\",\"episodes\":%d,\"sdim\":%d,"
                + "\"cdim\":%d,\"phi\":%d",
                mode, episodes, StateEncoder.STATE_DIM, StateEncoder.CAND_DIM,
                Boolean.getBoolean("rl.phi") ? 1 : 0);
        if (StateEncoder.ENCODER_V >= 6) {
            hello += String.format(Locale.ROOT,
                    ",\"gdim\":%d,\"edim\":%d,\"emax\":%d,\"rtypes\":%d",
                    StateEncoder.GDIM, StateEncoder.EDIM, StateEncoder.EMAX,
                    StateEncoder.RTYPES);
        }
        out.write((hello + "}\n").getBytes(StandardCharsets.UTF_8));
        out.flush();
        // READ THE REPLY. It used to be discarded, which meant a server
        // that refused the handshake - because the vectors now mean
        // something else - looked exactly like one that accepted it, and
        // the run died later somewhere unrelated. The server answers
        // {"ok":1} or {"ok":0,"err":"..."}.
        String ack = in.readLine();
        // FAIL CLOSED: anything that is not an explicit ok is a refusal.
        // Matching on "ok":0 instead let a rejection whose JSON happened
        // to be spaced differently through, and the run then died three
        // frames deep in a consult rather than here.
        if (ack == null || !ack.replace(" ", "").contains("\"ok\":1")) {
            throw new IOException("policy server refused the handshake: "
                    + (ack == null ? "connection closed" : ack));
        }
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

    /** v6 consult: globals, entity rows, relation edges, candidates. */
    @Override
    public int choose(StateEncoder.EntityView view, float[][] candidates,
                      float phi) {
        try {
            sb.setLength(0);
            sb.append("{\"t\":\"consult\",\"g\":");
            floats(view.globals);
            sb.append(",\"e\":[");
            for (int i = 0; i < view.entities.length; i++) {
                if (i > 0) {
                    sb.append(',');
                }
                floats(view.entities[i]);
            }
            sb.append("],\"r\":[");
            for (int i = 0; i < view.relations.length; i++) {
                int[] e = view.relations[i];
                if (i > 0) {
                    sb.append(',');
                }
                sb.append('[').append(e[0]).append(',').append(e[1])
                        .append(',').append(e[2]).append(']');
            }
            sb.append("],\"c\":[");
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
            if (line == null) {
                // the server rejected the consult and died - a relation
                // index out of range, a row of the wrong width. Say so
                // here rather than NPEing on the parse below.
                throw new IOException("policy server closed mid-consult "
                        + "(see the server log: it prints the reason)");
            }
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
