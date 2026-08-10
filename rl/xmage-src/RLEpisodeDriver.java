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
 *   -Drl.seed=0              base seed; episode i uses seed+i
 *   -Drl.stopTurn=60         stall bound; stalls score reward 0
 *   -Drl.report=100          print a progress line every N episodes
 *
 * Consult convention (milestone 1): all counts in rl/ are AGENT-SEAT
 * consults per episode. Phase 1/2 "windows/game" numbers summed BOTH
 * seats via shared static counters - divide by ~2 to compare.
 */
public class RLEpisodeDriver extends MageTestPlayerBase {

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
                                      String deckName, int stopTurn,
                                      boolean agentOnPlay) throws Exception {
        Game game = new TwoPlayerDuel(MultiplayerAttackOption.LEFT, RangeOfInfluence.ONE,
                MulliganType.GAME_DEFAULT.getMulligan(0), 60, 20, 7);
        // fresh player objects every episode: a finished game marks its
        // players lost/left, and those flags survive reuse (found the hard
        // way - a reused agent instantly loses every game after its first)
        RLPlayer agent = new RLPlayer("Agent");
        agent.policy = policy;
        agent.resetPerEpisode();
        agent.benchSeed = seed;
        agent.setTestMode(true);

        Player opp;
        if ("heuristic".equals(opponentKind)) {
            HeuristicPlayer h = new HeuristicPlayer("Opponent");
            h.benchSeed = seed;
            h.setTestMode(true);
            opp = h;
        } else {
            RandomPlayer r = new RandomPlayer("Opponent");
            r.setTestMode(true);
            opp = r;
        }

        Deck deckA = loadDeck(deckName);
        Deck deckB = loadDeck(deckName);
        Player first = agentOnPlay ? agent : opp;
        Player second = agentOnPlay ? opp : agent;
        game.loadCards(deckA.getCards(), first.getId());
        game.loadCards(deckB.getCards(), second.getId());
        game.addPlayer(first, deckA);
        game.addPlayer(second, deckB);

        GameOptions options = new GameOptions();
        options.testMode = false;      // real opening hands (Phase 2 erratum)
        options.stopOnTurn = stopTurn;
        options.stopAtStep = PhaseStep.END_TURN;
        game.setGameOptions(options);
        RandomUtil.setSeed(seed);
        game.start(first.getId());

        EpisodeResult r = new EpisodeResult();
        r.turns = game.getTurnNum();
        r.consults = agent.consults;
        r.windows = agent.windows;
        r.actions = agent.actions;
        agent.fallbackCalls.forEach((k, v) -> fallbacks.merge(k, v, Integer::sum));
        String winner = String.valueOf(game.getWinner());
        if (Boolean.getBoolean("rl.debug")) {
            System.out.println("RLDBG|ep seed=" + seed + " turns=" + r.turns
                    + " winner=" + winner + " agentLife=" + agent.getLife()
                    + " agentLib=" + agent.getLibrary().size()
                    + " agentHand=" + agent.getHand().size()
                    + " consults=" + agent.consults);
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
        String deck = System.getProperty("rl.deck", "BenchBurn.dck");
        long seed = Long.getLong("rl.seed", 0L);
        int stopTurn = Integer.getInteger("rl.stopTurn", 60);
        int report = Integer.getInteger("rl.report", 100);

        String mode = System.getProperty("rl.mode", "train");
        PolicyClient policy = "socket".equals(policyKind)
                ? new SocketPolicyClient(port, mode, episodes)
                : new RandomPolicyClient(seed);
        java.util.Map<String, Integer> fallbacks = new java.util.TreeMap<>();

        int wins = 0, losses = 0, draws = 0, stalls = 0;
        long totalConsults = 0, totalWindows = 0, totalActions = 0;
        double totalTurns = 0;
        long t0 = System.nanoTime();
        for (int i = 0; i < episodes; i++) {
            EpisodeResult r = playEpisode(policy, fallbacks, seed + i, opponent,
                    deck, stopTurn, i % 2 == 0);
            policy.episodeEnd(r.reward);
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
                        + "|opponent=%s|policy=%s|deck=%s|seed=%d|fallbacks=%s",
                episodes, wins, losses, draws, stalls,
                wins / (double) episodes, episodes / sec,
                totalConsults / (double) episodes,
                totalWindows / (double) episodes,
                totalActions / (double) episodes,
                totalTurns / episodes,
                opponent, policyKind, deck, seed, fb);
        System.out.println(line);
        String outFile = System.getProperty("rl.out");
        if (outFile != null) {
            java.nio.file.Files.write(java.nio.file.Paths.get(outFile),
                    (line + "\n").getBytes(java.nio.charset.StandardCharsets.UTF_8),
                    java.nio.file.StandardOpenOption.CREATE,
                    java.nio.file.StandardOpenOption.APPEND);
        }
        policy.close();
    }
}
