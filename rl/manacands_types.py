#!/usr/bin/env python3
"""Candidate-type census of a v7 recording: consults, K per consult, type counts."""
import collections
import json
import sys

c, n, ks = collections.Counter(), 0, []
for line in open(sys.argv[1]):
    m = json.loads(line)
    if m.get("t") == "consult":
        n += 1
        c.update(m["v7_cand_type"])
        ks.append(len(m["v7_cand_type"]))
print("consults", n, "meanK", round(sum(ks) / max(1, n), 2), "types", dict(sorted(c.items())))
