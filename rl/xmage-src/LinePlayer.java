package org.mage.test.benchmark.rl;

import mage.MageObject;
import mage.abilities.Ability;
import mage.constants.RangeOfInfluence;
import mage.game.Game;
import mage.game.combat.CombatGroup;
import mage.game.permanent.Permanent;
import mage.player.ai.ComputerPlayer;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * A seat whose combat choices come from a fixed LINE - a list of integer
 * indices consumed in order, one per decision. Everything else passes.
 *
 * WHY THIS SHAPE. The subgame solver enumerates by REPLAY, not by state
 * copying: run the game with a line prefix, and when a decision arrives
 * past the end of the prefix, record how many options it had and stop.
 * Each extension of the prefix is then a fresh replay. Subgames are a
 * few turns long, so a replay is cheap, and replay needs no game copy,
 * no transposition table and no assumptions about what XMage's copy
 * constructor preserves.
 *
 * Determinism is the whole contract: options are enumerated in a
 * canonical order (name-sorted), so index i means the same thing on
 * every replay of the same line.
 *
 * SCOPE: attacks and blocks only. Priority always passes, which is
 * correct for tier-1 subgames (empty hands, inert filler libraries) and
 * must be revisited before any rung with cards to cast.
 */
public class LinePlayer extends ComputerPlayer {

    /** The choices to make, in order. */
    public int[] line = new int[0];
    /** How many decisions this seat has been asked so far. */
    public int decisionsSeen = 0;
    /** Option count at the first decision past the end of the line,
     *  or -1 if the line covered every decision. */
    public int frontierOptions = -1;
    /** What kind of decision the frontier was: "atk" or "blk". */
    public String frontierKind = null;
    /** Set once the line is exhausted; the solver reads it to know the
     *  replay reached new ground. */
    public boolean beyondLine = false;

    public LinePlayer(String name) {
        super(name, RangeOfInfluence.ONE);
    }

    public void reset(int[] newLine) {
        this.line = newLine;
        this.decisionsSeen = 0;
        this.frontierOptions = -1;
        this.frontierKind = null;
        this.beyondLine = false;
    }

    /** Consume one choice. Returns 0 (the canonical do-nothing option)
     *  once past the end of the line, and records the frontier. */
    private int next(int optionCount, String kind) {
        int idx = decisionsSeen++;
        if (idx < line.length) {
            int v = line[idx];
            return (v >= 0 && v < optionCount) ? v : 0;
        }
        if (!beyondLine) {
            beyondLine = true;
            frontierOptions = optionCount;
            frontierKind = kind;
        }
        return 0;
    }

    @Override
    public boolean priority(Game game) {
        pass(game);
        return false;
    }

    // ----------------------------------------------------------- attacks

    /** Available attackers, canonically ordered. */
    public static List<Permanent> attackers(Game game, ComputerPlayer me) {
        List<Permanent> avail = new ArrayList<>(me.getAvailableAttackers(game));
        avail.sort(Comparator.comparing(MageObject::getName)
                .thenComparing(p -> p.getId().toString()));
        return avail;
    }

    @Override
    public void selectAttackers(Game game, UUID attackingPlayerId) {
        List<Permanent> avail = attackers(game, this);
        int n = avail.size();
        if (n == 0) {
            return;
        }
        UUID defender = null;
        for (UUID opp : game.getOpponents(playerId)) {
            defender = opp;
            break;
        }
        if (defender == null) {
            return;
        }
        // option i is the bitmask i over the canonical attacker list;
        // option 0 is "attack with nobody"
        int options = 1 << n;
        int mask = next(options, "atk");
        for (int j = 0; j < n; j++) {
            if ((mask & (1 << j)) != 0) {
                this.declareAttacker(avail.get(j).getId(), defender, game, false);
            }
        }
    }

    // ------------------------------------------------------------ blocks

    /** Untapped creatures that could block, canonically ordered. */
    public List<Permanent> blockers(Game game) {
        List<Permanent> mine = new ArrayList<>();
        for (Permanent p : game.getBattlefield().getAllActivePermanents(playerId)) {
            if (p.isCreature(game) && !p.isTapped()) {
                mine.add(p);
            }
        }
        mine.sort(Comparator.comparing(MageObject::getName)
                .thenComparing(p -> p.getId().toString()));
        return mine;
    }

    /** Attackers in this combat, canonically ordered. */
    public static List<Permanent> attacking(Game game) {
        List<Permanent> atk = new ArrayList<>();
        for (CombatGroup g : game.getCombat().getGroups()) {
            for (UUID id : g.getAttackers()) {
                Permanent p = game.getPermanent(id);
                if (p != null) {
                    atk.add(p);
                }
            }
        }
        atk.sort(Comparator.comparing(MageObject::getName)
                .thenComparing(p -> p.getId().toString()));
        return atk;
    }

    @Override
    public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
        List<Permanent> atk = attacking(game);
        List<Permanent> mine = blockers(game);
        if (atk.isEmpty() || mine.isEmpty()) {
            return;
        }
        // one assignment = a base-(A+1) number over my blockers, digit 0
        // meaning "does not block". Illegal digits (canBlock false) are
        // skipped when applied, so the option space is a superset of the
        // legal one and every legal assignment is reachable.
        int base = atk.size() + 1;
        long options = 1;
        for (int i = 0; i < mine.size(); i++) {
            options *= base;
            if (options > 100000L) {           // guard; tier-1 boards are tiny
                options = 100000L;
                break;
            }
        }
        int code = next((int) options, "blk");
        for (int b = 0; b < mine.size(); b++) {
            int digit = code % base;
            code /= base;
            if (digit == 0) {
                continue;
            }
            Permanent target = atk.get(digit - 1);
            Permanent blocker = mine.get(b);
            if (blocker.canBlock(target.getId(), game)) {
                this.declareBlocker(defendingPlayerId, blocker.getId(),
                        target.getId(), game);
            }
        }
    }
}
