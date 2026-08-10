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
 */
public final class StateEncoder {

    public static final int STATE_DIM = 24;
    public static final int CAND_DIM = 38;
    private static final int ID_BASE = 22;   // 16 identity buckets from here

    private StateEncoder() {
    }

    public static float[] encodeState(Game game, UUID me, UUID opp) {
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
        return s;
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
            identity(c, card.getName());
        }
        return c;
    }

    public static float[] forTargetPlayer(boolean isMe, int life) {
        float[] c = blank(T_TARGET);
        c[isMe ? 12 : 13] = 1f;
        c[15] = life / 20f;
        return c;
    }

    public static float[] forTargetPermanent(Permanent p, Game game, UUID me) {
        float[] c = blank(T_TARGET);
        c[14] = p.isCreature(game) ? 1f : 0f;
        c[15] = p.getPower().getValue() / 6f;
        c[16] = p.getToughness().getValue() / 6f;
        c[12] = p.getControllerId().equals(me) ? 1f : 0f;
        identity(c, p.getName());
        return c;
    }

    public static float[] forCombat(int type, Permanent creature, Game game) {
        float[] c = blank(type);
        c[7] = creature.getPower().getValue() / 6f;
        c[8] = creature.getToughness().getValue() / 6f;
        c[9] = 1f;
        identity(c, creature.getName());
        return c;
    }

    private static void identity(float[] c, String name) {
        c[ID_BASE + Math.floorMod(name.hashCode(), 16)] = 1f;
    }
}
