import mage.cards.repository.*;
import mage.constants.CardType;
import mage.constants.SuperType;
import java.util.*;

public class LadderScan {
    public static void main(String[] args) throws Exception {
        // creatures whose ENTIRE text is one short line (keyword candidates)
        CardCriteria cc = new CardCriteria();
        cc.types(CardType.CREATURE);
        Map<String,String> creatures = new TreeMap<>();
        for (CardInfo ci : CardRepository.instance.findCards(cc)) {
            if (ci.getSupertypes().contains(SuperType.LEGENDARY)) continue;
            List<String> r = ci.getRules();
            if (r == null || r.size() != 1) continue;
            String rule = r.get(0).trim();
            if (rule.isEmpty() || rule.length() > 24) continue;
            String p = ci.getPower(), t = ci.getToughness();
            String mc = String.join("", ci.getManaCosts(CardInfo.ManaCostSide.ALL));
            if (p == null || t == null || mc.isEmpty()) continue;
            if (p.contains("*") || t.contains("*")) continue;
            creatures.putIfAbsent(ci.getName(),
                mc + "|" + p + "/" + t + "|" + ci.getSetCode() + ":" + ci.getCardNumber() + "|" + rule);
        }
        System.out.println("KEYWORD_CREATURES=" + creatures.size());
        for (Map.Entry<String,String> e : creatures.entrySet())
            System.out.println("K|" + e.getKey() + "|" + e.getValue());

        // cheap instants (pump / removal candidates)
        CardCriteria ic = new CardCriteria();
        ic.types(CardType.INSTANT);
        Map<String,String> instants = new TreeMap<>();
        for (CardInfo ci : CardRepository.instance.findCards(ic)) {
            List<String> r = ci.getRules();
            if (r == null || r.size() != 1) continue;
            String rule = r.get(0).trim();
            if (rule.isEmpty() || rule.length() > 70) continue;
            String mc = String.join("", ci.getManaCosts(CardInfo.ManaCostSide.ALL));
            if (mc.isEmpty()) continue;
            instants.putIfAbsent(ci.getName(),
                mc + "|" + ci.getSetCode() + ":" + ci.getCardNumber() + "|" + rule);
        }
        System.out.println("SIMPLE_INSTANTS=" + instants.size());
        for (Map.Entry<String,String> e : instants.entrySet())
            System.out.println("I|" + e.getKey() + "|" + e.getValue());
    }
}
