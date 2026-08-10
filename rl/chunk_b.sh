#!/bin/bash
# One Task B work chunk (fits inside a tracked background window):
#   train  : one 256-episode train batch + one 100-game argmax eval
#   confirm: one 500-game argmax eval on the confirmation seed block
# Always resumes the checkpoint. Appends to curve.txt. Exits when done.
# Usage: bash rl/chunk_b.sh <seed> <port> <train|confirm> [train_eps]
set -u
SEED=$1; PORT=$2; MODE=$3; TRAIN_EPS=${4:-256}
OUT=/tmp/rl_taskB_s${SEED}
mkdir -p $OUT
cd /home/user/mage
pkill -f "policy_server.py --port $PORT" 2>/dev/null
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $OUT/e0.pt --seed $SEED --log $OUT/train.csv \
    > $OUT/server.log 2>&1 &
SERVER=$!
until grep -q "policy server" $OUT/server.log 2>/dev/null; do true; done

batch=$(grep -c 'TASKB|seed' $OUT/curve.txt 2>/dev/null || echo 0)
if [ "$MODE" = "train" ]; then
    batch=$((batch+1))
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$TRAIN_EPS \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.mode=train -Drl.seed=$((2000000 + SEED*1000000 + batch*1000)) \
        -Drl.report=0 > /dev/null 2>&1
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=100 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
        -Drl.out=$OUT/evals.txt > /dev/null 2>&1
    wr=$(tail -1 $OUT/evals.txt | grep -o 'win_rate=[0-9.]*' | cut -d= -f2)
    trained=$((batch * TRAIN_EPS))
    echo "TASKB|seed=$SEED|trained=$trained|eval_win_rate=$wr" | tee -a $OUT/curve.txt
else
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=500 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.mode=eval -Drl.seed=960000 -Drl.report=0 \
        -Drl.out=$OUT/confirm.txt > /dev/null 2>&1
    cwr=$(tail -1 $OUT/confirm.txt | grep -o 'win_rate=[0-9.]*' | cut -d= -f2)
    trained=$((batch * TRAIN_EPS))
    verdict=$(python3 -c "
import math
w=float('$cwr'); n=500
lo=w-1.96*math.sqrt(w*(1-w)/n)
print('GATE_PASSED' if (w>=0.55 and lo>0.50) else 'CONFIRM_FAILED')")
    echo "TASKB|seed=$SEED|CONFIRM_500|win_rate=$cwr|episodes=$trained|$verdict" | tee -a $OUT/curve.txt
fi
kill $SERVER 2>/dev/null
echo "CHUNK_DONE|seed=$SEED|mode=$MODE"
