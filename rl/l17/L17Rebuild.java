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
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.effects.common.InfoEffect;
import mage.cards.repository.CardInfo;
import mage.cards.repository.CardRepository;
import mage.cards.repository.TokenInfo;
import mage.cards.repository.TokenRepository;
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
import mage.game.permanent.token.Token;
import mage.players.Player;
import mage.util.CardUtil;
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
        int tries;
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
        // ---- cloud variant data (rl/L17-FIDELITY-CLOUD.md §2)
        List<Act> abils = new ArrayList<>();                  // ABIL: logged ability, by owning card name
        Map<Integer, List<String>> future = new HashMap<>();  // FUT: user's draws on this turn or later
        Map<String, List<String>> disc = new HashMap<>();     // DISC: turn:seat -> cards discarded
        Map<String, List<String>> rsPerm = new HashMap<>();   // RS: turn:seat -> permanents at end of turn
        Map<Integer, int[]> rsLife = new HashMap<>();         // RL: turn -> {user life, oppo life}
        Map<Integer, List<String>> rsHand = new HashMap<>();  // RH: turn -> user's hand at end of turn
        Map<Integer, Integer> rsOHand = new HashMap<>();      // RO: turn -> opponent's hand SIZE
    }

    /** -Dl17.guide=true: log-guided hidden choices (removal targets, manifest dread, draws rescued from the graveyard). */
    static final boolean GUIDE = Boolean.getBoolean("l17.guide");

    /**
     * -Dl17.variant=base|abil|choice|oppo|order|resync|all (comma separated also accepted).
     * "all" is abil+choice+oppo+order; resync is a different measurement and is never
     * included in "all". See rl/L17-FIDELITY-CLOUD.md §2 for what each may and may not move.
     */
    static final String VARIANT = System.getProperty("l17.variant", "base");
    static final Set<String> VARIANTS = new HashSet<>(Arrays.asList(VARIANT.split(",")));

    static boolean on(String v) {
        return VARIANTS.contains(v) || (VARIANTS.contains("all") && !"resync".equals(v));
    }

    static final boolean V_ABIL = on("abil"), V_CHOICE = on("choice"), V_OPPO = on("oppo"),
            V_ORDER = on("order"), V_RESYNC = on("resync");
    /** the log-outcome steering of hidden choices: the original guided run, or the `choice` variant. */
    static final boolean STEER = GUIDE || V_CHOICE;
    static final int ORDER_MAX_TRIES = 8;
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
            if (V_RESYNC && t > 1) resync(game, t - 1);
        }
    }

    // ---------------------------------------------------------------- resync
    /**
     * `resync` variant (rl/L17-FIDELITY-CLOUD.md §2a). Right after the snapshot for
     * side-turn T is taken, the engine's state is pushed to the LOGGED end-of-side-turn-T
     * state, so side-turn T+1 is replayed from a correct start rather than from whatever
     * the replay had drifted to. That makes each side-turn an independent test of
     * one-turn fidelity, which is a different quantity from "turns matched before the
     * first mismatch" and is reported separately, never against the base run.
     *
     * Three things the log does not hold, and which therefore cannot be resynced:
     * a token or a [Face-Down Card] the engine does not already have (the log names the
     * token but not which card is under a face-down permanent, and the token's identity
     * is not enough to rebuild its characteristics reliably) -- these are counted as
     * `unmet`; the CONTENTS of the opponent's hand (only its size is logged); and
     * everything the compared state never held -- graveyards, exile, counters, tapped
     * status, the libraries' order below the forced draws.
     */
    static Ability fakeAbility(UUID controllerId) {
        Ability a = new SimpleStaticAbility(Zone.OUTSIDE, new InfoEffect("l17 resync"));
        a.setControllerId(controllerId);
        return a;
    }

    static Card findCard(Player p, String name, Game game) {
        String n = front(name);
        for (Card c : p.getLibrary().getCards(game)) if (front(c.getMainCard().getName()).equals(n)) return c;
        for (Card c : p.getHand().getCards(game)) if (front(c.getMainCard().getName()).equals(n)) return c;
        for (Card c : p.getGraveyard().getCards(game)) if (front(c.getMainCard().getName()).equals(n)) return c;
        return null;
    }

    /** Take a card out of whatever zone it is in so it can be moved somewhere else. */
    static void detach(Player p, Card c, Game game) {
        p.getLibrary().remove(c.getId(), game);
        p.getHand().remove(c);
        p.getGraveyard().remove(c);
    }

    /** A copy of the named card, registered with the game, for a permanent the log has and the engine does not. */
    static Card freshCard(Game game, Player p, String name) {
        CardInfo ci = CardRepository.instance.findCard(dbName(name), true);
        if (ci == null) return null;
        Card c = ci.createCard();
        if (c == null) return null;
        game.loadCards(new HashSet<>(Collections.singletonList(c)), p.getId());
        return c;
    }

    static boolean addPermanent(Game game, Player p, String name) {
        Card c = findCard(p, name, game);
        if (c != null) detach(p, c, game);
        else c = freshCard(game, p, name);
        if (c == null) return false;
        try {
            CardUtil.putCardOntoBattlefieldWithEffects(fakeAbility(p.getId()), game, c, p, false);
            return true;
        } catch (Throwable e) {
            return false;
        }
    }

    static boolean addToken(Game game, Player p, String tokenName) {
        try {
            for (TokenInfo ti : TokenRepository.instance.getAll()) {
                if (!front(ti.getName()).equals(front(tokenName))) continue;
                Object o = Class.forName(ti.getFullClassFileName()).getDeclaredConstructor().newInstance();
                if (!(o instanceof Token)) continue;
                Set<UUID> before = new HashSet<>();
                for (Permanent q : game.getBattlefield().getAllActivePermanents(p.getId())) before.add(q.getId());
                if (!((Token) o).putOntoBattlefield(1, game, fakeAbility(p.getId()), p.getId())) return false;
                for (Permanent q : game.getBattlefield().getAllActivePermanents(p.getId())) {
                    if (!before.contains(q.getId()) && q instanceof mage.game.permanent.PermanentImpl) {
                        ((mage.game.permanent.PermanentImpl) q).removeSummoningSickness();
                    }
                }
                return true;
            }
        } catch (Throwable ignored) {
        }
        return false;
    }

    /** Remove a permanent the log does not have, without firing leave-the-battlefield triggers. */
    static void removeSilently(Game game, Permanent perm, Player p) {
        // Break both directions of every attachment first. A host that keeps the id of a
        // removed aura or equipment is dereferenced by the AI's board evaluator
        // (GameStateEvaluator2.evaluatePermanent) and throws, killing the game.
        for (UUID aid : new ArrayList<>(perm.getAttachments())) {
            Permanent at = game.getPermanent(aid);
            if (at != null) at.unattach(game);
        }
        if (perm.getAttachedTo() != null) {
            Permanent host = game.getPermanent(perm.getAttachedTo());
            if (host != null) host.removeAttachment(perm.getId(), null, game);
            perm.unattach(game);
        }
        game.getBattlefield().removePermanent(perm.getId());
        if (perm instanceof PermanentCard) {
            Card c = ((PermanentCard) perm).getCard();
            if (c != null) {
                c.setZone(Zone.GRAVEYARD, game);
                p.getGraveyard().add(c);
            }
        }
    }

    static void resync(Game game, int T) {
        Player u = game.getPlayer(uId), o = game.getPlayer(oId);
        int unmet = 0, removed = 0, added = 0, handFix = 0;
        int[] lf = CUR.rsLife.get(T);
        if (lf != null) {
            u.setLife(lf[0], game, (Ability) null);
            o.setLife(lf[1], game, (Ability) null);
        }
        for (String s : new String[]{"U", "O"}) {
            Player p = "U".equals(s) ? u : o;
            List<String> want = CUR.rsPerm.get(T + ":" + s);
            if (want == null) continue;
            List<String> wantN = new ArrayList<>();
            for (String x : want) wantN.add(x.startsWith("tok:") ? "tok:" + front(x.substring(4)) : front(x));
            List<Permanent> extra = new ArrayList<>();
            for (Permanent perm : game.getBattlefield().getAllActivePermanents(p.getId())) {
                String n = pname(perm, game);                       // tok:x / FD:x / plain
                String key = n.startsWith("FD:") ? "fd" : n;
                if (wantN.remove(key) || wantN.remove(bare(n))) continue;
                extra.add(perm);
            }
            for (Permanent perm : extra) {
                removeSilently(game, perm, p);
                removed++;
            }
            for (String n : wantN) {
                boolean ok;
                if ("fd".equals(n)) ok = false;                     // the log never says what is under it
                else if (n.startsWith("tok:")) ok = addToken(game, p, n.substring(4));
                else ok = addPermanent(game, p, n);
                if (ok) added++;
                else unmet++;
            }
        }
        List<String> wh = CUR.rsHand.get(T);
        if (wh != null) {
            List<String> wantH = new ArrayList<>();
            for (String x : wh) wantH.add(front(x));
            for (Card c : new ArrayList<>(u.getHand().getCards(game))) {
                if (wantH.remove(front(c.getMainCard().getName()))) continue;
                u.getHand().remove(c);
                c.setZone(Zone.LIBRARY, game);
                u.getLibrary().putOnBottom(c, game);
                handFix++;
            }
            for (String n : wantH) {
                Card c = findCard(u, n, game);
                if (c != null) detach(u, c, game);
                else c = freshCard(game, u, n);
                if (c == null) {
                    unmet++;
                    continue;
                }
                c.setZone(Zone.HAND, game);
                u.getHand().add(c);
                handFix++;
            }
        }
        Integer oh = CUR.rsOHand.get(T);
        if (oh != null) {
            while (o.getHand().size() < oh) {
                Card c = o.getLibrary().removeFromTop(game);
                if (c == null) break;
                c.setZone(Zone.HAND, game);
                o.getHand().add(c);
                handFix++;
            }
            while (o.getHand().size() > oh) {
                Card c = o.getHand().getCards(game).iterator().next();
                o.getHand().remove(c);
                c.setZone(Zone.LIBRARY, game);
                o.getLibrary().putOnBottom(c, game);
                handFix++;
            }
            if (o.getHand().size() != oh) unmet++;
        }
        game.applyEffects();
        out("RS\t" + CUR.idx + "\t" + T + "\t" + unmet + "\t" + removed + "\t" + added + "\t" + handFix);
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
                boolean pending = false;
                for (Act a : CUR.acts) {
                    if (a.done || a.turn != t || !a.seat.equals(seat)) continue;
                    if (PhaseStep.valueOf(a.step).getIndex() > stepIdx) {
                        pending = true;
                        continue;
                    }
                    // `order` variant: a cast that is not payable or not yet drawable in
                    // this step is left pending and retried at every later priority of the
                    // same turn (so the effective within-turn order is whatever works),
                    // instead of being spent on its first chance. Base marks it done here.
                    boolean last = !V_ORDER || ++a.tries >= ORDER_MAX_TRIES
                            || game.getTurnStepType() == PhaseStep.END_TURN;
                    a.done = !V_ORDER || last;
                    if (tryAct(game, a, last)) return true;
                    if (!a.done) pending = true;
                }
                if (V_ABIL && !pending) {
                    for (Act a : CUR.abils) {
                        if (a.done || a.turn != t || !a.seat.equals(seat)) continue;
                        a.done = true;
                        if (tryAbility(game, a)) return true;
                    }
                }
            }
            return super.priority(game);
        }

        /**
         * `abil` variant: rl/l17/ability_map.py identified which CARD owns each logged
         * ability id, but not which ability of it, so activate the first playable
         * non-mana activated ability of a permanent or hand card of that name. Casts
         * and land plays are excluded -- those are already forced from the log.
         */
        private boolean tryAbility(Game game, Act a) {
            String want = front(a.name);
            List<ActivatedAbility> cands = new ArrayList<>();
            for (ActivatedAbility ab : getPlayable(game, true)) {
                if (ab instanceof mage.abilities.mana.ManaAbility || ab instanceof SpellAbility
                        || ab instanceof PlayLandAbility) continue;
                Card c = game.getCard(ab.getSourceId());
                if (c == null) continue;
                if (!front(c.getMainCard().getName()).equals(want) && !front(c.getName()).equals(want)) continue;
                cands.add(ab);
            }
            for (ActivatedAbility ab : cands) {
                int bm = game.bookmarkState();
                if (activateAbility(ab.copy(), game)) {
                    out("T\t" + CUR.idx + "\t" + a.turn + "\t" + seat + "\tABIL:" + a.name + "\t0");
                    return true;
                }
                game.restoreState(bm, "l17");
            }
            fail(a.turn, seat, "ABIL", a.name,
                    (cands.isEmpty() ? "no_activatable_ability_" + where(this, a.name, game) : "activate_failed")
                            + "@" + game.getTurnStepType());
            return false;
        }

        private boolean tryAct(Game game, Act a, boolean reportFailure) {
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
            if (reportFailure) fail(a.turn, seat, a.kind, a.name, why + "@" + game.getTurnStepType());
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
            if (!STEER || !"U".equals(seat) || !(target instanceof TargetCardInLibrary) || cards == null) return false;
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
            if (STEER && outcome == Outcome.PutCreatureInPlay && cards != null && pickManifest(cards, target, game)) return true;
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
            // `choice` variant: a forced discard takes the card the log records discarded
            // that turn. (Rare in this sample: ~0.5 logged discards per game.)
            if (V_CHOICE && outcome == Outcome.Discard) {
                List<String> want = CUR.disc.get(game.getTurnNum() + ":" + seat);
                if (want != null) {
                    List<String> w = new ArrayList<>();
                    for (String s : want) w.add(front(s));
                    for (Card c : getHand().getCards(game)) {
                        if (!w.contains(front(c.getMainCard().getName()))) continue;
                        if (!target.canTarget(getId(), c.getId(), source, game)) continue;
                        target.addTarget(c.getId(), source, game);
                        w.remove(front(c.getMainCard().getName()));
                        out("G\t" + CUR.idx + "\t" + game.getTurnNum() + "\t" + seat + "\tdiscard\t"
                                + front(c.getMainCard().getName()));
                        if (target.isChosen(game)) return true;
                    }
                }
            }
            if (STEER && !outcome.isGood()) {
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
            if (pickLibraryOrder(cards, target, game)) return true;
            if (pickFetch(cards, target, game)) return true;
            return super.chooseTarget(outcome, cards, target, source, game);
        }

        /**
         * `choice` variant: surveil and scry both ask, through this method, which of the
         * top N cards to move off the top (PlayerImpl.doSurveil -> graveyard,
         * PlayerImpl.scry -> bottom). The base rebuild leaves it to the AI, and the
         * verified single biggest mechanism of unseen drift (rl/L17-FIDELITY.md §5,
         * game 167) is an AI surveil burying a card the log draws two turns later.
         * Here every card the log shows the user drawing on this turn or a later one is
         * kept on top, and the rest are moved off -- the choice a player who knew the
         * future would make, which is what "steered by the logged outcome" means.
         */
        private boolean pickLibraryOrder(Cards cards, TargetCard target, Game game) {
            if (!V_CHOICE || !"U".equals(seat) || cards == null || cards.isEmpty()) return false;
            String tn = target.getTargetName() == null ? "" : target.getTargetName();
            if (!tn.contains("(Surveil)") && !tn.contains("(Scry)")) return false;
            int at = Integer.MAX_VALUE;
            for (Integer k : CUR.future.keySet()) {
                if (k >= game.getTurnNum() && k < at) at = k;
            }
            List<String> keep = new ArrayList<>();
            if (at != Integer.MAX_VALUE) {
                for (String s : CUR.future.get(at)) keep.add(front(s));
            }
            int moved = 0;
            for (Card c : cards.getCards(game)) {
                String n = front(c.getMainCard().getName());
                if (keep.remove(n)) continue;              // a logged future draw: leave on top
                target.add(c.getId(), game);
                moved++;
                if (target.getTargets().size() >= target.getMaxNumberOfTargets()) break;
            }
            out("G\t" + CUR.idx + "\t" + game.getTurnNum() + "\t" + seat + "\t"
                    + (tn.contains("(Scry)") ? "scry" : "surveil") + "\t" + moved + "/" + cards.size());
            return true;
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
                    if (hit == null && STEER) {
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
            if (V_OPPO) sizeOppoHand(game, t);
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

        /**
         * `oppo` variant. The opponent's hand is logged only as a COUNT, and the base
         * rebuild keeps its size fixed by swapping one card out for each one it swaps in
         * -- which drifts whenever it has no spare to give back ("no_spare_hand_grew", 87
         * records in the 200-game base run) or whenever an unreplayed ability drew it a
         * card. Here the size is pushed to the logged end-of-previous-turn count, taking
         * from or giving back to the top of its library. Only the COUNT is logged, so
         * this fixes the compared field while the hand's CONTENTS stay invented.
         */
        private void sizeOppoHand(Game game, int t) {
            Integer want = CUR.rsOHand.get(t - 1);
            if (want == null) return;
            // the seat draws for its turn before this point, except on game turn 1
            int target = want + (game.getActivePlayerId().equals(getId()) && t > 1 ? 1 : 0);
            int have = getHand().size();
            for (int i = have; i < target; i++) {
                Card c = getLibrary().removeFromTop(game);
                if (c == null) break;
                c.setZone(Zone.HAND, game);
                getHand().add(c);
            }
            for (int i = have; i > target; i--) {
                Card spare = null;
                Set<String> need = new HashSet<>();
                for (Act a : CUR.acts) {
                    if (a.turn >= t && a.seat.equals(seat) && !a.done) need.add(front(a.name));
                }
                for (Card c : getHand().getCards(game)) {
                    if (!need.contains(front(c.getMainCard().getName()))) {
                        spare = c;
                        break;
                    }
                }
                if (spare == null) break;
                getHand().remove(spare);
                spare.setZone(Zone.LIBRARY, game);
                getLibrary().putOnBottom(spare, game);
            }
            if (getHand().size() != target) {
                fail(t, seat, "OHAND", String.valueOf(target), "size_" + getHand().size());
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
                case "ABIL": {
                    Act a = new Act();
                    a.turn = Integer.parseInt(f[1]);
                    a.seat = f[2];
                    a.step = "PRECOMBAT_MAIN";
                    a.kind = "ABIL";
                    a.name = f[3];
                    cur.abils.add(a);
                    break;
                }
                case "FUT":
                    cur.future.put(Integer.parseInt(f[1]), split(f[2]));
                    break;
                case "DISC":
                    cur.disc.put(f[1] + ":" + f[2], split(f[3]));
                    break;
                case "RS":
                    cur.rsPerm.put(f[1] + ":" + f[2], split(f[3]));
                    break;
                case "RL":
                    cur.rsLife.put(Integer.parseInt(f[1]), new int[]{Integer.parseInt(f[2]), Integer.parseInt(f[3])});
                    break;
                case "RH":
                    cur.rsHand.put(Integer.parseInt(f[1]), split(f[2]));
                    break;
                case "RO":
                    cur.rsOHand.put(Integer.parseInt(f[1]), Integer.parseInt(f[2]));
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
