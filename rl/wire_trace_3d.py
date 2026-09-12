#!/usr/bin/env python3
"""Per-consult trace of the knowledge tracker: turn, hand drift, slot count
vs the opponent's hand size, known slots, tracker events.
    python3 rl/wire_trace_3d.py FILE [max consults]"""
import json
import sys

n = 0
lim = int(sys.argv[2]) if len(sys.argv) > 2 else 40
for raw in open(sys.argv[1], "rb"):
    if not raw.startswith(b'{"t":"consult"') or n >= lim:
        continue
    m = json.loads(raw)
    if "v7_opp_hand" not in m:
        continue
    n += 1
    c = m["v7_ctr"]
    turn = round(m["v7_game"][0] * 30)
    hs = round(m["v7_players"][1][2] * 10)
    known = sum(1 for r in m["v7_opp_hand"] if r[5] == 1)
    origins = "".join("odro"[max(range(4), key=lambda i: r[i])] for r in m["v7_opp_hand"])
    print(f"t{turn:2d} drift={c.get('handDrift')} slots={len(m['v7_opp_hand'])} hand={hs} known={known} "
          f"origins={origins} events={c.get('trackerEvents')} acts={len(m['v7_opp_actions'])}")
