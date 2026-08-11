package org.mage.test.benchmark;

import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.common.PassAbility;
import mage.cards.Card;
import mage.constants.Zone;
import mage.game.Game;
import mage.players.Player;
import mage.util.RandomUtil;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * Phase 5 C0: imperfect-information variant of SearchPlayer.
 *
 * Same minimax skeleton, same GameStateEvaluator2 leaves, same ordering
 * and breadth cap — the ONLY change is that each candidate is scored as
 * the average over K determinizations. A determinization is a sim copy
 * whose hidden zones are re-randomized before anything is executed:
 *  - opponent's hand + library are pooled and re-dealt (decks are known
 *    mirrors, so "decklist minus observed" == shuffle hidden cards among
 *    hidden slots) — the MCTSNode.randomizePlayers pattern;
 *  - own library order is also shuffled (an honest player knows its own
 *    hand but not its library order; sims that draw would otherwise read
 *    the true order).
 * Everything derived from the determinized root (candidate execution,
 * deeper plies) is perfect-info minimax WITHIN that determinization.
 *
 * Determinism: each (decision, k) reseeds RandomUtil from
 * (benchSeed, decision#, k); after the search the stream is re-keyed
 * exactly as SearchPlayer does, so a SearchPlayerIP seat perturbs the
 * main game's random stream identically to a SearchPlayer seat.
 *
 * Dial: plies x breadth x K (determinizations).
 */
public class SearchPlayerIP extends SearchPlayer {

    public int determinizations = 4;
    public long determinizationsRun = 0;

    public SearchPlayerIP(String name) {
        super(name);
    }

    @Override
    public boolean priority(Game game) {
        if (!canRespond()) {
            return heuristicPriority(game);
        }
        List<ActivatedAbility> playable;
        try {
            playable = getPlayable(game, true);
        } catch (Exception e) {
            return heuristicPriority(game);
        }
        List<Ability> candidates = new ArrayList<>();
        for (ActivatedAbility a : playable) {
            if (!a.isManaAbility()) {
                candidates.add(a);
            }
        }
        if (candidates.size() <= 1) {
            return heuristicPriority(game);   // no real choice: D0 behavior
        }
        candidates.sort(Comparator
                .comparingInt((Ability a) -> -a.getManaCosts().manaValue())
                .thenComparing(a -> String.valueOf(a.getRule())));
        if (candidates.size() > searchBreadth) {
            candidates = candidates.subList(0, searchBreadth);
        }
        candidates.add(new PassAbility());

        Ability best = null;
        double bestScore = -Double.MAX_VALUE;
        for (Ability cand : candidates) {
            double sum = 0;
            for (int k = 0; k < determinizations; k++) {
                RandomUtil.setSeed(benchSeed * 7_777_777L
                        + decisionCounter * 101L + k + 1);
                double s;
                Game det;
                try {
                    det = game.createSimulationForAI();
                    determinize(det);
                } catch (Exception e) {
                    det = null;
                }
                if (det == null) {
                    s = Integer.MIN_VALUE + 1;
                } else if (cand instanceof PassAbility) {
                    s = value(det, searchPlies - 1, opponentOf(game));
                } else {
                    Game sim = execute(det, getId(), cand);
                    s = sim == null ? Integer.MIN_VALUE + 1
                            : value(sim, searchPlies - 1, opponentOf(game));
                }
                sum += s;
            }
            double score = sum / determinizations;
            if (score > bestScore) {
                bestScore = score;
                best = cand;
            }
        }
        searchDecisions++;
        decisionCounter++;
        RandomUtil.setSeed(benchSeed * 7_777_777L + decisionCounter);
        if (best == null || best instanceof PassAbility) {
            return heuristicPriority(game);   // heuristic handles the pass
        }
        return this.activateAbility((ActivatedAbility) best.copy(), game);
    }

    /** re-randomize hidden zones on a sim copy (never on the real game) */
    protected void determinize(Game sim) {
        determinizationsRun++;
        for (Player p : sim.getState().getPlayers().values()) {
            if (p.getId().equals(getId())) {
                p.getLibrary().shuffle();
            } else {
                int handSize = p.getHand().size();
                p.getLibrary().addAll(p.getHand().getCards(sim), sim);
                p.getHand().clear();
                p.getLibrary().shuffle();
                for (int i = 0; i < handSize; i++) {
                    Card c = p.getLibrary().drawFromTop(sim);
                    if (c == null) {
                        break;
                    }
                    c.setZone(Zone.HAND, sim);
                    p.getHand().add(c);
                }
            }
        }
    }
}
