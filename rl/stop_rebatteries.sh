#!/bin/bash
# Stop ONLY the two side re-battery jobs (C1 paired re-battery: server 7947 / driver 7913;
# L0 2560 recovery: server 7948 / driver 7914) to relieve WSL memory (11 GB box, 0 free
# with four policy servers + three JVMs resident, 2026-09-13 06:10 WSL). The lanes on
# 7910/7940 (D-PPO) and 7912/7950 (L0/L1) are NOT touched. Both jobs are resumable
# (battery_ck.sh / rebattery_c1.sh skip finished rows) - rerun them when a lane ends.
# This file's own name (stop_rebatteries) matches none of the patterns below.
set -u
k() { local pat=$1; local pids; pids=$(pgrep -f "$pat"); echo "$pat -> ${pids:-none}"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; }
k 'bash rl/rebattery_c[1]\.sh'
k 'bash rl/battery_c[k]\.sh'
k 'bash rl/fill_na_batterie[s]\.sh'
k 'driver_client\.py --port 791[34]'
k 'policy_server\.py --port 794[78]'
sleep 2
cd /home/user/CardGuru && for p in 7913 7914; do bash rl/driver_server.sh stop $p 2>&1 | tail -n 1; done
sleep 3
echo "servers left: $(pgrep -fa 'policy_serve[r]' | grep -o 'port [0-9]*' | tr '\n' ' ')"
echo "drivers left: $(pgrep -fc 'RLDriverServe[r]')  lanes: $(pgrep -fc 'rung0_lan[e]')"
free -g | sed -n '2p'
