#!/bin/bash
# E3 verification battery: is anything the E3 encoder added actually
# READ by the pilot policy? The Phase 8b protocol (rl/p8b_scramble.py,
# PHASE8B-CHANNEL.md step 1), refined per channel.
#
# Card-channel conditions corrupt the feature TSV (rl/e3_scramble.py):
#   text_scrambled / text_zeroed   the NEW 32 text dims
#   mech_scrambled                 E2's 68 dims - the positive control,
#                                  8b measured -.38 for this channel
#   all_scrambled                  the exact 8b corruption
# Hand-built-dim conditions zero dims in the encoder itself:
#   ablate_top   s[24-27] known top of library
#   ablate_hand  s[28]    hand differential
#   ablate_pips  c[17-21] colored-pip structure
#
# Every condition needs a FRESH driver JVM: the feature table and the
# ablation masks are read in StateEncoder's static initializer, and
# RLDriverServer pins both for the life of the JVM.
#
# Usage: bash rl/e3_ablate.sh <net.pt> [games=200] [seed=0]
#   E3_DECK   deck to evaluate on (default BenchDimir.dck; the group-1
#             dims are dark on it - use E3ScryProbe.dck, which swaps 3
#             Islands for scry lands, to exercise them)
#   E3_CASES  space-separated subset of cases to run (default: all)
#   E3_OUT    output directory
set -u
NET=$1
GAMES=${2:-200}
SEED=${3:-0}
CG=/home/user/CardGuru
ARCH=lstmattn
SDIM=29; CDIM=123
APORT=7961; DPORT=7960
DECK=${E3_DECK:-BenchDimir.dck}
OUT=${E3_OUT:-/tmp/rl_e3_ablate}
mkdir -p $OUT
python3 $CG/rl/e3_scramble.py --outdir $OUT || exit 1

run_case() {   # $1 tag $2 featfile $3 extra-D-flags $4 opponent $5 games
    bash $CG/rl/driver_server.sh stop $DPORT > /dev/null 2>&1
    bash $CG/rl/driver_server.sh start $DPORT \
        "-Dmage.randomPerThread=true -XX:+UseParallelGC" > /dev/null || return 1
    rm -f $OUT/srv_$1.log
    python3 $CG/rl/policy_server.py --port $APORT --ckpt "$NET" --seed $SEED \
        --sdim $SDIM --cdim $CDIM --arch $ARCH > $OUT/srv_$1.log 2>&1 &
    local PSRV=$!
    SECONDS=0
    while [ $SECONDS -lt 120 ]; do
        grep -q "policy server" $OUT/srv_$1.log 2>/dev/null && break
        sleep 1
    done
    RL_PERSIST=1 RL_DRIVER_PORT=$DPORT \
    bash $CG/rl/run_driver.sh \
        -Drl.episodes=$5 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.cardFeatures=$2 -Drl.e3=on $3 \
        -Drl.opponent=$4 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=950000 -Drl.report=1 \
        -Drl.out=$OUT/probe_$1_$4.txt > /dev/null 2>&1
    kill $PSRV 2>/dev/null; wait $PSRV 2>/dev/null
    # eval is argmax and seeds are fixed, so a condition that changes
    # NOTHING in the summary counters did not change a single decision:
    # a behavioural read that survives a win rate pinned near the floor
    local line=$(grep "RL|summary" $OUT/probe_$1_$4.txt 2>/dev/null | tail -1)
    local wr=$(echo "$line" | grep -o 'win_rate=[0-9.]*' | cut -d= -f2)
    local kt=$(echo "$line" | grep -o 'knownTopWindows=[0-9]*' | cut -d= -f2)
    local ew=$(echo "$line" | grep -o 'encodeWindows=[0-9]*' | cut -d= -f2)
    local sr=$(echo "$line" | grep -o 'seenRecorded=[0-9]*' | cut -d= -f2)
    local tp=$(echo "$line" | grep -o 'turns_per_ep=[0-9.]*' | cut -d= -f2)
    local ac=$(echo "$line" | grep -o 'agent_actions_per_ep=[0-9.]*' | cut -d= -f2)
    local cs=$(echo "$line" | grep -o 'agent_consults_per_ep=[0-9.]*' | cut -d= -f2)
    local bd=$(echo "$line" | grep -o 'blocksDeclared=[0-9]*' | cut -d= -f2)
    local ftc=$(echo "$line" | grep -o 'flashThreats=[0-9]*' | cut -d= -f2)
    echo -e "E3ABL|case=$1|opp=$4|games=$5|win_rate=${wr:-NA}|turns=${tp:-NA}|actions=${ac:-NA}|consults=${cs:-NA}|blocks=${bd:-0}|flash=${ftc:-0}|knownTop=${kt:-0}|encodeWindows=${ew:-0}|seenRecorded=${sr:-0}" \
        | tee -a $OUT/results.txt
}

FEAT=$CG/rl/e3_features.tsv
CASES=${E3_CASES:-"baseline baseline_d1 text_scrambled text_zeroed mech_scrambled all_scrambled ablate_top ablate_hand ablate_pips"}
: > $OUT/results.txt
for c in $CASES; do
    case $c in
    baseline)       run_case baseline       $FEAT ""                       heuristic $GAMES ;;
    baseline_d1)    run_case baseline       $FEAT ""                       search    $GAMES ;;
    text_scrambled) run_case text_scrambled $OUT/e3_text_scrambled.tsv ""  heuristic $GAMES ;;
    text_zeroed)    run_case text_zeroed    $OUT/e3_text_zeroed.tsv ""     heuristic $GAMES ;;
    mech_scrambled) run_case mech_scrambled $OUT/e3_mech_scrambled.tsv ""  heuristic $GAMES ;;
    all_scrambled)  run_case all_scrambled  $OUT/e3_all_scrambled.tsv ""   heuristic $GAMES ;;
    ablate_top)     run_case ablate_top     $FEAT "-Drl.ablateState=24-27" heuristic $GAMES ;;
    ablate_hand)    run_case ablate_hand    $FEAT "-Drl.ablateState=28"    heuristic $GAMES ;;
    ablate_pips)    run_case ablate_pips    $FEAT "-Drl.ablateCand=17-21"  heuristic $GAMES ;;
    *) echo "unknown case $c" ;;
    esac
done
bash $CG/rl/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "E3ABL_DONE -> $OUT/results.txt"
cat $OUT/results.txt
