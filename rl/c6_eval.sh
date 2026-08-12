#!/bin/bash
# C6 eval: arch-aware student eval (argmax). E2 encoding when arch != e0.
# Usage: bash rl/c6_eval.sh <ckpt> <arch> <port> <opponent> <deck(s)> \
#            <games> <evalseed> <tag>
set -u
CKPT=$1; ARCH=$2; PORT=$3; OPP=$4; DECK=$5; GAMES=$6; ESEED=$7; TAG=$8
OUT=/tmp/rl_c6_evals
FEATS=/home/user/CardGuru/rl/e2_features.tsv
mkdir -p $OUT
if [ "$ARCH" = "e0" ]; then CDIM=38; JFEAT=""; else CDIM=91; JFEAT="-Drl.cardFeatures=$FEATS"; fi
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $CKPT --seed 0 --arch $ARCH --cdim $CDIM \
    > $OUT/server_${TAG}.log 2>&1 &
SERVER=$!
up=0; SECONDS=0
while [ $SECONDS -lt 90 ]; do
    grep -q "policy server" $OUT/server_${TAG}.log 2>/dev/null && { up=1; break; }
    grep -q "Traceback" $OUT/server_${TAG}.log 2>/dev/null && { cat $OUT/server_${TAG}.log; exit 1; }
done
[ "$up" = "1" ] || { echo "C6_EVAL_FAILED|$TAG|server_never_started"; kill $SERVER 2>/dev/null; exit 1; }
cd /home/user/mage
mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
    -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
    -DfailIfNoTests=false -Drl.episodes=$GAMES \
    -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT $JFEAT \
    -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.deck=$DECK -Drl.stopTurn=80 \
    -Drl.mode=eval -Drl.seed=$ESEED -Drl.report=0 \
    -Drl.out=$OUT/eval_${TAG}.txt > /dev/null 2>&1
kill $SERVER 2>/dev/null; wait $SERVER 2>/dev/null
line=$(tail -1 $OUT/eval_${TAG}.txt 2>/dev/null)
[ -z "$line" ] && { echo "C6_EVAL_FAILED|$TAG|no_summary"; exit 1; }
echo "C6EVAL|ckpt=$(basename $CKPT)|arch=$ARCH|opp=$OPP|tag=$TAG|$line" | tee -a $OUT/log.txt
