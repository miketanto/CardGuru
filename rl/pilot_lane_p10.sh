#!/bin/bash
# Phase 10 action 4.4 — UPPER-BOUND PILOTS.
#
# 7c recommendation #4: every archetype row in the robustness matrix is
# piloted by a SCRIPTED seat, and the pilot calibration proved that seat
# is a lower bound of unknown tightness (D1 is a *worse* pilot than D0 on
# 4/6 archetypes; a 1-ply materialistic evaluator cannot value holding a
# counterspell). The only way to find the real bound is to train a net to
# pilot the deck. That is this lane.
#
# Differences from the lanes it is forked from:
#   - league_lane_p7.sh gave it the PFSP league (P7_PFSP recipe: pool
#     Elo, optimism +100, sigma 150, floor .02) and the Phase 9 fast path
#     (persistent driver JVM + rl.concurrency, per-worker opponent
#     connections, --threads on both policy servers).
#   - league_lane_p7c.sh gave it the deck-carrying pool schema and
#     -Drl.oppDeck.
#   - NEW here: the AGENT's deck is the archetype, not BenchDimir. The
#     agent is a pilot of X; its snapshots are X-mirror rungs; the
#     scripted rows pilot everything else. Nets start from RANDOM INIT —
#     these are meant to be upper bounds on how well the architecture can
#     pilot X, not transfer measurements.
#   - the rating anchor is CROSS-DECK and identical for every pilot:
#     100g agent(X) vs D0 piloting BenchDimir. Mirror Elo does not exist
#     for an agent that never plays the mirror, so this anchor (and only
#     this anchor) is what makes the three pilot curves comparable to
#     each other. It is NOT on the project's mirror Elo scale.
#
# Usage:
#   bash rl/pilot_lane_p10.sh <name> <agentDeck> <seed> <aport> <oport> \
#        <initCkpt> [budget=4096]
# Env: P10_RATE (default 2048) anchor-probe cadence
#      P10_SNAP (default 256)  snapshot/pool cadence
#      P10_CONC (default 4)    concurrent episodes per training chunk
#      P10_LR   (default 1e-4) same as the 7b scratch line
set -u
NAME=$1; ADECK=$2; SEED=$3; APORT=$4; OPORT=$5; INIT=$6; BUDGET=${7:-4096}
ARCH=lstmattn
CDIM=91
RL=/home/user/CardGuru/rl
FEATS=$RL/e2_features.tsv
OUT=/tmp/rl_p10_pilot_${NAME}
POOLSPEC=${P10_POOLSPEC:-$RL/p10_pilot_pool.tsv}
LRVAL=${P10_LR:-1e-4}
RATE=${P10_RATE:-2048}
SNAP=${P10_SNAP:-256}
CONCN=${P10_CONC:-4}
ANCHOR_DECK=BenchDimir.dck      # the common cross-pilot anchor seat
mkdir -p $OUT/pool
[ -f $OUT/net.pt ] || cp "$INIT" $OUT/net.pt

# ---------------------------------------------------------------- servers
start_server() {  # $1 ckpt $2 arch $3 port $4 log [$5 extra flags]
    local try
    for try in 1 2 3; do
        rm -f $4
        # one intra-op thread per server: two policy servers x --threads N
        # connection threads on 4 cores oversubscribe torch badly, and
        # these are batch-1 matmuls that gain nothing from it anyway
        OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
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
    echo "P10_FAILED|$NAME|server_never_started|$4"; cat $4; exit 1
}
stop_server() { kill $1 2>/dev/null; wait $1 2>/dev/null; }
field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

# ------------------------------------------------------------------ pool
# Rows: name|kind|deck|elo   (kind = heuristic|search|searchhold|rl:arch:ckpt)
seed_pool() {
    [ -s $OUT/pool_elo.tsv ] && return 0
    while IFS=$'\t' read -r RN RK RD RE; do
        case "$RN" in \#*|"") continue ;; esac
        # the agent's own deck is covered by its snapshot rungs
        [ "$RD" = "$ADECK" ] && continue
        echo "${RN}|${RK}|${RD}|${RE}" >> $OUT/pool_elo.tsv
    done < $POOLSPEC
    echo "P10_POOL_SEEDED|$NAME|rows=$(wc -l < $OUT/pool_elo.tsv)"
}

# --------------------------------------------------------------- probing
probe() {  # $1 out $2 oppKind $3 oppDeck $4 games $5 seed
    # eval stays SEQUENTIAL (no RL_CONC) so the curve stays reproducible
    RL_PERSIST=${P10_PERSIST:-1} RL_AUTOSTART=0 \
    bash $RL/run_driver.sh \
        -Drl.episodes=$4 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=$2 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$ADECK -Drl.oppDeck=$3 -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$5 -Drl.report=0 \
        -Drl.out=$1 > /dev/null 2>&1
}

# Running self-Elo between the (deliberately sparse, 2048-cadence) anchor
# probes. Without it the PFSP target and every snapshot's pool rating are
# frozen for 2048 episodes, so the ladder's own rungs all enter at a stale
# rating and the picker keeps re-sampling opponents the agent has outgrown
# - the 7b drift failure in miniature. One Elo update per 64-episode chunk
# against the sampled opponent's pool rating; the measured anchor Elo
# overwrites it whenever one is taken.
update_self_elo() {   # $1 chunk win rate $2 opponent elo
    python3 - "$1" "$2" "$(cat $OUT/self_elo.txt 2>/dev/null || echo 400)" \
        <<'PY' > $OUT/self_elo.txt.new && mv $OUT/self_elo.txt.new $OUT/self_elo.txt
import sys
s, opp, self_elo = (float(x) for x in sys.argv[1:4])
exp = 1.0 / (1.0 + 10 ** ((opp - self_elo) / 400.0))
K = 32.0                       # 64 games per chunk, sampled (not argmax) play
print("%.0f" % min(max(self_elo + K * (s - exp), 0.0), 2000.0))
PY
}

# score -> Elo on the anchor scale (D0 piloting BenchDimir = 1000)
anchor_elo() {  # $1 wins $2 draws $3 games
    python3 - "$1" "$2" "$3" <<'PY'
import math, sys
w, d, n = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
s = min(max((w + .5 * d) / n, .005), .995)
print("%.0f" % (1000 + 400 * math.log10(s / (1 - s))))
PY
}

rate_checkpoint() {   # $1 trained
    local trained=$1 f line w d n elo
    # the cadences can ask for the same point twice (snapshot block at the
    # top of an iteration, rate block at the bottom of the previous one)
    [ -f $OUT/.rated_${trained} ] && return 0
    f=$OUT/anchor_${trained}.txt
    if [ ! -s "$f" ]; then
        start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
        local ASRV=$(cat $OUT/.srvpid)
        probe $f heuristic $ANCHOR_DECK 100 950000
        stop_server $ASRV
    fi
    line=$(tail -1 $f 2>/dev/null)
    [ -z "$line" ] && { echo "P10_FAILED|$NAME|anchor_${trained} empty"; exit 1; }
    w=$(echo "$line" | grep -o 'wins=[0-9]*' | cut -d= -f2)
    d=$(echo "$line" | grep -o 'draws=[0-9]*' | cut -d= -f2)
    elo=$(anchor_elo ${w:-0} ${d:-0} 100)
    echo "$elo" > $OUT/self_elo.txt        # measured: overrides the running estimate
    echo "P10ELO|pilot=$NAME|trained=$trained|wr=$(field $f win_rate)|elo=$elo|wins=$w|draws=$d|blocks=$(field $f blocksDeclared)|blockOpps=$(field $f blockOpportunities)|stalls=$(field $f stalls)|turns=$(field $f turns_per_ep)|flashThreats=$(field $f flashThreats)|oppTurn=$(field $f flashThreatsOppTurn)" \
        | tee -a $OUT/elo_curve.txt
    touch $OUT/.rated_${trained}
}

# ------------------------------------------------------------------ loop
# a crashed prior run can leave servers bound to our ports
pkill -f "policy_serve[r].py --port $APORT" 2>/dev/null
pkill -f "policy_serve[r].py --port $OPORT" 2>/dev/null
sleep 1
cd /home/user/mage
seed_pool
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break

    if [ $((trained % SNAP)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
        if [ $((trained % RATE)) -eq 0 ]; then
            rate_checkpoint $trained
        fi
        # snapshots enter the pool at the current anchor-Elo estimate
        SELFE=$(cat $OUT/self_elo.txt 2>/dev/null || echo 400)
        grep -q "^ck_${trained}|" $OUT/pool_elo.tsv 2>/dev/null || \
            echo "ck_${trained}|rl:${ARCH}:$OUT/pool/ck_${trained}.pt|$ADECK|$SELFE" \
                >> $OUT/pool_elo.tsv
    fi

    CHUNK=$((trained / 64))
    SELF=$(cat $OUT/self_elo.txt 2>/dev/null || echo 400)
    IFS='|' read -r OKIND ODECK ONAME OELO <<< \
        "$(python3 $RL/pfsp_pick_p7c.py --pool $OUT/pool_elo.tsv \
             --self-elo $SELF --chunk $CHUNK --mirror-deck $ADECK)"

    THREADFLAG=""
    [ "$CONCN" -gt 1 ] && THREADFLAG="--threads $CONCN"
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
    RL_PERSIST=${P10_PERSIST:-1} RL_AUTOSTART=0 \
    RL_CONC=$([ "$CONCN" -gt 1 ] && echo $CONCN || echo "") \
    bash $RL/run_driver.sh \
        -Drl.episodes=64 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        $OPPFLAGS \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$ADECK -Drl.oppDeck=$ODECK -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((100000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > $OUT/.chunk_out.txt 2>&1
    # dense, free curve: the chunk's own win rate against the sampled
    # opponent, labelled with who that was (the 2048-cadence anchor probe
    # is the comparable metric, this is the texture between the points)
    CWR=$(grep -o 'win_rate=[0-9.]*' $OUT/.chunk_out.txt | head -1 | cut -d= -f2)
    echo -e "${trained}\t${ONAME}\t${ODECK}\t${OELO}\t${CWR}\t$(grep -o 'turns_per_ep=[0-9.]*' $OUT/.chunk_out.txt | head -1 | cut -d= -f2)" \
        >> $OUT/chunks.tsv
    [ -n "${CWR:-}" ] && update_self_elo "$CWR" "${OELO:-1000}"
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    [ -n "$OSRV" ] && stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "P10_FAILED|$NAME|no_training_rows (trained stays $trained)"
        exit 1
    fi
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt
    echo "P10|$NAME|trained=$trained|opp=$ONAME|deck=$ODECK"

    if [ $((trained % RATE)) -eq 0 ] || [ "$trained" -ge "$BUDGET" ]; then
        rate_checkpoint $trained
    fi
done
cp $OUT/net.pt $OUT/p10_${NAME}_final.pt
echo "P10_DONE|pilot=$NAME|trained=$(cat $OUT/trained.txt)"
