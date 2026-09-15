#!/bin/bash
# Phase 13 Amendment 1 watcher: every 5 min run rl/p13_makebreak.py; when the 2,048 level has landed,
# record the verdict in rl/artifacts/v7/13/c/makebreak.txt and, on BREAK, run rl/stop_13c.sh.
RL=/home/user/CardGuru/rl
OUT=$RL/artifacts/v7/13/c/makebreak.txt
while true; do
    V=$(python3 $RL/p13_makebreak.py 2>&1)
    case "$V" in
        MB\|MAKE*)  echo "$(date -u +%FT%TZ) $V" >> $OUT; exit 0 ;;
        MB\|BREAK*) echo "$(date -u +%FT%TZ) $V" >> $OUT; bash $RL/stop_13c.sh >> $OUT 2>&1; exit 0 ;;
        MB\|PENDING*) : ;;
        *) echo "$(date -u +%FT%TZ) evaluator error: $V" >> $OUT ;;
    esac
    sleep 300
done
