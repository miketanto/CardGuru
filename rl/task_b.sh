#!/bin/bash
# Task B: train E0 vs HeuristicPlayer (burn mirror) - THE measurement.
# Competence = eval win rate >=0.55 over 500 games (checked as a rolling
# gate at 100-game evals; the final 500-game confirmation runs once the
# rolling gate passes). Resumable: RESUME=1 keeps checkpoint and curve.
# Usage: [RESUME=1] bash rl/task_b.sh <SEED> <BUDGET_EPISODES> <PORT>
set -u
SEED=${1:-0}
BUDGET=${2:-60000}
PORT=${3:-7810}
TAG=taskB_s${SEED}
OUT=/tmp/rl_${TAG}
mkdir -p $OUT
cd /home/user/mage

pkill -f "policy_server.py --port $PORT" 2>/dev/null
if [ "${RESUME:-0}" != "1" ]; then rm -f $OUT/e0.pt $OUT/curve.txt $OUT/evals.txt $OUT/train.csv; fi
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $OUT/e0.pt --seed $SEED --log $OUT/train.csv \
    > $OUT/server.log 2>&1 &
SERVER=$!
until grep -q "policy server" $OUT/server.log 2>/dev/null; do true; done

TRAIN_BATCH=256
EVAL_EPS=100
batch=$(grep -c 'TASKB|seed' $OUT/curve.txt 2>/dev/null || echo 0)
trained=$((batch * TRAIN_BATCH))
while [ $trained -lt $BUDGET ]; do
    batch=$((batch+1))
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$TRAIN_BATCH \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.mode=train -Drl.seed=$((2000000 + SEED*1000000 + batch*1000)) \
        -Drl.report=0 > /dev/null 2>&1
    trained=$((trained + TRAIN_BATCH))
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$EVAL_EPS \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
        -Drl.out=$OUT/evals.txt > /dev/null 2>&1
    wr=$(tail -1 $OUT/evals.txt | grep -o 'win_rate=[0-9.]*' | cut -d= -f2)
    echo "TASKB|seed=$SEED|trained=$trained|eval_win_rate=$wr" | tee -a $OUT/curve.txt
    pass=$(python3 -c "print(1 if float('$wr' or 0) >= 0.55 else 0)")
    if [ "$pass" = "1" ]; then
        # confirmation: 500 eval games, disjoint eval seed block
        mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
            -DfailIfNoTests=false -Drl.episodes=500 \
            -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
            -Drl.mode=eval -Drl.seed=960000 -Drl.report=0 \
            -Drl.out=$OUT/confirm.txt > /dev/null 2>&1
        cwr=$(tail -1 $OUT/confirm.txt | grep -o 'win_rate=[0-9.]*' | cut -d= -f2)
        echo "TASKB|seed=$SEED|CONFIRM_500|win_rate=$cwr|episodes=$trained" | tee -a $OUT/curve.txt
        confirmed=$(python3 -c "
import math
w=float('$cwr'); n=500
lo=w-1.96*math.sqrt(w*(1-w)/n)
print(1 if (w>=0.55 and lo>0.50) else 0)")
        if [ "$confirmed" = "1" ]; then
            echo "TASKB|seed=$SEED|GATE_PASSED|episodes=$trained|confirm_wr=$cwr" | tee -a $OUT/curve.txt
            break
        fi
    fi
done
kill $SERVER 2>/dev/null
echo "TASKB|done|seed=$SEED|trained=$trained"
