package org.mage.test.benchmark;

import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.constants.RangeOfInfluence;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.permanent.Permanent;
import mage.player.ai.ComputerPlayer;
import mage.util.RandomUtil;

import java.util.List;
import java.util.UUID;

/**
 * Uniform-random priority policy on top of ComputerPlayer's cheap
 * (non-simulating) choice machinery.
 *
 * At each priority window the player computes the legal activations via
 * getPlayable() and picks uniformly among {each playable, pass}. Target
 * and mode choices inside a chosen action fall back to ComputerPlayer's
 * heuristic (loop-cheap, no tree search) - documented in RESULTS.md as
 * "random action selection, heuristic choice resolution".
 *
 * NOT ComputerPlayer7: no simulation, no state copying from the policy
 * itself. What this measures is the ENGINE cost of stepping decisions.
 *
 * Static counters are single-process/single-game-thread only - the
 * benchmark runs one game at a time per JVM; parallelism is process-level.
 */
public class RandomPlayer extends ComputerPlayer {

    /** priority windows seen (decision points) */
    public static long decisions = 0;
    /** histogram of playable-count k per priority window; bucket k
     *  (k=0 means pass was the only legal action); last bucket = overflow */
    public static final long[] PLAYABLE_HIST = new long[65];
    /** actions actually taken (non-pass) */
    public static long actionsTaken = 0;
    /** combat instrumentation */
    public static long attackWindows = 0;
    public static long attacksDeclared = 0;

    public RandomPlayer(String name) {
        super(name, RangeOfInfluence.ONE);
    }

    public static void resetCounters() {
        decisions = 0;
        actionsTaken = 0;
        java.util.Arrays.fill(PLAYABLE_HIST, 0);
    }

    @Override
    public boolean priority(Game game) {
        decisions++;
        List<ActivatedAbility> playable = getPlayable(game, true);
        int k = playable.size();
        PLAYABLE_HIST[Math.min(k, PLAYABLE_HIST.length - 1)]++;
        if (k == 0) {
            pass(game);
            return false;
        }
        int pick = RandomUtil.nextInt(k + 1);   // uniform over playables + pass
        if (pick == k) {
            pass(game);
            return false;
        }
        ActivatedAbility ability = (ActivatedAbility) playable.get(pick).copy();
        boolean acted = this.activateAbility(ability, game);
        if (acted) {
            actionsTaken++;
        } else {
            pass(game);
        }
        return acted;
    }

    @Override
    public void selectAttackers(Game game, UUID attackingPlayerId) {
        // each creature that can attack does so with p=0.5, at a random
        // defender (ComputerPlayer's base method is a do-nothing stub)
        attackWindows++;
        UUID defender = null;
        for (UUID opp : game.getOpponents(playerId)) {
            defender = opp;
            break;
        }
        if (defender == null) {
            return;
        }
        for (Permanent creature : this.getAvailableAttackers(game)) {
            if (RandomUtil.nextInt(2) == 0) {
                this.declareAttacker(creature.getId(), defender, game, false);
                attacksDeclared++;
            }
        }
    }

    @Override
    public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
        // each untapped creature blocks a uniformly random attacker with p=0.5
        List<CombatGroup> groups = game.getCombat().getGroups();
        if (groups.isEmpty()) {
            return;
        }
        for (Permanent creature : game.getBattlefield().getAllActivePermanents(playerId)) {
            if (!creature.isCreature(game) || creature.isTapped()) {
                continue;
            }
            if (RandomUtil.nextInt(2) != 0) {
                continue;
            }
            CombatGroup group = groups.get(RandomUtil.nextInt(groups.size()));
            if (!group.getAttackers().isEmpty()) {
                UUID attackerId = group.getAttackers().get(0);
                Permanent attacker = game.getPermanent(attackerId);
                if (attacker != null && creature.canBlock(attackerId, game)) {
                    this.declareBlocker(defendingPlayerId, creature.getId(), attackerId, game);
                }
            }
        }
    }
}
