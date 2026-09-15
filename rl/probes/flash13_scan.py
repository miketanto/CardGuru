"""13a check (coordinator): are instant-speed flash casts offered to the CP7 teacher seat?
Over recordings: consults on the OPPONENT's turn (g[1] < 0.5). Entities: zone battlefield e[0], hand e[1],
mine e[7], tapped e[22], land e[30] (dimir_census.py indices). Flash cards = dimir_census.FLASH.
Counts: opp-turn consults; with a flash card in my hand; by untapped own lands; and whether a SPELL
candidate referring to the flash card was offered. Also every flash card offered as a SPELL candidate
by turn owner, and every flash cast (label) by turn owner."""
import collections
import json
import sys

FLASH = {"Floodpits Drowner", "Enduring Curiosity", "The Wondrous Wasp", "Nowhere to Run"}
c = collections.Counter()
unt_hist = collections.Counter()
for p in sys.argv[1:]:
    for raw in open(p, "rb"):
        if b'"t":"consult"' not in raw:
            continue
        m = json.loads(raw)
        g = m.get("v7_game") or []
        ents = m.get("v7_ent") or []
        names = m.get("v7_ent_name") or []
        ct = m.get("v7_cand_type") or []
        refs = m.get("v7_cand_refers") or [[] for _ in ct]
        y = m.get("y")
        opp_turn = len(g) > 1 and g[1] < 0.5
        flash_rows = [i for i, e in enumerate(ents)
                      if i < len(names) and names[i] in FLASH and e[1] > 0.5 and e[7] > 0.5]
        offered = []
        for k, t in enumerate(ct):
            if t == 2:
                for r in refs[k]:
                    if 0 <= r - 3 < len(names) and names[r - 3] in FLASH:
                        offered.append(k)
        side = "opp" if opp_turn else "own"
        c[f"consults_{side}"] += 1
        if offered:
            c[f"flash_offered_{side}"] += 1
            if y is not None and int(y) in offered:
                c[f"flash_cast_{side}"] += 1
        if not opp_turn:
            continue
        unt = sum(1 for e in ents if e[0] > 0.5 and e[7] > 0.5 and e[30] > 0.5 and e[22] < 0.5)
        unt_hist[min(unt, 6)] += 1
        if flash_rows:
            c["opp_flash_in_hand"] += 1
            if unt >= 2:
                c["opp_flash_in_hand_unt2"] += 1
                if offered:
                    c["opp_flash_in_hand_unt2_offered"] += 1
            if unt >= 3:
                c["opp_flash_in_hand_unt3"] += 1
                if offered:
                    c["opp_flash_in_hand_unt3_offered"] += 1
print("FLASHSCAN|files=%d|" % len(sys.argv[1:]) + "|".join(f"{k}={v}" for k, v in sorted(c.items())))
print("FLASHSCAN|opp_turn_untapped_own_lands_hist=" + ",".join(f"{k}:{unt_hist[k]}" for k in sorted(unt_hist)))
