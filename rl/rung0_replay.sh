#!/bin/bash
# Dump an annotated replay of one game from a rung-0 checkpoint.
#
#   bash rl/rung0_replay.sh <ckpt> <encoderV> <deck> <opponent> <seed> <out>
#
# WHY THIS EXISTS AS A SCRIPT
# The transcripts committed under rl/artifacts were produced by
# hand-assembled driver invocations, and every one of them took a couple
# of tries to get right - the encoder version has to match the checkpoint
# (a v4 net against a v2 server handshakes 32/94 against 32/94 and then
# silently mispredicts, because the CANDIDATE meaning changed, not the
# width), the server has to come up with --max-k 64 for v4, and eval must
# run with no --lr or the "replay" is a training episode.
#
# rl.debug puts one line per decision into the RLGAME block on stdout;
# rl.blockAudit adds the [audit] line comparing what the policy did to
# CombatMath's best assignment for the same position. The audit is read
# AFTER the policy commits, so it annotates the replay without changing it.
set -u
CKPT=${1:?usage: rung0_replay.sh <ckpt> <encV> <deck> <opp> <seed> <out>}
ENC=${2:-4}
DECK=${3:-W0Base}
OPP=${4:-heuristic}
SEED=${5:-6001}
OUT=${6:-/tmp/replay.txt}
RL=/home/user/CardGuru/rl
PORT=${REPLAY_PORT:-7899}

if [ "$ENC" = "1" ]; then SDIM=24; CDIM=91; else SDIM=32; CDIM=94; fi
SRVEXTRA=""
[ "$ENC" -ge 4 ] 2>/dev/null && SRVEXTRA="--max-k 64"

cp $RL/$DECK.dck /home/user/mage/Mage.Tests/

# The driver JVM fixes rl.encoderV at StateEncoder class-init, so one that
# already served another arm cannot serve this one.
pkill -f "[R]LDriverServer" 2>/dev/null
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
sleep 2

RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py \
    --port $PORT --ckpt $CKPT --seed 0 --sdim $SDIM --cdim $CDIM \
    --arch lstmattn --threads 1 $SRVEXTRA > /tmp/replay_server.log 2>&1 &
t=0
while [ $t -lt 90 ]; do
    grep -q "policy server" /tmp/replay_server.log 2>/dev/null && break
    grep -q "Traceback" /tmp/replay_server.log 2>/dev/null && \
        { echo REPLAY_FAILED_SERVER; tail -20 /tmp/replay_server.log; exit 1; }
    sleep 2; t=$((t + 2))
done

cd /home/user/mage
RL_PERSIST=1 RL_AUTOSTART=1 timeout 900 bash $RL/run_driver.sh \
    -Drl.episodes=1 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
    -Drl.consultBudget=4000 -Drl.encoderV=$ENC -Drl.blockAudit=true \
    -Drl.debug=true -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck \
    -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 \
    > /tmp/replay_driver.log 2>&1

sed -n '/^RLGAME|/,/^RLGAME_END/p' /tmp/replay_driver.log > $OUT
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
if [ ! -s "$OUT" ]; then
    echo "REPLAY_EMPTY - driver log tail:"; tail -20 /tmp/replay_driver.log
    exit 1
fi
wc -l < $OUT | xargs echo "REPLAY_DONE lines:"
