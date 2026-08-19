#!/bin/bash
# Read the ATTACK AUDIT off a checkpoint, over N games, sequentially.
#
#   bash rl/attack_audit.sh <ckpt> <encoderV> <deck> <opponent> <games> <seed> <out>
#
# WHY THIS EXISTS AS A SCRIPT, not a hand-assembled driver invocation.
# The same three things go wrong every time (rung0_replay.sh's header
# lists them for replays and they apply here): the encoder version has to
# match the checkpoint or the handshake succeeds and the CANDIDATE
# MEANING silently differs; the server needs a raised --max-k for the
# joint arms; and eval must start the server with no --lr or the
# "measurement" is a training run that changes the thing it measures.
#
# SEQUENTIAL ON PURPOSE. RL_CONC is left unset, per the standing rule
# that every reported number is sequential.
#
# The audit is READ-ONLY with respect to the policy: auditAttacks runs
# after selectAttackers has committed, so a run with -Drl.attackAudit=true
# plays exactly the games it plays without it. It costs wall-clock (a
# second minimax search per combat, reported as attackAuditMs) and
# nothing else.
set -u
CKPT=${1:?usage: attack_audit.sh <ckpt> <encV> <deck> <opp> <games> <seed> <out>}
ENC=${2:-4}
DECK=${3:-W0Base}
OPP=${4:-heuristic}
GAMES=${5:-100}
SEED=${6:-900512}
OUT=${7:-/tmp/attack_audit_v${ENC}.txt}
RL=/home/user/CardGuru/rl
PORT=${AUDIT_PORT:-7897}

if [ "$ENC" = "1" ]; then SDIM=24; CDIM=91; else SDIM=32; CDIM=94; fi
SRVEXTRA=""
[ "$ENC" -ge 4 ] 2>/dev/null && SRVEXTRA="--max-k 64"
# v5's candidates are attack SUBSETS: rl.attackMaxCands defaults to 64,
# so the buffer has to clear it or the server drops candidates the policy
# was supposed to choose between.
[ "$ENC" -ge 5 ] 2>/dev/null && SRVEXTRA="--max-k 96"

cp $RL/$DECK.dck /home/user/mage/Mage.Tests/

# ATTACK_AUDIT=false turns the instrument off while leaving everything
# else identical. That is the only way to measure what the POLICY's own
# minimax search costs on a v5 arm: with the audit on, the audit's search
# is 76% of wall clock and swamps it.
#
# AUDIT_EXTRA passes further -D flags through, e.g.
#   AUDIT_EXTRA=-Drl.legacyTieBreak=true
# to read the same games under the pre-fix combat damage tie-break.
#
# rl.encoderV is fixed at StateEncoder class-init, and rl.legacyTieBreak
# is fixed at CombatMath class-init the same way, so a driver JVM that
# has served another arm cannot serve this one. Killing it here is not
# optional - the previous arm's value would silently survive.
pkill -f "[R]LDriverServer" 2>/dev/null
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
sleep 2

RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py \
    --port $PORT --ckpt $CKPT --seed 0 --sdim $SDIM --cdim $CDIM \
    --arch lstmattn --threads 1 $SRVEXTRA > /tmp/audit_server.log 2>&1 &
t=0
while [ $t -lt 90 ]; do
    grep -q "policy server" /tmp/audit_server.log 2>/dev/null && break
    grep -q "Traceback" /tmp/audit_server.log 2>/dev/null && \
        { echo AUDIT_FAILED_SERVER; tail -20 /tmp/audit_server.log; exit 1; }
    sleep 2; t=$((t + 2))
done

cd /home/user/mage
RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
    -Drl.episodes=$GAMES -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
    -Drl.consultBudget=4000 -Drl.encoderV=$ENC \
    -Drl.blockAudit=true -Drl.attackAudit=${ATTACK_AUDIT:-true} ${AUDIT_EXTRA:-} \
    -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck -Drl.stopTurn=60 \
    -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 -Drl.out=$OUT \
    > /tmp/audit_driver.log 2>&1

pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
if [ ! -s "$OUT" ]; then
    echo "AUDIT_EMPTY - driver log tail:"; tail -20 /tmp/audit_driver.log; exit 1
fi
python3 $RL/attack_audit_report.py "$OUT" --label "v$ENC vs $OPP on $DECK"
