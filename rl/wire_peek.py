#!/usr/bin/env python3
"""Print one entity row of one consult line from a wire recording, decoded
by the v6 row layout (StateEncoder §1): python3 rl/wire_peek.py FILE LINE ENT"""
import json
import sys

f, ln, ent = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
m = json.loads(open(f, "rb").read().split(b"\n")[ln - 1])
r = m["e"][ent]
names = {1: "mine", 2: "theirs", 3: "battlefield", 4: "hand", 5: "stack", 6: "grave", 7: "player",
         8: "pow", 9: "tou", 10: "dmg", 11: "tou_left", 12: "creature", 13: "land", 14: "other",
         15: "mv", 16: "tapped", 17: "sick", 18: "attacking", 19: "blocking", 20: "canAttack",
         21: "canBlock", 22: "enteredThisTurn", 23: "token"}
print(f"line {ln} ent {ent} turn={m['g'][0] * 30:.0f} active={m['g'][1]} step={m['g'][2:8]}")
print(" ".join(f"{names[i]}={r[i]:.2f}" for i in sorted(names) if r[i] != 0))
if "v7_ent_name" in m and ent >= 2:
    print("v7 name:", m["v7_ent_name"][ent - 2])
