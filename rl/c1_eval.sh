#!/bin/bash
# Phase 5 C1: eval a student checkpoint (argmax, no learning).
# Usage: bash rl/c1_eval.sh <ckpt> <port> <opponent: heuristic|search> \
#            <deck(s)> <games> <evalseed> <tag>
set -u
CKPT=$1; PORT=$2; OPP=$3; DECK=$4; GAMES=$5; ESEED=$6; TAG=$7
OUT=/tmp/rl_p5_c1
mkdir -p $OUT
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $CKPT --seed 0 --log $OUT/eval_${TAG}_server.csv \
    > $OUT/server_${TAG}.log 2>&1 &
SERVER=$!
up=0
SECONDS=0
while [ $SECONDS -lt 60 ]; do
    grep -q "policy server" $OUT/server_${TAG}.log 2>/dev/null && { up=1; break; }
    grep -q "Traceback" $OUT/server_${TAG}.log 2>/dev/null && { cat $OUT/server_${TAG}.log; exit 1; }
done
if [ "$up" = "0" ]; then
    echo "C1_EVAL_FAILED|tag=$TAG|server_never_started"
    cat $OUT/server_${TAG}.log 2>/dev/null
    kill $SERVER 2>/dev/null
    exit 1
fi
cd /home/user/mage
mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
    -DfailIfNoTests=false -Drl.episodes=$GAMES \
    -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.deck=$DECK -Drl.stopTurn=80 \
    -Drl.mode=eval -Drl.seed=$ESEED -Drl.report=0 \
    -Drl.out=$OUT/eval_${TAG}.txt > /dev/null 2>&1
line=$(tail -1 $OUT/eval_${TAG}.txt 2>/dev/null)
kill $SERVER 2>/dev/null
if [ -z "$line" ]; then
    echo "C1_EVAL_FAILED|tag=$TAG|no_summary_line"
    exit 1
fi
echo "C1|ckpt=$(basename $CKPT)|opp=$OPP|tag=$TAG|$line" | tee -a $OUT/c1_log.txt
