"""Rung 0 deck builder — vanilla mono-colour creatures, no instants.

The curriculum's design rule is ONE VARIABLE PER RUNG, implemented as a
controlled substitution: every deck below is the same 60-card shell with
one thing changed, so a performance drop has exactly one candidate
cause. That is what every prior phase lacked (7c swapped whole
archetypes, 8b swapped 12 cards at once, P10 varied decks + pool +
gating simultaneously).

Three decks:

  R0Base   the training deck. Mono-red, 24 Mountain + 36 vanilla
           creatures on a curve with deliberately mixed P/T, so
           "attack?" and "which blocker?" have board-dependent right
           answers rather than card-dependent ones.

  R0Twin   TRANSFER TEST A — functional twin. Every creature replaced by
           a DIFFERENT card with identical mana cost and identical P/T.
           The two decks are strategically indistinguishable: same
           curve, same combat math, same everything except names. Any
           performance drop is therefore PURE card-identity dependence,
           with no strategic confound available to explain it away.
           This is the sharpest possible version of Phase 8b's
           "features are consumed as local identifiers" finding, which
           was inferred from a 12-card swap where roles only
           approximately matched.

  R0Novel  TRANSFER TEST B — novel stat lines. Same colour, same curve
           shape, P/T combinations that never appear in training. Tests
           whether the agent learned combat MATH or a lookup table over
           the specific creatures it saw.

Card pool is read from the pin's own database (rl/r0_scan.txt, produced
by the VanillaScan utility): truly vanilla (empty rules text),
mono-colour, integer P/T, non-legendary. Legendaries are excluded
because four copies would trigger the legend rule and silently change
combat - the exact kind of hidden variable this rung exists to avoid.

Run: python3 rl/r0_decks.py [--scan rl/r0_scan.txt] [--out-dir rl]
"""
import argparse
import collections
import re

COLOUR = "R"
LAND = "Mountain"
N_LAND = 24

# (cmc, power, toughness, copies) — the curve.
#
# The 4/1 vs 2/3 vs 2/2 triangle is the point of the design: a 4/1
# trades up into anything but dies to a 1/1 chump; a 2/3 blocks 2/2s and
# 4/1s profitably; a 2/2 is the baseline. Whether to attack, and which
# blocker to assign, therefore depends on the BOARD rather than on which
# card is which - which is exactly the skill being probed.
#
# Stats skew toward power > toughness on purpose: vanilla creatures with
# no removal and no evasion is the classic board-stall configuration,
# and stalls would run games to stopTurn and wreck the rung. Aggressive
# bodies make attacks trade, trades turn boards over, and games end.
BASE_CURVE = [
    (1, 1, 1, 4),
    (2, 2, 2, 8),
    (3, 3, 2, 4),
    (3, 4, 1, 4),
    (3, 2, 3, 4),
    (4, 3, 3, 8),
    (5, 4, 4, 4),
]

# R0Novel: same cmc slots and same copy counts, P/T never seen in
# training. Kept mono-colour and same-cost so the ONLY difference is the
# stat line.
# Every target below is a stat line that EXISTS in the mono-red vanilla
# pool and does NOT appear in R0Base, so the deck is buildable from real
# cards while sharing no P/T with training. Same cmc slots, same copy
# counts, same colour: the stat line is the only thing that moves.
NOVEL_PT = {
    (1, 1, 1): (2, 1),      # 1cmc: aggressive instead of even
    (2, 2, 2): (2, 1),      # 2cmc: glass cannon instead of baseline
    (3, 3, 2): (4, 2),      # 3cmc: bigger both ways
    (3, 4, 1): (3, 3),      # 3cmc: even instead of glass cannon
    (3, 2, 3): (2, 2),      # 3cmc: loses the wall role
    (4, 3, 3): (4, 3),      # 4cmc: attacks past 3/3, dies to 3/3 pairs
    (5, 4, 4): (5, 4),      # 5cmc: bigger top end
}


def load_pool(path):
    """name -> (colour, cmc, power, toughness), vanilla non-legendary."""
    pool = []
    for line in open(path):
        if not line.startswith("V|"):
            continue
        _, name, mc, pt, _set = line.rstrip("\n").split("|")
        syms = re.findall(r"\{([^}]*)\}", mc)
        if not syms:
            continue
        cols = {s for s in syms if s in "WUBRG"}
        if len(cols) != 1 or any("/" in s for s in syms):
            continue                      # mono-colour, no hybrid/phyrexian
        cmc = sum(int(s) if s.isdigit() else 1 for s in syms)
        try:
            p, t = (int(x) for x in pt.split("/"))
        except ValueError:
            continue
        pool.append((name, cols.pop(), cmc, p, t))
    return pool


def index(pool, colour):
    by = collections.defaultdict(list)
    for name, c, cmc, p, t in pool:
        if c == colour:
            by[(cmc, p, t)].append(name)
    for k in by:
        by[k].sort()                      # deterministic
    return by


MAX_COPIES = 4


def build(by, curve, arm):
    """arm=0 -> base cards, arm=1 -> the functional twins.

    A slot of N copies is spread over ceil(N/4) DISTINCT cards, because
    four copies is the constructed limit and eight of one card would be
    an illegal list nobody could reproduce. The twin arm then takes the
    NEXT block of cards for the same stat line, so base and twin never
    share a card while sharing every stat line exactly.
    """
    out, missing = [], []
    for cmc, p, t, copies in curve:
        need = (copies + MAX_COPIES - 1) // MAX_COPIES
        cards = by.get((cmc, p, t), [])
        if len(cards) < need * (arm + 1):
            missing.append((cmc, p, t, "need %d have %d" % (need * (arm + 1), len(cards))))
            continue
        chosen = cards[arm * need:(arm + 1) * need]
        left = copies
        for card in chosen:
            n = min(MAX_COPIES, left)
            out.append((n, card, cmc, p, t))
            left -= n
    return out, missing


def write_deck(path, name, entries, n_land=N_LAND, land=LAND):
    with open(path, "w") as fh:
        fh.write("NAME:%s\n" % name)
        for copies, card, _cmc, _p, _t in entries:
            fh.write("%d [] %s\n" % (copies, card))
        fh.write("%d [] %s\n" % (n_land, land))
    return sum(c for c, *_ in entries) + n_land


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", default="/home/user/CardGuru/rl/r0_scan.txt")
    ap.add_argument("--out-dir", default="/home/user/CardGuru/rl")
    args = ap.parse_args()

    pool = load_pool(args.scan)
    by = index(pool, COLOUR)
    print("mono-%s vanilla non-legendary stat lines: %d" % (COLOUR, len(by)))

    novel_curve = [(cmc, *NOVEL_PT[(cmc, p, t)], copies)
                   for cmc, p, t, copies in BASE_CURVE]

    for deck_name, curve, pick in [("R0Base", BASE_CURVE, 0),
                                   ("R0Twin", BASE_CURVE, 1),
                                   ("R0Novel", novel_curve, 0)]:
        entries, missing = build(by, curve, pick)
        if missing:
            print("  %-8s MISSING slots (cmc,p,t,available): %s"
                  % (deck_name, missing))
            continue
        path = "%s/%s.dck" % (args.out_dir, deck_name)
        total = write_deck(path, deck_name, entries)
        print("  %-8s %d cards -> %s" % (deck_name, total, path))
        for copies, card, cmc, p, t in entries:
            print("      %dx %-28s %dcmc %d/%d" % (copies, card, cmc, p, t))


if __name__ == "__main__":
    main()
