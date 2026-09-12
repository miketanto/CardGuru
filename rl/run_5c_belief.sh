#!/bin/bash
# 5c: belief gates B1-B4 (rl/v7_belief_real.py) over every 5b recording, cuda.
cd /home/user/CardGuru || exit 1
OUT=rl/artifacts/v7/5c_belief.txt
echo "# 5c belief gates $(date -u +%FT%TZ) steps=1500 batch=64 leak-per-file=40" > "$OUT"
python3 rl/v7_belief_real.py rl/artifacts/v7/wire3a/5b*.jsonl --steps 1500 --leak-per-file 40 \
  --out rl/artifacts/v7/5c_belief.json 2>&1 | grep '^BELIEF5C' >> "$OUT"
echo "# done $(date -u +%FT%TZ) rc=${PIPESTATUS[0]}" >> "$OUT"
