#!/bin/bash
# Phase 13: 13b -> 13c chain. Waits for rl/run_13b.sh's B13|done line, waits until no policy server and no
# driver JVM is resident (the box rule: the training lane plus at most one other model-holding process; 13b's
# batteries must be gone), starts a fresh 18 h session-independent WSL keepalive through Windows interop, then
# launches the 13c controller rl/phase13.py (P13_START = rl/artifacts/v7/13/bc/bc.pt) detached.
# Kills nothing.
#   launch: setsid nohup bash rl/chain_13bc.sh > rl/artifacts/v7/13/chain_13bc.log 2>&1 < /dev/null &
[ -f ~/.profile ] && . ~/.profile
set -u
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
B=$LB/rl/artifacts/v7/13/bc/run_13b.log
C=$LB/rl/artifacts/v7/13/c
echo "C13C|wait|$(date -u +%FT%TZ)"
until grep -q '^B13|done' $B 2>/dev/null; do sleep 60; done
echo "C13C|13b_done|$(date -u +%FT%TZ)"
t=0
until [ "$(pgrep -fc 'policy_serve[r].py|RLDriverServe[r]')" = 0 ]; do
    sleep 30; t=$((t + 30))
    [ $t -ge 1800 ] && { echo "C13C|resident processes after 30 min - 13c NOT launched: $(pgrep -fa 'policy_serve[r].py|RLDriverServe[r]' | cut -c1-80 | paste -sd';')"; exit 1; }
done
[ -s $LB/rl/artifacts/v7/13/bc/bc.pt ] || { echo "C13C|no bc.pt - 13c NOT launched"; exit 1; }
cmd.exe /c start /min wsl -e bash -lc "sleep 64800" > /dev/null 2>&1
echo "C13C|keepalive_started|$(date -u +%FT%TZ)"
mkdir -p $C
cd /home/user/CardGuru
setsid nohup python3 $RL/phase13.py > $C/phase13.log 2>&1 < /dev/null &
echo "C13C|launched|pid=$!|$(date -u +%FT%TZ)|log=$C/phase13.log"
