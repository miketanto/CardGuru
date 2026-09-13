#!/bin/bash
# Stop the 7l league run (parent run_7l.sh, its rung0_lane_league.sh lane, servers
# 7950/7951/7960, driver 7912). Never touches 7910/7940 (D-PPO). Own name cannot match.
[ -f ~/.profile ] && . ~/.profile
for pat in 'bash rl/run_7[l].sh' 'run_7[l].sh' 'rung0_lane_leagu[e].sh' 'rung0_lan[e].sh W0Base W0Twin 3072'; do
    for p in $(pgrep -f "$pat"); do kill -TERM $p 2>/dev/null && echo "killed $p ($pat)"; done
done
sleep 1
for port in 7950 7951 7960; do pkill -f "policy_serve[r].py --port $port" 2>/dev/null && echo "server $port stopped"; done
bash /home/user/CardGuru/rl/driver_server.sh stop 7912 > /dev/null 2>&1; echo "driver 7912 stopped"
pkill -f "driver_clien[t].py --port 7912" 2>/dev/null
sleep 2
echo "left: run_7l=$(pgrep -fc 'run_7[l].sh') league=$(pgrep -fc 'rung0_lane_leagu[e]') srv795x=$(pgrep -fc 'policy_serve[r].py --port 79[56]') drv7912=$(pgrep -fc 'RLDriverServe[r] --port 7912') dppo_lane=$(pgrep -fc 'rung0_lan[e].sh W0Base W0Twin 2048') dppo_srv=$(pgrep -fc 'policy_serve[r].py --port 7940')"
