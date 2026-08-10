#!/bin/bash
# Task A orchestrator: train E0 vs RANDOM opponent until eval win rate
# >70% (gate) or the episode budget is spent.
# Usage: bash rl/task_a.sh [SEED] [BUDGET_EPISODES]
set -u
SEED=${1:-0}
BUDGET=${2:-10000}
PORT=${3:-7801}
TAG=taskA_s${SEED}
OUT=/tmp/rl_${TAG}
mkdir -p $OUT
cd /home/user/mage

pkill -f "policy_server.py --port $PORT" 2>/dev/null
rm -f $OUT/e0.pt
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $OUT/e0.pt --seed $SEED --log $OUT/train.csv \
    > $OUT/server.log 2>&1 &
SERVER=$!
until grep -q "policy server" $OUT/server.log 2>/dev/null; do true; done

TRAIN_BATCH=512
EVAL_EPS=100
trained=0
batch=0
while [ $trained -lt $BUDGET ]; do
    batch=$((batch+1))
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$TRAIN_BATCH \
        -Drl.opponent=random -Drl.policy=socket -Drl.port=$PORT \
        -Drl.mode=train -Drl.seed=$((1000000 + SEED*100000 + batch*1000)) \
        -Drl.report=0 -Drl.out=$OUT/train_batches.txt \
        > /dev/null 2>&1
    trained=$((trained + TRAIN_BATCH))
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$EVAL_EPS \
        -Drl.opponent=random -Drl.policy=socket -Drl.port=$PORT \
        -Drl.mode=eval -Drl.seed=900000 -Drl.report=0 \
        -Drl.out=$OUT/evals.txt \
        > /dev/null 2>&1
    wr=$(tail -1 $OUT/evals.txt | grep -o 'win_rate=[0-9.]*' | cut -d= -f2)
    echo "TASKA|seed=$SEED|trained=$trained|eval_win_rate=$wr" | tee -a $OUT/curve.txt
    pass=$(python3 -c "print(1 if float('$wr' or 0) >= 0.70 else 0)")
    if [ "$pass" = "1" ]; then
        echo "TASKA|seed=$SEED|GATE_PASSED|episodes=$trained" | tee -a $OUT/curve.txt
        break
    fi
done
kill $SERVER 2>/dev/null
echo "TASKA|done|trained=$trained"
