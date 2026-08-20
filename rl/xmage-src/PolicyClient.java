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

    /**
     * Encoder v6 consult: the state is entity tokens + a typed relation
     * edge list instead of one flat vector (ENCODER-V6-BUILD.md §4b).
     * The candidate side is UNCHANGED - v6 is a state-path change and
     * nothing else.
     *
     * Default drops the view and consults with an empty state, which is
     * what RandomPolicyClient wants (it ignores the state entirely) and
     * would be wrong for anything that reads it; SocketPolicyClient
     * overrides. Kept as a default so v1-v5 arms still run from ONE
     * build, exactly as -Drl.encoderV already allows.
     */
    default int choose(StateEncoder.EntityView view, float[][] candidates,
                       float phi) {
        return choose(new float[0], candidates, phi);
    }

    /** Terminal signal for the episode: +1 win, -1 loss, 0 draw/stall. */
    void episodeEnd(float reward);

    default void close() {
    }
}
