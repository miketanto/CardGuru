"""13a flash check, per card: opponent-turn PRIORITY consults; per flash card in my hand with untapped own
lands >= its mana value (MV below) and a blue source untapped: offered as a SPELL candidate or not."""
import collections
import json
import sys

MV = {"Floodpits Drowner": 2, "Enduring Curiosity": 3, "The Wondrous Wasp": 4, "Nowhere to Run": 2}
BLUE_WORDS = ("Island", "Watery", "Underground", "Darkslick", "Drowned", "Undercity", "Choked", "Sunken",
              "Fetid", "Shipwreck", "Morphic", "Gloomlake", "Creeping", "Tidehollow", "Restless Reef")
c = collections.Counter()
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
        lands = [names[i] for i, e in enumerate(ents)
                 if i < len(names) and e[0] > 0.5 and e[7] > 0.5 and e[30] > 0.5 and e[22] < 0.5]
        blue = any(any(w in n for w in BLUE_WORDS) for n in lands)
        offered = {names[r - 3] for k, t in enumerate(ct) if t == 2 for r in refs[k] if 0 <= r - 3 < len(names)}
        inhand = {names[i] for i, e in enumerate(ents) if i < len(names) and names[i] in MV and e[1] > 0.5 and e[7] > 0.5}
        for nm in inhand:
            if len(lands) >= MV[nm] and (blue or nm == "Nowhere to Run"):
                c[f"{nm}|castable_state"] += 1
                c[f"{nm}|offered"] += nm in offered
print("FLASH4|files=%d|" % len(sys.argv[1:]) + "|".join(f"{k}={v}" for k, v in sorted(c.items())))
