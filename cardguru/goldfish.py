"""Goldfish consistency simulation: Monte Carlo dealing of the actual list.

Answers the questions curve analysis can only estimate: how often do you hit
your land drops, when is the commander actually castable (color-aware), how
often are you mana-screwed? Pure dealing simulation over the real decklist —
honest label: computed, not engine-simulated (engine goldfishing with an AI
player is future work).

Simplifications (stated, not hidden): every land taps for its printed colors
untapped; no mulligans; no ramp spells cast (so results are a FLOOR for decks
with rocks/dorks); commander castability checks total lands >= MV and
per-color producing lands >= pips.
"""
from __future__ import annotations

import random

from .deck import COLOR_LETTERS, mana_value


def _land_colors(rec: dict) -> set[str]:
    oracle = rec.get("oracle") or ""
    colors = {c for c in COLOR_LETTERS if "{%s}" % c in oracle}
    if "any color" in oracle:
        colors = set(COLOR_LETTERS)
    return colors


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
                  "colors": _land_colors(rec) if is_land else set()}] * count

    cmd_mv = mana_value(commander_rec.get("manaCost")) or 0
    cmd_pips = _pips(commander_rec.get("manaCost"))

    rng = random.Random(seed)
    land_drop_hits = [0] * (turns + 1)      # index = turn
    commander_by = [0] * (turns + 1)
    screwed = 0                              # <3 lands in play on turn 4

    for _ in range(iterations):
        deck = pool[:]
        rng.shuffle(deck)
        hand = deck[:7]
        library = deck[7:]
        lands_in_play: list[set[str]] = []
        commander_turn = None
        for turn in range(1, turns + 1):
            if not (turn == 1 and on_play) and library:
                hand.append(library.pop(0))
            # greedy land drop: prefer a land producing a commander color
            # we still lack, else any land
            land_idx = None
            missing = {c for c in cmd_pips
                       if sum(1 for l in lands_in_play if c in l) < cmd_pips[c]}
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
            if commander_turn is None and len(lands_in_play) >= cmd_mv:
                if all(sum(1 for l in lands_in_play if c in l) >= n
                       for c, n in cmd_pips.items()):
                    commander_turn = turn
            if turn == 4 and len(lands_in_play) < 3:
                screwed += 1
        if commander_turn is not None:
            for t in range(commander_turn, turns + 1):
                commander_by[t] += 1

    n = float(iterations)
    return {
        "iterations": iterations, "turns": turns, "on_play": on_play,
        "commander": commander_rec["name"], "commander_mv": cmd_mv,
        "land_drop_pct": {t: round(100 * land_drop_hits[t] / n, 1)
                          for t in range(1, turns + 1)},
        "commander_by_turn_pct": {t: round(100 * commander_by[t] / n, 1)
                                  for t in range(max(cmd_mv, 1), turns + 1)},
        "screw_rate_pct": round(100 * screwed / n, 1),
        "caveats": "no mulligans, no ramp spells, untapped lands - "
                   "consistency floor, not ceiling",
    }
