"""Phase 8b step 2: deck-randomized TRAINING pool.

Generates N (default 24) BenchDimir variants for fine-tuning. Each deck
swaps a random 8-12 nonland cards (Kaito/Cecil/lands fixed, as in the
Phase 8 eval variants) for E2-nearest analogs sampled from each slot's
top-8 candidate list. The eval decks (P8Swap*, P8Faeries) and all
their cards stay HELD OUT: the candidate filter excludes every card of
every committed deck under rl/ and benchmark/, which includes them.

Purpose: a policy that sees a different deck every episode cannot
solve the task from deck-structure memorization; the card-feature
channel becomes the only stable signal — the E0 control arm cannot
exploit it, the E2 arm can. Deck power varies across the pool but
every game is a mirror, so training stays symmetric.

Run: python3 rl/p8b_pool.py [--n 24]
     (writes rl/p8b_pool/P8BTrain*.dck + copies into Mage.Tests)
"""
import argparse
import glob
import gzip
import json
import os
import random
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
FIXED = {"Kaito, Bane of Nightmares", "Cecil, Dark Knight"}
BASICS = {"Island", "Swamp", "Plains", "Mountain", "Forest"}


def printing_rank(code):
    if code in ("XANA", "OANA", "PRM", "F16", "F11", "J25", "J22", "PHUK"):
        return 3
    if code[:1] in "POF":
        return 2
    return 0 if len(code) == 3 else 1


def mv(cost):
    return sum(int(t) if t.isdigit() else 1 for t in (cost or "").split())


def colors(cost):
    return {c for c in (cost or "") if c in "WUBRG"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=24)
    args = ap.parse_args()

    printings = {}
    for f in glob.glob(os.path.join(SETS_DIR, "*.java")):
        text = open(f, encoding="utf-8", errors="replace").read()
        m = SET_CODE_RE.search(text)
        if not m:
            continue
        for name, num in CARD_INFO_RE.findall(text):
            printings.setdefault(name, []).append((m.group(1), num))

    excl = set()
    for pat in ("rl/*.dck", "rl/m3_decks/*.dck", "benchmark/xmage/*.dck"):
        for p in glob.glob(os.path.join(REPO, pat)):
            for line in open(p):
                m = DECK_LINE.match(line.strip())
                if m:
                    excl.add(m.group(2))

    feats = {}
    with open(os.path.join(REPO, "rl/e2_features.tsv")) as f:
        f.readline()
        for line in f:
            nm, _, vec = line.rstrip("\n").partition("\t")
            feats[nm] = tuple(float(x) for x in vec.split(","))

    cards, multiface = {}, set()
    with gzip.open(os.path.join(REPO, "data/dataset.jsonl.gz"), "rt") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            if r.get("faceIndex"):
                multiface.add(r.get("file") or r["name"])
                continue
            cards[r["name"]] = r

    src_lines = open(os.path.join(REPO, "rl/BenchDimir.dck")).read().splitlines()
    slots = []          # (line index, name)
    for i, line in enumerate(src_lines):
        m = DECK_LINE.match(line.strip())
        if not m:
            continue
        name = m.group(2)
        rec = cards.get(name)
        if (name in BASICS or name in FIXED or not rec
                or "Land" in (rec.get("types") or "")):
            continue
        slots.append((i, name))

    # top-8 analog candidates per swappable slot (same gates as the
    # Phase 8 eval picker)
    cand = {}
    for _, name in slots:
        src, fv = cards[name], feats.get(name)
        smv, scol = mv(src.get("manaCost")), colors(src.get("manaCost"))
        stypes = src.get("types") or ""
        ranked = []
        for cn, cr in cards.items():
            if cn in excl or cn == name or cn not in feats or cn not in printings:
                continue
            if (cr.get("file") or cn) in multiface:
                continue
            if mv(cr.get("manaCost")) != smv or colors(cr.get("manaCost")) != scol:
                continue
            ct = cr.get("types") or ""
            if any((t in stypes) != (t in ct) for t in
                   ("Creature", "Instant", "Sorcery", "Planeswalker",
                    "Enchantment", "Land", "Artifact")):
                continue
            if HAZARD_KW.search(json.dumps(cr)):
                continue
            d = sum(1 for a, b in zip(fv, feats[cn]) if a != b)
            pt_bonus = -0.5 if src.get("pt") and cr.get("pt") == src.get("pt") else 0
            ranked.append((d + pt_bonus, cn))
        ranked.sort()
        cand[name] = [cn for _, cn in ranked[:8]]

    rng = random.Random(2024)
    outdir = os.path.join(REPO, "rl/p8b_pool")
    os.makedirs(outdir, exist_ok=True)
    decks = []
    for k in range(args.n):
        nswap = rng.randint(8, 12)
        # sample slots until the swapped COPY COUNT reaches nswap
        order = rng.sample(slots, len(slots))
        chosen, count = {}, 0
        for i, name in order:
            if count >= nswap or not cand.get(name):
                continue
            chosen[i] = rng.choice(cand[name])
            count += int(DECK_LINE.match(src_lines[i].strip()).group(1))
        deck = f"P8BTrain{k:02d}"
        out = []
        for i, line in enumerate(src_lines):
            if line.startswith("NAME:"):
                out.append("NAME:" + deck)
            elif i in chosen:
                m = DECK_LINE.match(line.strip())
                new = chosen[i]
                code, num = sorted(printings[new],
                                   key=lambda cn: (printing_rank(cn[0]), cn[0]))[0]
                out.append(f"{m.group(1)} [{code}:{num}] {new}")
            else:
                out.append(line)
        total = sum(int(l.split()[0]) for l in out if re.match(r"^\d", l))
        assert total == 60, (deck, total)
        content = "\n".join(out) + "\n"
        for d in (outdir, "/home/user/mage/Mage.Tests"):
            with open(os.path.join(d, deck + ".dck"), "w") as fo:
                fo.write(content)
        decks.append(deck)
        print(deck, "swapped", count)
    with open(os.path.join(outdir, "pool_list.txt"), "w") as fo:
        fo.write(",".join(d + ".dck" for d in decks) + "\n")
    print(f"{len(decks)} training decks -> {outdir}")


if __name__ == "__main__":
    main()
