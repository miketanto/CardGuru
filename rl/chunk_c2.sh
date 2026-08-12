#!/bin/bash
# Phase 5 C2a work chunk. Arms:
#   shape   : BC-init (student_full.pt) + PPO + potential shaping (--shape 1)
#   noshape : BC-init + PPO terminal-only (attribution control)
#   scratch : fresh net + PPO + shaping (did BC-init matter?)
# Usage: bash rl/chunk_c2.sh <arm> <seed> <port> train [N]
#        bash rl/chunk_c2.sh <arm> <seed> <port> eval <deck(s)> <games> <evalseed> <tag>
set -u
ARM=$1; SEED=$2; PORT=$3; MODE=$4
# v3 instrument line (flash/ninjutsu): fresh output namespace + v3 BC
# init. v2 runs live in /tmp/rl_c2_<arm>_s<seed> (partials recorded in
# PHASE5-V3.md).
OUT=/tmp/rl_c2v3_${ARM}_s${SEED}
POOL="BenchBurn.dck,BenchControl.dck,BenchMidrange.dck,BenchDimir.dck"
BC=/tmp/rl_p5_c1/student_v3.pt
mkdir -p $OUT
if [ ! -f $OUT/net.pt ] && [ "$ARM" != "scratch" ]; then
    cp $BC $OUT/net.pt
fi
case $ARM in
    shape)   SHAPE=1.0; JPHI="-Drl.phi=true"; ARMOFF=0 ;;
    noshape) SHAPE=0.0; JPHI="";              ARMOFF=3000000 ;;
    scratch) SHAPE=1.0; JPHI="-Drl.phi=true"; ARMOFF=6000000 ;;
    *) echo "bad arm"; exit 1 ;;
esac
python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
    --ckpt $OUT/net.pt --seed $SEED --log $OUT/train.csv \
    --shape $SHAPE > $OUT/server.log 2>&1 &
SERVER=$!
up=0
SECONDS=0
while [ $SECONDS -lt 60 ]; do
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
        -Drl.opponent=search -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.policy=socket -Drl.port=$PORT $JPHI \
        -Drl.deck=$POOL -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((21000000 + ARMOFF + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "CHUNK_FAILED|arm=$ARM|seed=$SEED|no_training_rows (trained stays $trained)"
        kill $SERVER 2>/dev/null
        exit 1
    fi
    trained=$((trained + N))
    echo $trained > $OUT/trained.txt
    echo "C2|arm=$ARM|seed=$SEED|trained=$trained|train_chunk_done"
else
    DECK=$5; GAMES=$6; ESEED=$7; TAG=$8
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=$GAMES \
        -Drl.opponent=search -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=$DECK -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$ESEED -Drl.report=0 \
        -Drl.out=$OUT/eval_${TAG}.txt > /dev/null 2>&1
    line=$(tail -1 $OUT/eval_${TAG}.txt 2>/dev/null)
    wr=$(echo "$line" | grep -o 'win_rate=[0-9.]*' | head -1 | cut -d= -f2)
    stalls=$(echo "$line" | grep -o 'stalls=[0-9]*' | cut -d= -f2)
    echo "C2|arm=$ARM|seed=$SEED|trained=$trained|eval=$TAG|deck=$DECK|win_rate=$wr|stalls=$stalls" \
        | tee -a $OUT/curve.txt
fi
kill $SERVER 2>/dev/null
echo "CHUNK_DONE|arm=$ARM|seed=$SEED|mode=$MODE"
