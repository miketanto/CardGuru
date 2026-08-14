package org.mage.test.benchmark.rl;

import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.stack.StackObject;
import mage.MageObject;
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

    // 24 -> 32. The first 24 are unchanged and in the same order, so the
    // diff to a prior net is purely additive - but the input width moves,
    // so checkpoints trained at sdim=24 cannot be loaded. See the combat
    // and stack blocks at the end of encodeState for why this was worth
    // breaking compatibility for.
    public static final int STATE_DIM = 32;
    // 22 -> 25: three more block-context slots ahead of the identity
    // block (see forBlock). CAND_DIM grows with it, which is a second
    // compatibility break - taken in the same commit as the sdim change
    // rather than as a separate one later.
    private static final int ID_BASE = 25;   // identity features from here

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

        // ---- COMBAT, s[24..28] ------------------------------------------
        // Nothing above this line reads game.getCombat(). That is why a
        // rung-0 agent piled four blockers onto one attacker and let four
        // others through: declaring a block taps nothing and changes no
        // life total or creature count, so the observation for the 2nd,
        // 3rd and 4th blocker in a combat was IDENTICAL to the 1st. Greedy
        // argmax on an identical observation returns an identical choice.
        // The only channel that could have distinguished them was the LSTM
        // hidden state, which had no explicit signal to learn from.
        int attackers = 0, unblocked = 0, unblockedPower = 0;
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID atkId : g.getAttackers()) {
                Permanent atk = game.getPermanent(atkId);
                if (atk == null) {
                    continue;
                }
                attackers++;
                if (g.getBlockers().isEmpty()) {
                    unblocked++;
                    unblockedPower += atk.getPower().getValue();
                }
            }
        }
        int freeBlockers = 0;
        for (Permanent p : game.getBattlefield().getAllActivePermanents(me)) {
            if (p.isCreature(game) && !p.isTapped()) {
                freeBlockers++;
            }
        }
        s[24] = attackers / 6f;
        s[25] = unblocked / 6f;
        s[26] = unblockedPower / 20f;
        // life AFTER the currently-unblocked attackers connect: negative
        // means dead on board unless something else blocks, which is the
        // single fact the t26 loss turned on
        s[27] = (my.getLife() - unblockedPower) / 20f;
        s[28] = freeBlockers / 6f;

        // ---- STACK, s[29..31] -------------------------------------------
        // s[20] carries only the DEPTH. Order and contents were invisible:
        // a Lightning Bolt and a Wrath of God on the stack looked the same,
        // and so did mine and theirs. Rungs 0-3 have no instants so this
        // costs nothing there, but rung 4 (instant removal) and rung 5
        // (combat tricks) are exactly the rungs that need it.
        if (!game.getStack().isEmpty()) {
            StackObject top = game.getStack().getFirst();
            s[29] = me.equals(top.getControllerId()) ? 1f : 0f;
            s[30] = top.getStackAbility() == null ? 0f
                    : top.getStackAbility().getManaCosts().manaValue() / 6f;
            // StackObject extends MageObject, so isInstant is available
            // directly - there is no getStackObject() accessor
            s[31] = top.isInstant(game) ? 1f : 0f;
        }
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

    /**
     * "Block this attacker with THIS blocker."
     *
     * forCombat carries only the attacker, so the candidate for blocking a
     * 3/3 looked the same whether the blocker was a 2/4 that survives or a
     * 3/1 that trades down - and it said nothing about how many blockers
     * were already on that attacker. Slots 17-21 were unused, so this adds
     * the missing context WITHOUT changing CAND_DIM: only the state width
     * moves, and only once.
     */
    public static float[] forBlock(Permanent attacker, Permanent blocker,
                                   Game game) {
        float[] c = forCombat(T_BLOCK, attacker, game);
        int already = 0, assignedPower = 0, assignedTough = 0;
        for (CombatGroup g : game.getCombat().getGroups()) {
            if (!g.getAttackers().contains(attacker.getId())) {
                continue;
            }
            already += g.getBlockers().size();
            for (UUID bId : g.getBlockers()) {
                Permanent b = game.getPermanent(bId);
                if (b != null) {
                    assignedPower += b.getPower().getValue();
                    assignedTough += b.getToughness().getValue();
                }
            }
        }
        int ap = attacker.getPower().getValue();
        int at = attacker.getToughness().getValue();
        int bp = blocker.getPower().getValue();
        int bt = blocker.getToughness().getValue();
        c[17] = already / 3f;              // piling signal
        c[18] = bp / 6f;                   // the blocker's own body
        c[19] = bt / 6f;
        c[20] = bp >= at ? 1f : 0f;        // this block kills the attacker
        c[21] = ap >= bt ? 1f : 0f;        // this block loses the blocker
        // A COUNT of prior blockers is not enough. Three 2/4s already on a
        // 3/3 have killed it six times over, and a fourth blocker is pure
        // waste - but "already = 3" reads the same as three 0/1s, which
        // have not killed it at all. What decides the question is the
        // power and toughness already committed, so encode that.
        c[22] = Math.min(1f, assignedPower / (float) Math.max(1, at));
        c[23] = assignedPower >= at ? 1f : 0f;   // attacker ALREADY dead
        c[24] = assignedTough >= ap ? 1f : 0f;   // its damage already eaten
        return c;
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
