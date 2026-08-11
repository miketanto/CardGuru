#!/bin/bash
# One C2a lane: train an arm/seed to BUDGET episodes in 64-ep chunks,
# rolling 100g pool eval vs D1 every 256 episodes. Fails fast on any
# chunk guard.
# Usage: bash rl/c2_lane.sh <arm> <seed> <port> [budget=1280]
set -u
ARM=$1; SEED=$2; PORT=$3; BUDGET=${4:-1280}
POOL="BenchBurn.dck,BenchControl.dck,BenchMidrange.dck,BenchDimir.dck"
OUT=/tmp/rl_c2_${ARM}_s${SEED}
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    if [ "$trained" -ge "$BUDGET" ]; then
        break
    fi
    bash /home/user/CardGuru/rl/chunk_c2.sh $ARM $SEED $PORT train 64 || exit 1
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    if [ $((trained % 256)) -eq 0 ]; then
        bash /home/user/CardGuru/rl/chunk_c2.sh $ARM $SEED $PORT eval \
            "$POOL" 100 950000 roll_${trained} || exit 1
    fi
done
echo "LANE_DONE|arm=$ARM|seed=$SEED|trained=$(cat $OUT/trained.txt)"
