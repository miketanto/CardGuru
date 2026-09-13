#!/bin/bash
# Waits for the C1 seed-1 lane to finish (R0_DONE|W0Base|s1 in its WSL-local
# lane.log, or the lane process gone), then runs rl/post_7c1_seed.sh 1. Detached
# so the post-processing happens even if the interactive session is gone; the
# watcher on the Windows side tails this script's log for WAIT7C1|.
# Its own name (wait_7c1_s1) cannot match the pgrep pattern below.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
LOG=/tmp/rl_7c1_s1/lane.log
echo "WAIT7C1|start=$(date -u +%FT%TZ)"
while true; do
    if grep -q 'R0_DONE|W0Base|s1' $LOG 2>/dev/null; then echo "WAIT7C1|done_line"; break; fi
    if grep -q 'R0_FAILED' $LOG 2>/dev/null; then echo "WAIT7C1|FAILED_line"; break; fi
    if [ "$(pgrep -fc 'rung0_lan[e]')" = "0" ]; then echo "WAIT7C1|lane_gone"; break; fi
    sleep 60
done
grep 'R0_DONE\|R0_FAILED\|R0|' $LOG | tail -3 | cut -c1-200
sleep 5
bash /home/user/CardGuru/rl/post_7c1_seed.sh 1
echo "WAIT7C1|end=$(date -u +%FT%TZ)|lane=$(pgrep -fc 'rung0_lan[e]')|server7941=$(pgrep -fc 'policy_serve[r].py --port 7941')"
