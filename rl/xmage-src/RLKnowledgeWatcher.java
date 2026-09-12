package org.mage.test.benchmark.rl;

import mage.abilities.Ability;
import mage.abilities.keyword.FlashAbility;
import mage.abilities.mana.ActivatedManaAbilityImpl;
import mage.cards.Card;
import mage.cards.decks.Deck;
import mage.constants.PhaseStep;
import mage.constants.WatcherScope;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.events.GameEvent;
import mage.game.events.ZoneChangeEvent;
import mage.game.permanent.Permanent;
import mage.game.stack.StackObject;
import mage.players.Player;
import mage.util.Copyable;
import mage.watchers.Watcher;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.UUID;

/**
 * WIRE-V7 §2g / ARCHITECTURE-V7-DESIGN §8: what the agent LEGALLY knows
 * about the opponent's hidden cards, kept as a game watcher so it is
 * built from public events only.
 *
 * <p>Sources, all public under the rules: zone changes (a card entering
 * the opponent's hand from a public zone is a known card; one leaving it
 * is a slot gone; one entering a public zone has been seen), the
 * engine's revealed / looked-at sets, search events (origin "tutored"),
 * the opponent's casts, activations, attacks and blocks, and two
 * derived observations (declined to block, passed with mana up). The
 * true identity of an unknown hand card is NEVER read: a slot carries
 * the card's UUID only as a position handle (which slot leaves when a
 * card is played), never its name unless the name became public.
 *
 * <p>Lifecycle: registered lazily by RLPlayer at its first priority
 * window of a game ({@link #ensure}); the first emission scans the
 * public zones and reconciles the slot count with the opponent's hand
 * size, so late registration and mulligans are covered (counted in
 * {@code handDrift}). Watchers are copied with the game state by
 * reflection ({@link Watcher#copy}: ONE constructor, every field deep
 * copied), so the state is plain lists and maps of immutable values or
 * {@link Copyable} records, and nothing here is final.
 */
public class RLKnowledgeWatcher extends Watcher {

    /** hand-slot origin one-hot, WIRE §2g idx 0..3. */
    public static final int O_OPENING = 0, O_DRAWN = 1, O_RETURNED = 2, O_OTHER = 3;
    /** opponent action type one-hot, WIRE §2g idx 0..6. */
    public static final int A_CAST = 0, A_ACTIVATE = 1, A_ATTACK = 2, A_BLOCK = 3,
            A_DECLINED_BLOCK = 4, A_PASSED_MANA_UP = 5, A_OTHER = 6;

    public static final class Slot implements Copyable<Slot> {
        public UUID card;           // position handle; null = reconciled slot
        public int origin;
        public int turnIn;
        public boolean known, seen;
        public String name;         // only when known

        @Override
        public Slot copy() {
            Slot s = new Slot();
            s.card = card;
            s.origin = origin;
            s.turnIn = turnIn;
            s.known = known;
            s.seen = seen;
            s.name = name;
            return s;
        }
    }

    public static final class Act implements Copyable<Act> {
        public int type;
        public long consult;
        public List<UUID> refs = new ArrayList<>();

        @Override
        public Act copy() {
            Act a = new Act();
            a.type = type;
            a.consult = consult;
            a.refs = new ArrayList<>(refs);
            return a;
        }
    }

    /** One name of the open decklist. A Copyable record because the
     *  watcher copy deep-copies every field and refuses raw arrays. */
    public static final class DeckCard implements Copyable<DeckCard> {
        public int count;
        public int mv;
        public boolean instantSpeed;

        @Override
        public DeckCard copy() {
            DeckCard d = new DeckCard();
            d.count = count;
            d.mv = mv;
            d.instantSpeed = instantSpeed;
            return d;
        }
    }

    /** What the emitter hands to StateEncoder. */
    public static final class Emission {
        public float[][] hand, deck, actions;
        public String[] handName, deckName, oeHand;
        public UUID[][] actionRefs;
        public int handDrift, handTrunc, bornTurn;
        public long events;
    }

    // ---- state: non-final, deep-copyable (see class comment) ----
    UUID me, opp;
    Map<String, DeckCard> deckInfo = new HashMap<>();   // the open decklist by name
    List<Slot> hand = new ArrayList<>();
    Set<UUID> seenIds = new HashSet<>();                // seen face-up in a public zone
    Map<UUID, String> knownIds = new HashMap<>();       // identity known to me (seen, revealed, looked at)
    List<Act> acts = new ArrayList<>();
    boolean scanned, openingDone, searchPending, oppCastThisTurn, oppBlockedThisCombat;
    int lastTurn = -1, lastEndTurnSeen = -1;
    long consults;
    int handDrift;
    /** diagnostics: the turn of the first event seen, events seen. */
    int bornTurn = -1;
    long events;

    /** -Drl.trackerDebug=file: one line per opponent-related event
     *  (turn|type|from|to|name|hand-size|slots). Public information only;
     *  a diagnostic for the event model, not a data path. */
    private static final String DEBUG = System.getProperty("rl.trackerDebug");
    private static java.io.PrintWriter debugOut;

    private static String short8(UUID id) {
        return id == null ? "-" : id.toString().substring(0, 8);
    }

    private String slotIds() {
        StringBuilder sb = new StringBuilder();
        for (Slot s : hand) {
            sb.append(short8(s.card)).append(s.known ? "*" : "").append(',');
        }
        return sb.toString();
    }

    private static synchronized void debug(String line) {
        try {
            if (debugOut == null) {
                debugOut = new java.io.PrintWriter(new java.io.FileWriter(DEBUG, true), true);
            }
            debugOut.println(line);
        } catch (java.io.IOException ignored) {
        }
    }

    public RLKnowledgeWatcher(UUID me, UUID opp, Map<String, DeckCard> deckInfo) {
        super(WatcherScope.GAME);
        this.me = me;
        this.opp = opp;
        if (deckInfo != null) {
            this.deckInfo = deckInfo;
        }
    }

    /** The open decklist by name: count, mana value, instant-speed. */
    public static Map<String, DeckCard> deckInfo(Deck deck) {
        Map<String, DeckCard> m = new HashMap<>();
        if (deck == null) {
            return m;
        }
        for (Card c : deck.getCards()) {
            DeckCard d = m.computeIfAbsent(c.getName(), k -> new DeckCard());
            d.count++;
            d.mv = c.getManaValue();
            boolean flash = false;
            for (Ability a : c.getAbilities()) {
                if (a instanceof FlashAbility) {
                    flash = true;
                }
            }
            d.instantSpeed = c.isInstant() || flash;
        }
        return m;
    }

    /** The game's tracker, registered on first use. */
    public static RLKnowledgeWatcher ensure(Game game, UUID me, UUID opp,
                                            Map<String, DeckCard> deckInfo) {
        RLKnowledgeWatcher w = game.getState().getWatcher(RLKnowledgeWatcher.class);
        if (w == null && me != null && opp != null) {
            w = new RLKnowledgeWatcher(me, opp, deckInfo);
            game.getState().addWatcher(w);
        }
        return w;
    }

    // ------------------------------------------------------------ events
    @Override
    public void watch(GameEvent event, Game game) {
        if (me == null || opp == null) {
            return;
        }
        int turn = game.getTurnNum();
        events++;
        if (bornTurn < 0) {
            bornTurn = turn;
        }
        if (turn != lastTurn) {
            lastTurn = turn;
            searchPending = false;
            oppCastThisTurn = false;
        }
        if (DEBUG != null) {
            try {
                Card dc = event.getTargetId() == null ? null : game.getCard(event.getTargetId());
                Card sc = event.getSourceId() == null ? null : game.getCard(event.getSourceId());
                boolean oppCard = (dc != null && opp.equals(dc.getOwnerId()))
                        || (sc != null && opp.equals(sc.getOwnerId()));
                if (opp.equals(event.getPlayerId()) || oppCard) {
                    Player op = game.getPlayer(opp);
                    String zones = event instanceof ZoneChangeEvent
                            ? ((ZoneChangeEvent) event).getFromZone() + ">" + ((ZoneChangeEvent) event).getToZone()
                            : String.valueOf(event.getZone());
                    // the name here is a DIAGNOSTIC of the event model (it
                    // reads hidden identities); the tracker itself never does
                    debug(turn + "|" + game.getTurnStepType() + "|" + event.getType() + "|" + zones + "|"
                            + (dc != null ? dc.getName() : sc != null ? sc.getName() : "-")
                            + "|hand=" + (op == null ? -1 : op.getHand().size()) + "|slots=" + hand.size()
                            // 5b diagnostic: the event's handle vs the handles the slots hold
                            + "|tid=" + short8(event.getTargetId()) + "|sids=" + slotIds());
                }
            } catch (RuntimeException ignored) {
                // test-mode lookups throw on non-card ids; diagnostics only
            }
        }
        switch (event.getType()) {
            case SEARCH_LIBRARY:
                if (opp.equals(event.getPlayerId())) {
                    searchPending = true;
                }
                break;
            case DREW_CARD:
                // draws fire DREW_CARD and no ZONE_CHANGE (measured with
                // -Drl.trackerDebug); the id is a position handle only
                if (opp.equals(event.getPlayerId())) {
                    onDrew(event.getTargetId() != null ? event.getTargetId() : event.getSourceId(), game);
                }
                break;
            case ZONE_CHANGE:
                if (event instanceof ZoneChangeEvent) {
                    onZoneChange((ZoneChangeEvent) event, game);
                }
                break;
            case SPELL_CAST:
                if (opp.equals(event.getPlayerId())) {
                    oppCastThisTurn = true;
                    act(A_CAST, event.getSourceId());
                    // the hand slot already left on the ZONE_CHANGE
                    // HAND>STACK that precedes this event (measured with
                    // -Drl.trackerDebug); here the spell becomes public
                    UUID card = event.getSourceId();
                    Card c = card == null ? null : game.getCard(card);
                    if (c != null && opp.equals(c.getOwnerId())) {
                        seenIds.add(card);
                        knownIds.put(card, c.getName());
                    }
                }
                break;
            case ACTIVATED_ABILITY:
                if (opp.equals(event.getPlayerId()) && !isManaAbility(event, game)) {
                    act(A_ACTIVATE, event.getSourceId());
                }
                break;
            case ATTACKER_DECLARED:
                if (opp.equals(event.getPlayerId())) {
                    act(A_ATTACK, event.getSourceId(), event.getTargetId());
                }
                break;
            case DECLARE_BLOCKERS_STEP_PRE:
                oppBlockedThisCombat = false;
                break;
            case BLOCKER_DECLARED:
                if (opp.equals(event.getPlayerId())) {
                    oppBlockedThisCombat = true;
                    act(A_BLOCK, event.getSourceId(), event.getTargetId());
                }
                break;
            case DECLARED_BLOCKERS:
                onDeclaredBlockers(game);
                break;
            default:
                break;
        }
        pollPublicKnowledge(game);
        pollEndOfMyTurn(game);
    }

    private static boolean isPublic(Zone z) {
        return z == Zone.BATTLEFIELD || z == Zone.GRAVEYARD || z == Zone.EXILED
                || z == Zone.STACK || z == Zone.COMMAND;
    }

    /** A draw: opening hand while no step has begun (the deal happens
     *  before the first turn's steps), else drawn, or tutored/other when a
     *  library search is pending. Identity stays unknown unless it was
     *  already public (a revealed card drawn from a known top). */
    private void onDrew(UUID id, Game game) {
        if (id == null) {
            return;
        }
        try {
            id = mainId(game.getCard(id), id);
        } catch (RuntimeException ignored) {
            // test-mode lookups throw on non-card ids; keep the handle
        }
        int origin = game.getTurnStepType() == null ? O_OPENING
                : searchPending ? O_OTHER : O_DRAWN;
        searchPending = false;
        removeSlot(id, false);
        Slot s = new Slot();
        s.card = id;
        s.origin = origin;
        s.turnIn = origin == O_OPENING ? 0 : game.getTurnNum();
        if (knownIds.containsKey(id)) {
            s.known = true;
            s.seen = true;
            s.name = knownIds.get(id);
        }
        hand.add(s);
    }

    /** The handle a hand slot is keyed by: the MAIN card's id. A transforming
     *  double-faced permanent leaves the battlefield under a different id
     *  from the one its card carries in hand (5b, BenchDimir: Cecil, Dark
     *  Knight returned by ninjutsu as 43a68e5c, cast again as f6a8b9b8), so
     *  keying by the event id left a phantom known slot behind and
     *  reconcile() then evicted a real unknown one - measured as handDrift 9
     *  and 22 known-not-in-truth consults on two of 48 recordings. */
    private static UUID mainId(Card c, UUID id) {
        try {
            Card m = c == null ? null : c.getMainCard();
            return m != null ? m.getId() : id;
        } catch (RuntimeException e) {
            return id;
        }
    }

    private void onZoneChange(ZoneChangeEvent z, Game game) {
        UUID id = z.getTargetId();
        Card c = game.getCard(id);
        if (c == null || !opp.equals(c.getOwnerId())) {
            return;
        }
        id = mainId(c, id);
        Zone from = z.getFromZone(), to = z.getToZone();
        if (to == Zone.HAND) {
            int origin;
            if (from == Zone.LIBRARY) {
                origin = game.getTurnNum() <= 0 ? O_OPENING : searchPending ? O_OTHER : O_DRAWN;
                searchPending = false;
            } else if (isPublic(from)) {
                origin = O_RETURNED;
            } else {
                origin = O_OTHER;
            }
            removeSlot(id, false);
            Slot s = new Slot();
            s.card = id;
            s.origin = origin;
            s.turnIn = game.getTurnNum();
            if (origin == O_RETURNED || knownIds.containsKey(id)) {
                s.known = true;
                s.seen = true;
                s.name = c.getName();
                knownIds.put(id, c.getName());
            }
            hand.add(s);
        } else if (from == Zone.HAND) {
            removeSlot(id, true);
        }
        if (isPublic(to)) {
            seenIds.add(id);
            knownIds.put(id, c.getName());
        }
    }

    /** A card left the hand: its own slot if we hold its handle, else
     *  a reconciled (handle-less) slot, else nothing (drift). */
    private void removeSlot(UUID id, boolean countDrift) {
        for (int i = 0; i < hand.size(); i++) {
            if (id.equals(hand.get(i).card)) {
                hand.remove(i);
                return;
            }
        }
        for (int i = 0; i < hand.size(); i++) {
            if (hand.get(i).card == null) {
                hand.remove(i);
                return;
            }
        }
        if (countDrift) {
            handDrift++;
        }
    }

    private boolean isManaAbility(GameEvent event, Game game) {
        Ability a = game.getAbility(event.getTargetId(), event.getSourceId()).orElse(null);
        return a instanceof ActivatedManaAbilityImpl;
    }

    private void act(int type, UUID... refs) {
        Act a = new Act();
        a.type = type;
        a.consult = consults;
        for (UUID r : refs) {
            if (r != null) {
                a.refs.add(r);
            }
        }
        acts.add(a);
        if (acts.size() > 64) {
            acts.remove(0);
        }
    }

    /** I attacked, blockers are declared, the opponent had an untapped
     *  creature and assigned none of them: a decision worth a token. */
    private void onDeclaredBlockers(Game game) {
        if (!me.equals(game.getActivePlayerId()) || oppBlockedThisCombat) {
            return;
        }
        List<UUID> attackers = new ArrayList<>();
        for (CombatGroup g : game.getCombat().getGroups()) {
            attackers.addAll(g.getAttackers());
        }
        if (attackers.isEmpty()) {
            return;
        }
        boolean couldBlock = false;
        for (Permanent p : game.getBattlefield().getAllActivePermanents(opp)) {
            if (p.isCreature(game) && !p.isTapped()) {
                couldBlock = true;
                break;
            }
        }
        if (couldBlock) {
            act(A_DECLINED_BLOCK, attackers.toArray(new UUID[0]));
        }
    }

    /** Revealed and looked-at cards are public knowledge for as long as
     *  the engine keeps them in those sets; poll on every event so a
     *  transient reveal is caught. */
    private void pollPublicKnowledge(Game game) {
        for (Collection<UUID> ids : revealedSets(game)) {
            for (UUID id : ids) {
                Card c = game.getCard(id);
                if (c != null && opp.equals(c.getOwnerId()) && !knownIds.containsKey(id)) {
                    knownIds.put(id, c.getName());
                    for (Slot s : hand) {
                        if (id.equals(s.card)) {
                            s.known = true;
                            s.seen = true;
                            s.name = c.getName();
                        }
                    }
                }
            }
        }
    }

    private List<Collection<UUID>> revealedSets(Game game) {
        List<Collection<UUID>> out = new ArrayList<>();
        try {
            for (mage.cards.Cards cs : game.getState().getRevealed().values()) {
                out.add(cs);
            }
            mage.game.LookedAt la = game.getState().getLookedAt(me);
            if (la != null) {
                for (mage.cards.Cards cs : la.values()) {
                    out.add(cs);
                }
            }
        } catch (RuntimeException ignored) {
            // a copied state mid-mutation; nothing public is lost, the
            // next event polls again
        }
        return out;
    }

    /** End of my turn: the opponent kept mana open and cast nothing on
     *  my turn - an observation about their hand (design §8). */
    private void pollEndOfMyTurn(Game game) {
        int turn = game.getTurnNum();
        if (turn == lastEndTurnSeen || game.getTurnStepType() != PhaseStep.END_TURN
                || !me.equals(game.getActivePlayerId())) {
            return;
        }
        lastEndTurnSeen = turn;
        if (oppCastThisTurn) {
            return;
        }
        int untapped = 0;
        for (Permanent p : game.getBattlefield().getAllActivePermanents(opp)) {
            if (p.isLand(game) && !p.isTapped()) {
                untapped++;
            }
        }
        if (untapped > 0) {
            act(A_PASSED_MANA_UP);
        }
    }

    // ------------------------------------------------------------ emission
    /** First emission: everything already face-up in a public zone is
     *  seen; then the slot count is reconciled with the opponent's hand
     *  size (late registration, mulligans, missed events). */
    private void reconcile(Game game) {
        Player op = game.getPlayer(opp);
        if (op == null) {
            return;
        }
        if (!scanned) {
            scanned = true;
            for (Permanent p : game.getBattlefield().getAllPermanents()) {
                if (opp.equals(p.getOwnerId())) {
                    seenIds.add(p.getId());
                    knownIds.put(p.getId(), p.getName());
                }
            }
            for (Card c : op.getGraveyard().getCards(game)) {
                seenIds.add(c.getId());
                knownIds.put(c.getId(), c.getName());
            }
            for (Card c : game.getExile().getCardsOwned(game, opp)) {
                seenIds.add(c.getId());
                knownIds.put(c.getId(), c.getName());
            }
            for (StackObject so : game.getStack()) {
                Card c = game.getCard(so.getSourceId());
                if (c != null && opp.equals(c.getOwnerId())) {
                    seenIds.add(c.getId());
                    knownIds.put(c.getId(), c.getName());
                }
            }
        }
        int actual = op.getHand().size();
        while (hand.size() > actual) {
            int victim = -1;
            for (int i = 0; i < hand.size() && victim < 0; i++) {
                if (hand.get(i).card == null) {
                    victim = i;
                }
            }
            for (int i = 0; i < hand.size() && victim < 0; i++) {
                if (!hand.get(i).known) {
                    victim = i;
                }
            }
            hand.remove(victim < 0 ? 0 : victim);
            handDrift++;
        }
        while (hand.size() < actual) {
            Slot s = new Slot();
            // the first reconciliation is the opening hand (turn <= 2 covers
            // both seats); anything reconciled later is a missed event
            s.origin = !openingDone && game.getTurnNum() <= 2 ? O_OPENING : O_OTHER;
            s.turnIn = s.origin == O_OPENING ? 0 : game.getTurnNum();
            hand.add(s);
            if (s.origin != O_OPENING) {
                handDrift++;
            }
        }
        openingDone = true;
    }

    public Emission emit(Game game, int oppUntappedLands, boolean oracle) {
        consults++;
        reconcile(game);
        Player op = game.getPlayer(opp);
        Emission e = new Emission();
        int turn = game.getTurnNum();
        int n = Math.min(hand.size(), StateEncoder.V7_OHMAX);
        e.handTrunc = hand.size() - n;
        e.hand = new float[n][];
        e.handName = new String[n];
        for (int i = 0; i < n; i++) {
            Slot s = hand.get(i);
            float[] r = new float[StateEncoder.V7_OHDIM];
            r[s.origin] = 1f;
            r[4] = Math.min(10, turn - s.turnIn) / 10f;
            r[5] = s.known ? 1f : 0f;
            r[6] = s.seen ? 1f : 0f;
            e.hand[i] = r;
            e.handName[i] = s.known ? s.name : null;
        }
        // remaining deck: the open list minus every card of theirs whose
        // identity is public (seen in a public zone, or a known hand card)
        Map<String, Integer> gone = new HashMap<>();
        Set<UUID> counted = new HashSet<>(seenIds);
        for (Slot s : hand) {
            if (s.known && s.card != null) {
                counted.add(s.card);
            }
        }
        for (UUID id : counted) {
            String nm = knownIds.get(id);
            if (nm != null) {
                gone.merge(nm, 1, Integer::sum);
            }
        }
        int library = op == null ? 0 : op.getLibrary().size();
        TreeMap<String, DeckCard> sorted = new TreeMap<>(deckInfo);
        List<float[]> rows = new ArrayList<>();
        List<String> names = new ArrayList<>();
        for (Map.Entry<String, DeckCard> en : sorted.entrySet()) {
            DeckCard info = en.getValue();
            int left = Math.max(0, info.count - gone.getOrDefault(en.getKey(), 0));
            if (left == 0 || rows.size() >= StateEncoder.V7_ODMAX) {
                continue;
            }
            float[] r = new float[StateEncoder.V7_ODDIM];
            r[0] = Math.min(4, left) / 4f;
            r[1] = library > 0 ? Math.min(1f, left / (float) library) : 0f;
            r[2] = info.mv <= oppUntappedLands ? 1f : 0f;
            r[3] = Math.min(6, info.mv) / 6f;
            r[4] = info.instantSpeed ? 1f : 0f;
            rows.add(r);
            names.add(en.getKey());
        }
        e.deck = rows.toArray(new float[0][]);
        e.deckName = names.toArray(new String[0]);
        int na = Math.min(acts.size(), StateEncoder.V7_OAMAX);
        e.actions = new float[na][];
        e.actionRefs = new UUID[na][];
        for (int i = 0; i < na; i++) {
            Act a = acts.get(acts.size() - 1 - i);          // newest first
            float[] r = new float[StateEncoder.V7_OADIM];
            r[a.type] = 1f;
            r[7] = Math.min(20, consults - a.consult) / 20f;
            e.actions[i] = r;
            e.actionRefs[i] = a.refs.toArray(new UUID[0]);
        }
        e.handDrift = handDrift;
        e.bornTurn = bornTurn;
        e.events = events;
        if (oracle && op != null) {
            List<String> truth = new ArrayList<>();
            for (Card c : op.getHand().getCards(game)) {
                truth.add(c.getName());
            }
            e.oeHand = truth.toArray(new String[0]);
        }
        return e;
    }
}
