"""Phase 7c: build + verify the archetype-curriculum decks that the M3
pool does not already cover.

The curriculum reuses 5 verified M3 decks (aggro / go-wide / ramp /
tempo / counter-control). The one axis M3 has no deck for is
"durdly control with SWEEPERS" - the skill the Dimir mirror never
demands is committing a board into a wrath. This script emits that
deck with the same guarantees m3_decks.py gives:

1. every card is implemented at the XMage pin (scanned from Mage.Sets),
2. every nonland card has E2 features in rl/e2_features.tsv,
3. no card on the M3 engine-hazard list (delve/escape enumerate
   graveyard subsets in getPlayable and OOM the heap; graveyard
   recursion and token-COPY engines were removed prophylactically).

Run: python3 rl/p7c_decks.py [--outdir /home/user/mage/Mage.Tests]
     (also writes copies to rl/m3_decks/ so restore/overlay picks it up)
"""
import argparse
import glob
import os
import re
import sys

SETS_DIR = "/home/user/mage/Mage.Sets/src/mage/sets"
FEATURES = "/home/user/CardGuru/rl/e2_features.tsv"

SET_CODE_RE = re.compile(r'super\("[^"]*",\s*"([A-Z0-9]{2,6})"')
CARD_INFO_RE = re.compile(r'new SetCardInfo\("([^"]+)",\s*(\d+)')

# M3 hazard list (PHASE5-M3.md): mechanics that blow up getPlayable or
# make the search opponent pathological. Audited by name here because
# the curriculum decks are hand-written, not generated.
HAZARD_TEXT = ("delve", "escape", "convoke")

DECKS = {
    # Azorius draw-go: 8 sweepers + 8 counters + 2 finishers. The whole
    # point is that curving out into it is PUNISHED - the agent's pure
    # race plan has to learn to hold back.
    "P7cSweepControl": ({"Plains": 13, "Island": 11}, [
        "Omenspeaker", "Essence Scatter", "Wall of Frost",
        "Cancel", "Divination", "Day of Judgment",
        "Wrath of God", "Serra Angel", "Windreader Sphinx"]),
}


def scan_sets():
    info = {}
    for f in glob.glob(os.path.join(SETS_DIR, "*.java")):
        text = open(f, encoding="utf-8", errors="replace").read()
        m = SET_CODE_RE.search(text)
        if not m:
            continue
        code = m.group(1)
        for name, num in CARD_INFO_RE.findall(text):
            info.setdefault(name, (code, num))
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="/home/user/mage/Mage.Tests")
    args = ap.parse_args()

    info = scan_sets()
    feats = set()
    with open(FEATURES) as f:
        f.readline()
        for line in f:
            feats.add(line.split("\t", 1)[0])

    problems = []
    os.makedirs("/home/user/CardGuru/rl/m3_decks", exist_ok=True)
    for deck, (lands, spells) in DECKS.items():
        assert len(spells) == 9, f"{deck}: needs exactly 9 spells"
        assert sum(lands.values()) == 24, f"{deck}: needs 24 lands"
        lines = [f"NAME:{deck}"]
        for name in spells:
            if name not in info:
                problems.append(f"{deck}: {name} NOT IMPLEMENTED at pin")
                continue
            if name not in feats:
                problems.append(f"{deck}: {name} missing from e2_features.tsv")
                continue
            low = name.lower()
            if any(h in low for h in HAZARD_TEXT):
                problems.append(f"{deck}: {name} matches hazard list")
                continue
            code, num = info[name]
            lines.append(f"4 [{code}:{num}] {name}")
        for land, n in lands.items():
            code, num = info[land]
            lines.append(f"{n} [{code}:{num}] {land}")
        if problems:
            continue
        body = "\n".join(lines) + "\n"
        for d in (args.outdir, "/home/user/CardGuru/rl/m3_decks"):
            with open(os.path.join(d, f"{deck}.dck"), "w") as fh:
                fh.write(body)
        print(f"{deck}: 9 spells x4 + {sum(lands.values())} lands -> ok")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(f"{len(problems)} problem(s); no deck written")


if __name__ == "__main__":
    main()
