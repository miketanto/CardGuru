#!/bin/bash
# Phase 5 C6: self-play league for the upgraded nets. Same clean league
# as C5 (no shaping, no yields, snapshot-pool opponents, D0/D1 as
# probes only) but: E2 graph candidate features (cdim 91) and a bigger
# net (--arch attn | lstmattn), BC-initialized from an E2 BC student.
# Usage: bash rl/league_lane_c6.sh <arch> <seed> <agentPort> <oppPort> \
#            <initCkpt> [budget=1024]
set -u
ARCH=$1; SEED=$2; APORT=$3; OPORT=$4; INIT=$5; BUDGET=${6:-1024}
OUT=/tmp/rl_c6_${ARCH}_s${SEED}
DECK=BenchDimir.dck
FEATS=/home/user/CardGuru/rl/e2_features.tsv
CDIM=91
mkdir -p $OUT/pool
if [ ! -f $OUT/net.pt ]; then
    cp "$INIT" $OUT/net.pt
fi

start_server() {  # $1 ckpt path, $2 port, $3 logfile -> pid in $OUT/.srvpid
    local try
    for try in 1 2 3; do
        rm -f $3
        python3 /home/user/CardGuru/rl/policy_server.py --port $2 \
            --ckpt "$1" --seed $SEED --log $OUT/train.csv \
            --cdim $CDIM --arch $ARCH > $3 2>&1 &
        echo $! > $OUT/.srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" $3 2>/dev/null && { up=1; break; }
            grep -q "Traceback" $3 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat $OUT/.srvpid) 2>/dev/null
        wait $(cat $OUT/.srvpid) 2>/dev/null
        grep -q "Address already in use" $3 2>/dev/null || break
    done
    echo "C6_FAILED|$ARCH s$SEED|server_never_started|$3"
    cat $3
    exit 1
}

stop_server() {
    kill $1 2>/dev/null
    wait $1 2>/dev/null
}

cd /home/user/mage
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break

    if [ $((trained % 256)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
    fi
    mapfile -t POOLCKS < <(ls $OUT/pool/*.pt 2>/dev/null | sort -V)
    NPOOL=${#POOLCKS[@]}
    OPPCK=${POOLCKS[$(( (trained / 64) % NPOOL ))]}

    start_server $OUT/net.pt $APORT $OUT/aserver.log
    ASRV=$(cat $OUT/.srvpid)
    start_server "$OPPCK" $OPORT $OUT/oserver.log
    OSRV=$(cat $OUT/.srvpid)
    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=64 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=rl -Drl.oppPort=$OPORT \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((60000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "C6_FAILED|$ARCH s$SEED|no_training_rows (trained stays $trained)"
        exit 1
    fi
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt

    if [ $((trained % 256)) -eq 0 ] || [ "$trained" -ge "$BUDGET" ]; then
        for PROBE in heuristic search; do
            start_server $OUT/net.pt $APORT $OUT/aserver.log
            ASRV=$(cat $OUT/.srvpid)
            mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
                -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
                -DfailIfNoTests=false -Drl.episodes=100 \
                -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
                -Drl.opponent=$PROBE -Drl.searchPlies=1 -Drl.searchBreadth=8 \
                -Drl.cardFeatures=$FEATS \
                -Drl.noYields=true -Drl.consultBudget=4000 \
                -Drl.deck=$DECK -Drl.stopTurn=80 \
                -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
                -Drl.out=$OUT/probe_${PROBE}_${trained}.txt > /dev/null 2>&1
            stop_server $ASRV
            line=$(tail -1 $OUT/probe_${PROBE}_${trained}.txt 2>/dev/null)
            wr=$(echo "$line" | grep -o 'win_rate=[0-9.]*' | head -1 | cut -d= -f2)
            stalls=$(echo "$line" | grep -o 'stalls=[0-9]*' | cut -d= -f2)
            echo "C6|arch=$ARCH|seed=$SEED|trained=$trained|probe=$PROBE|win_rate=$wr|stalls=$stalls" \
                | tee -a $OUT/curve.txt
        done
    fi
done
echo "C6_DONE|arch=$ARCH|seed=$SEED|trained=$(cat $OUT/trained.txt)"
