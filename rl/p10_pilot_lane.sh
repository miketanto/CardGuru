#!/bin/bash
# Phase 10 action 4.4 — UPPER-BOUND ARCHETYPE PILOTS.
#
# CHECKPOINT-PHASE10.md 4.4: "per-archetype random-init pilots trained
# to convergence (7c rec #4) — lifts the D0-piloted matrix caveat and
# supplies gated-league pressure at the top."
#
# The 7c robustness matrix rated every archetype row with a D0 pilot,
# and p7c_pilot_calib.sh showed D0 is not a neutral instrument: on
# redrush/skies the SEARCH seat is a *worse* pilot than the heuristic
# one (D1-over-D0 .44 / .43), so the archetype rows were rated by a
# pilot of unknown, deck-dependent competence. This lane replaces that
# pilot with a learned one: a from-random-init lstmattn that pilots the
# archetype deck itself, trained in a Phase-7b-style optimistic-Elo
# PFSP league whose pool is the Dimir field it will eventually pressure.
#
# Differences from league_lane_p7.sh (the fork parent):
#  - the AGENT's deck is the archetype (-Drl.deck=$DECK); the pool rows
#    carry their own deck (-Drl.oppDeck), as in league_lane_p7c.sh.
#  - the pool is the mirror-side field: scripted D0/D1/D1h on
#    BenchDimir + the project champion ck_6144 + attn_desp, PLUS the
#    lane's own snapshots (which pilot the archetype, both seats) as the
#    low ladder rungs a from-scratch net needs before the Dimir field
#    is playable at all. Selection is rl/p10_pilot_pick.py: Phase 7b
#    optimistic weighting, plus a 1-chunk-in-4 field share (Phase 7b's
#    scratch line rotated a real external opponent in at exactly that
#    cadence, and it is needed here: an argmax-mode random-init
#    snapshot is nearly passive, so the mirror family alone hands the
#    sampling seat 64-0 chunks it cannot learn from).
#  - RATING (P10_RATE, default 2048): 100g vs D0 piloting BenchDimir —
#    the exact cell the 7c matrix measured, with the seats swapped.
#    Reported raw AND as a deck-power-normalised pseudo-Elo:
#        elo = 1000 + 400*log10(wr/(1-wr))
#                   - 400*log10(power/(1-power))
#                   + 400*log10(.58/.42)
#    where power = D0(deck) vs D0(BenchDimir) from p7c_pilot_calib.sh
#    and .58 is that screen's same-deck seat baseline (D0 dimir vs D0
#    dimir), so a pilot exactly as good as D0 normalises to ~1000 on the
#    mirror Elo scale regardless of how strong its deck is.
#  - between ratings the self-Elo that drives PFSP is carried by an
#    ordinary Elo update (K=16) on each 64-episode chunk result against
#    the picked opponent's rating, and re-anchored to the measured value
#    at every rating. Free (the games are already played) and it keeps
#    the ladder from going flat over 32 chunks.
#
# Usage: bash rl/p10_pilot_lane.sh <seed> <name> <deck.dck> \
#            <agentPort> <oppPort> [budget=4096]
set -u
SEED=$1; NAME=$2; DECK=$3; APORT=$4; OPORT=$5; BUDGET=${6:-4096}
ARCH=lstmattn
LRVAL=${P10_LR:-1e-4}
RL=/home/user/CardGuru/rl
OUT=${P10_OUT:-/tmp/rl_p10_pilot_${NAME}}
FEATS=$RL/e2_features.tsv
CDIM=91
MIRROR=BenchDimir.dck
RATE=${P10_RATE:-2048}
SNAP=${P10_SNAP:-256}
CONC=${P10_CONC:-4}
PERSIST=${P10_PERSIST:-1}
INIT=${P10_INIT:-/tmp/rl_p7_scratch_init.pt}
POWER=${P10_POWER:-0.58}
CHAMP=${P10_CHAMP:-/tmp/rl_p7_lstmattn_s0/p7b_champion.pt}
CHAMPG=${P10_CHAMPG:-200}
mkdir -p $OUT/pool
touch $OUT/train.csv
[ -f $OUT/net.pt ] || cp "$INIT" $OUT/net.pt

# ---------------------------------------------------------------- server
start_server() {  # $1 ckpt $2 arch $3 port $4 logfile [$5 extra flags]
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
    echo "P10_FAILED|$NAME|server_never_started|$4"
    cat $4
    exit 1
}

stop_server() { kill $1 2>/dev/null; wait $1 2>/dev/null; }

field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

# --------------------------------------------------------------- ratings
# pseudo-Elo from one anchor, deck power divided out (see header)
norm_elo() {  # $1 win_rate -> Elo on the mirror scale
    python3 - "$1" "$POWER" <<'PY'
import math, sys
wr = min(max(float(sys.argv[1]), 0.01), 0.99)
p  = min(max(float(sys.argv[2]), 0.01), 0.99)
lg = lambda x: 400.0 * math.log10(x / (1.0 - x))
print(round(1000.0 + lg(wr) - lg(p) + lg(0.58)))
PY
}

# $1 out $2 opp-kind $3 opp-deck $4 episodes $5 seed [$6 extra flags]
# eval is always SEQUENTIAL (no RL_CONC) — probes must stay reproducible
probe() {
    RL_PERSIST=$PERSIST RL_AUTOSTART=1 \
    bash $RL/run_driver.sh \
        -Drl.episodes=$4 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=$2 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$3 -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$5 -Drl.report=0 \
        ${6:-} -Drl.out=$1 > /dev/null 2>&1
}

rate_checkpoint() {  # $1 trained
    local trained=$1 f=$OUT/probe_D0_${1}.txt
    if [ ! -s "$f" ]; then
        start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
        local ASRV=$(cat $OUT/.srvpid)
        probe $f heuristic $MIRROR 100 952000
        stop_server $ASRV
    fi
    [ -s "$f" ] || { echo "P10_FAILED|$NAME|probe_D0_${trained} empty"; exit 1; }
    local wr=$(field $f win_rate) elo
    elo=$(norm_elo ${wr:-0.5})
    echo "$elo" > $OUT/self_elo.txt
    echo "P10ELO|pilot=$NAME|deck=$DECK|trained=$trained|vs_D0_dimir=${wr}|norm_elo=${elo}|blocks=$(field $f blocksDeclared)|blockOpps=$(field $f blockOpportunities)|stalls=$(field $f stalls)|flashThreats=$(field $f flashThreats)|oppTurn=$(field $f flashThreatsOppTurn)" \
        | tee -a $OUT/elo_curve.txt
    # the freshly rated snapshot re-enters the pool at its measured value
    if [ -f $OUT/pool/ck_${trained}.pt ]; then
        grep -q "^ck_${trained}|" $OUT/pool_elo.tsv 2>/dev/null || \
            echo "ck_${trained}|rl:${ARCH}:$OUT/pool/ck_${trained}.pt|$DECK|$elo" \
                >> $OUT/pool_elo.tsv
    fi
}

# ------------------------------------------------------------------ pool
seed_pool() {
    [ -s $OUT/pool_elo.tsv ] && return 0
    cat > $OUT/pool_elo.tsv <<EOF
D0|heuristic|$MIRROR|1000
D1|search|$MIRROR|1085
D1h|searchhold|$MIRROR|1088
EOF
    local C CN CK CE
    for C in "champ6144|$CHAMP|1101" \
             "attn_desp|/tmp/rl_c6_attn_s7/attn_desp_final.pt|1053" \
             "p7c_1536|/tmp/rl_p7c_lstmattn_s0/pool/ck_1536.pt|1096"; do
        IFS='|' read -r CN CK CE <<< "$C"
        local CA=$ARCH
        [ "$CN" = "attn_desp" ] && CA=attn
        [ -f "$CK" ] && echo "${CN}|rl:${CA}:${CK}|$MIRROR|$CE" >> $OUT/pool_elo.tsv
    done
    echo "P10_POOL_SEEDED|$NAME|rows=$(wc -l < $OUT/pool_elo.tsv)"
}

# ------------------------------------------------------------------ loop
cd /home/user/mage
pkill -f "policy_serve[r].py --port $APORT" 2>/dev/null
pkill -f "policy_serve[r].py --port $OPORT" 2>/dev/null
sleep 1

while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break
    seed_pool

    if [ $((trained % SNAP)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
        if [ $((trained % RATE)) -eq 0 ] && [ ! -s $OUT/probe_D0_${trained}.txt ]; then
            rate_checkpoint $trained
        else
            SELFE=$(cat $OUT/self_elo.txt 2>/dev/null || echo 46)
            grep -q "^ck_${trained}|" $OUT/pool_elo.tsv 2>/dev/null || \
                echo "ck_${trained}|rl:${ARCH}:$OUT/pool/ck_${trained}.pt|$DECK|$SELFE" \
                    >> $OUT/pool_elo.tsv
        fi
    fi

    CHUNK=$((trained / 64))
    SELF=$(cat $OUT/self_elo.txt 2>/dev/null || echo 46)
    IFS='|' read -r OKIND ODECK ONAME OELO <<< \
        "$(python3 $RL/p10_pilot_pick.py --pool $OUT/pool_elo.tsv \
             --self-elo $SELF --chunk $CHUNK --agent-deck $DECK \
             --field-share ${P10_FIELD_SHARE:-0.25})"

    THREADFLAG=""
    [ "$CONC" -gt 1 ] && THREADFLAG="--threads $CONC"
    start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log \
        "--lr $LRVAL --log $OUT/train.csv $THREADFLAG"
    ASRV=$(cat $OUT/.srvpid)
    OSRV=""
    if [[ "$OKIND" == rl:* ]]; then
        OPPARCH=$(echo "$OKIND" | cut -d: -f2)
        OPPCK=$(echo "$OKIND" | cut -d: -f3-)
        start_server "$OPPCK" "$OPPARCH" $OPORT $OUT/oserver.log "$THREADFLAG"
        OSRV=$(cat $OUT/.srvpid)
        OPPFLAGS="-Drl.opponent=rl -Drl.oppPort=$OPORT"
    else
        OPPFLAGS="-Drl.opponent=$OKIND -Drl.searchPlies=1 -Drl.searchBreadth=8"
    fi

    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    RL_PERSIST=$PERSIST RL_AUTOSTART=1 \
    RL_CONC=$([ "$CONC" -gt 1 ] && echo $CONC || echo "") \
    bash $RL/run_driver.sh \
        -Drl.episodes=64 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        $OPPFLAGS \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$ODECK -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((100000000 + SEED*1000000 + trained)) \
        -Drl.report=0 -Drl.out=$OUT/chunk.txt > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    [ -n "$OSRV" ] && stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "P10_FAILED|$NAME|no_training_rows (trained stays $trained)"
        exit 1
    fi

    CWR=$(field $OUT/chunk.txt win_rate)
    # Elo update on the chunk (K=16), so the ladder keeps moving between
    # the sparse measured ratings; re-anchored at every rate_checkpoint.
    NEWSELF=$(python3 - "$SELF" "${OELO:-1000}" "${CWR:-0.5}" <<'PY'
import sys
self_e, opp_e, wr = (float(x) for x in sys.argv[1:4])
exp = 1.0 / (1.0 + 10 ** ((opp_e - self_e) / 400.0))
print(round(min(max(self_e + 16.0 * (wr - exp), 0.0), 1600.0)))
PY
)
    echo "$NEWSELF" > $OUT/self_elo.txt

    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt
    echo "P10|$NAME|trained=$trained|opp=$ONAME|deck=$ODECK|chunk_wr=${CWR}|self_elo=$NEWSELF"

    if [ $((trained % RATE)) -eq 0 ] || [ "$trained" -ge "$BUDGET" ]; then
        [ -f $OUT/pool/ck_${trained}.pt ] || cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
        [ -s $OUT/probe_D0_${trained}.txt ] || rate_checkpoint $trained
    fi
done

cp $OUT/net.pt $OUT/p10_pilot_${NAME}.pt

# ------------------------------------------------- champion match (200g)
# The deliverable claim: does a converged archetype pilot pressure the
# project champion? Agent pilots $DECK, ck_6144 pilots BenchDimir.
if [ -f "$CHAMP" ] && [ ! -s $OUT/champ_match.txt ]; then
    THREADFLAG=""
    start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
    ASRV=$(cat $OUT/.srvpid)
    start_server "$CHAMP" $ARCH $OPORT $OUT/oserver.log
    OSRV=$(cat $OUT/.srvpid)
    RL_PERSIST=$PERSIST RL_AUTOSTART=1 \
    bash $RL/run_driver.sh \
        -Drl.episodes=$CHAMPG \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=rl -Drl.oppPort=$OPORT \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$MIRROR -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=955000 -Drl.report=0 \
        -Drl.out=$OUT/champ_match.txt > /dev/null 2>&1
    stop_server $ASRV
    stop_server $OSRV
fi
if [ -s $OUT/champ_match.txt ]; then
    echo "P10CHAMP|pilot=$NAME|deck=$DECK|games=$CHAMPG|vs_ck6144=$(field $OUT/champ_match.txt win_rate)|wins=$(field $OUT/champ_match.txt wins)|draws=$(field $OUT/champ_match.txt draws)|stalls=$(field $OUT/champ_match.txt stalls)|blocks=$(field $OUT/champ_match.txt blocksDeclared)|blockOpps=$(field $OUT/champ_match.txt blockOpportunities)" \
        | tee -a $OUT/elo_curve.txt
fi
echo "P10_DONE|pilot=$NAME|trained=$(cat $OUT/trained.txt)"
