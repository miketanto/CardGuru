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
import mage.game.stack.StackObject;
import mage.player.ai.ComputerPlayer;
import mage.players.Player;
import mage.target.Target;
import mage.target.TargetCard;
import mage.util.RandomUtil;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;

/**
 * The RL agent seat. All DECISION callbacks are policy-delegated with
 * canonical candidate ordering; wrapper filters run before anything
 * reaches the policy:
 *   - phantom land drop removed outside own main / empty stack
 *   - k=0 windows auto-passed without a consult
 *   - Phase 2 yield predicates (REACTIVE / MY_NEXT_MAIN) auto-pass runs
 *     of windows the policy has implicitly released
 *
 * DOCUMENTED DEVIATION from the spec's "extends PlayerImpl / no
 * ComputerPlayer anywhere": this class extends ComputerPlayer to reuse
 * its mana-payment SOLVER only. Every callback where ComputerPlayer
 * tie-breaks by UUID order (priority, targets, combat, discard) is
 * overridden here with policy delegation over name-sorted candidates.
 * Mana payment on the bench pools is tie-break-inert (identical basic
 * lands); any OTHER heuristic callback that fires is counted in
 * fallbackCalls and reported, not silently absorbed.
 */
public class RLPlayer extends ComputerPlayer {

    public PolicyClient policy;
    public long benchSeed = 0;
    private int shuffleCount = 0;

    // agent-seat accounting (per episode; reset by driver)
    public long windows = 0;
    public long consults = 0;
    public long yieldSkipped = 0;
    public long autoPassK0 = 0;
    public long actions = 0;
    public long failedActivations = 0;
    /** C7 emergence metric: flash/instant-speed-castable PERMANENT spells
     *  cast on the opponent's turn vs total - the draw-go behavior we
     *  want to see emerge without a teacher */
    public long flashThreatCasts = 0;
    public long flashThreatCastsOppTurn = 0;

    /** Phase 7c: blocks the agent actually declared (the scratch agent's
     *  headline hole is that it never blocks - the mirror never punished
     *  it, so the deck curriculum has to). */
    public long blocksDeclared = 0;
    /** Windows where a block was legal at all, so the counter above can
     *  be read as a RATE rather than an artifact of board state. */
    public long blockOpportunities = 0;
    /** -Drl.blockAudit: compare the policy's WHOLE block assignment against
     *  CombatMath's best for the same position. This is the low-variance
     *  A/B metric - a within-net measurement on the positions the agent
     *  actually reached, rather than a win rate that between-run variance
     *  swamps (seeds 0 and 1 differed .635 vs .500 at one checkpoint). */
    public long blockCombats = 0;
    public long blockCombatsOptimal = 0;
    public long blockScoreGap = 0;
    public long blockTruncated = 0;
    /** per-episode consult budget: a runaway episode (random policy can
     * mana-loop) degrades to always-pass instead of hanging the driver */
    public long consultBudget = Long.getLong("rl.consultBudget", 20000L);
    public boolean budgetExhausted = false;
    public final Map<String, Integer> fallbackCalls = new TreeMap<>();
    /** rl.debug transcript: one line per chosen action (RLGAME block) */
    public final StringBuilder actionLog = new StringBuilder();

    /** C2a shaping: emit Φ(s) = GameStateEvaluator2 score per consult */
    private static final boolean PHI_ENABLED = Boolean.getBoolean("rl.phi");

    /** C5 league: -Drl.noYields=true disables the hand-crafted yield
     *  predicates entirely - the policy sees EVERY k>0 window. The
     *  yields were a Phase 2 throughput optimization that encodes
     *  strategic priors (they hid the flash windows pre-v3); a clean
     *  self-play run carries no such rules. */
    private static final boolean NO_YIELDS = Boolean.getBoolean("rl.noYields");

    private float phi(Game game) {
        if (!PHI_ENABLED) {
            return 0f;
        }
        try {
            return mage.player.ai.score.GameStateEvaluator2
                    .evaluate(playerId, game).getTotalScore();
        } catch (Exception e) {
            return 0f;
        }
    }

    private enum YieldKind { NONE, REACTIVE, MY_NEXT_MAIN }

    private YieldKind yield = YieldKind.NONE;

    public RLPlayer(String name) {
        super(name, RangeOfInfluence.ONE);
    }

    public void resetPerEpisode() {
        budgetExhausted = false;
        yield = YieldKind.NONE;
        shuffleCount = 0;
        windows = consults = yieldSkipped = autoPassK0 = 0;
        actions = failedActivations = 0;
        blocksDeclared = blockOpportunities = 0;
        blockCombats = blockCombatsOptimal = blockScoreGap = blockTruncated = 0;
    }

    private UUID opponentId(Game game) {
        for (UUID opp : game.getOpponents(playerId)) {
            return opp;
        }
        return playerId;
    }

    private void countFallback(String name) {
        fallbackCalls.merge(name, 1, Integer::sum);
    }

    // -------------------------------------------------------- determinism

    @Override
    public void shuffleLibrary(Ability source, Game game) {
        List<Card> cards = new ArrayList<>(getLibrary().getCards(game));
        if (Boolean.getBoolean("rl.debug")) {
            System.out.println("RLDBG|shuffle libSize=" + getLibrary().size()
                    + " resolved=" + cards.size());
        }
        cards.sort(Comparator.comparing(MageObject::getName));
        getLibrary().clear();
        for (Card c : cards) {
            getLibrary().putOnTop(c, game);
        }
        RandomUtil.setSeed(benchSeed
                + 1000003L * getName().hashCode() + shuffleCount++);
        super.shuffleLibrary(source, game);
    }

    // ---------------------------------------------- C3 shadow teacher

    /**
     * True-DAgger logging (rl agent + rl.imitateOut): at every consulted
     * priority window, write the D1 teacher's label for THIS
     * (student-visited) state while the STUDENT still chooses the
     * action. Labels: searchBest when it fires; the static D0 policy
     * (HeuristicPlayer.choosePolicyActionStatic) on delegated/pass
     * windows - the complete D1 policy. Search sims cannot perturb the
     * main game: the stream is re-keyed after every query. Priority
     * windows only (combat/target labels come from teacher datasets).
     */
    public java.io.PrintWriter shadowOut;
    public long shadowExamples = 0;
    private long shadowCounter = 0;

    private void shadowLabel(Game game, List<ActivatedAbility> playable,
                             float[] state, float[][] cands) {
        long[] nodes = {0};
        Ability tBest = org.mage.test.benchmark.SearchPlayer.searchBest(
                game, playerId,
                Integer.getInteger("rl.shadowPlies", 1),
                Integer.getInteger("rl.shadowBreadth", 8),
                benchSeed * 5_555_557L + shadowCounter, nodes);
        shadowCounter++;
        RandomUtil.setSeed(benchSeed * 5_555_557L + shadowCounter);
        Ability chosen = tBest;
        if (tBest == null
                || tBest instanceof mage.abilities.common.PassAbility) {
            chosen = org.mage.test.benchmark.HeuristicPlayer
                    .choosePolicyActionStatic(game, playerId, playable);
        }
        int label = 0;
        if (chosen != null
                && !(chosen instanceof mage.abilities.common.PassAbility)) {
            String key = chosen.getSourceId() + "|" + chosen.getRule();
            for (int i = 0; i < playable.size(); i++) {
                ActivatedAbility a = playable.get(i);
                if ((a.getSourceId() + "|" + a.getRule()).equals(key)) {
                    label = i + 1;
                    break;
                }
            }
        }
        shadowExamples++;
        TeacherLogPlayer.writeExample(shadowOut, "prio", state, cands, label);
    }

    // ------------------------------------------------------------- yields

    private boolean holdsInstant(Game game) {
        // v3 (matches HeuristicPlayer): instants, flash permanents, and
        // ninjutsu all keep the REACTIVE yield alive - otherwise the
        // windows where flash lines live are auto-passed unseen
        for (Card c : getHand().getCards(game)) {
            if (c.isInstant(game)
                    || c.getAbilities(game).containsClass(
                            mage.abilities.keyword.FlashAbility.class)
                    || c.getAbilities(game).containsClass(
                            mage.abilities.keyword.NinjutsuAbility.class)) {
                return true;
            }
        }
        return false;
    }

    private boolean yieldHolds(Game game) {
        PhaseStep st = game.getTurnStepType();
        boolean myTurn = playerId.equals(game.getActivePlayerId());
        boolean ownMain = myTurn && (st == PhaseStep.PRECOMBAT_MAIN
                || st == PhaseStep.POSTCOMBAT_MAIN);
        switch (yield) {
            case REACTIVE:
                if (!game.getStack().isEmpty()
                        || (st == PhaseStep.END_TURN && !myTurn)
                        || st == PhaseStep.DECLARE_BLOCKERS
                        || ownMain) {
                    return false;
                }
                return true;
            case MY_NEXT_MAIN:
                return !ownMain;
            default:
                return false;
        }
    }

    private void setYieldAfterPass(Game game) {
        if (NO_YIELDS) {
            return;
        }
        if (game.getStack().isEmpty()) {
            yield = holdsInstant(game) ? YieldKind.REACTIVE : YieldKind.MY_NEXT_MAIN;
        }
    }

    // ------------------------------------------------------------ priority

    @Override
    public boolean priority(Game game) {
        windows++;
        if (yield != YieldKind.NONE && yieldHolds(game)) {
            yieldSkipped++;
            pass(game);
            return false;
        }
        yield = YieldKind.NONE;

        boolean myTurn = playerId.equals(game.getActivePlayerId());
        boolean sorceryWindow = myTurn && game.getStack().isEmpty()
                && (game.getTurnStepType() == PhaseStep.PRECOMBAT_MAIN
                || game.getTurnStepType() == PhaseStep.POSTCOMBAT_MAIN);

        List<ActivatedAbility> playable = new ArrayList<>(getPlayable(game, true));
        // phantom land drop: getPlayable lists it at illegal steps
        playable.removeIf(a -> a instanceof PlayLandAbility && !sorceryWindow);
        if (playable.isEmpty()) {
            autoPassK0++;
            pass(game);
            setYieldAfterPass(game);
            return false;
        }
        playable.sort(Comparator.comparing(a -> {
            MageObject o = game.getObject(a.getSourceId());
            return (o == null ? "?" : o.getName()) + "|" + a.getRule();
        }));

        float[] state = StateEncoder.encodeState(game, playerId, opponentId(game));
        float[][] cands = new float[playable.size() + 1][];
        cands[0] = StateEncoder.blank(StateEncoder.T_PASS);
        for (int i = 0; i < playable.size(); i++) {
            ActivatedAbility a = playable.get(i);
            // v3: resolve the source card for EVERY candidate (ninjutsu,
            // creature-land activations...), not just casts - non-spell
            // candidates used to encode featureless
            Card card = game.getCard(a.getSourceId());
            cands[i + 1] = StateEncoder.forCard(
                    a instanceof PlayLandAbility
                            ? StateEncoder.T_LAND : StateEncoder.T_SPELL,
                    card, game);
        }
        if (consults >= consultBudget) {
            budgetExhausted = true;
            pass(game);
            setYieldAfterPass(game);
            return false;
        }
        if (shadowOut != null) {
            shadowLabel(game, playable, state, cands);
        }
        consults++;
        int pick = policy.choose(state, cands, phi(game));
        if (pick <= 0 || pick > playable.size()) {
            pass(game);
            setYieldAfterPass(game);
            return false;
        }
        ActivatedAbility chosen =
                (ActivatedAbility) playable.get(pick - 1).copy();
        boolean acted = this.activateAbility(chosen, game);
        if (acted) {
            actions++;
            Card chosenCard = game.getCard(chosen.getSourceId());
            if (chosenCard != null && !chosenCard.isInstant(game)
                    && org.mage.test.benchmark.HeuristicPlayer.holdable(game, chosenCard)) {
                flashThreatCasts++;
                if (!playerId.equals(game.getActivePlayerId())) {
                    flashThreatCastsOppTurn++;
                }
            }
            if (Boolean.getBoolean("rl.debug")) {
                // Log the CARD NAME, not just the rule text. On the
                // curriculum rung-0 decks every creature is vanilla, so
                // getRule() is the empty string and a whole game's
                // transcript came out as blank lines and mana taps -
                // technically complete, unreadable, and easy to mistake
                // for "the agent never cast anything".
                String what = chosenCard != null ? chosenCard.getName() : "";
                String rule = chosen.getRule();
                if (rule != null && !rule.trim().isEmpty()) {
                    what = what.isEmpty() ? rule : what + " (" + rule + ")";
                }
                if (what.isEmpty()) {
                    what = String.valueOf(chosen.getSourceObject(game));
                }
                actionLog.append("t").append(game.getTurnNum()).append('|')
                        .append(what).append('\n');
            }
        } else {
            failedActivations++;
            pass(game);
            setYieldAfterPass(game);
        }
        return acted;
    }

    // ------------------------------------------------------------ targets

    private boolean policyPickTargets(Target target, Ability source, Game game) {
        UUID opp = opponentId(game);
        int guard = 0;
        while (target.getTargets().size() < target.getMinNumberOfTargets()
                && guard++ < 16) {
            List<UUID> possible = new ArrayList<>(
                    target.possibleTargets(playerId, source, game));
            possible.removeAll(target.getTargets());
            possible.removeIf(id -> !target.canTarget(playerId, id, source, game));
            if (possible.isEmpty()) {
                return !target.getTargets().isEmpty();
            }
            possible.sort(Comparator.comparing(id -> canonicalName(id, game)));
            float[] state = StateEncoder.encodeState(game, playerId, opp);
            float[][] cands = new float[possible.size()][];
            for (int i = 0; i < possible.size(); i++) {
                UUID id = possible.get(i);
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
            consults++;
            int pick = policy.choose(state, cands, phi(game));
            pick = Math.max(0, Math.min(pick, possible.size() - 1));
            target.addTarget(possible.get(pick), source, game);
        }
        return true;
    }

    private String canonicalName(UUID id, Game game) {
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

    @Override
    public boolean chooseTarget(Outcome outcome, Target target, Ability source, Game game) {
        return policyPickTargets(target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source, Game game) {
        return policyPickTargets(target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source, Game game,
                          Map<String, java.io.Serializable> options) {
        return policyPickTargets(target, source, game);
    }

    private boolean policyPickCards(Cards cards, TargetCard target,
                                    Ability source, Game game) {
        UUID opp = opponentId(game);
        int guard = 0;
        while (target.getTargets().size() < target.getMinNumberOfTargets()
                && guard++ < 16) {
            List<Card> possible = new ArrayList<>(cards.getCards(game));
            possible.removeIf(c -> target.getTargets().contains(c.getId())
                    || !target.canTarget(playerId, c.getId(), source, game));
            if (possible.isEmpty()) {
                return !target.getTargets().isEmpty();
            }
            possible.sort(Comparator.comparing(MageObject::getName));
            float[] state = StateEncoder.encodeState(game, playerId, opp);
            float[][] cands = new float[possible.size()][];
            for (int i = 0; i < possible.size(); i++) {
                cands[i] = StateEncoder.forCard(StateEncoder.T_TARGET,
                        possible.get(i), game);
            }
            consults++;
            int pick = policy.choose(state, cands, phi(game));
            pick = Math.max(0, Math.min(pick, possible.size() - 1));
            target.addTarget(possible.get(pick).getId(), source, game);
        }
        return true;
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Cards cards, TargetCard target,
                                Ability source, Game game) {
        return policyPickCards(cards, target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Cards cards, TargetCard target,
                          Ability source, Game game) {
        return policyPickCards(cards, target, source, game);
    }

    // ------------------------------------------------------------- combat

    /** -Drl.debug transcript line. */
    private void log(Game game, String s) {
        if (Boolean.getBoolean("rl.debug")) {
            actionLog.append("t").append(game.getTurnNum()).append('|')
                    .append(s).append('\n');
        }
    }

    /** "Name 2/3" - the transcript is unreadable without the body. */
    private static String pt(Permanent p, Game game) {
        return p.getName() + " " + p.getPower().getValue()
                + "/" + p.getToughness().getValue();
    }

    private String boardLine(Game game, String what) {
        UUID opp = opponentId(game);
        int mine = 0, theirs = 0;
        for (Permanent p : game.getBattlefield().getAllActivePermanents()) {
            if (!p.isCreature(game)) {
                continue;
            }
            if (playerId.equals(p.getControllerId())) {
                mine++;
            } else if (opp != null && opp.equals(p.getControllerId())) {
                theirs++;
            }
        }
        Player me = game.getPlayer(playerId);
        Player they = opp == null ? null : game.getPlayer(opp);
        return String.format("== %s: life %d-%d, creatures %d-%d", what,
                me == null ? 0 : me.getLife(), they == null ? 0 : they.getLife(),
                mine, theirs);
    }

    @Override
    public void selectAttackers(Game game, UUID attackingPlayerId) {
        yield = YieldKind.NONE;
        UUID defender = opponentId(game);
        List<Permanent> avail = new ArrayList<>(getAvailableAttackers(game));
        avail.sort(Comparator.comparing(MageObject::getName));
        // Combat was invisible in the transcript: attacks and blocks go
        // through these callbacks, not through the activated-ability path
        // the action log was recording, so a "sample game" showed only
        // lands and spells. On a rung-0 deck combat IS the game.
        if (!avail.isEmpty()) {
            log(game, boardLine(game, "my combat"));
        }
        for (Permanent creature : avail) {
            float[] state = StateEncoder.encodeState(game, playerId, defender);
            float[][] cands = {
                StateEncoder.blank(StateEncoder.T_PASS),
                StateEncoder.forCombat(StateEncoder.T_ATTACK, creature, game)};
            consults++;
            if (policy.choose(state, cands, phi(game)) == 1) {
                this.declareAttacker(creature.getId(), defender, game, false);
                actions++;
                log(game, "  ATTACK  " + pt(creature, game));
            } else {
                log(game, "  hold    " + pt(creature, game));
            }
        }
    }

    @Override
    public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
        yield = YieldKind.NONE;
        List<CombatGroup> groups = game.getCombat().getGroups();
        List<Permanent> attackers = new ArrayList<>();
        for (CombatGroup g : groups) {
            for (UUID atkId : g.getAttackers()) {
                Permanent atk = game.getPermanent(atkId);
                if (atk != null) {
                    attackers.add(atk);
                }
            }
        }
        if (attackers.isEmpty()) {
            return;
        }
        attackers.sort(Comparator.comparing(MageObject::getName));
        if (Boolean.getBoolean("rl.debug")) {
            StringBuilder atk = new StringBuilder();
            for (Permanent a : attackers) {
                atk.append(atk.length() == 0 ? "" : ", ").append(pt(a, game));
            }
            log(game, boardLine(game, "incoming"));
            log(game, "  attacked by " + atk);
        }
        List<Permanent> mine = new ArrayList<>();
        for (Permanent p : game.getBattlefield().getAllActivePermanents(playerId)) {
            if (p.isCreature(game) && !p.isTapped()) {
                mine.add(p);
            }
        }
        // Blocks are declared SIMULTANEOUSLY in real Magic; this loop is
        // an autoregressive decomposition of one joint decision, so the
        // iteration order is ours to choose - and sorting by NAME was a
        // bad choice. It makes "which creature decides first" a function
        // of card identity, which is exactly the coupling W0Twin exists
        // to detect: rename every card and the block order changes.
        // Sort by body instead, smallest toughness first (the natural
        // chump-block order), with name only as a determinism tiebreak.
        if (StateEncoder.ENCODER_V == 1) {
            mine.sort(Comparator.comparing(MageObject::getName));
        } else {
            mine.sort(Comparator
                    .comparingInt((Permanent p) -> p.getToughness().getValue())
                    .thenComparingInt(p -> p.getPower().getValue())
                    .thenComparing(MageObject::getName));
        }
        UUID opp = opponentId(game);

        // -Drl.solverBlocks=true replaces the POLICY's block decisions
        // with CombatMath's best assignment, leaving every other decision
        // to the net. This is a measurement, not a mode we would ship: it
        // bounds how much of the agent's win rate is being lost to
        // blocking at all. If a net blocks perfectly and barely improves,
        // no amount of block encoding is worth building.
        if (Boolean.getBoolean("rl.solverBlocks")) {
            List<CombatMath.Body> ab = CombatMath.bodies(attackers);
            List<CombatMath.Body> bb = CombatMath.bodies(mine);
            CombatMath.Best best = CombatMath.best(
                    ab, bb, getLife(), Long.getLong("rl.solverCap", 200000L));
            for (int i = 0; i < mine.size(); i++) {
                blockOpportunities++;
                if (best.assign[i] < 0) {
                    continue;
                }
                Permanent atk = attackers.get(best.assign[i]);
                if (!mine.get(i).canBlock(atk.getId(), game)) {
                    continue;
                }
                this.declareBlocker(defendingPlayerId, mine.get(i).getId(),
                        atk.getId(), game);
                actions++;
                blocksDeclared++;
                log(game, "  SOLVER  " + pt(mine.get(i), game) + "  <- "
                        + pt(atk, game));
            }
            if (!best.exhaustive) {
                countFallback("solverBlocksTruncated");
            }
            return;
        }

        for (Permanent blocker : mine) {
            List<Permanent> can = new ArrayList<>();
            for (Permanent atk : attackers) {
                if (blocker.canBlock(atk.getId(), game)) {
                    can.add(atk);
                }
            }
            if (can.isEmpty()) {
                continue;
            }
            float[] state = StateEncoder.encodeState(game, playerId, opp);
            float[][] cands = new float[can.size() + 1][];
            cands[0] = StateEncoder.blank(StateEncoder.T_PASS);
            for (int i = 0; i < can.size(); i++) {
                cands[i + 1] = StateEncoder.forBlock(can.get(i), blocker, game);
            }
            consults++;
            blockOpportunities++;
            int pick = policy.choose(state, cands, phi(game));
            if (pick > 0 && pick <= can.size()) {
                this.declareBlocker(defendingPlayerId, blocker.getId(),
                        can.get(pick - 1).getId(), game);
                actions++;
                blocksDeclared++;
                log(game, "  BLOCK   " + pt(blocker, game) + "  <- "
                        + pt(can.get(pick - 1), game));
            } else {
                // declining a block is a real decision and the project has
                // measured it before (7c: agents block ~100% when asked),
                // so it has to be visible, not an absent line
                log(game, "  decline " + pt(blocker, game)
                        + "  (could block " + can.size() + ")");
            }
        }
        auditBlocks(game, attackers, mine);
    }

    /**
     * Score the assignment the policy just made against the best one
     * CombatMath can find for the same position. Read AFTER the policy
     * has committed, so it never influences the decision.
     */
    private void auditBlocks(Game game, List<Permanent> attackers,
                             List<Permanent> mine) {
        if (!Boolean.getBoolean("rl.blockAudit") || attackers.isEmpty()) {
            return;
        }
        List<CombatMath.Body> ab = CombatMath.bodies(attackers);
        List<CombatMath.Body> bb = CombatMath.bodies(mine);
        int[] actual = new int[mine.size()];
        java.util.Arrays.fill(actual, -1);
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID atkId : g.getAttackers()) {
                int ai = -1;
                for (int i = 0; i < attackers.size(); i++) {
                    if (attackers.get(i).getId().equals(atkId)) {
                        ai = i;
                    }
                }
                if (ai < 0) {
                    continue;
                }
                for (UUID bId : g.getBlockers()) {
                    for (int i = 0; i < mine.size(); i++) {
                        if (mine.get(i).getId().equals(bId)) {
                            actual[i] = ai;
                        }
                    }
                }
            }
        }
        int total = 0;
        for (CombatMath.Body a : ab) {
            total += a.power;
        }
        CombatMath.Outcome got = CombatMath.resolve(ab, bb, actual, getLife());
        int gotScore = CombatMath.defenderScore(got, total);
        CombatMath.Best best = CombatMath.best(ab, bb, getLife(),
                Long.getLong("rl.solverCap", 200000L));
        blockCombats++;
        if (!best.exhaustive) {
            blockTruncated++;
        }
        if (gotScore >= best.score) {
            blockCombatsOptimal++;
        } else {
            blockScoreGap += (best.score - gotScore);
        }
    }

    // ------------------------------------ counted heuristic fallbacks

    @Override
    public int announceX(int min, int max, String message, Game game,
                         Ability source, boolean isManaPay) {
        countFallback("announceX");
        return super.announceX(min, max, message, game, source, isManaPay);
    }

    @Override
    public mage.abilities.Mode chooseMode(mage.abilities.Modes modes,
                                          Ability source, Game game) {
        countFallback("chooseMode");
        return super.chooseMode(modes, source, game);
    }

    @Override
    public boolean chooseUse(Outcome outcome, String message, Ability source, Game game) {
        countFallback("chooseUse");
        return super.chooseUse(outcome, message, source, game);
    }

    @Override
    public int getAmount(int min, int max, String message, Ability source, Game game) {
        countFallback("getAmount");
        return super.getAmount(min, max, message, source, game);
    }
}
