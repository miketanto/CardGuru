package org.mage.test.benchmark.rl;

import mage.cards.decks.Deck;
import mage.cards.decks.DeckCardLists;
import mage.cards.decks.importer.DeckImporter;
import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.Game;
import mage.game.GameOptions;
import mage.game.TwoPlayerDuel;
import mage.game.mulligan.MulliganType;
import mage.players.Player;
import mage.util.RandomUtil;
import org.junit.Test;
import org.mage.test.benchmark.HeuristicPlayer;
import org.mage.test.benchmark.RandomPlayer;
import org.mage.test.serverside.base.MageTestPlayerBase;

import java.util.Locale;

/**
 * Episode loop: RLPlayer (agent seat) vs a fixed opponent, mirror decks.
 * NOT self-play - the opponent is stationary by design (the measurement
 * depends on it).
 *
 * System properties:
 *   -Drl.episodes=100        episodes this invocation
 *   -Drl.opponent=random     random | heuristic
 *   -Drl.policy=random       random | socket
 *   -Drl.port=7777           socket policy port
 *   -Drl.deck=BenchBurn.dck
 *   -Drl.oppDeck=...        opponent-seat deck (Phase 7c archetype
 *                           curriculum); unset = mirror of rl.deck
 *   -Drl.seed=0              base seed; episode i uses seed+i
 *   -Drl.stopTurn=60         stall bound; stalls score reward 0
 *   -Drl.report=100          print a progress line every N episodes
 *
 * Consult convention (milestone 1): all counts in rl/ are AGENT-SEAT
 * consults per episode. Phase 1/2 "windows/game" numbers summed BOTH
 * seats via shared static counters - divide by ~2 to compare.
 */
public class RLEpisodeDriver extends MageTestPlayerBase {

    /** C1 imitation log (rl.imitateOut): open across all episodes */
    private java.io.PrintWriter imitateOut;

    /** C5 league: rl.opponent=rl - a second policy seat, served by its
     *  own (frozen, eval-mode) server on rl.oppPort */
    private PolicyClient oppPolicy;

    @org.junit.BeforeClass
    public static void buildCardDb() {
        // MageTestPlayerBase never scans; without this a fresh checkout has
        // an empty card DB and every deck loads 0 cards (synchronous, one-time
        // cost per checkout - the db/ directory persists)
        mage.cards.repository.CardScanner.scan();
        // inert unless -Dxmage.dataCollectors.printGameLogs=true, which
        // routes the engine's informPlayers game log to log4j (full
        // human-readable transcripts for debugging/sampling)
        mage.collectors.DataCollectorServices.init(false, false);
    }

    private Deck loadDeck(String name) throws Exception {
        DeckCardLists list = DeckImporter.importDeckFromFile(name, true);
        Deck deck = Deck.load(list, false, false, loadedCardInfo);
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

    private EpisodeResult playEpisode(PolicyClient policy, java.util.Map<String, Integer> fallbacks,
                                      long seed, String opponentKind,
                                      String deckName, String oppDeckName,
                                      int stopTurn,
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
            r.policy = oppPolicy;
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
        // decks bind to SEATS, not to play order: with asymmetric decks the
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

    @Test
    public void runEpisodes() throws Exception {
        int episodes = Integer.getInteger("rl.episodes", 100);
        String opponent = System.getProperty("rl.opponent", "random");
        String policyKind = System.getProperty("rl.policy", "random");
        int port = Integer.getInteger("rl.port", 7777);
        // comma-separated list = Task C training pool; episode i plays a
        // mirror of decks[i % n] so every deck gets equal exposure
        String[] decks = System.getProperty("rl.deck", "BenchBurn.dck").split(",");
        // Phase 7c: opponent-seat deck. Unset => mirror (historical default).
        String oppDeckProp = System.getProperty("rl.oppDeck");
        String[] oppDecks = oppDeckProp == null ? null : oppDeckProp.split(",");
        long seed = Long.getLong("rl.seed", 0L);
        int stopTurn = Integer.getInteger("rl.stopTurn", 60);
        int report = Integer.getInteger("rl.report", 100);

        String mode = System.getProperty("rl.mode", "train");
        PolicyClient policy = "socket".equals(policyKind)
                ? new SocketPolicyClient(port, mode, episodes)
                : new RandomPolicyClient(seed);
        java.util.Map<String, Integer> fallbacks = new java.util.TreeMap<>();
        String imitatePath = System.getProperty("rl.imitateOut");
        if (imitatePath != null) {
            imitateOut = new java.io.PrintWriter(new java.io.BufferedWriter(
                    new java.io.FileWriter(imitatePath, true)));
        }
        if ("rl".equals(opponent)) {
            oppPolicy = new SocketPolicyClient(
                    Integer.getInteger("rl.oppPort", port + 1), "eval", episodes);
        }

        int wins = 0, losses = 0, draws = 0, stalls = 0;
        long totalConsults = 0, totalWindows = 0, totalActions = 0;
        double totalTurns = 0;
        long t0 = System.nanoTime();
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
            totalConsults += r.consults;
            totalWindows += r.windows;
            totalActions += r.actions;
            totalTurns += r.turns;
            if (report > 0 && (i + 1) % report == 0) {
                double sec = (System.nanoTime() - t0) / 1e9;
                System.out.println(String.format(Locale.ROOT,
                        "RL|progress|ep=%d|win_rate=%.3f|games_per_sec=%.2f",
                        i + 1, wins / (double) (i + 1), (i + 1) / sec));
            }
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
                episodes, wins, losses, draws, stalls,
                wins / (double) episodes, episodes / sec,
                totalConsults / (double) episodes,
                totalWindows / (double) episodes,
                totalActions / (double) episodes,
                totalTurns / episodes,
                opponent, policyKind, String.join(",", decks),
                oppDecks == null ? "mirror" : String.join(",", oppDecks), seed, fb);
        System.out.println(line);
        if (policy instanceof SocketPolicyClient) {
            SocketPolicyClient s = (SocketPolicyClient) policy;
            System.out.println(String.format(Locale.ROOT,
                    "RL|ipc|round_trips=%d|avg_rtt_us=%.1f|ipc_sec_total=%.1f",
                    s.roundTrips,
                    s.roundTripNanos / 1e3 / Math.max(1, s.roundTrips),
                    s.roundTripNanos / 1e9));
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
        }
        if (oppPolicy != null) {
            oppPolicy.close();
        }
        policy.close();
    }
}
