package org.mage.test.benchmark;

import mage.MageObject;
import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.Mode;
import mage.abilities.Modes;
import mage.abilities.PlayLandAbility;
import mage.abilities.SpellAbility;
import mage.abilities.costs.mana.ManaCost;
import mage.cards.Card;
import mage.cards.Cards;
import mage.choices.Choice;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.permanent.Permanent;
import mage.game.stack.StackObject;
import mage.player.ai.ComputerPlayer;
import mage.target.Target;
import mage.util.RandomUtil;
import mage.target.TargetAmount;
import mage.target.TargetCard;

import java.io.Serializable;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * A deliberately simple, deterministic, search-free player used as a
 * MEASURING INSTRUMENT for decision density (Phase 2). It is a floor on
 * how often a competent player acts, not an agent.
 *
 * Policy (documented for RESULTS-PHASE2.md):
 *  - Sorcery speed (own turn, main phase, stack empty):
 *      1. play a land if one is playable
 *      2. cast the highest-mana-value CREATURE affordable
 *      3. else cast the highest-mana-value SORCERY affordable
 *      4. else pass
 *  - Instant speed:
 *      - if the stack is non-empty and its top object belongs to an
 *        opponent: cast a known COUNTERSPELL if playable
 *      - at an opponent's END_TURN step: cast the highest-MV playable
 *        INSTANT (removal/draw/tricks all fire here - crude but
 *        deterministic)
 *      - else pass
 *  - Combat: attack when no untapped defender both kills the attacker
 *    and survives it; block when the blocker kills the attacker and
 *    survives, or chump-block anything when unblocked damage is lethal.
 *  - All targets/modes/costs inside a chosen action resolve via
 *    ComputerPlayer's non-simulating heuristics (each callback counted).
 *
 * Yield support: when the policy passes at an EMPTY stack it emits a
 * yield predicate (REACTIVE if it holds a castable instant/counter,
 * else MY_NEXT_TURN). With yields enabled, subsequent windows are
 * auto-passed WITHOUT consulting the policy until the predicate fires.
 * Predicates (all engine-state evaluated):
 *   REACTIVE      = stack non-empty OR opponent END_TURN step
 *                   OR DECLARE_BLOCKERS step
 *   MY_NEXT_TURN  = active player is me on a later turn
 * Any action or combat callback clears the current yield.
 */
public class HeuristicPlayer extends ComputerPlayer {

    private static final java.util.Set<String> COUNTERSPELLS =
            new java.util.HashSet<>(java.util.Arrays.asList(
                    "Counterspell", "Cancel", "Essence Scatter", "Mana Leak"));

    public boolean yieldsEnabled = false;

    /**
     * Per-player shuffle seeding. XMage shuffles every library from the
     * single global RandomUtil stream, in player-map iteration order -
     * and player UUIDs are random per game, so WHICH player's shuffle
     * consumes WHICH slice of the stream varies between game instances
     * even under RandomUtil.setSeed. Re-seeding at each shuffle from
     * (benchSeed, player name, shuffle index) makes deck order a pure
     * function of the seed, independent of iteration order.
     */
    public long benchSeed = 0;
    private int shuffleCount = 0;

    private enum YieldKind { NONE, REACTIVE, MY_NEXT_TURN }

    private YieldKind yield = YieldKind.NONE;
    private int yieldSetOnTurn = 0;

    /** callback counting for the CURRENT action (B7) */
    private boolean inAction = false;
    private int callbackCount = 0;

    /** action log for the equivalence check (B6) */
    public final StringBuilder actionLog = new StringBuilder();

    public HeuristicPlayer(String name) {
        super(name, RangeOfInfluence.ONE);
    }

    public void resetPerGame() {
        yield = YieldKind.NONE;
        yieldSetOnTurn = 0;
        inAction = false;
        callbackCount = 0;
        shuffleCount = 0;
        actionLog.setLength(0);
    }

    @Override
    public void shuffleLibrary(mage.abilities.Ability source, Game game) {
        // canonicalize order first: Deck stores cards in UUID-keyed sets,
        // so the PRE-shuffle library order differs per game instance even
        // for identical decklists; sort by name, then seeded shuffle =>
        // deck order is a pure function of (seed, player, shuffle index)
        List<Card> cards = new java.util.ArrayList<>(getLibrary().getCards(game));
        cards.sort(java.util.Comparator.comparing(MageObject::getName));
        getLibrary().clear();
        for (Card c : cards) {
            getLibrary().putOnTop(c, game);
        }
        RandomUtil.setSeed(benchSeed
                + 1000003L * getName().hashCode() + shuffleCount++);
        super.shuffleLibrary(source, game);
    }

    // ------------------------------------------------------------ yields

    private boolean yieldHolds(Game game) {
        switch (yield) {
            case REACTIVE:
                if (!game.getStack().isEmpty()) {
                    return false;
                }
                if (game.getTurnStepType() == PhaseStep.END_TURN
                        && !game.getActivePlayerId().equals(playerId)) {
                    return false;
                }
                if (game.getTurnStepType() == PhaseStep.DECLARE_BLOCKERS) {
                    return false;
                }
                // never sleep through our own main phases: sorcery-speed
                // plays live there
                if (game.getActivePlayerId().equals(playerId)
                        && (game.getTurnStepType() == PhaseStep.PRECOMBAT_MAIN
                        || game.getTurnStepType() == PhaseStep.POSTCOMBAT_MAIN)) {
                    return false;
                }
                return true;
            case MY_NEXT_TURN:
                // semantics: "wake at my next MAIN phase" - a yield set
                // during my own upkeep must not sleep through this turn's
                // main (equivalence bug found by the B6 replay check)
                return !(game.getActivePlayerId().equals(playerId)
                        && (game.getTurnStepType() == PhaseStep.PRECOMBAT_MAIN
                        || game.getTurnStepType() == PhaseStep.POSTCOMBAT_MAIN));
            default:
                return false;
        }
    }

    // ------------------------------------------------------------ policy

    @Override
    public boolean priority(Game game) {
        if (yieldsEnabled && yield != YieldKind.NONE && yieldHolds(game)) {
            P2Stats.recordYieldSkip();
            pass(game);
            return false;
        }
        yield = YieldKind.NONE;

        List<ActivatedAbility> playable = getPlayable(game, true);
        int k = playable.size();
        String step = String.valueOf(game.getTurnStepType());

        if (Boolean.getBoolean("bench.trace")
                && game.getTurnStepType() == PhaseStep.UPKEEP
                && game.getActivePlayerId().equals(playerId)) {
            java.util.List<String> h = new java.util.ArrayList<>();
            for (Card c : getHand().getCards(game)) {
                h.add(c.getName());
            }
            h.sort(String::compareTo);
            actionLog.append("T").append(game.getTurnNum())
                    .append("hand=").append(h).append(';');
        }

        if (Boolean.getBoolean("bench.trace")
                && game.getTurnStepType() == PhaseStep.END_TURN) {
            StringBuilder pl = new StringBuilder();
            for (ActivatedAbility a : playable) {
                MageObject o = game.getObject(a.getSourceId());
                pl.append(o == null ? "?" : o.getName()).append(',');
            }
            actionLog.append("W").append(game.getTurnNum())
                    .append("ET:k=").append(k)
                    .append(":stack=").append(game.getStack().size())
                    .append(":pl=").append(pl).append(';');
        }
        ActivatedAbility chosen = choosePolicyAction(game, playable);
        boolean acted = false;
        if (chosen != null) {
            inAction = true;
            callbackCount = 0;
            acted = this.activateAbility((ActivatedAbility) chosen.copy(), game);
            inAction = false;
            if (acted) {
                P2Stats.recordActionCallbacks(callbackCount);
                MageObject obj = game.getObject(chosen.getSourceId());
                actionLog.append(game.getTurnNum()).append(':').append(step)
                        .append(':').append(obj == null ? "?" : obj.getName())
                        .append(';');
            }
        }
        P2Stats.recordWindow(k, acted, step);
        if (!acted) {
            pass(game);
            if (game.getStack().isEmpty()) {
                yield = holdsReactiveCard(game, playable)
                        ? YieldKind.REACTIVE : YieldKind.MY_NEXT_TURN;
                yieldSetOnTurn = game.getTurnNum();
            }
        }
        return acted;
    }

    private boolean holdsReactiveCard(Game game, List<ActivatedAbility> playable) {
        // holding any instant-speed card (castable now or later) keeps us
        // reactive; approximate by scanning hand for instants/counters
        for (Card c : getHand().getCards(game)) {
            if (c.isInstant(game)) {
                return true;
            }
        }
        return false;
    }

    private ActivatedAbility choosePolicyAction(Game game, List<ActivatedAbility> playable) {
        if (playable.isEmpty()) {
            return null;
        }
        boolean myTurn = game.getActivePlayerId().equals(playerId);
        boolean sorcerySpeed = myTurn && game.getStack().isEmpty()
                && (game.getTurnStepType() == PhaseStep.PRECOMBAT_MAIN
                || game.getTurnStepType() == PhaseStep.POSTCOMBAT_MAIN);

        if (sorcerySpeed) {
            for (ActivatedAbility a : playable) {
                if (a instanceof PlayLandAbility) {
                    return a;
                }
            }
            ActivatedAbility best = bestSpell(game, playable, true);
            if (best != null) {
                return best;
            }
            return bestSorcery(game, playable);
        }

        StackObject top = game.getStack().isEmpty()
                ? null : game.getStack().getFirst();
        if (top != null && !top.getControllerId().equals(playerId)) {
            ActivatedAbility counter = bestBy(game, playable,
                    c -> COUNTERSPELLS.contains(c.getName()));
            if (counter != null) {
                return counter;
            }
        }
        if (game.getTurnStepType() == PhaseStep.END_TURN && !myTurn) {
            return bestBy(game, playable, c -> c.isInstant(game));
        }
        return null;
    }

    private Card cardOf(Game game, ActivatedAbility a) {
        if (!(a instanceof SpellAbility)) {
            return null;
        }
        return game.getCard(a.getSourceId());
    }

    /**
     * Deterministic pick: highest mana value, ties broken by card name.
     * getPlayable's order follows hand-set iteration over per-game random
     * UUIDs, so "first in list" is NOT reproducible across game instances
     * (found by the B6 equivalence check).
     */
    private ActivatedAbility bestBy(Game game, List<ActivatedAbility> playable,
                                    java.util.function.Predicate<Card> filter) {
        ActivatedAbility best = null;
        int bestMv = -1;
        String bestName = null;
        for (ActivatedAbility a : playable) {
            Card c = cardOf(game, a);
            if (c == null || !filter.test(c)) {
                continue;
            }
            int mv = c.getManaValue();
            String name = c.getName();
            if (mv > bestMv || (mv == bestMv && bestName != null
                    && name.compareTo(bestName) < 0)) {
                best = a;
                bestMv = mv;
                bestName = name;
            }
        }
        return best;
    }

    private ActivatedAbility bestSpell(Game game, List<ActivatedAbility> playable,
                                       boolean creaturesOnly) {
        return bestBy(game, playable, c -> !creaturesOnly || c.isCreature(game));
    }

    private ActivatedAbility bestSorcery(Game game, List<ActivatedAbility> playable) {
        return bestBy(game, playable, c -> c.isSorcery(game));
    }

    // ------------------------------------------------------------ combat

    @Override
    public void selectAttackers(Game game, UUID attackingPlayerId) {
        yield = YieldKind.NONE;
        UUID defender = null;
        for (UUID opp : game.getOpponents(playerId)) {
            defender = opp;
            break;
        }
        if (defender == null) {
            return;
        }
        for (Permanent mine : this.getAvailableAttackers(game)) {
            boolean beaten = false;
            for (Permanent theirs
                    : game.getBattlefield().getAllActivePermanents(defender)) {
                if (theirs.isCreature(game) && !theirs.isTapped()
                        && theirs.getPower().getValue() >= mine.getToughness().getValue()
                        && theirs.getToughness().getValue() > mine.getPower().getValue()) {
                    beaten = true;
                    break;
                }
            }
            if (!beaten) {
                this.declareAttacker(mine.getId(), defender, game, false);
            }
        }
    }

    @Override
    public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
        yield = YieldKind.NONE;
        List<CombatGroup> groups = game.getCombat().getGroups();
        java.util.Set<UUID> used = new java.util.HashSet<>();
        int incoming = 0;
        for (CombatGroup g : groups) {
            for (UUID atkId : g.getAttackers()) {
                Permanent atk = game.getPermanent(atkId);
                if (atk != null) {
                    incoming += atk.getPower().getValue();
                }
            }
        }
        boolean lethal = incoming >= getLife();
        for (CombatGroup g : groups) {
            if (g.getAttackers().isEmpty()) {
                continue;
            }
            UUID atkId = g.getAttackers().get(0);
            Permanent atk = game.getPermanent(atkId);
            if (atk == null) {
                continue;
            }
            for (Permanent mine
                    : game.getBattlefield().getAllActivePermanents(playerId)) {
                if (!mine.isCreature(game) || mine.isTapped()
                        || used.contains(mine.getId())
                        || !mine.canBlock(atkId, game)) {
                    continue;
                }
                boolean kills = mine.getPower().getValue()
                        >= atk.getToughness().getValue();
                boolean survives = mine.getToughness().getValue()
                        > atk.getPower().getValue();
                if ((kills && survives) || lethal) {
                    this.declareBlocker(defendingPlayerId, mine.getId(), atkId, game);
                    used.add(mine.getId());
                    break;
                }
            }
        }
    }

    // ------------------------------------------------ callback counting

    private void tick() {
        if (inAction) {
            callbackCount++;
        }
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source, Game game) {
        tick();
        return super.choose(outcome, target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source, Game game,
                          Map<String, Serializable> options) {
        tick();
        return super.choose(outcome, target, source, game, options);
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Target target, Ability source, Game game) {
        tick();
        return super.chooseTarget(outcome, target, source, game);
    }

    @Override
    public boolean chooseTargetAmount(Outcome outcome, TargetAmount target,
                                      Ability source, Game game) {
        tick();
        return super.chooseTargetAmount(outcome, target, source, game);
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Cards cards, TargetCard target,
                                Ability source, Game game) {
        tick();
        return super.chooseTarget(outcome, cards, target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Cards cards, TargetCard target,
                          Ability source, Game game) {
        tick();
        return super.choose(outcome, cards, target, source, game);
    }

    @Override
    public boolean choose(Outcome outcome, Choice choice, Game game) {
        tick();
        return super.choose(outcome, choice, game);
    }

    @Override
    public boolean chooseUse(Outcome outcome, String message, Ability source, Game game) {
        tick();
        return super.chooseUse(outcome, message, source, game);
    }

    @Override
    public boolean chooseUse(Outcome outcome, String message, String secondMessage,
                             String trueText, String falseText, Ability source, Game game) {
        tick();
        return super.chooseUse(outcome, message, secondMessage, trueText, falseText,
                source, game);
    }

    @Override
    public Mode chooseMode(Modes modes, Ability source, Game game) {
        tick();
        return super.chooseMode(modes, source, game);
    }

    @Override
    public int announceX(int min, int max, String message, Game game, Ability source,
                         boolean isManaPay) {
        tick();
        return super.announceX(min, max, message, game, source, isManaPay);
    }

    @Override
    public int getAmount(int min, int max, String message, Ability source, Game game) {
        tick();
        return super.getAmount(min, max, message, source, game);
    }

    @Override
    public boolean playMana(Ability ability, ManaCost unpaid, String promptText, Game game) {
        tick();
        return super.playMana(ability, unpaid, promptText, game);
    }
}
