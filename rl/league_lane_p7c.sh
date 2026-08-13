#!/bin/bash
# Phase 7c: archetype-curriculum league. The agent always pilots
# BenchDimir.dck; the VARIABLE is what it faces. One new opponent
# archetype is introduced every $INTRO_EVERY episodes, easiest-first,
# piloted by a scripted seat (D0/D1/D1h) - so deck identity, not
# opponent skill, is what changes.
#
# Differences from league_lane_p7.sh (which this is a fork of):
#  - pool rows carry a DECK: name|kind|deck|elo, kind is heuristic |
#    search | searchhold | rl:<arch>:<ckpt>. Scripted rows need no
#    server; rl rows get one on $OPORT as before.
#  - opponent-seat deck is passed with -Drl.oppDeck (driver change
#    mirrored into rl/xmage-src/RLEpisodeDriver.java).
#  - selection is rl/pfsp_pick_p7c.py (Phase 7b weighting + a floor on
#    archetype mass, so the curriculum cannot be starved by the mirror).
#  - every $MEASURE_EVERY episodes: mirror mini-Elo (comparable to the
#    main session's curve) + a robustness matrix over every introduced
#    archetype + the blocking counters + a sample transcript.
#
# Usage: bash rl/league_lane_p7c.sh <seed> <agentPort> <oppPort> \
#            <initCkpt> [budget=3072]
set -u
SEED=$1; APORT=$2; OPORT=$3; INIT=$4; BUDGET=${5:-3072}
ARCH=lstmattn
LRVAL=${P7C_LR:-3e-4}
OUT=/tmp/rl_p7c_${ARCH}_s${SEED}
DECK=BenchDimir.dck
FEATS=/home/user/CardGuru/rl/e2_features.tsv
CDIM=91
RL=/home/user/CardGuru/rl
INTRO_EVERY=${P7C_INTRO_EVERY:-512}
MEASURE_EVERY=${P7C_MEASURE_EVERY:-512}
CURRIC=${P7C_CURRICULUM:-$RL/p7c_curriculum.tsv}
mkdir -p $OUT/pool
[ -f $OUT/net.pt ] || cp "$INIT" $OUT/net.pt

# ---------------------------------------------------------------- server
start_server() {  # $1 ckpt $2 arch $3 port $4 logfile [$5 train-flags]
    local try
    for try in 1 2 3; do
        rm -f $4
        python3 $RL/policy_server.py --port $3 \
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
    echo "P7C_FAILED|s$SEED|server_never_started|$4"
    cat $4
    exit 1
}

stop_server() { kill $1 2>/dev/null; wait $1 2>/dev/null; }

# ------------------------------------------------------------ mirror pool
# The curriculum supplies DECK variety; these rows supply the SKILL
# ladder, all on BenchDimir, so PFSP always has something at every
# rating. Elos are the Phase 6 leaderboard (D0 = 1000 anchor).
seed_pool() {
    [ -s $OUT/pool_elo.tsv ] && return 0
    cat > $OUT/pool_elo.tsv <<EOF
D0|heuristic|$DECK|1000
D1|search|$DECK|1085
D1h|searchhold|$DECK|1088
EOF
    local C CN CA CC
    for C in "attn_bc|attn|/tmp/rl_p5_c1/student_e2attn.pt|1044" \
             "attn_v2|attn|/tmp/rl_c6_attn_s0/attn_v2_final.pt|1039" \
             "attn_desp|attn|/tmp/rl_c6_attn_s7/attn_desp_final.pt|1053"; do
        IFS='|' read -r CN CA CC CE <<< "$C"
        [ -f "$CC" ] && echo "${CN}|rl:${CA}:${CC}|$DECK|$CE" >> $OUT/pool_elo.tsv
    done
    echo "P7C_POOL_SEEDED|rows=$(wc -l < $OUT/pool_elo.tsv)"
}

# ------------------------------------------------------------ curriculum
# p7c_curriculum.tsv rows: order<TAB>name<TAB>deck<TAB>kind<TAB>elo
# (elo seeded by the calibration screen; recomputed at each checkpoint)
introduced_count() {   # $1 trained -> how many archetypes are live
    local n=$(( $1 / INTRO_EVERY + 1 ))
    local total=$(grep -vc '^#' $CURRIC)
    [ "$n" -gt "$total" ] && n=$total
    echo $n
}

sync_pool() {   # append rows for archetypes that just became live
    local trained=$1 n i line name deck kind elo
    n=$(introduced_count $trained)
    touch $OUT/pool_elo.tsv
    i=0
    while IFS=$'\t' read -r ord name deck kind elo; do
        case "$ord" in \#*|"") continue ;; esac
        i=$((i + 1))
        [ "$i" -gt "$n" ] && break
        grep -q "^${name}|" $OUT/pool_elo.tsv && continue
        echo "${name}|${kind}|${deck}|${elo}" >> $OUT/pool_elo.tsv
        echo "P7C_INTRO|trained=${trained}|archetype=${name}|deck=${deck}|kind=${kind}|elo=${elo}"
    done < $CURRIC
}

live_archetypes() {   # echo "name deck kind" per live row
    local n=$(introduced_count $1) i=0
    while IFS=$'\t' read -r ord name deck kind elo; do
        case "$ord" in \#*|"") continue ;; esac
        i=$((i + 1))
        [ "$i" -gt "$n" ] && break
        echo "$name $deck $kind"
    done < $CURRIC
}

# ------------------------------------------------------------- probing
# $1 out-file $2 opponent-kind $3 opp-deck $4 episodes $5 seed [$6 extra]
probe() {
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=$4 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=$2 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$3 -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$5 -Drl.report=0 \
        ${6:-} -Drl.out=$1 > /dev/null 2>&1
}

field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

# mirror mini-Elo: directly comparable to the Phase 7 curve
rate_checkpoint() {
    local trained=$1 AK SN line w d ELO
    touch $OUT/elo_matches.tsv
    for SK in "heuristic|D0" "search|D1" "searchhold|D1h"; do
        IFS='|' read -r AK SN <<< "$SK"
        grep -q "^p7c_${trained}	${SN}	" $OUT/elo_matches.tsv && continue
        start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
        local ASRV=$(cat $OUT/.srvpid)
        probe $OUT/probe_${SN}_${trained}.txt $AK $DECK 100 950000
        stop_server $ASRV
        line=$(tail -1 $OUT/probe_${SN}_${trained}.txt 2>/dev/null)
        [ -z "$line" ] && { echo "P7C_FAILED|probe_${SN}_${trained} empty"; exit 1; }
        w=$(echo "$line" | grep -o 'wins=[0-9]*' | cut -d= -f2)
        d=$(echo "$line" | grep -o 'draws=[0-9]*' | cut -d= -f2)
        echo -e "p7c_${trained}\t${SN}\t${w}\t${d}\t100" >> $OUT/elo_matches.tsv
    done
    ELO=$(python3 $RL/elo_fit.py --matches $OUT/elo_matches.tsv \
        | grep " p7c_${trained} " | awk '{print $2}')
    local d0=$(field $OUT/probe_D0_${trained}.txt win_rate)
    local d1=$(field $OUT/probe_D1_${trained}.txt win_rate)
    local d1h=$(field $OUT/probe_D1h_${trained}.txt win_rate)
    local bd=$(field $OUT/probe_D1_${trained}.txt blocksDeclared)
    local bo=$(field $OUT/probe_D1_${trained}.txt blockOpportunities)
    local ft=$(field $OUT/probe_D1_${trained}.txt flashThreats)
    local fto=$(field $OUT/probe_D1_${trained}.txt flashThreatsOppTurn)
    echo "P7CELO|seed=$SEED|trained=$trained|elo=$ELO|d0=$d0|d1=$d1|d1h=$d1h|blocks=${bd:-0}|blockOpps=${bo:-0}|flashThreats=${ft:-0}|oppTurn=${fto:-0}" \
        | tee -a $OUT/elo_curve.txt
    [ -n "$ELO" ] && echo "$ELO" > $OUT/self_elo.txt
    # the agent's own snapshot joins the pool as a mirror row
    grep -q "^ck_${trained}|" $OUT/pool_elo.tsv 2>/dev/null || \
        echo "ck_${trained}|rl:${ARCH}:$OUT/pool/ck_${trained}.pt|$DECK|$ELO" \
            >> $OUT/pool_elo.tsv
}

# robustness matrix: 100g vs D0 piloting EACH introduced archetype
rate_matrix() {
    local trained=$1 name deck kind f wr bd bo st
    while read -r name deck kind; do
        [ -z "$name" ] && continue
        f=$OUT/matrix_${name}_${trained}.txt
        if [ ! -s "$f" ]; then
            start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
            local ASRV=$(cat $OUT/.srvpid)
            probe $f heuristic $deck 100 951000
            stop_server $ASRV
        fi
        wr=$(field $f win_rate); bd=$(field $f blocksDeclared)
        bo=$(field $f blockOpportunities); st=$(field $f stalls)
        echo "P7CMATRIX|trained=$trained|archetype=$name|deck=$deck|win_rate=${wr:-NA}|blocks=${bd:-0}|blockOpps=${bo:-0}|stalls=${st:-0}" \
            | tee -a $OUT/matrix.txt
    done < <(live_archetypes $trained)
}

# one full transcript per checkpoint, vs the newest archetype
sample_game() {
    local trained=$1 name deck kind
    [ -s $OUT/transcript_${trained}.txt ] && return 0
    read -r name deck kind < <(live_archetypes $trained | tail -1)
    [ -z "${name:-}" ] && return 0
    start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
    local ASRV=$(cat $OUT/.srvpid)
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=1 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=heuristic -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$deck -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=951000 -Drl.report=0 \
        -Dxmage.dataCollectors.printGameLogs=true \
        > $OUT/transcript_${trained}.txt 2>&1
    stop_server $ASRV
    echo "P7C_SAMPLE|trained=$trained|vs=$name|lines=$(wc -l < $OUT/transcript_${trained}.txt)"
}

# Each sub-step is independently resumable (elo_matches.tsv pairings,
# matrix_*.txt, transcript_*.txt); the marker only lets a completed
# battery be skipped without re-deriving all of that.
checkpoint_battery() {
    local trained=$1
    [ -f $OUT/.battery_${trained}.done ] && return 0
    rate_checkpoint $trained
    rate_matrix $trained
    sample_game $trained
    touch $OUT/.battery_${trained}.done
}

# ------------------------------------------------------------------ loop
cd /home/user/mage
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break

    seed_pool
    sync_pool $trained

    if [ $((trained % 256)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
    fi
    if [ $((trained % MEASURE_EVERY)) -eq 0 ]; then
        checkpoint_battery $trained
    fi

    CHUNK=$((trained / 64))
    SELF=$(cat $OUT/self_elo.txt 2>/dev/null || echo 916)
    IFS='|' read -r OKIND ODECK ONAME OELO <<< \
        "$(python3 $RL/pfsp_pick_p7c.py --pool $OUT/pool_elo.tsv \
             --self-elo $SELF --chunk $CHUNK)"

    start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log \
        "--lr $LRVAL --log $OUT/train.csv"
    ASRV=$(cat $OUT/.srvpid)
    OSRV=""
    if [[ "$OKIND" == rl:* ]]; then
        OPPARCH=$(echo "$OKIND" | cut -d: -f2)
        OPPCK=$(echo "$OKIND" | cut -d: -f3-)
        start_server "$OPPCK" "$OPPARCH" $OPORT $OUT/oserver.log
        OSRV=$(cat $OUT/.srvpid)
        OPPFLAGS="-Drl.opponent=rl -Drl.oppPort=$OPORT"
    else
        # scripted seat: no server, but it needs its search dials
        OPPFLAGS="-Drl.opponent=$OKIND -Drl.searchPlies=1 -Drl.searchBreadth=8"
    fi

    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=64 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        $OPPFLAGS \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$ODECK -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((90000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    [ -n "$OSRV" ] && stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "P7C_FAILED|s$SEED|no_training_rows (trained stays $trained)"
        exit 1
    fi
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt
    echo "P7C|s$SEED|trained=$trained|opp=$ONAME|deck=$ODECK|kind=$OKIND"

    if [ $((trained % MEASURE_EVERY)) -eq 0 ] || [ "$trained" -ge "$BUDGET" ]; then
        sync_pool $trained
        checkpoint_battery $trained
    fi
done
cp $OUT/net.pt $OUT/p7c_final.pt
echo "P7C_DONE|seed=$SEED|trained=$(cat $OUT/trained.txt)"
