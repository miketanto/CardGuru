#!/bin/bash
# Phase 12: find the conc4 bottleneck.
#
# Removing 35% of game-thread work bought 1.28x sequential but only
# 1.05x at conc4, so something other than engine CPU is the constraint
# when 4 workers run. JFR cannot see it: ExecutionSample only samples
# ON-CPU threads, so time blocked on the policy-server socket is
# invisible (which is why "IPC = 2%" is misleading - that is 2% of CPU,
# not 2% of wall clock).
#
# Three candidates, and a scaling curve separates them:
#   1. policy server serialization (one lock guards inference + buffers)
#   2. CPU oversubscription (4 game threads + torch's own threads on 4 cores)
#   3. the engine simply not scaling on this box
#
# Probe: measure games/sec at conc 1/2/4 for a workload WITH the policy
# server and one WITHOUT it (scripted). If the scripted workload scales
# and the policy one does not, the policy path is the bottleneck; if
# neither scales, it is the box.
#
# Usage: bash rl/p12_bottleneck_probe.sh [episodes=20] [torch_threads=2]
set -u
EPS=${1:-20}
TORCH_THREADS=${2:-2}
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_p12
PORT=7891
mkdir -p $OUT

start_srv() {
    bash $RL/driver_server.sh stop 7910 > /dev/null 2>&1
    cd /home/user/mage
    bash $RL/driver_server.sh start 7910 \
        "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.manaNoRecopy=on" \
        > /dev/null 2>&1
}

policy_run() {   # $1 conc
    local conc=$1 flag=""
    [ "$conc" -gt 1 ] && flag="$conc"
    RL_PERSIST=1 RL_CONC=$flag bash $RL/run_driver.sh \
        -Drl.episodes=$EPS -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
        -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
        -Drl.consultBudget=4000 -Drl.deck=BenchDimir.dck \
        -Drl.oppDeck=BenchDimir.dck -Drl.stopTurn=80 -Drl.mode=eval \
        -Drl.seed=950000 -Drl.report=0 2>&1 | grep -o "games_per_sec=[0-9.]*" | cut -d= -f2
}

scripted_run() {  # $1 conc - no policy server in the loop at all
    local conc=$1 flag=""
    [ "$conc" -gt 1 ] && flag="$conc"
    RL_PERSIST=1 RL_CONC=$flag bash $RL/run_driver.sh \
        -Drl.episodes=$EPS -Drl.agent=search -Drl.policy=random \
        -Drl.agentPlies=1 -Drl.agentBreadth=8 \
        -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
        -Drl.consultBudget=4000 -Drl.deck=BenchDimir.dck \
        -Drl.oppDeck=BenchDimir.dck -Drl.stopTurn=80 -Drl.mode=eval \
        -Drl.seed=960000 -Drl.report=0 2>&1 | grep -o "games_per_sec=[0-9.]*" | cut -d= -f2
}

pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
sleep 1
TORCH_NUM_THREADS=$TORCH_THREADS python3 $RL/policy_server.py --port $PORT \
    --ckpt /tmp/rl_p10_flagship_s0/p10_final.pt --seed 0 --cdim 91 \
    --arch lstmattn --threads 4 > $OUT/probe_server.log 2>&1 &
sleep 12
start_srv

echo "P12PROBE|episodes=$EPS|torch_threads=$TORCH_THREADS"
for C in 1 2 4; do
    scripted_run $C > /dev/null 2>&1          # warm
    S=$(scripted_run $C)
    policy_run $C > /dev/null 2>&1            # warm
    P=$(policy_run $C)
    echo "P12PROBE|conc=$C|scripted_gps=$S|policy_gps=$P"
done
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
echo "P12PROBE_DONE"
