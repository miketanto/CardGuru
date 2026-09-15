#!/bin/bash
# Stop the Phase 12 sampled-play diagnostic side job (server 7949, driver 7914) because the
# box is swapping (2026-09-15 03:23Z: 336 MB available, 2.5 GB swap, training updates 20 -> 36 s).
# The training lane (server 7950 + its JVM) and the CPU readout are NOT touched. Resumable later.
set -u
k() { local pat=$1; local pids; pids=$(pgrep -f "$pat"); echo "$pat -> ${pids:-none}"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; }
k 'run_p12[s]\.sh'
k 'battery_p12[s]\.sh'
k 'driver_client\.py --port 791[4]'
k 'policy_serve[r]\.py --port 794[9]'
sleep 2
cd /home/user/CardGuru && bash rl/driver_server.sh stop 7914 2>&1 | tail -n 1
sleep 3
echo "servers: $(pgrep -fa 'policy_serve[r]' | grep -o 'port [0-9]*' | tr '\n' ' ') drivers=$(pgrep -fc 'RLDriverServe[r]')"
free -m | sed -n 2p
