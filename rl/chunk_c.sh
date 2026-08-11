#!/bin/bash
# One Task C work chunk. Two arms, identical except candidate features:
#   e0: 16-bucket name hash (cdim 38)   e2: graph features (cdim 91)
# Training pool: 4 mirror decks interleaved per episode. Fixed budget
# per TASKC-SPEC.md; evals are argmax on a named deck.
# Usage: bash rl/chunk_c.sh <e0|e2> <seed> <port> train [N]
#        bash rl/chunk_c.sh <e0|e2> <seed> <port> eval <deck.dck> <games> <evalseed> <tag>
set -u
ARM=$1; SEED=$2; PORT=$3; MODE=$4
OUT=/tmp/rl_taskC_${ARM}_s${SEED}
POOL="BenchBurn.dck,BenchControl.dck,BenchMidrange.dck,BenchDimir.dck"
FEATS=/home/user/CardGuru/rl/e2_features.tsv
mkdir -p $OUT
if [ "$ARM" = "e2" ]; then
    CDIM=91
    JFEAT="-Drl.cardFeatures=$FEATS"
    ARMOFF=3000000
else
    CDIM=38
    JFEAT=""
    ARMOFF=0
fi
pkill -f "policy_server.py --port $PORT" 2>/dev/null
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $OUT/net.pt --seed $SEED --log $OUT/train.csv --cdim $CDIM \
    > $OUT/server.log 2>&1 &
SERVER=$!
up=0
for i in $(seq 1 3000); do
    grep -q "policy server" $OUT/server.log 2>/dev/null && { up=1; break; }
    grep -q "Traceback" $OUT/server.log 2>/dev/null && { cat $OUT/server.log; exit 1; }
done
if [ "$up" = "0" ]; then
    echo "CHUNK_FAILED|arm=$ARM|seed=$SEED|server_never_started"
    cat $OUT/server.log 2>/dev/null
    kill $SERVER 2>/dev/null
    exit 1
fi
cd /home/user/mage

trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
if [ "$MODE" = "train" ]; then
    N=${5:-64}
    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$N \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=$POOL -Drl.stopTurn=80 $JFEAT \
        -Drl.mode=train -Drl.seed=$((6000000 + ARMOFF + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "CHUNK_FAILED|arm=$ARM|seed=$SEED|no_training_rows (trained stays $trained)"
        kill $SERVER 2>/dev/null
        exit 1
    fi
    trained=$((trained + N))
    echo $trained > $OUT/trained.txt
    echo "TASKC|arm=$ARM|seed=$SEED|trained=$trained|train_chunk_done"
else
    DECK=$5; GAMES=$6; ESEED=$7; TAG=$8
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$GAMES \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=$DECK -Drl.stopTurn=80 $JFEAT \
        -Drl.mode=eval -Drl.seed=$ESEED -Drl.report=0 \
        -Drl.out=$OUT/eval_${TAG}.txt > /dev/null 2>&1
    line=$(tail -1 $OUT/eval_${TAG}.txt)
    wr=$(echo "$line" | grep -o 'win_rate=[0-9.]*' | head -1 | cut -d= -f2)
    stalls=$(echo "$line" | grep -o 'stalls=[0-9]*' | cut -d= -f2)
    echo "TASKC|arm=$ARM|seed=$SEED|trained=$trained|eval=$TAG|deck=$DECK|win_rate=$wr|stalls=$stalls" \
        | tee -a $OUT/curve.txt
fi
kill $SERVER 2>/dev/null
echo "CHUNK_DONE|arm=$ARM|seed=$SEED|mode=$MODE"
