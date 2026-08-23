#!/bin/bash
# Measure the critic's EXPLAINED VARIANCE on a short training arm.
#
#   bash rl/ev_probe.sh <ckpt> [deck] [episodes] [port]
#
# Why this number and not a win rate. CardGuru trains with terminal-only
# reward and GAE(lambda=0.95), so for every NON-terminal consult the TD
# residual is exactly gamma*V(s') - V(s): the whole dense credit path IS
# the critic. EV = 1 - Var(ret - V)/Var(ret) says how much of the return
# that path actually explains. At EV ~ 0 the agent is doing policy
# gradient on noise, and every lever downstream of the advantage -
# shaping included, which PHASE5-VERDICT already found null - is
# operating on a signal that was never there.
#
# Suphx (global reward prediction, oracle guiding) and AlphaStar
# (opponent-conditioned value) are both interventions on this quantity.
# Measure it before building either.
#
# Runs on a COPY of the checkpoint: this trains, and must not touch a
# checkpoint whose numbers are already published.
set -u
RL=/home/user/CardGuru/rl
CKPT=${1:?usage: ev_probe.sh <ckpt> [deck] [episodes] [port]}
DECK=${2:-B1Fast}
EPS=${3:-128}
PORT=${4:-7991}
# EV_ORACLE=1 runs the asymmetric-critic arm: the driver emits the
# opponent's hand under "oe" and the server scores GAE with a separate
# privileged critic. Everything else is held identical.
ORACLE=${EV_ORACLE:-0}
SRV_ORACLE=""; DRV_ORACLE=""
if [ "$ORACLE" = "1" ]; then
    SRV_ORACLE="--oracle"; DRV_ORACLE="-Drl.oracle=true"
fi
OUT=${EV_OUT:-/tmp/rl_ev_$(basename $CKPT .pt)_${DECK}_or${EV_ORACLE:-0}}

[ -s "$CKPT" ] || { echo "no such checkpoint: $CKPT"; exit 1; }
if pgrep -f "[R]LDriverServer" > /dev/null; then
    echo "REFUSING: a driver JVM is already up - a lane may be running."; exit 1
fi

pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
sleep 2
rm -rf "$OUT"; mkdir -p "$OUT"
cp "$CKPT" "$OUT/agent.pt"
cp "$RL/$DECK.dck" /home/user/mage/Mage.Tests/ 2>/dev/null || true

RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT \
    --ckpt "$OUT/agent.pt" --seed 0 --sdim 32 --cdim 94 --arch entattn \
    --gdim 16 --edim 48 --emax 96 --max-k 96 --threads 2 \
    --lr 3e-4 $SRV_ORACLE --log "$OUT/train.csv" > "$OUT/server.log" 2>&1 &
for i in $(seq 1 45); do
    grep -q "policy server" "$OUT/server.log" 2>/dev/null && break; sleep 2
done
grep -q "policy server" "$OUT/server.log" || {
    echo "server failed"; tail -5 "$OUT/server.log"; exit 1; }

cd /home/user/mage
RL_PERSIST=1 RL_AUTOSTART=1 RL_CONC=2 timeout 5400 bash $RL/run_driver.sh \
    -Drl.episodes=$EPS -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=heuristic -Drl.cardFeatures=$RL/e2_features.tsv \
    -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=6 $DRV_ORACLE -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck \
    -Drl.stopTurn=60 -Drl.mode=train -Drl.seed=$((77000000 + RANDOM)) \
    -Drl.report=0 -Drl.out="$OUT/sum.txt" > "$OUT/drv.log" 2>&1

pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
echo "ckpt=$CKPT deck=$DECK episodes=$EPS -> $OUT"
echo "update,episodes,steps,batch_wr,value_ev  (oracle=$ORACLE)"
awk -F, '{printf "%s,%s,%s,%s,%s\n",$2,$3,$4,$5,$6}' "$OUT/train.csv" 2>/dev/null
