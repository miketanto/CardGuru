"""Phase 8 swap-card picker: for each BenchDimir nonland card slated for
replacement, rank candidate analogs by E2 feature distance (the exact
representation the attn arm sees), constrained to same mana value, same
color identity of cost, and same major type split — the holdout_pick.py
notion of "functionally similar", plus Phase 8's extra gates:

  1. implemented in the XMage pin (SetCardInfo scan, like m3_decks.py);
  2. present in data/dataset.jsonl.gz AND rl/e2_features.tsv;
  3. seen in NOBODY's training data: every card of every committed deck
     (Bench*, M3*, Holdout*) is excluded;
  4. no delve/escape/flashback/graveyard-cast mechanics (getPlayable OOM
     class, PHASE5-M3.md) — filtered on the Forge script keywords;
  5. single-faced only (multi-face cards need XMage name-join checks
     that aren't worth the risk for a swap experiment).

Run: PYTHONPATH=/home/user/CardGuru python3 rl/p8_swap_pick.py [card ...]
Prints top-10 analogs per requested card (default: every BenchDimir
nonland card).
"""
import glob
import gzip
import json
import os
import re
import sys

REPO = "/home/user/CardGuru"
SETS_DIR = "/home/user/mage/Mage.Sets/src/mage/sets"
FEATURES = os.path.join(REPO, "rl/e2_features.tsv")
DATASET = os.path.join(REPO, "data/dataset.jsonl.gz")

SET_CODE_RE = re.compile(r'super\("[^"]*",\s*"([A-Z0-9]{2,6})"')
CARD_INFO_RE = re.compile(r'new SetCardInfo\("([^"]+)",\s*(\d+)')

# graveyard-cast mechanics that explode getPlayable (PHASE5-M3 OOM class)
HAZARD_KW = re.compile(
    r"\b(delve|escape|flashback|unearth|jump-start|retrace|aftermath|"
    r"disturb|embalm|eternalize|madness|dredge|scavenge|encore|"
    r"recover|retrace)\b", re.I)

DECK_LINE = re.compile(r"^\d+ \[[A-Z0-9]+:\w+\] (.+)$")


def deck_cards():
    seen = set()
    for pat in ("rl/*.dck", "rl/m3_decks/*.dck", "benchmark/xmage/*.dck"):
        for path in glob.glob(os.path.join(REPO, pat)):
            for line in open(path, encoding="utf-8"):
                m = DECK_LINE.match(line.strip())
                if m:
                    seen.add(m.group(1))
    return seen


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


def mv(cost):
    total = 0
    for tok in (cost or "").split():
        total += int(tok) if tok.isdigit() else 1
    return total


def colors(cost):
    return {c for c in (cost or "") if c in "WUBRG"}


def main():
    feats = {}
    with open(FEATURES) as f:
        f.readline()
        for line in f:
            name, _, vec = line.rstrip("\n").partition("\t")
            feats[name] = tuple(float(x) for x in vec.split(","))

    cards, multiface = {}, set()
    with gzip.open(DATASET, "rt") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            if r.get("faceIndex"):
                multiface.add(r.get("file") or r["name"])
                continue
            cards[r["name"]] = r
    for r in list(cards.values()):
        if (r.get("file") or r["name"]) in multiface:
            r["_multi"] = True

    impl = scan_sets()
    excl = deck_cards()
    dimir = [c for c in excl_deck("rl/BenchDimir.dck")]

    targets = sys.argv[1:] or dimir
    for name in targets:
        src = cards.get(name)
        fv = feats.get(name)
        if not src or not fv:
            print(f"{name}: MISSING (dataset={bool(src)} feats={bool(fv)})")
            continue
        smv, scol = mv(src.get("manaCost")), colors(src.get("manaCost"))
        stypes = src.get("types") or ""
        ranked = []
        for cn, cr in cards.items():
            if cn in excl or cn == name or cn not in feats or cn not in impl:
                continue
            if cr.get("_multi"):
                continue
            if mv(cr.get("manaCost")) != smv:
                continue
            if colors(cr.get("manaCost")) != scol:
                continue
            ct = cr.get("types") or ""
            keep = True
            for t in ("Creature", "Instant", "Sorcery", "Planeswalker",
                      "Enchantment", "Land", "Artifact"):
                if (t in stypes) != (t in ct):
                    keep = False
                    break
            if not keep:
                continue
            script = json.dumps(cr)
            if HAZARD_KW.search(script):
                continue
            d = sum(1 for a, b in zip(fv, feats[cn]) if a != b)
            pt_bonus = -0.5 if src.get("pt") and cr.get("pt") == src.get("pt") else 0
            code, num = impl[cn]
            ranked.append((d + pt_bonus, d, cn, cr.get("pt") or "",
                           f"{code}:{num}"))
        ranked.sort()
        hdr = f"{name} ({src.get('manaCost')}, {src.get('pt') or '-'}, {stypes})"
        print(f"\n{hdr}")
        for score, d, cn, pt, setnum in ranked[:10]:
            print(f"    d={d:2d}  {cn:<40} {pt or '-':>7}  [{setnum}]")


def excl_deck(rel):
    names = []
    for line in open(os.path.join(REPO, rel), encoding="utf-8"):
        m = DECK_LINE.match(line.strip())
        if m and m.group(1) not in ("Island", "Swamp", "Plains", "Mountain",
                                    "Forest"):
            names.append(m.group(1))
    seen = set()
    return [n for n in names if not (n in seen or seen.add(n))]


if __name__ == "__main__":
    main()
