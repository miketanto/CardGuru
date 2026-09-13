#!/bin/bash
# Stop the D-PPO runner's PARENT only (rl/run_7d3.sh) so the seed that is training
# (rung0_lane.sh on driver 7910 / server 7940) runs to its end untouched and seed 1
# does not auto-start. Post-processing of the finished seed is then done by hand:
# rl/post_lane_seed.sh /tmp/rl_7d3_s0 <art>/7d3/s0 "0 512 1024 1536 2048".
# Own name (stop_7d3_parent) cannot match the pattern below.
set -u
pids=$(pgrep -f 'bash rl/run_7d[3]\.sh')
echo "run_7d3.sh pids: ${pids:-none}"
for p in $pids; do kill -TERM "$p" && echo "killed $p"; done
sleep 1
echo "remaining run_7d3: $(pgrep -fc 'run_7d[3]\.sh')  lane: $(pgrep -fc 'rung0_lan[e].sh W0Base W0Twin 2048')  server7940: $(pgrep -fc 'policy_serve[r].py --port 7940')  driver7910: $(pgrep -fc 'RLDriverServe[r] --port 7910')"
