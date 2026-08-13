#!/bin/bash
# Phase 8 zero-shot eval: one policy checkpoint vs a scripted ruler on a
# deck mirror. Argmax, no-yields, consult budget 4000, fixed seed.
# Usage: bash rl/p8_eval.sh <name> <arch: e0|attn> <ckpt> \
#            <opp: heuristic|search> <deck.dck> <games> <seed> <port>
set -u
NAME=$1; ARCH=$2; CKPT=$3; OPP=$4; DECK=$5; GAMES=$6; SEED=$7; PORT=$8
OUT=/tmp/rl_p8
FEATS=${P8_FEATS:-/home/user/CardGuru/rl/e2_features.tsv}
TAG="${NAME}_${OPP}_$(basename $DECK .dck)"
mkdir -p $OUT
[ -f "$CKPT" ] || { echo "P8_EVAL_FAILED|missing_ckpt|$CKPT"; exit 1; }

CDIM=38; FEATARG=""
if [ "$ARCH" != "e0" ]; then CDIM=91; FEATARG="-Drl.cardFeatures=$FEATS"; fi

# serve with bind-retry (elo_tournament.sh pattern)
up=0
for try in 1 2 3; do
    rm -f $OUT/server_${TAG}.log
    python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
        --ckpt "$CKPT" --seed 0 --arch $ARCH --cdim $CDIM \
        > $OUT/server_${TAG}.log 2>&1 &
    SRV=$!
    SECONDS=0
    while [ $SECONDS -lt 90 ]; do
        grep -q "policy server" $OUT/server_${TAG}.log 2>/dev/null && { up=1; break; }
        grep -q "Traceback" $OUT/server_${TAG}.log 2>/dev/null && break
        sleep 1
    done
    [ "$up" = "1" ] && break
    kill $SRV 2>/dev/null; wait $SRV 2>/dev/null
    grep -q "Address already in use" $OUT/server_${TAG}.log 2>/dev/null || break
    sleep 5
done
[ "$up" = "1" ] || { echo "P8_EVAL_FAILED|server|$TAG"; cat $OUT/server_${TAG}.log; exit 1; }

cd /home/user/mage
mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
    -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
    -DfailIfNoTests=false -Drl.episodes=$GAMES \
    -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT $FEATARG \
    -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.deck=$DECK -Drl.stopTurn=80 \
    -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 \
    -Drl.out=$OUT/eval_${TAG}.txt > /dev/null 2>&1
cd /home/user/CardGuru
kill $SRV 2>/dev/null; wait $SRV 2>/dev/null

line=$(tail -1 $OUT/eval_${TAG}.txt 2>/dev/null)
[ -z "$line" ] && { echo "P8_EVAL_FAILED|no_summary|$TAG"; exit 1; }
echo "P8EVAL|policy=$NAME|opp=$OPP|deck=$(basename $DECK .dck)|$line" \
    | tee -a $OUT/eval_log.txt
