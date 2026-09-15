"""13a flash check, refined: OPPONENT-turn PRIORITY consults only (a LAND/SPELL/ACTIVATE candidate exists,
so getPlayable returned something). Flash card in my hand + untapped own lands (dimir_census indices).
Per case: flash offered? other spells offered without it? Examples of 'not offered while another spell was'."""
import collections
import json
import sys

FLASH = {"Floodpits Drowner", "Enduring Curiosity", "The Wondrous Wasp", "Nowhere to Run"}
c = collections.Counter()
ex = []
for p in sys.argv[1:]:
    for raw in open(p, "rb"):
        if b'"t":"consult"' not in raw:
            continue
        m = json.loads(raw)
        ct = m.get("v7_cand_type") or []
        if not (set(ct) & {1, 2, 3}):
            continue                       # priority consults only
        g = m.get("v7_game") or []
        if not (len(g) > 1 and g[1] < 0.5):
            continue                       # opponent's turn
        ents = m.get("v7_ent") or []
        names = m.get("v7_ent_name") or []
        refs = m.get("v7_cand_refers") or [[] for _ in ct]
        c["opp_prio"] += 1
        inhand = sorted({names[i] for i, e in enumerate(ents)
                         if i < len(names) and names[i] in FLASH and e[1] > 0.5 and e[7] > 0.5})
        if not inhand:
            continue
        unt = sum(1 for e in ents if e[0] > 0.5 and e[7] > 0.5 and e[30] > 0.5 and e[22] < 0.5)
        spell_names = set()
        for k, t in enumerate(ct):
            if t == 2:
                for r in refs[k]:
                    if 0 <= r - 3 < len(names):
                        spell_names.add(names[r - 3])
        flash_off = sorted(spell_names & FLASH)
        other = sorted(spell_names - FLASH)
        b = "unt>=3" if unt >= 3 else ("unt2" if unt == 2 else "unt<=1")
        c[f"inhand|{b}"] += 1
        c[f"inhand|{b}|flash_offered"] += bool(flash_off)
        c[f"inhand|{b}|other_spell_no_flash"] += bool(other) and not flash_off
        if unt >= 3 and other and not flash_off and len(ex) < 5:
            ex.append(f"turn={g[0] * 30:.0f}|unt={unt}|hand_flash={','.join(inhand)}|offered={','.join(other)}")
print("FLASH2|files=%d|" % len(sys.argv[1:]) + "|".join(f"{k}={v}" for k, v in sorted(c.items())))
for e in ex:
    print("FLASH2|example|" + e)
