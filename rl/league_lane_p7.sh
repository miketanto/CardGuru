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
# ===================== PHASE 10 EXTENSIONS (opt-in) =====================
# Everything below is off unless its flag is set, so P7_PFSP=1 with no
# P10_* flags reproduces the Phase 7b lane exactly.
#
#  P10_POOL=1   DECK-CARRYING POOL SCHEMA. pool_elo.tsv rows become
#               name|kind|deck|elo (the Phase 7c schema) where kind is
#               heuristic | search | searchhold | rl:<arch>:<ckpt>.
#               Scripted rows need no policy server and pilot their own
#               deck via -Drl.oppDeck, so archetype and meta decks sit
#               in the same Elo-rated ladder as the snapshots. Selection
#               moves to rl/pfsp_pick_p7c.py (same optimistic weighting,
#               plus a floor on non-mirror mass so PFSP cannot starve the
#               deck curriculum). Seeded from $P10_POOL_SEED.
#
#  P10_GATE=1   CHAMPION GATING (Phase 7b's #1 recommendation). A
#               snapshot enters pool_elo.tsv ONLY if it beats the
#               reigning champion over $P10_GATE_G games head to head on
#               the mirror; a snapshot that passes also BECOMES the
#               reigning champion. This is the fix for the late drift
#               that cost the 7b line 57 Elo after 6144: an ungated pool
#               lets every snapshot in, so the optimism target chases a
#               population that is itself drifting. The gate is
#               evaluation, so it runs SEQUENTIALLY.
#               $P10_CHAMPION seeds the initial champion (ck_6144).
#
#  P10_DECK_SCHEDULE   AGENT-SIDE DECK ROTATION (Phase 8b's from-init
#               compositional bet). Semicolon-separated stages
#               "<from-episode>:<deck,deck,...>"; the driver plays
#               episode i with decks[i % n], so repeating a deck in the
#               list weights it. Unset = the agent pilots $DECK in every
#               episode, which is exactly the control arm.
#
#  P10_MATRIX_DECKS    robustness matrix (7c): 100g vs D0 piloting each
#               named deck at every rating checkpoint, agent on $DECK.
#
# Usage: bash rl/league_lane_p7.sh <seed> <agentPort> <oppPort> \
#            <initCkpt> [budget=1024]
set -u
SEED=$1; APORT=$2; OPORT=$3; INIT=$4; BUDGET=${5:-1024}
ARCH=lstmattn
LRVAL=${P7_LR:-1e-4}
OUT=${P7_OUT:-/tmp/rl_p7_${ARCH}_s${SEED}}
EXPDIR=${P7_EXPDIR:-/tmp/rl_p7_exploiters}
DECK=BenchDimir.dck
FEATS=/home/user/CardGuru/rl/e2_features.tsv
CDIM=91
RL=/home/user/CardGuru/rl
# Phase 10 knobs
P10_POOL=${P10_POOL:-0}
P10_GATE=${P10_GATE:-0}
P10_GATE_G=${P10_GATE_G:-50}
P10_GATE_THRESH=${P10_GATE_THRESH:-0.5}
P10_POOL_SEED=${P10_POOL_SEED:-$RL/p10_pool_seed.tsv}
P10_CHAMPION=${P10_CHAMPION:-/tmp/rl_p7_lstmattn_s0/p7b_champion.pt}
P10_CHAMPION_NAME=${P10_CHAMPION_NAME:-p7b_ck6144}
P10_CHAMPION_ARCH=${P10_CHAMPION_ARCH:-lstmattn}
P10_CHAMPION_ELO=${P10_CHAMPION_ELO:-1101}
P10_DECK_SCHEDULE=${P10_DECK_SCHEDULE:-}
P10_MATRIX_DECKS=${P10_MATRIX_DECKS:-}
P10_ARCHSHARE=${P10_ARCHSHARE:-0.5}
P7_PROBE_G=${P7_PROBE_G:-100}       # games per Elo-anchor probe
P10_MATRIX_G=${P10_MATRIX_G:-100}   # games per robustness-matrix cell
P10_SAMPLE_DECK=${P10_SAMPLE_DECK-M3RedRush.dck}  # 2nd transcript opponent deck
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

field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

# --------------------------------------------------------------- P10 pool
# The deck-carrying pool is seeded ONCE from a committed file so the
# flagship and its control arm start from an identical population.
seed_pool() {
    [ "$P10_POOL" = "1" ] || return 0
    [ -s $OUT/pool_elo.tsv ] && return 0
    [ -s "$P10_POOL_SEED" ] || { echo "P7_FAILED|no_pool_seed|$P10_POOL_SEED"; exit 1; }
    cp "$P10_POOL_SEED" $OUT/pool_elo.tsv
    echo "P10_POOL_SEEDED|rows=$(grep -vc '^#' $OUT/pool_elo.tsv)|from=$P10_POOL_SEED"
}

# champion state: one row name|arch|ckpt|elo
champion_row() {
    [ -s $OUT/champion.tsv ] || \
        echo "$P10_CHAMPION_NAME|$P10_CHAMPION_ARCH|$P10_CHAMPION|$P10_CHAMPION_ELO" \
            > $OUT/champion.tsv
    cat $OUT/champion.tsv
}

# --------------------------------------------------------- staged knobs
# Schedules are "<from-episode>:<value>[;<from-episode>:<value>...]";
# a value with no ':' in it is a constant. Used for the agent's deck
# rotation and for the archetype share (which has to start low: a
# random-init net learns nothing from 50% of its games against decks it
# cannot yet beat, and the low rungs of the ladder are all mirror rows).
stage_value() {   # $1 trained $2 schedule $3 default
    local trained=$1 sched=$2 out=$3 stage from val
    [ -z "$sched" ] && { echo "$out"; return; }
    case "$sched" in *:*) ;; *) echo "$sched"; return ;; esac
    local IFSBAK=$IFS
    IFS=';'
    for stage in $sched; do
        from=${stage%%:*}; val=${stage#*:}
        [ "$trained" -ge "$from" ] && out=$val
    done
    IFS=$IFSBAK
    echo "$out"
}

agent_decks() { stage_value $1 "$P10_DECK_SCHEDULE" "$DECK"; }

pick_opponent() {  # $1 chunk $2 trained -> "ckpt|arch" | "kind|deck|name|elo"
    local chunk=$1
    if [ "$P10_POOL" = "1" ]; then
        local SELF=$(cat $OUT/self_elo.txt 2>/dev/null || echo 46)
        python3 $RL/pfsp_pick_p7c.py --pool $OUT/pool_elo.tsv \
            --self-elo $SELF --chunk $chunk \
            --archetype-share "$(stage_value ${2:-0} "$P10_ARCHSHARE" 0.5)" \
            --mirror-deck $DECK
        return
    fi
    # Phase 7b (P7_PFSP=1): optimistic Elo-based selection over the
    # whole pool (snapshots + champions + exploiters), targeting
    # opponents ~optimism Elo above the agent's current rating.
    if [ "${P7_PFSP:-0}" = "1" ]; then
        local SELF=$(cat $OUT/self_elo.txt 2>/dev/null || echo 46)
        python3 /home/user/CardGuru/rl/pfsp_pick.py \
            --pool $OUT/pool_elo.tsv --self-elo $SELF --chunk $chunk \
            | cut -d'|' -f1,2
        return
    fi
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
                # candidate encoding is global per JVM: e0/cdim38 nets
                # cannot seat in this cdim91 league
                [ "$EA" = "e0" ] && continue
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

# ------------------------------------------------------- champion gating
# 50g head-to-head, candidate (the frozen snapshot) vs the reigning
# champion, both on the mirror, SEQUENTIAL (this is evaluation: it
# decides pool membership, so it must be reproducible). Score counts a
# draw as half. Promotion rule: score > $P10_GATE_THRESH.
#
# A promoted snapshot enters the pool at the champion's Elo plus the
# margin the h2h itself implies (delta = -400*log10(1/s - 1), capped at
# +-150) - the only rating information the gate actually produces.
gate_snapshot() {   # $1 trained -> 0 promoted, 1 rejected
    local trained=$1 CN CA CC CE line w d g score delta newelo
    IFS='|' read -r CN CA CC CE <<< "$(champion_row)"
    local F=$OUT/gate_${trained}.txt
    if [ ! -s "$F" ]; then
        start_server $OUT/pool/ck_${trained}.pt $ARCH $APORT $OUT/aserver.log
        local ASRV=$(cat $OUT/.srvpid)
        start_server "$CC" "$CA" $OPORT $OUT/oserver.log
        local OSRV=$(cat $OUT/.srvpid)
        RL_PERSIST=${P7_PERSIST:-0} RL_AUTOSTART=1 \
        bash $RL/run_driver.sh \
            -Drl.episodes=$P10_GATE_G \
            -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
            -Drl.opponent=rl -Drl.oppPort=$OPORT \
            -Drl.cardFeatures=$FEATS \
            -Drl.noYields=true -Drl.consultBudget=4000 \
            -Drl.deck=$DECK -Drl.oppDeck=$DECK -Drl.stopTurn=80 \
            -Drl.mode=eval -Drl.seed=952000 -Drl.report=0 \
            -Drl.out=$F > /dev/null 2>&1
        stop_server $ASRV
        stop_server $OSRV
    fi
    line=$(tail -1 $F 2>/dev/null)
    [ -z "$line" ] && { echo "P7_FAILED|gate_${trained} empty"; exit 1; }
    w=$(echo "$line" | grep -o 'wins=[0-9]*' | cut -d= -f2)
    d=$(echo "$line" | grep -o 'draws=[0-9]*' | cut -d= -f2)
    g=$P10_GATE_G
    read -r score delta <<< "$(python3 -c "
import math
w,d,g=$w,$d,$g
s=(w+0.5*d)/g
s2=min(max(s,0.05),0.95)
print('%.4f %.0f' % (s, -400*math.log10(1/s2-1)))")"
    if python3 -c "import sys; sys.exit(0 if $score > $P10_GATE_THRESH else 1)"; then
        newelo=$(python3 -c "print(int($CE + max(-150,min(150,$delta))))")
        grep -q "^ck_${trained}|" $OUT/pool_elo.tsv 2>/dev/null || \
            echo "ck_${trained}|rl:${ARCH}:$OUT/pool/ck_${trained}.pt|$DECK|$newelo" \
                >> $OUT/pool_elo.tsv
        echo "ck_${trained}|$ARCH|$OUT/pool/ck_${trained}.pt|$newelo" > $OUT/champion.tsv
        echo "P10GATE|trained=$trained|champion=$CN|score=$score|wins=$w|draws=$d|games=$g|verdict=PROMOTED|pool_elo=$newelo" \
            | tee -a $OUT/gate_log.txt
        return 0
    fi
    echo "P10GATE|trained=$trained|champion=$CN|score=$score|wins=$w|draws=$d|games=$g|verdict=rejected|pool_elo=-" \
        | tee -a $OUT/gate_log.txt
    return 1
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
        # eval stays SEQUENTIAL (no RL_CONC): Elo probes must remain
        # reproducible; the persistent JVM alone is behavior-identical
        RL_PERSIST=${P7_PERSIST:-0} RL_AUTOSTART=1 \
        bash /home/user/CardGuru/rl/run_driver.sh \
            -Drl.episodes=$P7_PROBE_G \
            -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
            -Drl.opponent=$AK -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS \
            -Drl.noYields=true -Drl.consultBudget=4000 \
            -Drl.deck=$DECK -Drl.oppDeck=$DECK -Drl.stopTurn=80 \
            -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
            -Drl.out=$OUT/probe_${SN}_${trained}.txt > /dev/null 2>&1
        stop_server $ASRV
        line=$(tail -1 $OUT/probe_${SN}_${trained}.txt 2>/dev/null)
        [ -z "$line" ] && { echo "P7_FAILED|probe_${SN}_${trained} empty"; exit 1; }
        w=$(echo "$line" | grep -o 'wins=[0-9]*' | cut -d= -f2)
        d=$(echo "$line" | grep -o 'draws=[0-9]*' | cut -d= -f2)
        echo -e "p7_${trained}\t${SN}\t${w}\t${d}\t$P7_PROBE_G" >> $OUT/elo_matches.tsv
    done
    local ELO=$(python3 /home/user/CardGuru/rl/elo_fit.py \
        --matches $OUT/elo_matches.tsv | grep " p7_${trained} " \
        | awk '{print $2}')
    local d0=$(field $OUT/probe_D0_${trained}.txt win_rate)
    local d1=$(field $OUT/probe_D1_${trained}.txt win_rate)
    local d1h=$(field $OUT/probe_D1h_${trained}.txt win_rate)
    local ft=$(field $OUT/probe_D1_${trained}.txt flashThreats)
    local fto=$(field $OUT/probe_D1_${trained}.txt flashThreatsOppTurn)
    local bd=$(field $OUT/probe_D1_${trained}.txt blocksDeclared)
    local bo=$(field $OUT/probe_D1_${trained}.txt blockOpportunities)
    echo "P7ELO|seed=$SEED|trained=$trained|elo=$ELO|d0=$d0|d1=$d1|d1h=$d1h|blocks=${bd:-0}|blockOpps=${bo:-0}|flashThreats=$ft|oppTurn=$fto" \
        | tee -a $OUT/elo_curve.txt
    [ -n "$ELO" ] && echo "$ELO" > $OUT/self_elo.txt
    # Phase 10: pool entry is the GATE's decision, never the rating's.
    if [ "$P10_GATE" != "1" ] && [ "${P7_PFSP:-0}" = "1" ] && [ -n "$ELO" ]; then
        grep -q "^ck_${trained}|" $OUT/pool_elo.tsv 2>/dev/null || \
            echo "ck_${trained}|$ARCH|$OUT/pool/ck_${trained}.pt|$ELO" \
                >> $OUT/pool_elo.tsv
    fi
}

# 7c robustness matrix: 100g vs D0 piloting each deck, agent on $DECK
rate_matrix() {
    local trained=$1 deck f wr bd bo st name
    [ -z "$P10_MATRIX_DECKS" ] && return 0
    for deck in ${P10_MATRIX_DECKS//,/ }; do
        name=$(basename $deck .dck)
        f=$OUT/matrix_${name}_${trained}.txt
        if [ ! -s "$f" ]; then
            start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
            local ASRV=$(cat $OUT/.srvpid)
            RL_PERSIST=${P7_PERSIST:-0} RL_AUTOSTART=1 \
            bash $RL/run_driver.sh \
                -Drl.episodes=$P10_MATRIX_G \
                -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
                -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
                -Drl.cardFeatures=$FEATS \
                -Drl.noYields=true -Drl.consultBudget=4000 \
                -Drl.deck=$DECK -Drl.oppDeck=$deck -Drl.stopTurn=80 \
                -Drl.mode=eval -Drl.seed=951000 -Drl.report=0 \
                -Drl.out=$f > /dev/null 2>&1
            stop_server $ASRV
        fi
        wr=$(field $f win_rate); bd=$(field $f blocksDeclared)
        bo=$(field $f blockOpportunities); st=$(field $f stalls)
        echo "P10MATRIX|trained=$trained|deck=$name|win_rate=${wr:-NA}|blocks=${bd:-0}|blockOpps=${bo:-0}|stalls=${st:-0}" \
            | tee -a $OUT/matrix.txt
    done
}

# Logged games per checkpoint: one on the mirror vs D1 (the rating
# game) and one vs D0 piloting $P10_SAMPLE_DECK (the matrix game, where
# blocking and opponent-turn casts are actually exercised).
#
# These go through the MVN path deliberately: the persistent driver
# server writes XMage's [LOG][GAME] lines to its own console, not to the
# job's captured stdout, so a transcript taken through the fast path
# comes back with the summary and no game. One episode each, twice per
# 2048, is a price worth paying for a readable transcript.
sample_game() {   # $1 trained $2 tag $3 opponent-kind $4 oppDeck $5 seed
    local trained=$1 tag=$2 f=$OUT/transcript_${2}_${1}.txt
    [ -s "$f" ] && return 0
    start_server $OUT/net.pt $ARCH $APORT $OUT/aserver.log
    local ASRV=$(cat $OUT/.srvpid)
    local XML=/home/user/mage/Mage.Tests/target/surefire-reports/TEST-org.mage.test.benchmark.rl.RLEpisodeDriver.xml
    rm -f $XML
    RL_PERSIST=0 \
    bash $RL/run_driver.sh \
        -Drl.episodes=1 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=$3 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$4 -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$5 -Drl.report=0 \
        -Dxmage.dataCollectors.printGameLogs=true \
        > $OUT/.transcript_mvn.log 2>&1
    stop_server $ASRV
    # surefire captures the forked JVM's stdout into the report rather
    # than relaying it, so the game log has to be read back out of it
    python3 $RL/p10_transcript.py --xml $XML --out $f \
        --header "Phase 10 sample game - trained=$trained, agent $DECK vs $3 piloting $4, seed $5, argmax" \
        || echo "P10_SAMPLE_FAILED|trained=$trained|tag=$tag"
    echo "P10_SAMPLE|trained=$trained|tag=$tag|lines=$(wc -l < $f 2>/dev/null || echo 0)"
}

checkpoint_battery() {
    local trained=$1
    [ -f $OUT/.battery_${trained}.done ] && return 0
    rate_checkpoint $trained
    rate_matrix $trained
    sample_game $trained mirror search $DECK 950000
    [ -n "$P10_SAMPLE_DECK" ] && \
        sample_game $trained "$(basename $P10_SAMPLE_DECK .dck)" heuristic \
            $P10_SAMPLE_DECK 951000
    touch $OUT/.battery_${trained}.done
}

cd /home/user/mage
# a crashed prior run can leave a server bound to our ports (failure
# paths exit without stopping the sibling server) - clear them first
pkill -f "policy_serve[r].py --port $APORT" 2>/dev/null
pkill -f "policy_serve[r].py --port $OPORT" 2>/dev/null
sleep 1
seed_pool
[ "$P10_GATE" = "1" ] && echo "P10_CHAMPION|$(champion_row)"
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)

    # Snapshot / gate / measure the CURRENT net first, then decide
    # whether the budget is spent - so the final checkpoint gets the
    # same battery and the same gate as every other one.
    if [ $((trained % ${P7_SNAP:-${P7_RATE:-256}})) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
    fi
    if [ $((trained % ${P7_RATE:-256})) -eq 0 ]; then
        # rate the starting point too (trained=0 -> baseline Elo)
        checkpoint_battery $trained
    fi
    if [ "$P10_GATE" = "1" ] && [ $((trained % ${P7_SNAP:-256})) -eq 0 ] \
       && [ "$trained" -gt 0 ] && ! grep -q "|trained=$trained|" $OUT/gate_log.txt 2>/dev/null; then
        gate_snapshot $trained || true
    elif [ "$P10_GATE" != "1" ] && [ "${P7_PFSP:-0}" = "1" ] \
         && [ $((trained % ${P7_SNAP:-256})) -eq 0 ] \
         && [ $((trained % ${P7_RATE:-256})) -ne 0 ]; then
        # ungated 7b behaviour: unrated snapshot enters at the current
        # self-Elo estimate so the ladder keeps dense self-rungs
        SELFE=$(cat $OUT/self_elo.txt 2>/dev/null || echo 46)
        grep -q "^ck_${trained}|" $OUT/pool_elo.tsv 2>/dev/null || \
            echo "ck_${trained}|$ARCH|$OUT/pool/ck_${trained}.pt|$SELFE" \
                >> $OUT/pool_elo.tsv
    fi
    [ "$trained" -ge "$BUDGET" ] && break

    CHUNK=$((trained / 64))
    ADECKS=$(agent_decks $trained)
    if [ "$P10_POOL" = "1" ]; then
        IFS='|' read -r OKIND ODECK ONAME OELO <<< "$(pick_opponent $CHUNK $trained)"
    else
        IFS='|' read -r OPPCK OPPARCH <<< "$(pick_opponent $CHUNK $trained)"
        OKIND="rl:${OPPARCH}:${OPPCK}"; ODECK=$DECK; ONAME=$(basename $OPPCK .pt)
    fi

    # Phase 9: P7_CONC>1 runs the chunk's episodes concurrently through
    # the persistent driver JVM (RL_PERSIST); both policy servers must
    # then accept one connection per worker (--threads)
    CONCN=${P7_CONC:-1}
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
        # scripted seat: no server, but it needs its search dials
        OPPFLAGS="-Drl.opponent=$OKIND -Drl.searchPlies=1 -Drl.searchBreadth=8"
    fi
    rows_before=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    RL_PERSIST=${P7_PERSIST:-0} RL_AUTOSTART=1 \
    RL_CONC=$([ "$CONCN" -gt 1 ] && echo $CONCN || echo "") \
    bash /home/user/CardGuru/rl/run_driver.sh \
        -Drl.episodes=64 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        $OPPFLAGS \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$ADECKS -Drl.oppDeck=$ODECK -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((80000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    [ -n "$OSRV" ] && stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "P7_FAILED|s$SEED|no_training_rows (trained stays $trained)"
        exit 1
    fi
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt
    echo "P7|s$SEED|trained=$trained|opp=$ONAME|deck=$ODECK|agentDeck=$ADECKS"
done
cp $OUT/net.pt $OUT/p7_final.pt
echo "P7_DONE|seed=$SEED|trained=$(cat $OUT/trained.txt)"
