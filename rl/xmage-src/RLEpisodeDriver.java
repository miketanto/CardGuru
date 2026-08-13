package org.mage.test.benchmark.rl;

import org.junit.Test;
import org.mage.test.serverside.base.MageTestPlayerBase;

/**
 * Episode loop: RLPlayer (agent seat) vs a fixed opponent, mirror decks.
 * NOT self-play - the opponent is stationary by design (the measurement
 * depends on it).
 *
 * System properties:
 *   -Drl.episodes=100        episodes this invocation
 *   -Drl.opponent=random     random | heuristic
 *   -Drl.policy=random       random | socket
 *   -Drl.port=7777           socket policy port
 *   -Drl.deck=BenchBurn.dck
 *   -Drl.seed=0              base seed; episode i uses seed+i
 *   -Drl.stopTurn=60         stall bound; stalls score reward 0
 *   -Drl.report=100          print a progress line every N episodes
 *
 * Consult convention (milestone 1): all counts in rl/ are AGENT-SEAT
 * consults per episode. Phase 1/2 "windows/game" numbers summed BOTH
 * seats via shared static counters - divide by ~2 to compare.
 *
 * Phase 9: the loop itself moved to {@link EpisodeRunner} so the
 * persistent {@link RLDriverServer} can run the same code without a
 * surefire JVM per chunk. This class is still THE mvn entry point and
 * its behavior is unchanged; league runners that call mvn keep working.
 */
public class RLEpisodeDriver extends MageTestPlayerBase {

    @org.junit.BeforeClass
    public static void buildCardDb() {
        // MageTestPlayerBase never scans; without this a fresh checkout has
        // an empty card DB and every deck loads 0 cards (synchronous, one-time
        // cost per checkout - the db/ directory persists)
        mage.cards.repository.CardScanner.scan();
        // inert unless -Dxmage.dataCollectors.printGameLogs=true, which
        // routes the engine's informPlayers game log to log4j (full
        // human-readable transcripts for debugging/sampling)
        mage.collectors.DataCollectorServices.init(false, false);
    }

    @Test
    public void runEpisodes() throws Exception {
        new EpisodeRunner().run(System.out);
    }
}
