#!/bin/bash
# Stop the Phase 11 drill-down immediately (user decision 2026-09-14 ~22:15Z): the controller,
# its lane, the lane's policy servers (learner 7950, opponent 7960) and its driver JVM (7912).
# Every learner's state is saved after each finished block, so only the running exploiter
# block is lost. This file's name (stop_drill11) matches none of the patterns below.
set -u
k() { local pat=$1; local pids; pids=$(pgrep -f "$pat"); echo "$pat -> ${pids:-none}"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; }
k 'run_drill1[1]\.sh'
k 'chain1[1]\.sh'
k 'league1[1]\.py'
k 'rung0_lane_leagu[e]\.sh'
k 'record_censu[s]\.sh'
k 'driver_client\.py --port 791[23]'
k 'policy_serve[r]\.py --port 79(47|48|50|60)'
sleep 3
cd /home/user/CardGuru && for p in 7912 7913; do bash rl/driver_server.sh stop $p 2>&1 | tail -n 1; done
sleep 2
echo "left: servers=$(pgrep -fc 'policy_serve[r]') drivers=$(pgrep -fc 'RLDriverServe[r]') controller=$(pgrep -fc 'league1[1]\.py') lanes=$(pgrep -fc 'rung0_lan[e]')"
