import mage.cards.repository.*;
import mage.constants.CardType;
import mage.constants.SuperType;
import java.util.*;

/** Rung 4/5 candidates: cheap single-line INSTANTS and SORCERIES.
 *  The pair we want is the SAME effect printed at both speeds, so a rung
 *  can move timing alone (sorcery -> instant) with the effect held fixed. */
public class SpellScan {
    static void dump(CardType type, String tag) {
        CardCriteria cc = new CardCriteria();
        cc.types(type);
        Map<String,String> out = new TreeMap<>();
        for (CardInfo ci : CardRepository.instance.findCards(cc)) {
            if (ci.getSupertypes().contains(SuperType.LEGENDARY)) continue;
            List<String> r = ci.getRules();
            if (r == null || r.size() != 1) continue;
            String rule = r.get(0).trim();
            if (rule.isEmpty() || rule.length() > 80) continue;
            String mc = String.join("", ci.getManaCosts(CardInfo.ManaCostSide.ALL));
            if (mc.isEmpty() || mc.length() > 12) continue;
            out.putIfAbsent(ci.getName(),
                mc + "|" + ci.getSetCode() + ":" + ci.getCardNumber() + "|" + rule);
        }
        System.out.println(tag + "_COUNT=" + out.size());
        for (Map.Entry<String,String> e : out.entrySet())
            System.out.println(tag + "|" + e.getKey() + "|" + e.getValue());
    }

    public static void main(String[] args) {
        dump(CardType.INSTANT, "I");
        dump(CardType.SORCERY, "S");
    }
}
