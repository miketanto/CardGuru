package org.mage.test.benchmark;

import mage.cards.Card;
import mage.cards.repository.CardInfo;
import mage.cards.repository.CardRepository;
import org.junit.Test;
import org.mage.test.serverside.base.MageTestPlayerBase;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

/**
 * Phase 3.3: card coverage. Reads sampled card-name files (one name per
 * line, written by the collector from the canonical printings index),
 * looks each up in XMage's card repository, and attempts to instantiate
 * the card class. Failure modes are separated:
 *   - not_in_db: CardRepository has no entry (card not implemented)
 *   - instantiation_error: DB entry exists but createCard failed
 *
 * Also verifies Phase 3.2 (failure signal): a nonexistent card name
 * must be detectable, not silently absorbed.
 */
public class B7CoverageTest extends MageTestPlayerBase {

    private void coverageFor(String sampleFile, String label) throws Exception {
        Path p = Paths.get(sampleFile);
        List<String> names = Files.readAllLines(p, StandardCharsets.UTF_8);
        int found = 0, instantiated = 0, notInDb = 0, instErr = 0;
        StringBuilder missSample = new StringBuilder();
        for (String name : names) {
            if (name.trim().isEmpty()) {
                continue;
            }
            List<CardInfo> infos = CardRepository.instance.findCards(name.trim());
            if (infos.isEmpty()) {
                notInDb++;
                if (missSample.length() < 400) {
                    missSample.append(name).append("; ");
                }
                continue;
            }
            found++;
            try {
                Card c = infos.get(0).createCard();
                if (c != null) {
                    instantiated++;
                } else {
                    instErr++;
                }
            } catch (Exception | Error e) {
                instErr++;
            }
        }
        int total = found + notInDb;
        System.out.println(String.format(Locale.ROOT,
                "BENCH|B7.%s|sampled=%d|in_db=%d|instantiated=%d|not_in_db=%d|instantiation_errors=%d|coverage_pct=%.1f",
                label, total, found, instantiated, notInDb, instErr,
                100.0 * instantiated / Math.max(1, total)));
        System.out.println("BENCH|B7." + label + ".misses|" + missSample);
    }

    @Test
    public void coverage() throws Exception {
        String dir = System.getProperty("bench.sampledir", "/tmp/bench_samples");
        coverageFor(dir + "/sample_modern.txt", "modern_pool");
        coverageFor(dir + "/sample_all.txt", "all_cards");

        // failure-signal check: unknown names are loudly detectable
        List<CardInfo> bogus = CardRepository.instance.findCards(
                "Totally Nonexistent Card " + UUID.randomUUID());
        System.out.println("BENCH|B7.failure_signal|unknown_card_lookup_empty="
                + bogus.isEmpty());
    }
}
