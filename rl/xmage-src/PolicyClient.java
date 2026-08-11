package org.mage.test.benchmark.rl;

/**
 * The policy boundary. One consult = one decision point AFTER the wrapper
 * filters (k=0 autopass, phantom-land filter, yields). Candidates arrive
 * canonically ordered (name-sorted) - this ordering is load-bearing:
 * getPlayable/UUID iteration order is not reproducible across game
 * instances (Phase 2 finding).
 *
 * Implementations: RandomPolicyClient (in-process, milestone 2),
 * SocketPolicyClient (IPC V1, milestone 3+).
 */
public interface PolicyClient {

    /** Returns the index of the chosen candidate in [0, candidates.length). */
    int choose(float[] state, float[][] candidates);

    /**
     * Consult with a potential value Φ(s) for reward shaping (C2a):
     * raw GameStateEvaluator2 score from the agent's perspective, or 0
     * when shaping is off. Default ignores it (RandomPolicyClient).
     */
    default int choose(float[] state, float[][] candidates, float phi) {
        return choose(state, candidates);
    }

    /** Terminal signal for the episode: +1 win, -1 loss, 0 draw/stall. */
    void episodeEnd(float reward);

    default void close() {
    }
}
