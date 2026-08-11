#!/bin/bash
# Task C few-shot recovery: fine-tune a COPY of a trained arm checkpoint
# on HoldoutControl for 128 episodes, then 100-game argmax eval.
# Usage: bash rl/chunk_ft.sh <e0|e2> <seed> <port> <train|eval>
set -u
ARM=$1; SEED=$2; PORT=$3; MODE=$4
SRC=/tmp/rl_taskC_${ARM}_s${SEED}
OUT=/tmp/rl_taskC_ft_${ARM}_s${SEED}
FEATS=/home/user/CardGuru/rl/e2_features.tsv
mkdir -p $OUT
[ -f $OUT/net.pt ] || cp $SRC/net.pt $OUT/net.pt
if [ "$ARM" = "e2" ]; then CDIM=91; JFEAT="-Drl.cardFeatures=$FEATS"; else CDIM=38; JFEAT=""; fi
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
[ "$up" = "1" ] || { echo "CHUNK_FAILED|server_never_started"; kill $SERVER 2>/dev/null; exit 1; }
cd /home/user/mage
if [ "$MODE" = "train" ]; then
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=128 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=HoldoutControl.dck -Drl.stopTurn=80 $JFEAT \
        -Drl.mode=train -Drl.seed=$((8000000 + SEED*100000)) \
        -Drl.report=0 > /dev/null 2>&1
    echo "FT|arm=$ARM|seed=$SEED|train128_done"
else
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=100 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=HoldoutControl.dck -Drl.stopTurn=80 $JFEAT \
        -Drl.mode=eval -Drl.seed=970000 -Drl.report=0 \
        -Drl.out=$OUT/eval.txt > /dev/null 2>&1
    line=$(tail -1 $OUT/eval.txt)
    wr=$(echo "$line" | grep -o 'win_rate=[0-9.]*' | head -1 | cut -d= -f2)
    st=$(echo "$line" | grep -o 'stalls=[0-9]*' | cut -d= -f2)
    echo "FT|arm=$ARM|seed=$SEED|ft128_eval|win_rate=$wr|stalls=$st" | tee -a $OUT/curve.txt
fi
kill $SERVER 2>/dev/null
echo "CHUNK_DONE|ft|$ARM|$SEED|$MODE"
