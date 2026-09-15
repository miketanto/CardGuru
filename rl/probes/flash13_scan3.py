"""13a flash check, colour: opponent-turn PRIORITY consults with a flash card in hand and >= 3 untapped own
lands. Tally the untapped land NAMES (sorted multiset) split by flash offered / not offered, and whether a
blue source is untapped (name contains Island, or a U dual by name)."""
import collections
import json
import sys

FLASH = {"Floodpits Drowner", "Enduring Curiosity", "The Wondrous Wasp", "Nowhere to Run"}
BLUE_WORDS = ("Island", "Watery", "Underground", "Darkslick", "Drowned", "Undercity", "Choked", "Sunken",
              "Fetid", "Shipwreck", "Morphic", "Gloomlake", "Creeping", "Tidehollow", "Restless Reef")
tal = collections.Counter()
blue = collections.Counter()
for p in sys.argv[1:]:
    for raw in open(p, "rb"):
        if b'"t":"consult"' not in raw:
            continue
        m = json.loads(raw)
        ct = m.get("v7_cand_type") or []
        g = m.get("v7_game") or []
        if not (set(ct) & {1, 2, 3}) or not (len(g) > 1 and g[1] < 0.5):
            continue
        ents = m.get("v7_ent") or []
        names = m.get("v7_ent_name") or []
        refs = m.get("v7_cand_refers") or [[] for _ in ct]
        if not any(i < len(names) and names[i] in FLASH and e[1] > 0.5 and e[7] > 0.5 for i, e in enumerate(ents)):
            continue
        lands = sorted(names[i] for i, e in enumerate(ents)
                       if i < len(names) and e[0] > 0.5 and e[7] > 0.5 and e[30] > 0.5 and e[22] < 0.5)
        if len(lands) < 3:
            continue
        off = any(t == 2 and any(0 <= r - 3 < len(names) and names[r - 3] in FLASH for r in refs[k])
                  for k, t in enumerate(ct))
        has_blue = any(any(w in n for w in BLUE_WORDS) for n in lands)
        key = "offered" if off else "not_offered"
        blue[f"{key}|blue_up={has_blue}"] += 1
        tal[f"{key}|{'+'.join(lands)}"] += 1
print("FLASH3|files=%d|" % len(sys.argv[1:]) + "|".join(f"{k}={v}" for k, v in sorted(blue.items())))
for k, v in tal.most_common(8):
    print(f"FLASH3|lands|{v}|{k}"[:200])
