#!/bin/bash
# One Task D work chunk (Dimir Midrange control mirror vs HeuristicPlayer v2).
# Dimir games run ~8x slower than burn (0.36 games/sec random-policy), so
# chunks are smaller than Task B's: 64-episode train batches, and the
# 500-game confirmation is split into five 100-game seed slices that an
# aggregator combines.
# Modes:
#   train [N]  : N training episodes (default 64), advances trained.txt
#   eval       : 100-game argmax eval @seed 950000, appends TASKD curve line
#   confirm P  : 100-game confirmation slice P in 0..4 @seed 960000+P*100
# Usage: bash rl/chunk_d.sh <seed> <port> <train|eval|confirm> [arg]
set -u
SEED=$1; PORT=$2; MODE=$3; ARG=${4:-}
OUT=/tmp/rl_taskD_s${SEED}
DECK=BenchDimir.dck
STOP=80
mkdir -p $OUT
cd /home/user/mage
pkill -f "policy_server.py --port $PORT" 2>/dev/null
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $OUT/e0.pt --seed $SEED --log $OUT/train.csv \
    > $OUT/server.log 2>&1 &
SERVER=$!
until grep -q "policy server" $OUT/server.log 2>/dev/null; do true; done

trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
if [ "$MODE" = "train" ]; then
    N=${ARG:-64}
    # per-episode seeds = base + i, so offsetting the base by the running
    # trained count guarantees every training episode sees a fresh seed
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$N \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=$DECK -Drl.stopTurn=$STOP \
        -Drl.mode=train -Drl.seed=$((4000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    trained=$((trained + N))
    echo $trained > $OUT/trained.txt
    echo "TASKD|seed=$SEED|trained=$trained|train_chunk_done"
elif [ "$MODE" = "eval" ]; then
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=100 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=$DECK -Drl.stopTurn=$STOP \
        -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
        -Drl.out=$OUT/evals.txt > /dev/null 2>&1
    wr=$(tail -1 $OUT/evals.txt | grep -o 'win_rate=[0-9.]*' | cut -d= -f2)
    echo "TASKD|seed=$SEED|trained=$trained|eval_win_rate=$wr" | tee -a $OUT/curve.txt
else
    P=${ARG:-0}
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=100 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=$DECK -Drl.stopTurn=$STOP \
        -Drl.mode=eval -Drl.seed=$((960000 + P*100)) -Drl.report=0 \
        -Drl.out=$OUT/confirm_p${P}.txt > /dev/null 2>&1
    line=$(tail -1 $OUT/confirm_p${P}.txt)
    wins=$(echo "$line" | grep -o 'wins=[0-9]*' | cut -d= -f2)
    echo "TASKD|seed=$SEED|trained=$trained|confirm_part=$P|wins=$wins/100" | tee -a $OUT/curve.txt
fi
kill $SERVER 2>/dev/null
echo "CHUNK_DONE|seed=$SEED|mode=$MODE|arg=${ARG:-}"
