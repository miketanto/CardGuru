#!/bin/bash
# Phase 5 M3 novelty sweep: one (arm, poolSize, seed) config end-to-end.
# Task C regime replicated: scratch terminal-PPO vs D0 (heuristic),
# fixed 640-episode budget regardless of pool size (exposure per deck
# IS the variable), then zero-shot holdout evals (freeze rate primary).
# Usage: bash rl/m3_lane.sh <e0|e2> <2|4|8|16|32> <seed> <port>
set -u
ARM=$1; PSIZE=$2; SEED=$3; PORT=$4
BUDGET=640
OUT=/tmp/rl_m3_${ARM}_p${PSIZE}_s${SEED}
FEATS=/home/user/CardGuru/rl/e2_features.tsv
mkdir -p $OUT

# nested pools: P2 c P4 c P8 c P16 c P32 (bench 4 = core; M3 decks in
# fixed alphabetical order beyond that)
BENCH="BenchBurn.dck,BenchDimir.dck"
P4="$BENCH,BenchControl.dck,BenchMidrange.dck"
M3ALL=$(ls /home/user/CardGuru/rl/m3_decks/*.dck | sort | xargs -n1 basename | tr '\n' ',' | sed 's/,$//')
case $PSIZE in
    2)  POOL="$BENCH" ;;
    4)  POOL="$P4" ;;
    8)  POOL="$P4,$(echo $M3ALL | cut -d, -f1-4)" ;;
    16) POOL="$P4,$(echo $M3ALL | cut -d, -f1-12)" ;;
    32) POOL="$P4,$(echo $M3ALL | cut -d, -f1-28)" ;;
    *) echo "bad pool size"; exit 1 ;;
esac
if [ "$ARM" = "e2" ]; then
    CDIM=91; JFEAT="-Drl.cardFeatures=$FEATS"; ARMOFF=3000000
else
    CDIM=38; JFEAT=""; ARMOFF=0
fi

run_server() {
    python3 /home/user/CardGuru/rl/policy_server.py --port $PORT \
        --ckpt $OUT/net.pt --seed $SEED --log $OUT/train.csv --cdim $CDIM \
        > $OUT/server.log 2>&1 &
    SERVER=$!
    local up=0; SECONDS=0
    while [ $SECONDS -lt 60 ]; do
        grep -q "policy server" $OUT/server.log 2>/dev/null && { up=1; break; }
        grep -q "Traceback" $OUT/server.log 2>/dev/null && break
    done
    [ "$up" = "1" ] || { echo "M3_FAILED|$OUT|server_never_started"; cat $OUT/server.log; exit 1; }
}

cd /home/user/mage
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break
    run_server
    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=64 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck="$POOL" -Drl.stopTurn=80 $JFEAT \
        -Drl.mode=train -Drl.seed=$((30000000 + ARMOFF + SEED*1000000 + PSIZE*100000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    kill $SERVER 2>/dev/null
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "M3_FAILED|$OUT|no_training_rows (trained stays $trained)"
        exit 1
    fi
    echo $((trained + 64)) > $OUT/trained.txt
done

for HD in HoldoutBurn HoldoutControl HoldoutMidrange; do
    run_server
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false -Drl.episodes=200 \
        -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=$PORT \
        -Drl.deck=$HD.dck -Drl.stopTurn=80 $JFEAT \
        -Drl.mode=eval -Drl.seed=970000 -Drl.report=0 \
        -Drl.out=$OUT/eval_${HD}.txt > /dev/null 2>&1
    kill $SERVER 2>/dev/null
    line=$(tail -1 $OUT/eval_${HD}.txt 2>/dev/null)
    [ -z "$line" ] && { echo "M3_FAILED|$OUT|no_eval_${HD}"; exit 1; }
    wr=$(echo "$line" | grep -o 'win_rate=[0-9.]*' | head -1 | cut -d= -f2)
    stalls=$(echo "$line" | grep -o 'stalls=[0-9]*' | cut -d= -f2)
    echo "M3|arm=$ARM|pool=$PSIZE|seed=$SEED|holdout=$HD|win_rate=$wr|stalls=$stalls" \
        | tee -a /tmp/rl_m3_results.txt
done
echo "M3_CONFIG_DONE|arm=$ARM|pool=$PSIZE|seed=$SEED"
