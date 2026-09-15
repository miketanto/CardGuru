package org.mage.test.benchmark.rl;

import mage.MageObject;
import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.PlayLandAbility;
import mage.abilities.SpellAbility;
import mage.cards.Card;
import mage.cards.Cards;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.Target;
import mage.target.TargetCard;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * 7d piece (1b) + Phase 13a: XMage's ComputerPlayer7 as an imitation
 * TEACHER on the v7 wire. The seat plays exactly as CP7 does; at every
 * decision where RLPlayer would consult its policy it ALSO emits the
 * consult RLPlayer would have emitted, labelled y = the index of the
 * candidate CP7 chose (-1 = CP7's choice is not in the candidate list).
 * The reply is ignored - CP7 already acted.
 *
 * PRIORITY (7d1b): same candidate list as RLPlayer.priority (getPlayable,
 * phantom-land filter, mana-ability filter unless rl.manaCands, name|rule
 * order); state taken BEFORE super.priority, label = the first non-mana
 * ability CP7 activates (y = 0 passed, i+1 = playable.get(i)).
 *
 * TARGETS (13a): RLPlayer consults once per required target
 * (policyPickTargets / policyPickCards: while chosen < min, candidates =
 * possibleTargets minus chosen, canTarget-filtered, sorted by canonical
 * name). CP7 chooses targets two ways: (a) a spell/ability cast from its
 * search arrives at activateAbility with its targets PRESET (the engine
 * then skips the choice, Targets.makeChoice isChoiceSelected) - labelled
 * at that interception, the view taken there (the spell still in hand,
 * where the RL seat's consult sees it on the stack: stated in the row);
 * (b) triggered / choose-style targets go through chooseTarget / choose,
 * wrapped here: CP7 chooses, the picks are read back and labelled, the
 * view taken before the choice. Candidate lists are built on a copy of
 * the target holding only the targets chosen before the RL loop.
 * A target with min 0 is never consulted by the RL seat (counted
 * tgtOptional).
 *
 * JOINT ATTACK / BLOCK (13a): the candidate list is JointCands.attacks /
 * blocks - the builders RLPlayer.jointAttacks / jointBlocks themselves
 * call - built before CP7 declares; the declared set is read back from
 * the combat and matched (JointCands.matchAttack / matchBlock: exact,
 * alias = same outcome key, miss = -1 counted teacherJointMiss).
 *
 * Simulations: ComputerPlayer6 replaces every player of its simulated
 * game copies with SimulatedPlayer2, so this object's overrides never see
 * a simulation; the isSimulation() guards are belt and braces.
 */
public class CP7TeacherPlayer extends mage.player.ai.ComputerPlayer7 {

    /** the recording policy (the echo server); null = plain CP7 */
    public PolicyClient policy;
    public long benchSeed = 0;
    /** 3d: the opponent's open decklist, set by EpisodeRunner (tracker) */
    public java.util.Map<String, RLKnowledgeWatcher.DeckCard> oppDeckInfo;
    /** the RL seat's budget: decisions past it are played unlabelled */
    public long consultBudget = Long.getLong("rl.consultBudget", 20000L);
    /** 7a amendment: mana abilities are candidates only with rl.manaCands */
    public boolean manaCands = Boolean.getBoolean("rl.manaCands");

    public long windows = 0, consults = 0, autoPassK0 = 0, manaCandsDropped = 0;
    /** priority-consult counters (the 7d1b names) */
    public long teacherLabelled = 0, teacherPassed = 0, teacherOutside = 0,
            teacherMultiAct = 0, teacherBudgetSkipped = 0, prioConsults = 0;
    /** 13a counters */
    public long tgtConsults = 0, tgtLabelled = 0, tgtOutside = 0, tgtOptional = 0,
            tgtPreset = 0, tgtBudgetSkipped = 0;
    public long atkConsults = 0, atkExact = 0, atkAlias = 0, atkMiss = 0;
    public long blkConsults = 0, blkExact = 0, blkAlias = 0, blkMiss = 0;
    public long jointFallbacks = 0;

    private boolean capturing = false;
    private ActivatedAbility captured = null;
    private int extraActs = 0;
    private boolean inChoose = false;

    public CP7TeacherPlayer(String name, RangeOfInfluence range, int skill) {
        super(name, range, skill);
    }

    private UUID opponentId(Game game) {
        for (UUID opp : game.getOpponents(playerId)) {
            return opp;
        }
        return playerId;
    }

    private void ensureTracker(Game game) {
        if (StateEncoder.ENCODER_V >= 7) {
            RLKnowledgeWatcher.ensure(game, playerId, opponentId(game), oppDeckInfo);
        }
    }

    private boolean live(Game game) {
        return policy != null && !game.isSimulation() && StateEncoder.ENCODER_V >= 7;
    }

    /** one labelled consult; consultsSoFar = the RL seat's running count */
    private void send(StateEncoder.EntityView view, float[][] cands,
                      StateEncoder.CandMeta meta, int y) {
        meta.consultsSoFar = consults;
        consults++;
        if (policy instanceof SocketPolicyClient) {
            ((SocketPolicyClient) policy).teacherY = y;
        }
        policy.choose(view, cands, 0f, meta);   // reply ignored: CP7 acted
    }

    // ------------------------------------------------------------ priority

    @Override
    public boolean activateAbility(ActivatedAbility ability, Game game) {
        // 13a: CP7's pass is itself an activation (act() activates the
        // PassAbility its search chose) - a pass is y = 0, never captured
        if (capturing && !game.isSimulation() && !ability.isManaAbility()
                && !(ability instanceof mage.abilities.common.PassAbility)) {
            if (captured == null) {
                captured = ability;
            } else {
                extraActs++;
            }
        }
        // 13a (a): targets preset by CP7's search. Attempt 2: the picks are
        // read here, the consults are built AFTER the activation, with the
        // spell / ability on the stack (the RL seat's target consult sees
        // it there; attempt 1 took the view with the spell still in hand,
        // so the targeting object was invisible). Costs are paid by then.
        List<Target> presetT = null;
        List<List<UUID>> presetP = null;
        if (live(game) && !ability.isManaAbility() && !inChoose
                && !ability.getTargets().isEmpty()) {
            presetT = new ArrayList<>();
            presetP = new ArrayList<>();
            for (Target t : ability.getTargets()) {
                presetT.add(t.copy());
                presetP.add(new ArrayList<>(t.getTargets()));
            }
        }
        boolean ok = super.activateAbility(ability, game);
        if (ok && presetT != null) {
            try {
                labelPresetTargets(presetT, presetP, ability, game);
            } catch (RuntimeException e) {
                tgtOutside++;       // never let a label break CP7's play
            }
        }
        return ok;
    }

    @Override
    public boolean priority(Game game) {
        if (policy == null || game.isSimulation() || !canRespond()
                || StateEncoder.ENCODER_V < 7) {
            return super.priority(game);
        }
        windows++;
        ensureTracker(game);
        boolean myTurn = playerId.equals(game.getActivePlayerId());
        boolean sorceryWindow = myTurn && game.getStack().isEmpty()
                && (game.getTurnStepType() == PhaseStep.PRECOMBAT_MAIN
                || game.getTurnStepType() == PhaseStep.POSTCOMBAT_MAIN);
        List<ActivatedAbility> playable;
        try {
            playable = new ArrayList<>(getPlayable(game, true));
        } catch (Exception e) {
            return super.priority(game);
        }
        // exactly RLPlayer.priority's filters and order
        playable.removeIf(a -> a instanceof PlayLandAbility && !sorceryWindow);
        if (!manaCands) {
            int before = playable.size();
            playable.removeIf(a -> a.isManaAbility());
            manaCandsDropped += before - playable.size();
        }
        if (playable.isEmpty()) {
            // the RL seat auto-passes k=0 without a consult; CP7 plays the
            // window as itself (there is nothing it could do but pass)
            autoPassK0++;
            return super.priority(game);
        }
        playable.sort(Comparator.comparing(a -> {
            MageObject o = game.getObject(a.getSourceId());
            return (o == null ? "?" : o.getName()) + "|" + a.getRule();
        }));
        if (consults >= consultBudget) {
            teacherBudgetSkipped++;
            return super.priority(game);
        }
        // the pre-action consult, built as RLPlayer.priority builds it
        float[][] cands = new float[playable.size() + 1][];
        StateEncoder.CandMeta meta = new StateEncoder.CandMeta(cands.length).pass(0);
        int untappedNow = StateEncoder.untappedLands(game, playerId);
        cands[0] = StateEncoder.blank(StateEncoder.T_PASS);
        for (int i = 0; i < playable.size(); i++) {
            ActivatedAbility a = playable.get(i);
            meta.set(i + 1, a instanceof PlayLandAbility ? StateEncoder.C_LAND
                    : a instanceof SpellAbility ? StateEncoder.C_SPELL
                    : StateEncoder.C_ACTIVATE, a.getSourceId());
            Card card = game.getCard(a.getSourceId());
            cands[i + 1] = StateEncoder.forCard(
                    a instanceof PlayLandAbility
                            ? StateEncoder.T_LAND : StateEncoder.T_SPELL,
                    card, game);
            meta.after(i + 1, StateEncoder.v7AfterPlayable(a, card, game, playerId, untappedNow));
        }
        StateEncoder.EntityView view =
                StateEncoder.encodeEntityView(game, playerId, opponentId(game));
        // the priority consult precedes its target consults in the RL seat:
        // reserve its slot in the running count before CP7 acts
        long mySlot = consults;
        consults++;

        // CP7 decides and acts
        capturing = true;
        captured = null;
        extraActs = 0;
        boolean r;
        try {
            r = super.priority(game);
        } finally {
            capturing = false;
        }
        int y;
        if (captured == null) {
            y = 0;
            teacherPassed++;
        } else {
            y = matchLabel(captured, playable, game);
        }
        if (extraActs > 0) {
            teacherMultiAct++;
        }
        if (y >= 0) {
            teacherLabelled++;
        } else {
            teacherOutside++;
        }
        prioConsults++;
        meta.consultsSoFar = mySlot;
        if (policy instanceof SocketPolicyClient) {
            ((SocketPolicyClient) policy).teacherY = y;
        }
        policy.choose(view, cands, 0f, meta);   // reply ignored: CP7 acted
        return r;
    }

    /** index of the acted ability in RLPlayer's candidate space (1-based;
     *  -1 = outside the set), keyed sourceId|rule as shadowLabel does;
     *  13a: when the acted copy's rule text differs from the playable
     *  ability's (a chosen mode, an X, a target named in the text), the
     *  unique candidate with the same source and ability class is the
     *  label (counted prioAlias); remaining misses are logged to stderr. */
    private int matchLabel(ActivatedAbility chosen, List<ActivatedAbility> playable, Game game) {
        String key = chosen.getSourceId() + "|" + chosen.getRule();
        for (int i = 0; i < playable.size(); i++) {
            ActivatedAbility a = playable.get(i);
            if ((a.getSourceId() + "|" + a.getRule()).equals(key)) {
                return i + 1;
            }
        }
        int hit = -1, same = 0, sameSrc = 0;
        for (int i = 0; i < playable.size(); i++) {
            ActivatedAbility a = playable.get(i);
            if (!a.getSourceId().equals(chosen.getSourceId())) {
                continue;
            }
            sameSrc++;
            if ((a instanceof SpellAbility) == (chosen instanceof SpellAbility)
                    && (a instanceof PlayLandAbility) == (chosen instanceof PlayLandAbility)) {
                hit = i;
                same++;
            }
        }
        if (same == 1) {
            prioAlias++;
            return hit + 1;
        }
        if (missLogged++ < 40) {
            MageObject o = game.getObject(chosen.getSourceId());
            StringBuilder cs = new StringBuilder();
            for (ActivatedAbility a : playable) {
                MageObject ao = game.getObject(a.getSourceId());
                cs.append(ao == null ? "?" : ao.getName()).append('/')
                        .append(a.getClass().getSimpleName()).append(';');
            }
            System.err.println("TEACHER_MISS|prio|" + (o == null ? "?" : o.getName())
                    + "|" + chosen.getClass().getSimpleName() + "|rule=" + chosen.getRule()
                    + "|sameSrc=" + sameSrc + "|sameClass=" + same + "|cands=" + cs);
        }
        return -1;
    }

    public long prioAlias = 0;
    private int missLogged = 0;

    // ------------------------------------------------------------- targets

    /** RLPlayer.canonicalName, verbatim */
    private static String canonicalName(UUID id, Game game) {
        Player pl = game.getPlayer(id);
        if (pl != null) {
            return "player:" + pl.getName();
        }
        MageObject o = game.getObject(id);
        if (o != null) {
            return o.getName();
        }
        Card c = game.getCard(id);
        return c != null ? c.getName() : id.toString();
    }

    /** a copy of the target holding only `keep` (the RL loop's state) */
    private static Target baseCopy(Target target, List<UUID> keep) {
        Target t2 = target.copy();
        for (UUID id : new ArrayList<>(t2.getTargets())) {
            if (!keep.contains(id)) {
                t2.remove(id);
            }
        }
        return t2;
    }

    private StateEncoder.EntityView targetView(Game game) {
        ensureTracker(game);
        return StateEncoder.encodeEntityView(game, playerId, opponentId(game));
    }

    /** RLPlayer.policyPickTargets' consults, labelled with CP7's picks */
    private void targetConsults(Target target, Ability source, Game game,
                                List<UUID> before, List<UUID> picks,
                                StateEncoder.EntityView view) {
        int need = target.getMinNumberOfTargets() - before.size();
        if (need <= 0) {
            if (!picks.isEmpty()) {
                tgtOptional++;
            }
            return;
        }
        Target base = baseCopy(target, before);
        List<UUID> chosen = new ArrayList<>(before);
        for (int j = 0; j < need && j < picks.size(); j++) {
            if (consults >= consultBudget) {
                tgtBudgetSkipped++;
                return;
            }
            List<UUID> possible = new ArrayList<>(
                    base.possibleTargets(playerId, source, game));
            possible.removeAll(chosen);
            possible.removeIf(id -> !base.canTarget(playerId, id, source, game));
            if (possible.isEmpty()) {
                return;
            }
            possible.sort(Comparator.comparing(id -> canonicalName(id, game)));
            float[][] cands = new float[possible.size()][];
            StateEncoder.CandMeta meta = new StateEncoder.CandMeta(cands.length);
            for (int i = 0; i < possible.size(); i++) {
                UUID id = possible.get(i);
                meta.set(i, StateEncoder.C_TARGET, id);
                meta.after(i, StateEncoder.v7AfterTarget(id, game, playerId));
                Player pl = game.getPlayer(id);
                if (pl != null) {
                    cands[i] = StateEncoder.forTargetPlayer(
                            id.equals(playerId), pl.getLife());
                } else {
                    Permanent perm = game.getPermanent(id);
                    if (perm != null) {
                        cands[i] = StateEncoder.forTargetPermanent(perm, game, playerId);
                    } else {
                        Card c = game.getCard(id);
                        cands[i] = StateEncoder.forCard(StateEncoder.T_TARGET, c, game);
                    }
                }
            }
            int y = possible.indexOf(picks.get(j));
            tgtConsults++;
            if (y >= 0) {
                tgtLabelled++;
            } else {
                tgtOutside++;
            }
            send(view, cands, meta, y);
            chosen.add(picks.get(j));
        }
    }

    /** RLPlayer.policyPickCards' consults, labelled with CP7's picks */
    private void cardConsults(Cards cards, TargetCard target, Ability source,
                              Game game, List<UUID> before, List<UUID> picks,
                              StateEncoder.EntityView view) {
        int need = target.getMinNumberOfTargets() - before.size();
        if (need <= 0) {
            if (!picks.isEmpty()) {
                tgtOptional++;
            }
            return;
        }
        Target base = baseCopy(target, before);
        List<UUID> chosen = new ArrayList<>(before);
        for (int j = 0; j < need && j < picks.size(); j++) {
            if (consults >= consultBudget) {
                tgtBudgetSkipped++;
                return;
            }
            List<Card> possible = new ArrayList<>(cards.getCards(game));
            possible.removeIf(c -> chosen.contains(c.getId())
                    || !base.canTarget(playerId, c.getId(), source, game));
            if (possible.isEmpty()) {
                return;
            }
            possible.sort(Comparator.comparing(MageObject::getName));
            float[][] cands = new float[possible.size()][];
            StateEncoder.CandMeta meta = new StateEncoder.CandMeta(cands.length);
            int y = -1;
            for (int i = 0; i < possible.size(); i++) {
                cands[i] = StateEncoder.forCard(StateEncoder.T_TARGET,
                        possible.get(i), game);
                meta.set(i, StateEncoder.C_TARGET, possible.get(i).getId());
                meta.after(i, StateEncoder.v7AfterTarget(possible.get(i).getId(), game, playerId));
                if (possible.get(i).getId().equals(picks.get(j))) {
                    y = i;
                }
            }
            tgtConsults++;
            if (y >= 0) {
                tgtLabelled++;
            } else {
                tgtOutside++;
            }
            send(view, cands, meta, y);
            chosen.add(picks.get(j));
        }
    }

    private void labelPresetTargets(List<Target> ts, List<List<UUID>> allPicks,
                                    ActivatedAbility ability, Game game) {
        StateEncoder.EntityView view = null;
        for (int ti = 0; ti < ts.size(); ti++) {
            Target t = ts.get(ti);
            List<UUID> picks = allPicks.get(ti);
            if (picks.isEmpty()) {
                continue;
            }
            if (t.getMinNumberOfTargets() <= 0) {
                tgtOptional++;
                continue;
            }
            if (view == null) {
                view = targetView(game);
            }
            tgtPreset++;
            targetConsults(t, ability, game, new ArrayList<>(), picks, view);
        }
    }

    private interface Chooser {
        boolean run();
    }

    private boolean wrapTarget(Target target, Ability source, Game game, Chooser c) {
        if (inChoose || !live(game) || target == null
                || target.getMinNumberOfTargets() - target.getTargets().size() <= 0) {
            return c.run();
        }
        List<UUID> before = new ArrayList<>(target.getTargets());
        StateEncoder.EntityView view = targetView(game);
        boolean r;
        inChoose = true;
        try {
            r = c.run();
        } finally {
            inChoose = false;
        }
        try {
            List<UUID> picks = new ArrayList<>(target.getTargets());
            picks.removeAll(before);
            targetConsults(target, source, game, before, picks, view);
        } catch (RuntimeException e) {
            tgtOutside++;
        }
        return r;
    }

    private boolean wrapCards(Cards cards, TargetCard target, Ability source,
                              Game game, Chooser c) {
        if (inChoose || !live(game) || target == null || cards == null
                || target.getMinNumberOfTargets() - target.getTargets().size() <= 0) {
            return c.run();
        }
        List<UUID> before = new ArrayList<>(target.getTargets());
        StateEncoder.EntityView view = targetView(game);
        boolean r;
        inChoose = true;
        try {
            r = c.run();
        } finally {
            inChoose = false;
        }
        try {
            List<UUID> picks = new ArrayList<>(target.getTargets());
            picks.removeAll(before);
            cardConsults(cards, target, source, game, before, picks, view);
        } catch (RuntimeException e) {
            tgtOutside++;
        }
        return r;
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Target target, Ability source, Game game) {
        return wrapTarget(target, source, game,
                () -> super.chooseTarget(outcome, target, source, game));
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source, Game game) {
        return wrapTarget(target, source, game,
                () -> super.choose(outcome, target, source, game));
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source, Game game,
                          Map<String, java.io.Serializable> options) {
        return wrapTarget(target, source, game,
                () -> super.choose(outcome, target, source, game, options));
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Cards cards, TargetCard target,
                                Ability source, Game game) {
        return wrapCards(cards, target, source, game,
                () -> super.chooseTarget(outcome, cards, target, source, game));
    }

    @Override
    public boolean choose(Outcome outcome, Cards cards, TargetCard target,
                          Ability source, Game game) {
        return wrapCards(cards, target, source, game,
                () -> super.choose(outcome, cards, target, source, game));
    }

    // -------------------------------------------------------------- combat

    private static int indexOfId(List<Permanent> ps, UUID id) {
        for (int i = 0; i < ps.size(); i++) {
            if (ps.get(i).getId().equals(id)) {
                return i;
            }
        }
        return -1;
    }

    @Override
    public void selectAttackers(Game game, UUID attackingPlayerId) {
        if (!live(game) || consults >= consultBudget || StateEncoder.ENCODER_V < 5) {
            super.selectAttackers(game, attackingPlayerId);
            return;
        }
        UUID defender = opponentId(game);
        List<Permanent> avail = new ArrayList<>(getAvailableAttackers(game));
        if (avail.isEmpty()) {
            super.selectAttackers(game, attackingPlayerId);
            return;
        }
        // RLPlayer.selectAttackers' order (v >= 5): body, name tiebreak
        avail.sort(Comparator
                .comparingInt((Permanent p) -> p.getToughness().getValue())
                .thenComparingInt(p -> p.getPower().getValue())
                .thenComparing(MageObject::getName));
        ensureTracker(game);
        JointCands.Attack ja = JointCands.attacks(game, defender, avail,
                getLife(), true, n -> jointFallbacks++);
        StateEncoder.EntityView view = StateEncoder.encodeEntityView(game, playerId, defender);
        super.selectAttackers(game, attackingPlayerId);
        Set<UUID> declared = new HashSet<>();
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID a : g.getAttackers()) {
                Permanent p = game.getPermanent(a);
                if (p != null && playerId.equals(p.getControllerId())) {
                    declared.add(a);
                }
            }
        }
        int[] how = new int[1];
        int y = JointCands.matchAttack(ja, declared, how);
        atkConsults++;
        if (how[0] == 0) {
            atkExact++;
        } else if (how[0] == 1) {
            atkAlias++;
        } else {
            atkMiss++;
            if (missLogged++ < 40) {
                int inPick = 0;
                for (Permanent p : ja.pick) {
                    if (declared.contains(p.getId())) {
                        inPick++;
                    }
                }
                System.err.println("TEACHER_MISS|atk|declared=" + declared.size()
                        + "|inPick=" + inPick + "|avail=" + avail.size()
                        + "|pick=" + ja.pick.size() + "|options=" + ja.search.options.size()
                        + "|kept=" + ja.kept.size() + "|theirs=" + ja.theirs.size());
            }
        }
        send(view, ja.cands, ja.meta, y);
    }

    @Override
    public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
        if (!live(game) || consults >= consultBudget || StateEncoder.ENCODER_V < 4) {
            super.selectBlockers(source, game, defendingPlayerId);
            return;
        }
        List<Permanent> attackers = new ArrayList<>();
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID atkId : g.getAttackers()) {
                Permanent atk = game.getPermanent(atkId);
                if (atk != null) {
                    attackers.add(atk);
                }
            }
        }
        if (attackers.isEmpty()) {
            super.selectBlockers(source, game, defendingPlayerId);
            return;
        }
        attackers.sort(Comparator.comparing(MageObject::getName));
        List<Permanent> mine = new ArrayList<>();
        for (Permanent p : game.getBattlefield().getAllActivePermanents(playerId)) {
            if (p.isCreature(game) && !p.isTapped()) {
                mine.add(p);
            }
        }
        mine.sort(Comparator
                .comparingInt((Permanent p) -> p.getToughness().getValue())
                .thenComparingInt(p -> p.getPower().getValue())
                .thenComparing(MageObject::getName));
        ensureTracker(game);
        JointCands.Block jb = JointCands.blocks(attackers, mine, getLife(), true,
                n -> jointFallbacks++);
        int lifeBefore = getLife();
        StateEncoder.EntityView view =
                StateEncoder.encodeEntityView(game, playerId, opponentId(game));
        super.selectBlockers(source, game, defendingPlayerId);
        int[] declared = new int[mine.size()];
        Arrays.fill(declared, -1);
        for (CombatGroup g : game.getCombat().getGroups()) {
            if (g.getAttackers().isEmpty()) {
                continue;
            }
            int ai = indexOfId(attackers, g.getAttackers().get(0));
            for (UUID bId : g.getBlockers()) {
                int bi = indexOfId(mine, bId);
                if (bi >= 0 && declared[bi] < 0) {
                    declared[bi] = ai;
                }
            }
        }
        int[] how = new int[1];
        int y = JointCands.matchBlock(jb, declared, lifeBefore, how);
        blkConsults++;
        if (how[0] == 0) {
            blkExact++;
        } else if (how[0] == 1) {
            blkAlias++;
        } else {
            blkMiss++;
        }
        send(view, jb.cands, jb.meta, y);
    }
}
