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
import re
from itertools import combinations

from .localrunner import LocalRunner

BURN_CANDIDATES = ["Shock", "Lightning Strike", "Lightning Bolt",
                   "Searing Spear", "Incinerate"]
DECOY_CANDIDATES = ["Merfolk of the Pearl Trident", "Coral Merfolk",
                    "Cloud Sprite", "Sea Scryer"]

# Tier 2: creature-only damage spells (must NOT be pointable at a player)
# and big juicy creatures that bait removal. Both verified against the
# store's oracle text before use; a candidate whose text has drifted is
# silently dropped rather than trusted.
CREATURE_BURN_CANDIDATES = ["Flame Slash", "Lava Coil", "Roast"]
BAIT_CANDIDATES = ["Craw Wurm", "Enormous Baloth", "Vizzerdrix",
                   "Canal Monitor"]

_CREATURE_ONLY = re.compile(r"deals (\d+) damage to target creature",
                            re.IGNORECASE)


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



# --- tier 2: choice traps -------------------------------------------------
#
# Every board is still a forced win, but a plausible wrong CHOICE loses.
# Discovered constraint (spike-block-unscripted): strict-choose XMage
# auto-declines unscripted defender blocks, so no trap may be premised on
# "the opponent would block" — and every defender creature is TAPPED so the
# engine artifact never contradicts real Magic. All decisions in a tier-2
# puzzle belong to the agent's own line. Admission requires --engine xmage:
# family "creature_only" traps hinge on target legality the local runner
# does not model.
#
# Families:
#   face_not_decoy   life = attack + ALL burn; a fat tapped creature bait
#                    means any burn diverted to it comes up short
#   right_burn       mana affords exactly one of two burn spells and only
#                    the bigger one reaches lethal
#   creature_only    the highest-damage spell in hand only targets
#                    creatures; pointing it at the face is illegal and
#                    fails the run, the smaller any-target spell wins

def _creature_burn_pool(runner: LocalRunner) -> list[tuple[str, int, int]]:
    pool = []
    for name in CREATURE_BURN_CANDIDATES:
        row = runner.store.resolve(name)
        text = (row["oracle_text"] or "") if row else ""
        m = _CREATURE_ONLY.search(text)
        if m and "any target" not in text.lower():
            pool.append((name, int(m.group(1)), int(row["cmc"] or 0)))
    return pool


def _bait_pool(store) -> list[str]:
    return [name for name in BAIT_CANDIDATES if store.resolve(name)]


def generate_t2(store, count: int = 30, seed: int = 11) -> list[dict]:
    rng = random.Random(seed)
    runner = LocalRunner(store)
    creatures = _vanilla_pool(store)
    burn = sorted(_burn_pool(runner), key=lambda b: b[1])
    cburn = _creature_burn_pool(runner)
    baits = _bait_pool(store)
    if len(creatures) < 8 or len(burn) < 2 or not cburn or not baits:
        raise RuntimeError("card store lacks the tier-2 generator's pools")

    makers = [_t2_face_not_decoy, _t2_right_burn, _t2_creature_only]
    puzzles, attempt = [], 0
    while len(puzzles) < count and attempt < count * 30:
        maker = makers[attempt % len(makers)]
        attempt += 1
        spec = maker(rng, creatures, burn, cburn, baits, len(puzzles) + 1)
        if spec is not None:
            puzzles.append(spec)
    if len(puzzles) < count:
        raise RuntimeError(f"only generated {len(puzzles)}/{count} t2 puzzles")
    return puzzles


def _t2_board(rng, attackers, lands, hand, life, baits, tapped_bait=True):
    battlefield = [{"card": name} for name, _ in attackers]
    if lands:
        battlefield.append({"card": "Mountain", "count": lands})
    bait = rng.choice(baits)
    b_field = [{"card": "Island", "count": rng.randint(2, 4), "tapped": True},
               {"card": bait, "tapped": tapped_bait}]
    return battlefield, b_field, bait


def _t2_base(n, family, battlefield, b_field, hand, life,
             trap, notes, known_good, known_bad):
    return {
        "id": f"t2-{family}-{n:03d}", "tier": 2,
        "description": f"Win this turn: {life} life, a choice to get right",
        "trap": trap, "notes": notes, "turn": 1,
        "players": {"A": {"life": 20, "battlefield": battlefield,
                          "hand": hand},
                    "B": {"life": life, "battlefield": b_field}},
        "win": [{"metric": "life", "player": "B", "max": 0}],
        "known_good": known_good, "known_bad": known_bad,
    }


def _cast_face(name):
    return {"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN",
            "player": "A", "card": name, "target_player": "B"}


def _cast_at_creature(name, target):
    return [{"do": "cast", "turn": 1, "phase": "PRECOMBAT_MAIN",
             "player": "A", "card": name},
            {"do": "target", "player": "A", "value": target}]


def _attacks(attackers):
    return [{"do": "attack", "turn": 1, "player": "A", "attacker": name}
            for name, _ in attackers]


def _t2_face_not_decoy(rng, creatures, burn, cburn, baits, n):
    attackers = rng.sample(creatures, rng.randint(2, 3))
    total = sum(p for _, p in attackers)
    spells = rng.sample(burn, rng.randint(1, 2))
    lands = sum(c for _, _, c in spells)
    dmg = sum(d for _, d, _ in spells)
    if dmg < 2:
        return None
    life = total + dmg  # every point of burn must go at the face
    battlefield, b_field, bait = _t2_board(rng, attackers, lands,
                                           None, life, baits)
    hand = [name for name, _, _ in spells]
    diverted = spells[0]  # the trap: "safely" killing the bait first
    good = [_cast_face(name) for name, _, _ in spells] + _attacks(attackers)
    bad = (_cast_at_creature(diverted[0], bait)
           + [_cast_face(name) for name, _, _ in spells[1:]]
           + _attacks(attackers))
    if max_damage([p for _, p in attackers],
                  [(d, c) for _, d, c in spells], lands) < life:
        return None
    if total + dmg - diverted[1] >= life:  # trap line must actually lose
        return None
    return _t2_base(n, "face-not-decoy", battlefield, b_field, hand, life,
                    trap=f"burning the {bait} instead of the face comes up "
                         f"{diverted[1]} short",
                    notes="family=face_not_decoy; all burn must be lethal-"
                          "directed; bait creature is tapped and harmless",
                    known_good=good, known_bad=bad)


def _t2_right_burn(rng, creatures, burn, cburn, baits, n):
    pairs = [(a, b) for a in burn for b in burn if a[1] < b[1]]
    if not pairs:
        return None
    low, high = rng.choice(pairs)
    attackers = rng.sample(creatures, rng.randint(2, 3))
    total = sum(p for _, p in attackers)
    lands = high[2]                       # affords either spell, not both
    if low[2] + high[2] <= lands:
        return None
    life = total + high[1]                # only the big spell gets there
    battlefield, b_field, _bait = _t2_board(rng, attackers, lands,
                                            None, life, baits)
    hand = [low[0], high[0]]
    good = [_cast_face(high[0])] + _attacks(attackers)
    bad = [_cast_face(low[0])] + _attacks(attackers)
    if total + low[1] >= life:
        return None
    return _t2_base(n, "right-burn", battlefield, b_field, hand, life,
                    trap=f"mana affords one spell; {low[0]} leaves the "
                         f"opponent at {life - total - low[1]}",
                    notes="family=right_burn; land count pays for exactly "
                          "one of the two spells in hand",
                    known_good=good, known_bad=bad)


def _t2_creature_only(rng, creatures, burn, cburn, baits, n):
    cre = rng.choice(cburn)               # bigger, creature-only
    faces = [b for b in burn if b[1] < cre[1]]
    if not faces:
        return None
    face = rng.choice(faces)              # smaller, any-target
    attackers = rng.sample(creatures, rng.randint(2, 3))
    total = sum(p for _, p in attackers)
    lands = max(face[2], cre[2])
    if face[2] + cre[2] <= lands:
        return None
    life = total + face[1]
    battlefield, b_field, _bait = _t2_board(rng, attackers, lands,
                                            None, life, baits)
    hand = [face[0], cre[0]]
    good = [_cast_face(face[0])] + _attacks(attackers)
    bad = [_cast_face(cre[0])] + _attacks(attackers)  # illegal: no player tgt
    return _t2_base(n, "creature-only", battlefield, b_field, hand, life,
                    trap=f"{cre[0]} deals more damage but only targets "
                         "creatures; pointing it at the face fails",
                    notes="family=creature_only; known_bad's cast is "
                          "illegal — the engine refuses it (observed: "
                          "silently skipped, not errored) and the attack "
                          "alone falls short",
                    known_good=good, known_bad=bad)


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
