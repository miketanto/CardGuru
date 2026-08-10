package org.mage.test.benchmark.rl;

import java.util.Random;

/** In-process uniform-random policy: milestone 2's throughput probe. */
public class RandomPolicyClient implements PolicyClient {

    private final Random rnd;

    public RandomPolicyClient(long seed) {
        this.rnd = new Random(seed);
    }

    @Override
    public int choose(float[] state, float[][] candidates) {
        return rnd.nextInt(candidates.length);
    }

    @Override
    public void episodeEnd(float reward) {
    }
}
