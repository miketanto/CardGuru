#!/bin/bash
# Stop the Phase 12 post-training evaluations by user decision (2026-09-15 ~12:40Z): the sampled
# battery after 4 of 6 snapshots, the queued two-stage battery, the after-training watcher and
# the queued CPU readouts. Results already written stay. This file's name matches none of the patterns.
set -u
k() { local pat=$1; local pids; pids=$(pgrep -f "$pat"); echo "$pat -> ${pids:-none}"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; }
k 'after_p1[2]\.sh'
k 'run_p12[st]\.sh'
k 'battery_p12[st]\.sh'
k 'battery_xdec[k]\.sh'
k 'p12_readou[t]\.py'
k 'driver_client\.py --port 791[34]'
k 'policy_serve[r]\.py --port 794[789]'
sleep 2
cd /home/user/CardGuru && for p in 7913 7914; do bash rl/driver_server.sh stop $p 2>&1 | tail -n 1; done
sleep 2
echo "left: servers=$(pgrep -fc 'policy_serve[r]') drivers=$(pgrep -fc 'RLDriverServe[r]') evals=$(pgrep -fc 'run_p12[st]|battery_p12[st]|after_p1[2]')"
