#!/bin/bash
# "I am alive" heartbeat for the 1024->2048 run.
#
# The container recycles on SESSION inactivity, not process activity, so a
# 65-minute training block with no output on the lane log looks idle from
# outside and the box gets reclaimed mid-run. This emits one line every 10
# minutes carrying the two numbers that say whether the run is healthy -
# episodes in the checkpoint and policy-server RSS - and exits on its own
# when the lane finishes or dies.
#
# RSS is here because the entattn server has OOM-killed once before (ep 383
# of 512, 11.2 GB, fixed by the per-window backward in _update_recurrent).
# Peak after the fix was 538 MB; anything climbing past ~2 GB is a
# regression, not noise.
set -u
CKPT=/tmp/rl_dimir_v6/agent.pt
while true; do
    sleep 600
    if ! pgrep -f "run_dimir_2k.s[h]" > /dev/null; then
        echo "ALIVE|lane process gone - run finished or died, heartbeat exiting"
        exit 0
    fi
    eps=$(python3 -c "
import torch
try: print(int(torch.load('$CKPT',map_location='cpu',weights_only=False).get('episodes',0)))
except Exception: print('?')" 2>/dev/null || echo '?')
    rss=$(ps -o rss= -C python3 2>/dev/null | sort -rn | head -1)
    echo "ALIVE|$(date +%H:%M)|trained=$eps/2048|srv_rss=$(( ${rss:-0} / 1024 ))MB"
done
