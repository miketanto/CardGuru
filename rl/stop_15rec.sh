#!/bin/bash
# Stop the Phase 15 A4L ladder recording: the runner, any running recording job,
# its echo servers and the two driver JVMs. This file's name (stop_15rec.sh)
# matches none of the patterns below, so it cannot kill its own shell.
# Recordings already written are kept; run_15rec.sh is resumable (a job whose
# REC15| line is in the deck's counts.txt is skipped on the next launch).
#   bash rl/stop_15rec.sh
set -u
k() { local pat=$1; local pids; pids=$(pgrep -f "$pat"); echo "$pat -> ${pids:-none}"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; }
k 'run_15re[c]\.sh'
k 'record_1[5]\.sh'
k 'wire_echo_serve[r]\.py --port 778[45]'
k 'run_drive[r]\.sh'
sleep 3
cd /home/user/CardGuru && for p in 7911 7912; do bash rl/driver_server.sh stop $p 2>&1 | tail -n 1; done
sleep 2
echo "left: runners=$(pgrep -fc 'run_15re[c]\.sh') jobs=$(pgrep -fc 'record_1[5]\.sh') echo=$(pgrep -fc 'wire_echo_serve[r]\.py') drivers=$(pgrep -fc 'RLDriverServe[r]')"
