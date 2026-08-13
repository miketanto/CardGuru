#!/bin/bash
# Phase 10: keep PFSP's self-Elo estimate fresh BETWEEN ratings, using
# the champion gate's head-to-head as a free measurement.
#
# The problem it fixes, measured on this run's first 2048 episodes:
# the lane rates the agent (and so updates self_elo.txt) only every
# $P7_RATE episodes. At the flagship's 2048 reporting cadence that left
# PFSP aiming at Elo 299 while the agent was actually ~860-970, and
# 59% of chunks went to opponents it beat 95-100% of the time. The
# fastest-improvement phase is exactly when a stale target hurts most.
#
# The fix costs nothing, because the gate is ALREADY playing 50 games
# against an opponent of known rating every $P7_SNAP episodes:
#
#     implied self Elo = champion Elo - 400*log10(1/score - 1)
#
# 50 games is ~+-100 Elo, which is far better than a target that is
# 600 Elo stale. This only feeds OPPONENT SELECTION - the reported Elo
# curve still comes from the lane's own sequential 300-game fit, and a
# real rating always wins over a gate estimate at the same episode.
#
# Runs alongside the lane, so no edit to a lane that is mid-flight.
#
# Usage: bash rl/p10_selfelo_daemon.sh [outdir] [poll_seconds]
set -u
OUT=${1:-/tmp/rl_p10_flagship_s0}
POLL=${2:-30}
SEEN=""
while true; do
    [ -f "$OUT/gate_log.txt" ] || { sleep $POLL; continue; }
    # last gate, and the last episode count that got a REAL rating
    LAST=$(grep "^P10GATE|" $OUT/gate_log.txt 2>/dev/null | tail -1)
    if [ -n "$LAST" ] && [ "$LAST" != "$SEEN" ]; then
        GT=$(echo "$LAST" | sed 's/.*|trained=\([0-9]*\)|.*/\1/')
        SC=$(echo "$LAST" | sed 's/.*|score=\([0-9.]*\)|.*/\1/')
        RT=$(grep -o "trained=[0-9]*" $OUT/elo_curve.txt 2>/dev/null \
             | tail -1 | cut -d= -f2)
        CE=$(cut -d'|' -f4 $OUT/champion.tsv 2>/dev/null)
        if [ -n "$GT" ] && [ -n "$SC" ] && [ -n "${CE:-}" ] \
           && [ "$GT" -gt "${RT:-0}" ]; then
            EST=$(python3 -c "
import math
s=min(max($SC,0.05),0.95)
d=max(-300,min(300,-400*math.log10(1/s-1)))
print(int($CE+d))")
            echo "$EST" > $OUT/self_elo.txt
            echo "P10SELFELO|trained=$GT|gate_score=$SC|champion_elo=$CE|self_elo:=$EST"
        fi
        SEEN=$LAST
    fi
    sleep $POLL
done
