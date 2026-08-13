"""Phase 8b lane 3: pin-era Standard meta deck approximations.

The actual August-2026 Standard meta uses sets newer than the XMage pin
(7554968c, ~late 2025), and deck sites are egress-blocked from this
container — so these are approximations of the LATE-2025 Standard meta
(the newest meta expressible at the pin), assembled from model
knowledge and screened card-by-card against the pin.

Screen per card: implemented at pin (SetCardInfo), present in
e2_features.tsv with a nonzero row, single-faced in the dataset, no
graveyard-cast hazard, and NOT a card of the held-out eval decks
(P8Swap*, P8Faeries) — overlap with *training* decks is fine.
Cards that fail are reported; decks are only written when every line
passes, so failures get hand-substituted in this file and re-run.

Run: python3 rl/p8b_meta.py [--check-only]
"""
import argparse
import glob
import gzip
import json
import os
import re

REPO = "/home/user/CardGuru"
SETS_DIR = "/home/user/mage/Mage.Sets/src/mage/sets"
SET_CODE_RE = re.compile(r'super\("[^"]*",\s*"([A-Z0-9]{2,6})"')
CARD_INFO_RE = re.compile(r'new SetCardInfo\("([^"]+)",\s*(\d+)')
DECK_LINE = re.compile(r"^(\d+) \[[A-Z0-9]+:\w+\] (.+)$")
HAZARD_KW = re.compile(
    r"\b(delve|escape|flashback|unearth|jump-start|retrace|aftermath|"
    r"disturb|embalm|eternalize|madness|dredge|scavenge|encore|recover)\b",
    re.I)
EVAL_DECKS = ("rl/P8SwapInteraction.dck", "rl/P8SwapThreats.dck",
              "rl/P8SwapMixed.dck", "rl/P8Faeries.dck")
BASICS = {"Plains", "Island", "Swamp", "Mountain", "Forest"}

# name -> [(count, card)]; 60 cards each
DECKS = {
    # mono-red mice aggro
    "P8MetaMonoRed": [
        (4, "Heartfire Hero"), (4, "Manifold Mouse"),
        (4, "Emberheart Challenger"), (4, "Screaming Nemesis"),
        (4, "Hired Claw"), (4, "Monstrous Rage"), (4, "Shock"),
        (3, "Lightning Strike"), (3, "Witchstalker Frenzy"),
        (2, "Sunspine Lynx"), (24, "Mountain")],
    # boros aggro
    "P8MetaBoros": [
        (4, "Slickshot Show-Off"), (4, "Inti, Seneschal of the Sun"),
        (4, "Monastery Swiftspear"), (4, "Phoenix Chick"),
        (4, "Boltwave"), (4, "Burst Lightning"), (3, "Felonious Rage"),
        (3, "Warleader's Call"), (4, "Inspiring Vantage"),
        (2, "Battlefield Forge"), (14, "Mountain"), (10, "Plains")],
    # golgari midrange
    "P8MetaGolgari": [
        (4, "Deep-Cavern Bat"), (4, "Preacher of the Schism"),
        (4, "Glissa Sunslayer"), (3, "Sentinel of the Nameless City"),
        (3, "Tranquil Frillback"), (4, "Bitter Triumph"),
        (3, "Murder"), (2, "Duress"),
        (4, "Llanowar Wastes"), (2, "Restless Cottage"),
        (14, "Swamp"), (13, "Forest")],
    # dimir bounce (pixie-lite, UB)
    "P8MetaDimirBounce": [
        (4, "This Town Ain't Big Enough"), (4, "Fear of Isolation"),
        (4, "Nurturing Pixie"), (4, "Stormchaser's Talent"),
        (4, "Nowhere to Run"), (3, "Bitter Triumph"),
        (2, "Kaito, Bane of Nightmares"), (2, "Enduring Curiosity"),
        (4, "Underground River"), (2, "Restless Reef"),
        (14, "Island"), (13, "Swamp")],
    # domain-lite (bant beans)
    "P8MetaDomain": [
        (4, "Up the Beanstalk"), (4, "Leyline Binding"),
        (4, "Overlord of the Hauntwoods"), (3, "Zur, Eternal Schemer"),
        (3, "Beza, the Bounding Spring"), (3, "Temporary Lockdown"),
        (3, "Get Lost"), (4, "Hedge Maze"), (4, "Lush Portico"),
        (4, "Meticulous Archive"), (8, "Forest"), (8, "Plains"),
        (8, "Island")],
    # azorius skies tempo
    "P8MetaAzorius": [
        (4, "Novice Inspector"), (4, "Optimistic Scavenger"),
        (4, "Sleep-Cursed Faerie"), (4, "Spectral Adversary"),
        (3, "Skrelv, Defector Mite"), (3, "Get Lost"),
        (3, "Spell Pierce"), (2, "Temporary Lockdown"),
        (4, "Adarkar Wastes"), (2, "Restless Anchorage"),
        (14, "Island"), (13, "Plains")],
}


def printing_rank(code):
    if code in ("XANA", "OANA", "PRM", "F16", "F11", "J25", "J22", "PHUK"):
        return 3
    if code[:1] in "POF":
        return 2
    return 0 if len(code) == 3 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    printings = {}
    for f in glob.glob(os.path.join(SETS_DIR, "*.java")):
        text = open(f, encoding="utf-8", errors="replace").read()
        m = SET_CODE_RE.search(text)
        if not m:
            continue
        for name, num in CARD_INFO_RE.findall(text):
            printings.setdefault(name, []).append((m.group(1), num))

    # held out = the eval decks' UNSEEN cards (replacements + faerie
    # spells). BenchDimir originals retained inside eval decks are
    # training-seen and stay legal for training pools.
    trained = set()
    for line in open(os.path.join(REPO, "rl/BenchDimir.dck")):
        m = DECK_LINE.match(line.strip())
        if m:
            trained.add(m.group(2))
    heldout = set()
    for rel in EVAL_DECKS:
        for line in open(os.path.join(REPO, rel)):
            m = DECK_LINE.match(line.strip())
            if m and m.group(2) not in BASICS and m.group(2) not in trained:
                heldout.add(m.group(2))

    feats = {}
    with open(os.path.join(REPO, "rl/e2_features.tsv")) as f:
        f.readline()
        for line in f:
            nm, _, vec = line.rstrip("\n").partition("\t")
            feats[nm] = any(float(x) for x in vec.split(","))

    recs, multiface = {}, set()
    with gzip.open(os.path.join(REPO, "data/dataset.jsonl.gz"), "rt") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            if r.get("faceIndex"):
                multiface.add(r.get("file") or r["name"])
                continue
            recs[r["name"]] = r

    problems = []
    for deck, cards in DECKS.items():
        total = sum(n for n, _ in cards)
        if total != 60:
            problems.append(f"{deck}: {total} cards")
        for _, name in cards:
            r = recs.get(name)
            errs = []
            if name not in printings:
                errs.append("NOT-IMPLEMENTED")
            if not r:
                errs.append("no-dataset")
            elif (r.get("file") or name) in multiface:
                errs.append("multiface")
            elif HAZARD_KW.search(json.dumps(r)):
                errs.append("hazard")
            if name not in BASICS and not feats.get(name):
                errs.append("no-feat")
            if name in heldout:
                errs.append("HELD-OUT-EVAL-CARD")
            if errs:
                problems.append(f"{deck}: {name}: {','.join(errs)}")
    if problems:
        print("PROBLEMS:")
        print("\n".join(problems))
        raise SystemExit(1)
    if args.check_only:
        print("all decks clean")
        return

    outdir = os.path.join(REPO, "rl/p8b_meta")
    os.makedirs(outdir, exist_ok=True)
    names = []
    for deck, cards in DECKS.items():
        lines = [f"NAME:{deck}"]
        for n, name in cards:
            code, num = sorted(printings[name],
                               key=lambda cn: (printing_rank(cn[0]), cn[0]))[0]
            lines.append(f"{n} [{code}:{num}] {name}")
        content = "\n".join(lines) + "\n"
        for d in (outdir, "/home/user/mage/Mage.Tests"):
            with open(os.path.join(d, deck + ".dck"), "w") as fo:
                fo.write(content)
        names.append(deck)
    with open(os.path.join(outdir, "meta_list.txt"), "w") as fo:
        fo.write(",".join(d + ".dck" for d in names) + "\n")
    print(f"{len(names)} meta decks -> {outdir}")


if __name__ == "__main__":
    main()
