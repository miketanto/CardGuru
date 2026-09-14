#!/bin/bash
# Phase 11 Part B chain: B1 census recordings (log rl/artifacts/v7/11/b1.log), then the B2
# drill-down (log rl/artifacts/v7/11/drill/league11.log) only if B1 printed B1|done.
# Launch: setsid nohup bash rl/chain11.sh > /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/11/chain11.log 2>&1 < /dev/null &
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
mkdir -p $LB/rl/artifacts/v7/11/drill
echo "CHAIN11|start|$(date -u +%FT%TZ)"
bash /home/user/CardGuru/rl/run_b1_census.sh >> $LB/rl/artifacts/v7/11/b1.log 2>&1
tail -1 $LB/rl/artifacts/v7/11/b1.log | grep -q '^B1|done' || { echo "CHAIN11|b1 did not finish"; exit 1; }
echo "CHAIN11|b2|$(date -u +%FT%TZ)"
bash /home/user/CardGuru/rl/run_drill11.sh >> $LB/rl/artifacts/v7/11/drill/league11.log 2>&1
echo "CHAIN11|end|$(date -u +%FT%TZ)"
