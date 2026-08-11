"""Holdout analog finder: for each training-pool card, rank candidate
functional analogs by distance in E2 feature space (the graph readout
the treatment arm sees), constrained to same mana value and a
color-compatible cost. The A/B's holdout decks are built from these -
cards E0 has never hashed, but which land at (or near) the same point
in E2 space as a trained card.

Run: PYTHONPATH=/home/user/CardGuru python3 rl/holdout_pick.py
"""
import gzip
import json

POOL = {
    "burn": ["Goblin Guide", "Jackal Pup", "Monastery Swiftspear",
             "Keldon Marauders", "Lightning Bolt", "Lava Spike", "Shock",
             "Incinerate", "Skullcrack"],
    "control": ["Counterspell", "Cancel", "Essence Scatter", "Doom Blade",
                "Murder", "Divination", "Mind Rot", "Air Elemental",
                "Sengir Vampire"],
    "midrange": ["Llanowar Elves", "Nessian Courser", "Rumbling Baloth",
                 "Craw Wurm", "Giant Growth", "Vastwood Gorger",
                 "Prey Upon", "Titanic Growth", "Grizzly Bears"],
}
ALL_POOL = {c for cards in POOL.values() for c in cards}
# the Dimir training deck's cards are also off-limits as "unseen"
DIMIR = ["Bitter Triumph", "Elektra, Daughter of the Hand",
         "Cecil, Dark Knight", "Floodpits Drowner", "Nowhere to Run",
         "Requiting Hex", "Shoot the Sheriff", "Kaito, Bane of Nightmares",
         "Spell Snare", "Spyglass Siren", "The Wondrous Wasp",
         "Enduring Curiosity", "We Say Thee Nay!", "Spell Pierce",
         "Day of Black Sun"]
ALL_POOL |= set(DIMIR)


def mv(cost):
    total = 0
    for tok in (cost or "").split():
        total += int(tok) if tok.isdigit() else 1
    return total


def colors(cost):
    return {c for c in (cost or "") if c in "WUBRG"}


def main():
    feats = {}
    with open("/home/user/CardGuru/rl/e2_features.tsv") as f:
        dim = int(f.readline())
        for line in f:
            name, _, vec = line.rstrip("\n").partition("\t")
            feats[name] = tuple(float(x) for x in vec.split(","))

    cards = {}
    with gzip.open("/home/user/CardGuru/data/dataset.jsonl.gz", "rt") as f:
        f.readline()
        for line in f:
            r = json.loads(line)
            if r.get("faceIndex"):        # front faces only for candidates
                continue
            cards[r["name"]] = r

    for arch, pool in POOL.items():
        print(f"\n===== {arch} =====")
        for name in pool:
            src = cards.get(name)
            fv = feats.get(name)
            if not src or not fv:
                print(f"{name}: MISSING from graph")
                continue
            smv, scol = mv(src.get("manaCost")), colors(src.get("manaCost"))
            stypes = src.get("types") or ""
            ranked = []
            for cn, cr in cards.items():
                if cn in ALL_POOL or cn == name or cn not in feats:
                    continue
                if mv(cr.get("manaCost")) != smv:
                    continue
                if colors(cr.get("manaCost")) != scol:
                    continue
                ct = cr.get("types") or ""
                if ("Creature" in stypes) != ("Creature" in ct):
                    continue
                if ("Instant" in stypes) != ("Instant" in ct):
                    continue
                if ("Sorcery" in stypes) != ("Sorcery" in ct):
                    continue
                d = sum(1 for a, b in zip(fv, feats[cn]) if a != b)
                pt_bonus = 0
                if src.get("pt") and cr.get("pt") == src.get("pt"):
                    pt_bonus = -0.5      # same stats sorts first
                ranked.append((d + pt_bonus, cn, cr.get("pt") or ""))
            ranked.sort()
            tops = ", ".join(f"{n}[{p}](d={d:g})" if p else f"{n}(d={d:g})"
                             for d, n, p in ranked[:8])
            print(f"{name} ({src.get('manaCost')}, {src.get('pt')}): {tops}")


if __name__ == "__main__":
    main()
