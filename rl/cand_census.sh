#!/bin/bash
# The §4 priority-window census, on a TRAINED checkpoint.
#
#   bash rl/cand_census.sh <ckpt> [deck] [games] [seed] [port]
#   bash rl/cand_census.sh /tmp/rl_b1fast/ck_1024.pt B1Fast 100 941001
#
# TIMING-GATE-RESULT.md §4 measured, on a RANDOM policy, that the agent
# reaches an opponent declare-attackers window with anything castable 4
# times in 451 while holding a legal instant in 116 - i.e. it is tapped
# out. A random policy taps out for uninteresting reasons, so that
# census bounds nothing about a trained one. This is the same census
# with the policy in the loop, and it is the measurement that decides
# whether "plays an instant deck at sorcery speed" is an encoding
# finding or a mana finding.
#
# DO NOT RUN THIS WHILE A LANE IS RUNNING. It pkills the driver JVM by
# process name, exactly as rung0_lane.sh does, and the lane is mid-job
# on that JVM.
set -u
RL=/home/user/CardGuru/rl
CKPT=${1:?usage: cand_census.sh <ckpt> [deck] [games] [seed] [port]}
DECK=${2:-B1Fast}
GAMES=${3:-100}
SEED=${4:-941001}
PORT=${5:-7981}
# CAND_MODE=train serves SAMPLED (Gumbel/categorical) instead of argmax.
# The server is still started without --lr, so it samples and does NOT
# learn. This is the exploration-vs-credit probe: if the policy never
# even TRIES the cast under sampling, the failure is exploration; if it
# tries and the behaviour never grows, the failure is credit assignment.
MODE=${CAND_MODE:-eval}
OUT=${CAND_OUT:-/tmp/census_$(basename $CKPT .pt)_${DECK}_${CAND_MODE:-eval}.jsonl}

[ -s "$CKPT" ] || { echo "no such checkpoint: $CKPT"; exit 1; }
if pgrep -f "[R]LDriverServer" > /dev/null; then
    echo "REFUSING: a driver JVM is already up - a lane may be running."
    echo "Kill it deliberately or wait; this script would take it down."
    exit 1
fi

pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
sleep 2
rm -f "$OUT"
cp "$RL/$DECK.dck" /home/user/mage/Mage.Tests/ 2>/dev/null || true

# eval only: no --lr, so the net cannot learn from the census games
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT \
    --ckpt "$CKPT" --seed 0 --sdim 32 --cdim 94 --arch entattn \
    --gdim 16 --edim 48 --emax 96 --max-k 96 --threads 1 \
    > /tmp/census_srv_$PORT.log 2>&1 &
for i in $(seq 1 45); do
    grep -q "policy server" /tmp/census_srv_$PORT.log 2>/dev/null && break
    sleep 2
done
grep -q "policy server" /tmp/census_srv_$PORT.log || {
    echo "server failed"; tail -5 /tmp/census_srv_$PORT.log; exit 1; }

cd /home/user/mage
timeout 5400 bash $RL/run_driver.sh \
    -Drl.episodes=$GAMES -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=heuristic -Drl.cardFeatures=$RL/e2_features.tsv \
    -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=6 -Drl.blockAudit=true -Drl.candDump=$OUT \
    -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck \
    -Drl.stopTurn=60 -Drl.mode=$MODE -Drl.seed=$SEED -Drl.report=0 \
    -Drl.out=/tmp/census_sum_$PORT.txt > /tmp/census_drv_$PORT.log 2>&1

pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
echo "ckpt=$CKPT deck=$DECK games=$GAMES -> $OUT"
grep -o "win_rate=[0-9.]*\|instantCasts=[0-9]*\|instantCastsOppTurn=[0-9]*\|instantCastsInCombat=[0-9]*" \
    /tmp/census_sum_$PORT.txt 2>/dev/null | tr '\n' ' '
echo
python3 $RL/timing_gate.py "$OUT" 2>/dev/null | grep -E "^GATE\|(WINDOWS|A\||AW|S\|)" || true
