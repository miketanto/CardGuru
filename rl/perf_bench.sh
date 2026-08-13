#!/bin/bash
# Phase 9 engine-perf benchmark harness — the ENGINE-PERF-KICKOFF contract.
#
# Two fixed workloads, wall-clock for a fixed episode count:
#   a  scripted : rl.agent=search vs heuristic, 100 eps, seed 960000,
#                 BenchDimir.dck, consultBudget 4000        (no Python)
#   b  policy   : rl.agent=rl (attn ckpt over the policy server) vs
#                 heuristic, 100 eps, seed 950000
#
# Usage: bash rl/perf_bench.sh <a|b> <tag> [runner] [extra -D args...]
#   runner: mvn (default) | persist  (persistent driver JVM, PORT via
#           RL_DRIVER_PORT, default 7910)
# Appends one BENCH| row to /tmp/rl_p9/bench_log.txt and writes the
# driver summary line to /tmp/rl_p9/<workload>_<tag>.txt.
set -u
WL=$1; TAG=$2; RUNNER=${3:-mvn}; shift 3 2>/dev/null || shift 2
EXTRA="$*"
OUT=/tmp/rl_p9
mkdir -p $OUT
CG=/home/user/CardGuru
FEATS=$CG/rl/e2_features.tsv
CKPT=${RL_BENCH_CKPT:-/tmp/rl_c6_attn_s0/net.pt}
PORT=${RL_BENCH_PORT:-7891}
DPORT=${RL_DRIVER_PORT:-7910}
RES=$OUT/${WL}_${TAG}.txt
rm -f "$RES"

case $WL in
a)  ARGS="-Drl.episodes=100 -Drl.agent=search -Drl.agentPlies=1
         -Drl.agentBreadth=8 -Drl.opponent=heuristic -Drl.policy=random
         -Drl.deck=BenchDimir.dck -Drl.stopTurn=80 -Drl.mode=eval
         -Drl.seed=960000 -Drl.report=0 -Drl.consultBudget=4000" ;;
b)  ARGS="-Drl.episodes=100 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT
         -Drl.opponent=heuristic -Drl.cardFeatures=$FEATS -Drl.noYields=true
         -Drl.consultBudget=4000 -Drl.deck=BenchDimir.dck -Drl.stopTurn=80
         -Drl.mode=eval -Drl.seed=950000 -Drl.report=0" ;;
*)  echo "BENCH_FAILED|unknown workload $WL"; exit 1 ;;
esac
ARGS="$ARGS -Drl.out=$RES $EXTRA"

SRV=""
if [ "$WL" = "b" ]; then
    python3 $CG/rl/policy_server.py --port $PORT --ckpt "$CKPT" \
        --cdim 91 --arch attn --seed 0 \
        --threads ${RL_BENCH_SRV_THREADS:-1} > $OUT/server_${TAG}.log 2>&1 &
    SRV=$!
    up=0; SECONDS=0
    while [ $SECONDS -lt 120 ]; do
        grep -q "policy server" $OUT/server_${TAG}.log 2>/dev/null && { up=1; break; }
        grep -q "Traceback" $OUT/server_${TAG}.log 2>/dev/null && break
        sleep 1
    done
    if [ "$up" != "1" ]; then
        echo "BENCH_FAILED|$WL|$TAG|server_never_started"
        cat $OUT/server_${TAG}.log; kill $SRV 2>/dev/null; exit 1
    fi
fi

cd /home/user/mage
T0=$(date +%s.%N)
if [ "$RUNNER" = "persist" ]; then
    python3 $CG/rl/driver_client.py --port $DPORT $ARGS > $OUT/run_${WL}_${TAG}.log 2>&1
    RC=$?
else
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DfailIfNoTests=false \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m ${RL_BENCH_JVM:-}" \
        $ARGS > $OUT/run_${WL}_${TAG}.log 2>&1
    RC=$?
fi
T1=$(date +%s.%N)
[ -n "$SRV" ] && { kill $SRV 2>/dev/null; wait $SRV 2>/dev/null; }

WALL=$(echo "$T1 - $T0" | bc)
LINE=$(tail -1 "$RES" 2>/dev/null)
if [ -z "$LINE" ]; then
    echo "BENCH_FAILED|$WL|$TAG|no_summary_line|rc=$RC|wall=${WALL}"
    tail -20 $OUT/run_${WL}_${TAG}.log
    exit 1
fi
EPS=$(echo "$LINE" | grep -o 'episodes=[0-9]*' | cut -d= -f2)
GPS=$(echo "scale=4; $EPS / $WALL" | bc)
MIN=$(echo "scale=2; $WALL / 60" | bc)
echo "BENCH|wl=$WL|tag=$TAG|runner=$RUNNER|wall_sec=${WALL%.*}|minutes=$MIN|games_per_sec_wall=$GPS|$LINE" \
    | tee -a $OUT/bench_log.txt
