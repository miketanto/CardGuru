package org.mage.test.benchmark;

import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.common.PassAbility;
import mage.game.Game;
import mage.player.ai.score.GameStateEvaluator2;
import mage.players.Player;
import mage.util.RandomUtil;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * Phase 4 depth-ladder opponent: depth-limited minimax over
 * Game.createSimulationForAI() copies with GameStateEvaluator2 at the
 * leaves (the mad module's battle-tested static evaluator - life,
 * board, hand; deliberately reused unchanged as an INSTRUMENT).
 *
 * Documented instrument choices (PHASE4-LADDER.md):
 *  - PERFECT-INFORMATION search: sims copy true hidden state, so this
 *    is a "cheating" evaluator - deterministic, cheap, and strictly
 *    harder to fool than determinized search at equal node budget.
 *    K (determinizations) is therefore 0 by design, held fixed.
 *  - Search fires only when there is a real choice (>1 non-mana
 *    playable); all other windows delegate to HeuristicPlayer logic,
 *    including all combat decisions (same combat as D0 - the ladder
 *    measures SPELL/priority depth only).
 *  - Targets/modes inside a candidate are resolved by ComputerPlayer
 *    heuristics on the sim, as in ComputerPlayer6.
 *  - Determinism: RandomUtil is reseeded from (benchSeed, decision#)
 *    before each search and again after it, so the number of nodes
 *    explored cannot perturb the main game's random stream.
 *
 * Dial: plies x breadth. D1=1x8 (~8 nodes), D2=2x6 (~36), D3=3x5
 * (~125), D4=3x8 (~512). Actual nodes are counted and reported.
 */
public class SearchPlayer extends HeuristicPlayer {

    public int searchPlies = 1;
    public int searchBreadth = 8;
    public long nodesEvaluated = 0;
    public long searchDecisions = 0;
    private long decisionCounter = 0;

    public SearchPlayer(String name) {
        super(name);
    }

    @Override
    public boolean priority(Game game) {
        if (!canRespond()) {
            return super.priority(game);
        }
        List<ActivatedAbility> playable;
        try {
            playable = getPlayable(game, true);
        } catch (Exception e) {
            return super.priority(game);
        }
        List<Ability> candidates = new ArrayList<>();
        for (ActivatedAbility a : playable) {
            if (!a.isManaAbility()) {
                candidates.add(a);
            }
        }
        if (candidates.size() <= 1) {
            return super.priority(game);   // no real choice: D0 behavior
        }
        // fixed ordering, then breadth cap: expensive spells first,
        // name tie-break for reproducibility
        candidates.sort(Comparator
                .comparingInt((Ability a) -> -a.getManaCosts().manaValue())
                .thenComparing(a -> String.valueOf(a.getRule())));
        if (candidates.size() > searchBreadth) {
            candidates = candidates.subList(0, searchBreadth);
        }
        candidates.add(new PassAbility());

        RandomUtil.setSeed(benchSeed * 7_777_777L + decisionCounter);
        Ability best = null;
        int bestScore = Integer.MIN_VALUE;
        for (Ability cand : candidates) {
            int score;
            if (cand instanceof PassAbility) {
                score = value(game, searchPlies - 1, opponentOf(game));
            } else {
                Game sim = execute(game, getId(), cand);
                score = sim == null ? Integer.MIN_VALUE + 1
                        : value(sim, searchPlies - 1, opponentOf(game));
            }
            if (score > bestScore) {
                bestScore = score;
                best = cand;
            }
        }
        searchDecisions++;
        decisionCounter++;
        RandomUtil.setSeed(benchSeed * 7_777_777L + decisionCounter);
        if (best == null || best instanceof PassAbility) {
            return super.priority(game);   // heuristic handles the pass
        }
        return this.activateAbility((ActivatedAbility) best.copy(), game);
    }

    private UUID opponentOf(Game game) {
        return game.getOpponents(getId()).stream().findFirst().orElse(getId());
    }

    /** apply one candidate on a fresh sim, drain the stack, return sim */
    private Game execute(Game game, UUID actor, Ability ability) {
        try {
            Game sim = game.createSimulationForAI();
            Player p = sim.getPlayer(actor);
            if (p == null
                    || !p.activateAbility((ActivatedAbility) ability.copy(), sim)) {
                return null;
            }
            sim.applyEffects();
            sim.checkStateAndTriggered();
            int guard = 25;
            while (!sim.getStack().isEmpty() && guard-- > 0) {
                sim.getStack().resolve(sim);
                sim.applyEffects();
                sim.checkStateAndTriggered();
            }
            nodesEvaluated++;
            return sim;
        } catch (Exception e) {
            return null;    // engine edge case in sim: treat as unevaluable
        }
    }

    /** minimax value of a state from MY perspective; toAct moves next */
    private int value(Game state, int pliesLeft, UUID toAct) {
        if (pliesLeft <= 0 || state.hasEnded()) {
            return GameStateEvaluator2.evaluate(getId(), state).getTotalScore();
        }
        Player actor = state.getPlayer(toAct);
        if (actor == null) {
            return GameStateEvaluator2.evaluate(getId(), state).getTotalScore();
        }
        List<ActivatedAbility> moves;
        try {
            moves = actor.getPlayable(state, true);
        } catch (Exception e) {
            return GameStateEvaluator2.evaluate(getId(), state).getTotalScore();
        }
        List<Ability> cands = new ArrayList<>();
        for (ActivatedAbility a : moves) {
            if (!a.isManaAbility()) {
                cands.add(a);
            }
        }
        cands.sort(Comparator
                .comparingInt((Ability a) -> -a.getManaCosts().manaValue())
                .thenComparing(a -> String.valueOf(a.getRule())));
        if (cands.size() > searchBreadth) {
            cands = cands.subList(0, searchBreadth);
        }
        boolean maximizing = toAct.equals(getId());
        UUID next = maximizing ? opponentOf(state) : getId();
        // pass is always available
        int best = value(stateAfterPass(state), 0, next);
        for (Ability cand : cands) {
            Game child = execute(state, toAct, cand);
            if (child == null) {
                continue;
            }
            int v = value(child, pliesLeft - 1, next);
            best = maximizing ? Math.max(best, v) : Math.min(best, v);
        }
        return best;
    }

    /** passing changes nothing material at this abstraction level */
    private Game stateAfterPass(Game state) {
        nodesEvaluated++;
        return state;
    }
}
