"""Phase 8: write the three BenchDimir swap variants.

Swaps chosen from rl/p8_swap_pick.py output (E2 nearest neighbors under
same-MV/color/type constraints; d = Hamming-ish feature distance).
Lands, Kaito, Cecil, Nowhere to Run, Day of Black Sun, Enduring
Curiosity stay fixed (no acceptable unseen analog or core engine).
Printings are re-resolved against the pin's set files, preferring
regular expansion codes over promo/custom sets.

Run: python3 rl/p8_decks.py   (writes rl/P8*.dck + copies into
     /home/user/mage/Mage.Tests/)
"""
import glob
import os
import re

SETS_DIR = "/home/user/mage/Mage.Sets/src/mage/sets"
REPO = "/home/user/CardGuru"
SET_CODE_RE = re.compile(r'super\("[^"]*",\s*"([A-Z0-9]{2,6})"')
CARD_INFO_RE = re.compile(r'new SetCardInfo\("([^"]+)",\s*(\d+)')

# variant -> {original name: replacement name}; counts follow the
# original deck line.
SWAPS = {
    "P8SwapInteraction": {           # 12 cards: the interaction suite
        "Bitter Triumph": "Go for the Throat",       # d=0  2x
        "Requiting Hex": "Cut Down",                 # d=2  4x
        "Shoot the Sheriff": "Eliminate",            # d=0  1x
        # Force Spike (first pick, d=0) calibrated hot: vs scripted
        # opponents that deploy on-curve tapped out, "unless pays {1}"
        # is a de-facto hard counter on ANY spell, where Snare only hits
        # MV2 — counters-only bisect .735 vs anchor .620. Dispel keeps
        # d=0 with a narrow slice (instants) like Snare's (MV2).
        "Spell Snare": "Dispel",                     # d=0  1x
        "We Say Thee Nay!": "Don't Make a Sound",    # d=0  3x
        "Spell Pierce": "Stubborn Denial",           # d=0  1x
    },
    "P8SwapThreats": {               # 12 cards: threats, flash kept flash
        "Floodpits Drowner": "Zephyr Sentinel",      # d=4  4x flash 2/1
        "The Wondrous Wasp": "Plumecreed Escort",    # d=1  3x flash 2/1 fly
        "Spyglass Siren": "Faerie Seer",             # d=2  4x 1/1 fly ETB
        "Elektra, Daughter of the Hand":
            "Fathom Fleet Cutthroat",                # d=0  1x 3/3 ETB kill
    },
    "P8SwapMixed": {                 # 12 cards: both halves, all-new cards
        "Bitter Triumph": "Easy Prey",               # d=0  2x
        "Shoot the Sheriff": "Cradle to Grave",      # d=0  1x
        "We Say Thee Nay!": "Clash of Wills",        # d=0  3x
        "Spell Pierce": "Concerted Defense",         # d=0  1x
        "Spyglass Siren": "Faerie Miscreant",        # d=2  4x
        "Elektra, Daughter of the Hand":
            "Ravenous Chupacabra",                   # d=0  1x
    },
}

# promo-ish / custom set codes to avoid when a regular printing exists
def printing_rank(code):
    if code in ("XANA", "OANA", "PRM", "F16", "J25", "J22", "PHUK"):
        return 3
    if code.startswith("P") or code.startswith("O") or code.startswith("F"):
        return 2
    return 0 if len(code) == 3 else 1


def scan_all():
    printings = {}
    for f in glob.glob(os.path.join(SETS_DIR, "*.java")):
        text = open(f, encoding="utf-8", errors="replace").read()
        m = SET_CODE_RE.search(text)
        if not m:
            continue
        code = m.group(1)
        for name, num in CARD_INFO_RE.findall(text):
            printings.setdefault(name, []).append((code, num))
    return printings


def main():
    printings = scan_all()
    src = open(os.path.join(REPO, "rl/BenchDimir.dck"), encoding="utf-8").read().splitlines()
    for deck, swaps in SWAPS.items():
        out, used = [], set()
        for line in src:
            m = re.match(r"^(\d+) \[[A-Z0-9]+:\w+\] (.+)$", line.strip())
            if not m:
                out.append("NAME:" + deck if line.startswith("NAME:") else line)
                continue
            n, name = m.group(1), m.group(2)
            if name in swaps:
                new = swaps[name]
                best = sorted(printings[new],
                              key=lambda cn: (printing_rank(cn[0]), cn[0]))[0]
                out.append(f"{n} [{best[0]}:{best[1]}] {new}")
                used.add(name)
            else:
                out.append(line)
        assert used == set(swaps), f"{deck}: unmatched {set(swaps)-used}"
        total = sum(int(l.split()[0]) for l in out if re.match(r"^\d", l))
        assert total == 60, f"{deck}: {total} cards"
        content = "\n".join(out) + "\n"
        for d in (os.path.join(REPO, "rl"), "/home/user/mage/Mage.Tests"):
            with open(os.path.join(d, deck + ".dck"), "w") as f:
                f.write(content)
        swapped = sum(int(l.split()[0]) for l in out
                      if re.match(r"^\d", l)
                      and l.split(None, 2)[2] in swaps.values())
        print(f"{deck}: swapped {swapped} cards, 60 total")
    # feature-row sanity: every replacement must have a NONZERO e2 row
    feats = {}
    with open(os.path.join(REPO, "rl/e2_features.tsv")) as f:
        f.readline()
        for line in f:
            nm, _, vec = line.rstrip("\n").partition("\t")
            feats[nm] = any(float(x) for x in vec.split(","))
    for deck, swaps in SWAPS.items():
        for new in swaps.values():
            assert feats.get(new), f"{new}: missing/zero e2 feature row!"
    print("all replacements have nonzero e2 feature rows")


if __name__ == "__main__":
    main()
