package org.mage.test.benchmark;

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
import mage.util.RandomUtil;
import org.junit.Test;
import org.mage.test.serverside.base.MageTestPlayerBase;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * B3: raw steps per second under a uniform-random policy - full games,
 * both players RandomPlayer (see its javadoc: random action selection,
 * heuristic-cheap choice resolution, NO ComputerPlayer7 simulation).
 *
 * Reports games/sec, decisions/sec, wall per game, turns and decisions
 * per game distributions, and the priority-window histogram (how many
 * windows had pass as the only legal action - the pruning headroom).
 *
 * Tunables via system properties:
 *   -Dbench.games=30    measured games (after warmup)
 *   -Dbench.warmup=5
 *   -Dbench.stopTurn=50 turn bound per game
 *   -Dbench.seed=42     base seed; game i uses seed+i
 */
public class B3RandomPolicyBenchmark extends MageTestPlayerBase {

    static class GameRun {
        double wallMs;
        long decisions;
        int turns;
        boolean ended;      // finished naturally (win/loss) vs hit turn bound
    }

    private Deck loadDeck(String name) throws Exception {
        DeckCardLists list = DeckImporter.importDeckFromFile(name, true);
        return Deck.load(list, false, false, loadedCardInfo);
    }

    private GameRun playOneGame(long seed, int stopTurn) throws Exception {
        RandomUtil.setSeed(seed);
        Game game = new TwoPlayerDuel(MultiplayerAttackOption.LEFT, RangeOfInfluence.ONE,
                MulliganType.GAME_DEFAULT.getMulligan(0), 60, 20, 7);
        RandomPlayer pa = new RandomPlayer("RandA");
        RandomPlayer pb = new RandomPlayer("RandB");
        Deck deckA = loadDeck("BenchBurn.dck");
        Deck deckB = loadDeck("BenchBurn.dck");
        game.loadCards(deckA.getCards(), pa.getId());
        game.loadCards(deckB.getCards(), pb.getId());
        game.addPlayer(pa, deckA);
        game.addPlayer(pb, deckB);
        GameOptions options = new GameOptions();
        options.testMode = true;
        options.stopOnTurn = stopTurn;
        options.stopAtStep = PhaseStep.END_TURN;
        game.setGameOptions(options);

        long d0 = RandomPlayer.decisions;
        long t0 = System.nanoTime();
        game.start(pa.getId());
        long t1 = System.nanoTime();

        GameRun r = new GameRun();
        r.wallMs = (t1 - t0) / 1e6;
        r.decisions = RandomPlayer.decisions - d0;
        r.turns = game.getTurnNum();
        r.ended = game.hasEnded();
        if (Boolean.getBoolean("bench.debug")) {
            long creatures = game.getBattlefield().getAllPermanents().stream()
                    .filter(p -> p.isCreature(game)).count();
            StringBuilder names = new StringBuilder();
            game.getBattlefield().getAllPermanents().stream().limit(6)
                    .forEach(p -> names.append(p.getName()).append(","));
            System.out.println("DEBUG|board creatures=" + creatures
                    + " sample=" + names);
            System.out.println(String.format(Locale.ROOT,
                    "DEBUG|game seed=%d turns=%d ended=%s lifeA=%d lifeB=%d battlefield=%d handA=%d graveA=%d attackWindows=%d attacksDeclared=%d",
                    seed, r.turns, r.ended, pa.getLife(), pb.getLife(),
                    game.getBattlefield().getAllPermanents().size(),
                    pa.getHand().size(), pa.getGraveyard().size(),
                    RandomPlayer.attackWindows, RandomPlayer.attacksDeclared));
        }
        return r;
    }

    @Test
    public void benchRandomGames() throws Exception {
        int games = Integer.getInteger("bench.games", 30);
        int warmup = Integer.getInteger("bench.warmup", 5);
        int stopTurn = Integer.getInteger("bench.stopTurn", 50);
        long seed = Long.getLong("bench.seed", 42L);

        for (int i = 0; i < warmup; i++) {
            playOneGame(seed - 1 - i, stopTurn);
        }
        RandomPlayer.resetCounters();

        List<Double> wall = new ArrayList<>();
        List<Double> decs = new ArrayList<>();
        List<Double> turns = new ArrayList<>();
        int endedNaturally = 0;
        long totalDecisions = 0;
        long t0 = System.nanoTime();
        for (int i = 0; i < games; i++) {
            GameRun r = playOneGame(seed + i, stopTurn);
            wall.add(r.wallMs);
            decs.add((double) r.decisions);
            turns.add((double) r.turns);
            totalDecisions += r.decisions;
            if (r.ended) {
                endedNaturally++;
            }
        }
        long t1 = System.nanoTime();
        double totalSec = (t1 - t0) / 1e9;

        List<String> out = new ArrayList<>();
        out.add(BenchStats.report("B3.wall_per_game", wall));
        out.add(BenchStats.report("B3.decisions_per_game", decs));
        out.add(BenchStats.report("B3.turns_per_game", turns));
        out.add(String.format(Locale.ROOT,
                "BENCH|B3.throughput|games=%d|total_sec=%.2f|games_per_sec=%.3f|decisions_per_sec=%.1f|ended_naturally=%d|turn_bound=%d",
                games, totalSec, games / totalSec, totalDecisions / totalSec,
                endedNaturally, stopTurn));
        for (String line : out) {
            System.out.println(line);
        }
        String outFile = System.getProperty("bench.out");
        if (outFile != null) {
            java.nio.file.Files.write(java.nio.file.Paths.get(outFile),
                    String.join("\n", out).concat("\n").getBytes(
                            java.nio.charset.StandardCharsets.UTF_8));
        }

        // priority-window histogram: bucket k = number of playable actions
        // (k=0 => pass was the only legal action)
        StringBuilder h = new StringBuilder("BENCH|B3.playable_hist");
        long windows = 0;
        long forcedPass = RandomPlayer.PLAYABLE_HIST[0];
        for (int k = 0; k < RandomPlayer.PLAYABLE_HIST.length; k++) {
            windows += RandomPlayer.PLAYABLE_HIST[k];
            if (RandomPlayer.PLAYABLE_HIST[k] > 0) {
                h.append(String.format(Locale.ROOT, "|k%d=%d",
                        k, RandomPlayer.PLAYABLE_HIST[k]));
            }
        }
        System.out.println(h);
        System.out.println(String.format(Locale.ROOT,
                "BENCH|B3.pruning|windows=%d|forced_pass=%d|forced_pass_pct=%.1f|actions_taken=%d",
                windows, forcedPass, 100.0 * forcedPass / Math.max(1, windows),
                RandomPlayer.actionsTaken));
    }
}
