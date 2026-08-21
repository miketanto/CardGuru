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
    /** Combats the policy's own blocks made LETHAL when a survivable
     *  assignment existed. Counted separately because defenderScore uses
     *  a death sentinel of Integer.MIN_VALUE/2 - subtracting it into the
     *  score gap produced blockScoreGap=1073743876 on the first real
     *  battery, i.e. one avoidable death swamping every material misplay
     *  in the run. Fatal errors are a different KIND of mistake and get
     *  their own counter. */
    public long blockFatal = 0;
    /** -Drl.attackAudit: the attack-side twin of the block audit. There
     *  was NO instrument for attacks at all, so "the agent holds
     *  everything for twelve turns at 20-20" was an anecdote read off one
     *  replay rather than a number. Same discipline as auditBlocks: read
     *  AFTER the policy commits, positions with nothing to decide
     *  excluded, truncation counted separately.
     *
     *  READ THE BIAS BEFORE READING THE NUMBERS. The reference is
     *  CombatMath.bestAttack, which is one combat deep and prices at ZERO
     *  the fact that an attacking creature cannot block on the opponent's
     *  next turn. It therefore over-credits attacking, which is the same
     *  direction as any fix that makes the agent attack more. The CA
     *  counters below re-score the same decisions against a reference
     *  that charges for the swing back; where the two disagree, the
     *  disagreement is the result and neither number settles it. */
    public long attackCombats = 0;
    public long attackCombatsWithChoice = 0;
    public long attackOptimal = 0;
    public long attackOptimalWithChoice = 0;
    public long attackScoreGap = 0;
    /** Reference finds lethal and the policy does not. Its own category
     *  for the same reason blockFatal is: attackerScore's lethal sentinel
     *  is Integer.MAX_VALUE/2 and subtracting it into a score gap would
     *  swamp every material misplay in the run. */
    public long attackLethalMissed = 0;
    /** Direction of the error, so "attack-optimality went up" cannot hide
     *  an agent that has simply started attacking with everything: UNDER
     *  = sent fewer creatures than the reference, OVER = sent more. */
    public long attackUnder = 0;
    public long attackOver = 0;
    /** Subset enumeration hit rl.attackCap, and any inner defender reply
     *  hit rl.attackReplyCap. Different truncations, counted apart. */
    public long attackTruncated = 0;
    public long attackReplyTruncated = 0;
    /** Sensitivity arm: the same decisions scored against a reference
     *  that subtracts the crack-back (CombatMath.attackerScoreCA). */
    public long attackOptimalCA = 0;
    public long attackScoreGapCA = 0;
    /** Creatures the REFERENCE would have sent, over the same
     *  denominator as attacksDeclared. Without this, UNDER/OVER says the
     *  policy attacks more than the reference wants but not BY HOW MUCH,
     *  and "OVER 208" is unreadable next to an attack rate of .674 - the
     *  overshoot could be one creature per combat or five. The CA variant
     *  is carried too, since the two references disagree about exactly
     *  the quantity in question. */
    public long attackRefDeclared = 0;
    public long attackRefDeclaredCA = 0;
    /** BLACK BRANCH instrument (CURRICULUM-LADDER.md §5): the power of
     *  the creature the policy pointed removal at, and the power census
     *  of everything it could legally have pointed at instead.
     *
     *  Win rate is the weak instrument on that branch; this is the
     *  strong one. A policy doing threat assessment concentrates its
     *  kills on high power, a policy ignoring the board is uniform over
     *  the legal set, and the difference is a chi-square on FIXED
     *  weights - no second training run, which is the class of claim
     *  POOLED-ANALYSIS.md §6 found actually replicates. The ladder
     *  records this instrument as "not built yet"; this is it.
     *
     *  Indexed by power, clamped into 0..6 (6 = "6 or more"). Only
     *  creature targets are counted: a spell aimed at a player has no
     *  power and would dilute the census. */
    public final long[] targetChosenByPower = new long[7];
    public final long[] targetLegalByPower = new long[7];
    public long targetCreatureChoices = 0;
    /** THE TEMPO HYPOTHESIS, made measurable. A kill can be chosen for
     *  size (threat assessment) or for what the creature is DOING right
     *  now - attacking, blocking, or tapped and unable to block back.
     *  Those are different policies and the power census cannot tell
     *  them apart, so the same chosen-vs-legal treatment is applied to
     *  combat status. Same denominators as the power census. */
    public long targetChosenAttacking = 0, targetLegalAttacking = 0;
    public long targetChosenBlocking = 0, targetLegalBlocking = 0;
    public long targetChosenTapped = 0, targetLegalTapped = 0;
    /** Was the chosen creature the single biggest legal target? The
     *  power histogram answers "what did it kill"; this answers "did it
     *  take the largest thing available", which is the sharpest form of
     *  the threat-assessment question and needs no binning. */
    public long targetChosenWasMaxPower = 0, targetMaxPowerTies = 0;
    /** WHOSE creature was killed, and whether an enemy one was even
     *  available. Without this split the power census pools the agent's
     *  own creatures with the opponent's and cannot tell "chose badly"
     *  from "had no enemy target at all" - which is exactly the mistake
     *  the first read of it made. targetWindowsNoOpp is the number that
     *  matters: a removal cast resolved into a board with ZERO legal
     *  enemy targets is a CAST error, not a targeting error, and the
     *  cast candidate (forCard) carries nothing about target
     *  availability. */
    public long targetChosenOpp = 0, targetLegalOpp = 0;
    public long targetWindowsNoOpp = 0;
    /** TIMING instrument, for the instant-speed rungs (B1Fast, W4Inst).
     *  The whole point of a timing rung is that the same effect is
     *  printed at both speeds, so the measured difference is whether
     *  the policy learned to WAIT. A player that only acts at sorcery
     *  speed gains nothing from the swap and these counters say so
     *  directly, instead of leaving it to a win rate to imply.
     *
     *  own turn / opponent's turn / inside a combat step. The last is
     *  the sharpest: killing a creature mid-combat is the tempo play
     *  that sorcery-speed removal structurally cannot make. */
    public long instantCasts = 0;
    public long instantCastsOppTurn = 0;
    public long instantCastsInCombat = 0;

    /** Attacks declared / creatures that could legally have attacked.
     *  The RATE the whole task is about - the v4 replay holds 12 turns
     *  running - and the number that catches the fix overshooting. */
    public long attacksDeclared = 0;
    public long attackOpportunities = 0;
    /** Cost of the minimax search, so "measure the cost per combat" is a
     *  measurement. Nanos are the policy's search only; the audit runs a
     *  second one and is counted separately because it is an instrument,
     *  not part of playing. */
    public long attackSearchNanos = 0;
    public long attackSearchNodes = 0;
    public long attackAuditNanos = 0;
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

    /**
     * ONE consult, on whichever state path the encoder arm selects.
     *
     * v1-v5 send the flat 24/32-dim vector; v6 sends entity tokens plus
     * the relation edge list (ENCODER-V6-BUILD.md §4a/§4b). The
     * CANDIDATES are identical either way - v6 changes what the agent
     * sees, never what it can choose - so every call site passes the
     * same cands it always did and this is the only place that knows
     * which arm is running.
     */
    /** Which STATE encoding this seat emits. Defaults to the global
     *  arm; the opponent seat overrides it via rl.oppEncoderV so a
     *  v5 net and a v6 net can meet in one JVM. Only the state path
     *  is per-seat - the CANDIDATE features are identical for v5 and
     *  v6 by construction, which is the whole reason this is a
     *  three-line change and not a fork of StateEncoder. */
    public int stateV = StateEncoder.ENCODER_V;

    /** -Drl.trace: one line per CONSULT, whatever the decision is.
     *  rl.debug logs the actions the agent took; this logs every
     *  decision it was asked to make, including the ones where it
     *  passed - which are invisible otherwise and are most of them. */
    private static final boolean TRACE = Boolean.getBoolean("rl.trace");

    private int consult(Game game, UUID opp, float[][] cands, String site) {
        int pick = consultInner(game, opp, cands);
        if (TRACE) {
            actionLog.append("t").append(game.getTurnNum())
                    .append("|  [trace] ").append(site)
                    .append(" step=").append(game.getTurnStepType())
                    .append(" k=").append(cands.length)
                    .append(" pick=").append(pick)
                    .append(pick == 0 && !"atkjoint".equals(site)
                            && !"blkjoint".equals(site) ? " (PASS)" : "")
                    .append('\n');
        }
        return pick;
    }

    private int consultInner(Game game, UUID opp, float[][] cands) {
        if (stateV >= 6) {
            return policy.choose(
                    StateEncoder.encodeEntityView(game, playerId, opp),
                    cands, phi(game));
        }
        return policy.choose(StateEncoder.encodeState(game, playerId, opp),
                cands, phi(game));
    }

    /** §5's target-by-power census. Counts the whole legal set as well
     *  as the pick, because "chose a 5-power creature" means nothing
     *  without "and could have chosen these". Windows with no creature
     *  in the legal set are skipped entirely rather than counted as a
     *  degenerate choice. */
    private void recordTargetChoice(Game game, List<UUID> possible, int pick) {
        int creatures = 0, maxPower = Integer.MIN_VALUE, atMax = 0;
        int oppLegal = 0;
        StringBuilder opts = new StringBuilder();
        for (UUID id : possible) {
            Permanent p = game.getPermanent(id);
            if (p == null || !p.isCreature(game)) {
                continue;
            }
            creatures++;
            int pw = p.getPower().getValue();
            targetLegalByPower[bucket(pw)]++;
            if (!p.getControllerId().equals(playerId)) {
                targetLegalOpp++;
                oppLegal++;
            }
            if (p.isAttacking()) {
                targetLegalAttacking++;
            }
            if (p.getBlocking() > 0) {
                targetLegalBlocking++;
            }
            if (p.isTapped()) {
                targetLegalTapped++;
            }
            if (pw > maxPower) {
                maxPower = pw;
                atMax = 1;
            } else if (pw == maxPower) {
                atMax++;
            }
            if (opts.length() > 0) {
                opts.append(", ");
            }
            opts.append(pt(p, game)).append(status(p));
        }
        if (creatures == 0) {
            return;                 // no creature was targetable; not a
        }                           // threat-assessment decision at all
        Permanent chosen = game.getPermanent(possible.get(pick));
        if (chosen == null || !chosen.isCreature(game)) {
            return;
        }
        int pw = chosen.getPower().getValue();
        targetChosenByPower[bucket(pw)]++;
        targetCreatureChoices++;
        if (oppLegal == 0) {
            targetWindowsNoOpp++;
        }
        if (!chosen.getControllerId().equals(playerId)) {
            targetChosenOpp++;
        }
        if (chosen.isAttacking()) {
            targetChosenAttacking++;
        }
        if (chosen.getBlocking() > 0) {
            targetChosenBlocking++;
        }
        if (chosen.isTapped()) {
            targetChosenTapped++;
        }
        if (pw == maxPower) {
            targetChosenWasMaxPower++;
            if (atMax > 1) {
                targetMaxPowerTies++;
            }
        }
        log(game, "  KILL    " + pt(chosen, game) + status(chosen)
                + (chosen.getControllerId().equals(playerId) ? " (MINE)" : "")
                + "   [of " + creatures + ", " + oppLegal + " enemy: "
                + opts + "]");
    }

    /** Compact combat status, so a transcript line says WHY a kill might
     *  have been chosen and not only how big it was. */
    private static String status(Permanent p) {
        StringBuilder b = new StringBuilder();
        if (p.isAttacking()) {
            b.append(" atk");
        }
        if (p.getBlocking() > 0) {
            b.append(" blk");
        }
        if (p.isTapped()) {
            b.append(" tap");
        }
        return b.toString();
    }

    private static int bucket(int power) {
        return Math.max(0, Math.min(6, power));
    }

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
        blockFatal = 0;
        attackCombats = attackCombatsWithChoice = attackOptimal = 0;
        attackOptimalWithChoice = attackScoreGap = attackLethalMissed = 0;
        attackUnder = attackOver = attackTruncated = attackReplyTruncated = 0;
        attackOptimalCA = attackScoreGapCA = 0;
        attacksDeclared = attackOpportunities = 0;
        attackRefDeclared = attackRefDeclaredCA = 0;
        attackSearchNanos = attackSearchNodes = attackAuditNanos = 0;
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

        // v6 does not read the flat state at all; only the shadow
        // teacher still logs it, so do not pay for it otherwise
        float[] state = (StateEncoder.ENCODER_V >= 6 && shadowOut == null)
                ? null
                : StateEncoder.encodeState(game, playerId, opponentId(game));
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
        int pick = consult(game, opponentId(game), cands, "prio");
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
            if (chosenCard != null && chosenCard.isInstant(game)) {
                instantCasts++;
                if (!playerId.equals(game.getActivePlayerId())) {
                    instantCastsOppTurn++;
                }
                PhaseStep st = game.getTurnStepType();
                if (st == PhaseStep.DECLARE_ATTACKERS
                        || st == PhaseStep.DECLARE_BLOCKERS
                        || st == PhaseStep.BEGIN_COMBAT
                        || st == PhaseStep.FIRST_COMBAT_DAMAGE
                        || st == PhaseStep.COMBAT_DAMAGE
                        || st == PhaseStep.END_COMBAT) {
                    instantCastsInCombat++;
                }
            }
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
            int pick = consult(game, opp, cands, "target");
            pick = Math.max(0, Math.min(pick, possible.size() - 1));
            recordTargetChoice(game, possible, pick);
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
            float[][] cands = new float[possible.size()][];
            for (int i = 0; i < possible.size(); i++) {
                cands[i] = StateEncoder.forCard(StateEncoder.T_TARGET,
                        possible.get(i), game);
            }
            consults++;
            int pick = consult(game, opp, cands, "targetCard");
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
        // v5: ONE joint decision over attack subsets. Below v5 the
        // original per-creature loop runs UNCHANGED, so a v4 checkpoint
        // measured through this method plays exactly the games it always
        // played and the audit reads the pre-fix policy.
        if (StateEncoder.ENCODER_V >= 5) {
            // Card identity must not decide who attacks first, the same
            // argument selectBlockers makes: rename every card in W0Twin
            // and a name sort changes the enumeration. Body order.
            avail.sort(Comparator
                    .comparingInt((Permanent p) -> p.getToughness().getValue())
                    .thenComparingInt(p -> p.getPower().getValue())
                    .thenComparing(MageObject::getName));
            jointAttacks(game, defender, avail);
            auditAttacks(game, defender, avail);
            return;
        }
        for (Permanent creature : avail) {
            float[][] cands = {
                StateEncoder.blank(StateEncoder.T_PASS),
                StateEncoder.forCombat(StateEncoder.T_ATTACK, creature, game)};
            consults++;
            attackOpportunities++;
            if (consult(game, defender, cands, "attack1") == 1) {
                this.declareAttacker(creature.getId(), defender, game, false);
                actions++;
                attacksDeclared++;
                log(game, "  ATTACK  " + pt(creature, game));
            } else {
                log(game, "  hold    " + pt(creature, game));
            }
        }
        auditAttacks(game, defender, avail);
    }

    /** The defender's potential blockers: their untapped creatures.
     *  Vanilla scope, exactly as CombatMath documents - no evasion, so
     *  "untapped creature" and "can block this" are the same set. */
    private List<Permanent> theirBlockers(Game game, UUID defender) {
        List<Permanent> out = new ArrayList<>();
        if (defender == null) {
            return out;
        }
        for (Permanent p : game.getBattlefield().getAllActivePermanents(defender)) {
            if (p.isCreature(game) && !p.isTapped()) {
                out.add(p);
            }
        }
        out.sort(Comparator
                .comparingInt((Permanent p) -> p.getToughness().getValue())
                .thenComparingInt(p -> p.getPower().getValue())
                .thenComparing(MageObject::getName));
        return out;
    }

    /** Creatures the choice actually ranges over. Above rl.attackMaxCreatures
     *  the 2^A enumeration is unaffordable, so the choice covers the
     *  BIGGEST bodies and the remainder is forced to hold. That
     *  truncation is hold-biased - the same direction as the bug this
     *  task exists to fix - so it is counted, and the counter is reported
     *  rather than assumed to be zero. */
    private List<Permanent> attackChoiceSet(List<Permanent> avail) {
        int maxA = Integer.getInteger("rl.attackMaxCreatures", 12);
        if (avail.size() <= maxA) {
            return avail;
        }
        countFallback("attackCreaturesCapped");
        List<Permanent> big = new ArrayList<>(avail);
        big.sort(Comparator.comparingInt(
                (Permanent p) -> -(p.getPower().getValue()
                        + p.getToughness().getValue())));
        return new ArrayList<>(big.subList(0, maxA));
    }

    /**
     * Enumerate attack subsets, value each by what a BEST-REPLYING
     * DEFENDER does to it, and let the policy pick one.
     *
     * The shape is jointBlocks', and the difference is the whole reason
     * this took a design decision rather than a copy: a block assignment
     * resolves deterministically, an attack subset does not resolve at
     * all until the defender answers. The answer modelled here is minimax
     * one ply (CombatMath.bestAttack); its cost and its three known
     * limitations are documented there, and the cost is measured into
     * attackSearchNanos rather than assumed affordable.
     */
    private void jointAttacks(Game game, UUID defender, List<Permanent> avail) {
        if (avail.isEmpty()) {
            return;
        }
        long t0 = System.nanoTime();
        List<Permanent> pick = attackChoiceSet(avail);
        List<Permanent> theirs = theirBlockers(game, defender);
        Player op = defender == null ? null : game.getPlayer(defender);
        int oppLife = op == null ? 20 : op.getLife();
        List<CombatMath.Body> mb = CombatMath.bodies(pick);
        List<CombatMath.Body> tb = CombatMath.bodies(theirs);
        CombatMath.BestAttack search = CombatMath.bestAttack(
                mb, tb, getLife(), oppLife,
                Long.getLong("rl.attackCap", 4096L),
                Long.getLong("rl.attackReplyCap", 200000L));
        attackSearchNodes += search.considered;
        if (!search.exhaustive) {
            countFallback("attackCapped");
        }
        if (!search.replyExhaustive) {
            countFallback("attackReplyCapped");
        }

        // PARETO FILTER, four objectives. Blocks use three; attacks need
        // RETAINED POWER as a fourth, and leaving it out would be a
        // policy decision disguised as a filter: under a one-combat
        // outcome, holding a creature back is dominated by attacking with
        // it almost always, so a three-objective filter would delete the
        // option to hold from the candidate list entirely and the agent
        // would alpha-strike by construction. The filter must not decide
        // the question the fix is supposed to let the policy decide.
        //
        // RETAINED BODIES is a fifth objective for the same reason, one
        // level down: blocking capacity is bodies, not power. Keeping one
        // 3/3 beats keeping two 1/1s on power and loses on blockers, and
        // a filter carrying only power would drop the two-body option as
        // dominated. Each extra objective weakens the filter, which costs
        // candidate slots and never costs correctness.
        List<CombatMath.AttackOption> kept = new ArrayList<>();
        java.util.Set<String> outcomes = new java.util.LinkedHashSet<>();
        int maxCands = Integer.getInteger("rl.attackMaxCands", 64);
        for (CombatMath.AttackOption o1 : search.options) {
            boolean dominated = false;
            for (CombatMath.AttackOption o2 : search.options) {
                if (o1 == o2) {
                    continue;
                }
                if (o2.outcome.damageTaken >= o1.outcome.damageTaken
                        && o2.outcome.blockerValueLost >= o1.outcome.blockerValueLost
                        && o2.outcome.attackerValueKilled <= o1.outcome.attackerValueKilled
                        && o2.retainedPower >= o1.retainedPower
                        && o2.retainedBodies >= o1.retainedBodies
                        && (o2.outcome.damageTaken > o1.outcome.damageTaken
                            || o2.outcome.blockerValueLost > o1.outcome.blockerValueLost
                            || o2.outcome.attackerValueKilled < o1.outcome.attackerValueKilled
                            || o2.retainedPower > o1.retainedPower
                            || o2.retainedBodies > o1.retainedBodies)) {
                    dominated = true;
                    break;
                }
            }
            if (dominated) {
                continue;
            }
            String key = o1.outcome.damageTaken + "/" + o1.outcome.blockersLost
                    + "/" + o1.outcome.blockerValueLost + "/"
                    + o1.outcome.attackersKilled + "/"
                    + o1.outcome.attackerValueKilled + "/" + o1.attackersUsed
                    + "/" + o1.retainedPower + "/" + o1.crackBack;
            if (!outcomes.add(key)) {
                continue;
            }
            kept.add(o1);
            if (kept.size() >= maxCands) {
                countFallback("attackCandsCapped");
                break;
            }
        }
        if (kept.isEmpty()) {                 // cannot happen; not a crash
            kept.add(search.options.get(0));
        }
        float[][] cands = new float[kept.size()][];
        for (int i = 0; i < kept.size(); i++) {
            cands[i] = StateEncoder.forAttackSet(kept.get(i), getLife(), oppLife);
        }
        attackSearchNanos += System.nanoTime() - t0;
        consults++;
        attackOpportunities += avail.size();
        log(game, String.format("  [atkjoint] %d avail, %d defenders, "
                + "%d distinct subsets, %d after Pareto, %.1fms",
                avail.size(), theirs.size(), search.options.size(),
                kept.size(), (System.nanoTime() - t0) / 1e6));
        int idx = consult(game, defender, cands, "atkjoint");
        if (idx < 0 || idx >= kept.size()) {
            return;
        }
        CombatMath.AttackOption chosen = kept.get(idx);
        for (int i = 0; i < pick.size(); i++) {
            Permanent c = pick.get(i);
            if (!chosen.attack[i]) {
                log(game, "  hold    " + pt(c, game));
                continue;
            }
            this.declareAttacker(c.getId(), defender, game, false);
            actions++;
            attacksDeclared++;
            log(game, "  ATTACK  " + pt(c, game));
        }
        for (Permanent c : avail) {
            if (!pick.contains(c)) {
                log(game, "  hold    " + pt(c, game) + "  (past cap)");
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

        // v4: ONE joint decision over complete assignments.
        if (StateEncoder.ENCODER_V >= 4) {
            jointBlocks(game, defendingPlayerId, attackers, mine);
            auditBlocks(game, attackers, mine);
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
            float[][] cands = new float[can.size() + 1][];
            cands[0] = StateEncoder.blank(StateEncoder.T_PASS);
            for (int i = 0; i < can.size(); i++) {
                cands[i + 1] = StateEncoder.forBlock(can.get(i), blocker, game);
            }
            consults++;
            blockOpportunities++;
            int pick = consult(game, opp, cands, "block1");
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
     * Enumerate complete block assignments, describe each by its
     * SIMULATED OUTCOME, and let the policy pick one.
     *
     * Two things make this tractable. Assignments are DEDUPED BY
     * OUTCOME - interchangeable blockers produce identical consequences,
     * and the policy only ever sees consequences, so distinct outcomes
     * are the real action space and the collapse is large. And the raw
     * space is capped, with anything past the cap dropped and counted
     * rather than silently truncated.
     */
    private void jointBlocks(Game game, UUID defendingPlayerId,
                             List<Permanent> attackers, List<Permanent> mine) {
        int A = attackers.size();
        int B = mine.size();
        List<CombatMath.Body> ab = CombatMath.bodies(attackers);
        List<CombatMath.Body> bb = CombatMath.bodies(mine);
        long cap = Long.getLong("rl.jointCap", 20000L);
        long space = 1;
        for (int i = 0; i < B; i++) {
            space *= (A + 1);
            if (space > cap) {
                space = cap;
                countFallback("jointCapped");
                break;
            }
        }
        Map<String, int[]> byOutcome = new java.util.LinkedHashMap<>();
        Map<String, float[]> feats = new java.util.LinkedHashMap<>();
        int[] assign = new int[B];
        for (long code = 0; code < space; code++) {
            long c = code;
            int used = 0;
            for (int b = 0; b < B; b++) {
                assign[b] = (int) (c % (A + 1)) - 1;
                c /= (A + 1);
                if (assign[b] >= 0) {
                    used++;
                }
            }
            CombatMath.Outcome o = CombatMath.resolve(ab, bb, assign, getLife());
            String key = o.damageTaken + "/" + o.attackersKilled + "/"
                    + o.attackerValueKilled + "/" + o.blockersLost + "/"
                    + o.blockerValueLost + "/" + used;
            if (byOutcome.containsKey(key)) {
                continue;
            }
            byOutcome.put(key, assign.clone());
            feats.put(key, StateEncoder.forAssignment(o, used, getLife()));
        }
        // PARETO FILTER. An assignment that takes MORE damage, kills LESS
        // attacker value and loses MORE blocker value than another is
        // never preferable under any value function, so it can be dropped
        // without encoding a preference. This is what keeps the candidate
        // list inside the policy server's buffer: raw enumeration on a
        // real board produced 46 distinct outcomes against a 40-slot
        // buffer and crashed the server mid-run.
        List<String> keys = new ArrayList<>(byOutcome.keySet());
        List<int[]> options = new ArrayList<>();
        List<float[]> kept = new ArrayList<>();
        int maxCands = Integer.getInteger("rl.jointMaxCands", 48);
        for (String k1 : keys) {
            int[] a1 = byOutcome.get(k1);
            CombatMath.Outcome o1 = CombatMath.resolve(ab, bb, a1, getLife());
            boolean dominated = false;
            for (String k2 : keys) {
                if (k1.equals(k2)) {
                    continue;
                }
                CombatMath.Outcome o2 =
                        CombatMath.resolve(ab, bb, byOutcome.get(k2), getLife());
                if (o2.damageTaken <= o1.damageTaken
                        && o2.attackerValueKilled >= o1.attackerValueKilled
                        && o2.blockerValueLost <= o1.blockerValueLost
                        && (o2.damageTaken < o1.damageTaken
                            || o2.attackerValueKilled > o1.attackerValueKilled
                            || o2.blockerValueLost < o1.blockerValueLost)) {
                    dominated = true;
                    break;
                }
            }
            if (!dominated) {
                options.add(a1);
                kept.add(feats.get(k1));
                if (options.size() >= maxCands) {
                    countFallback("jointCandsCapped");
                    break;
                }
            }
        }
        if (options.isEmpty()) {          // every option dominated: fall back
            options.add(byOutcome.values().iterator().next());
            kept.add(feats.values().iterator().next());
        }
        float[][] cands = kept.toArray(new float[0][]);
        consults++;
        blockOpportunities += B;
        log(game, String.format("  [joint] %d attackers, %d blockers, "
                + "%d distinct outcomes, %d after Pareto",
                A, B, byOutcome.size(), options.size()));
        int pick = consult(game, opponentId(game), cands, "blkjoint");
        if (pick < 0 || pick >= options.size()) {
            return;
        }
        int[] chosen = options.get(pick);
        for (int b = 0; b < B; b++) {
            if (chosen[b] < 0) {
                log(game, "  decline " + pt(mine.get(b), game));
                continue;
            }
            Permanent atk = attackers.get(chosen[b]);
            if (!mine.get(b).canBlock(atk.getId(), game)) {
                continue;
            }
            this.declareBlocker(defendingPlayerId, mine.get(b).getId(),
                    atk.getId(), game);
            actions++;
            blocksDeclared++;
            log(game, "  BLOCK   " + pt(mine.get(b), game) + "  <- "
                    + pt(atk, game));
        }
    }

    /** "Lion 2/2->Vanguard 2/1, Seeker 2/2->-- (score 7)" */
    private static String assignStr(List<CombatMath.Body> ab,
                                    List<CombatMath.Body> bb,
                                    int[] assign, int score) {
        StringBuilder sb = new StringBuilder();
        for (int b = 0; b < bb.size(); b++) {
            if (sb.length() > 0) {
                sb.append(", ");
            }
            CombatMath.Body me = bb.get(b);
            sb.append(me.name).append(' ').append(me.power).append('/')
                    .append(me.toughness).append("->");
            if (assign[b] < 0 || assign[b] >= ab.size()) {
                sb.append("--");
            } else {
                CombatMath.Body a = ab.get(assign[b]);
                sb.append(a.name).append(' ').append(a.power).append('/')
                        .append(a.toughness);
            }
        }
        // the death sentinel is Integer.MIN_VALUE/2; printing it raw made
        // an earlier report read "gap 1073743876"
        sb.append(score <= Integer.MIN_VALUE / 4 ? " (LETHAL)"
                : " (score " + score + ")");
        return sb.toString();
    }

    /**
     * Score the assignment the policy just made against the best one
     * CombatMath can find for the same position. Read AFTER the policy
     * has committed, so it never influences the decision.
     */
    private void auditBlocks(Game game, List<Permanent> attackers,
                             List<Permanent> mine) {
        // mine.isEmpty() means there was NOTHING TO DECIDE - the empty
        // assignment is trivially optimal, and counting those inflated
        // the untrained net to 420/427 purely by having no creatures.
        if (!Boolean.getBoolean("rl.blockAudit")
                || attackers.isEmpty() || mine.isEmpty()) {
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
        boolean gotDies = got.defenderDies;
        boolean bestDies = best.outcome.defenderDies;
        // The audit already knows the reference assignment; without this
        // line a transcript shows WHAT was blocked but never whether it
        // was right, which is the only interesting question about a block.
        log(game, "  [audit] policy " + assignStr(ab, bb, actual, gotScore)
                + " | solver " + assignStr(ab, bb, best.assign, best.score)
                + (gotDies && !bestDies ? "  AVOIDABLE DEATH"
                   : gotScore >= best.score ? "  MATCH"
                   : "  GAP " + (best.score - gotScore))
                + (best.exhaustive ? "" : "  (solver truncated)"));
        if (gotDies && !bestDies) {
            blockFatal++;              // avoidable death: its own category
        } else if (gotScore >= best.score) {
            blockCombatsOptimal++;
        } else if (!gotDies && !bestDies) {
            blockScoreGap += (best.score - gotScore);
        }
    }

    /**
     * Score the attack the policy just declared against the best subset
     * CombatMath can find for the same position. Read AFTER the policy
     * has committed, so it never influences the decision.
     *
     * THIS INSTRUMENT DID NOT EXIST. auditBlocks has given
     * block-optimality since the encoder A/B; there was no equivalent for
     * attacks, so the only evidence that attacking was broken was a human
     * reading twelve consecutive `hold` lines out of one replay. Nothing
     * could say whether an attack was good, which means nothing could
     * have said whether a fix worked.
     *
     * WHAT IS EXCLUDED AND WHAT IS SPLIT OUT.
     *   - avail.isEmpty(): no creature could attack, so there was no
     *     decision. Counting those is the mistake that once inflated an
     *     untrained net to 98.4% block-optimality by scoring positions it
     *     had no creatures in.
     *   - attackCombatsWithChoice: combats where more than one distinct
     *     subset outcome existed. Where only one does, a MATCH belongs to
     *     the position, not the policy - the same caveat that makes
     *     blockOptimal/blockCombats an upper bound (12 outcomes collapsed
     *     to 1 at t22 of the v4 replay).
     *   - truncation is two counters, not one: the subset enumeration and
     *     the inner defender reply are different searches and either can
     *     be cut.
     *   - UNDER/OVER: the direction of the error. Without it, an agent
     *     that alpha-strikes every turn would post a high optimality
     *     against a reference that cannot see the cost of tapping out.
     */
    private void auditAttacks(Game game, UUID defender, List<Permanent> avail) {
        if (!Boolean.getBoolean("rl.attackAudit") || avail.isEmpty()) {
            return;
        }
        long t0 = System.nanoTime();
        List<Permanent> theirs = theirBlockers(game, defender);
        Player op = defender == null ? null : game.getPlayer(defender);
        int oppLife = op == null ? 20 : op.getLife();
        List<CombatMath.Body> mb = CombatMath.bodies(avail);
        List<CombatMath.Body> tb = CombatMath.bodies(theirs);

        boolean[] actual = new boolean[avail.size()];
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID atkId : g.getAttackers()) {
                for (int i = 0; i < avail.size(); i++) {
                    if (avail.get(i).getId().equals(atkId)) {
                        actual[i] = true;
                    }
                }
            }
        }
        long replyCap = Long.getLong("rl.attackReplyCap", 200000L);
        CombatMath.AttackOption got = CombatMath.evaluate(
                mb, actual, tb, getLife(), oppLife, replyCap);
        CombatMath.BestAttack ref = CombatMath.bestAttack(
                mb, tb, getLife(), oppLife,
                Long.getLong("rl.attackCap", 4096L), replyCap);
        CombatMath.AttackOption best = ref.best;
        CombatMath.AttackOption bestCA = ref.bestCA;

        attackCombats++;
        attackRefDeclared += best.attackersUsed;
        attackRefDeclaredCA += bestCA.attackersUsed;
        // "Was there anything to decide" has to be counted over distinct
        // OUTCOMES, not distinct subsets: two subsets that resolve
        // identically are one decision. This is the attack-side version
        // of the t22 caveat, where the Pareto filter left the v4 policy
        // one block candidate and the MATCH belonged to the filter.
        java.util.Set<String> distinct = new java.util.HashSet<>();
        for (CombatMath.AttackOption o : ref.options) {
            distinct.add(o.outcome.damageTaken + "/" + o.outcome.blockersLost
                    + "/" + o.outcome.blockerValueLost + "/"
                    + o.outcome.attackersKilled + "/"
                    + o.outcome.attackerValueKilled + "/" + o.attackersUsed
                    + "/" + o.retainedPower + "/" + o.crackBack);
        }
        boolean hasChoice = distinct.size() > 1;
        if (hasChoice) {
            attackCombatsWithChoice++;
        }
        if (!ref.exhaustive) {
            attackTruncated++;
        }
        if (!ref.replyExhaustive || !got.replyExhaustive) {
            attackReplyTruncated++;
        }

        String verdict;
        if (best.outcome.defenderDies && !got.outcome.defenderDies) {
            attackLethalMissed++;             // its own category, never a gap
            verdict = "  MISSED LETHAL";
        } else if (got.score >= best.score) {
            attackOptimal++;
            if (hasChoice) {
                attackOptimalWithChoice++;
            }
            verdict = "  MATCH";
        } else {
            // both scores are inside the normal band here: got < best and
            // best is not the lethal sentinel, so neither is a sentinel
            attackScoreGap += (best.score - got.score);
            verdict = "  GAP " + (best.score - got.score);
            if (got.attackersUsed < best.attackersUsed) {
                attackUnder++;
                verdict += " UNDER";
            } else if (got.attackersUsed > best.attackersUsed) {
                attackOver++;
                verdict += " OVER";
            }
        }
        // The sensitivity arm, scored on the SAME decision. Sentinels are
        // filtered out of the gap on both sides: a lethal attack and a
        // lethal crack-back are MAX/2 and MIN/2, and subtracting either
        // into a running total is how blockScoreGap once read 1073743876.
        if (got.scoreCA >= bestCA.scoreCA) {
            attackOptimalCA++;
        } else if (Math.abs((long) bestCA.scoreCA) < Integer.MAX_VALUE / 4
                && Math.abs((long) got.scoreCA) < Integer.MAX_VALUE / 4) {
            attackScoreGapCA += (bestCA.scoreCA - got.scoreCA);
        }
        attackAuditNanos += System.nanoTime() - t0;

        log(game, "  [atkaudit] policy " + CombatMath.subsetStr(mb, actual)
                + " (" + CombatMath.scoreStr(got.score) + ", dealt "
                + got.outcome.damageTaken + ", lost " + got.outcome.attackersKilled
                + ", killed " + got.outcome.blockersLost + ", back "
                + got.crackBack + ")"
                + " | ref " + CombatMath.subsetStr(mb, best.attack)
                + " (" + CombatMath.scoreStr(best.score) + ")"
                + verdict
                + (bestCA == best ? "" : "  | refCA "
                   + CombatMath.subsetStr(mb, bestCA.attack) + " ("
                   + CombatMath.scoreStr(bestCA.scoreCA) + " vs policy "
                   + CombatMath.scoreStr(got.scoreCA) + ")")
                + (ref.exhaustive ? "" : "  (subsets truncated)")
                + (ref.replyExhaustive ? "" : "  (replies truncated)")
                + (hasChoice ? "" : "  (no choice: 1 distinct outcome)"));
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
