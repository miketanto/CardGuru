#!/bin/bash
# Phase 9 recordings on BenchDimir vs the heuristic (8 games each), driver 7911 (v7 flags).
#   bash rl/probes/record_p9.sh driver   - start driver 7911 alone (v7 recording driver)
#   bash rl/probes/record_p9.sh cp7      - CP7 teacher seat (rl.agent=cp7) via the echo server -> rec_cp7_dimir.jsonl
#   bash rl/probes/record_p9.sh dim      - DIM (8ab ck_512) argmax via frozen server 7947 + record proxy 7948 -> rec_dim_dimir.jsonl
#   bash rl/probes/record_p9.sh stop     - stop the policy server on 7947 and driver 7911
[ -f ~/.profile ] && . ~/.profile
set -u
STAGE=${1:?stage}
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
OUT=$LB/rl/artifacts/v7/9
DPORT=7911; SPORT=7947; PPORT=7948; EPORT=7784
EP=${EP:-8}; SEED=${SEED:-9100}; DECK=BenchDimir
mkdir -p $OUT
DRV="-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7"
COMMON="-Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 -Drl.cardFeatures=$RL/e2_features.tsv
        -Drl.noYields=true -Drl.consultBudget=4000 -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true
        -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck -Drl.stopTurn=60 -Drl.mode=eval -Drl.report=0"

case $STAGE in
driver)
    bash $RL/driver_server.sh start $DPORT "$DRV" > $OUT/driver_start.log 2>&1
    echo "P9REC|driver|rc=$?|$(tail -1 $OUT/driver_start.log | cut -c1-100)"
    ;;
cp7)
    TAG=rec_cp7_dimir${TAGSFX:-}
    rm -f $OUT/$TAG.jsonl
    python3 $LB/rl/wire_echo_server.py --port $EPORT --out $OUT/$TAG.jsonl --max-conns 1 --pick 0 > $OUT/$TAG.echo.log 2>&1 &
    EPID=$!; sleep 1
    cp $RL/$DECK.dck /home/user/mage/Mage.Tests/; cd /home/user/mage
    RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=$DPORT timeout 1500 bash $RL/run_driver.sh \
        -Drl.episodes=$EP -Drl.agent=cp7 -Drl.policy=socket -Drl.port=$EPORT -Drl.aiSkill=6 $COMMON \
        -Drl.seed=$SEED -Drl.out=$OUT/$TAG.probe.txt > $OUT/$TAG.driver.log 2>&1
    RC=$?; kill $EPID 2>/dev/null; wait $EPID 2>/dev/null
    echo "P9REC|$TAG|rc=$RC|consults=$(grep -c '"t":"consult"' $OUT/$TAG.jsonl)|labelled=$(grep -c '"y":' $OUT/$TAG.jsonl)|ends=$(grep -c '"t":"end"' $OUT/$TAG.jsonl)|$(grep -o 'wins=[0-9]*\|losses=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $OUT/$TAG.probe.txt 2>/dev/null | paste -sd' ')"
    grep -h 'Exception\|refused\|RLJOB|error' $OUT/$TAG.driver.log | head -3
    ;;
dim)
    TAG=rec_dim_dimir${TAGSFX:-}
    CK=$LB/rl/artifacts/v7/8ab/s0/ck_512.pt
    rm -f $OUT/$TAG.jsonl
    pkill -f "policy_serve[r].py --port $SPORT" 2>/dev/null; sleep 2
    : > $OUT/dim_server.log
    cd /home/user/CardGuru
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $SPORT --ckpt "$CK" --seed 0 \
        --sdim 32 --cdim 94 --arch v7 --threads 1 --frozen --device cuda --logit-bound 5 --argmax-classes > $OUT/dim_server.log 2>&1 &
    t=0; until grep -q "policy server" $OUT/dim_server.log; do sleep 2; t=$((t+2)); [ $t -ge 180 ] && { echo "P9REC|server failed"; exit 1; }; done
    python3 $LB/rl/probes/record_proxy.py --port $PPORT --upstream $SPORT --out $OUT/$TAG.jsonl --max-conns 1 > $OUT/$TAG.proxy.log 2>&1 &
    PPID_=$!; sleep 1
    cp $RL/$DECK.dck /home/user/mage/Mage.Tests/; cd /home/user/mage
    RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=$DPORT timeout 1500 bash $RL/run_driver.sh \
        -Drl.episodes=$EP -Drl.agent=rl -Drl.policy=socket -Drl.port=$PPORT $COMMON \
        -Drl.seed=$SEED -Drl.out=$OUT/$TAG.probe.txt > $OUT/$TAG.driver.log 2>&1
    RC=$?; kill $PPID_ 2>/dev/null; wait $PPID_ 2>/dev/null
    echo "P9REC|$TAG|rc=$RC|consults=$(grep -c '"t":"consult"' $OUT/$TAG.jsonl)|acts=$(grep -c '^{"a":' $OUT/$TAG.jsonl)|ends=$(grep -c '"t":"end"' $OUT/$TAG.jsonl)|$(grep -o 'wins=[0-9]*\|losses=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $OUT/$TAG.probe.txt 2>/dev/null | paste -sd' ')"
    grep -h 'Exception\|refused\|RLJOB|error' $OUT/$TAG.driver.log | head -3
    ;;
stop)
    pkill -f "policy_serve[r].py --port $SPORT" 2>/dev/null
    bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
    sleep 2; echo "P9REC|stop|left=$(pgrep -fc 'policy_serve[r].py|RLDriverServe[r]')"
    ;;
esac
