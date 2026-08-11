package org.mage.test.benchmark.rl;

import mage.MageObject;
import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.abilities.PlayLandAbility;
import mage.abilities.SpellAbility;
import mage.cards.Card;
import mage.cards.Cards;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.Target;
import mage.target.TargetCard;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Phase 5 C1: imitation teacher. A SearchPlayer (D1 by default) that ALSO
 * logs, at every decision point where RLPlayer would consult its policy,
 * the exact (state, candidates) vectors StateEncoder would hand the RL
 * agent, labeled with the index of the action the teacher actually took.
 *
 * Capture strategy: enumerate/encode candidates RLPlayer-style BEFORE
 * delegating to the teacher logic (search + heuristic fallback), then
 * observe what it did — priority actions via an activateAbility
 * interception, combat via before/after diffs of the combat state,
 * targets by replaying the additions against a cleared Target copy.
 * Everything is guarded by game.isSimulation() so search-internal sim
 * decisions never reach the log.
 *
 * Output: NDJSON, one line per example:
 *   {"t":"prio|atk|blk|tgt|card","y":<label>,"s":[SDIM],"c":[[CDIM]...]}
 * plus one {"t":"end","r":<reward>} line per episode (written by the
 * driver) so imitate.py can attach outcomes/discounts.
 * Label convention matches RLPlayer's action space exactly:
 * prio/blk 0 = pass, i+1 = candidate i; atk 0/1 = don't/attack;
 * tgt/card = index into the possible-targets list (no pass slot).
 */
public class TeacherLogPlayer extends org.mage.test.benchmark.SearchPlayer {

    public java.io.PrintWriter out;      // owned by the driver
    public long examples = 0;
    public long unmatched = 0;           // teacher acted outside the encoded list
    private boolean capturing = false;
    private ActivatedAbility captured;

    public TeacherLogPlayer(String name) {
        super(name);
    }

    private UUID oppId(Game game) {
        return game.getOpponents(getId()).stream().findFirst().orElse(getId());
    }

    // --------------------------------------------------------- priority

    @Override
    public boolean activateAbility(ActivatedAbility ability, Game game) {
        if (capturing && !game.isSimulation()
                && captured == null && !ability.isManaAbility()) {
            captured = ability;
        }
        return super.activateAbility(ability, game);
    }

    @Override
    public boolean priority(Game game) {
        if (out == null || game.isSimulation() || !canRespond()) {
            return super.priority(game);
        }
        boolean myTurn = getId().equals(game.getActivePlayerId());
        boolean sorceryWindow = myTurn && game.getStack().isEmpty()
                && (game.getTurnStepType() == PhaseStep.PRECOMBAT_MAIN
                || game.getTurnStepType() == PhaseStep.POSTCOMBAT_MAIN);
        List<ActivatedAbility> playable;
        try {
            playable = new ArrayList<>(getPlayable(game, true));
        } catch (Exception e) {
            return super.priority(game);
        }
        playable.removeIf(a -> a instanceof PlayLandAbility && !sorceryWindow);
        if (playable.isEmpty()) {
            return super.priority(game);    // RLPlayer auto-passes k=0: no consult
        }
        playable.sort(Comparator.comparing(a -> {
            MageObject o = game.getObject(a.getSourceId());
            return (o == null ? "?" : o.getName()) + "|" + a.getRule();
        }));
        float[] state = StateEncoder.encodeState(game, getId(), oppId(game));
        float[][] cands = new float[playable.size() + 1][];
        cands[0] = StateEncoder.blank(StateEncoder.T_PASS);
        for (int i = 0; i < playable.size(); i++) {
            ActivatedAbility a = playable.get(i);
            Card card = a instanceof SpellAbility || a instanceof PlayLandAbility
                    ? game.getCard(a.getSourceId()) : null;
            cands[i + 1] = StateEncoder.forCard(
                    a instanceof PlayLandAbility
                            ? StateEncoder.T_LAND : StateEncoder.T_SPELL,
                    card, game);
        }
        capturing = true;
        captured = null;
        boolean r = super.priority(game);
        capturing = false;
        int label = 0;
        if (captured != null) {
            String key = captured.getSourceId() + "|" + captured.getRule();
            for (int i = 0; i < playable.size(); i++) {
                ActivatedAbility a = playable.get(i);
                if ((a.getSourceId() + "|" + a.getRule()).equals(key)) {
                    label = i + 1;
                    break;
                }
            }
            if (label == 0) {
                unmatched++;
            }
        }
        write("prio", state, cands, label);
        return r;
    }

    // ----------------------------------------------------------- combat

    @Override
    public void selectAttackers(Game game, UUID attackingPlayerId) {
        if (out == null || game.isSimulation()) {
            super.selectAttackers(game, attackingPlayerId);
            return;
        }
        List<Permanent> avail = new ArrayList<>(getAvailableAttackers(game));
        avail.sort(Comparator.comparing(MageObject::getName));
        // encodeState has no per-declaration combat fields, so one snapshot
        // at entry equals RLPlayer's per-creature re-encode
        float[] state = StateEncoder.encodeState(game, getId(), oppId(game));
        super.selectAttackers(game, attackingPlayerId);
        Set<UUID> attacking = new HashSet<>(game.getCombat().getAttackers());
        for (Permanent creature : avail) {
            float[][] cands = {
                StateEncoder.blank(StateEncoder.T_PASS),
                StateEncoder.forCombat(StateEncoder.T_ATTACK, creature, game)};
            write("atk", state, cands,
                    attacking.contains(creature.getId()) ? 1 : 0);
        }
    }

    @Override
    public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
        if (out == null || game.isSimulation()) {
            super.selectBlockers(source, game, defendingPlayerId);
            return;
        }
        List<Permanent> attackers = new ArrayList<>();
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID atkId : g.getAttackers()) {
                Permanent atk = game.getPermanent(atkId);
                if (atk != null) {
                    attackers.add(atk);
                }
            }
        }
        if (attackers.isEmpty()) {
            super.selectBlockers(source, game, defendingPlayerId);
            return;
        }
        attackers.sort(Comparator.comparing(MageObject::getName));
        List<Permanent> mine = new ArrayList<>();
        for (Permanent p : game.getBattlefield().getAllActivePermanents(getId())) {
            if (p.isCreature(game) && !p.isTapped()) {
                mine.add(p);
            }
        }
        mine.sort(Comparator.comparing(MageObject::getName));
        // can-block sets before declaration (declaring can perturb canBlock)
        Map<UUID, List<Permanent>> canMap = new LinkedHashMap<>();
        for (Permanent blocker : mine) {
            List<Permanent> can = new ArrayList<>();
            for (Permanent atk : attackers) {
                if (blocker.canBlock(atk.getId(), game)) {
                    can.add(atk);
                }
            }
            canMap.put(blocker.getId(), can);
        }
        float[] state = StateEncoder.encodeState(game, getId(), oppId(game));
        super.selectBlockers(source, game, defendingPlayerId);
        Map<UUID, UUID> assigned = new HashMap<>();   // blocker -> attacker
        for (CombatGroup g : game.getCombat().getGroups()) {
            if (g.getAttackers().isEmpty()) {
                continue;
            }
            for (UUID b : g.getBlockers()) {
                assigned.put(b, g.getAttackers().get(0));
            }
        }
        for (Permanent blocker : mine) {
            List<Permanent> can = canMap.get(blocker.getId());
            if (can == null || can.isEmpty()) {
                continue;
            }
            float[][] cands = new float[can.size() + 1][];
            cands[0] = StateEncoder.blank(StateEncoder.T_PASS);
            int label = 0;
            for (int i = 0; i < can.size(); i++) {
                cands[i + 1] = StateEncoder.forCombat(
                        StateEncoder.T_BLOCK, can.get(i), game);
                if (can.get(i).getId().equals(assigned.get(blocker.getId()))) {
                    label = i + 1;
                }
            }
            write("blk", state, cands, label);
        }
    }

    // ---------------------------------------------------------- targets

    private String canonicalName(UUID id, Game game) {
        Player pl = game.getPlayer(id);
        if (pl != null) {
            return "player:" + pl.getName();
        }
        MageObject o = game.getObject(id);
        if (o != null) {
            return o.getName();
        }
        Card c = game.getCard(id);
        return c != null ? c.getName() : id.toString();
    }

    /** replay heuristic-chosen targets through RLPlayer's enumeration */
    private void logTargetDiff(Target target, List<UUID> before,
                               Ability source, Game game) {
        if (!before.isEmpty()) {
            return;     // partially pre-filled targets: skip, count nothing
        }
        List<UUID> added = new ArrayList<>(target.getTargets());
        if (added.isEmpty()) {
            return;
        }
        Target probe;
        try {
            probe = target.copy();
            probe.clearChosen();
        } catch (Exception e) {
            return;
        }
        for (UUID chosenId : added) {
            List<UUID> possible;
            try {
                possible = new ArrayList<>(
                        probe.possibleTargets(getId(), source, game));
            } catch (Exception e) {
                return;
            }
            possible.removeAll(probe.getTargets());
            possible.removeIf(id -> !probe.canTarget(getId(), id, source, game));
            possible.sort(Comparator.comparing(id -> canonicalName(id, game)));
            int label = possible.indexOf(chosenId);
            if (label < 0) {
                unmatched++;
                return;
            }
            float[] state = StateEncoder.encodeState(game, getId(), oppId(game));
            float[][] cands = new float[possible.size()][];
            for (int i = 0; i < possible.size(); i++) {
                UUID id = possible.get(i);
                Player pl = game.getPlayer(id);
                if (pl != null) {
                    cands[i] = StateEncoder.forTargetPlayer(
                            id.equals(getId()), pl.getLife());
                } else {
                    Permanent perm = game.getPermanent(id);
                    if (perm != null) {
                        cands[i] = StateEncoder.forTargetPermanent(perm, game, getId());
                    } else {
                        Card c = game.getCard(id);
                        cands[i] = StateEncoder.forCard(StateEncoder.T_TARGET, c, game);
                    }
                }
            }
            write("tgt", state, cands, label);
            try {
                probe.addTarget(chosenId, source, game);
            } catch (Exception e) {
                return;
            }
        }
    }

    private void logCardDiff(TargetCard target, List<UUID> before, Cards cards,
                             Ability source, Game game) {
        if (!before.isEmpty()) {
            return;
        }
        List<UUID> added = new ArrayList<>(target.getTargets());
        if (added.isEmpty()) {
            return;
        }
        Target probe;
        try {
            probe = target.copy();
            probe.clearChosen();
        } catch (Exception e) {
            return;
        }
        for (UUID chosenId : added) {
            List<Card> possible = new ArrayList<>(cards.getCards(game));
            Target fp = probe;
            possible.removeIf(c -> fp.getTargets().contains(c.getId())
                    || !fp.canTarget(getId(), c.getId(), source, game));
            possible.sort(Comparator.comparing(MageObject::getName));
            int label = -1;
            for (int i = 0; i < possible.size(); i++) {
                if (possible.get(i).getId().equals(chosenId)) {
                    label = i;
                    break;
                }
            }
            if (label < 0) {
                unmatched++;
                return;
            }
            float[] state = StateEncoder.encodeState(game, getId(), oppId(game));
            float[][] cands = new float[possible.size()][];
            for (int i = 0; i < possible.size(); i++) {
                cands[i] = StateEncoder.forCard(StateEncoder.T_TARGET,
                        possible.get(i), game);
            }
            write("card", state, cands, label);
            try {
                probe.addTarget(chosenId, source, game);
            } catch (Exception e) {
                return;
            }
        }
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Target target,
                                Ability source, Game game) {
        if (out == null || game.isSimulation()) {
            return super.chooseTarget(outcome, target, source, game);
        }
        List<UUID> before = new ArrayList<>(target.getTargets());
        boolean r = super.chooseTarget(outcome, target, source, game);
        logTargetDiff(target, before, source, game);
        return r;
    }

    @Override
    public boolean choose(Outcome outcome, Target target,
                          Ability source, Game game) {
        if (out == null || game.isSimulation()) {
            return super.choose(outcome, target, source, game);
        }
        List<UUID> before = new ArrayList<>(target.getTargets());
        boolean r = super.choose(outcome, target, source, game);
        logTargetDiff(target, before, source, game);
        return r;
    }

    @Override
    public boolean choose(Outcome outcome, Target target, Ability source,
                          Game game, Map<String, java.io.Serializable> options) {
        if (out == null || game.isSimulation()) {
            return super.choose(outcome, target, source, game, options);
        }
        List<UUID> before = new ArrayList<>(target.getTargets());
        boolean r = super.choose(outcome, target, source, game, options);
        logTargetDiff(target, before, source, game);
        return r;
    }

    @Override
    public boolean chooseTarget(Outcome outcome, Cards cards, TargetCard target,
                                Ability source, Game game) {
        if (out == null || game.isSimulation()) {
            return super.chooseTarget(outcome, cards, target, source, game);
        }
        List<UUID> before = new ArrayList<>(target.getTargets());
        boolean r = super.chooseTarget(outcome, cards, target, source, game);
        logCardDiff(target, before, cards, source, game);
        return r;
    }

    @Override
    public boolean choose(Outcome outcome, Cards cards, TargetCard target,
                          Ability source, Game game) {
        if (out == null || game.isSimulation()) {
            return super.choose(outcome, cards, target, source, game);
        }
        List<UUID> before = new ArrayList<>(target.getTargets());
        boolean r = super.choose(outcome, cards, target, source, game);
        logCardDiff(target, before, cards, source, game);
        return r;
    }

    // ------------------------------------------------------------ output

    private void write(String kind, float[] state, float[][] cands, int label) {
        examples++;
        StringBuilder sb = new StringBuilder(
                64 + cands.length * (cands.length > 0 ? cands[0].length : 0) * 7);
        sb.append("{\"t\":\"").append(kind).append("\",\"y\":").append(label)
                .append(",\"s\":[");
        appendVec(sb, state);
        sb.append("],\"c\":[");
        for (int i = 0; i < cands.length; i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append('[');
            appendVec(sb, cands[i]);
            sb.append(']');
        }
        sb.append("]}");
        out.println(sb);
    }

    private void appendVec(StringBuilder sb, float[] v) {
        for (int i = 0; i < v.length; i++) {
            if (i > 0) {
                sb.append(',');
            }
            float x = v[i];
            if (x == 0f) {
                sb.append('0');
            } else if (x == 1f) {
                sb.append('1');
            } else {
                sb.append(String.format(Locale.ROOT, "%.4g", x));
            }
        }
    }
}
