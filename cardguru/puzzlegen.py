"""Generate tier-1 lethal puzzles with a machine-checked win proof.

Tier 1 tests the calibration floor: can an agent count damage and construct
a legal line? Boards are deliberately clean — mono-red mana, vanilla
attackers, a defender with no untapped creatures (so strict-choose XMage has
no block decisions to fail on; see `localrunner` for why that constraint
exists) — and the interesting variation is arithmetic:

  - `combat`      attacking with everything is lethal on its own
  - `combat+burn` attacking alone is NOT lethal; the line must also cast
                  direct damage, within the mana actually available

Every generated puzzle passes two independent gates before it is written:

  1. `max_damage` — a brute force over attacker subsets and castable burn
     subsets (knapsack over untapped lands) — proves a win EXISTS, without
     reference to how the puzzle was constructed.
  2. The known_bad line's damage is proved short of lethal the same way.

That keeps the generator honest with itself: a construction bug that breaks
either property drops the puzzle instead of shipping a broken instrument.
Admission through a runner (`puzzle admit`) then checks the same two lines
end-to-end.

Card facts (power, cmc, burn amounts) come from the card store, not from
tables kept here. The burn pool is a candidate list filtered by what the
store's oracle text actually says a card does.
"""
from __future__ import annotations

import json
import os
import random
from itertools import combinations

from .localrunner import LocalRunner

BURN_CANDIDATES = ["Shock", "Lightning Strike", "Lightning Bolt",
                   "Searing Spear", "Incinerate"]
DECOY_CANDIDATES = ["Merfolk of the Pearl Trident", "Coral Merfolk",
                    "Cloud Sprite", "Sea Scryer"]


def _vanilla_pool(store, limit: int = 200) -> list[tuple[str, int]]:
    """(name, power) for keyword-free creatures with clean numeric stats."""
    rows = store.conn.execute(
        "SELECT name, power FROM cards WHERE layout='normal' "
        "AND type_line LIKE 'Creature%' AND oracle_text = '' "
        "ORDER BY name").fetchall()
    pool = []
    for row in rows:
        try:
            power = int(row["power"])
        except (TypeError, ValueError):
            continue
        if 1 <= power <= 5:
            pool.append((row["name"], power))
        if len(pool) >= limit:
            break
    return pool


def _burn_pool(runner: LocalRunner) -> list[tuple[str, int, int]]:
    """(name, damage, cmc) for candidates the store confirms are burn."""
    pool = []
    for name in BURN_CANDIDATES:
        try:
            pool.append((name, runner.burn_damage(name), runner.cmc(name)))
        except Exception:
            continue
    return pool


def max_damage(attackers: list[int], burn: list[tuple[int, int]],
               lands: int) -> int:
    """Brute-force maximum guaranteed damage: every attacker subset (attack
    all is optimal with no blockers, but we do not assume it) plus the best
    burn subset payable with `lands`."""
    best_combat = 0
    for r in range(len(attackers) + 1):
        for combo in combinations(attackers, r):
            best_combat = max(best_combat, sum(combo))
    best_burn = 0
    for r in range(len(burn) + 1):
        for combo in combinations(burn, r):
            if sum(c for _, c in combo) <= lands:
                best_burn = max(best_burn, sum(d for d, _ in combo))
    return best_combat + best_burn


def generate(store, count: int = 30, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    runner = LocalRunner(store)
    creatures = _vanilla_pool(store)
    burn = _burn_pool(runner)
    if len(creatures) < 8 or not burn:
        raise RuntimeError("card store lacks the generator's pools")

    puzzles = []
    attempt = 0
    while len(puzzles) < count and attempt < count * 20:
        attempt += 1
        spec = _one(rng, creatures, burn, len(puzzles) + 1)
        if spec is not None:
            puzzles.append(spec)
    if len(puzzles) < count:
        raise RuntimeError(f"only generated {len(puzzles)}/{count} puzzles")
    return puzzles


def _one(rng, creatures, burn, n) -> dict | None:
    attackers = rng.sample(creatures, rng.randint(2, 4))
    powers = [p for _, p in attackers]
    total = sum(powers)
    variant = rng.choice(["combat", "combat", "combat+burn"])

    if variant == "combat":
        lands, hand, casts, burn_hand = 0, [], [], []
        if total < min(powers) + 2:
            return None
        life = rng.randint(min(powers) + 1, total)
    else:
        burn_hand = rng.sample(burn, rng.randint(1, min(2, len(burn))))
        lands = sum(c for _, _, c in burn_hand)
        hand = [name for name, _, _ in burn_hand]
        dmg = sum(d for _, d, _ in burn_hand)
        # attacking alone must NOT get there; attack + all burn must
        if total + 1 > total + dmg:
            return None
        life = rng.randint(total + 1, total + dmg)
        casts = [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN",
                  "player": "A", "card": name, "target_player": "B"}
                 for name, _, _ in burn_hand]

    # independent proof gates
    burn_dc = [(d, c) for _, d, c in burn_hand]
    if max_damage(powers, burn_dc, lands) < life:
        return None
    weakest = min(attackers, key=lambda a: a[1])
    if weakest[1] >= life:
        return None

    battlefield = [{"card": name} for name, _ in attackers]
    if lands:
        battlefield.append({"card": "Mountain", "count": lands})
    decoys = rng.sample(DECOY_CANDIDATES, rng.randint(1, 2))
    b_field = [{"card": "Island", "count": rng.randint(2, 4), "tapped": True}]
    b_field += [{"card": name, "tapped": True} for name in decoys]

    attacks = [{"do": "attack", "turn": 1, "player": "A", "attacker": name}
               for name, _ in attackers]
    return {
        "id": f"t1-lethal-{n:03d}",
        "tier": 1,
        "description": f"Find lethal: {life} life across "
                       f"{len(attackers)} attackers"
                       + (" and burn in hand" if hand else ""),
        "trap": None,
        "notes": f"variant={variant}; generated seed-deterministically, "
                 "win proved by brute force over attack and burn subsets",
        "turn": 1,
        "players": {
            "A": {"life": 20, "battlefield": battlefield, "hand": hand},
            "B": {"life": life, "battlefield": b_field},
        },
        "win": [{"metric": "life", "player": "B", "max": 0}],
        "known_good": casts + attacks,
        "known_bad": [{"do": "attack", "turn": 1, "player": "A",
                       "attacker": weakest[0]}],
    }


def write_puzzles(puzzles: list[dict], outdir: str) -> list[str]:
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for spec in puzzles:
        path = os.path.join(outdir, spec["id"] + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=1)
            f.write("\n")
        paths.append(path)
    return paths
