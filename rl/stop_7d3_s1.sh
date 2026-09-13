#!/bin/bash
# Stop a D-PPO seed-1 lane and its processes (run_7d3.sh parent, rung0_lane.sh ... 2048 1,
# policy server 7941, driver 7910). Own name cannot match the patterns.
[ -f ~/.profile ] && . ~/.profile
for pat in 'bash rl/run_7d[3].sh' 'rung0_lan[e].sh W0Base W0Twin 2048 1'; do
    for p in $(pgrep -f "$pat"); do kill -TERM $p 2>/dev/null && echo "killed $p ($pat)"; done
done
sleep 1
pkill -f 'policy_serve[r].py --port 7941' 2>/dev/null && echo "server 7941 stopped"
pkill -f 'driver_clien[t].py --port 7910' 2>/dev/null
bash /home/user/CardGuru/rl/driver_server.sh stop 7910 > /dev/null 2>&1; echo "driver 7910 stopped"
sleep 2
echo "left: $(pgrep -fa 'run_7d3|rung0_lane|policy_server|RLDriverServer' | cut -c1-40 | tr '\n' ';')"
