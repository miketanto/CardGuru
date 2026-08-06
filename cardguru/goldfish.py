"""Goldfish consistency simulation: Monte Carlo dealing of the actual list.

Answers the questions curve analysis can only estimate: how often do you hit
your land drops, when is the commander actually castable (color-aware), how
often are you mana-screwed? Pure dealing simulation over the real decklist —
honest label: computed, not engine-simulated (engine goldfishing with an AI
player is future work).

Simplifications (stated, not hidden): every land taps for its printed colors
untapped; no mulligans; mana rocks/dorks ARE cast greedily (cheapest first,
producing any color, usable the following turn); other spells are "cast" only
for the dead-turn metric (can this hand use its mana at all). Commander
castability checks total sources >= MV and per-color lands >= pips.

Deficiency here is MEASURED, not quoted: `verdicts` compares the simulated
stats to stated targets and reports the shortfall in percentage points.
"""
from __future__ import annotations

import random

from .deck import COLOR_LETTERS, detect_roles, mana_value

# consistency targets: the product's stated standards, applied to measurements
TARGETS = {
    "land_drop_t3": 85.0,        # hit your first three land drops
    "commander_on_curve": 60.0,  # commander castable the turn its MV allows
    "screw_rate_max": 15.0,      # <3 lands on turn 4
    "dead_turn_t3_max": 15.0,    # nothing castable at all on turn 3
}


def _land_colors(rec: dict) -> set[str]:
    oracle = rec.get("oracle") or ""
    colors = {c for c in COLOR_LETTERS if "{%s}" % c in oracle}
    if "any color" in oracle:
        colors = set(COLOR_LETTERS)
    return colors


def _is_rock(rec: dict) -> bool:
    """Mana rock/dork: a permanent ramp engine castable early."""
    if "Land" in (rec.get("types") or ""):
        return False
    mv = mana_value(rec.get("manaCost"))
    return mv is not None and mv <= 3 and detect_roles(rec).get("ramp") == "engine"


def _is_dork(rec: dict) -> bool:
    return _is_rock(rec) and "Creature" in (rec.get("types") or "")


def _is_amplifier(rec: dict) -> bool:
    """Mana multiplier (Badgermole Cub family): each creature tapped for mana
    yields +1 extra while this is in play."""
    from .recommend import HOOKS
    return HOOKS["amplifies_mana"]["detect"](rec)


def _is_reducer(rec: dict) -> bool:
    """Cost-reduction static (the gap miner's ReduceCost cluster): modeled as
    -1 generic on your spells while in play (floor: colored pips)."""
    return any(n.get("kind") == "S"
               and ((n.get("params") or {}).get("Mode") == "ReduceCost"
                    or n.get("mode") == "ReduceCost")
               for n in rec.get("nodes") or [])


def _pips(mana_cost: str | None) -> dict[str, int]:
    out: dict[str, int] = {}
    for sym in (mana_cost or "").split():
        if sym in COLOR_LETTERS:
            out[sym] = out.get(sym, 0) + 1
    return out


def simulate(by_name: dict, commander_rec: dict,
             decklist: list[tuple[str, int]], iterations: int = 5000,
             turns: int = 6, on_play: bool = True, seed: int = 7) -> dict:
    pool = []
    for name, count in decklist:
        rec = by_name.get(name)
        if rec is None:
            continue
        is_land = "Land" in (rec.get("types") or "")
        pool += [{"name": name, "land": is_land,
                  "rock": _is_rock(rec),
                  "dork": _is_dork(rec),
                  "amp": _is_amplifier(rec),
                  "reducer": _is_reducer(rec),
                  "mv": mana_value(rec.get("manaCost")),
                  "colors": _land_colors(rec) if is_land else set()}] * count

    cmd_mv = mana_value(commander_rec.get("manaCost")) or 0
    cmd_pips = _pips(commander_rec.get("manaCost"))

    rng = random.Random(seed)
    land_drop_hits = [0] * (turns + 1)      # index = turn
    commander_by = [0] * (turns + 1)
    dead_turns = [0] * (turns + 1)          # no land drop AND nothing castable
    mana_sum = [0] * (turns + 1)
    screwed = 0                              # <3 lands in play on turn 4

    for _ in range(iterations):
        deck = pool[:]
        rng.shuffle(deck)
        hand = deck[:7]
        library = deck[7:]
        lands_in_play: list[set[str]] = []
        rocks_in_play = 0
        dorks_in_play = 0
        amps_in_play = 0
        reducers_in_play = 0
        commander_turn = None
        for turn in range(1, turns + 1):
            if not (turn == 1 and on_play) and library:
                hand.append(library.pop(0))
            # greedy land drop: prefer a land producing a commander color
            # we still lack, else any land
            land_idx = None
            missing = {c for c in cmd_pips
                       if sum(1 for l in lands_in_play if c in l) < cmd_pips[c]}
            dropped = False
            for i, card in enumerate(hand):
                if card["land"]:
                    if card["colors"] & missing:
                        land_idx = i
                        break
                    if land_idx is None:
                        land_idx = i
            if land_idx is not None:
                lands_in_play.append(hand.pop(land_idx)["colors"])
                land_drop_hits[turn] += 1
                dropped = True

            # amplifiers add +1 per creature tapped for mana (dorks)
            mana = (len(lands_in_play) + rocks_in_play
                    + amps_in_play * dorks_in_play)
            mana_sum[turn] += mana
            discount = reducers_in_play
            # cast the cheapest affordable mana-system piece
            # (rock/dork/amplifier/reducer - they compound from next turn)
            piece_idx = min((i for i, c in enumerate(hand)
                             if (c["rock"] or c["amp"] or c["reducer"])
                             and (c["mv"] or 0) <= mana),
                            key=lambda i: hand[i]["mv"] or 0, default=None)
            cast_something = False
            if piece_idx is not None:
                c = hand.pop(piece_idx)
                if c["rock"]:
                    rocks_in_play += 1
                if c["dork"]:
                    dorks_in_play += 1
                if c["amp"]:
                    amps_in_play += 1
                if c["reducer"]:
                    reducers_in_play += 1
                cast_something = True
            elif any(not c["land"] and c["mv"] is not None
                     and max((c["mv"] or 0) - discount, 1) <= mana
                     for c in hand):
                cast_something = True    # could cast SOME spell (not tracked)

            if not dropped and not cast_something:
                dead_turns[turn] += 1

            pip_total = sum(cmd_pips.values())
            eff_cmd_mv = max(cmd_mv - discount, pip_total, 1) if cmd_mv else 0
            if commander_turn is None and mana >= eff_cmd_mv:
                if all(sum(1 for l in lands_in_play if c in l) >= n
                       for c, n in cmd_pips.items()):
                    commander_turn = turn
            if turn == 4 and len(lands_in_play) < 3:
                screwed += 1
        if commander_turn is not None:
            for t in range(commander_turn, turns + 1):
                commander_by[t] += 1

    n = float(iterations)
    stats = {
        "iterations": iterations, "turns": turns, "on_play": on_play,
        "commander": commander_rec["name"], "commander_mv": cmd_mv,
        "land_drop_pct": {t: round(100 * land_drop_hits[t] / n, 1)
                          for t in range(1, turns + 1)},
        "commander_by_turn_pct": {t: round(100 * commander_by[t] / n, 1)
                                  for t in range(max(cmd_mv, 1), turns + 1)},
        "dead_turn_pct": {t: round(100 * dead_turns[t] / n, 1)
                          for t in range(1, turns + 1)},
        "avg_mana_by_turn": {t: round(mana_sum[t] / n, 2)
                             for t in range(1, turns + 1)},
        "screw_rate_pct": round(100 * screwed / n, 1),
        "caveats": "no mulligans; rocks/dorks/amplifiers/reducers cast "
                   "greedily (any-color, +1 per amp per dork, -1 generic per "
                   "reducer); untapped lands - an optimistic-mana / "
                   "pessimistic-sequencing model",
    }

    on_curve_t = max(cmd_mv, 1)
    on_curve = stats["commander_by_turn_pct"].get(min(on_curve_t, turns), 0.0)
    verdicts = []
    t3 = stats["land_drop_pct"].get(3, 0.0)
    if t3 < TARGETS["land_drop_t3"]:
        verdicts.append(f"MANA DEFICIT: T3 land drop {t3}% vs {TARGETS['land_drop_t3']}% target")
    if on_curve < TARGETS["commander_on_curve"]:
        verdicts.append(f"MANA DEFICIT: commander on curve {on_curve}% vs "
                        f"{TARGETS['commander_on_curve']}% target")
    if stats["screw_rate_pct"] > TARGETS["screw_rate_max"]:
        verdicts.append(f"MANA DEFICIT: screw rate {stats['screw_rate_pct']}% vs "
                        f"<={TARGETS['screw_rate_max']}% target")
    dt3 = stats["dead_turn_pct"].get(3, 0.0)
    if dt3 > TARGETS["dead_turn_t3_max"]:
        verdicts.append(f"CURVE DEFICIT: dead turn 3 in {dt3}% of games vs "
                        f"<={TARGETS['dead_turn_t3_max']}% target")
    stats["verdicts"] = verdicts or ["mana base meets all consistency targets"]
    stats["targets"] = TARGETS
    return stats
