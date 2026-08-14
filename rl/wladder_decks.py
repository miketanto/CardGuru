"""The white trunk of the curriculum ladder: rungs 0-5, one variable each.

WHY WHITE, AND WHY ONE SLOT
---------------------------
A rung must change exactly one thing. For a keyword rung that means
swapping vanilla creatures for creatures with the SAME mana cost and the
SAME power/toughness that differ only by a keyword. Scanning the pin for
mono-colour creatures whose entire rules text is one keyword, and keeping
only stat lines that also have >=2 distinct vanilla cards (so a control
arm exists), gives:

    colour   fly  1st  vig  lif  dth  trm  men  hst
    W          4    1    2    5    0    1    0    0
    U          5    0    0    0    0    0    0    0
    B          1    0    0    2    2    0    1    0
    R          1    0    1    0    0    3    0    5
    G          0    0    3    0    1    9    0    0

No colour covers everything, and more importantly no colour except white
puts several keywords on ONE stat line. White's 2cmc 2/2 slot has:

    6 vanilla   Fresh Volunteers, Glory Seeker, Knight Errant,
                Shrine Keeper, Silvercoat Lion, Traveling Philosopher
    flying      Leonin Skyhunter, Silverbeak Griffin
    first str   Head of Security
    vigilance   Sun Sentinel, Alpine Watchdog, +4 more
    lifelink    Mesa Unicorn, Ajani's Sunstriker, +4 more

That single slot is the whole keyword ladder. Every keyword rung is the
SAME four cards of the SAME deck replaced by a 2/2 that costs the same
and differs by one word, which makes the rungs comparable to each other
and not merely to rung 0. Six vanilla cards is exactly enough to fill
three disjoint roles: 2 for the base deck, 2 for the twin, 2 for the
keyword rungs' control arm.

WHY THE TIMING RUNG IS ALSO WHITE
---------------------------------
Scanning cheap single-line instants and sorceries for the same effect
printed at both speeds turns up a white pair at identical cost:

    Take Vengeance  {1}{W} SORCERY  destroy target tapped creature
    Swift Response  {1}{W} INSTANT  destroy target tapped creature

Same colour, same cost, same text, same deck slot. The only variable
between rung 3 and rung 4 is WHEN the card may be cast, which is the
cleanest possible probe for whether the policy has learned priority.

WHAT THE LADDER DELIBERATELY DOES NOT DO
----------------------------------------
There is no W0Novel. Rung 0's novel-stat-line transfer test needs a deck
of unseen P/T at the same curve; white's vanilla pool is 25 stat lines
but shallow and lopsided (its only 5cmc line is 3/5, its only novel 2cmc
lines have one card each, and the rest are 1/7 and 2/10 walls). Forcing
one would smuggle a strategic change - a wall deck - in beside the stat
lines and defeat the point. That probe stays in red, where R0Base /
R0Twin / R0Novel already exist and are gated; red doubles as a
colour-transfer arm for rung 0.

Run: python3 rl/wladder_decks.py [--out-dir rl]
"""
import argparse
import collections
import os

PLAINS = ("Plains", "FDN:272")
N_LAND = 24

# ---------------------------------------------------------------- rung 0
# (cmc, power, toughness, copies, [base cards], [twin cards])
#
# Curve tops out at 4 and skews power>toughness. Vanilla creatures with
# no removal and no evasion is the classic board-stall configuration, and
# a stall runs the game to stopTurn and wrecks the rung; R0's gate showed
# an aggressive curve fixes it (0/40 stalls, ~15 turns). The 3/1 vs 2/3
# vs 2/2 triangle is the point of the design: a 3/1 trades up but dies to
# anything, a 2/3 eats both, a 2/2 is the baseline - so "attack?" and
# "block with which?" depend on the BOARD, not on which card is which.
SHELL = [
    (1, 2, 1, 4, [("Elite Vanguard", "EMA:8")],
                 [("Savannah Lions", "J22:237")]),
    # ---- THE LADDER SLOT: every rung >=1 swaps the second block here ----
    (2, 2, 2, 8, [("Glory Seeker", "W17:2"), ("Silvercoat Lion", "M11:31")],
                 [("Fresh Volunteers", "MMQ:20"), ("Knight Errant", "S00:7")]),
    (2, 3, 1, 8, [("Blade of the Sixth Pride", "FUT:19"),
                  ("Dromoka Warrior", "DTK:14")],
                 [("Oreskos Swiftclaw", "M15:22"),
                  ("Prowling Caracal", "RNA:17")]),
    (3, 3, 2, 4, [("Knight of the Keep", "ELD:19")],
                 [("Bastion Enforcer", "AER:8")]),
    (3, 2, 3, 4, [("Regal Unicorn", "POR:22")],
                 [("Alaborn Trooper", "ME4:2")]),
    (4, 3, 3, 4, [("Shu Elite Infantry", "PTK:22")],
                 [("Trokin High Guard", "P02:26")]),
    (4, 2, 4, 4, [("Foot Soldiers", "POR:16")],
                 [("Great Hart", "BNG:15")]),
]

# The block that every rung >=1 replaces: 4x Silvercoat Lion, 2cmc 2/2.
SWAP_CARD = ("Silvercoat Lion", "M11:31")
SWAP_N = 4

# ---------------------------------------------------------------- rung 1
# Same cost, same 2/2 body, one keyword. W1Ctrl is the control: the same
# four slots replaced by a DIFFERENT VANILLA 2/2, so "trained on a deck
# whose 2/2s changed name" is subtracted out and the residual is the
# keyword.
KEYWORD_RUNGS = [
    ("W1Fly",  ("Leonin Skyhunter", "MBS:11"),
     "flying - changes which blocks are LEGAL"),
    ("W1Fst",  ("Head of Security", "TRC:133"),
     "first strike - changes the MATH of a trade, not its legality"),
    ("W1Vig",  ("Sun Sentinel", "RIX:26"),
     "vigilance - removes the attack-vs-hold-back tradeoff"),
    ("W1Lif",  ("Mesa Unicorn", "J25:224"),
     "lifelink - changes the arithmetic of a race"),
    ("W1Ctrl", ("Shrine Keeper", "ANB:19"),
     "CONTROL: same swap, no keyword"),
]

# ---------------------------------------------------------------- rung 2
# Two keywords at once, in the two halves of the ladder slot. Tests
# composition: an agent that learned flying and lifelink separately is
# not thereby an agent that handles both. Control keeps the slot vanilla
# but uses the two control cards, so the card-identity change matches.
COMPOSITE = [
    ("W2FlyLif", [(("Leonin Skyhunter", "MBS:11"), 4),
                  (("Mesa Unicorn", "J25:224"), 4)],
     "flying + lifelink together"),
    ("W2Ctrl",   [(("Shrine Keeper", "ANB:19"), 4),
                  (("Traveling Philosopher", "THS:34"), 4)],
     "CONTROL for W2: both blocks swapped, no keywords"),
]

# ------------------------------------------------------------- rungs 3-5
# Spells replace the 4x Silvercoat Lion block, so creature count drops
# 36 -> 32 in all three. That is a real second change, and it is held
# CONSTANT across the three: W3/W4/W5 differ from each other by exactly
# one property of the spell, which is what the rungs actually compare.
#
#   W3 -> W4  the same card at instant speed instead of sorcery speed:
#             identical text, identical cost. Pure priority/timing.
#   W4 -> W5  removal replaced by a pump trick: the opponent now holds
#             cards that punish a block, so blocking becomes a decision
#             under hidden information rather than arithmetic.
SPELL_RUNGS = [
    ("W3Sorc",  ("Take Vengeance", "GN2:13"),
     "sorcery, destroy target tapped creature - removal, no timing"),
    ("W4Inst",  ("Swift Response", "J25:269"),
     "INSTANT, identical text and cost - the only variable is timing"),
    ("W5Trick", ("Aegis of the Heavens", "M19:1"),
     "instant, +1/+7 - blocking now risks a trick the agent cannot see"),
]


def shell_entries(arm):
    """arm 0 = base cards, arm 1 = twin cards."""
    out = []
    for cmc, p, t, copies, base, twin in SHELL:
        cards = (base, twin)[arm]
        left = copies
        for card in cards:
            n = min(4, left)
            out.append((n, card, cmc, p, t))
            left -= n
        assert left == 0, (cmc, p, t, copies, cards)
    return out


def swap(entries, replacements):
    """Drop SWAP_N copies of SWAP_CARD; add `replacements` in its place."""
    out, dropped = [], 0
    for n, card, cmc, p, t in entries:
        if card == SWAP_CARD:
            dropped += n
            continue
        out.append((n, card, cmc, p, t))
    assert dropped == SWAP_N, dropped
    return out + list(replacements)


def write_deck(path, name, entries):
    counts = collections.Counter()
    for n, card, *_ in entries:
        counts[card[0]] += n
    illegal = {c: k for c, k in counts.items() if k > 4}
    assert not illegal, "more than 4 copies: %s" % illegal
    total = sum(n for n, *_ in entries) + N_LAND
    assert total == 60, "%s has %d cards" % (name, total)
    with open(path, "w") as fh:
        fh.write("NAME:%s\n" % name)
        for n, card, *_ in entries:
            fh.write("%d [%s] %s\n" % (n, card[1], card[0]))
        fh.write("%d [%s] %s\n" % (N_LAND, PLAINS[1], PLAINS[0]))
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/home/user/CardGuru/rl")
    args = ap.parse_args()

    base = shell_entries(0)
    twin = shell_entries(1)
    decks = [("W0Base", base, "rung 0: vanilla combat"),
             ("W0Twin", twin, "rung 0 transfer: every card a different "
                              "card with the same cost and stat line")]

    for name, card, note in KEYWORD_RUNGS:
        decks.append((name, swap(base, [(SWAP_N, card, 2, 2, 2)]), note))
    for name, blocks, note in COMPOSITE:
        # W2 swaps BOTH 2/2 blocks, so start from a shell with neither.
        stripped = [e for e in base if e[1][0] not in
                    ("Silvercoat Lion", "Glory Seeker")]
        decks.append((name, stripped + [(n, c, 2, 2, 2) for c, n in blocks],
                      note))
    for name, card, note in SPELL_RUNGS:
        decks.append((name, swap(base, [(SWAP_N, card, 2, 0, 0)]), note))

    seen_cards = collections.defaultdict(set)
    for name, entries, note in decks:
        path = os.path.join(args.out_dir, name + ".dck")
        write_deck(path, name, entries)
        print("%-9s 60 cards  %s" % (name, note))
        for n, card, *_ in entries:
            seen_cards[name].add(card[0])

    # the twin claim has to be checked, not asserted
    # lands are written outside `entries`, so this set is spells only and
    # must come back empty - base and twin may share nothing but Plains.
    shared = seen_cards["W0Base"] & seen_cards["W0Twin"]
    print()
    print("W0Base n W0Twin, nonland (must be empty): %s"
          % (sorted(shared) or "none"))
    for name, _, _ in decks[2:]:
        d = seen_cards[name] ^ seen_cards["W0Base"]
        print("%-9s differs from W0Base by %d card names: %s"
              % (name, len(d), ", ".join(sorted(d))))


if __name__ == "__main__":
    main()
