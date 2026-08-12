#!/bin/bash
# Phase 5 C5: CLEAN self-play league. No shaping, no BC init, no yield
# rules, no teacher - scratch terminal-PPO, both seats policy-driven.
# The opponent seat is a frozen snapshot from the pool of the agent's
# own past checkpoints (deterministic rotation), refreshed per chunk;
# a new snapshot joins the pool every 256 episodes. D0/D1 serve as
# external PROBES only (100g rolling evals), never as teachers.
# Usage: bash rl/league_lane.sh <seed> <agentPort> <oppPort> [budget=2560]
set -u
SEED=$1; APORT=$2; OPORT=$3; BUDGET=${4:-2560}
OUT=/tmp/rl_league_s${SEED}
DECK=BenchDimir.dck
mkdir -p $OUT/pool

start_server() {  # $1 ckpt path, $2 port, $3 logfile -> pid in $OUT/.srvpid
    # runs in the PARENT shell so exit 1 really aborts the lane (a
    # command-substitution version swallowed failures), and retries the
    # bind: a just-killed server's socket can linger briefly
    local try
    for try in 1 2 3; do
        rm -f $3
        python3 /home/user/CardGuru/rl/policy_server.py --port $2 \
            --ckpt "$1" --seed $SEED --log $OUT/train.csv \
            > $3 2>&1 &
        echo $! > $OUT/.srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 60 ]; do
            grep -q "policy server" $3 2>/dev/null && { up=1; break; }
            grep -q "Traceback" $3 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat $OUT/.srvpid) 2>/dev/null
        wait $(cat $OUT/.srvpid) 2>/dev/null
        grep -q "Address already in use" $3 2>/dev/null || break
    done
    echo "LEAGUE_FAILED|s$SEED|server_never_started|$3"
    cat $3
    exit 1
}

stop_server() {  # $1 pid
    kill $1 2>/dev/null
    wait $1 2>/dev/null
}

cd /home/user/mage
while true; do
    trained=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    [ "$trained" -ge "$BUDGET" ] && break

    # snapshot into the pool every 256 episodes (and at 0: random init)
    if [ $((trained % 256)) -eq 0 ] && [ ! -f $OUT/pool/ck_${trained}.pt ]; then
        if [ -f $OUT/net.pt ]; then
            cp $OUT/net.pt $OUT/pool/ck_${trained}.pt
        fi
    fi
    # opponent: deterministic rotation over the pool; empty pool =
    # nonexistent path = random-init opponent (bootstrap)
    mapfile -t POOLCKS < <(ls $OUT/pool/*.pt 2>/dev/null | sort -V)
    NPOOL=${#POOLCKS[@]}
    if [ "$NPOOL" -gt 0 ]; then
        OPPCK=${POOLCKS[$(( (trained / 64) % NPOOL ))]}
    else
        OPPCK=$OUT/pool/bootstrap_absent.pt
    fi

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
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.stopTurn=80 \
        -Drl.mode=train -Drl.seed=$((50000000 + SEED*1000000 + trained)) \
        -Drl.report=0 > /dev/null 2>&1
    rows_after=$(wc -l < $OUT/train.csv 2>/dev/null || echo 0)
    stop_server $ASRV
    stop_server $OSRV
    if [ "$rows_after" -le "$rows_before" ]; then
        echo "LEAGUE_FAILED|s$SEED|no_training_rows (trained stays $trained)"
        exit 1
    fi
    trained=$((trained + 64))
    echo $trained > $OUT/trained.txt

    # external probes every 512 episodes (and at the end)
    if [ $((trained % 256)) -eq 0 ] || [ "$trained" -ge "$BUDGET" ]; then
        for PROBE in heuristic search; do
            start_server $OUT/net.pt $APORT $OUT/aserver.log
            ASRV=$(cat $OUT/.srvpid)
            mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
                -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
                -DfailIfNoTests=false -Drl.episodes=100 \
                -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
                -Drl.opponent=$PROBE -Drl.searchPlies=1 -Drl.searchBreadth=8 \
                -Drl.noYields=true -Drl.consultBudget=4000 \
                -Drl.deck=$DECK -Drl.stopTurn=80 \
                -Drl.mode=eval -Drl.seed=950000 -Drl.report=0 \
                -Drl.out=$OUT/probe_${PROBE}_${trained}.txt > /dev/null 2>&1
            stop_server $ASRV
            line=$(tail -1 $OUT/probe_${PROBE}_${trained}.txt 2>/dev/null)
            wr=$(echo "$line" | grep -o 'win_rate=[0-9.]*' | head -1 | cut -d= -f2)
            stalls=$(echo "$line" | grep -o 'stalls=[0-9]*' | cut -d= -f2)
            echo "LEAGUE|seed=$SEED|trained=$trained|probe=$PROBE|win_rate=$wr|stalls=$stalls" \
                | tee -a $OUT/curve.txt
        done
    fi
done
echo "LEAGUE_DONE|seed=$SEED|trained=$(cat $OUT/trained.txt)"
