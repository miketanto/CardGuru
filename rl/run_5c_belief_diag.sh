#!/bin/bash
# 5c diagnostic (NOT a gate; the B3 bar stays 0.3): the same belief probe with 4x the
# training steps and a second seed, to see whether the held-out margin is training-limited.
cd /home/user/CardGuru || exit 1
OUT=rl/artifacts/v7/5c_belief_diag.txt
echo "# 5c belief DIAGNOSTIC $(date -u +%FT%TZ) steps=6000 seed=1 batch=64 leak-per-file=5" > "$OUT"
python3 rl/v7_belief_real.py rl/artifacts/v7/wire3a/5b*.jsonl --steps 6000 --seed 1 --leak-per-file 5 \
  --out rl/artifacts/v7/5c_belief_diag.json 2>&1 | grep '^BELIEF5C' >> "$OUT"
echo "# done $(date -u +%FT%TZ) rc=${PIPESTATUS[0]}" >> "$OUT"
