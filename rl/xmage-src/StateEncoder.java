package org.mage.test.benchmark.rl;

import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.stack.StackObject;
import mage.MageObject;
import mage.game.permanent.Permanent;
import mage.players.Player;

import mage.target.Target;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * E0 feature encoder: fixed-size hand-rolled vectors, one allocation-light
 * pass. This is the CONTROL encoder of the ablation ladder - card identity
 * is a 16-bucket stable name hash, adequate for a fixed 10-card pool and
 * deliberately unable to generalize (that is E1/E2's job).
 */
public final class StateEncoder {

    /**
     * Encoder version, -Drl.encoderV (default 2).
     *
     *   v1  the original: 24 state dims, no combat channels, no stack
     *       contents, and forBlock == forCombat. This is what every
     *       checkpoint before August 2026 was trained against, so it is
     *       the ONLY way to load them.
     *   v2  adds combat and stack state (s[24..31]) and block context
     *       (c[17..24]); see encodeState and forBlock.
     *   v3  v2 with the controller-blind combat channels fixed.
     *   v4  v3 state, but blocks become ONE joint decision per combat
     *       over complete assignments described by their simulated
     *       OUTCOME (see forAssignment). Sequential conditioning can fix
     *       over-piling and provably cannot fix under-committing - a
     *       blocker cannot condition on a decision not yet made - so the
     *       decomposition itself has to go.
     *   v5  v4 plus the SAME move on the attack side: one joint decision
     *       per combat over attack SUBSETS, each described by its value
     *       under a best-replying defender (see forAttackSet).
     *       selectAttackers carried the original per-creature bug
     *       untouched through v1-v4 - declaring an attacker taps nothing
     *       encodeState reads and changes no life total, so creature 2's
     *       observation was byte-identical to creature 1's.
     *
     * Deliberately NOT a compile-time constant. javac inlines
     * `static final int X = 32` into every caller, so the previous
     * version had SocketPolicyClient still sending the old width in its
     * handshake after a rebuild. Reading a property at class-init also
     * means A0 and A1 arms of an encoder A/B run from ONE build, which
     * is what makes the comparison clean.
     */
    public static final int ENCODER_V = Integer.getInteger("rl.encoderV", 2);
    public static final int STATE_DIM = ENCODER_V == 1 ? 24 : 32;
    private static final int ID_BASE = ENCODER_V == 1 ? 22 : 25;

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

        if (ENCODER_V == 1) {
            return s;              // v1 stops here, exactly as trained
        }

        // ---- COMBAT, s[24..28] ------------------------------------------
        // Nothing above this line reads game.getCombat(). That is why a
        // rung-0 agent piled four blockers onto one attacker and let four
        // others through: declaring a block taps nothing and changes no
        // life total or creature count, so the observation for the 2nd,
        // 3rd and 4th blocker in a combat was IDENTICAL to the 1st. Greedy
        // argmax on an identical observation returns an identical choice.
        // The only channel that could have distinguished them was the LSTM
        // hidden state, which had no explicit signal to learn from.
        // v3 FIX. This loop had no controller check, so during the
        // agent's OWN combat its own attackers were counted as incoming
        // damage and s[27] read "my life after my own attack" - an
        // explicit anti-attack signal. Only count attackers the agent
        // does NOT control; on its own turn the channels go to zero,
        // which is the truthful reading of "nothing is attacking me".
        int attackers = 0, unblocked = 0, unblockedPower = 0;
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID atkId : g.getAttackers()) {
                Permanent atk = game.getPermanent(atkId);
                if (atk == null || me.equals(atk.getControllerId())) {
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

    /**
     * A COMPLETE block assignment, described by what it does rather than
     * by which cards it uses. The policy never sees the assignment - only
     * its consequences - which is the afterstate formulation and the
     * reason this is learnable: no combat arithmetic has to be inferred
     * from stat lines.
     *
     * Reuses the T_BLOCK type slot and the card-feature region 6..16,
     * which carry mana value / power / toughness / card flags for
     * single-card candidates and are meaningless for an assignment.
     * CAND_DIM is unchanged.
     */
    public static float[] forAssignment(CombatMath.Outcome o, int blockersUsed,
                                        int myLife) {
        float[] c = blank(T_BLOCK);
        c[6] = o.damageTaken / 20f;
        c[7] = o.attackersKilled / 6f;
        c[8] = o.attackerValueKilled / 20f;
        c[9] = o.blockersLost / 6f;
        c[10] = o.blockerValueLost / 20f;
        c[11] = o.defenderDies ? 1f : 0f;
        c[12] = blockersUsed / 6f;
        c[13] = (myLife - o.damageTaken) / 20f;
        return c;
    }

    /**
     * A COMPLETE attack subset, described by what the defender's best
     * reply does to it. The attack-side twin of forAssignment, and the
     * same afterstate argument applies: the policy never sees which
     * cards are in the subset, only its consequences.
     *
     * WHAT IS HERE THAT forAssignment DOES NOT NEED. A block assignment
     * has no cost outside the combat it resolves; an attack does, because
     * an attacking creature is tapped through the opponent's whole next
     * turn. So c[14..18] carry what is LEFT AT HOME and what swings back
     * at it. Nothing in the terminal reward points at those channels
     * specifically - they are facts about the afterstate, offered
     * because the alternative is that the cost of attacking is invisible
     * in the candidate the way blocker count is invisible in c[12].
     *
     * Reuses the T_ATTACK type slot and slots 6..18. Those carry
     * mana value / power / toughness / block context for single-card
     * candidates and are meaningless for a subset; a subset candidate
     * never shares a candidate list with a card candidate. CAND_DIM is
     * unchanged, so v4 checkpoints still LOAD - but the MEANING of a
     * T_ATTACK candidate has changed, so a v4-trained net driven through
     * this path is out of distribution and its answers carry no claim.
     */
    public static float[] forAttackSet(CombatMath.AttackOption op,
                                       int myLife, int oppLife) {
        float[] c = blank(T_ATTACK);
        CombatMath.Outcome o = op.outcome;
        c[6] = o.damageTaken / 20f;              // damage DEALT
        c[7] = o.blockersLost / 6f;              // THEIR creatures killed
        c[8] = o.blockerValueLost / 20f;
        c[9] = o.attackersKilled / 6f;           // MY creatures lost
        c[10] = o.attackerValueKilled / 20f;
        c[11] = o.defenderDies ? 1f : 0f;        // lethal this combat
        c[12] = op.attackersUsed / 6f;
        c[13] = (oppLife - o.damageTaken) / 20f;
        c[14] = op.retainedBodies / 6f;          // left untapped to block
        c[15] = op.retainedPower / 20f;
        c[16] = op.retainedToughness / 20f;
        c[17] = op.crackBack / 20f;              // unabsorbed swing back
        c[18] = (myLife - op.crackBack) / 20f;   // my life after it
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
        if (ENCODER_V == 1) {
            return c;              // v1 saw the attacker and nothing else
        }
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

    // =================================================================
    // v6: ENTITY TOKENS + RELATIONS  (ENCODER-V6-BUILD.md §1, §2, §4a)
    //
    // encodeState above compresses a battlefield into six scalars -
    // count, total power, total toughness, per side. ATTACK-JOINT-RESULT
    // §6c measured what that costs: 86% of three-creature boards and 97%
    // of five-creature boards share an encoding with a DIFFERENT board.
    // v6 replaces those six scalars with one token per card plus a typed
    // edge list, and leaves the candidate path untouched.
    //
    // The emission order does NOT matter to the pooled embedding - the
    // server sum-pools, and rl/entattn_check.py measures the invariance -
    // but it must be DETERMINISTIC, because the relation edge list
    // indexes into it and a replay has to reproduce it.
    // =================================================================

    public static final int GDIM = 16, EDIM = 48;

    /** §1's zone one-hot, idx 3..7 of the entity token. */
    private static final int Z_BATTLEFIELD = 3, Z_HAND = 4, Z_STACK = 5,
            Z_GRAVE = 6, Z_PLAYER = 7;

    /**
     * Entity buffer. A BUFFER, not a meaning: the server pads and masks,
     * so raising it changes no weights and no checkpoint.
     *
     * MEASURED, not chosen. The build plan guessed 24; 40 rung-0 games
     * (13.6 turns avg) overflowed it on 23.6% of consults with a
     * largest board of 45, so it went to 48. Then 20 v6-vs-v5 mirror
     * games (50.6 turns avg, 11 of 20 hitting the turn cap) reached
     * boards of 75 and overflowed 48 on 43% of consults. Long games
     * build boards short ones never reach, so the buffer is sized for
     * the stalls: 96. entityTrunc below keeps measuring it.
     */
    public static final int EMAX = Integer.getInteger("rl.entityMax", 96);

    /** §2's relation vocabulary. THE INDEX IS THE CONTRACT with
     *  policy_server.py's RTYPES; append only, never reorder. */
    public static final int R_BLOCKS = 0, R_BLOCKED_BY = 1,
            R_ATTACKING_PLAYER = 2, R_TARGETS = 3, R_CONTROLS = 4,
            R_ATTACHED_TO = 5;
    public static final int RTYPES = 6;

    /** Emission counters, reported by the driver. entityTrunc is the one
     *  that matters: it is the number of consults that had more entities
     *  than EMAX slots, i.e. board state the agent could not see. Silent
     *  truncation is how an encoder starts measuring its own limit. */
    public static long entityConsults = 0, entityTrunc = 0, entityDropped = 0;
    public static long entityUnknown = 0, entityMaxSeen = 0;

    /** Columns of the e2 feature table (rl/e2_features.tsv), so the
     *  fourteen combat keywords have ONE definition in this codebase.
     *  Order matches §1 idx 24..37; -1 = no column exists.
     *  INDESTRUCTIBLE has no column in e2_extract.py's KEYWORDS list, so
     *  its slot is always 0. Adding it would change FEAT_DIM, hence
     *  CAND_DIM, hence every checkpoint - it is a rung-4+ decision, not
     *  one to make in passing. Rungs 0-3 have no indestructible. */
    private static final int[] KW_COL = {
        29,   // flying
        39,   // reach
        33,   // first strike
        34,   // double strike
        31,   // deathtouch
        35,   // trample
        36,   // vigilance
        38,   // menace
        40,   // defender
        32,   // lifelink
        -1,   // indestructible - no column, see above
        41,   // ward
        42,   // hexproof
        44,   // protection
    };
    private static final int KW_BASE = 24;
    private static final int TGT_CREATURE_COL = 56, TGT_PLAYER_COL = 57,
            TGT_SPELL_COL = 58;

    /** globals + entity rows + edge list, built in ONE pass so the edge
     *  indices cannot drift from the token order (§4a). */
    public static final class EntityView {
        public final float[] globals;
        public final float[][] entities;
        public final int[][] relations;
        /** opponent-hand rows, CRITIC ONLY. Empty unless -Drl.oracle.
         *  Never merged into `entities` - see patch_oracle.py. */
        public final float[][] oracle;

        EntityView(float[] g, float[][] e, int[][] r) {
            this(g, e, r, EMPTY);
        }

        EntityView(float[] g, float[][] e, int[][] r, float[][] o) {
            globals = g;
            entities = e;
            relations = r;
            oracle = o;
        }
    }

    private static final float[][] EMPTY = new float[0][];

    /** One emitted slot, with its sort keys. */
    private static final class Ent {
        int group;              // priority band, see encodeEntityView
        int power, tough, mv;
        long tiebreak;          // createOrder for permanents, else 0
        String name;            // last-resort tiebreak only
        float[] row;
        UUID id;
    }

    private static final Comparator<Ent> ORDER = Comparator
            .comparingInt((Ent e) -> e.group)
            .thenComparing(Comparator.comparingInt((Ent e) -> -e.power))
            .thenComparing(Comparator.comparingInt((Ent e) -> -e.tough))
            .thenComparing(Comparator.comparingInt((Ent e) -> -e.mv))
            // createOrder is a stable non-name tiebreak (§4a) and is
            // reproducible across replays; UUIDs are not (they come from
            // SecureRandom, not the seeded stream). Name is the final
            // fallback for zone cards, which have no createOrder. None
            // of it is observable: the pool is a SUM.
            .thenComparing(Comparator.comparingLong((Ent e) -> e.tiebreak))
            .thenComparing(e -> e.name);

    public static EntityView encodeEntityView(Game game, UUID me, UUID opp) {
        Player my = game.getPlayer(me);
        Player op = game.getPlayer(opp);
        List<Ent> ents = new ArrayList<>();

        // Priority bands. Truncation drops from the BOTTOM, so the two
        // player tokens and the creatures - what every combat decision
        // turns on - survive a board that overflows the buffer.
        //   0 players | 1 my creatures | 2 their creatures | 3 stack
        //   4 lands & other permanents | 5 my hand | 6 graveyards
        int myLands = 0, myUntapped = 0, opLands = 0, opUntapped = 0;
        for (Permanent p : game.getBattlefield().getAllPermanents()) {
            if (p.isLand(game)) {
                if (p.getControllerId().equals(me)) {
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
        }
        ents.add(playerEnt(me, my, true, myLands, myUntapped));
        ents.add(playerEnt(opp, op, false, opLands, opUntapped));
        for (Permanent p : game.getBattlefield().getAllPermanents()) {
            boolean mine = p.getControllerId().equals(me);
            int group = p.isCreature(game) ? (mine ? 1 : 2) : 4;
            ents.add(permEnt(p, game, me, mine ? opp : me, group));
        }
        int depth = 0;
        for (StackObject so : game.getStack()) {
            ents.add(stackEnt(so, game, me, depth++));
        }
        for (Card c : my.getHand().getCards(game)) {
            ents.add(cardEnt(c, game, true, Z_HAND, 5));
        }
        for (Card c : my.getGraveyard().getCards(game)) {
            ents.add(cardEnt(c, game, true, Z_GRAVE, 6));
        }
        for (Card c : op.getGraveyard().getCards(game)) {
            ents.add(cardEnt(c, game, false, Z_GRAVE, 6));
        }

        ents.sort(ORDER);
        entityConsults++;
        entityMaxSeen = Math.max(entityMaxSeen, ents.size());
        if (ents.size() > EMAX) {
            entityTrunc++;
            entityDropped += ents.size() - EMAX;
            ents = ents.subList(0, EMAX);
        }
        Map<UUID, Integer> index = new HashMap<>();
        float[][] rows = new float[ents.size()][];
        for (int i = 0; i < ents.size(); i++) {
            rows[i] = ents.get(i).row;
            index.put(ents.get(i).id, i);
        }
        float[][] oracleRows = EMPTY;
        if (ORACLE) {
            List<Ent> oe = new ArrayList<>();
            for (Card c : op.getHand().getCards(game)) {
                oe.add(cardEnt(c, game, false, Z_HAND, 5));
            }
            oe.sort(ORDER);
            if (oe.size() > EMAX) {
                oe = oe.subList(0, EMAX);
            }
            oracleRows = new float[oe.size()][];
            for (int i = 0; i < oe.size(); i++) {
                oracleRows[i] = oe.get(i).row;
            }
        }
        EntityView view = new EntityView(encodeGlobals(game, me, opp), rows,
                relations(game, me, opp, index), oracleRows);
        if (DUMP != null) {
            dump(view, game, me, opp);
        }
        return view;
    }

    /**
     * -Drl.entityDump=&lt;file&gt;: one JSON line per consult, carrying the
     * v6 view AND the v5 state vector for the same position.
     *
     * This is what makes §5b's collision gate a measurement on REAL
     * emission rather than on constructed rows: group the dumped
     * positions by their v5 vector - positions that are byte-identical
     * to the old encoder - and ask whether v6 tells them apart. A
     * synthetic board cannot answer that, because the question is about
     * what the game actually produces.
     */
    private static final boolean DEBUG_UNKNOWN = Boolean.getBoolean("rl.debug");
    private static final java.util.Set<String> UNKNOWN_SEEN =
            java.util.Collections.synchronizedSet(new java.util.HashSet<>());

    /** -Drl.oracle=true: also emit the opponent's hand, for the
     *  CRITIC ONLY. Class-init like every other rl.* constant, so a
     *  driver JVM that served one arm cannot serve the other. */
    public static final boolean ORACLE = Boolean.getBoolean("rl.oracle");

    private static final String DUMP = System.getProperty("rl.entityDump");
    private static java.io.PrintWriter dumpOut;

    private static synchronized void dump(EntityView v, Game game, UUID me,
                                          UUID opp) {
        try {
            if (dumpOut == null) {
                dumpOut = new java.io.PrintWriter(new java.io.BufferedWriter(
                        new java.io.FileWriter(DUMP, true)));
                Runtime.getRuntime().addShutdownHook(
                        new Thread(() -> dumpOut.flush()));
            }
            StringBuilder b = new StringBuilder(1 << 12);
            b.append("{\"g\":").append(arr(v.globals)).append(",\"e\":[");
            for (int i = 0; i < v.entities.length; i++) {
                b.append(i > 0 ? "," : "").append(arr(v.entities[i]));
            }
            b.append("],\"r\":[");
            for (int i = 0; i < v.relations.length; i++) {
                int[] e = v.relations[i];
                b.append(i > 0 ? "," : "").append('[').append(e[0]).append(',')
                        .append(e[1]).append(',').append(e[2]).append(']');
            }
            // the v5 vector for the SAME position: the collision gate
            // groups on this, so it has to come from the same call
            b.append("],\"v5\":").append(arr(encodeStateV5(game, me, opp)))
                    .append('}');
            dumpOut.println(b);
            // flush per line: the driver JVM is persistent, so a
            // buffered tail sits unwritten while the gate is already
            // reading the file and trips over a half-written line
            dumpOut.flush();
        } catch (java.io.IOException e) {
            throw new IllegalStateException("rl.entityDump failed: " + DUMP, e);
        }
    }

    /** encodeState's v2-v5 body, callable while ENCODER_V is 6. */
    private static float[] encodeStateV5(Game game, UUID me, UUID opp) {
        return encodeState(game, me, opp);
    }

    private static String arr(float[] v) {
        StringBuilder b = new StringBuilder(v.length * 7 + 2);
        b.append('[');
        for (int i = 0; i < v.length; i++) {
            b.append(i > 0 ? "," : "")
                    .append(String.format(java.util.Locale.ROOT, "%.4f", v[i]));
        }
        return b.append(']').toString();
    }

    private static int[][] relations(Game game, UUID me, UUID opp,
                                     Map<UUID, Integer> index) {
        List<int[]> out = new ArrayList<>();
        // controls: player token -> permanent
        for (Permanent p : game.getBattlefield().getAllPermanents()) {
            edge(out, index, p.getControllerId(), p.getId(), R_CONTROLS);
            // attached_to: aura/equipment -> creature (empty at rung 0-3)
            if (p.getAttachedTo() != null) {
                edge(out, index, p.getId(), p.getAttachedTo(), R_ATTACHED_TO);
            }
        }
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID atk : g.getAttackers()) {
                // attacking_player: attacker -> the player token it is
                // attacking. The defender of a group is a player here
                // (no planeswalkers at any rung built so far); if it is
                // not an emitted entity the edge is simply dropped.
                edge(out, index, atk, g.getDefenderId(), R_ATTACKING_PLAYER);
                for (UUID blk : g.getBlockers()) {
                    // typed BOTH ways on purpose: the server's bias is
                    // directed, so blocks and blocked_by are different
                    // facts and get different types (§2)
                    edge(out, index, blk, atk, R_BLOCKS);
                    edge(out, index, atk, blk, R_BLOCKED_BY);
                }
            }
        }
        for (StackObject so : game.getStack()) {
            if (so.getStackAbility() == null) {
                continue;
            }
            for (Target t : so.getStackAbility().getTargets()) {
                for (UUID tid : t.getTargets()) {
                    edge(out, index, so.getId(), tid, R_TARGETS);
                }
            }
        }
        return out.toArray(new int[0][]);
    }

    /** Appends the edge only if BOTH endpoints were emitted. An edge
     *  into a truncated slot is not "close enough": the server rejects
     *  out-of-range indices precisely because that is how an edge list
     *  and a token order drift apart unnoticed. */
    private static void edge(List<int[]> out, Map<UUID, Integer> index,
                             UUID src, UUID dst, int type) {
        Integer s = index.get(src);
        Integer d = index.get(dst);
        if (s != null && d != null) {
            out.add(new int[]{s, d, type});
        }
    }

    public static float[] encodeGlobals(Game game, UUID me, UUID opp) {
        Player my = game.getPlayer(me);
        Player op = game.getPlayer(opp);
        float[] g = new float[GDIM];
        g[0] = game.getTurnNum() / 30f;
        g[1] = me.equals(game.getActivePlayerId()) ? 1f : 0f;
        PhaseStep st = game.getTurnStepType();
        if (st == PhaseStep.PRECOMBAT_MAIN || st == PhaseStep.POSTCOMBAT_MAIN) {
            g[2] = 1f;
        } else if (st == PhaseStep.DECLARE_ATTACKERS) {
            g[3] = 1f;
        } else if (st == PhaseStep.DECLARE_BLOCKERS) {
            g[4] = 1f;
        } else if (st == PhaseStep.BEGIN_COMBAT || st == PhaseStep.COMBAT_DAMAGE
                || st == PhaseStep.FIRST_COMBAT_DAMAGE || st == PhaseStep.END_COMBAT) {
            g[5] = 1f;
        } else if (st == PhaseStep.END_TURN) {
            g[6] = 1f;
        } else {
            g[7] = 1f;
        }
        g[8] = my.getLife() / 20f;
        g[9] = op.getLife() / 20f;
        g[10] = my.getLibrary().size() / 60f;
        g[11] = my.getGraveyard().size() / 30f;
        g[12] = op.getGraveyard().size() / 30f;
        g[13] = game.getStack().size() / 3f;
        g[14] = op.getHand().size() / 10f;   // theirs is a COUNT; mine are tokens
        g[15] = 0f;                          // consult budget remaining, set by RLPlayer
        return g;
    }

    private static Ent playerEnt(UUID id, Player pl, boolean mine,
                                 int lands, int untapped) {
        Ent e = new Ent();
        e.group = 0;
        e.id = id;
        e.name = mine ? " me" : " opp";
        float[] r = new float[EDIM];
        r[0] = 1f;
        r[mine ? 1 : 2] = 1f;
        r[Z_PLAYER] = 1f;
        r[44] = pl.getLife() / 20f;
        r[45] = pl.getHand().size() / 10f;
        r[46] = lands / 10f;
        r[47] = untapped / 10f;
        e.row = r;
        return e;
    }

    private static Ent permEnt(Permanent p, Game game, UUID me, UUID defender,
                               int group) {
        Ent e = new Ent();
        e.group = group;
        e.id = p.getId();
        e.name = p.getName();
        e.tiebreak = p.getCreateOrder();
        int pw = p.getPower().getValue();
        int to = p.getToughness().getValue();
        int dmg = p.getDamage();
        e.power = pw;
        e.tough = to;
        e.mv = p.getManaValue();
        float[] r = new float[EDIM];
        r[0] = 1f;
        r[p.getControllerId().equals(me) ? 1 : 2] = 1f;
        r[Z_BATTLEFIELD] = 1f;
        r[8] = pw / 6f;
        r[9] = to / 6f;
        // DAMAGE MARKED is invisible to encodeState and decides every
        // combat: a 3/3 with 2 damage blocks nothing like a fresh 3/3
        r[10] = dmg / 6f;
        r[11] = (to - dmg) / 6f;
        r[12] = p.isCreature(game) ? 1f : 0f;
        r[13] = p.isLand(game) ? 1f : 0f;
        r[14] = (!p.isCreature(game) && !p.isLand(game)) ? 1f : 0f;
        r[15] = p.getManaValue() / 6f;
        r[16] = p.isTapped() ? 1f : 0f;
        r[17] = p.hasSummoningSickness() ? 1f : 0f;
        r[18] = p.isAttacking() ? 1f : 0f;
        r[19] = p.getBlocking() > 0 ? 1f : 0f;
        r[20] = p.canAttack(defender, game) ? 1f : 0f;
        r[21] = p.canBlockAny(game) ? 1f : 0f;
        r[22] = p.getTurnsOnBattlefield() == 0 ? 1f : 0f;
        r[23] = (p instanceof mage.game.permanent.PermanentToken) ? 1f : 0f;
        keywords(p.getName(), r);
        e.row = r;
        return e;
    }

    private static Ent cardEnt(Card c, Game game, boolean mine, int zone,
                               int group) {
        Ent e = new Ent();
        e.group = group;
        e.id = c.getId();
        e.name = c.getName();
        e.power = c.getPower().getValue();
        e.tough = c.getToughness().getValue();
        e.mv = c.getManaValue();
        float[] r = new float[EDIM];
        r[0] = 1f;
        r[mine ? 1 : 2] = 1f;
        r[zone] = 1f;
        r[8] = e.power / 6f;
        r[9] = e.tough / 6f;
        r[11] = e.tough / 6f;                 // nothing is damaged off-board
        r[12] = c.isCreature(game) ? 1f : 0f;
        r[13] = c.isLand(game) ? 1f : 0f;
        r[15] = e.mv / 6f;
        keywords(c.getName(), r);
        e.row = r;
        return e;
    }

    private static Ent stackEnt(StackObject so, Game game, UUID me, int depth) {
        Ent e = new Ent();
        e.group = 3;
        e.id = so.getId();
        e.name = so.getName() == null ? "?" : so.getName();
        e.mv = so.getStackAbility() == null ? 0
                : so.getStackAbility().getManaCosts().manaValue();
        float[] r = new float[EDIM];
        r[0] = 1f;
        r[me.equals(so.getControllerId()) ? 1 : 2] = 1f;
        r[Z_STACK] = 1f;
        r[15] = e.mv / 6f;
        r[38] = depth / 4f;
        r[39] = so.isInstant(game) ? 1f : 0f;
        r[40] = so.isSorcery(game) ? 1f : 0f;
        // Look the features up by the SOURCE CARD, not by the stack
        // object's name. A triggered ability's getName() is its rule
        // text - "stack ability (When {this} enters, create a Map
        // token.)" - which is never in a card table, so every trigger
        // counted as an unknown card AND lost the keyword bits of the
        // permanent that produced it. On BenchDimir that read
        // entityUnknown=64289 in ten games and looked like the whole
        // deck was missing; it was triggers and one token.
        Card src = game.getCard(so.getSourceId());
        keywords(src != null ? src.getName() : e.name, r);
        e.row = r;
        return e;
    }

    /** §1's rows 24-37 and 41-43, by INDEXING the e2 table rather than
     *  re-deriving them: there is one definition of "deathtouch" in this
     *  codebase and it lives in e2_extract.py. */
    private static void keywords(String name, float[] r) {
        if (CARD_FEATURES == null) {
            return;                  // E0 arm: no table, no keyword bits
        }
        float[] v = CARD_FEATURES.get(name);
        if (v == null) {
            entityUnknown++;
            // -Drl.debug: name each MISSING card once. "64289 unknown
            // lookups" is unactionable; a list of names says whether the
            // table is missing tokens, split cards, or the whole deck.
            if (DEBUG_UNKNOWN && UNKNOWN_SEEN.size() < 40
                    && UNKNOWN_SEEN.add(name)) {
                System.out.println("RL|entityUnknownName|" + name);
            }
            // No unknown-card FLAG: v1's 48 dims have no free slot and
            // widening EDIM would break the handshake mid-ladder. The
            // count is reported instead, and the E2-116 extension (§1)
            // is where the flag belongs when rung 4+ needs it.
            return;
        }
        for (int i = 0; i < KW_COL.length; i++) {
            if (KW_COL[i] >= 0 && KW_COL[i] < v.length) {
                r[KW_BASE + i] = v[KW_COL[i]];
            }
        }
        if (TGT_SPELL_COL < v.length) {
            r[41] = v[TGT_CREATURE_COL];
            r[42] = v[TGT_PLAYER_COL];
            r[43] = v[TGT_SPELL_COL];
        }
    }
}
