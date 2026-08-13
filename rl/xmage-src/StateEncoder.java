package org.mage.test.benchmark.rl;

import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;

import java.util.UUID;

/**
 * E0 feature encoder: fixed-size hand-rolled vectors, one allocation-light
 * pass. This is the CONTROL encoder of the ablation ladder - card identity
 * is a 16-bucket stable name hash, adequate for a fixed 10-card pool and
 * deliberately unable to generalize (that is E1/E2's job).
 *
 * E3 (CHECKPOINT-PHASE10.md 4.3) adds two hand-built groups on top:
 *   - STATE dims 24-28: card-advantage visibility. Known top-of-library
 *     after surveil/scry/explore (the agent filters its own draw and then
 *     cannot see the result - Kaito-0 is never activated) plus the hand
 *     differential, which is the card-advantage scoreboard s[2]/s[3] only
 *     imply.
 *   - CANDIDATE dims 17-21: the colored-pip STRUCTURE of a cast. c[6]
 *     carries generic mana value only, so {U}{U} and {2}{U} are the same
 *     candidate - the distinction that decides what to hold open. These
 *     land in the five slots left free between the type/stat block and
 *     ID_BASE, so CAND_DIM does not move for the pip group.
 */
public final class StateEncoder {

    public static final int STATE_DIM = 29;
    /** s[24]: "I know what my next draw is" (E3 group 1) - exported so
     *  the seat can report how often the new visibility is live. */
    public static final int S_KNOWN_TOP = 24;
    private static final int ID_BASE = 22;   // identity features from here

    /**
     * E2 support: -Drl.cardFeatures=<file> loads a per-card mechanical
     * feature table (TSV: first line = dim, then "name\tv1,v2,...").
     * When present, identity = the table vector plus a trailing
     * unknown-card flag; when absent, identity = the E0 16-bucket name
     * hash. CAND_DIM is therefore fixed at class load, and the hello
     * handshake carries it to the policy server.
     */
    private static final java.util.Map<String, float[]> CARD_FEATURES;
    private static final int FEAT_DIM;
    public static final int CAND_DIM;

    static {
        String path = System.getProperty("rl.cardFeatures");
        java.util.Map<String, float[]> table = null;
        int dim = 0;
        if (path != null && !path.trim().isEmpty()) {
            table = new java.util.HashMap<>();
            try (java.io.BufferedReader r = new java.io.BufferedReader(
                    new java.io.FileReader(path))) {
                dim = Integer.parseInt(r.readLine().trim());
                String line;
                while ((line = r.readLine()) != null) {
                    if (line.trim().isEmpty()) {
                        continue;
                    }
                    int tab = line.indexOf('\t');
                    String[] parts = line.substring(tab + 1).split(",");
                    if (parts.length != dim) {
                        throw new IllegalStateException("bad feature row: " + line);
                    }
                    float[] v = new float[dim];
                    for (int i = 0; i < dim; i++) {
                        v[i] = Float.parseFloat(parts[i]);
                    }
                    table.put(line.substring(0, tab), v);
                }
            } catch (java.io.IOException e) {
                throw new IllegalStateException("rl.cardFeatures load failed: " + path, e);
            }
            System.out.println("RL|cardFeatures|path=" + path
                    + "|cards=" + table.size() + "|dim=" + dim);
        }
        CARD_FEATURES = table;
        FEAT_DIM = dim;
        CAND_DIM = table == null ? ID_BASE + 16 : ID_BASE + dim + 1;
    }

    /**
     * Diagnostic ablation, the hand-built-dim analog of the Phase 8b
     * feature scramble (rl/p8b_scramble.py can only corrupt the TSV, and
     * the E3 state/pip dims are computed in Java): zero a set of dims at
     * eval time and see whether the policy's win rate moves.
     *   -Drl.ablateState=24-28   -Drl.ablateCand=17-21
     * Both default to empty, i.e. no ablation.
     */
    private static final boolean[] ABLATE_STATE = ablationMask(
            System.getProperty("rl.ablateState"), STATE_DIM);
    private static final boolean[] ABLATE_CAND = ablationMask(
            System.getProperty("rl.ablateCand"), CAND_DIM);

    private static boolean[] ablationMask(String spec, int dim) {
        if (spec == null || spec.trim().isEmpty()) {
            return null;
        }
        boolean[] mask = new boolean[dim];
        for (String part : spec.split(",")) {
            part = part.trim();
            if (part.isEmpty()) {
                continue;
            }
            int dash = part.indexOf('-');
            int lo = Integer.parseInt(dash < 0 ? part : part.substring(0, dash));
            int hi = dash < 0 ? lo : Integer.parseInt(part.substring(dash + 1));
            for (int i = lo; i <= hi && i < dim; i++) {
                mask[i] = true;
            }
        }
        System.out.println("RL|ablate|dim=" + dim + "|spec=" + spec);
        return mask;
    }

    private static float[] ablate(float[] v, boolean[] mask) {
        if (mask != null) {
            for (int i = 0; i < v.length; i++) {
                if (mask[i]) {
                    v[i] = 0f;
                }
            }
        }
        return v;
    }

    private StateEncoder() {
    }

    /**
     * What the seat has actually SEEN of its own library. Implemented by
     * RLPlayer, which records every card it was shown in a library-zone
     * choice (scry, surveil, explore, "look at the top N"); the encoder
     * only asks whether the card currently on top is one of them, so the
     * knowledge expires by itself the moment that card is drawn.
     */
    public interface LibraryKnowledge {
        boolean hasSeen(UUID cardId);
    }

    public static float[] encodeState(Game game, UUID me, UUID opp) {
        return encodeState(game, me, opp, null);
    }

    public static float[] encodeState(Game game, UUID me, UUID opp,
                                      LibraryKnowledge seen) {
        Player my = game.getPlayer(me);
        Player op = game.getPlayer(opp);
        float[] s = new float[STATE_DIM];
        s[0] = my.getLife() / 20f;
        s[1] = op.getLife() / 20f;
        s[2] = my.getHand().size() / 10f;
        s[3] = op.getHand().size() / 10f;
        int myLands = 0, myUntapped = 0, opLands = 0, opUntapped = 0;
        int myCre = 0, opCre = 0, myPow = 0, myTou = 0, opPow = 0, opTou = 0;
        for (Permanent p : game.getBattlefield().getAllPermanents()) {
            boolean mine = p.getControllerId().equals(me);
            if (p.isLand(game)) {
                if (mine) {
                    myLands++;
                    if (!p.isTapped()) {
                        myUntapped++;
                    }
                } else {
                    opLands++;
                    if (!p.isTapped()) {
                        opUntapped++;
                    }
                }
            }
            if (p.isCreature(game)) {
                int pw = p.getPower().getValue();
                int to = p.getToughness().getValue();
                if (mine) {
                    myCre++;
                    myPow += pw;
                    myTou += to;
                } else {
                    opCre++;
                    opPow += pw;
                    opTou += to;
                }
            }
        }
        s[4] = myUntapped / 10f;
        s[5] = myLands / 10f;
        s[6] = opUntapped / 10f;
        s[7] = opLands / 10f;
        s[8] = myCre / 10f;
        s[9] = opCre / 10f;
        s[10] = myPow / 20f;
        s[11] = myTou / 20f;
        s[12] = opPow / 20f;
        s[13] = opTou / 20f;
        s[14] = game.getTurnNum() / 30f;
        s[15] = me.equals(game.getActivePlayerId()) ? 1f : 0f;
        PhaseStep st = game.getTurnStepType();
        if (st == PhaseStep.PRECOMBAT_MAIN || st == PhaseStep.POSTCOMBAT_MAIN) {
            s[16] = 1f;
        } else if (st == PhaseStep.DECLARE_ATTACKERS || st == PhaseStep.DECLARE_BLOCKERS
                || st == PhaseStep.BEGIN_COMBAT || st == PhaseStep.COMBAT_DAMAGE
                || st == PhaseStep.FIRST_COMBAT_DAMAGE || st == PhaseStep.END_COMBAT) {
            s[17] = 1f;
        } else if (st == PhaseStep.END_TURN) {
            s[18] = 1f;
        } else {
            s[19] = 1f;
        }
        s[20] = game.getStack().size() / 3f;
        s[21] = my.getGraveyard().size() / 30f;
        s[22] = op.getGraveyard().size() / 30f;
        s[23] = my.getLibrary().size() / 60f;

        // E3 group 1 - card-advantage visibility
        if (seen != null) {
            Card top = my.getLibrary().getFromTop(game);
            if (top != null && seen.hasSeen(top.getId())) {
                s[24] = 1f;
                s[25] = top.isLand(game) ? 1f : 0f;
                s[26] = top.isCreature(game) ? 1f : 0f;
                s[27] = Math.min(top.getManaValue(), 6) / 6f;
            }
        }
        int handDiff = my.getHand().size() - op.getHand().size();
        s[28] = Math.max(-7, Math.min(7, handDiff)) / 7f;
        return ablate(s, ABLATE_STATE);
    }

    /** decision-type slots */
    public static final int T_PASS = 0, T_LAND = 1, T_SPELL = 2, T_TARGET = 3,
            T_ATTACK = 4, T_BLOCK = 5;

    public static float[] blank(int type) {
        float[] c = new float[CAND_DIM];
        c[type] = 1f;
        return c;
    }

    public static float[] forCard(int type, Card card, Game game) {
        float[] c = blank(type);
        if (card != null) {
            c[6] = card.getManaValue() / 6f;
            if (card.isCreature(game)) {
                c[7] = card.getPower().getValue() / 6f;
                c[8] = card.getToughness().getValue() / 6f;
                c[9] = 1f;
            }
            c[10] = card.isInstant(game) ? 1f : 0f;
            c[11] = card.isSorcery(game) ? 1f : 0f;
            pips(c, card);
            identity(c, card.getName());
        }
        return ablate(c, ABLATE_CAND);
    }

    /**
     * E3 group 3 - colored-pip structure of the printed cost, in the five
     * free candidate slots. c[6] (mana value) cannot tell {U}{U} from
     * {2}{U}, and the difference is the whole of hold-open-mana planning:
     * two blue sources vs one blue and any two.
     *
     *   c[17] generic portion        c[18] specific (colored) pips
     *   c[19] deepest single-colour requirement (the {U}{U} signal)
     *   c[20] distinct colours       c[21] flexible symbols (hybrid/X/phy)
     */
    private static void pips(float[] c, Card card) {
        int generic = 0, specific = 0, distinct = 0, deepest = 0;
        int[] perColor = new int[6];        // W U B R G C
        boolean flexible = false;
        for (String sym : card.getManaCostSymbols()) {
            String s = sym.replace("{", "").replace("}", "").trim();
            if (s.isEmpty()) {
                continue;
            }
            if (s.chars().allMatch(Character::isDigit)) {
                generic += Integer.parseInt(s);
            } else if (s.contains("/") || s.equalsIgnoreCase("X")
                    || s.equalsIgnoreCase("S")) {
                // hybrid, phyrexian, X, snow: a requirement the seat can
                // satisfy more than one way - counted, but not attributed
                flexible = true;
                if (!s.equalsIgnoreCase("X")) {
                    specific++;
                }
            } else {
                int idx = "WUBRGC".indexOf(Character.toUpperCase(s.charAt(0)));
                if (idx >= 0) {
                    specific++;
                    perColor[idx]++;
                }
            }
        }
        for (int n : perColor) {
            if (n > 0) {
                distinct++;
                deepest = Math.max(deepest, n);
            }
        }
        c[17] = Math.min(generic, 6) / 6f;
        c[18] = Math.min(specific, 4) / 4f;
        c[19] = Math.min(deepest, 3) / 3f;
        c[20] = Math.min(distinct, 3) / 3f;
        c[21] = flexible ? 1f : 0f;
    }

    public static float[] forTargetPlayer(boolean isMe, int life) {
        float[] c = blank(T_TARGET);
        c[isMe ? 12 : 13] = 1f;
        c[15] = life / 20f;
        return ablate(c, ABLATE_CAND);
    }

    public static float[] forTargetPermanent(Permanent p, Game game, UUID me) {
        float[] c = blank(T_TARGET);
        c[14] = p.isCreature(game) ? 1f : 0f;
        c[15] = p.getPower().getValue() / 6f;
        c[16] = p.getToughness().getValue() / 6f;
        c[12] = p.getControllerId().equals(me) ? 1f : 0f;
        identity(c, p.getName());
        return ablate(c, ABLATE_CAND);
    }

    public static float[] forCombat(int type, Permanent creature, Game game) {
        float[] c = blank(type);
        c[7] = creature.getPower().getValue() / 6f;
        c[8] = creature.getToughness().getValue() / 6f;
        c[9] = 1f;
        identity(c, creature.getName());
        return ablate(c, ABLATE_CAND);
    }

    private static void identity(float[] c, String name) {
        if (CARD_FEATURES == null) {
            c[ID_BASE + Math.floorMod(name.hashCode(), 16)] = 1f;
            return;
        }
        float[] v = CARD_FEATURES.get(name);
        if (v == null) {
            c[ID_BASE + FEAT_DIM] = 1f;   // unknown-card flag
            return;
        }
        System.arraycopy(v, 0, c, ID_BASE, FEAT_DIM);
    }
}
