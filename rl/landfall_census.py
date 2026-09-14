#!/usr/bin/env python3
"""Phase 11 / A2 - landfall card-play census (rl/PHASE11-DRILL.md Part A2), G1Landfall.

Same inputs and wire fields as rl/dimir_census.py (shared helpers imported
from it).  Per own turn it tracks the land drops (step), whether the seat
declared an attack, whether a landfall creature could attack (entity
operator can-attack [55]) and whether one did, and whether a land drop came
before the attack declaration.  Counters (Wilson 95 % / normal 95 % means):
  land drops per game and per own turn;
  share of land drops made in the precombat main phase on turns the seat
    attacks (a landfall deck wants the trigger before combat);
  land-search casts (Rampant Growth, Harrow, Nissa's Pilgrimage, Evolving
    Wilds activation) by step, and how many came precombat on a turn a
    landfall creature attacked;
  P(a landfall creature attacks | it can) on turns with a land drop before
    the attack declaration vs without;
  Adventuring Gear cast / offered, equip taken / offered;
  blocks: chosen BLOCK pairs (refers = [blocker, attacker, ...], RLPlayer
    joint blocks) where the blocker is smaller in both power and toughness
    (current P/T, pumps included) - from the recording;
  the rate at which the combat search (CombatMath.best, the driver's
    `[audit] policy ... | solver ...` line) would NOT have assigned that
    blocker - only from audit text (a debug transcript or the driver-server
    log of the recording run), given with --audit NAME=GLOB; the recording
    carries no solver reference.

  python3 rl/landfall_census.py --out rl/artifacts/v7/11 NAME=GLOB[,GLOB] [--audit NAME=GLOB] ...
"""
import argparse
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dimir_census import (ACT, ATK, BLK, LAND, SPELL, Consult, GameState, expand, fmt,  # noqa: E402
                          instant_speed, mean_ci, records)

LANDFALL = ("Scythe Leopard", "Plated Geopede", "Snapping Gnarlid", "Oran-Rief Survivalist", "Lotus Cobra",
            "Grazing Gladehart", "Valakut Predator", "Rampaging Baloths")
SEARCH = ("Rampant Growth", "Harrow", "Nissa's Pilgrimage")
WILDS = "Evolving Wilds"
GEAR = "Adventuring Gear"


class Turn:
    def __init__(self):
        self.land_steps = []
        self.atk_seen = False
        self.land_before_atk = False
        self.lf_can = False
        self.attacked = False
        self.lf_attacked = False
        self.search_pre = 0


class LandfallGame(GameState):
    def __init__(self, f):
        super().__init__(f)
        self.turns = collections.defaultdict(Turn)
        self.lands = 0
        self.blk_pairs = 0
        self.blk_small = 0
        self.creatures = 0


def census(paths):
    S = collections.defaultdict(int)
    by = collections.defaultdict(lambda: collections.defaultdict(int))
    games, g = [], None
    for ev in records(paths):
        if ev[0] == "end":
            if g is None:
                g = LandfallGame(ev[1])
            g.r = ev[2]
            games.append(g)
            g = None
            continue
        _, f, m, a = ev
        if g is None or g.f != f:
            if g is not None:
                games.append(g)
            g = LandfallGame(f)
        c = Consult(m, a)
        S["consults"] += 1
        if c.a is None:
            S["no_choice"] += 1
            continue
        g.own_turn(c)
        g.turn_max = max(g.turn_max, c.turn)
        ch, cht = c.a, c.ct[c.a]
        T = g.turns[c.turn] if c.active else None

        if cht == SPELL:
            i = c.ent(ch)
            if i is not None and c.ents[i][29] > 0.5:
                g.creatures += 1
        if cht == LAND:
            g.lands += 1
            if T is not None:
                T.land_steps.append(c.step)
                if not T.atk_seen:
                    T.land_before_atk = True
        # land search
        srch = c.cands(SPELL, SEARCH) + c.cands(ACT, (WILDS,), zone=0)
        if srch:
            S["search_off"] += 1
            if ch in srch:
                nm = c.name(ch)
                S["search_cast"] += 1
                by["search_step"]["%s:%s" % (nm, c.step if c.active else "opp_" + c.step)] += 1
                if T is not None and not T.atk_seen and c.step == "main1":
                    T.search_pre += 1
        # Adventuring Gear
        gs = c.cands(SPELL, (GEAR,))
        if gs:
            S["gear_off"] += 1
            S["gear_cast"] += ch in gs
        ge = c.cands(ACT, (GEAR,), zone=0)
        if ge:
            S["equip_off"] += 1
            S["equip_taken"] += ch in ge
        # attacks
        if T is not None and c.step == "attack" and ATK in c.ct:
            T.atk_seen = True
            if any(nm in LANDFALL and e[0] > 0.5 and e[7] > 0.5 and e[55] > 0.5 for nm, e in zip(c.names, c.ents)):
                T.lf_can = True
            if cht == ATK and c.refs[ch]:
                T.attacked = True
                if any(c.name(ch, j) in LANDFALL for j in range(len(c.refs[ch]))):
                    T.lf_attacked = True
        # blocks
        if BLK in c.ct:
            S["blk_consults"] += 1
            if cht == BLK:
                S["blk_blocked"] += 1
                r = c.refs[ch]
                for j in range(0, len(r) - 1, 2):
                    b, at = c.ent(ch, j), c.ent(ch, j + 1)
                    if b is None or at is None:
                        continue
                    bp, bt = round(c.ents[b][10] * 6), round(c.ents[b][11] * 6)
                    ap_, at_ = round(c.ents[at][10] * 6), round(c.ents[at][11] * 6)
                    S["blk_pairs"] += 1
                    g.blk_pairs += 1
                    if bp < ap_ and bt < at_:
                        S["blk_small"] += 1
                        g.blk_small += 1
    if g is not None:
        games.append(g)
    return S, by, games


PAIR = re.compile(r"(.+?) (-?\d+)/(-?\d+)->(?:(--)|(.+?) (-?\d+)/(-?\d+))(?:, |$)")


def parse_assign(s):
    """'A 1/1->B 3/3, C 2/2->--' -> [(A, 1, 1, B, 3, 3) | (C, 2, 2, None, None, None)]"""
    out = []
    for mm in PAIR.finditer(s.strip()):
        if mm.group(4):
            out.append((mm.group(1), int(mm.group(2)), int(mm.group(3)), None, None, None))
        else:
            out.append((mm.group(1), int(mm.group(2)), int(mm.group(3)), mm.group(5), int(mm.group(6)), int(mm.group(7))))
    return out


def audit(paths):
    """Small-into-big blocks in the policy's assignment and whether the solver left that blocker unassigned."""
    A = collections.Counter()
    for p in paths:
        for ln in open(p, errors="replace"):
            if "[audit] policy " not in ln:
                continue
            body = ln.split("[audit] policy ", 1)[1]
            if " | solver " not in body:
                continue
            pol, sol = body.split(" | solver ", 1)
            pol = pol.rsplit(" (score", 1)[0]
            sol = sol.rsplit(" (score", 1)[0]
            A["combats"] += 1
            sol_by = {}
            for b in parse_assign(sol):
                sol_by.setdefault(b[0], []).append(b)
            for b in parse_assign(pol):
                if b[3] is None:
                    continue
                A["pairs"] += 1
                if b[1] < b[4] and b[2] < b[5]:
                    A["small"] += 1
                    ref = sol_by.get(b[0], [])
                    if ref and all(x[3] is None for x in ref):
                        A["small_solver_none"] += 1
                    elif not ref:
                        A["small_solver_unparsed"] += 1
    return A


def report(name, S, by, games, A=None, audit_src=None):
    L = []
    P = "LC|%s|" % name
    res = collections.Counter("W" if (x.r or 0) > 0 else ("L" if (x.r or 0) < 0 else ("D" if x.r is not None else "cut")) for x in games)
    L.append(P + "games=%d|W/L/D/cut=%d/%d/%d/%d|consults_with_choice=%d|no_choice=%d|turns_per_game=%s" % (
        len(games), res["W"], res["L"], res["D"], res["cut"], S["consults"] - S["no_choice"], S["no_choice"],
        mean_ci([x.turn_max for x in games])))
    own_turns = [len(x.turns) for x in games]
    L.append(P + "land_drops|per_game=%s|per_own_turn_with_a_consult=%s" % (
        mean_ci([x.lands for x in games]),
        "%.3f (%d/%d)" % (sum(x.lands for x in games) / max(1, sum(own_turns)), sum(x.lands for x in games), sum(own_turns))))
    atk_drops = [s for x in games for t in x.turns.values() if t.attacked for s in t.land_steps]
    all_drops = [s for x in games for t in x.turns.values() for s in t.land_steps]
    L.append(P + "precombat_land_drop|on attack turns %s|all own turns %s" % (
        fmt(sum(1 for s in atk_drops if s == "main1"), len(atk_drops)), fmt(sum(1 for s in all_drops if s == "main1"), len(all_drops))))
    lf = [t for x in games for t in x.turns.values() if t.lf_can]
    w = [t for t in lf if t.land_before_atk]
    wo = [t for t in lf if not t.land_before_atk]
    L.append(P + "landfall_attacks|P(a landfall creature attacks | one can): with a land drop before the declaration %s; without %s" % (
        fmt(sum(t.lf_attacked for t in w), len(w)), fmt(sum(t.lf_attacked for t in wo), len(wo))))
    pre = sum(t.search_pre for x in games for t in x.turns.values() if t.lf_attacked)
    L.append(P + "land_search|cast %d of %d offering consults|precombat on a landfall-attack turn=%d|by card:step %s" % (
        S["search_cast"], S["search_off"], pre, ";".join("%s %d" % kv for kv in sorted(by["search_step"].items()))))
    L.append(P + "board|creatures_cast_per_game=%s" % mean_ci([x.creatures for x in games]))
    L.append(P + "adventuring_gear|cast %s|equip %s" % (fmt(S["gear_cast"], S["gear_off"]), fmt(S["equip_taken"], S["equip_off"])))
    L.append(P + "blocks|consults=%d|blocked %s|small-into-big pairs (blocker P and T both lower) %s [source: recording]" % (
        S["blk_consults"], fmt(S["blk_blocked"], S["blk_consults"]), fmt(S["blk_small"], S["blk_pairs"])))
    if A is not None:
        L.append(P + "blocks_audit|source=%s|combats=%d|policy block pairs=%d|small-into-big %s|of those the solver would not block %s|unparsed=%d" % (
            audit_src, A["combats"], A["pairs"], fmt(A["small"], A["pairs"]), fmt(A["small_solver_none"], A["small"]),
            A["small_solver_unparsed"]))
    return L


def game_rows(name, games):
    rows = ["set\tgame\tfile\tr\tturns\tlands\town_turns\tattack_turns\tprecombat_drops_on_attack_turns\tdrops_on_attack_turns\tlf_can_turns\tlf_attack_turns\tblk_pairs\tblk_small"]
    for i, x in enumerate(games):
        ts = x.turns.values()
        rows.append("\t".join(str(v) for v in (
            name, i, os.path.basename(x.f), x.r, x.turn_max, x.lands, len(x.turns), sum(t.attacked for t in ts),
            sum(1 for t in ts if t.attacked for s in t.land_steps if s == "main1"),
            sum(len(t.land_steps) for t in ts if t.attacked), sum(t.lf_can for t in ts), sum(t.lf_attacked for t in ts),
            x.blk_pairs, x.blk_small)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="+", help="NAME=GLOB[,GLOB]")
    ap.add_argument("--audit", action="append", default=[], help="NAME=GLOB of transcripts / driver logs with [audit] lines")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    auds = {}
    for spec in args.audit:
        nm, pats = spec.split("=", 1)
        auds[nm] = [q for p in pats.split(",") for q in sorted(glob.glob(p))]
    os.makedirs(args.out, exist_ok=True)
    for spec in args.sets:
        name, paths = expand(spec)
        S, by, games = census(paths)
        A = audit(auds[name]) if name in auds else None
        lines = report(name, S, by, games, A, ",".join(os.path.basename(p) for p in auds.get(name, [])))
        for ln in lines:
            print(ln)
        with open(os.path.join(args.out, "landfall_census_%s.txt" % name), "w") as fh:
            fh.write("files=%s\n" % ",".join(paths) + "\n".join(lines) + "\n")
        with open(os.path.join(args.out, "landfall_census_%s_games.tsv" % name), "w") as fh:
            fh.write("\n".join(game_rows(name, games)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
