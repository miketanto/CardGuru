package org.mage.test.l17;

import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.SpellAbility;
import mage.abilities.PlayLandAbility;
import mage.abilities.TriggeredAbility;
import mage.abilities.StaticAbility;
import mage.abilities.mana.ManaAbility;
import mage.cards.Card;
import mage.cards.repository.CardInfo;
import mage.cards.repository.CardRepository;
import org.mage.test.serverside.base.MageTestPlayerBase;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;

/**
 * Does the card an ability id was traced to even HAVE an activated ability?
 *
 * rl/l17/ability_map.py maps a logged 17Lands ability id to the CARD that owns it, not
 * to which of that card's abilities it is -- the 17Lands column logs triggered abilities
 * as well as activated ones. The `abil` variant can only replay activated ones. This
 * prints, per mapped card, whether XMage's implementation at the pin has a non-mana
 * activated ability at all, so the share of logged ability occurrences that were ever
 * replayable can be stated rather than guessed.
 *
 *   java -cp classes:CP org.mage.test.l17.AbilityKinds MAP.tsv OUT.csv
 *
 * MAP.tsv is ability_map_cloud.csv re-written tab-separated (card names contain commas).
 */
public class AbilityKinds {

    public static void main(String[] args) throws Exception {
        MageTestPlayerBase.init();
        org.apache.log4j.Logger.getRootLogger().setLevel(org.apache.log4j.Level.ERROR);
        List<String> lines = Files.readAllLines(Paths.get(args[0]), StandardCharsets.UTF_8);
        PrintWriter out = new PrintWriter(new OutputStreamWriter(new FileOutputStream(args[1]), StandardCharsets.UTF_8));
        out.println("ability_id,occurrences,card,has_activated_nonmana,n_activated_nonmana,n_triggered,found");
        long occTotal = 0, occAct = 0, occNotFound = 0;
        int nAct = 0, nCards = 0;
        for (String line : lines.subList(1, lines.size())) {
            String[] f = line.split("\t", -1);
            // ability_id,occurrences,card,coverage,lift,accepted,is_basic_land,runner_up,runner_up_coverage
            if (f.length < 7 || !"1".equals(f[5]) || !"0".equals(f[6]) || f[2].isEmpty()) continue;
            String name = f[2];
            long occ = Long.parseLong(f[1]);
            CardInfo ci = CardRepository.instance.findCard(name, true);
            if (ci == null && name.contains(" // ")) {
                ci = CardRepository.instance.findCard(name.substring(0, name.indexOf(" // ")), true);
            }
            Card c = ci == null ? null : ci.createCard();
            occTotal += occ;
            nCards++;
            if (c == null) {
                occNotFound += occ;
                out.println(f[0] + "," + occ + ",\"" + name + "\",,,,0");
                continue;
            }
            int act = 0, trig = 0;
            for (Ability a : c.getAbilities()) {
                if (a instanceof TriggeredAbility) trig++;
                else if (a instanceof ActivatedAbility && !(a instanceof ManaAbility)
                        && !(a instanceof SpellAbility) && !(a instanceof PlayLandAbility)) act++;
            }
            if (act > 0) {
                nAct++;
                occAct += occ;
            }
            out.println(f[0] + "," + occ + ",\"" + name + "\"," + (act > 0 ? 1 : 0) + "," + act + "," + trig + ",1");
        }
        out.flush();
        out.close();
        System.out.println("ABILKIND|mapped_non_basic_land_ids=" + nCards + "|with_activated_nonmana=" + nAct
                + "|card_not_found=" + (occNotFound > 0 ? "some" : "none"));
        System.out.println("ABILKIND|occurrences=" + occTotal + "|on_a_card_with_an_activated_nonmana_ability="
                + occAct + "=" + String.format(Locale.ROOT, "%.3f", occAct / (double) Math.max(1, occTotal)));
    }
}
