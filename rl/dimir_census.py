#!/usr/bin/env python3
"""Phase 11 / A1 - Dimir card-play census (rl/PHASE11-DRILL.md Part A1).

Reads v7 recordings that carry the seat's choice: a teacher label `y` on the
consult (CP7 seat, echo-server files; the echo's own {"a":k} replies are then
ignored) or the {"a":k} reply line after the consult (a policy recorded
through rl/probes/record_proxy.py).  Game token (WIRE-V7 2b): turn = g[0]*30,
active = g[1], step one-hot g[2..9], stack depth g[11].  Entities (2d): zone
one-hot [0..6] (0 battlefield, 1 hand, 2 stack), mine [7], stack position
[9], P/T [10,11], tapped [22], is-creature [29], land [30], stack controller
is me [60], stack is ability [61].  Candidates (2f): type 0..7 = PASS LAND
SPELL ACTIVATE TARGET ATTACK BLOCK OTHER; TARGET afterstate is-creature
cand[11], power cand[12]*6, mine cand[14]; referents v7_cand_refers (token
index - 3 = entity row).  Names come from v7_ent_name (the wire carries them).

Counters (pooled and per game; Wilson 95 % for proportions, normal 95 % for
per-game means):
  ninjutsu  - windows = consults on the seat's own turn in the declare-
              blockers or combat-damage step offering an ACTIVATE of Kaito
              in HAND (ninjutsu); taken = that candidate chosen.  Kaito cast
              as a spell separately.  Opportunity check: own attack
              declarations with >= 1 attacker, Kaito in hand and >= 3
              untapped own lands, and whether a blockers-step window
              followed in that turn (an upper bound: the recording cannot
              say whether an attacker went unblocked).
  flash     - per flash card, offers at instant speed (not active, or not a
              main phase, or stack non-empty) vs taken; every cast by timing.
  counter   - consults offering a counterspell vs taken.
  removal   - TARGET consults whose top own stack object is a removal spell
              (or Nowhere to Run's -3/-3 trigger) with >= 1 enemy creature
              candidate: chosen = a highest-power enemy creature; chance =
              #highest / #enemy (k >= 2 subset, bootstrap CI of the
              difference); tapped-chosen when an untapped enemy creature of
              equal or higher power was legal.
  board     - creatures cast per game, own turn of the first creature, land
              drops by the seat's own turn 4.

  python3 rl/dimir_census.py --out rl/artifacts/v7/11 NAME=GLOB[,GLOB] ...
"""
import argparse
import collections
import glob
import json
import math
import os
import random
import sys

STEPS = ["upkeep", "draw", "main1", "attack", "block", "damage", "main2", "end"]
PASS, LAND, SPELL, ACT, TGT, ATK, BLK, OTH = range(8)
KAITO = "Kaito, Bane of Nightmares"
FLASH = ("Floodpits Drowner", "Enduring Curiosity", "The Wondrous Wasp", "Nowhere to Run")
COUNTER = ("Spell Snare", "Spell Pierce", "We Say Thee Nay!")
REMOVAL = ("Bitter Triumph", "Requiting Hex", "Shoot the Sheriff", "Nowhere to Run")
NTR_TRIGGER = "gets -3/-3"   # Nowhere to Run's ETB trigger is named by its rule text on the stack


# ------------------------------------------------------------------ helpers (shared with landfall_census)
def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def fmt(k, n):
    if n == 0:
        return "%d/0=nan" % k
    p, lo, hi = wilson(k, n)
    return "%d/%d=%.3f [%.3f,%.3f]" % (k, n, p, lo, hi)


def mean_ci(xs):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n == 0:
        return "nan (n=0)"
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    h = 1.96 * sd / math.sqrt(n)
    return "%.2f [%.2f,%.2f] (n=%d)" % (m, m - h, m + h, n)


def boot_diff(hits, chance, reps=2000, seed=0):
    n = len(hits)
    if n == 0:
        return "nan"
    rng = random.Random(seed)
    ds = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        ds.append(sum(hits[i] for i in idx) / n - sum(chance[i] for i in idx) / n)
    ds.sort()
    m = sum(hits) / n - sum(chance) / n
    return "%+.3f [%+.3f,%+.3f]" % (m, ds[int(0.025 * reps)], ds[int(0.975 * reps) - 1])


def step_of(g):
    for i in range(8):
        if g[2 + i] > 0.5:
            return STEPS[i]
    return "none"


def instant_speed(g):
    """P3's rule: not the active player, or not a main phase, or a non-empty stack."""
    main = g[2 + 2] > 0.5 or g[2 + 6] > 0.5
    return g[1] < 0.5 or not main or g[11] > 0.01


def timing(g):
    """response (stack non-empty) | opp_turn | own_main | own_<step> (own turn, a non-main step)."""
    if g[11] > 0.01:
        return "response"
    if g[1] < 0.5:
        return "opp_turn"
    st = step_of(g)
    return "own_main" if st in ("main1", "main2") else "own_" + st


def records(paths):
    """Yield ('choice', file, consult, a) and ('end', file, r).  A file with teacher labels
    (`"y":` in its head) takes `y` and ignores the echo server's {"a":k} replies."""
    for p in paths:
        with open(p, "rb") as fh:
            teacher = b'"y":' in fh.read(4_000_000)
        last = None
        for raw in open(p, "rb"):
            if not raw.strip():
                continue
            m = json.loads(raw)
            t = m.get("t")
            if t == "consult" and "v7_ent" in m:
                last = None
                if teacher:
                    if m.get("y") is not None:
                        yield ("choice", p, m, m["y"])
                else:
                    last = m
            elif t == "end":
                last = None
                yield ("end", p, m.get("r"))
            elif t is None and "a" in m and last is not None:
                yield ("choice", p, last, m["a"])
                last = None


class Consult:
    """Convenience view of one consult and the seat's choice."""
    def __init__(self, m, a):
        self.m = m
        self.g = m["v7_game"]
        self.turn = int(round(self.g[0] * 30))
        self.active = self.g[1] > 0.5
        self.step = step_of(self.g)
        self.ents = m["v7_ent"]
        self.names = m["v7_ent_name"]
        self.ct = m["v7_cand_type"]
        self.cand = m["v7_cand"]
        self.refs = m["v7_cand_refers"]
        self.a = a if isinstance(a, int) and 0 <= a < len(self.ct) else None

    def ent(self, k, j=0):
        r = self.refs[k]
        if len(r) <= j:
            return None
        i = r[j] - 3
        return i if 0 <= i < len(self.ents) else None

    def name(self, k, j=0):
        i = self.ent(k, j)
        return self.names[i] if i is not None else "?"

    def cands(self, typ, names=None, zone=None):
        out = []
        for k, t in enumerate(self.ct):
            if t != typ:
                continue
            i = self.ent(k)
            if i is None:
                continue
            if names is not None and self.names[i] not in names:
                continue
            if zone is not None and self.ents[i][zone] < 0.5:
                continue
            out.append(k)
        return out

    def chosen_type(self):
        return self.ct[self.a] if self.a is not None else None


class GameState:
    def __init__(self, f):
        self.f = f
        self.parity = None
        self.r = None
        self.turn_max = 0

    def own_turn(self, c):
        if self.parity is None:
            self.parity = c.turn % 2 if c.active else (c.turn + 1) % 2
        return (c.turn + 1) // 2 if self.parity == 1 else c.turn // 2


# ------------------------------------------------------------------ Dimir census
class DimirGame(GameState):
    def __init__(self, f):
        super().__init__(f)
        self.creatures = 0
        self.first_creature = None
        self.lands = 0
        self.lands_by4 = 0
        self.nin_win = 0
        self.nin_taken = 0
        self.nin_opp_turns = set()
        self.nin_win_turns = set()
        self.flash_off = 0
        self.flash_taken = 0
        self.ctr_off = 0
        self.ctr_taken = 0
        self.rem_n = 0
        self.rem_best = 0


def census(paths):
    S = collections.defaultdict(int)
    by = collections.defaultdict(lambda: collections.defaultdict(int))
    rem_hits, rem_chance = [], []
    games, g = [], None
    for ev in records(paths):
        if ev[0] == "end":
            if g is None:
                g = DimirGame(ev[1])
            g.r = ev[2]
            games.append(g)
            g = None
            continue
        _, f, m, a = ev
        if g is None or g.f != f:
            if g is not None:
                games.append(g)            # a game cut off by the end of its file
            g = DimirGame(f)
        c = Consult(m, a)
        S["consults"] += 1
        if c.a is None:
            S["no_choice"] += 1
            continue
        ot = g.own_turn(c)
        g.turn_max = max(g.turn_max, c.turn)
        S["step_%s_%s" % ("own" if c.active else "opp", c.step)] += 1
        ch = c.a
        cht = c.ct[ch]

        # ninjutsu: ACTIVATE of Kaito from hand
        kh = c.cands(ACT, (KAITO,), zone=1)
        if kh:
            if c.active and c.step in ("block", "damage"):
                S["nin_win_" + c.step] += 1
                g.nin_win += 1
                if c.step == "block":
                    g.nin_win_turns.add(c.turn)
                if ch in kh:
                    S["nin_taken_" + c.step] += 1
                    g.nin_taken += 1
            else:
                S["nin_hand_act_elsewhere"] += 1
                by["nin_elsewhere_step"]["%s_%s" % ("own" if c.active else "opp", c.step)] += 1
        ks = c.cands(SPELL, (KAITO,))
        if ks:
            S["kaito_spell_off"] += 1
            if ch in ks:
                S["kaito_spell_cast"] += 1
                by["kaito_cast_step"][c.step] += 1
        if c.active and c.step == "attack" and cht == ATK and c.refs[ch]:
            k_in_hand = any(nm == KAITO and e[1] > 0.5 for nm, e in zip(c.names, c.ents))
            untapped = sum(1 for e in c.ents if e[0] > 0.5 and e[7] > 0.5 and e[30] > 0.5 and e[22] < 0.5)
            if k_in_hand and untapped >= 3:
                g.nin_opp_turns.add(c.turn)

        # flash
        inst = instant_speed(c.g)
        fk = {}
        for k in c.cands(SPELL, FLASH, zone=1):
            fk.setdefault(c.name(k), []).append(k)
        if fk and inst:
            S["flash_win_inst"] += 1
            g.flash_off += 1
            took = any(ch in ks_ for ks_ in fk.values())
            if took:
                S["flash_take_inst"] += 1
                g.flash_taken += 1
            for nm, ks_ in fk.items():
                by["flash_off_inst"][nm] += 1
                if ch in ks_:
                    by["flash_take_inst"][nm] += 1
        if fk and c.g[1] < 0.5:
            S["flash_win_oppturn"] += 1
            if any(ch in ks_ for ks_ in fk.values()):
                S["flash_take_oppturn"] += 1
        if fk and not inst:
            S["flash_win_sorc"] += 1
            if any(ch in ks_ for ks_ in fk.values()):
                S["flash_take_sorc"] += 1

        # counterspells
        ck = c.cands(SPELL, COUNTER)
        if ck:
            S["ctr_win"] += 1
            g.ctr_off += 1
            if c.g[11] < 0.01:
                S["ctr_win_empty_stack"] += 1
            for k in ck:
                by["ctr_off"][c.name(k)] += 1
            if ch in ck:
                S["ctr_taken"] += 1
                g.ctr_taken += 1
                by["ctr_take"][c.name(ch)] += 1

        # every cast by timing
        if cht == SPELL:
            nm = c.name(ch)
            by["cast_inst" if inst else "cast_sorc"][nm] += 1
            by["timing:" + nm][timing(c.g)] += 1
            i = c.ent(ch)
            if i is not None and c.ents[i][29] > 0.5:
                g.creatures += 1
                if g.first_creature is None:
                    g.first_creature = ot
        if cht == LAND:
            g.lands += 1
            if c.active and ot <= 4:
                g.lands_by4 += 1

        # removal targeting
        if TGT in c.ct:
            st = sorted((c.ents[i][9], i) for i in range(len(c.ents)) if c.ents[i][2] > 0.5 and c.ents[i][60] > 0.5)
            src = None
            if st:
                top = c.names[st[0][1]]
                src = top if top in REMOVAL else ("Nowhere to Run" if NTR_TRIGGER in top else None)
            if src is not None:
                E = [k for k, t in enumerate(c.ct) if t == TGT and c.cand[k][11] > 0.5 and c.cand[k][14] < 0.5]
                if not E:
                    S["rem_no_enemy_creature"] += 1
                else:
                    pw = {k: round(c.cand[k][12] * 6) for k in E}
                    mx = max(pw.values())
                    best = ch in E and pw[ch] == mx
                    S["rem_n"] += 1
                    by["rem_n"][src] += 1
                    g.rem_n += 1
                    if ch not in E:
                        S["rem_not_enemy_creature"] += 1
                    if best:
                        S["rem_best"] += 1
                        by["rem_best"][src] += 1
                        g.rem_best += 1
                    if len(E) >= 2:
                        S["rem_k2"] += 1
                        rem_hits.append(1.0 if best else 0.0)
                        rem_chance.append(sum(1 for k in E if pw[k] == mx) / len(E))
                    tapped = {k: (c.ent(k) is not None and c.ents[c.ent(k)][22] > 0.5) for k in E}
                    alt = any(tapped[t] and any(not tapped[u] and pw[u] >= pw[t] for u in E) for t in E)
                    if alt:
                        S["rem_tap_alt"] += 1
                        if ch in E and tapped[ch] and any(not tapped[u] and pw[u] >= pw[ch] for u in E):
                            S["rem_tap_chosen"] += 1
    if g is not None:
        games.append(g)
    return S, by, rem_hits, rem_chance, games


def report(name, S, by, rem_hits, rem_chance, games):
    L = []
    P = "DC|%s|" % name
    res = collections.Counter("W" if (x.r or 0) > 0 else ("L" if (x.r or 0) < 0 else ("D" if x.r is not None else "cut")) for x in games)
    L.append(P + "games=%d|W/L/D/cut=%d/%d/%d/%d|consults_with_choice=%d|no_choice=%d|turns_per_game=%s" % (
        len(games), res["W"], res["L"], res["D"], res["cut"], S["consults"] - S["no_choice"], S["no_choice"],
        mean_ci([x.turn_max for x in games])))
    steps = sorted(((k[5:], v) for k, v in S.items() if k.startswith("step_")), key=lambda kv: -kv[1])
    L.append(P + "consult_steps|" + " ".join("%s:%d" % kv for kv in steps))
    nw = S["nin_win_block"] + S["nin_win_damage"]
    nt = S["nin_taken_block"] + S["nin_taken_damage"]
    opp = sum(len(x.nin_opp_turns) for x in games)
    cov = sum(len(x.nin_opp_turns & x.nin_win_turns) for x in games)
    L.append(P + "ninjutsu|offered_windows=%d (blockers %d, damage %d)|taken %s (blockers %s, damage %s)|games_with_window=%d|"
             "hand_ACT_outside_combat=%d %s|opportunity_turns(attack, Kaito in hand, >=3 untapped lands)=%d, with a blockers-step window=%d|"
             "kaito_cast_as_spell=%d of %d offers, steps %s" % (
                 nw, S["nin_win_block"], S["nin_win_damage"], fmt(nt, nw), fmt(S["nin_taken_block"], S["nin_win_block"]),
                 fmt(S["nin_taken_damage"], S["nin_win_damage"]), sum(1 for x in games if x.nin_win), S["nin_hand_act_elsewhere"],
                 dict(by["nin_elsewhere_step"]), opp, cov, S["kaito_spell_cast"], S["kaito_spell_off"], dict(by["kaito_cast_step"])))
    L.append(P + "flash|instant-speed windows offering a flash card: taken %s|per card (taken/offered at instant speed) %s|"
             "sorcery-speed windows: taken %s" % (
                 fmt(S["flash_take_inst"], S["flash_win_inst"]),
                 ";".join("%s %d/%d" % (nm, by["flash_take_inst"][nm], by["flash_off_inst"][nm]) for nm in FLASH),
                 fmt(S["flash_take_sorc"], S["flash_win_sorc"])))
    fc_i = sum(by["cast_inst"][nm] for nm in FLASH)
    fc_s = sum(by["cast_sorc"][nm] for nm in FLASH)
    L.append(P + "flash_casts|at instant speed %s|per card (instant/all) %s" % (
        fmt(fc_i, fc_i + fc_s), ";".join("%s %d/%d" % (nm, by["cast_inst"][nm], by["cast_inst"][nm] + by["cast_sorc"][nm]) for nm in FLASH)))
    L.append(P + "flash_oppturn|windows on the OPPONENT's turn offering a flash card: taken %s" % fmt(
        S["flash_take_oppturn"], S["flash_win_oppturn"]))
    L.append(P + "cast_timing|" + ";".join(
        "%s %s" % (nm, " ".join("%s:%d" % kv for kv in sorted(by["timing:" + nm].items())))
        for nm in FLASH + COUNTER + REMOVAL[:3] + (KAITO,) if by["timing:" + nm]))
    L.append(P + "counterspells|windows offering one: taken %s|offered with empty stack=%d|per card (taken/offered) %s" % (
        fmt(S["ctr_taken"], S["ctr_win"]), S["ctr_win_empty_stack"],
        ";".join("%s %d/%d" % (nm, by["ctr_take"][nm], by["ctr_off"][nm]) for nm in COUNTER)))
    L.append(P + "instant_removal_casts|per card (instant/all) %s" % ";".join(
        "%s %d/%d" % (nm, by["cast_inst"][nm], by["cast_inst"][nm] + by["cast_sorc"][nm]) for nm in REMOVAL[:3]))
    L.append(P + "removal_targeting|consults with >=1 enemy creature=%d|highest-power enemy chosen %s|k>=2 enemy: P(highest) vs chance diff %s (n=%d, chance %.3f)|"
             "not an enemy creature chosen=%d|tapped chosen when an untapped >= power was legal %s|no enemy creature offered=%d|per source (best/n) %s" % (
                 S["rem_n"], fmt(S["rem_best"], S["rem_n"]), boot_diff(rem_hits, rem_chance), len(rem_hits),
                 (sum(rem_chance) / len(rem_chance)) if rem_chance else float("nan"), S["rem_not_enemy_creature"],
                 fmt(S["rem_tap_chosen"], S["rem_tap_alt"]), S["rem_no_enemy_creature"],
                 ";".join("%s %d/%d" % (nm, by["rem_best"][nm], by["rem_n"][nm]) for nm in REMOVAL)))
    L.append(P + "board|creatures_cast_per_game=%s|first_creature_own_turn=%s (games with none: %d)|land_drops_by_own_turn4=%s|land_drops_per_game=%s" % (
        mean_ci([x.creatures for x in games]), mean_ci([x.first_creature for x in games]),
        sum(1 for x in games if x.first_creature is None), mean_ci([x.lands_by4 for x in games]), mean_ci([x.lands for x in games])))
    return L


def game_rows(name, games):
    hdr = "set\tgame\tfile\tr\tturns\tcreatures\tfirst_creature_own_turn\tlands_by4\tlands\tnin_windows\tnin_taken\tnin_opp_turns\tflash_inst_off\tflash_inst_taken\tctr_off\tctr_taken\trem_n\trem_best"
    rows = [hdr]
    for i, x in enumerate(games):
        rows.append("\t".join(str(v) for v in (name, i, os.path.basename(x.f), x.r, x.turn_max, x.creatures, x.first_creature,
                                               x.lands_by4, x.lands, x.nin_win, x.nin_taken, len(x.nin_opp_turns), x.flash_off,
                                               x.flash_taken, x.ctr_off, x.ctr_taken, x.rem_n, x.rem_best)))
    return rows


def expand(spec):
    name, pats = spec.split("=", 1)
    paths = [q for p in pats.split(",") for q in sorted(glob.glob(p))]
    if not paths:
        sys.exit("no files for " + spec)
    return name, paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="+", help="NAME=GLOB[,GLOB]")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for spec in args.sets:
        name, paths = expand(spec)
        S, by, rh, rc, games = census(paths)
        lines = report(name, S, by, rh, rc, games)
        for ln in lines:
            print(ln)
        with open(os.path.join(args.out, "dimir_census_%s.txt" % name), "w") as fh:
            fh.write("files=%s\n" % ",".join(paths) + "\n".join(lines) + "\n")
        with open(os.path.join(args.out, "dimir_census_%s_games.tsv" % name), "w") as fh:
            fh.write("\n".join(game_rows(name, games)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
