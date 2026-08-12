#!/bin/bash
# Phase 7: lstm+attention self-play league with a MIXED opponent
# population and an Elo growth benchmark (user direction: "self play
# still uses lstm and attention... it needs the correct opponents and a
# way to benchmark growth").
#
# Differences from the C6 lane:
#  - main agent: lstmattn trained with TRUE BPTT (policy_server.py
#    Phase 7 recurrent update; the stored-hidden variant fed the
#    attention a noise token)
#  - opponents rotate over FOUR sources by chunk index (mod 4):
#      0 -> ck_0 BC anchor (frozen sequence-BC student; external
#           grounding, the C6-v2 fix)
#      2 -> external champion (attn_bc / attn_v2 / attn_desp rotation)
#           or an exploiter from $EXPDIR once any exist - the
#           AlphaStar ingredient: adversaries trained to beat US
#      1,3 -> own snapshot pool (classic self-play ladder)
#  - growth benchmark: every 256 eps the checkpoint plays 100g vs each
#    scripted anchor (D0/D1/D1h) and gets an Elo from the same
#    logistic-MLE fit as the Phase 6 leaderboard (D0=1000), appended
#    to $OUT/elo_curve.txt. D0/D1 win rates remain visible but the
#    RATING is the metric.
#
# Exploiters: drop attn/lstmattn ckpts into $EXPDIR named
# <name>__<arch>.pt (double underscore separates arch); the lane picks
# them up on the next external-opponent chunk.
#
# Usage: bash rl/league_lane_p7.sh <seed> <agentPort> <oppPort> \
#            <initCkpt> [budget=1024]
set -u
SEED=$1; APORT=$2; OPORT=$3; INIT=$4; BUDGET=${5:-1024}
ARCH=lstmattn
LRVAL=${P7_LR:-1e-4}
OUT=/tmp/rl_p7_${ARCH}_s${SEED}
EXPDIR=${P7_EXPDIR:-/tmp/rl_p7_exploiters}
DECK=BenchDimir.dck
FEATS=/home/user/CardGuru/rl/e2_features.tsv
CDIM=91
mkdir -p $OUT/pool $EXPDIR
[ -f $OUT/net.pt ] || cp "$INIT" $OUT/net.pt

# external champions: name|arch|ckpt (all cdim 91)
CHAMPS=(
  "attn_bc|attn|/tmp/rl_p5_c1/student_e2attn.pt"
  "attn_v2|attn|/tmp/rl_c6_attn_s0/attn_v2_final.pt"
  "attn_desp|attn|/tmp/rl_c6_attn_s7/attn_desp_final.pt"
)

start_server() {  # $1 ckpt $2 arch $3 port $4 logfile [$5 train-flags]
    local try
    for try in 1 2 3; do
        rm -f $4
        python3 /home/user/CardGuru/rl/policy_server.py --port $3 \
            --ckpt "$1" --seed $SEED --cdim $CDIM --arch $2 \
            ${5:-} > $4 2>&1 &
        echo $! > $OUT/.srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" $4 2>/dev/null && { up=1; break; }
            grep -q "Traceback" $4 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat $OUT/.srvpid) 2>/dev/null
        wait $(cat $OUT/.srvpid) 2>/dev/null
        grep -q "Address already in use" $4 2>/dev/null || break
    done
    echo "P7_FAILED|s$SEED|server_never_started|$4"
    cat $4
    exit 1
}

stop_server() {
    kill $1 2>/dev/null
    wait $1 2>/dev/null
}

pick_opponent() {  # -> echoes "ckpt|arch"
    local chunk=$1
    mapfile -t POOLCKS < <(ls $OUT/pool/*.pt 2>/dev/null | sort -V)
    case $((chunk % 4)) in
        0) # scratch mode (P7_NOANCHOR=1): no BC prior exists, so the
           # anchor slot becomes another self-play snapshot chunk
           if [ "${P7_NOANCHOR:-0}" = "1" ]; then
               echo "${POOLCKS[$((chunk % ${#POOLCKS[@]}))]}|$ARCH"
           else
               echo "$OUT/pool/ck_0.pt|$ARCH"
           fi ;;
        2)
            # externals: champions + any exploiters, rotated
            local EXT=()
            for C in "${CHAMPS[@]}"; do
                IFS='|' read -r _ CA CC <<< "$C"
                [ -f "$CC" ] && EXT+=("$CC|$CA")
            done
            local E BASE EA
            for E in $EXPDIR/*.pt; do
                [ -f "$E" ] || continue
                BASE=$(basename "$E" .pt)
                EA=${BASE##*__}
                [ "$EA" = "$BASE" ] && EA=$ARCH
                EXT+=("$E|$EA")
            done
            if [ ${#EXT[@]} -eq 0 ]; then
                echo "$OUT/pool/ck_0.pt|$ARCH"
            else
                echo "${EXT[$(( (chunk / 4) % ${#EXT[@]} ))]}"
            fi ;;
        *) echo "${POOLCKS[$((chunk % ${#POOLCKS[@]}))]}|$ARCH" ;;
    esac
}

rate_checkpoint() {  # $1 trained -> P7ELO| line
    local trained=$1 AK SK SN wr w d line
    touch $OUT/elo_matches.tsv
    for SK in "heuristic|D0" "search|D1" "searchhold|D1h"; do
        IFS='|' read -r AK SN <<< "$SK"
        # resume-safe: a restarted lane must not double-append a pairing
        grep -q "^p7_${trained}	${SN}	" $OUT/elo_matches.tsv && continue
        start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
        local ASRV=$(cat $OUT/.srvpid)
        mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
            -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
            -DfailIfNoTests=false -Drl.episodes=100 \
            -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
            -Drl.opponent=$AK -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS \
            -Drl.noYields=true -Drl.consultBudget=4000 \
            -Drl.deck=$DECK -Drl.stopTurn=80 \
            -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
            -Drl.out=$OUT/probe_${SN}_${trained}.txt > /dev/null 2>&1
        stop_server $ASRV
        line=$(tail -1 $OUT/probe_${SN}_${trained}.txt 2>/dev/null)
        [ -z "$line" ] && { echo "P7_FAILED|probe_${SN}_${trained} empty"; exit 1; }
        w=$(echo "$line" | grep -o 'wins=[0-9]*' | cut -d= -f2)
        d=$(echo "$line" | grep -o 'draws=[0-9]*' | cut -d= -f2)
        echo -e "p7_${trained}\t${SN}\t${w}\t${d}\t100" >> $OUT/elo_matches.tsv
    done
    local ELO=$(python3 /home/user/CardGuru/rl/elo_fit.py \
        --matches $OUT/elo_matches.tsv | grep " p7_${trained} " \
        | awk '{print $2}')
    local d0=$(grep -o 'win_rate=[0-9.]*' $OUT/probe_D0_${trained}.txt | head -1 | cut -d= -f2)
    local d1=$(grep -o 'win_rate=[0-9.]*' $OUT/probe_D1_${trained}.txt | head -1 | cut -d= -f2)
    local d1h=$(grep -o 'win_rate=[0-9.]*' $OUT/probe_D1h_${trained}.txt | head -1 | cut -d= -f2)
    local ft=$(grep -o 'flashThreats=[0-9]*' $OUT/probe_D1_${trained}.txt | cut -d= -f2)
    local fto=$(grep -o 'flashThreatsOppTurn=[0-9]*' $OUT/probe_D1_${trained}.txt | cut -d= -f2)
    echo "P7ELO|seed=$SEED|trained=$trained|elo=$ELO|d0=$d0|d1=$d1|d1h=$d1h|flashThreats=$ft|oppTurn=$fto" \
        | tee -a $OUT/elo_curve.txt
}

cd /home/user/mage
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break

    if [ $((trained % 256)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
        # rate the starting point too (trained=0 -> BC baseline Elo)
        [ ! -f $OUT/probe_D1h_${trained}.txt ] && rate_checkpoint $trained
    fi
    CHUNK=$((trained / 64))
    IFS='|' read -r OPPCK OPPARCH <<< "$(pick_opponent $CHUNK)"

    start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log \
        "--lr $LRVAL --log $OUT/train.csv"
    ASRV=$(cat $OUT/.srvpid)
    start_server "$OPPCK" "$OPPARCH" $OPORT $OUT/oserver.log
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
        -Drl.mode=train -Drl.seed=$((80000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "P7_FAILED|s$SEED|no_training_rows (trained stays $trained)"
        exit 1
    fi
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt
    echo "P7|s$SEED|trained=$trained|opp=$(basename $OPPCK)"

    if [ $((trained % 256)) -eq 0 ] || [ "$trained" -ge "$BUDGET" ]; then
        rate_checkpoint $trained
    fi
done
cp $OUT/net.pt $OUT/p7_final.pt
echo "P7_DONE|seed=$SEED|trained=$(cat $OUT/trained.txt)"
