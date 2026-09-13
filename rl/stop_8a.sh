#!/bin/bash
# Stop the 8a lane by decision (PHASE8-DECKS STATE 2026-09-13 19:10): the run_8a.sh
# parent, the seed-0 lane, its driver client job, its policy server (7940) and its
# driver JVM (7910). Nothing else. Patterns carry a bracket so this script's own
# command line cannot match them.
pkill -f 'run_8[a].sh' 2>/dev/null
pkill -f 'rung0_lane.sh BenchDimi[r]' 2>/dev/null
pkill -f 'driver_clien[t].py --port 7910' 2>/dev/null
pkill -f 'policy_serve[r].py --port 7940' 2>/dev/null
bash /home/user/CardGuru/rl/driver_server.sh stop 7910 > /dev/null 2>&1
sleep 2
echo "STOP8A|left=$(pgrep -fa 'run_8[a]|rung0_lan[e]|policy_serve[r].py --port 7940|RLDriverServe[r]' | wc -l)|$(date -u +%FT%TZ)"
