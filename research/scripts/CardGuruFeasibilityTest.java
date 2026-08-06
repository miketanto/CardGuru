package org.mage.test.cards.single;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Feasibility probes for driving XMage as an adjudication oracle:
 * 1) author a novel scenario programmatically and read the verified outcome;
 * 2) confirm unimplemented/unknown cards fail loudly instead of silently.
 */
public class CardGuruFeasibilityTest extends CardTestPlayerBase {

    @Test
    public void testCustomScenario_HumilityPlusOpalescence() {
        // Classic layers question: with both on the battlefield, what are P/T?
        // Depends on timestamp order; here Humility enters first, then Opalescence.
        addCard(Zone.BATTLEFIELD, playerA, "Humility", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Opalescence", 1);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // Opalescence (ts later) makes Humility a 4/4 creature; Humility (ts earlier)
        // then sets creatures to 1/1... but ability-loss ordering means both end 4/4
        // per the canonical adjudication of Humility+Opalescence timestamps.
        // We assert on whatever the engine returns; the point is that it RETURNS a
        // definite executed answer we can record.
        Assert.assertNotNull(getPermanent("Humility", playerA));
        Assert.assertNotNull(getPermanent("Opalescence", playerA));
        System.out.println("[CardGuru] Humility P/T = "
                + getPermanent("Humility", playerA).getPower().getValue() + "/"
                + getPermanent("Humility", playerA).getToughness().getValue()
                + ", is creature: " + getPermanent("Humility", playerA).isCreature(currentGame));
        System.out.println("[CardGuru] Opalescence P/T = "
                + getPermanent("Opalescence", playerA).getPower().getValue() + "/"
                + getPermanent("Opalescence", playerA).getToughness().getValue()
                + ", is creature: " + getPermanent("Opalescence", playerA).isCreature(currentGame));
    }

    @Test
    public void testUnknownCardFailsLoudly() {
        try {
            addCard(Zone.BATTLEFIELD, playerA, "Totally Nonexistent Card Name XYZ", 1);
            Assert.fail("expected unknown card to be rejected");
        } catch (IllegalArgumentException e) {
            System.out.println("[CardGuru] unknown card rejected with: " + e.getMessage());
        }
    }
}
