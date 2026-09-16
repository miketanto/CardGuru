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
        int life = 20;
        final List<Body> battlefield = new ArrayList<>();
        final List<String> hand = new ArrayList<>();
        int filler = 5;
        String fillerCard = "Plains";
    }

    public static final class Spec {
        String name = "unnamed";
        final Side a = new Side();
        final Side b = new Side();
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
    }

    public static Result play(Spec spec, int[] lineA, int[] lineB) {
        Game game = new TwoPlayerDuel(MultiplayerAttackOption.LEFT,
                RangeOfInfluence.ONE, MulliganType.GAME_DEFAULT.getMulligan(0),
                60, 20, 7);

        LinePlayer pa = new LinePlayer("A");
        LinePlayer pb = new LinePlayer("B");
        pa.setTestMode(true);
        pb.setTestMode(true);
        pa.reset(lineA);
        pb.reset(lineB);

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
        r.frontierOptions = pa.frontierOptions;
        r.frontierKind = pa.frontierKind;
        r.decisionsA = pa.decisionsSeen;
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
