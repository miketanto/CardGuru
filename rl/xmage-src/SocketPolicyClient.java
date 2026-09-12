package org.mage.test.benchmark.rl;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.UUID;

/**
 * IPC V1: synchronous newline-delimited JSON over localhost TCP.
 * One consult = one round trip. Kept dependency-free (hand-rolled JSON:
 * the payload is floats, ints and, from v7, card names).
 *
 * Protocol (one JSON object per line):
 *   -> {"t":"consult","s":[...],"c":[[...],...][,"phi":<f>]}  <- {"a":<idx>}
 *   -> {"t":"end","r":<reward>}                               <- {"ok":1}
 * The optional phi field (C2a) carries the raw GameStateEvaluator2 score
 * for potential-based shaping; hello advertises it via "phi":1.
 * v6 (encoderV 6): {"t":"consult","g":..,"e":..,"r":..[,"oe":..],"c":..}.
 * v7 (encoderV 7): the v6 line PLUS the WIRE-V7 keys (rl/WIRE-V7.md):
 *   "wire":7, v7_game, v7_players, v7_ent, v7_ent_name, v7_ent_token,
 *   v7_edges, v7_cand_type, v7_cand, v7_cand_refers, v7_ctr; the hello
 *   carries "wire":7 and the v7 widths. The v6 bytes of a v7 line are the
 *   v6 line's bytes: appendV6 is the one writer for both.
 * The Python side owns trajectories, training, and eval bookkeeping.
 */
public class SocketPolicyClient implements PolicyClient {

    private final Socket socket;
    private final OutputStream out;
    private final BufferedReader in;
    private final StringBuilder sb = new StringBuilder(1 << 14);

    public long roundTrips = 0;
    public long roundTripNanos = 0;
    /** WIRE-V7 §2f: non-PASS candidates whose referents were not emitted
     *  entities (fell back to the player token) - the 3c coverage gate
     *  reads this; and consults that reached the client without a
     *  CandMeta (an unmapped site). */
    public static long v7RefersFallback = 0, v7MetaMissing = 0;

    /** The encoder version THIS SEAT emits. Normally the global
     *  StateEncoder.ENCODER_V; the opponent seat can differ, which is
     *  what makes a v5-vs-v6 match possible in one JVM (see
     *  rl.oppEncoderV in EpisodeRunner). */
    private final int encV;

    public SocketPolicyClient(int port, String mode, int episodes) throws IOException {
        this(port, mode, episodes, StateEncoder.ENCODER_V);
    }

    public SocketPolicyClient(int port, String mode, int episodes, int encV)
            throws IOException {
        this.encV = encV;
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
        if (encV >= 6) {
            hello += String.format(Locale.ROOT,
                    ",\"gdim\":%d,\"edim\":%d,\"emax\":%d,\"rtypes\":%d",
                    StateEncoder.GDIM, StateEncoder.EDIM, StateEncoder.EMAX,
                    StateEncoder.RTYPES);
        }
        if (encV >= 7) {
            hello += v7Hello();
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

    /** WIRE-V7 §1: the v7 hello keys. v7_decks (§5) is not sent yet
     *  (5a); the server treats a missing key as closed lists. */
    private static String v7Hello() {
        StringBuilder h = new StringBuilder(256);
        h.append(",\"wire\":").append(StateEncoder.WIRE_V7)
         .append(",\"card_emb\":");
        jsonString(h, StateEncoder.CARD_EMB);
        h.append(",\"d_c\":").append(StateEncoder.V7_DC)
         .append(",\"v7_dims\":{\"game\":").append(StateEncoder.V7_GDIM)
         .append(",\"player\":").append(StateEncoder.V7_PDIM)
         .append(",\"ent\":").append(StateEncoder.V7_EDIM)
         .append(",\"cand\":").append(StateEncoder.V7_CDIM)
         .append(",\"opp_hand\":").append(StateEncoder.V7_OHDIM)
         .append(",\"opp_deck\":").append(StateEncoder.V7_ODDIM)
         .append(",\"opp_action\":").append(StateEncoder.V7_OADIM)
         .append("},\"v7_rtypes\":").append(StateEncoder.V7_RTYPES)
         .append(",\"v7_ctypes\":").append(StateEncoder.V7_CTYPES)
         .append(",\"v7_zones\":").append(StateEncoder.V7_ZONES)
         .append(",\"v7_emax\":").append(StateEncoder.V7_EMAX)
         .append(",\"v7_kmax\":").append(StateEncoder.V7_KMAX)
         .append(",\"v7_ohmax\":").append(StateEncoder.V7_OHMAX)
         .append(",\"v7_odmax\":").append(StateEncoder.V7_ODMAX)
         .append(",\"v7_oamax\":").append(StateEncoder.V7_OAMAX);
        return h.toString();
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

    private void rows(float[][] m) {
        sb.append('[');
        for (int i = 0; i < m.length; i++) {
            if (i > 0) {
                sb.append(',');
            }
            floats(m[i]);
        }
        sb.append(']');
    }

    private void triples(int[][] m) {
        sb.append('[');
        for (int i = 0; i < m.length; i++) {
            int[] e = m[i];
            if (i > 0) {
                sb.append(',');
            }
            sb.append('[').append(e[0]).append(',').append(e[1])
                    .append(',').append(e[2]).append(']');
        }
        sb.append(']');
    }

    /** JSON string literal with the escapes card names need (quotes in
     *  names, backslashes, control characters). */
    private static void jsonString(StringBuilder b, String s) {
        b.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':
                    b.append("\\\"");
                    break;
                case '\\':
                    b.append("\\\\");
                    break;
                case '\n':
                    b.append("\\n");
                    break;
                case '\r':
                    b.append("\\r");
                    break;
                case '\t':
                    b.append("\\t");
                    break;
                default:
                    if (c < 0x20) {
                        b.append(String.format(Locale.ROOT, "\\u%04x", (int) c));
                    } else {
                        b.append(c);
                    }
            }
        }
        b.append('"');
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

    /** The v6 consult body, from the opening brace to the last v6 key
     *  (no closing brace): globals, entity rows, relation edges, the
     *  critic-only oracle rows, candidates, phi. THE ONE WRITER of the
     *  v6 bytes - the v6 consult and the v7 consult both call it, so a
     *  v7 line's v6 keys are byte-for-byte the v6 line. */
    private void appendV6(StateEncoder.EntityView view, float[][] candidates,
                          float phi) {
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
        sb.append(']');
        // CRITIC-ONLY channel. Emitted as its own key so a server
        // that does not know about it simply ignores it, and so the
        // policy's own "e" is byte-identical either way.
        if (view.oracle.length > 0) {
            sb.append(",\"oe\":[");
            for (int i = 0; i < view.oracle.length; i++) {
                if (i > 0) {
                    sb.append(',');
                }
                floats(view.oracle[i]);
            }
            sb.append(']');
        }
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
    }

    /** Writes sb, reads the reply, returns the candidate index. */
    private int roundTrip() throws IOException {
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
    }

    /** v6 consult: globals, entity rows, relation edges, candidates. */
    @Override
    public int choose(StateEncoder.EntityView view, float[][] candidates,
                      float phi) {
        try {
            sb.setLength(0);
            appendV6(view, candidates, phi);
            sb.append("}\n");
            return roundTrip();
        } catch (IOException e) {
            throw new RuntimeException("policy IPC failed", e);
        }
    }

    /** v7 consult: the v6 line plus the WIRE-V7 keys. A seat below v7,
     *  or a view without the v7 block, is the v6 consult. */
    @Override
    public int choose(StateEncoder.EntityView view, float[][] candidates,
                      float phi, StateEncoder.CandMeta meta) {
        if (encV < 7 || view.v7 == null) {
            return choose(view, candidates, phi);
        }
        try {
            sb.setLength(0);
            appendV6(view, candidates, phi);
            appendV7(view.v7, candidates.length, meta);
            sb.append("}\n");
            return roundTrip();
        } catch (IOException e) {
            throw new RuntimeException("policy IPC failed", e);
        }
    }

    /** The decision type of a consult (game token idx 12..19): the most
     *  frequent non-PASS candidate type, lowest type on a tie; PASS only
     *  when every candidate is a pass. Mixed consults are the priority
     *  window (LAND / SPELL / ACTIVATE together). */
    private static int decisionType(int[] types) {
        int[] count = new int[StateEncoder.V7_CTYPES];
        for (int t : types) {
            if (t > 0 && t < count.length) {
                count[t]++;
            }
        }
        int best = StateEncoder.C_PASS, bestN = 0;
        for (int t = 1; t < count.length; t++) {
            if (count[t] > bestN) {
                best = t;
                bestN = count[t];
            }
        }
        return best;
    }

    private void appendV7(StateEncoder.V7 v7, int k, StateEncoder.CandMeta meta) {
        int[] types = new int[k];
        if (meta == null) {
            v7MetaMissing++;
            java.util.Arrays.fill(types, StateEncoder.C_OTHER);
        } else {
            System.arraycopy(meta.type, 0, types, 0, Math.min(k, meta.type.length));
        }
        sb.append(",\"wire\":").append(StateEncoder.WIRE_V7);
        // game token: idx 0..11 from the encoder, 12..21 per consult here
        float[] g = v7.game.clone();
        g[12 + decisionType(types)] = 1f;
        g[20] = k / 32f;
        g[21] = meta == null ? 0f : meta.consultsSoFar / 200f;
        sb.append(",\"v7_game\":");
        floats(g);
        sb.append(",\"v7_players\":");
        rows(v7.players);
        sb.append(",\"v7_ent\":");
        rows(v7.ent);
        sb.append(",\"v7_ent_name\":[");
        for (int i = 0; i < v7.entName.length; i++) {
            if (i > 0) {
                sb.append(',');
            }
            jsonString(sb, v7.entName[i] == null ? "?" : v7.entName[i]);
        }
        sb.append("],\"v7_ent_token\":[");
        for (int i = 0; i < v7.entToken.length; i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append(v7.entToken[i]);
        }
        sb.append("],\"v7_edges\":");
        triples(v7.edges);
        sb.append(",\"v7_cand_type\":[");
        for (int i = 0; i < k; i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append(types[i]);
        }
        // v7_cand: the type one-hot in idx 0..7; the afterstate slots
        // (idx 8..) are 3b and stay 0 here
        sb.append("],\"v7_cand\":[");
        float[] row = new float[StateEncoder.V7_CDIM];
        for (int i = 0; i < k; i++) {
            if (i > 0) {
                sb.append(',');
            }
            java.util.Arrays.fill(row, 0f);
            row[types[i]] = 1f;
            // PASS / OTHER afterstates are reserved (WIRE §2f; the pass
            // afterstate is deferred, design §6) even where the joint
            // sites could supply one
            float[] af = meta == null || i >= meta.after.length
                    || types[i] == StateEncoder.C_PASS ? null : meta.after[i];
            if (af != null) {
                System.arraycopy(af, 0, row, 8, Math.min(af.length, row.length - 8));
            }
            floats(row);
        }
        // v7_cand_refers: token indices of the entities the candidate
        // acts on. A referent that is not an emitted entity (truncated,
        // or a card in a zone 3a does not emit, e.g. the library) falls
        // back to the acting player's token and is COUNTED: the 3c gate
        // wants this at 0 on the ladder decks.
        sb.append("],\"v7_cand_refers\":[");
        int fallback = 0;
        for (int i = 0; i < k; i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append('[');
            int n = 0;
            UUID[] refs = meta == null || i >= meta.refs.length ? null : meta.refs[i];
            if (refs != null) {
                for (UUID id : refs) {
                    Integer t = v7.token.get(id);
                    if (t != null) {
                        if (n++ > 0) {
                            sb.append(',');
                        }
                        sb.append(t.intValue());
                    }
                }
            }
            if (n == 0 && types[i] != StateEncoder.C_PASS) {
                sb.append(StateEncoder.V7_TOK_ME);
                fallback++;
            }
            sb.append(']');
        }
        v7RefersFallback += fallback;
        sb.append("],\"v7_ctr\":{\"entityTrunc\":").append(v7.entityTrunc)
          .append(",\"refersFallback\":").append(fallback)
          .append(",\"metaMissing\":").append(meta == null ? 1 : 0)
          .append('}');
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
