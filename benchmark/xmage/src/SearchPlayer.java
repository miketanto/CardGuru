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
 *    is a "cheating" yardstick - deterministic, cheap, and strictly
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
 * Phase 5 C3 refactor: the root search is exposed as static
 * searchBest(...) so a DAgger shadow teacher can label arbitrary
 * states from any seat. The instance behavior is bit-identical to the
 * pre-refactor version (verified by same-seed calibration replay).
 *
 * Dial: plies x breadth. D1=1x8 (~8 nodes), D2=2x6 (~36), D3=3x5
 * (~125), D4=3x8 (~512). Actual nodes are counted and reported.
 */
public class SearchPlayer extends HeuristicPlayer {

    public int searchPlies = 1;
    public int searchBreadth = 8;
    public long nodesEvaluated = 0;
    public long searchDecisions = 0;
    protected long decisionCounter = 0;
    /** open-mana experiment: hold flash/instants out of sorcery-speed
     *  search candidates (SearchPlayerHold sets this) */
    public boolean holdFlashSearch = false;

    public SearchPlayer(String name) {
        super(name);
    }

    /** D0 delegation point — lets subclasses (SearchPlayerIP) fall back to
     *  HeuristicPlayer behavior without re-entering this class's search */
    protected boolean heuristicPriority(Game game) {
        return super.priority(game);
    }

    @Override
    public boolean priority(Game game) {
        if (!canRespond()) {
            return heuristicPriority(game);
        }
        long[] nodes = {0};
        Ability best = searchBest(game, getId(), searchPlies, searchBreadth,
                benchSeed * 7_777_777L + decisionCounter, nodes,
                holdFlashSearch);
        nodesEvaluated += nodes[0];
        if (best == null) {
            return heuristicPriority(game);   // no real choice: D0 behavior
        }
        searchDecisions++;
        decisionCounter++;
        RandomUtil.setSeed(benchSeed * 7_777_777L + decisionCounter);
        if (best instanceof PassAbility) {
            return heuristicPriority(game);   // heuristic handles the pass
        }
        return this.activateAbility((ActivatedAbility) best.copy(), game);
    }

    /**
     * Root search, callable from any seat (C3 shadow teacher). Returns
     * the chosen ability (PassAbility = search prefers passing), or
     * null when there is no real choice (<=1 non-mana candidates - the
     * instrument delegates those windows to D0). reseedKey is applied
     * AFTER candidate enumeration, exactly as the pre-refactor
     * instance code did; pass Long.MIN_VALUE to skip reseeding.
     * nodesOut[0] accumulates nodes evaluated.
     */
    public static Ability searchBest(Game game, UUID me, int plies,
                                     int breadth, long reseedKey,
                                     long[] nodesOut) {
        return searchBest(game, me, plies, breadth, reseedKey, nodesOut, false);
    }

    public static Ability searchBest(Game game, UUID me, int plies,
                                     int breadth, long reseedKey,
                                     long[] nodesOut, boolean holdFlash) {
        Player actor = game.getPlayer(me);
        if (actor == null) {
            return null;
        }
        List<ActivatedAbility> playable;
        try {
            playable = actor.getPlayable(game, true);
        } catch (Exception e) {
            return null;
        }
        boolean sorceryWindow = game.getActivePlayerId() != null
                && game.getActivePlayerId().equals(me)
                && game.getStack().isEmpty()
                && (game.getTurnStepType() == mage.constants.PhaseStep.PRECOMBAT_MAIN
                || game.getTurnStepType() == mage.constants.PhaseStep.POSTCOMBAT_MAIN);
        List<Ability> candidates = new ArrayList<>();
        for (ActivatedAbility a : playable) {
            if (a.isManaAbility()) {
                continue;
            }
            if (holdFlash && sorceryWindow && HeuristicPlayer.holdable(
                    game, game.getCard(a.getSourceId()))) {
                continue;   // hold it: cast at instant speed or not at all
            }
            candidates.add(a);
        }
        if (candidates.size() <= 1) {
            return null;
        }
        // fixed ordering, then breadth cap: expensive spells first,
        // name tie-break for reproducibility
        candidates.sort(Comparator
                .comparingInt((Ability a) -> -a.getManaCosts().manaValue())
                .thenComparing(a -> String.valueOf(a.getRule())));
        if (candidates.size() > breadth) {
            candidates = candidates.subList(0, breadth);
        }
        candidates.add(new PassAbility());

        if (reseedKey != Long.MIN_VALUE) {
            RandomUtil.setSeed(reseedKey);
        }
        Ability best = null;
        int bestScore = Integer.MIN_VALUE;
        for (Ability cand : candidates) {
            int score;
            if (cand instanceof PassAbility) {
                score = valueStatic(game, plies - 1, opponentOf(game, me),
                        me, breadth, nodesOut);
            } else {
                Game sim = executeStatic(game, me, cand, nodesOut);
                score = sim == null ? Integer.MIN_VALUE + 1
                        : valueStatic(sim, plies - 1, opponentOf(game, me),
                                me, breadth, nodesOut);
            }
            if (score > bestScore) {
                bestScore = score;
                best = cand;
            }
        }
        return best;
    }

    protected static UUID opponentOf(Game game, UUID me) {
        return game.getOpponents(me).stream().findFirst().orElse(me);
    }

    protected UUID opponentOf(Game game) {
        return opponentOf(game, getId());
    }

    /** apply one candidate on a fresh sim, drain the stack, return sim */
    protected static Game executeStatic(Game game, UUID actor, Ability ability,
                                        long[] nodesOut) {
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
            nodesOut[0]++;
            return sim;
        } catch (Exception e) {
            return null;    // engine edge case in sim: treat as unevaluable
        }
    }

    /** instance wrapper kept for SearchPlayerIP */
    protected Game execute(Game game, UUID actor, Ability ability) {
        long[] nodes = {0};
        Game sim = executeStatic(game, actor, ability, nodes);
        nodesEvaluated += nodes[0];
        return sim;
    }

    /** minimax value of a state from ME's perspective; toAct moves next */
    protected static int valueStatic(Game state, int pliesLeft, UUID toAct,
                                     UUID me, int breadth, long[] nodesOut) {
        if (pliesLeft <= 0 || state.hasEnded()) {
            return GameStateEvaluator2.evaluate(me, state).getTotalScore();
        }
        Player actor = state.getPlayer(toAct);
        if (actor == null) {
            return GameStateEvaluator2.evaluate(me, state).getTotalScore();
        }
        List<ActivatedAbility> moves;
        try {
            moves = actor.getPlayable(state, true);
        } catch (Exception e) {
            return GameStateEvaluator2.evaluate(me, state).getTotalScore();
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
        if (cands.size() > breadth) {
            cands = cands.subList(0, breadth);
        }
        boolean maximizing = toAct.equals(me);
        UUID next = maximizing ? opponentOf(state, me) : me;
        // pass is always available; passing changes nothing material at
        // this abstraction level (counted as a node, as before)
        nodesOut[0]++;
        int best = valueStatic(state, 0, next, me, breadth, nodesOut);
        for (Ability cand : cands) {
            Game child = executeStatic(state, toAct, cand, nodesOut);
            if (child == null) {
                continue;
            }
            int v = valueStatic(child, pliesLeft - 1, next, me, breadth, nodesOut);
            best = maximizing ? Math.max(best, v) : Math.min(best, v);
        }
        return best;
    }

    /** instance wrapper kept for SearchPlayerIP */
    protected int value(Game state, int pliesLeft, UUID toAct) {
        long[] nodes = {0};
        int v = valueStatic(state, pliesLeft, toAct, getId(), searchBreadth, nodes);
        nodesEvaluated += nodes[0];
        return v;
    }
}
