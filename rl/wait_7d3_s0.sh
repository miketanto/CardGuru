#!/bin/bash
# Waits for the D-PPO seed-0 lane to finish (R0_DONE|W0Base|s0 in its WSL-local
# lane.log, or the lane gone), then post-processes it (rl/post_lane_seed.sh) and
# recovers any NA battery row (rl/fill_na_batteries.sh, server 7949 / driver 7915).
# The run_7d3.sh parent was stopped by rl/stop_7d3_parent.sh, so nobody else does.
# Own name (wait_7d3_s0) cannot match the pgrep pattern below.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
LOG=/tmp/rl_7d3_s0/lane.log
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7d3
echo "WAIT7D3|start=$(date -u +%FT%TZ)"
while true; do
    if grep -q 'R0_DONE|W0Base|s0' $LOG 2>/dev/null; then echo "WAIT7D3|done_line"; break; fi
    if grep -q 'R0_FAILED' $LOG 2>/dev/null; then echo "WAIT7D3|FAILED_line"; break; fi
    if [ "$(pgrep -fc 'rung0_lan[e].sh W0Base W0Twin 2048')" = "0" ]; then echo "WAIT7D3|lane_gone"; break; fi
    sleep 60
done
grep 'R0_DONE\|R0_FAILED\|R0|' $LOG | tail -6 | cut -c1-200
sleep 5
bash rl/post_lane_seed.sh /tmp/rl_7d3_s0 $ART/s0 "0 512 1024 1536 2048"
if grep -q 'D0=NA' $LOG; then
    echo "WAIT7D3|na_rows=$(grep -c 'D0=NA' $LOG)|recovering"
    bash rl/fill_na_batteries.sh /tmp/rl_7d3_s0 $ART/s0_rebat 7949 7915
fi
echo "WAIT7D3|end=$(date -u +%FT%TZ)|lane=$(pgrep -fc 'rung0_lan[e].sh W0Base W0Twin 2048')|server7940=$(pgrep -fc 'policy_serve[r].py --port 7940')"
