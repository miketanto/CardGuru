package org.mage.test.benchmark.rl;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

/**
 * Phase 9 optimization 1: the persistent driver JVM.
 *
 * Every league chunk used to pay for a fresh Maven + surefire JVM, then
 * CardScanner.scan() and the plugin/game-type init inside @BeforeClass,
 * before a single game was played. This process pays all of that ONCE and
 * then serves episode-batch jobs over a localhost socket.
 *
 * Run (cwd MUST be Mage.Tests - decks and config/config.xml resolve
 * relative to it, exactly as surefire's working directory did):
 *   java -cp <Mage.Tests classpath> org.mage.test.benchmark.rl.RLDriverServer \
 *        --port 7910
 *
 * Protocol: one job per line, newline-delimited, on a persistent
 * connection. A job line is EXACTLY the -D list the mvn command took:
 *   -Drl.episodes=100 -Drl.agent=search -Drl.opponent=heuristic ...
 * The server applies them as system properties, runs one EpisodeRunner,
 * streams the driver's stdout back line by line, and terminates the job
 * with
 *   RLJOB|done|rc=0            (or RLJOB|done|rc=1 with RLJOB|error|... above)
 * Other commands: "ping" -> RLJOB|pong, "shutdown" -> exits.
 *
 * Jobs are serialized (one at a time) - within a job, -Drl.concurrency=N
 * is what plays games in parallel. Properties are per-JVM global, so the
 * server clears every rl.* property between jobs; the ones that are read
 * into static finals at class load (rl.cardFeatures -> StateEncoder
 * CAND_DIM, rl.phi, rl.noYields, rl.debug) are pinned by the first job
 * and a later job that changes them is REFUSED rather than silently run
 * with the old value.
 */
public class RLDriverServer {

    /** properties frozen into static finals downstream: pin and enforce */
    private static final String[] PINNED = {
            "rl.cardFeatures", "rl.phi", "rl.noYields", "rl.debug",
            // E3 ablations are read in StateEncoder's static initializer,
            // so a job that changes them in a warm JVM would be silently
            // ignored - fail loudly instead
            "rl.ablateState", "rl.ablateCand"};

    private static String[] pinnedValues;
    private static long jobs = 0;

    public static void main(String[] args) throws Exception {
        int port = 7910;
        for (int i = 0; i < args.length - 1; i++) {
            if ("--port".equals(args[i])) {
                port = Integer.parseInt(args[i + 1]);
            }
        }
        long t0 = System.nanoTime();
        // the same one-time init the surefire path did: game types +
        // plugin classloader (MageTestPlayerBase.@BeforeClass), card db
        // scan and the data-collector no-op wiring (RLEpisodeDriver's)
        org.mage.test.serverside.base.MageTestPlayerBase.init();
        mage.cards.repository.CardScanner.scan();
        mage.collectors.DataCollectorServices.init(false, false);
        // warm the lazily-built token index here too: concurrent jobs
        // race its unsynchronized initializer (see EpisodeRunner)
        mage.cards.repository.TokenRepository.instance.init();
        // bind BEFORE announcing readiness: a stale server still holding
        // the port would otherwise let this one print ready, die, and
        // leave the launcher pointing at the old JVM
        try (ServerSocket server = new ServerSocket(port, 8,
                InetAddress.getByName("127.0.0.1"))) {
            System.out.printf("RLSRV|ready|port=%d|init_sec=%.1f|perThreadRandom=%s%n",
                    port, (System.nanoTime() - t0) / 1e9,
                    mage.util.RandomUtil.isPerThread());
            System.out.flush();
            while (true) {
                try (Socket sock = server.accept()) {
                    sock.setTcpNoDelay(true);
                    if (!serve(sock)) {
                        break;      // shutdown requested
                    }
                } catch (Exception e) {
                    System.out.println("RLSRV|conn_error|" + e);
                    System.out.flush();
                }
            }
        }
        System.out.println("RLSRV|bye|jobs=" + jobs);
    }

    /** @return false when the client asked the server to shut down */
    private static boolean serve(Socket sock) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(
                sock.getInputStream(), StandardCharsets.UTF_8));
        PrintWriter out = new PrintWriter(new java.io.OutputStreamWriter(
                sock.getOutputStream(), StandardCharsets.UTF_8), true);
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            if ("shutdown".equals(line)) {
                out.println("RLJOB|bye");
                return false;
            }
            if ("ping".equals(line)) {
                out.println("RLJOB|pong|jobs=" + jobs);
                continue;
            }
            runJob(line, out);
        }
        return true;
    }

    private static void runJob(String jobLine, PrintWriter out)
            throws java.io.UnsupportedEncodingException {
        jobs++;
        long t0 = System.nanoTime();
        try {
            applyProps(jobLine);
        } catch (Exception e) {
            out.println("RLJOB|error|" + e.getMessage());
            out.println("RLJOB|done|rc=1");
            return;
        }
        // capture the runner's stdout so it can be streamed back with the
        // job instead of landing in the server's own log
        ByteArrayOutputStream buf = new ByteArrayOutputStream(1 << 16);
        PrintStream ps = new PrintStream(buf, true, "UTF-8");
        int rc = 0;
        try {
            new EpisodeRunner().run(ps);
        } catch (Throwable e) {
            rc = 1;
            e.printStackTrace(ps);
            out.println("RLJOB|error|" + e);
        }
        ps.flush();
        for (String l : buf.toString("UTF-8").split("\n")) {
            out.println(l);
        }
        out.printf("RLJOB|done|rc=%d|job_sec=%.1f%n", rc,
                (System.nanoTime() - t0) / 1e9);
        System.out.printf("RLSRV|job=%d|rc=%d|sec=%.1f%n", jobs, rc,
                (System.nanoTime() - t0) / 1e9);
        System.out.flush();
    }

    /**
     * Replace every rl.* system property with this job's -D list. Clearing
     * first matters: a stale -Drl.imitateOut from the previous job would
     * otherwise silently keep logging.
     */
    private static void applyProps(String jobLine) {
        List<String> stale = new ArrayList<>();
        for (Object k : System.getProperties().keySet()) {
            String key = String.valueOf(k);
            if (key.startsWith("rl.")) {
                stale.add(key);
            }
        }
        stale.forEach(System::clearProperty);
        for (String tok : jobLine.split("\\s+")) {
            if (!tok.startsWith("-D")) {
                continue;
            }
            String kv = tok.substring(2);
            int eq = kv.indexOf('=');
            if (eq < 0) {
                System.setProperty(kv, "true");
            } else {
                System.setProperty(kv.substring(0, eq), kv.substring(eq + 1));
            }
        }
        String[] now = new String[PINNED.length];
        for (int i = 0; i < PINNED.length; i++) {
            now[i] = System.getProperty(PINNED[i], "");
        }
        if (pinnedValues == null) {
            pinnedValues = now;
            return;
        }
        for (int i = 0; i < PINNED.length; i++) {
            if (!pinnedValues[i].equals(now[i])) {
                throw new IllegalStateException(String.format(
                        "%s is fixed for the life of this JVM (was '%s', job "
                                + "asked for '%s') - start a new server",
                        PINNED[i], pinnedValues[i], now[i]));
            }
        }
    }
}
