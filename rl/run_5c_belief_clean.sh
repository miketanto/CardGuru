#!/bin/bash
# 5c check: the belief gate run again on the 48 round-1/round-2 recordings only (no 5bx_ extras:
# the three trackerDebug re-recordings of 5b_BenchDimir_p99 duplicate its games and can straddle
# the game-grouped hold-out).  Same seed/steps as the gate run.
cd /home/user/CardGuru || exit 1
OUT=rl/artifacts/v7/5c_belief_clean.txt
echo "# 5c belief gates, 48 non-duplicate recordings $(date -u +%FT%TZ) steps=1500 seed=0 leak-per-file=5" > "$OUT"
python3 rl/v7_belief_real.py rl/artifacts/v7/wire3a/5b_*.jsonl rl/artifacts/v7/wire3a/5b2_*.jsonl --steps 1500 --seed 0 --leak-per-file 5 \
  --out rl/artifacts/v7/5c_belief_clean.json 2>&1 | grep '^BELIEF5C' >> "$OUT"
echo "# done $(date -u +%FT%TZ) rc=${PIPESTATUS[0]}" >> "$OUT"
