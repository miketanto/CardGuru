"""Extract the FRA playable card list from Forge's edition file.

Output: JSON list of {name, number, rarity, sections} for every unique
non-token, non-basic card whose collector number is in the main set
(SPG special guests are a separate set code and excluded).
"""
import json, re, sys, collections

EDITION = sys.argv[1]
OUT = sys.argv[2]
SKIP = {"metadata", "tokens", "other", "special guests"}
BASICS = {"Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes"}

sec = None
cards = collections.OrderedDict()
for line in open(EDITION, encoding="utf-8"):
    line = line.rstrip("\n")
    m = re.match(r"^\[(.*)\]$", line)
    if m:
        sec = m.group(1); continue
    if sec in SKIP or not line.strip() or not line[0].isdigit():
        continue
    m = re.match(r"^(\d+)\s+(?:([CURMSLT])\s+)?(.+?)\s*(@.*)?$", line)
    if not m:
        continue
    num, rar, name = int(m.group(1)), m.group(2), m.group(3)
    name = name.split("|")[0].strip()
    if name in BASICS:
        continue
    c = cards.setdefault(name, {"name": name, "number": num, "rarity": rar, "sections": []})
    c["number"] = min(c["number"], num)
    c["rarity"] = c["rarity"] or rar
    if sec not in c["sections"]:
        c["sections"].append(sec)

# Booster-sheet sections (lines like "1 Name|FRA|[341]") carry typos
# ("Overwrite the Multivers", "Lyla, Tolarian Archangel", "Winter,
# Tormented Lover"). The canonical list is the [cards] section; sheet
# names absent from it are reported and dropped.
dropped = [n for n, c in cards.items() if "cards" not in c["sections"]]
for n in dropped:
    del cards[n]
print("dropped sheet-only names:", dropped)
json.dump(list(cards.values()), open(OUT, "w"), indent=1, ensure_ascii=False)
bysec = collections.Counter(s for c in cards.values() for s in c["sections"])
print(f"unique={len(cards)} maxnum={max(c['number'] for c in cards.values())}", dict(bysec))
