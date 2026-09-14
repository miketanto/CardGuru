#!/bin/bash
# Hard stop of Phase 12 (the graceful stop is: touch rl/artifacts/v7/12/STOP).
# This file's own name cannot match any pattern below.
pkill -f 'run_phase1[2].sh'
pkill -f 'phase1[2].py'
pkill -f 'rung0_lane_leagu[e].sh'
pkill -f 'battery_xdec[k].sh'
pkill -f 'record_censu[s].sh'
sleep 1
pkill -f 'policy_serve[r].py --port 79'
pkill -f 'record_prox[y].py'
for p in 7912 7913; do bash /home/user/CardGuru/rl/driver_server.sh stop $p > /dev/null 2>&1; done
sleep 2
pgrep -fa 'policy_serve[r]|RLDriverServe[r]|phase1[2]|rung0_lan[e]' | cut -c1-120
echo "kill_p12 done"
