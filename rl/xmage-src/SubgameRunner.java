package org.mage.test.benchmark.rl;

import mage.abilities.Ability;
import mage.cards.Card;
import mage.cards.decks.Deck;
import mage.cards.repository.CardInfo;
import mage.cards.repository.CardRepository;
import mage.constants.MultiplayerAttackOption;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.GameOptions;
import mage.game.PutToBattlefieldInfo;
import mage.game.TwoPlayerDuel;
import mage.game.match.MatchType;
import mage.game.mulligan.MulliganType;
import mage.players.Player;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Builds a SUBGAME - a constructed board with small libraries - and plays
 * it to a real terminal state through two {@link LinePlayer} seats.
 *
 * The board is constructed with the engine's own GameImpl.cheat(), which
 * lives in Mage core rather than the test module, so nothing here depends
 * on CardTestPlayerBase. Libraries are CLEARED after addPlayer and then
 * cheated to exactly N filler cards: that count is the subgame's clock,
 * and it is what guarantees the game ends on its own rather than at a
 * horizon we picked.
 *
 * Modes:
 *   describe <card> [<card> ...]   print engine P/T and rules text - the
 *                                  verification step before any card
 *                                  enters a family, so no stat is guessed
 *   play <lineA> <lineB>           run T1.HOLD with the given lines,
 *                                  comma-separated indices, e.g. 0,3
 */
public final class SubgameRunner {

    // ------------------------------------------------------------- spec

    public static final class Body {
        final String card;
        final int count;
        final boolean tapped;
        Body(String card, int count, boolean tapped) {
            this.card = card;
            this.count = count;
            this.tapped = tapped;
        }
        public static Body of(String card, int count) {
            return new Body(card, count, false);
        }
    }

    public static final class Side {
        public int life = 20;
        final List<Body> battlefield = new ArrayList<>();
        final List<String> hand = new ArrayList<>();
        public int filler = 5;
        String fillerCard = "Plains";
    }

    public static final class Spec {
        String name = "unnamed";
        public final Side a = new Side();
        public final Side b = new Side();
        boolean aOnPlay = true;
    }

    // -------------------------------------------------------- the build

    private static Card create(String name) {
        CardInfo info = CardRepository.instance.findCard(name, true);
        if (info == null) {
            throw new IllegalArgumentException("card not found: " + name);
        }
        return info.createCard();
    }

    /** A deck big enough for the engine to accept the seat. Its contents
     *  never reach play: the library is cleared before the cheat. */
    private static Deck stubDeck(String fillerCard) {
        Deck deck = new Deck();
        for (int i = 0; i < 40; i++) {
            deck.getCards().add(create(fillerCard));
        }
        return deck;
    }

    private static void furnish(Game game, Player player, Side side) {
        // the library the seat got from its stub deck is not the clock we
        // want; replace it wholesale
        player.getLibrary().clear();

        List<Card> library = new ArrayList<>();
        for (int i = 0; i < side.filler; i++) {
            library.add(create(side.fillerCard));
        }
        List<Card> hand = new ArrayList<>();
        for (String n : side.hand) {
            hand.add(create(n));
        }
        List<PutToBattlefieldInfo> field = new ArrayList<>();
        for (Body b : side.battlefield) {
            for (int i = 0; i < b.count; i++) {
                field.add(new PutToBattlefieldInfo(create(b.card), b.tapped));
            }
        }
        Map<Zone, String> commands = new EnumMap<>(Zone.class);
        commands.put(Zone.OUTSIDE, "life:" + side.life);
        game.cheat(player.getId(), commands);
        game.cheat(player.getId(), library, hand, field,
                new ArrayList<>(), new ArrayList<>(), new ArrayList<>());
    }

    public static final class Result {
        public String winner;          // player name, or null
        public int turns;
        public int lifeA;
        public int lifeB;
        public int frontierOptions;    // from seat A
        public String frontierKind;
        public int decisionsA;
        public int decisionsB;
        public String log = "";
        public boolean frontierHit = false;
        public String frontierSeat = null;
    }

    /** Both seats consume ONE shared script in global decision order.
     *  This is the entry point the solver replays through. */
    public static Result scripted(Spec spec, int[] choices) {
        LinePlayer.Script script = new LinePlayer.Script(choices);
        LinePlayer pa = new LinePlayer("A");
        pa.script = script;
        Result r = run(spec, pa, new int[0], null, script);
        r.frontierHit = script.frontierHit;
        r.frontierOptions = script.frontierOptions;
        r.frontierKind = script.frontierKind;
        r.frontierSeat = script.frontierSeat;
        return r;
    }

    public static Result play(Spec spec, int[] lineA, int[] lineB) {
        LinePlayer pa = new LinePlayer("A");
        pa.reset(lineA);
        return run(spec, pa, lineB, null, null);
    }

    /** Seat A is whatever player is passed in - a LinePlayer for scripted
     *  checks, an RLPlayer for a policy. Seat B stays a LinePlayer so the
     *  opponent is a stated, fixed line and not a second moving part. */
    public static Result run(Spec spec, Player seatA, int[] lineB, RLPlayer rlA) {
        return run(spec, seatA, lineB, rlA, null);
    }

    public static Result run(Spec spec, Player seatA, int[] lineB, RLPlayer rlA,
                             LinePlayer.Script shared) {
        Game game = new TwoPlayerDuel(MultiplayerAttackOption.LEFT,
                RangeOfInfluence.ONE, MulliganType.GAME_DEFAULT.getMulligan(0),
                60, 20, 7);

        Player pa = seatA;
        LinePlayer pb = new LinePlayer("B");
        pa.setTestMode(true);
        pb.setTestMode(true);
        pb.reset(lineB);
        if (shared != null) {
            pb.script = shared;
        }

        Player first = spec.aOnPlay ? pa : pb;
        Player second = spec.aOnPlay ? pb : pa;
        Deck deckFirst = stubDeck(spec.aOnPlay ? spec.a.fillerCard : spec.b.fillerCard);
        Deck deckSecond = stubDeck(spec.aOnPlay ? spec.b.fillerCard : spec.a.fillerCard);
        game.loadCards(deckFirst.getCards(), first.getId());
        game.loadCards(deckSecond.getCards(), second.getId());
        game.addPlayer(first, deckFirst);
        game.addPlayer(second, deckSecond);

        for (Player p : game.getPlayers().values()) {
            p.updateRange(game);
        }
        furnish(game, pa, spec.a);
        furnish(game, pb, spec.b);

        // PIN THE STARTING PLAYER. Without this the engine asks the
        // CHOOSING player's choose() callback who goes first - and for an
        // RL seat that question reaches the POLICY, so a random policy
        // silently decided which side was on the play and turned one
        // subgame into two. Found by an RL smoke whose action log showed
        // seat A being attacked on turn 1.
        game.setStartingPlayerId(first.getId());

        GameOptions options = new GameOptions();
        options.testMode = true;
        options.stopOnTurn = 30;
        game.setGameOptions(options);
        game.start(first.getId());

        Result r = new Result();
        UUID w = null;
        for (Player p : game.getPlayers().values()) {
            if (p.hasWon()) {
                w = p.getId();
            }
        }
        r.winner = w == null ? null : game.getPlayer(w).getName();
        r.turns = game.getTurnNum();
        r.lifeA = pa.getLife();
        r.lifeB = pb.getLife();
        if (pa instanceof LinePlayer) {
            LinePlayer la = (LinePlayer) pa;
            r.frontierOptions = la.frontierOptions;
            r.frontierKind = la.frontierKind;
            r.decisionsA = la.decisionsSeen;
        } else if (rlA != null) {
            r.decisionsA = (int) rlA.consults;
            r.log = rlA.actionLog.toString();
        }
        r.decisionsB = pb.decisionsSeen;
        return r;
    }

    // ------------------------------------------------------- T1.HOLD

    /** The sample instance from rl/SUBGAME-DESIGN.md, with the bodies
     *  left as parameters because their real stats are whatever the
     *  engine says they are - see `describe`. */
    public static Spec t1Hold(String smallBody, String bigBody) {
        Spec s = new Spec();
        s.name = "T1.HOLD";
        s.a.life = 3;
        s.a.battlefield.add(Body.of(smallBody, 2));
        s.a.filler = 7;
        s.b.life = 4;
        s.b.battlefield.add(Body.of(bigBody, 1));
        s.b.filler = 4;
        s.aOnPlay = true;
        return s;
    }

    private static int[] parseLine(String s) {
        if (s == null || s.isEmpty() || "-".equals(s)) {
            return new int[0];
        }
        String[] parts = s.split(",");
        int[] out = new int[parts.length];
        for (int i = 0; i < parts.length; i++) {
            out[i] = Integer.parseInt(parts[i].trim());
        }
        return out;
    }

    public static void main(String[] args) {
        mage.cards.repository.CardScanner.scan();
        if (args.length == 0) {
            System.out.println("usage: describe <card>... | play <lineA> <lineB> [small] [big]");
            return;
        }
        if ("describe".equals(args[0])) {
            for (int i = 1; i < args.length; i++) {
                Card c = create(args[i]);
                StringBuilder ab = new StringBuilder();
                for (Ability a : c.getAbilities()) {
                    String rule = a.getRule();
                    if (rule != null && !rule.trim().isEmpty()) {
                        ab.append('[').append(rule.trim()).append(']');
                    }
                }
                System.out.println("CARD|" + c.getName()
                        + "|pt=" + c.getPower().getValue() + "/" + c.getToughness().getValue()
                        + "|mv=" + c.getManaValue()
                        + "|types=" + c.getCardType()
                        + "|abilities=" + (ab.length() == 0 ? "NONE" : ab));
            }
            return;
        }
        if ("scripted".equals(args[0])) {
            Result r = scripted(t1Hold(
                    args.length > 2 ? args[2] : "Silvercoat Lion",
                    args.length > 3 ? args[3] : "Trokin High Guard"),
                    parseLine(args[1]));
            System.out.println("SCRIPTED|winner=" + r.winner + "|turns=" + r.turns
                    + "|lifeA=" + r.lifeA + "|lifeB=" + r.lifeB
                    + "|frontier=" + r.frontierSeat + ":" + r.frontierKind
                    + ":" + r.frontierOptions);
            return;
        }
        if ("rl".equals(args[0])) {
            int episodes = Integer.parseInt(args[1]);
            int[] lineB = parseLine(args.length > 2 ? args[2] : "-");
            String small = args.length > 3 ? args[3] : "Silvercoat Lion";
            String big = args.length > 4 ? args[4] : "Trokin High Guard";
            Spec spec = t1Hold(small, big);
            int winsA = 0;
            String firstLog = null;
            long t0 = System.nanoTime();
            for (int i = 0; i < episodes; i++) {
                RLPlayer rl = new RLPlayer("A");
                rl.policy = new RandomPolicyClient(1000L + i);
                rl.resetPerEpisode();
                rl.benchSeed = 1000L + i;
                Result r = run(spec, rl, lineB, rl);
                if ("A".equals(r.winner)) {
                    winsA++;
                }
                if (firstLog == null) {
                    firstLog = r.log;
                }
            }
            double secs = (System.nanoTime() - t0) / 1e9;
            System.out.println("SUBGAMERL|" + spec.name
                    + "|episodes=" + episodes
                    + "|winsA=" + winsA
                    + "|rateA=" + String.format("%.3f", winsA / (double) episodes)
                    + "|eps_per_sec=" + String.format("%.2f", episodes / secs));
            if (firstLog != null && !firstLog.isEmpty()) {
                System.out.println("---- episode 0 action log ----");
                System.out.println(firstLog);
            }
            return;
        }
        if ("play".equals(args[0])) {
            String small = args.length > 3 ? args[3] : "Silvercoat Lion";
            String big = args.length > 4 ? args[4] : "Hill Giant";
            Spec spec = t1Hold(small, big);
            Result r = play(spec, parseLine(args[1]),
                    args.length > 2 ? parseLine(args[2]) : new int[0]);
            System.out.println("SUBGAME|" + spec.name
                    + "|lineA=" + (args[1])
                    + "|lineB=" + (args.length > 2 ? args[2] : "-")
                    + "|winner=" + r.winner
                    + "|turns=" + r.turns
                    + "|lifeA=" + r.lifeA + "|lifeB=" + r.lifeB
                    + "|decisionsA=" + r.decisionsA + "|decisionsB=" + r.decisionsB
                    + "|frontier=" + r.frontierKind + ":" + r.frontierOptions);
        }
    }

    private SubgameRunner() {
    }
}
