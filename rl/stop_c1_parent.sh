#!/bin/bash
# Stop the C1 runner's PARENT script only (rl/run_7c1.sh), so the seed that is
# currently training (rung0_lane.sh + its policy server + driver 7910) runs to its
# end untouched and no further seed starts. The seed's post-processing (the tail of
# run_seed in run_7c1.sh) is then done by rl/post_7c1_seed.sh <seed>.
# Its own name (stop_c1_parent) cannot match the pattern below.
set -u
pids=$(pgrep -f 'bash rl/run_7c[1]\.sh')
echo "run_7c1.sh pids: ${pids:-none}"
for p in $pids; do kill -TERM "$p" && echo "killed $p"; done
sleep 1
echo "remaining run_7c1: $(pgrep -fc 'run_7c[1]\.sh')  lane: $(pgrep -fc 'rung0_lan[e]')  server: $(pgrep -fc 'policy_serve[r]')"
