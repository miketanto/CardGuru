#!/bin/bash
# Phase 10: copy the flagship lane's reportable state into rl/artifacts
# so every checkpoint is committed, not just described.
#
# Deliberately does NOT copy the whole snapshot pool every time (each
# lstmattn ckpt is ~1.7MB and the lane makes one every 512 episodes) -
# only the champion, the current net, and the curves/transcripts. Pass
# --pool to include the snapshot pool at the end of the run.
#
# Usage: bash rl/p10_sync_artifacts.sh [--pool] [srcdir]
set -u
POOL=0
[ "${1:-}" = "--pool" ] && { POOL=1; shift; }
SRC=${1:-/tmp/rl_p10_flagship_s0}
DST=/home/user/CardGuru/rl/artifacts/tmp/$(basename $SRC)
mkdir -p $DST
for f in elo_curve.txt elo_matches.tsv matrix.txt gate_log.txt \
         pool_elo.tsv champion.tsv self_elo.txt trained.txt train.csv \
         p7_final.pt net.pt; do
    [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DST/$f"
done
cp $SRC/transcript_*.txt $DST/ 2>/dev/null
cp $SRC/gate_*.txt $DST/ 2>/dev/null
if [ "$POOL" = "1" ] && [ -d "$SRC/pool" ]; then
    mkdir -p $DST/pool && cp $SRC/pool/*.pt $DST/pool/ 2>/dev/null
fi
echo "P10SYNC|from=$SRC|to=$DST|files=$(ls $DST | wc -l)"
