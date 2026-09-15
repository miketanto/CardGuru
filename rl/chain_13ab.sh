#!/bin/bash
# Phase 13: 13a -> 13b chain. Waits for the recording runner's RUN13A|done line, writes the per-kind
# summary (rl/rec13_summary.py), clones only the kinds that pass the pre-registered 13a gate
# (labelled fraction >= 0.9; rec13_summary prints gate=pass|FAIL), stops the recording drivers
# 7911/7912 (memory: the box holds one model-holding job beside nothing else here), then runs
# rl/run_13b.sh with KINDS set. Kills nothing by pattern.
#   launch: setsid nohup bash rl/chain_13ab.sh > rl/artifacts/v7/13/chain_13ab.log 2>&1 < /dev/null &
[ -f ~/.profile ] && . ~/.profile
set -u
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
R=$LB/rl/artifacts/v7/13/rec
echo "C13|wait|$(date -u +%FT%TZ)"
until grep -q 'RUN13A|done' $R/run_13a.log 2>/dev/null; do sleep 60; done
echo "C13|recording_done|$(date -u +%FT%TZ)|$(grep 'RUN13A|done' $R/run_13a.log | tail -1)"
cd /home/user/CardGuru
python3 $RL/rec13_summary.py $R/rec13_*.jsonl > $R/summary.txt 2>&1
cat $R/summary.txt | sed 's/^/C13|/'
KINDS=$(grep -o 'kind=[a-z]*|.*gate=pass' $R/summary.txt | grep -o '^kind=[a-z]*' | cut -d= -f2 | grep -v 'trivial\|other' | paste -sd,)
[ -n "$KINDS" ] || { echo "C13|no kind passed the gate - 13b not run"; exit 1; }
echo "C13|kinds=$KINDS"
for p in 7911 7912; do bash $RL/driver_server.sh stop $p > /dev/null 2>&1; done
sleep 3
echo "C13|drivers_left=$(pgrep -fc 'RLDriverServe[r]')"
mkdir -p $LB/rl/artifacts/v7/13/bc
KINDS=$KINDS bash $RL/run_13b.sh > $LB/rl/artifacts/v7/13/bc/run_13b.log 2>&1
echo "C13|13b_rc=$?|$(date -u +%FT%TZ)"
