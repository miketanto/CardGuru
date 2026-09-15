package org.mage.test.l17;

import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.PlayLandAbility;
import mage.abilities.SpellAbility;
import mage.abilities.keyword.DeathtouchAbility;
import mage.abilities.keyword.MenaceAbility;
import mage.cards.Card;
import mage.cards.Cards;
import mage.constants.Outcome;
import mage.target.TargetCard;
import mage.target.common.TargetCardInLibrary;
import mage.cards.repository.CardInfo;
import mage.cards.repository.CardRepository;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.filter.StaticFilters;
import mage.filter.common.FilterCreatureForCombat;
import mage.filter.predicate.Predicates;
import mage.filter.predicate.permanent.SummoningSicknessPredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.game.permanent.PermanentCard;
import mage.players.Player;
import mage.util.ThreadUtils;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;
import org.mage.test.serverside.base.MageTestPlayerBase;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;

/**
 * L17 fidelity trial: rebuild a logged 17Lands game in XMage, turn by turn.
 *
 * java -cp classes:CP org.mage.test.l17.L17Rebuild SPEC.tsv OUT.tsv
 * (run from a directory holding db/ and config/ copied from Mage.Tests)
 *
 * Both seats are driven by L17Player (a TestPlayer): forced land plays and casts
 * from the spec, forced attackers, blockers assigned to match the logged kills;
 * everything else (targets, modes, payments, "may" choices) falls to the
 * TestComputerPlayer AI. A snapshot of the compared fields is written at the
 * first priority of every turn for the turn before (i.e. after cleanup).
 * Output lines: R (snapshot), F (forced action failed), T (targeted spell),
 * X (block assignment), S (setup), Z (game status). Resumable: games with a Z
 * line in OUT are skipped.
 */
public class L17Rebuild extends CardTestPlayerBase {

    static final long TIMEOUT_MS = Long.getLong("l17.timeoutMs", 120_000L);

    static class Act {
        int turn;
        String seat, step, kind, name;
        boolean done;
    }

    static class Blk {
        int turn;
        String def;
        List<String> blockers, blocked, kDef, kAtk;
    }

    static class Spec {
        int idx;
        boolean userIsA;
        int last;
        Map<String, List<String>> hand = new HashMap<>(), lib = new HashMap<>();
        List<Act> acts = new ArrayList<>();
        Map<String, List<String>> atk = new HashMap<>();
        List<Blk> blocks = new ArrayList<>();
        Map<Integer, List<String>> draws = new HashMap<>();
        Map<String, List<String>> eotLands = new HashMap<>(); // turn:seat -> logged lands at end of turn
        Map<String, List<String>> eotCre = new HashMap<>();   // turn:seat -> logged creatures at end of turn
        Map<String, List<String>> kills = new HashMap<>();    // turn:seat -> that seat's creatures killed non-combat
        Map<Integer, List<String>> seen = new HashMap<>();    // turn -> user's logged hand + permanents at end of turn
    }

    /** -Dl17.guide=true: log-guided hidden choices (removal targets, manifest dread, draws rescued from the graveyard). */
    static final boolean GUIDE = Boolean.getBoolean("l17.guide");
    static final Map<String, Boolean> FLASH_CACHE = new HashMap<>();

    static boolean hasFlash(String name) {
        return FLASH_CACHE.computeIfAbsent(name, n -> {
            CardInfo ci = CardRepository.instance.findCard(dbName(n), true);
            if (ci == null) return false;
            Card c = ci.createCard();
            return c != null && c.getAbilities().containsClass(mage.abilities.keyword.FlashAbility.class);
        });
    }

    static final Map<String, String> PENDING_FETCH = new HashMap<>();
    static final Map<String, Integer> FETCH_TRIES = new HashMap<>();

    static Spec CUR;
    static PrintWriter OUT;
    static final Set<String> PREPARED = new HashSet<>();
    static int lastSnapTurn = 0;
    static UUID uId, oId;
    static final Map<String, String> NAME_CACHE = new HashMap<>();

    // ------------------------------------------------------------------ names
    static String front(String n) {
        if (n == null) return "";
        int i = n.indexOf(" // ");
        if (i >= 0) n = n.substring(0, i);
        return n.replace('’', '\'').trim().toLowerCase(Locale.ROOT);
    }

    static String pname(Permanent p, Game game) {
        if (p.isToken()) {
            String tn = front(p.getName());
            if (tn.endsWith(" token")) tn = tn.substring(0, tn.length() - 6);
            return "tok:" + tn;
        }
        String n = p.getName();
        if (p instanceof PermanentCard) {
            Card c = ((PermanentCard) p).getCard();
            if (c != null) n = c.getMainCard().getName();
        }
        String f = front(n);
        if (p.isFaceDown(game)) f = "FD:" + f;
        return f;
    }

    static boolean nameMatch(Permanent p, String want, Game game) {
        if ("TOKEN".equals(want)) return p.isToken();
        // 17Lands names face-down permanents (manifest dread) "[Face-Down Card]"
        if ("[face-down card]".equals(front(want))) return p.isFaceDown(game);
        return bare(pname(p, game)).equals(front(want));
    }

    static String bare(String n) {
        if (n.startsWith("FD:")) n = n.substring(3);
        if (n.startsWith("tok:")) n = n.substring(4);
        return n;
    }

    /** Where a player's card of this name is, for failure reasons. */
    static String where(Player pl, String name, Game game) {
        String n = front(name);
        for (Card c : pl.getHand().getCards(game)) if (front(c.getMainCard().getName()).equals(n)) return "hand";
        for (Card c : pl.getGraveyard().getCards(game)) if (front(c.getMainCard().getName()).equals(n)) return "graveyard";
        for (Permanent p : game.getBattlefield().getAllActivePermanents(pl.getId())) if (nameMatch(p, name, game)) return "battlefield";
        for (Card c : pl.getLibrary().getCards(game)) if (front(c.getMainCard().getName()).equals(n)) return "library";
        return "elsewhere";
    }

    static String dbName(String name) {
        return NAME_CACHE.computeIfAbsent(name, n -> {
            CardInfo ci = CardRepository.instance.findCard(n, true);
            if (ci != null) return n;
            if (n.contains(" // ")) {
                String f = n.substring(0, n.indexOf(" // "));
                if (CardRepository.instance.findCard(f, true) != null) return f;
            }
            return n;
        });
    }

    static void out(String s) {
        OUT.println(s.replace('\n', ' '));
    }

    static void fail(int turn, String seat, String kind, String name, String why) {
        out("F\t" + CUR.idx + "\t" + turn + "\t" + seat + "\t" + kind + "\t" + name + "\t" + why);
    }

    // --------------------------------------------------------------- snapshot
    static void snapshot(Game game, int turn, boolean over) {
        Player u = game.getPlayer(uId), o = game.getPlayer(oId);
        List<String> lands = new ArrayList<>(), cre = new ArrayList<>(), non = new ArrayList<>(), hand = new ArrayList<>();
        for (Permanent p : game.getBattlefield().getAllActivePermanents(uId)) {
            String n = pname(p, game);
            if (p.isLand(game)) lands.add(n);
            else if (p.isCreature(game)) cre.add(n);
            else non.add(n);
        }
        for (Card c : u.getHand().getCards(game)) hand.add(front(c.getMainCard().getName()));
        Collections.sort(lands);
        Collections.sort(cre);
        Collections.sort(non);
        Collections.sort(hand);
        out("R\t" + CUR.idx + "\t" + turn + "\t" + u.getLife() + "\t" + o.getLife() + "\t"
                + String.join("|", lands) + "\t" + String.join("|", cre) + "\t" + String.join("|", non) + "\t"
                + String.join("|", hand) + "\t" + o.getHand().size() + "\t" + (over ? 1 : 0));
    }

    static void onPriority(Game game) {
        int t = game.getTurnNum();
        if (t - 1 > lastSnapTurn) {
            snapshot(game, t - 1, false);
            lastSnapTurn = t - 1;
        }
    }

    // ----------------------------------------------------------------- player
    public static class L17Player extends TestPlayer {
        final String seat;

        public L17Player(TestComputerPlayer cp, String seat) {
            super(cp);
            this.seat = seat;
        }

        public L17Player(final L17Player o) {
            super(o);
            this.seat = o.seat;
        }

        @Override
        public L17Player copy() {
            return new L17Player(this);
        }

        @Override
        public boolean chooseMulligan(Game game) {
            return false;
        }

        @Override
        public boolean priority(Game game) {
            onPriority(game);
            int t = game.getTurnNum();
            if (PREPARED.add(t + ":" + seat)) {
                prepare(game, t);
            }
            if (game.getStack().isEmpty() && game.getTurnStepType() == PhaseStep.END_TURN) {
                String k = t + ":" + seat;
                int tries = FETCH_TRIES.getOrDefault(k, 0);
                if (tries < 3) {
                    FETCH_TRIES.put(k, tries + 1);
                    if (crackFetch(game, t)) return true;
                }
            }
            if (game.getStack().isEmpty()) {
                int stepIdx = game.getTurnStepType().getIndex();
                for (Act a : CUR.acts) {
                    if (a.done || a.turn != t || !a.seat.equals(seat)) continue;
                    if (PhaseStep.valueOf(a.step).getIndex() > stepIdx) continue;
                    a.done = true;
                    if (tryAct(game, a)) return true;
                }
            }
            return super.priority(game);
        }

        private boolean tryAct(Game game, Act a) {
            boolean land = "LAND".equals(a.kind);
            if ("CASTI".equals(a.kind) && !hasFlash(a.name)) {
                return false; // inferred from end-of-turn state but not a flash card: not a cast
            }
            List<ActivatedAbility> cands = new ArrayList<>();
            for (ActivatedAbility ab : getPlayable(game, true)) {
                if (land ? !(ab instanceof PlayLandAbility) : !(ab instanceof SpellAbility)) continue;
                Card c = game.getCard(ab.getSourceId());
                if (c == null) continue;
                String want = front(a.name);
                if (!front(c.getMainCard().getName()).equals(want) && !front(c.getName()).equals(want)) continue;
                cands.add(ab);
            }
            cands.sort(Comparator.comparingInt(ab -> {
                Card c = game.getCard(ab.getSourceId());
                return game.getState().getZone(c.getMainCard().getId()) == Zone.HAND ? 0 : 1;
            }));
            for (ActivatedAbility ab : cands) {
                boolean targeted = !ab.getTargets().isEmpty();
                int bm = game.bookmarkState();
                if (activateAbility(ab.copy(), game)) {
                    if (!land) {
                        out("T\t" + CUR.idx + "\t" + a.turn + "\t" + seat + "\t" + a.name + "\t" + (targeted ? 1 : 0));
                    }
                    return true;
                }
                game.restoreState(bm, "l17");
            }
            String why;
            if (cands.isEmpty()) {
                boolean inHand = false;
                for (Card c : getHand().getCards(game)) {
                    if (front(c.getMainCard().getName()).equals(front(a.name))) inHand = true;
                }
                why = inHand ? "not_playable" : "not_in_hand";
            } else {
                why = "activate_failed";
            }
            fail(a.turn, seat, a.kind, a.name, why + "@" + game.getTurnStepType());
            return false;
        }

        /**
         * Activated abilities are logged only as unmapped ability ids, so they are not replayed in
         * general. One kind is replayed because it is common (Terramorphic Expanse is in a third of
         * the decks) and fully determined by the logged lands: a land with a "sacrifice ... search
         * your library" ability that the engine still holds but the log's end-of-turn lands no
         * longer do is cracked at the end step, fetching the basic the log gained.
         */
        private boolean crackFetch(Game game, int t) {
            List<String> logged = CUR.eotLands.get(t + ":" + seat);
            if (logged == null) return false;
            List<String> logN = new ArrayList<>();
            for (String s : logged) logN.add(front(s));
            List<Permanent> lands = new ArrayList<>();
            List<String> engN = new ArrayList<>();
            for (Permanent p : game.getBattlefield().getAllActivePermanents(getId())) {
                if (p.isLand(game)) {
                    lands.add(p);
                    engN.add(bare(pname(p, game)));
                }
            }
            for (Permanent p : lands) {
                String n = bare(pname(p, game));
                if (Collections.frequency(engN, n) <= Collections.frequency(logN, n)) continue;
                for (ActivatedAbility ab : getPlayable(game, true)) {
                    if (!ab.getSourceId().equals(p.getId()) || ab instanceof mage.abilities.mana.ManaAbility) continue;
                    String rule = ab.getRule().toLowerCase(Locale.ROOT);
                    if (!rule.contains("sacrifice") || !rule.contains("search your library")) continue;
                    List<String> missing = new ArrayList<>(logN);
                    for (String e : engN) missing.remove(e);
                    String basic = null;
                    for (String m : missing) {
                        if (Arrays.asList("plains", "island", "swamp", "mountain", "forest").contains(m)) {
                            basic = m;
                            break;
                        }
                    }
                    if (basic != null) PENDING_FETCH.put(seat, basic);
                    int bm = game.bookmarkState();
                    if (activateAbility(ab.copy(), game)) {
                        out("T\t" + CUR.idx + "\t" + t + "\t" + seat + "\tFETCH:" + n + ">" + basic + "\t0");
                        return true;
                    }
                    game.restoreState(bm, "l17");
                    PENDING_FETCH.remove(seat);
                    fail(t, seat, "FETCH", n, "activate_failed");
                }
            }
            return false;
        }

        /** Guided mode, user seat: a library search takes the card the log shows arriving this turn. */
        private boolean pickSearch(Cards cards, TargetCard target, Game game) {
            if (!GUIDE || !"U".equals(seat) || !(target instanceof TargetCardInLibrary) || cards == null) return false;
            List<String> vis = CUR.seen.get(game.getTurnNum());
            if (vis == null) return false;
            List<String> want = new ArrayList<>();
            for (String s : vis) want.add(front(s));
            for (Card c : getHand().getCards(game)) want.remove(front(c.getMainCard().getName()));
            for (Permanent p : game.getBattlefield().getAllActivePermanents(getId())) want.remove(bare(pname(p, game)));
            for (Card c : cards.getCards(game)) {
                String n = front(c.getMainCard().getName());
                if (want.contains(n) && ((TargetCardInLibrary) target).getFilter().match(c, game)) {
                    target.add(c.getId(), game);
                    out("G\t" + CUR.idx + "\t" + game.getTurnNum() + "\t" + seat + "\tsearch\t" + n);
                    return true;
                }
            }
            return false;
        }

        private boolean pickFetch(Cards cards, TargetCard target, Game game) {
            if (!(target instanceof TargetCardInLibrary)) return false;
            String want = PENDING_FETCH.remove(seat);
            if (want == null) return pickSearch(cards, target, game);
            if (cards == null) return false;
            for (Card c : cards.getCards(game)) {
                if (front(c.getName()).equals(want)) {
                    target.add(c.getId(), game);
                    return true;
                }
            }
            return false;
        }

        @Override
        public boolean choose(Outcome outcome, Cards cards, TargetCard target, Ability source, Game game) {
            if (pickFetch(cards, target, game)) return true;
            if (GUIDE && outcome == Outcome.PutCreatureInPlay && cards != null && pickManifest(cards, target, game)) return true;
            return super.choose(outcome, cards, target, source, game);
        }

        /** Guided mode, manifest dread: the log names the face-down card, so manifest the one the log shows arriving. */
        private boolean pickManifest(Cards cards, TargetCard target, Game game) {
            int t = game.getTurnNum();
            List<String> logged = CUR.eotCre.get(t + ":" + seat);
            if (logged == null) return false;
            List<String> want = new ArrayList<>();
            for (String s : logged) want.add(front(s));
            for (Permanent p : game.getBattlefield().getAllActivePermanents(getId())) want.remove(bare(pname(p, game)));
            for (Card c : cards.getCards(game)) {
                if (want.contains(front(c.getMainCard().getName()))) {
                    target.add(c.getId(), game);
                    out("G\t" + CUR.idx + "\t" + t + "\t" + seat + "\tmanifest\t" + front(c.getMainCard().getName()));
                    return true;
                }
            }
            // the logged card is not in the engine's top two (library order below the logged
            // draws is unknown): swap it in from deeper in the library (doManifestDread reads
            // the choice back through this same Cards object; the swapped-out card stays in library)
            for (Card c : getLibrary().getCards(game)) {
                if (cards.contains(c.getId()) || !want.contains(front(c.getMainCard().getName()))) continue;
                UUID drop = cards.iterator().next();
                cards.remove(drop);
                cards.add(c);
                target.add(c.getId(), game);
                out("G\t" + CUR.idx + "\t" + t + "\t" + seat + "\tmanifest_swapped\t" + front(c.getMainCard().getName()));
                return true;
            }
            return false;
        }

        /** Guided mode: a harmful targeted choice prefers permanents the log says died (non-combat) this turn. */
        @Override
        public boolean chooseTarget(Outcome outcome, mage.target.Target target, Ability source, Game game) {
            if (GUIDE && !outcome.isGood()) {
                int t = game.getTurnNum();
                List<String> killed = new ArrayList<>();
                for (String s : new String[]{"U", "O"}) {
                    List<String> k = CUR.kills.get(t + ":" + s);
                    if (k != null) for (String x : k) killed.add(front(x));
                }
                if (!killed.isEmpty()) {
                    for (UUID id : target.possibleTargets(getId(), source, game)) {
                        Permanent p = game.getPermanent(id);
                        if (p == null || !killed.contains(bare(pname(p, game)))) continue;
                        if (!target.canTarget(id, source, game)) continue;
                        target.addTarget(id, source, game);
                        killed.remove(bare(pname(p, game)));
                        out("G\t" + CUR.idx + "\t" + t + "\t" + seat + "\ttarget\t" + bare(pname(p, game)));
                        if (target.isChosen(game)) return true;
                    }
                }
            }
            return super.chooseTarget(outcome, target, source, game);
        }

        @Override
        public boolean chooseTarget(Outcome outcome, Cards cards, TargetCard target, Ability source, Game game) {
            if (pickFetch(cards, target, game)) return true;
            return super.chooseTarget(outcome, cards, target, source, game);
        }

        /** User: stack this turn's logged draws on top. Opponent: swap needed cards into its hidden hand. */
        private void prepare(Game game, int t) {
            if ("U".equals(seat)) {
                List<String> d = CUR.draws.get(t);
                if (d == null) return;
                for (int i = d.size() - 1; i >= 0; i--) {
                    Card hit = null;
                    for (Card c : getLibrary().getCards(game)) {
                        if (front(c.getMainCard().getName()).equals(front(d.get(i)))) {
                            hit = c;
                            break;
                        }
                    }
                    if (hit == null && GUIDE) {
                        for (Card c : getGraveyard().getCards(game)) {
                            if (front(c.getMainCard().getName()).equals(front(d.get(i)))) {
                                hit = c;
                                break;
                            }
                        }
                        if (hit != null) {
                            getGraveyard().remove(hit);
                            hit.setZone(Zone.LIBRARY, game);
                            getLibrary().putOnTop(hit, game);
                            fail(t, seat, "DRAW", d.get(i), "rescued_from_graveyard");
                            continue;
                        }
                    }
                    if (hit == null) {
                        fail(t, seat, "DRAW", d.get(i), "not_in_library_" + where(this, d.get(i), game));
                        continue;
                    }
                    getLibrary().remove(hit.getId(), game);
                    getLibrary().putOnTop(hit, game);
                }
                return;
            }
            List<String> need = new ArrayList<>();
            for (Act a : CUR.acts) {
                if (a.turn == t && a.seat.equals(seat) && (!"CASTI".equals(a.kind) || hasFlash(a.name))) need.add(front(a.name));
            }
            if (need.isEmpty()) return;
            Set<String> future = new HashSet<>();
            for (Act a : CUR.acts) {
                if (a.turn > t && a.seat.equals(seat)) future.add(front(a.name));
            }
            List<Card> hand = new ArrayList<>(getHand().getCards(game));
            List<Card> reserved = new ArrayList<>();
            for (String n : need) {
                Card have = null;
                for (Card c : hand) {
                    if (!reserved.contains(c) && front(c.getMainCard().getName()).equals(n)) {
                        have = c;
                        break;
                    }
                }
                if (have != null) {
                    reserved.add(have);
                    continue;
                }
                Card lib = null;
                for (Card c : getLibrary().getCards(game)) {
                    if (front(c.getMainCard().getName()).equals(n)) {
                        lib = c;
                        break;
                    }
                }
                if (lib == null) {
                    String where = "missing";
                    for (Card c : getGraveyard().getCards(game)) {
                        if (front(c.getMainCard().getName()).equals(n)) where = "graveyard";
                    }
                    for (Permanent p : game.getBattlefield().getAllActivePermanents(getId())) {
                        if (nameMatch(p, n, game)) where = "battlefield";
                    }
                    fail(t, seat, "SWAP", n, "not_in_library_" + where);
                    continue;
                }
                // spare: a hand card not needed now, preferring cards never needed later
                Card spare = null;
                for (int pass = 0; pass < 2 && spare == null; pass++) {
                    for (Card c : hand) {
                        if (reserved.contains(c)) continue;
                        String cn = front(c.getMainCard().getName());
                        if (need.contains(cn)) continue;
                        if (pass == 0 && future.contains(cn)) continue;
                        spare = c;
                        break;
                    }
                }
                getLibrary().remove(lib.getId(), game);
                lib.setZone(Zone.HAND, game);
                getHand().add(lib);
                hand.add(lib);
                reserved.add(lib);
                if (spare != null) {
                    getHand().remove(spare);
                    hand.remove(spare);
                    spare.setZone(Zone.LIBRARY, game);
                    getLibrary().putOnBottom(spare, game);
                } else {
                    fail(t, seat, "SWAP", n, "no_spare_hand_grew");
                }
            }
        }

        @Override
        public void selectAttackers(Game game, UUID attackingPlayerId) {
            int t = game.getTurnNum();
            List<String> names = CUR.atk.get(t + ":" + seat);
            if (names == null) return;
            UUID def = game.getOpponents(getId()).iterator().next();
            FilterCreatureForCombat f = new FilterCreatureForCombat();
            f.add(Predicates.not(SummoningSicknessPredicate.instance));
            List<Permanent> avail = new ArrayList<>(game.getBattlefield().getAllActivePermanents(f, getId(), game));
            for (String n : names) {
                Permanent pick = null;
                for (Permanent p : avail) {
                    if (nameMatch(p, n, game) && p.canAttack(def, game)) {
                        pick = p;
                        break;
                    }
                }
                if (pick == null) {
                    String why = "absent";
                    for (Permanent p : game.getBattlefield().getAllActivePermanents(StaticFilters.FILTER_PERMANENT_CREATURE, getId(), game)) {
                        if (nameMatch(p, n, game)) {
                            why = p.isTapped() ? "tapped" : (p.isAttacking() ? "already_attacking" : "sick_or_cannot");
                            break;
                        }
                    }
                    fail(t, seat, "ATTACK", n, "no_attacker_" + why);
                    continue;
                }
                avail.remove(pick);
                declareAttacker(pick.getId(), def, game, false);
                // restrictions ("can't attack unless ...") can refuse the declaration silently
                if (!game.getCombat().getAttackers().contains(pick.getId())) {
                    fail(t, seat, "ATTACK", n, "attack_rejected");
                }
            }
        }

        @Override
        public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
            int t = game.getTurnNum();
            for (Blk b : CUR.blocks) {
                if (b.turn != t || !b.def.equals(seat)) continue;
                List<Permanent> mine = new ArrayList<>();
                for (Permanent p : game.getBattlefield().getAllActivePermanents(StaticFilters.FILTER_PERMANENT_CREATURE, getId(), game)) {
                    if (!p.isTapped()) mine.add(p);
                }
                List<Permanent> atks = new ArrayList<>();
                for (UUID id : game.getCombat().getAttackers()) {
                    Permanent p = game.getPermanent(id);
                    if (p != null) atks.add(p);
                }
                List<Permanent> bl = new ArrayList<>();
                for (String n : b.blockers) {
                    Permanent hit = null;
                    for (Permanent p : mine) {
                        if (!bl.contains(p) && nameMatch(p, n, game)) {
                            hit = p;
                            break;
                        }
                    }
                    if (hit == null) fail(t, seat, "BLOCK", n, "no_blocker");
                    else bl.add(hit);
                }
                List<Permanent> at = new ArrayList<>();
                for (String n : b.blocked) {
                    Permanent hit = null;
                    for (Permanent p : atks) {
                        if (!at.contains(p) && nameMatch(p, n, game)) {
                            hit = p;
                            break;
                        }
                    }
                    if (hit == null) fail(t, seat, "BLOCK", n, "no_blocked_attacker");
                    else at.add(hit);
                }
                if (at.isEmpty()) at.addAll(atks);
                if (bl.isEmpty() || at.isEmpty()) continue;
                int nb = bl.size(), na = at.size();
                long total = 1;
                for (int i = 0; i < nb && total <= 50_000; i++) total *= na;
                int[] best = null;
                int bestScore = Integer.MAX_VALUE;
                Set<String> bestSigs = new HashSet<>();
                if (total > 50_000) {
                    best = new int[nb];
                    for (int i = 0; i < nb; i++) best[i] = i % na;
                    bestSigs.add("greedy");
                    bestSigs.add("greedy2");
                } else {
                    int[] as = new int[nb];
                    for (long code = 0; code < total; code++) {
                        long c = code;
                        for (int i = 0; i < nb; i++) {
                            as[i] = (int) (c % na);
                            c /= na;
                        }
                        int[] cnt = new int[na];
                        boolean legal = true;
                        for (int i = 0; i < nb; i++) {
                            cnt[as[i]]++;
                            if (!bl.get(i).canBlock(at.get(as[i]).getId(), game)) legal = false;
                        }
                        if (!legal) continue;
                        if (nb >= na) {
                            for (int j = 0; j < na; j++) if (cnt[j] == 0) legal = false;
                        }
                        for (int j = 0; j < na && legal; j++) {
                            if (cnt[j] == 1 && at.get(j).getAbilities().containsClass(MenaceAbility.class)) legal = false;
                        }
                        if (!legal) continue;
                        int s = score(as, bl, at, b, game);
                        String sig = sig(as, bl, at, game);
                        if (s < bestScore) {
                            bestScore = s;
                            best = as.clone();
                            bestSigs.clear();
                            bestSigs.add(sig);
                        } else if (s == bestScore) {
                            bestSigs.add(sig);
                        }
                    }
                }
                if (best == null) {
                    fail(t, seat, "BLOCK", String.join("|", b.blockers), "no_legal_assignment");
                    continue;
                }
                out("X\t" + CUR.idx + "\t" + t + "\t" + seat + "\t" + bestSigs.size() + "\t" + bestScore + "\t" + nb + "\t" + na);
                for (int i = 0; i < nb; i++) {
                    declareBlocker(defendingPlayerId, bl.get(i).getId(), at.get(best[i]).getId(), game);
                }
            }
        }
    }

    static int tough(Permanent p) {
        return p.getToughness().getValue() - p.getDamage();
    }

    static String sig(int[] as, List<Permanent> bl, List<Permanent> at, Game game) {
        List<String> parts = new ArrayList<>();
        for (int i = 0; i < as.length; i++) parts.add(pname(bl.get(i), game) + ">" + pname(at.get(as[i]), game));
        Collections.sort(parts);
        return String.join(",", parts);
    }

    /** Distance between predicted combat deaths and the logged ones (0 = consistent). */
    static int score(int[] as, List<Permanent> bl, List<Permanent> at, Blk b, Game game) {
        List<String> dDef = new ArrayList<>(), dAtk = new ArrayList<>();
        for (int j = 0; j < at.size(); j++) {
            Permanent a = at.get(j);
            List<Permanent> s = new ArrayList<>();
            for (int i = 0; i < as.length; i++) if (as[i] == j) s.add(bl.get(i));
            if (s.isEmpty()) continue;
            int sumP = 0;
            boolean dt = false;
            for (Permanent x : s) {
                sumP += Math.max(0, x.getPower().getValue());
                if (x.getAbilities().containsClass(DeathtouchAbility.class) && x.getPower().getValue() > 0) dt = true;
            }
            if (sumP >= tough(a) || dt) dAtk.add(pname(a, game));
            boolean adt = a.getAbilities().containsClass(DeathtouchAbility.class);
            int rem = Math.max(0, a.getPower().getValue());
            s.sort(Comparator.comparingInt(L17Rebuild::tough));
            for (Permanent x : s) {
                int need = adt ? 1 : Math.max(1, tough(x));
                if (rem >= need) {
                    dDef.add(pname(x, game));
                    rem -= need;
                }
            }
        }
        return symdiff(dDef, b.kDef) + symdiff(dAtk, b.kAtk);
    }

    static int symdiff(List<String> pred, List<String> logged) {
        List<String> l = new ArrayList<>();
        for (String s : logged) l.add("TOKEN".equals(s) ? "TOKEN" : front(s));
        int d = 0;
        for (String s : pred) {
            String k = s.startsWith("FD:") ? s.substring(3) : s;
            if (!l.remove(k)) d++;
        }
        return d + l.size();
    }

    // ------------------------------------------------------------- framework
    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        boolean isA = "PlayerA".equals(playerName);
        String seat = (isA == CUR.userIsA) ? "U" : "O";
        return new L17Player(new TestComputerPlayer(playerName, rangeOfInfluence), seat);
    }

    String runOne(Spec s) {
        CUR = s;
        PREPARED.clear();
        PENDING_FETCH.clear();
        FETCH_TRIES.clear();
        lastSnapTurn = 0;
        try {
            reset();
            setStrictChooseMode(false);
            skipInitShuffling();
            TestPlayer u = s.userIsA ? playerA : playerB;
            TestPlayer o = s.userIsA ? playerB : playerA;
            uId = u.getId();
            oId = o.getId();
            removeAllCardsFromLibrary(playerA);
            removeAllCardsFromLibrary(playerB);
            for (String seat : new String[]{"U", "O"}) {
                TestPlayer p = "U".equals(seat) ? u : o;
                List<String> lib = s.lib.get(seat);
                for (int i = lib.size() - 1; i >= 0; i--) addCard(Zone.LIBRARY, p, dbName(lib.get(i)));
                for (String h : s.hand.get(seat)) addCard(Zone.HAND, p, dbName(h));
            }
            setStopAt(s.last + 1, PhaseStep.UPKEEP);
            execute();
            finalSnap();
            return "ok";
        } catch (Throwable e) {
            try {
                finalSnap();
            } catch (Throwable ignored) {
            }
            String m = String.valueOf(e.getMessage());
            if (m.length() > 200) m = m.substring(0, 200);
            return "error:" + e.getClass().getSimpleName() + ":" + m.replace('\t', ' ');
        }
    }

    void finalSnap() {
        Game g = currentGame;
        if (g == null || uId == null) return;
        int t = g.getTurnNum();
        boolean over = g.hasEnded();
        if (over && t > lastSnapTurn) {
            snapshot(g, t, true);
            lastSnapTurn = t;
        } else if (!over && t - 1 > lastSnapTurn) {
            snapshot(g, t - 1, false);
            lastSnapTurn = t - 1;
        }
    }

    // ------------------------------------------------------------------ specs
    static List<String> split(String s) {
        List<String> r = new ArrayList<>();
        if (s == null || s.isEmpty()) return r;
        for (String x : s.split("\\|")) if (!x.isEmpty()) r.add(x);
        return r;
    }

    static List<Spec> parse(String path) throws IOException {
        List<Spec> specs = new ArrayList<>();
        Spec cur = null;
        for (String line : Files.readAllLines(Paths.get(path), StandardCharsets.UTF_8)) {
            String[] f = line.split("\t", -1);
            switch (f[0]) {
                case "G":
                    cur = new Spec();
                    cur.idx = Integer.parseInt(f[1]);
                    cur.userIsA = "1".equals(f[2]);
                    cur.last = Integer.parseInt(f[3]);
                    break;
                case "H":
                    cur.hand.put(f[1], split(f[2]));
                    break;
                case "L":
                    cur.lib.put(f[1], split(f[2]));
                    break;
                case "A": {
                    Act a = new Act();
                    a.turn = Integer.parseInt(f[1]);
                    a.seat = f[2];
                    a.step = f[3];
                    a.kind = f[4];
                    a.name = f[5];
                    cur.acts.add(a);
                    break;
                }
                case "K":
                    cur.atk.put(f[1] + ":" + f[2], split(f[3]));
                    break;
                case "B": {
                    Blk b = new Blk();
                    b.turn = Integer.parseInt(f[1]);
                    b.def = f[2];
                    b.blockers = split(f[3]);
                    b.blocked = split(f[4]);
                    b.kDef = split(f[5]);
                    b.kAtk = split(f[6]);
                    cur.blocks.add(b);
                    break;
                }
                case "D":
                    cur.draws.put(Integer.parseInt(f[1]), split(f[3]));
                    break;
                case "P":
                    cur.eotLands.put(f[1] + ":" + f[2], split(f[3]));
                    break;
                case "Q":
                    cur.eotCre.put(f[1] + ":" + f[2], split(f[3]));
                    break;
                case "N":
                    cur.kills.put(f[1] + ":" + f[2], split(f[3]));
                    break;
                case "W":
                    cur.seen.put(Integer.parseInt(f[1]), split(f[3]));
                    break;
                case "E":
                    specs.add(cur);
                    cur = null;
                    break;
                default:
            }
        }
        return specs;
    }

    public static void main(String[] args) throws Exception {
        MageTestPlayerBase.init();
        Logger.getRootLogger().setLevel(Level.ERROR);
        List<Spec> specs = parse(args[0]);
        Set<Integer> done = new HashSet<>();
        File outF = new File(args[1]);
        if (outF.exists()) {
            for (String line : Files.readAllLines(outF.toPath(), StandardCharsets.UTF_8)) {
                if (line.startsWith("Z\t")) done.add(Integer.parseInt(line.split("\t")[1]));
            }
        }
        OUT = new PrintWriter(new BufferedWriter(new OutputStreamWriter(new FileOutputStream(outF, true), StandardCharsets.UTF_8)));
        int batch = args.length > 2 ? Integer.parseInt(args[2]) : Integer.MAX_VALUE;
        int ran = 0;
        L17Rebuild r = new L17Rebuild();
        for (Spec s : specs) {
            if (done.contains(s.idx)) continue;
            if (ran++ >= batch) {
                OUT.flush();
                System.exit(4); // batch finished, more games remain (driver re-checks memory and relaunches)
            }
            final String[] res = {"no_result"};
            long t0 = System.currentTimeMillis();
            Thread th = new Thread(() -> res[0] = r.runOne(s), ThreadUtils.THREAD_PREFIX_GAME + " l17-" + s.idx);
            th.setDaemon(true);
            th.start();
            th.join(TIMEOUT_MS);
            long ms = System.currentTimeMillis() - t0;
            if (th.isAlive()) {
                out("Z\t" + s.idx + "\ttimeout\t" + ms);
                OUT.flush();
                System.exit(3);
            }
            out("Z\t" + s.idx + "\t" + res[0] + "\t" + ms);
            OUT.flush();
        }
        OUT.flush();
        System.exit(0);
    }
}
