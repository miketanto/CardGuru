package org.mage.test.benchmark;

import mage.cards.Card;
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
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.RandomUtil;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.MageTestPlayerBase;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/**
 * Phase 2 driver: decision density under HeuristicPlayer (B5), yield
 * abstraction equivalence + savings (B6), sub-action callback counts (B7).
 * One deck+mode per invocation; the archetype sweep (B8) is a shell loop.
 *
 * System properties:
 *   -Dbench.deck=BenchBurn.dck   mirror-match deck
 *   -Dbench.games=200
 *   -Dbench.warmup=5
 *   -Dbench.stopTurn=80
 *   -Dbench.yields=false         auto-pass via yield predicates
 *   -Dbench.label=aggro_perwindow
 *   -Dbench.out=/path            also write BENCH lines to a file
 */
public class P2DecisionDensityBenchmark extends MageTestPlayerBase {

    static class GameOut {
        String canonical;
        String actions;
        int turns;
        boolean ended;
    }

    private Deck loadDeck(String name) throws Exception {
        DeckCardLists list = DeckImporter.importDeckFromFile(name, true);
        return Deck.load(list, false, false, loadedCardInfo);
    }

    static String canonicalSummary(Game game) {
        StringBuilder sb = new StringBuilder();
        sb.append("turn=").append(game.getTurnNum());
        List<String> perms = new ArrayList<>();
        for (Permanent p : game.getBattlefield().getAllPermanents()) {
            perms.add(p.getName() + (p.isTapped() ? "/T" : "") + "/d" + p.getDamage());
        }
        perms.sort(String::compareTo);
        sb.append("|bf=").append(perms);
        for (UUID pid : game.getState().getPlayersInRange(null, game)) {
            Player p = game.getPlayer(pid);
            List<String> grave = new ArrayList<>();
            for (Card c : p.getGraveyard().getCards(game)) {
                grave.add(c.getName());
            }
            grave.sort(String::compareTo);
            sb.append('|').append(p.getName()).append(":life=").append(p.getLife())
                    .append(":hand=").append(p.getHand().size())
                    .append(":grave=").append(grave);
        }
        return sb.toString();
    }

    private GameOut playGame(long seed, String deckName, boolean yields,
                             int stopTurn) throws Exception {
        Game game = new TwoPlayerDuel(MultiplayerAttackOption.LEFT, RangeOfInfluence.ONE,
                MulliganType.GAME_DEFAULT.getMulligan(0), 60, 20, 7);
        HeuristicPlayer pa = new HeuristicPlayer("HeurA");
        HeuristicPlayer pb = new HeuristicPlayer("HeurB");
        pa.setTestMode(true);   // skip real mulligans (keep every 7) - the
        pb.setTestMode(true);   // instrument measures play, not mull luck
        pa.yieldsEnabled = yields;
        pb.yieldsEnabled = yields;
        pa.benchSeed = seed;
        pb.benchSeed = seed;
        pa.resetPerGame();
        pb.resetPerGame();
        Deck deckA = loadDeck(deckName);
        Deck deckB = loadDeck(deckName);
        game.loadCards(deckA.getCards(), pa.getId());
        game.loadCards(deckB.getCards(), pb.getId());
        game.addPlayer(pa, deckA);
        game.addPlayer(pb, deckB);
        // testMode=false: draw real 7-card opening hands (testMode skips
        // mulligan.drawHand entirely - Phase 1's B3 accidentally ran
        // hellbent games this way). Turn-stop pauses via
        // Phase.checkStopOnStepOption, which does not need testMode.
        // Mulligan choices are skipped at the PLAYER level (setTestMode).
        GameOptions options = new GameOptions();
        options.testMode = false;
        options.stopOnTurn = stopTurn;
        options.stopAtStep = PhaseStep.END_TURN;
        game.setGameOptions(options);
        // seed at the last moment: construction/DB init consume RandomUtil
        // unevenly on a cold JVM, which would shift the shuffle stream
        RandomUtil.setSeed(seed);
        game.start(pa.getId());

        GameOut out = new GameOut();
        out.canonical = canonicalSummary(game);
        out.actions = pa.actionLog + "#" + pb.actionLog;
        out.turns = game.getTurnNum();
        out.ended = game.hasEnded();
        if (Boolean.getBoolean("bench.debug")) {
            System.out.println("DEBUG|seed=" + seed + " turns=" + out.turns
                    + " ended=" + out.ended
                    + " lifeA=" + pa.getLife() + " lifeB=" + pb.getLife()
                    + " handA=" + pa.getHand().size()
                    + " libA=" + pa.getLibrary().size()
                    + " bf=" + game.getBattlefield().getAllPermanents().size()
                    + " winner=" + game.getWinner()
                    + " actionsA=" + pa.actionLog);
        }
        return out;
    }

    @Test
    public void benchDensity() throws Exception {
        String deck = System.getProperty("bench.deck", "BenchBurn.dck");
        String label = System.getProperty("bench.label", "run");
        int games = Integer.getInteger("bench.games", 200);
        int warmup = Integer.getInteger("bench.warmup", 5);
        int stopTurn = Integer.getInteger("bench.stopTurn", 80);
        boolean yields = Boolean.getBoolean("bench.yields");

        for (int i = 0; i < warmup; i++) {
            playGame(9000 + i, deck, yields, stopTurn);
        }
        P2Stats.reset();
        List<Double> turns = new ArrayList<>();
        int ended = 0;
        long t0 = System.nanoTime();
        for (int i = 0; i < games; i++) {
            GameOut g = playGame(10000 + i, deck, yields, stopTurn);
            turns.add((double) g.turns);
            if (g.ended) {
                ended++;
            }
        }
        double totalSec = (System.nanoTime() - t0) / 1e9;

        List<String> lines = new ArrayList<>(P2Stats.report(label, games, totalSec));
        lines.add(BenchStats.report("P2." + label + ".turns_per_game", turns));
        lines.add(String.format(Locale.ROOT,
                "BENCH|P2.%s.completion|games=%d|ended_naturally=%d|turn_bound=%d|yields=%s",
                label, games, ended, stopTurn, yields));
        for (String l : lines) {
            System.out.println(l);
        }
        String outFile = System.getProperty("bench.out");
        if (outFile != null) {
            java.nio.file.Files.write(java.nio.file.Paths.get(outFile),
                    (String.join("\n", lines) + "\n").getBytes(
                            java.nio.charset.StandardCharsets.UTF_8));
        }
    }

    /**
     * B6 correctness: same seed, per-window vs yields, must produce the
     * SAME action log and the SAME canonical final state. A yield that
     * skips a window where the policy would have acted shows up here.
     */
    @Test
    public void yieldEquivalence() throws Exception {
        String deck = System.getProperty("bench.deck", "BenchBurn.dck");
        int games = Integer.getInteger("bench.games", 50);
        int stopTurn = Integer.getInteger("bench.stopTurn", 80);
        playGame(19999, deck, false, stopTurn);   // JVM/static-init warmup
        int checked = 0;
        for (int i = 0; i < games; i++) {
            P2Stats.reset();
            GameOut plain = playGame(20000 + i, deck, false, stopTurn);
            P2Stats.reset();
            GameOut yielded = playGame(20000 + i, deck, true, stopTurn);
            Assert.assertEquals("action log diverged at seed " + (20000 + i),
                    plain.actions, yielded.actions);
            Assert.assertEquals("final state diverged at seed " + (20000 + i),
                    plain.canonical, yielded.canonical);
            checked++;
        }
        System.out.println("BENCH|P2.equivalence|deck=" + deck
                + "|games=" + checked + "|identical=true");
    }
}
