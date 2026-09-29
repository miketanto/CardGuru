"""Parse Forge card scripts into structured records.

Forge scripts are flat line-oriented `Key:Value`. Ability-bearing lines
(A:, T:, S:, R:, and SVar: values that are themselves abilities) are
pipe-separated `Key$ Value` lists. This module does no interpretation:
it only splits, so the tallies downstream reflect what the scripts say.

A card is a list of faces (split / DFC / adventure / MDFC faces are
separated by a bare `ALTERNATE` line). Each face has:
  name, mana_cost, types, pt, loyalty, oracle, keywords,
  abilities: [{kind, id, api, params}]  -- A/T/S/R/SVar abilities
  svars:     {name: raw}                -- non-ability SVars (X counts, AI hints)
"""
import os, re, json

ABILITY_KEYS = ("AB$", "SP$", "DB$")          # effect abilities
MODE_KEYS = ("Mode$", "Event$")                # trigger / static / replacement
AI_SVARS = {"DeckHas", "DeckHints", "DeckNeeds", "AIPreference", "AIHints",
            "RemAIDeck", "RemRandomDeck", "PlayMain1", "AILogic", "NeedsToPlay",
            "NeedsToPlayVar", "HasAttackEffect", "HasCombatEffect", "MustBeBlocked",
            "BuffedBy", "SacMe", "EndOfTurnLeavePlay", "Picture", "NonStackingEffect",
            "MustAttack", "AIEvaluationModifier", "DiscardMe", "MayBeBlocked"}


def split_params(body):
    """'SP$ Draw | NumCards$ 2' -> [('SP','Draw'), ('NumCards','2')]"""
    out = []
    for part in body.split("|"):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\$\s*(.*)$", part, re.S)
        if m:
            out.append((m.group(1), m.group(2).strip()))
        elif out:  # a stray '|' inside a value: glue back on
            k, v = out[-1]
            out[-1] = (k, v + "|" + part)
    return out


def parse_ability(kind, ident, body):
    pairs = split_params(body)
    if not pairs:
        return None
    head_k, head_v = pairs[0]
    params = {}
    for k, v in pairs[1:]:
        params[k] = v if k not in params else params[k] + " ;; " + v
    return {"kind": kind, "id": ident, "head": head_k, "api": head_v, "params": params}


def cmc_of(cost):
    if not cost or cost == "no cost":
        return 0
    n = 0
    for sym in cost.split():
        if sym.isdigit():
            n += int(sym)
        elif sym in ("X", "Y", "Z"):
            continue
        else:
            n += 1  # W, U/B, 2/W (counts as 2 for CMC; approximate as 1), P
            if sym.startswith("2/"):
                n += 1
    return n


def colors_of(cost):
    return sorted({ch for ch in (cost or "") if ch in "WUBRG"})


def parse_face(lines):
    f = {"name": None, "mana_cost": None, "types": None, "pt": None, "loyalty": None,
         "oracle": None, "keywords": [], "abilities": [], "svars": {}, "other": {}}
    for raw in lines:
        line = raw.rstrip("\n")
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        if key == "Name": f["name"] = val.strip()
        elif key == "ManaCost": f["mana_cost"] = val.strip()
        elif key == "Types": f["types"] = val.strip()
        elif key == "PT": f["pt"] = val.strip()
        elif key == "Loyalty": f["loyalty"] = val.strip()
        elif key == "Oracle": f["oracle"] = val.strip()
        elif key == "K": f["keywords"].append(val.strip())
        elif key in ("A", "T", "S", "R"):
            ab = parse_ability(key, None, val)
            if ab: f["abilities"].append(ab)
        elif key == "SVar":
            name, _, sval = val.partition(":")
            sval = sval.strip()
            first = sval.split("|")[0].strip()
            if first.startswith(ABILITY_KEYS) or first.startswith(MODE_KEYS):
                ab = parse_ability("SVar", name, sval)
                if ab: f["abilities"].append(ab)
            else:
                f["svars"][name] = sval
        else:
            f["other"].setdefault(key, []).append(val.strip())
    f["cmc"] = cmc_of(f["mana_cost"])
    f["colors"] = colors_of(f["mana_cost"])
    return f


def parse_script(text):
    faces, cur, alt_mode = [], [], None
    for line in text.splitlines():
        if line.strip() == "ALTERNATE":
            faces.append(cur); cur = []
            continue
        if line.startswith("AlternateMode:"):
            alt_mode = line.split(":", 1)[1].strip()
        cur.append(line)
    faces.append(cur)
    parsed = [parse_face(fl) for fl in faces]
    return {"name": parsed[0]["name"], "alt_mode": alt_mode, "faces": parsed}


def build_index(cardsfolder):
    idx = {}
    for root, _, files in os.walk(cardsfolder):
        for fn in files:
            if not fn.endswith(".txt"):
                continue
            p = os.path.join(root, fn)
            with open(p, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("Name:"):
                        idx.setdefault(line[5:].strip(), p)
                        break
    return idx


if __name__ == "__main__":
    import sys
    cardsfolder, cardlist, out = sys.argv[1:4]
    idx = build_index(cardsfolder)
    wanted = json.load(open(cardlist, encoding="utf-8"))
    cards, missing = [], []
    for c in wanted:
        nm = c["name"]
        p = idx.get(nm) or idx.get(nm.split(" // ")[0])
        if not p:
            missing.append(nm); continue
        rec = parse_script(open(p, encoding="utf-8", errors="replace").read())
        rec.update({"set_number": c["number"], "rarity": c["rarity"],
                    "sections": c["sections"], "script": os.path.relpath(p, cardsfolder)})
        cards.append(rec)
    json.dump(cards, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"parsed={len(cards)} missing={len(missing)} {missing[:20]}")
