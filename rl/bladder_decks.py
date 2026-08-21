"""The black branch: threat assessment, run in parallel with the white one.

WHAT SKILL THIS BRANCH IS FOR
-----------------------------
The white ladder is about COMBAT - attack, block, trade math, and (at its
top) timing and hidden information. Its removal spell targets a *tapped
creature*, which on a real board is usually one or two attackers, so the
choice is close to forced. Nothing in the white branch asks the question
"of everything on the battlefield, which one matters most?"

That is this branch. The axis is **how wide the legal target set is**,
and the pin supports it at a fixed cost, in one colour, with one
template:

    Defeat      {1}{B}  SORCERY  destroy target creature with power 2 or less
    Reave Soul  {1}{B}  SORCERY  destroy target creature with power 3 or less
    Fell        {1}{B}  SORCERY  destroy target creature

Same colour, same cost, same card type, same wording, same deck slot,
four copies each. The ONLY thing that moves between rungs is how many
creatures the spell is allowed to point at. That is as clean as a
one-variable rung gets, and it is cleaner than the white branch's
keyword rungs, which at least change a creature's body text.

TWO MORE CARDS AT THE SAME COST AND SLOT
----------------------------------------
    Cruel Cut   {1}{B}  INSTANT  destroy target creature with power 2 or less
    Mind Knives {1}{B}  SORCERY  target opponent discards a card at random

`Cruel Cut` is `Defeat` at instant speed - identical restriction,
identical cost - so the branch carries its own replication of the white
branch's W3->W4 timing result in a second colour, for free.

`Mind Knives` is the odd one and the point of including it: it costs the
same, occupies the same slot, has NO board effect at all, and offers no
choice (the discard is random). It is pure card advantage. Phase 4
recorded terminal-reward PPO failing to beat 1-ply search, and a card
whose value never appears on the battlefield is the hardest possible
case for a terminal reward signal. **Prediction, recorded before the
run: this is the rung the agent fails.** If it learns to cast Mind
Knives at a sensible rate the prediction is wrong and that is worth more
than a win rate.

WHY THE DECK LOOKS LIKE THIS
----------------------------
A targeting ladder is vacuous unless the board has creatures on both
sides of each threshold. B0Base is built around its POWER census:

    power 2   16 creatures    <- all Defeat can ever hit
    power 3    8 creatures    <- Reave Soul adds these
    power 4    4 creatures    <- only Fell can hit these
    power 5    8 creatures    <- and these, which are the real threats

So the rungs do not merely differ in wording, they differ in whether the
best target on a typical board is legal at all. At B1 the choice is
close to forced; at B3 picking a 2/1 over a 5/3 is an unambiguous error.

THE MEASUREMENT THIS BRANCH MAKES POSSIBLE
------------------------------------------
Win rate is the weak instrument here. The strong one is the DISTRIBUTION
of chosen targets by power: a policy doing threat assessment concentrates
its kills on high power, a policy ignoring the board is uniform over the
legal set. That is a chi-square on fixed weights - a within-net
measurement, the class POOLED-ANALYSIS section 6 found actually
replicates, and it needs no second training run.

Everything except B1Fast is sorcery speed, so the opponent can never
respond during combat and the combat subgame stays perfect information -
minimax still gives ground truth for "which creature should have died".

Run: python3 rl/bladder_decks.py [--out-dir rl]
"""
import argparse
import collections
import os

SWAMP = ("Swamp", "FDN:276")
N_LAND = 24

# (cmc, power, toughness, copies, [base], [twin])
#
# The curve is built for its POWER census (see module docstring) and, as
# in every rung-0 deck here, skewed toward power > toughness: the 5/1 and
# 4/2 and 5/3 at the top mean attacks trade, trades turn the board over,
# and games end instead of stalling out to stopTurn.
SHELL = [
    (2, 2, 1, 4, [("Dakmor Scorpion", "P02:70")],
                 [("Krovikan Scoundrel", "ANB:50")]),
    # ---- THE LADDER SLOT: every rung >=1 replaces the second block ----
    (2, 2, 2, 8, [("Cabal Evangel", "DOM:78"), ("Gutter Skulk", "GTC:67")],
                 [("Queen's Bay Soldier", "XLN:115"),
                  ("Walking Corpse", "ISD:126")]),
    (3, 3, 2, 8, [("Barony Vampire", "M11:82"), ("Moriok Reaver", "SOM:70")],
                 [("Python", "VIS:68"), ("Vampire Noble", "E02:24")]),
    (3, 2, 3, 4, [("Felhide Minotaur", "THS:87")],
                 [("Undead Minotaur", "M14:119")]),
    (4, 4, 2, 4, [("Giant Cockroach", "ULG:54")],
                 [("Nether Horror", "M11:108")]),
    (4, 5, 1, 4, [("Dross Crocodile", "10E:138")],
                 [("Rotting Fensnake", "ISD:113")]),
    (5, 5, 3, 4, [("Canal Monitor", "RIX:63")],
                 [("Mass of Ghouls", "FUT:88")]),
]

SWAP_CARD = ("Gutter Skulk", "GTC:67")
SWAP_N = 4
# The same slot in the TWIN shell. The ladder builds a twin for rung 0
# only, so a higher rung has no transfer arm: passing B0Twin would move
# the RUNG and the card identities at once, which is the confound the
# twin exists to remove. (The white branch needed the same fix - see
# TWIN_SWAP_CARD in wladder_decks.py.)
TWIN_SWAP_CARD = ("Krovikan Scoundrel", "ANB:50")

# Every rung is the same slot, the same cost, the same count. Only the
# card name changes.
RUNGS = [
    ("B1Narrow", ("Defeat", "DTK:97"),
     "sorcery, destroy target creature with power 2 or less - near-forced"),
    ("B2Mid", ("Reave Soul", "J22:459"),
     "sorcery, power 3 or less - a real but small choice"),
    ("B3Open", ("Fell", "BLB:383"),
     "sorcery, destroy target creature - full threat assessment"),
    ("B1Fast", ("Cruel Cut", "ANB:47"),
     "INSTANT, power 2 or less - Defeat's timing twin, replicates W3->W4"),
    ("B4Card", ("Mind Knives", "POR:100"),
     "sorcery, opponent discards at random - card advantage, no board, "
     "no choice"),
]


def shell_entries(arm):
    out = []
    for cmc, p, t, copies, base, twin in SHELL:
        left = copies
        for card in (base, twin)[arm]:
            n = min(4, left)
            out.append((n, card, cmc, p, t))
            left -= n
        assert left == 0, (cmc, p, t, copies)
    return out


def swap(entries, card, swap_card=SWAP_CARD):
    out, dropped = [], 0
    for n, c, cmc, p, t in entries:
        if c == swap_card:
            dropped += n
            continue
        out.append((n, c, cmc, p, t))
    assert dropped == SWAP_N, dropped
    return out + [(SWAP_N, card, 2, 0, 0)]


def write_deck(path, name, entries):
    counts = collections.Counter()
    for n, card, *_ in entries:
        counts[card[0]] += n
    over = {c: k for c, k in counts.items() if k > 4}
    assert not over, "more than 4 copies: %s" % over
    total = sum(n for n, *_ in entries) + N_LAND
    assert total == 60, "%s has %d cards" % (name, total)
    with open(path, "w") as fh:
        fh.write("NAME:%s\n" % name)
        for n, card, *_ in entries:
            fh.write("%d [%s] %s\n" % (n, card[1], card[0]))
        fh.write("%d [%s] %s\n" % (N_LAND, SWAMP[1], SWAMP[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/home/user/CardGuru/rl")
    args = ap.parse_args()

    base, twin = shell_entries(0), shell_entries(1)
    decks = [("B0Base", base, "rung 0: vanilla combat, power spread 2-5"),
             ("B0Twin", twin, "rung 0 transfer: same costs and stat lines, "
                              "no shared card")]
    for name, card, note in RUNGS:
        decks.append((name, swap(base, card), note))
    # Transfer arms, by the rung-0 recipe: the twin shell with ITS
    # ladder slot swapped for the same spell. The ladder builds a twin
    # for rung 0 only, so any rung that gets TRAINED needs one of these
    # or its transfer probe moves the rung and the card identities at
    # once. Add a line here when a new rung is trained.
    for tname, tcard, tnote in [
            ("B3Twin", ("Fell", "BLB:383"),
             "rung 3 transfer: B0Twin's identities, B3's spell"),
            ("B1FastTwin", ("Cruel Cut", "ANB:47"),
             "B1Fast transfer: B0Twin's identities, the instant")]:
        decks.append((tname, swap(twin, tcard, swap_card=TWIN_SWAP_CARD),
                      tnote))

    names = {}
    for name, entries, note in decks:
        write_deck(os.path.join(args.out_dir, name + ".dck"), name, entries)
        names[name] = {c[0] for _, c, *_ in entries}
        print("%-9s 60 cards  %s" % (name, note))

    # the power census is the whole reason the rungs differ, so print it
    census = collections.Counter()
    for n, _c, _cmc, p, _t in base:
        census[p] += n
    print()
    print("B0Base power census: %s  (Defeat<=2 hits %d, Reave<=3 hits %d, "
          "Fell hits %d of 36)"
          % (dict(sorted(census.items())),
             sum(v for k, v in census.items() if k <= 2),
             sum(v for k, v in census.items() if k <= 3),
             sum(census.values())))
    shared = names["B0Base"] & names["B0Twin"]
    print("B0Base n B0Twin, nonland (must be empty): %s"
          % (sorted(shared) or "none"))
    for name, _, _ in decks[2:]:
        d = names[name] ^ names["B0Base"]
        print("%-9s differs from B0Base by %d card names: %s"
              % (name, len(d), ", ".join(sorted(d))))


if __name__ == "__main__":
    main()
