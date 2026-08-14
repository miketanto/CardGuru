package org.mage.test.benchmark.rl;

import mage.cards.decks.Deck;
import mage.cards.decks.DeckCardLists;
import mage.cards.decks.importer.DeckImporter;
import mage.cards.repository.CardInfo;
import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.Game;
import mage.game.GameOptions;
import mage.game.TwoPlayerDuel;
import mage.game.mulligan.MulliganType;
import mage.players.Player;
import mage.util.RandomUtil;
import mage.util.ThreadUtils;
import org.mage.test.benchmark.HeuristicPlayer;
import org.mage.test.benchmark.RandomPlayer;

import java.io.PrintStream;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Phase 9: the episode loop, lifted verbatim out of {@link RLEpisodeDriver}
 * so it can be driven by something other than a fresh surefire JVM.
 * Two callers:
 *   - RLEpisodeDriver (the @Test): unchanged mvn path, sequential;
 *   - RLDriverServer: one long-lived JVM, many jobs.
 *
 * Everything is still configured through rl.* system properties, so a job
 * is literally the same -D list the mvn command line took. Two properties
 * are read ONCE per JVM (they land in static finals downstream) and the
 * server refuses jobs that change them: rl.cardFeatures (fixes
 * StateEncoder.CAND_DIM at class load).
 *
 * Phase 9 additions, both opt-in and off by default:
 *   -Drl.concurrency=N   play N episodes at a time on N threads
 *   -Drl.deckCache=true  parse each .dck file once per JVM
 * Sequential, cache-off behavior is bit-identical to the pre-Phase-9
 * driver (the only structural change is that the CardInfo cache is a
 * field instead of MageTestPlayerBase's static - same contents, same
 * lifetime within a run).
 */
public class EpisodeRunner {

    /** db card cache: Deck.load memoizes name -> CardInfo lookups here */
    private final Map<String, CardInfo> cardCache = new ConcurrentHashMap<>();
    /** rl.deckCache: parsed deck lists, reused across episodes */
    private final Map<String, DeckCardLists> deckCache = new ConcurrentHashMap<>();

    /** C1 imitation log (rl.imitateOut): open across all episodes */
    private java.io.PrintWriter imitateOut;

    /** C5 league: rl.opponent=rl - a second policy seat, served by its
     *  own (frozen, eval-mode) server on rl.oppPort */
    private PolicyClient oppPolicy;
    /** concurrent rl-vs-rl: each worker gets its own opponent
     *  connection (the opponent server must run --threads >= N) */
    private final ThreadLocal<PolicyClient> oppPolicyLocal = new ThreadLocal<>();

    private final boolean deckCacheOn = Boolean.getBoolean("rl.deckCache");

    /** sequential path only: kept so the RL|ipc line still trails the
     *  summary exactly as the pre-Phase-9 driver printed it */
    private SocketPolicyClient seqSocket;

    private Deck loadDeck(String name) throws Exception {
        DeckCardLists list;
        if (deckCacheOn) {
            list = deckCache.get(name);
            if (list == null) {
                list = DeckImporter.importDeckFromFile(name, true);
                deckCache.put(name, list);
            }
        } else {
            list = DeckImporter.importDeckFromFile(name, true);
        }
        Deck deck;
        // Deck.load mutates the shared CardInfo cache; the concurrent map
        // handles the writes, the lock keeps a half-built deck out of a
        // second thread's view of the importer's static state
        synchronized (EpisodeRunner.class) {
            deck = Deck.load(list, false, false, cardCache);
        }
        if (deck.getMaindeckCards().size() < 40) {
            throw new IllegalStateException("deck load failed: " + name
                    + " -> " + deck.getMaindeckCards().size() + " cards");
        }
        return deck;
    }

    static class EpisodeResult {
        float reward;
        int turns;
        long consults;
        long windows;
        long actions;
        boolean stalled;
    }

    private EpisodeResult playEpisode(PolicyClient policy, Map<String, Integer> fallbacks,
                                      long seed, String opponentKind,
                                      String deckName, String oppDeckName, int stopTurn,
                                      boolean agentOnPlay) throws Exception {
        Game game = new TwoPlayerDuel(MultiplayerAttackOption.LEFT, RangeOfInfluence.ONE,
                MulliganType.GAME_DEFAULT.getMulligan(0), 60, 20, 7);
        // fresh player objects every episode: a finished game marks its
        // players lost/left, and those flags survive reuse (found the hard
        // way - a reused agent instantly loses every game after its first)
        // seat A: RL agent by default; -Drl.agent=heuristic|search turns the
        // driver into a scripted-vs-scripted match harness (ladder calibration)
        String agentKind = System.getProperty("rl.agent", "rl");
        Player agent;
        RLPlayer rlAgent = null;
        if ("heuristic".equals(agentKind)) {
            HeuristicPlayer h = new HeuristicPlayer("Agent");
            h.benchSeed = seed;
            h.setTestMode(true);
            agent = h;
        } else if ("search".equals(agentKind)) {
            org.mage.test.benchmark.SearchPlayer sp =
                    new org.mage.test.benchmark.SearchPlayer("Agent");
            sp.benchSeed = seed;
            sp.searchPlies = Integer.getInteger("rl.agentPlies", 1);
            sp.searchBreadth = Integer.getInteger("rl.agentBreadth", 8);
            sp.setTestMode(true);
            agent = sp;
        } else if ("searchip".equals(agentKind)) {
            org.mage.test.benchmark.SearchPlayerIP sp =
                    new org.mage.test.benchmark.SearchPlayerIP("Agent");
            sp.benchSeed = seed;
            sp.searchPlies = Integer.getInteger("rl.agentPlies", 1);
            sp.searchBreadth = Integer.getInteger("rl.agentBreadth", 8);
            sp.determinizations = Integer.getInteger("rl.agentDetK", 4);
            sp.setTestMode(true);
            agent = sp;
        } else if ("searchhold".equals(agentKind)) {
            org.mage.test.benchmark.SearchPlayerHold sp =
                    new org.mage.test.benchmark.SearchPlayerHold("Agent");
            sp.benchSeed = seed;
            sp.searchPlies = Integer.getInteger("rl.agentPlies", 1);
            sp.searchBreadth = Integer.getInteger("rl.agentBreadth", 8);
            sp.setTestMode(true);
            agent = sp;
        } else if ("teacher".equals(agentKind)) {
            TeacherLogPlayer tp = new TeacherLogPlayer("Agent");
            tp.benchSeed = seed;
            tp.searchPlies = Integer.getInteger("rl.agentPlies", 1);
            tp.searchBreadth = Integer.getInteger("rl.agentBreadth", 8);
            tp.daggerEps = Double.parseDouble(
                    System.getProperty("rl.daggerEps", "0"));
            if (Boolean.getBoolean("rl.teacherHold")) {
                // C7: D1h teacher - hold flash threats, cast at instant
                // speed (the draw-go prior the students imitate)
                tp.holdFlashAtMain = true;
                tp.holdFlashSearch = true;
            }
            tp.out = imitateOut;
            tp.setTestMode(true);
            agent = tp;
        } else {
            rlAgent = new RLPlayer("Agent");
            rlAgent.policy = policy;
            rlAgent.resetPerEpisode();
            rlAgent.benchSeed = seed;
            rlAgent.shadowOut = imitateOut;   // C3 true-DAgger labels
            rlAgent.setTestMode(true);
            agent = rlAgent;
        }

        Player opp;
        if ("rl".equals(opponentKind)) {
            RLPlayer r = new RLPlayer("Opponent");
            r.policy = oppPolicyLocal.get() != null
                    ? oppPolicyLocal.get() : oppPolicy;
            r.resetPerEpisode();
            r.benchSeed = seed;
            r.setTestMode(true);
            opp = r;
        } else if ("search".equals(opponentKind)) {
            org.mage.test.benchmark.SearchPlayer sp =
                    new org.mage.test.benchmark.SearchPlayer("Opponent");
            sp.benchSeed = seed;
            sp.searchPlies = Integer.getInteger("rl.searchPlies", 1);
            sp.searchBreadth = Integer.getInteger("rl.searchBreadth", 8);
            sp.setTestMode(true);
            opp = sp;
        } else if ("searchhold".equals(opponentKind)) {
            org.mage.test.benchmark.SearchPlayerHold sp =
                    new org.mage.test.benchmark.SearchPlayerHold("Opponent");
            sp.benchSeed = seed;
            sp.searchPlies = Integer.getInteger("rl.searchPlies", 1);
            sp.searchBreadth = Integer.getInteger("rl.searchBreadth", 8);
            sp.setTestMode(true);
            opp = sp;
        } else if ("searchip".equals(opponentKind)) {
            org.mage.test.benchmark.SearchPlayerIP sp =
                    new org.mage.test.benchmark.SearchPlayerIP("Opponent");
            sp.benchSeed = seed;
            sp.searchPlies = Integer.getInteger("rl.searchPlies", 1);
            sp.searchBreadth = Integer.getInteger("rl.searchBreadth", 8);
            sp.determinizations = Integer.getInteger("rl.detK", 4);
            sp.setTestMode(true);
            opp = sp;
        } else if ("heuristic".equals(opponentKind)) {
            HeuristicPlayer h = new HeuristicPlayer("Opponent");
            h.benchSeed = seed;
            h.setTestMode(true);
            opp = h;
        } else {
            RandomPlayer r = new RandomPlayer("Opponent");
            r.setTestMode(true);
            opp = r;
        }

        // Phase 7c: the opponent seat may pilot a DIFFERENT archetype deck
        // (rl.oppDeck); unset keeps the historical mirror behaviour.
        // Decks bind to SEATS, not to play order: with asymmetric decks the
        // old order-bound version handed the agent the opponent's list on
        // every other episode (harmless while every match was a mirror).
        Deck agentDeck = loadDeck(deckName);
        Deck oppDeck = loadDeck(oppDeckName == null ? deckName : oppDeckName);
        Player first = agentOnPlay ? agent : opp;
        Player second = agentOnPlay ? opp : agent;
        Deck deckFirst = agentOnPlay ? agentDeck : oppDeck;
        Deck deckSecond = agentOnPlay ? oppDeck : agentDeck;
        game.loadCards(deckFirst.getCards(), first.getId());
        game.loadCards(deckSecond.getCards(), second.getId());
        game.addPlayer(first, deckFirst);
        game.addPlayer(second, deckSecond);

        GameOptions options = new GameOptions();
        options.testMode = false;      // real opening hands (Phase 2 erratum)
        options.stopOnTurn = stopTurn;
        options.stopAtStep = PhaseStep.END_TURN;
        game.setGameOptions(options);
        RandomUtil.setSeed(seed);
        game.start(first.getId());

        EpisodeResult r = new EpisodeResult();
        r.turns = game.getTurnNum();
        if (rlAgent != null) {
            r.consults = rlAgent.consults;
            r.windows = rlAgent.windows;
            r.actions = rlAgent.actions;
            rlAgent.fallbackCalls.forEach((k, v) -> fallbacks.merge(k, v, Integer::sum));
            if (rlAgent.shadowExamples > 0) {
                fallbacks.merge("shadowExamples", (int) rlAgent.shadowExamples, Integer::sum);
            }
            fallbacks.merge("flashThreats", (int) rlAgent.flashThreatCasts, Integer::sum);
            fallbacks.merge("flashThreatsOppTurn", (int) rlAgent.flashThreatCastsOppTurn, Integer::sum);
            fallbacks.merge("blocksDeclared", (int) rlAgent.blocksDeclared, Integer::sum);
            fallbacks.merge("blockOpportunities", (int) rlAgent.blockOpportunities, Integer::sum);
            // Phase 12 (perf scoping): priority windows where getPlayable
            // came back empty, i.e. the seat paid a full state copy - 67%
            // of game-thread time lives under createSimulationForPlayableCalc
            // - only to discover it had nothing to do and pass. This is the
            // denominator for "is a cheap can-I-act-at-all pre-check worth
            // building"; it was counted in RLPlayer but never surfaced.
            fallbacks.merge("autoPassEmpty", (int) rlAgent.autoPassK0, Integer::sum);
            fallbacks.merge("windows", (int) rlAgent.windows, Integer::sum);
        }
        if (agent instanceof org.mage.test.benchmark.SearchPlayer) {
            org.mage.test.benchmark.SearchPlayer sp = (org.mage.test.benchmark.SearchPlayer) agent;
            fallbacks.merge("agentSearchNodes", (int) Math.min(Integer.MAX_VALUE, sp.nodesEvaluated), Integer::sum);
            fallbacks.merge("agentSearchDecisions", (int) sp.searchDecisions, Integer::sum);
        }
        if (agent instanceof TeacherLogPlayer) {
            TeacherLogPlayer tp = (TeacherLogPlayer) agent;
            fallbacks.merge("teacherExamples", (int) tp.examples, Integer::sum);
            fallbacks.merge("teacherUnmatched", (int) tp.unmatched, Integer::sum);
            fallbacks.merge("daggerDeviations", (int) tp.daggerDeviations, Integer::sum);
        }
        if (opp instanceof org.mage.test.benchmark.SearchPlayer) {
            org.mage.test.benchmark.SearchPlayer sp = (org.mage.test.benchmark.SearchPlayer) opp;
            fallbacks.merge("searchNodes", (int) Math.min(Integer.MAX_VALUE, sp.nodesEvaluated), Integer::sum);
            fallbacks.merge("searchDecisions", (int) sp.searchDecisions, Integer::sum);
        }
        String winner = String.valueOf(game.getWinner());
        if (Boolean.getBoolean("rl.debug")) {
            System.out.println("RLDBG|ep seed=" + seed + " turns=" + r.turns
                    + " winner=" + winner + " agentLife=" + agent.getLife()
                    + " agentLib=" + agent.getLibrary().size()
                    + " agentHand=" + agent.getHand().size()
                    + " consults=" + (rlAgent != null ? rlAgent.consults : 0));
            if (rlAgent != null) {
                System.out.println("RLGAME|reward=" + r.reward + "|seed=" + seed
                        + "\n" + rlAgent.actionLog + "RLGAME_END");
            }
        }
        if (winner.contains(agent.getName())) {
            r.reward = 1f;
        } else if (winner.contains("Opponent")) {
            r.reward = -1f;
        } else {
            r.reward = 0f;      // draw or stall bound: deliberate, documented
            r.stalled = !game.hasEnded();
        }
        return r;
    }

    /** aggregate counters, shared by the sequential and concurrent loops */
    private static final class Totals {
        int wins, losses, draws, stalls;
        long consults, windows, actions;
        double turns;

        synchronized void add(EpisodeResult r) {
            if (r.reward > 0) {
                wins++;
            } else if (r.reward < 0) {
                losses++;
            } else {
                draws++;
                if (r.stalled) {
                    stalls++;
                }
            }
            consults += r.consults;
            windows += r.windows;
            actions += r.actions;
            turns += r.turns;
        }

        synchronized int done() {
            return wins + losses + draws;
        }
    }

    /**
     * The whole run. Returns the RL|summary line (also printed to out,
     * and appended to rl.out when set) so a caller can gate on it.
     */
    public String run(PrintStream out) throws Exception {
        int episodes = Integer.getInteger("rl.episodes", 100);
        String opponent = System.getProperty("rl.opponent", "random");
        String policyKind = System.getProperty("rl.policy", "random");
        int port = Integer.getInteger("rl.port", 7777);
        // comma-separated list = Task C training pool; episode i plays a
        // mirror of decks[i % n] so every deck gets equal exposure
        String[] decks = System.getProperty("rl.deck", "BenchBurn.dck").split(",");
        // Phase 7c: opponent-seat deck list. Unset => mirror (historical).
        String oppDeckProp = System.getProperty("rl.oppDeck");
        final String[] oppDecks = oppDeckProp == null ? null : oppDeckProp.split(",");
        long seed = Long.getLong("rl.seed", 0L);
        int stopTurn = Integer.getInteger("rl.stopTurn", 60);
        int report = Integer.getInteger("rl.report", 100);
        int concurrency = Math.max(1, Integer.getInteger("rl.concurrency", 1));
        String mode = System.getProperty("rl.mode", "train");

        Map<String, Integer> fallbacks = java.util.Collections.synchronizedMap(
                new java.util.TreeMap<>());
        String imitatePath = System.getProperty("rl.imitateOut");
        if (imitatePath != null) {
            imitateOut = new java.io.PrintWriter(new java.io.BufferedWriter(
                    new java.io.FileWriter(imitatePath, true)));
        }
        if ("rl".equals(opponent) && concurrency == 1) {
            // concurrent mode opens one opponent connection per worker
            // inside runConcurrent instead of sharing this one
            oppPolicy = new SocketPolicyClient(
                    Integer.getInteger("rl.oppPort", port + 1), "eval", episodes);
        }

        Totals t = new Totals();
        long t0 = System.nanoTime();
        if (concurrency == 1) {
            PolicyClient policy = "socket".equals(policyKind)
                    ? new SocketPolicyClient(port, mode, episodes)
                    : new RandomPolicyClient(seed);
            for (int i = 0; i < episodes; i++) {
                EpisodeResult r = playEpisode(policy, fallbacks, seed + i, opponent,
                        decks[i % decks.length].trim(),
                        oppDecks == null ? null : oppDecks[i % oppDecks.length].trim(),
                        stopTurn, i % 2 == 0);
                policy.episodeEnd(r.reward);
                if (imitateOut != null) {
                    imitateOut.println("{\"t\":\"end\",\"r\":" + r.reward + "}");
                    imitateOut.flush();
                }
                t.add(r);
                if (report > 0 && (i + 1) % report == 0) {
                    double sec = (System.nanoTime() - t0) / 1e9;
                    out.println(String.format(Locale.ROOT,
                            "RL|progress|ep=%d|win_rate=%.3f|games_per_sec=%.2f",
                            i + 1, t.wins / (double) (i + 1), (i + 1) / sec));
                }
            }
            seqSocket = policy instanceof SocketPolicyClient
                    ? (SocketPolicyClient) policy : null;
            policy.close();
        } else {
            runConcurrent(out, t, fallbacks, episodes, concurrency, opponent,
                    policyKind, port, decks, oppDecks, seed, stopTurn, report,
                    mode, t0);
        }
        double sec = (System.nanoTime() - t0) / 1e9;
        StringBuilder fb = new StringBuilder();
        fallbacks.forEach((k, v) -> fb.append(k).append('=').append(v).append(' '));
        String line = String.format(Locale.ROOT,
                "RL|summary|episodes=%d|wins=%d|losses=%d|draws=%d|stalls=%d"
                        + "|win_rate=%.4f|games_per_sec=%.3f"
                        + "|agent_consults_per_ep=%.1f|agent_windows_per_ep=%.1f"
                        + "|agent_actions_per_ep=%.1f|turns_per_ep=%.1f"
                        + "|opponent=%s|policy=%s|deck=%s|oppDeck=%s|seed=%d|fallbacks=%s",
                episodes, t.wins, t.losses, t.draws, t.stalls,
                t.wins / (double) episodes, episodes / sec,
                t.consults / (double) episodes,
                t.windows / (double) episodes,
                t.actions / (double) episodes,
                t.turns / episodes,
                opponent, policyKind, String.join(",", decks),
                oppDecks == null ? "mirror" : String.join(",", oppDecks), seed, fb);
        out.println(line);
        if (seqSocket != null) {
            out.println(String.format(Locale.ROOT,
                    "RL|ipc|round_trips=%d|avg_rtt_us=%.1f|ipc_sec_total=%.1f",
                    seqSocket.roundTrips,
                    seqSocket.roundTripNanos / 1e3 / Math.max(1, seqSocket.roundTrips),
                    seqSocket.roundTripNanos / 1e9));
            seqSocket = null;
        }
        // -Dmage.playableCache: report the memo's hit rate so a run can
        // never claim the speedup without showing the cache did work
        if (!"off".equals(System.getProperty("mage.playableCache", "off"))) {
            out.printf(Locale.ROOT, "RL|playableMemo|mode=%s|hits=%d|misses=%d"
                            + "|mismatches=%d%n",
                    System.getProperty("mage.playableCache"),
                    mage.players.PlayerImpl.PLAYABLE_MEMO_HITS.get(),
                    mage.players.PlayerImpl.PLAYABLE_MEMO_MISSES.get(),
                    mage.players.PlayerImpl.PLAYABLE_MEMO_MISMATCHES.get());
        }
        String outFile = System.getProperty("rl.out");
        if (outFile != null) {
            java.nio.file.Files.write(java.nio.file.Paths.get(outFile),
                    (line + "\n").getBytes(java.nio.charset.StandardCharsets.UTF_8),
                    java.nio.file.StandardOpenOption.CREATE,
                    java.nio.file.StandardOpenOption.APPEND);
        }
        if (imitateOut != null) {
            imitateOut.close();
            imitateOut = null;
        }
        if (oppPolicy != null) {
            oppPolicy.close();
            oppPolicy = null;
        }
        return line;
    }

    /**
     * -Drl.concurrency=N: N worker threads, each pulling the next episode
     * index off a shared counter. Episode i keeps ITS seed (seed+i) and
     * ITS play/draw parity (i%2), so the set of games played is exactly
     * the sequential set - only the order they finish in changes.
     *
     * Per-thread state, deliberately:
     *   - one PolicyClient per worker (socket: one connection each, which
     *     needs a server that accepts N connections; random: seeded
     *     seed+worker so the streams don't alias);
     *   - RandomUtil must be per-thread or the games shred each other's
     *     stream - RLDriverServer sets mage.randomPerThread for us, and
     *     we fail fast here rather than silently produce garbage.
     * The IPC counters printed by the sequential path are per-client, so
     * the RL|ipc line is omitted in concurrent mode.
     */
    private void runConcurrent(PrintStream out, Totals t, Map<String, Integer> fallbacks,
                               int episodes, int concurrency, String opponent,
                               String policyKind, int port, String[] decks,
                               String[] oppDecks, long seed, int stopTurn,
                               int report, String mode, long t0) throws Exception {
        // TokenRepository.init() is an unsynchronized lazy initializer
        // guarded by "allTokens is not empty": a second thread walks in
        // between the assignment and the indexing and streams a
        // half-built index (ConcurrentModificationException out of
        // GameImpl.initGameDefaultHelperEmblems, ~1 job in 15). Force it
        // to completion on this thread before any worker starts - init
        // is idempotent once the list is populated.
        mage.cards.repository.TokenRepository.instance.init();
        if (!mage.util.RandomUtil.isPerThread()) {
            throw new IllegalStateException(
                    "rl.concurrency>1 requires -Dmage.randomPerThread=true "
                            + "(a shared RandomUtil stream is not reproducible "
                            + "across interleaved games)");
        }
        // rl-vs-rl concurrency: supported since Phase 7b - each worker
        // opens its own opponent connection below; the opponent server
        // must be started with --threads >= concurrency
        final int oppPort = Integer.getInteger("rl.oppPort", port + 1);
        AtomicInteger next = new AtomicInteger(0);
        java.util.List<Throwable> errors =
                java.util.Collections.synchronizedList(new java.util.ArrayList<>());
        Thread[] workers = new Thread[concurrency];
        for (int w = 0; w < concurrency; w++) {
            final int worker = w;
            final int[] lastEpisode = {-1};
            workers[w] = new Thread(() -> {
                PolicyClient policy = null;
                PolicyClient oppClient = null;
                try {
                    policy = "socket".equals(policyKind)
                            ? new SocketPolicyClient(port, mode, episodes)
                            : new RandomPolicyClient(seed + worker);
                    if ("rl".equals(opponent)) {
                        oppClient = new SocketPolicyClient(oppPort, "eval", episodes);
                        oppPolicyLocal.set(oppClient);
                    }
                    int i;
                    while ((i = next.getAndIncrement()) < episodes) {
                        lastEpisode[0] = i;
                        EpisodeResult r = playEpisode(policy, fallbacks, seed + i,
                                opponent, decks[i % decks.length].trim(),
                                oppDecks == null ? null : oppDecks[i % oppDecks.length].trim(),
                                stopTurn, i % 2 == 0);
                        policy.episodeEnd(r.reward);
                        synchronized (EpisodeRunner.this) {
                            if (imitateOut != null) {
                                imitateOut.println("{\"t\":\"end\",\"r\":" + r.reward + "}");
                                imitateOut.flush();
                            }
                        }
                        t.add(r);
                        int done = t.done();
                        if (report > 0 && done % report == 0) {
                            double sec = (System.nanoTime() - t0) / 1e9;
                            out.println(String.format(Locale.ROOT,
                                    "RL|progress|ep=%d|win_rate=%.3f|games_per_sec=%.2f",
                                    done, t.wins / (double) done, done / sec));
                        }
                    }
                } catch (Throwable e) {
                    // print here as well as rethrowing: the job reply only
                    // carries the first failure, and a flaky episode is
                    // worth having the seed for in the server log
                    System.out.println("RLSRV|episode_failed|worker=" + worker
                            + "|episode=" + lastEpisode[0]
                            + "|seed=" + (seed + lastEpisode[0]) + "|" + e);
                    e.printStackTrace(System.out);
                    System.out.flush();
                    errors.add(e);
                } finally {
                    if (policy != null) {
                        policy.close();
                    }
                    if (oppClient != null) {
                        oppClient.close();
                    }
                    oppPolicyLocal.remove();
                }
            // the GAME prefix is load-bearing: ThreadUtils.isRunGameThread
            // gates engine code (checkConcede, state checks) by thread name
            // and only "main" or a GAME*/AI-SIM-* thread may run a game.
            // Naming the workers is the fix the engine itself documents -
            // no engine patch needed.
            }, ThreadUtils.THREAD_PREFIX_GAME + " rl-episode-" + w);
            workers[w].start();
        }
        for (Thread th : workers) {
            th.join();
        }
        if (!errors.isEmpty()) {
            throw new IllegalStateException("concurrent episode failed: "
                    + errors.get(0), errors.get(0));
        }
    }
}
