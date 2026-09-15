#!/bin/bash
# Stop the Phase 13a recording (rl/run_13a.sh, its record_13a.sh jobs and echo servers 7784/7785)
# and restart nothing. This file's own name matches none of its patterns.
pkill -f 'run_13[a].sh' 2>/dev/null
pkill -f 'record_13[a].sh' 2>/dev/null
pkill -f 'wire_echo_serve[r].py --port 778[45]' 2>/dev/null
pkill -f 'run_drive[r].sh' 2>/dev/null
sleep 2
echo "STOP13A|left_runner=$(pgrep -fc 'run_13[a].sh|record_13[a].sh')|left_echo=$(pgrep -fc 'wire_echo_serve[r]')"
