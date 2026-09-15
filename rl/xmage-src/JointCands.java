package org.mage.test.benchmark.rl;

import mage.MageObject;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;

/**
 * Phase 13a: the joint attack / block candidate lists, lifted VERBATIM out
 * of RLPlayer.jointAttacks / jointBlocks (and attackChoiceSet /
 * theirBlockers) into package-static builders, so the CP7 teacher seat
 * (CP7TeacherPlayer) builds exactly the list the RL seat is offered and
 * its label indexes the same candidates. RLPlayer calls these builders
 * itself - one code path, no copy to drift. Fallback counters go through
 * the caller's Consumer (RLPlayer.countFallback; the teacher counts its
 * own). The consult, the declarations and the transcript stay in the
 * callers.
 */
final class JointCands {

    private JointCands() {
    }

    // ------------------------------------------------------------ attacks

    /** The defender's potential blockers: their untapped creatures.
     *  Vanilla scope, exactly as CombatMath documents - no evasion, so
     *  "untapped creature" and "can block this" are the same set. */
    static List<Permanent> theirBlockers(Game game, UUID defender) {
        List<Permanent> out = new ArrayList<>();
        if (defender == null) {
            return out;
        }
        for (Permanent p : game.getBattlefield().getAllActivePermanents(defender)) {
            if (p.isCreature(game) && !p.isTapped()) {
                out.add(p);
            }
        }
        out.sort(Comparator
                .comparingInt((Permanent p) -> p.getToughness().getValue())
                .thenComparingInt(p -> p.getPower().getValue())
                .thenComparing(MageObject::getName));
        return out;
    }

    /** Creatures the choice actually ranges over (rl.attackMaxCreatures;
     *  the biggest bodies; the remainder is forced to hold, counted). */
    static List<Permanent> attackChoiceSet(List<Permanent> avail, Consumer<String> fallback) {
        int maxA = Integer.getInteger("rl.attackMaxCreatures", 12);
        if (avail.size() <= maxA) {
            return avail;
        }
        fallback.accept("attackCreaturesCapped");
        List<Permanent> big = new ArrayList<>(avail);
        big.sort(Comparator.comparingInt(
                (Permanent p) -> -(p.getPower().getValue()
                        + p.getToughness().getValue())));
        return new ArrayList<>(big.subList(0, maxA));
    }

    /** The joint attack candidate list and what built it. */
    static final class Attack {
        List<Permanent> pick;
        List<Permanent> theirs;
        List<CombatMath.Body> mb;
        int oppLife;
        CombatMath.BestAttack search;
        List<CombatMath.AttackOption> kept;
        float[][] cands;
        StateEncoder.CandMeta meta;
    }

    /** RLPlayer.jointAttacks' dedup key (the Pareto survivors are also
     *  deduped by it: identical outcome + retained + crack-back). */
    static String attackKey(CombatMath.AttackOption o1) {
        return o1.outcome.damageTaken + "/" + o1.outcome.blockersLost
                + "/" + o1.outcome.blockerValueLost + "/"
                + o1.outcome.attackersKilled + "/"
                + o1.outcome.attackerValueKilled + "/" + o1.attackersUsed
                + "/" + o1.retainedPower + "/" + o1.crackBack;
    }

    /** avail must already be in RLPlayer.selectAttackers' order. */
    static Attack attacks(Game game, UUID defender, List<Permanent> avail,
                          int myLife, boolean v7, Consumer<String> fallback) {
        Attack ja = new Attack();
        List<Permanent> pick = attackChoiceSet(avail, fallback);
        List<Permanent> theirs = theirBlockers(game, defender);
        Player op = defender == null ? null : game.getPlayer(defender);
        int oppLife = op == null ? 20 : op.getLife();
        List<CombatMath.Body> mb = CombatMath.bodies(pick);
        List<CombatMath.Body> tb = CombatMath.bodies(theirs);
        CombatMath.BestAttack search = CombatMath.bestAttack(
                mb, tb, myLife, oppLife,
                Long.getLong("rl.attackCap", 4096L),
                Long.getLong("rl.attackReplyCap", 200000L));
        if (!search.exhaustive) {
            fallback.accept("attackCapped");
        }
        if (!search.replyExhaustive) {
            fallback.accept("attackReplyCapped");
        }
        if (search.budgetHit) {
            fallback.accept("attackBudgetHit");
        }
        // PARETO FILTER, five objectives (RLPlayer.jointAttacks documents
        // why retained power and retained bodies are objectives).
        List<CombatMath.AttackOption> kept = new ArrayList<>();
        java.util.Set<String> outcomes = new java.util.LinkedHashSet<>();
        int maxCands = Integer.getInteger("rl.attackMaxCands", 64);
        for (CombatMath.AttackOption o1 : search.options) {
            boolean dominated = false;
            for (CombatMath.AttackOption o2 : search.options) {
                if (o1 == o2) {
                    continue;
                }
                if (o2.outcome.damageTaken >= o1.outcome.damageTaken
                        && o2.outcome.blockerValueLost >= o1.outcome.blockerValueLost
                        && o2.outcome.attackerValueKilled <= o1.outcome.attackerValueKilled
                        && o2.retainedPower >= o1.retainedPower
                        && o2.retainedBodies >= o1.retainedBodies
                        && (o2.outcome.damageTaken > o1.outcome.damageTaken
                            || o2.outcome.blockerValueLost > o1.outcome.blockerValueLost
                            || o2.outcome.attackerValueKilled < o1.outcome.attackerValueKilled
                            || o2.retainedPower > o1.retainedPower
                            || o2.retainedBodies > o1.retainedBodies)) {
                    dominated = true;
                    break;
                }
            }
            if (dominated) {
                continue;
            }
            if (!outcomes.add(attackKey(o1))) {
                continue;
            }
            kept.add(o1);
            if (kept.size() >= maxCands) {
                fallback.accept("attackCandsCapped");
                break;
            }
        }
        if (kept.isEmpty()) {                 // cannot happen; not a crash
            kept.add(search.options.get(0));
        }
        float[][] cands = new float[kept.size()][];
        StateEncoder.CandMeta meta = new StateEncoder.CandMeta(cands.length);
        for (int i = 0; i < kept.size(); i++) {
            cands[i] = StateEncoder.forAttackSet(kept.get(i), myLife, oppLife);
            if (v7) {
                meta.after(i, StateEncoder.v7AfterAttack(kept.get(i), myLife, oppLife));
            }
            // referents: the attackers in the subset (over `pick`, the list
            // the search ran on); the empty subset IS the pass here
            List<UUID> refs = new ArrayList<>();
            boolean[] att = kept.get(i).attack;
            for (int j = 0; j < att.length && j < pick.size(); j++) {
                if (att[j]) {
                    refs.add(pick.get(j).getId());
                }
            }
            if (refs.isEmpty()) {
                meta.pass(i);
            } else {
                meta.set(i, StateEncoder.C_ATTACK, refs.toArray(new UUID[0]));
            }
        }
        ja.pick = pick;
        ja.theirs = theirs;
        ja.mb = mb;
        ja.oppLife = oppLife;
        ja.search = search;
        ja.kept = kept;
        ja.cands = cands;
        ja.meta = meta;
        return ja;
    }

    private static String bodySig(List<CombatMath.Body> mb, boolean[] attack) {
        List<String> sig = new ArrayList<>();
        for (int i = 0; i < mb.size() && i < attack.length; i++) {
            if (attack[i]) {
                sig.add(mb.get(i).power + "/" + mb.get(i).toughness);
            }
        }
        sig.sort(null);
        return sig.toString();
    }

    /** The candidate whose attack set is the declared one.
     *  how[0] = 0 exact (same body multiset - the search's own dedup, so
     *  exact up to interchangeable bodies), 1 alias (the declared
     *  multiset's option was deduped into a kept candidate with the same
     *  outcome key), 2 miss (dominated / not enumerated / an attacker
     *  outside `pick`). Returns the index or -1. */
    static int matchAttack(Attack ja, Set<UUID> declared, int[] how) {
        boolean[] att = new boolean[ja.pick.size()];
        int inPick = 0;
        for (int i = 0; i < ja.pick.size(); i++) {
            if (declared.contains(ja.pick.get(i).getId())) {
                att[i] = true;
                inPick++;
            }
        }
        if (inPick != declared.size()) {
            how[0] = 2;
            return -1;
        }
        String sig = bodySig(ja.mb, att);
        for (int i = 0; i < ja.kept.size(); i++) {
            if (sig.equals(bodySig(ja.mb, ja.kept.get(i).attack))) {
                how[0] = 0;
                return i;
            }
        }
        for (CombatMath.AttackOption o : ja.search.options) {
            if (sig.equals(bodySig(ja.mb, o.attack))) {
                String key = attackKey(o);
                for (int i = 0; i < ja.kept.size(); i++) {
                    if (key.equals(attackKey(ja.kept.get(i)))) {
                        how[0] = 1;
                        return i;
                    }
                }
                break;
            }
        }
        how[0] = 2;
        return -1;
    }

    // ------------------------------------------------------------- blocks

    /** The joint block candidate list and what built it. */
    static final class Block {
        List<CombatMath.Body> ab;
        List<CombatMath.Body> bb;
        int distinct;
        List<int[]> options;
        float[][] cands;
        StateEncoder.CandMeta meta;
    }

    /** RLPlayer.jointBlocks' dedup key. */
    static String blockKey(CombatMath.Outcome o, int used) {
        return o.damageTaken + "/" + o.attackersKilled + "/"
                + o.attackerValueKilled + "/" + o.blockersLost + "/"
                + o.blockerValueLost + "/" + used;
    }

    static Block blocks(List<Permanent> attackers, List<Permanent> mine,
                        int myLife, boolean v7, Consumer<String> fallback) {
        int A = attackers.size();
        int B = mine.size();
        List<CombatMath.Body> ab = CombatMath.bodies(attackers);
        List<CombatMath.Body> bb = CombatMath.bodies(mine);
        long cap = Long.getLong("rl.jointCap", 20000L);
        long space = 1;
        for (int i = 0; i < B; i++) {
            space *= (A + 1);
            if (space > cap) {
                space = cap;
                fallback.accept("jointCapped");
                break;
            }
        }
        Map<String, int[]> byOutcome = new java.util.LinkedHashMap<>();
        Map<String, float[]> feats = new java.util.LinkedHashMap<>();
        int[] assign = new int[B];
        for (long code = 0; code < space; code++) {
            long c = code;
            int used = 0;
            for (int b = 0; b < B; b++) {
                assign[b] = (int) (c % (A + 1)) - 1;
                c /= (A + 1);
                if (assign[b] >= 0) {
                    used++;
                }
            }
            CombatMath.Outcome o = CombatMath.resolve(ab, bb, assign, myLife);
            String key = blockKey(o, used);
            if (byOutcome.containsKey(key)) {
                continue;
            }
            byOutcome.put(key, assign.clone());
            feats.put(key, StateEncoder.forAssignment(o, used, myLife));
        }
        // PARETO FILTER (RLPlayer.jointBlocks documents it).
        List<String> keys = new ArrayList<>(byOutcome.keySet());
        List<int[]> options = new ArrayList<>();
        List<float[]> kept = new ArrayList<>();
        int maxCands = Integer.getInteger("rl.jointMaxCands", 48);
        for (String k1 : keys) {
            int[] a1 = byOutcome.get(k1);
            CombatMath.Outcome o1 = CombatMath.resolve(ab, bb, a1, myLife);
            boolean dominated = false;
            for (String k2 : keys) {
                if (k1.equals(k2)) {
                    continue;
                }
                CombatMath.Outcome o2 =
                        CombatMath.resolve(ab, bb, byOutcome.get(k2), myLife);
                if (o2.damageTaken <= o1.damageTaken
                        && o2.attackerValueKilled >= o1.attackerValueKilled
                        && o2.blockerValueLost <= o1.blockerValueLost
                        && (o2.damageTaken < o1.damageTaken
                            || o2.attackerValueKilled > o1.attackerValueKilled
                            || o2.blockerValueLost < o1.blockerValueLost)) {
                    dominated = true;
                    break;
                }
            }
            if (!dominated) {
                options.add(a1);
                kept.add(feats.get(k1));
                if (options.size() >= maxCands) {
                    fallback.accept("jointCandsCapped");
                    break;
                }
            }
        }
        if (options.isEmpty()) {          // every option dominated: fall back
            options.add(byOutcome.values().iterator().next());
            kept.add(feats.values().iterator().next());
        }
        float[][] cands = kept.toArray(new float[0][]);
        StateEncoder.CandMeta meta = new StateEncoder.CandMeta(cands.length);
        for (int i = 0; i < options.size() && i < cands.length; i++) {
            // referents: every blocker assigned and the attacker it blocks;
            // the all-unassigned option IS the pass here
            int[] as = options.get(i);
            List<UUID> refs = new ArrayList<>();
            for (int b = 0; b < as.length && b < mine.size(); b++) {
                if (as[b] >= 0 && as[b] < attackers.size()) {
                    refs.add(mine.get(b).getId());
                    refs.add(attackers.get(as[b]).getId());
                }
            }
            if (refs.isEmpty()) {
                meta.pass(i);
            } else {
                meta.set(i, StateEncoder.C_BLOCK, refs.toArray(new UUID[0]));
            }
            if (v7) {
                meta.after(i, StateEncoder.v7AfterBlock(
                        CombatMath.resolve(ab, bb, as, myLife), refs.size() / 2, myLife));
            }
        }
        Block jb = new Block();
        jb.ab = ab;
        jb.bb = bb;
        jb.distinct = byOutcome.size();
        jb.options = options;
        jb.cands = cands;
        jb.meta = meta;
        return jb;
    }

    /** The candidate whose outcome is the declared assignment's (options
     *  are one per outcome key, so the key IS the candidate).
     *  how[0] = 0 exact assignment, 1 same outcome key, 2 miss. */
    static int matchBlock(Block jb, int[] declared, int myLife, int[] how) {
        int used = 0;
        for (int a : declared) {
            if (a >= 0) {
                used++;
            }
        }
        String key = blockKey(CombatMath.resolve(jb.ab, jb.bb, declared, myLife), used);
        for (int i = 0; i < jb.options.size(); i++) {
            int[] as = jb.options.get(i);
            if (Arrays.equals(as, declared)) {
                how[0] = 0;
                return i;
            }
        }
        for (int i = 0; i < jb.options.size(); i++) {
            int[] as = jb.options.get(i);
            int u = 0;
            for (int a : as) {
                if (a >= 0) {
                    u++;
                }
            }
            if (key.equals(blockKey(CombatMath.resolve(jb.ab, jb.bb, as, myLife), u))) {
                how[0] = 1;
                return i;
            }
        }
        how[0] = 2;
        return -1;
    }
}
