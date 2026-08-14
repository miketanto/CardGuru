import mage.cards.repository.*;
import mage.constants.CardType;
import java.util.*;

public class VanillaScan {
    public static void main(String[] args) throws Exception {
        CardCriteria c = new CardCriteria();
        c.types(CardType.CREATURE);
        List<CardInfo> all = CardRepository.instance.findCards(c);
        Map<String,String> best = new TreeMap<>();
        for (CardInfo ci : all) {
            List<String> rules = ci.getRules();
            boolean vanilla = rules == null || rules.isEmpty()
                    || rules.stream().allMatch(r -> r == null || r.trim().isEmpty());
            if (!vanilla) continue;
            String p = ci.getPower(), t = ci.getToughness(); String mc = String.join("", ci.getManaCosts(CardInfo.ManaCostSide.ALL));
            if (p == null || t == null || mc == null || mc.isEmpty()) continue;
            if (p.contains("*") || t.contains("*")) continue;
            boolean leg = ci.getSupertypes().contains(mage.constants.SuperType.LEGENDARY);
            if (leg) continue;
            best.putIfAbsent(ci.getName(), mc + "|" + p + "/" + t + "|" + ci.getSetCode() + ":" + ci.getCardNumber());
        }
        System.out.println("VANILLA_CREATURES=" + best.size());
        for (Map.Entry<String,String> e : best.entrySet()) {
            System.out.println("V|" + e.getKey() + "|" + e.getValue());
        }
    }
}
