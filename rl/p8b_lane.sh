#!/bin/bash
# Phase 8b: deck-randomized self-play fine-tune lane.
#
# Same league skeleton as league_lane_p7.sh, two changes:
#  1. every training episode plays a DIFFERENT deck: the driver rotates
#     -Drl.deck over the 24-deck P8BTrain pool (mirror per episode), so
#     deck-structure memorization stops paying and the card channel is
#     the only stable signal;
#  2. probes every 256 eps: 100g D0 + D1 on BenchDimir (anchor
#     comparability) + 100g D0 on P8Faeries (the held-out transfer
#     probe this phase is about).
#
# Two arms, identical regimen (lr 1e-4, no desperation, self-play vs
# own snapshot pool): arch=attn (treatment, E2 features) and arch=e0
# (control, name-hash — CANNOT benefit from deck diversity by design).
#
# Usage: bash rl/p8b_lane.sh <arch: attn|e0> <seed> <agentPort> \
#            <oppPort> <initCkpt> [budget=4096]
set -u
ARCH=$1; SEED=$2; APORT=$3; OPORT=$4; INIT=$5; BUDGET=${6:-4096}
LRVAL=${P8B_LR:-1e-4}
OUT=/tmp/rl_p8b_${ARCH}_s${SEED}
FEATS=/home/user/CardGuru/rl/e2_features.tsv
CDIM=91; FEATARG="-Drl.cardFeatures=$FEATS"
[ "$ARCH" = "e0" ] && { CDIM=38; FEATARG=""; }
DECKS=$(cat /home/user/CardGuru/rl/p8b_pool/pool_list.txt)
# P8B_META_LIST (optional): comma list of meta decks. When set, odd
# chunks train vs D0 (heuristic pilots the opposing mirror seat) on
# these decks; even chunks stay self-play on the variant pool.
META=${P8B_META_LIST:-}
mkdir -p $OUT/pool
[ -f $OUT/net.pt ] || cp "$INIT" $OUT/net.pt

start_server() {  # $1 ckpt $2 port $3 logfile [$4 extra flags]
    local try
    for try in 1 2 3; do
        rm -f $3
        python3 /home/user/CardGuru/rl/policy_server.py --port $2 \
            --ckpt "$1" --seed $SEED --cdim $CDIM --arch $ARCH \
            ${4:-} > $3 2>&1 &
        echo $! > $OUT/.srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" $3 2>/dev/null && { up=1; break; }
            grep -q "Traceback" $3 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat $OUT/.srvpid) 2>/dev/null
        wait $(cat $OUT/.srvpid) 2>/dev/null
        grep -q "Address already in use" $3 2>/dev/null || { sleep 5; break; }
        sleep 5
    done
    echo "P8B_FAILED|$ARCH|server_never_started|$3"
    cat $3
    exit 1
}

stop_server() { kill $1 2>/dev/null; wait $1 2>/dev/null; }

probe() {  # $1 tag $2 opp $3 deck $4 games -> win_rate on stdout
    start_server $OUT/net.pt $APORT $OUT/aserver.log
    local ASRV=$(cat $OUT/.srvpid)
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=$4 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT $FEATARG \
        -Drl.opponent=$2 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$3 -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
        -Drl.out=$OUT/probe_$1.txt > /dev/null 2>&1
    stop_server $ASRV
    grep -o 'win_rate=[0-9.]*' $OUT/probe_$1.txt | head -1 | cut -d= -f2
}

rate_checkpoint() {  # $1 trained
    local t=$1
    local d0=$(probe d0_$t heuristic BenchDimir.dck 100)
    local d1=$(probe d1_$t search BenchDimir.dck 100)
    local tf=$(probe faer_$t heuristic P8Faeries.dck 100)
    echo "P8BPROBE|arch=$ARCH|trained=$t|bench_d0=$d0|bench_d1=$d1|faeries_d0=$tf" \
        | tee -a $OUT/curve.txt
}

cd /home/user/mage
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break

    if [ $((trained % 256)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
        grep -q "|trained=${trained}|" $OUT/curve.txt 2>/dev/null || \
            rate_checkpoint $trained
    fi
    CHUNK=$((trained / 64))
    mapfile -t POOLCKS < <(ls $OUT/pool/*.pt 2>/dev/null | sort -V)
    OPPCK=${POOLCKS[$((CHUNK % ${#POOLCKS[@]}))]}

    CHUNKDECKS=$DECKS
    OPPARGS="-Drl.opponent=rl -Drl.oppPort=$OPORT"
    OSRV=""
    if [ -n "$META" ] && [ $((CHUNK % 2)) -eq 1 ]; then
        CHUNKDECKS=$META
        OPPARGS="-Drl.opponent=heuristic"
        OPPCK="D0-meta"
    fi

    start_server $OUT/net.pt $APORT $OUT/aserver.log \
        "--lr $LRVAL --log $OUT/train.csv"
    ASRV=$(cat $OUT/.srvpid)
    if [ "$OPPCK" != "D0-meta" ]; then
        start_server "$OPPCK" $OPORT $OUT/oserver.log
        OSRV=$(cat $OUT/.srvpid)
    fi
    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    mvn -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=64 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT $FEATARG \
        $OPPARGS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$CHUNKDECKS -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((90000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > $OUT/last_chunk.log 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    [ -n "$OSRV" ] && stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        fails=$((${CHUNK_FAILS:-0} + 1))
        CHUNK_FAILS=$fails
        echo "P8B_RETRY|$ARCH|no_training_rows at trained=$trained (attempt $fails)"
        tail -5 $OUT/last_chunk.log
        if [ "$fails" -ge 3 ]; then
            echo "P8B_FAILED|$ARCH|no_training_rows x3 (trained stays $trained)"
            exit 1
        fi
        sleep 10
        continue
    fi
    CHUNK_FAILS=0
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt
    echo "P8B|$ARCH|trained=$trained|opp=$(basename $OPPCK)"
done
rate_checkpoint $(cat $OUT/trained.txt)
cp $OUT/net.pt $OUT/p8b_final.pt
echo "P8B_DONE|$ARCH|trained=$(cat $OUT/trained.txt)"
