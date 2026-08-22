#!/bin/bash
# B1Narrow vs B1Fast at matched budget - CURRICULUM-LADDER.md §5's
# timing pair. See rl/B1-TIMING-AB.md for the pre-registration.
#
#   nohup bash rl/b1_timing_ab.sh > /tmp/b1_ab.log 2>&1 &
#
# SEQUENTIAL, not parallel, and that is not a throughput oversight:
# rung0_lane.sh opens with `pkill -f "[R]LDriverServer"`, which matches
# by process name and not by port, so a second lane starting up kills
# the driver JVM the first one is mid-job on. Two lanes need two
# containers or a lane change; two hours of wall-clock does not.
#
# Same seed in both arms => p10_init_net.py emits byte-identical initial
# weights, so ck_0 is the same net playing two decks. That is the
# control the pre-registration leans on.
set -u
RL=/home/user/CardGuru/rl
BUDGET=${B1_BUDGET:-1024}
SEED=${B1_SEED:-0}

run_arm() {   # $1 deck  $2 port  $3 out
    echo "=== ARM $1 === $(date -u +%H:%M:%S)"
    R0_ENCODER_V=6 R0_EVAL_G=100 R0_EVERY=512 R0_CP7_G=0 R0_CONC=2 \
    R0_OUT=$3 R0_PORT=$2 \
        timeout 21600 bash $RL/rung0_lane.sh "$1" "$1" "$BUDGET" "$SEED"
    echo "=== ARM $1 exit=$? === $(date -u +%H:%M:%S)"
}

run_arm B1Fast   7971 /tmp/rl_b1fast
run_arm B1Narrow 7972 /tmp/rl_b1narrow
echo "B1_AB_DONE $(date -u +%H:%M:%S)"
