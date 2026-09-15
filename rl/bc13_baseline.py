#!/usr/bin/env python3
"""Phase 13b: trivial-predictor baselines for the BC top-1, per decision kind (kinds as rl/v7_bc.py).
    python3 rl/bc13_baseline.py REC.jsonl [...]
Per kind over labelled consults: fraction with label == index 0; fraction with label == the kind's most
common label position; fraction with label == the LAST index; mean k. A BC top-1 close to one of these is a
positional rule, not imitation."""
import collections
import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from v7_bc import kind_of  # noqa: E402

pos = collections.defaultdict(collections.Counter)
n = collections.Counter()
z = collections.Counter()
last = collections.Counter()
ks = collections.Counter()
for p in sys.argv[1:]:
    for raw in open(p, "rb"):
        if b'"t":"consult"' not in raw or b'"y":' not in raw:
            continue
        m = json.loads(raw)
        ct = m.get("v7_cand_type") or []
        y = int(m["y"])
        if y < 0 or y >= len(ct):
            continue
        k = kind_of(ct)
        n[k] += 1
        ks[k] += len(ct)
        z[k] += y == 0
        last[k] += y == len(ct) - 1
        pos[k][y] += 1
for k in ("prio", "target", "attack", "block", "trivial"):
    if not n[k]:
        continue
    mp, mc = pos[k].most_common(1)[0]
    print(f"BASE|kind={k}|n={n[k]}|mean_k={ks[k] / n[k]:.2f}|y0={z[k] / n[k]:.3f}|ylast={last[k] / n[k]:.3f}"
          f"|modal_pos={mp}:{mc / n[k]:.3f}")
