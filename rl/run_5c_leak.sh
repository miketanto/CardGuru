#!/bin/bash
# 5c: the oracle leak gate (rl/v7_leak_real.py, probes/leak.py levels 1-3) over
# EVERY 5b recording, all consults per recording (--limit 2000 > the largest file).
# Output: rl/artifacts/v7/5c_leak.txt, one line per recording.
cd /home/user/CardGuru || exit 1
OUT=rl/artifacts/v7/5c_leak.txt
[ -f "$OUT" ] || echo "# 5c oracle leak gate $(date -u +%FT%TZ) layers=2 limit=2000 (every consult of every 5b recording)" > "$OUT"
echo "# (re)start $(date -u +%FT%TZ)" >> "$OUT"
for f in rl/artifacts/v7/wire3a/5b*.jsonl; do
  b=$(basename "$f" .jsonl)
  grep -q "^$b " "$OUT" && continue        # resumable: skip recordings already gated
  r=$(python3 rl/v7_leak_real.py "$f" --limit 2000 2>&1 | grep '^LEAK3D' | tr '\n' ' ')
  echo "$b $r" >> "$OUT"
done
echo "# done $(date -u +%FT%TZ)" >> "$OUT"
