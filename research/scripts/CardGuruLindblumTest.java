package org.mage.test.cards.single;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Adjudication scenario: an impulse-exile effect hitting Lindblum, Industrial
 * Regency // Mage Siege (a land with an Adventure).
 *
 * (Original question used Improvisation Capstone; XMage marks that card
 * unfinished, so the engine refuses it. Reckless Impulse exercises the same
 * adventure-land mechanics: exile from library + permission to play.)
 *
 * Questions under test:
 * 1. Can the exile-play permission cast Mage Siege (the Adventure instant)
 *    even though the card is a land? (Expected: yes.)
 * 2. After Mage Siege resolves, is the card exiled again with the adventure
 *    rule, and can its owner play Lindblum from that exile as a land drop —
 *    even though that second exile no longer carries the impulse permission?
 *    (Expected: yes.)
 */
public class CardGuruLindblumTest extends CardTestPlayerBase {

    @Test
    public void testImpulseExileHitsLindblumAdventure() {
        skipInitShuffling();

        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 6);
        addCard(Zone.HAND, playerA, "Reckless Impulse", 1);
        // Library: last added ends on top. Top two: Lindblum, Grizzly Bears.
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears", 1);
        addCard(Zone.LIBRARY, playerA, "Lindblum, Industrial Regency", 1);

        // Exile the top two; until end of next turn, may play them.
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Reckless Impulse");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);

        // Q1: cast the Adventure half from exile (paying its {2}{R}).
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Mage Siege");
        waitStackResolved(1, PhaseStep.POSTCOMBAT_MAIN);

        // Q2: the adventure re-exiled the card; play the land from exile.
        playLand(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Lindblum, Industrial Regency");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Wizard Token", 1);
        assertPermanentCount(playerA, "Lindblum, Industrial Regency", 1);
        assertTapped("Lindblum, Industrial Regency", true);
        assertExileCount(playerA, "Grizzly Bears", 1);
    }
}
