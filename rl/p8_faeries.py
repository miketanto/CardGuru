"""Phase 8 M2b: full-archetype transfer deck — UB Faeries.

Same *concept* as BenchDimir (UB flash-tempo: cheap evasive flash
threats, counters, instant-speed removal, a card-advantage engine) but
ZERO spell overlap with any committed deck: all 37 spells are unseen by
every policy. Lands are kept identical to BenchDimir to isolate
spell-side transfer from mana-base texture. Role structure mirrors the
trained deck: 23 lands / 22 threats / 15 interaction.

All spells verified: implemented at the XMage pin, present in
data/dataset.jsonl.gz + rl/e2_features.tsv (nonzero rows), absent from
every committed deck, no graveyard-cast mechanics (PHASE5-M3 OOM
class; prowl/champion/clash cards were deliberately skipped).

Run: python3 rl/p8_faeries.py  (writes rl/P8Faeries.dck + Mage.Tests copy)
"""
import glob
import os
import re

SETS_DIR = "/home/user/mage/Mage.Sets/src/mage/sets"
REPO = "/home/user/CardGuru"
SET_CODE_RE = re.compile(r'super\("[^"]*",\s*"([A-Z0-9]{2,6})"')
CARD_INFO_RE = re.compile(r'new SetCardInfo\("([^"]+)",\s*(\d+)')

# threats (22): all flash, echoing the trained deck's tempo plan
# interaction (15): tribal removal + counters at the same curve slots
SPELLS = [
    (4, "Spectral Sailor"),          # U    1/1 flash fly  ~Spyglass Siren
    (4, "Faerie Vandal"),            # 1U   1/2 flash fly  ~Wondrous Wasp
    (4, "Quickling"),                # 1U   2/2 flash fly  ~Floodpits Drowner
    (4, "Pestermite"),               # 2U   2/1 flash fly tap ~Drowner ETB
    (3, "Obyra, Dreaming Duelist"),  # UB   2/2 flash fly drain ~Cecil (3x legend)
    (3, "Slitherwisp"),              # UBB  3/2 flash draw engine ~Enduring Curiosity
    (3, "Spellstutter Sprite"),      # 1U   1/1 flash fly counter ~We Say Thee Nay!
    (2, "Faerie Trickery"),          # 1UU  counter non-Faerie ~counter suite
    (4, "Peppersmoke"),              # B    -1/-1 cantrip   ~Requiting Hex
    (3, "Agony Warp"),               # UB   -3/-0 & -0/-3   ~Bitter Triumph
    (2, "Eyeblight's Ending"),       # 2B   destroy non-Elf ~Shoot the Sheriff
    (1, "Nameless Inversion"),       # 1B   changeling +3/-3 ~removal 1-of
]

LANDS = [  # identical to BenchDimir
    "4 [DSK:260] Gloomlake Verge",
    "4 [MSH:269] Hidden Lair",
    "2 [FDN:133] Soulstone Sanctuary",
    "2 [LCI:282] Restless Reef",
    "3 [AFR:266] Island",
    "4 [AFR:270] Swamp",
    "4 [EOE:261] Watery Grave",
]


def printing_rank(code):
    if code in ("XANA", "OANA", "PRM", "F16", "F11", "J25", "J22", "PHUK"):
        return 3
    if code.startswith("P") or code.startswith("O") or code.startswith("F"):
        return 2
    return 0 if len(code) == 3 else 1


def main():
    printings = {}
    for f in glob.glob(os.path.join(SETS_DIR, "*.java")):
        text = open(f, encoding="utf-8", errors="replace").read()
        m = SET_CODE_RE.search(text)
        if not m:
            continue
        for name, num in CARD_INFO_RE.findall(text):
            printings.setdefault(name, []).append((m.group(1), num))

    feats = {}
    with open(os.path.join(REPO, "rl/e2_features.tsv")) as f:
        f.readline()
        for line in f:
            nm, _, vec = line.rstrip("\n").partition("\t")
            feats[nm] = any(float(x) for x in vec.split(","))

    lines = ["NAME:P8Faeries"]
    total = 0
    for n, name in SPELLS:
        assert name in printings, f"{name}: not implemented"
        assert feats.get(name), f"{name}: missing/zero e2 row"
        code, num = sorted(printings[name],
                           key=lambda cn: (printing_rank(cn[0]), cn[0]))[0]
        lines.append(f"{n} [{code}:{num}] {name}")
        total += n
    assert total == 37, total
    lines += LANDS
    content = "\n".join(lines) + "\n"
    for d in (os.path.join(REPO, "rl"), "/home/user/mage/Mage.Tests"):
        with open(os.path.join(d, "P8Faeries.dck"), "w") as f:
            f.write(content)
    print(content)


if __name__ == "__main__":
    main()
