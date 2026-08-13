#!/bin/bash
# Phase 7c follow-up A: per-deck SPECIALISTS.
#
# Question: is 3072 episodes better spent blocked (one deck at a time,
# to convergence) or interleaved (the curriculum league)? Each
# specialist starts from the SAME frozen p7_final.pt the curriculum
# started from and trains against ONE deck only, 512 episodes - so six
# specialists cost exactly the 3072 episodes the curriculum spent.
#
# What it measures that the curriculum cannot:
#   - per-deck CEILING: how well this architecture can do against deck X
#     when it only has to beat X. Specialist WR minus generalist WR is a
#     direct read on interference.
#   - FORGETTING: each specialist is re-rated on the Dimir mirror. Phase
#     6 found a narrow league gradient eroded the attention family's
#     prior (attn_bc 1044 -> attn_v2 1039); single-deck training is the
#     maximally narrow gradient, so this is where that shows up.
#
# The agent always pilots BenchDimir - a "specialist" is a specialist in
# the Dimir-vs-X matchup, not a pilot of X. (Piloting X is the exploiter
# lane, rl/p7c_exploiter.sh.)
#
# Usage: bash rl/p7c_specialist.sh <agentPort> [budget=512]
set -u
APORT=${1:-7811}
BUDGET=${2:-512}
RL=/home/user/CardGuru/rl
INIT=/tmp/rl_p7_lstmattn_s0/p7_final.pt
ARCH=lstmattn
CDIM=91
DECK=BenchDimir.dck
FEATS=$RL/e2_features.tsv
LRVAL=${P7C_LR:-3e-4}
CURRIC=${P7C_CURRICULUM:-$RL/p7c_curriculum.tsv}
ROOT=/tmp/rl_p7c_spec

start_server() {  # $1 ckpt $2 port $3 log [$4 train-flags]
    local try
    for try in 1 2 3; do
        rm -f $3
        python3 $RL/policy_server.py --port $2 --ckpt "$1" \
            --seed 0 --cdim $CDIM --arch $ARCH ${4:-} > $3 2>&1 &
        echo $! > /tmp/.spec_srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" $3 2>/dev/null && { up=1; break; }
            grep -q "Traceback" $3 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat /tmp/.spec_srvpid) 2>/dev/null
        wait $(cat /tmp/.spec_srvpid) 2>/dev/null
        grep -q "Address already in use" $3 2>/dev/null || break
    done
    echo "SPEC_FAILED|server_never_started|$3"; exit 1
}
stop_server() { kill $1 2>/dev/null; wait $1 2>/dev/null; }
field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

cd /home/user/mage
while IFS=$'\t' read -r ORD NAME DCK KIND ELO; do
    case "$ORD" in \#*|"") continue ;; esac
    OUT=$ROOT/$NAME
    mkdir -p $OUT
    [ -f $OUT/net.pt ] || cp "$INIT" $OUT/net.pt

    # ---- train 512 episodes against this deck only
    while true; do
        T=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
        [ "$T" -ge "$BUDGET" ] && break
        start_server $OUT/net.pt $APORT $OUT/server.log \
            "--lr $LRVAL --log $OUT/train.csv"
        SRV=$(cat /tmp/.spec_srvpid)
        before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
        mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
            -DargLine="-Dfile.encoding=UTF-8 -Xmx3500m" \
            -DfailIfNoTests=false -Drl.episodes=64 \
            -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
            -Drl.opponent=$KIND -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS \
            -Drl.noYields=true -Drl.consultBudget=4000 \
            -Drl.deck=$DECK -Drl.oppDeck=$DCK -Drl.stopTurn=80 \
            -Drl.mode=train -Drl.seed=$((91000000 + T)) \
            -Drl.report=0 > /dev/null 2>&1
        after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
        stop_server $SRV
        if [ "$after" -le "$before" ]; then
            echo "SPEC_FAILED|$NAME|no_training_rows at $T"; exit 1
        fi
        T=$((T + 64)); echo $T > $OUT/trained.txt
        echo "SPEC|$NAME|trained=$T"
    done
    cp $OUT/net.pt $OUT/final.pt

    # ---- own-deck ceiling (100g vs the same opponent it trained on)
    if [ ! -s $OUT/own.txt ]; then
        start_server $OUT/final.pt $APORT $OUT/server.log
        SRV=$(cat /tmp/.spec_srvpid)
        mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
            -DargLine="-Dfile.encoding=UTF-8 -Xmx3500m" \
            -DfailIfNoTests=false -Drl.episodes=100 \
            -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
            -Drl.opponent=$KIND -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS \
            -Drl.noYields=true -Drl.consultBudget=4000 \
            -Drl.deck=$DECK -Drl.oppDeck=$DCK -Drl.stopTurn=80 \
            -Drl.mode=eval -Drl.seed=951000 -Drl.report=0 \
            -Drl.out=$OUT/own.txt > /dev/null 2>&1
        stop_server $SRV
    fi

    # ---- forgetting check: mirror Elo on the Phase 6 scale
    touch $ROOT/elo_matches.tsv
    for SK in "heuristic|D0" "search|D1" "searchhold|D1h"; do
        IFS='|' read -r AK SN <<< "$SK"
        grep -q "^spec_${NAME}	${SN}	" $ROOT/elo_matches.tsv && continue
        start_server $OUT/final.pt $APORT $OUT/server.log
        SRV=$(cat /tmp/.spec_srvpid)
        mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
            -DargLine="-Dfile.encoding=UTF-8 -Xmx3500m" \
            -DfailIfNoTests=false -Drl.episodes=100 \
            -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
            -Drl.opponent=$AK -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS \
            -Drl.noYields=true -Drl.consultBudget=4000 \
            -Drl.deck=$DECK -Drl.oppDeck=$DECK -Drl.stopTurn=80 \
            -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
            -Drl.out=$OUT/probe_${SN}.txt > /dev/null 2>&1
        stop_server $SRV
        w=$(grep -o 'wins=[0-9]*' $OUT/probe_${SN}.txt | cut -d= -f2)
        d=$(grep -o 'draws=[0-9]*' $OUT/probe_${SN}.txt | cut -d= -f2)
        echo -e "spec_${NAME}\t${SN}\t${w}\t${d}\t100" >> $ROOT/elo_matches.tsv
    done
    ELO=$(python3 $RL/elo_fit.py --matches $ROOT/elo_matches.tsv \
        | grep " spec_${NAME} " | awk '{print $2}')
    echo "SPEC_RESULT|deck=$NAME|own_deck_wr=$(field $OUT/own.txt win_rate)|mirror_elo=${ELO:-NA}|d0=$(field $OUT/probe_D0.txt win_rate)|d1=$(field $OUT/probe_D1.txt win_rate)|blocks=$(field $OUT/own.txt blocksDeclared)|blockOpps=$(field $OUT/own.txt blockOpportunities)|stalls=$(field $OUT/own.txt stalls)" \
        | tee -a $ROOT/results.txt
done < $CURRIC
echo "SPEC_DONE"
