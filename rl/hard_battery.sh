#!/bin/bash
# 7d Q2 deciding batteries (V7-VALIDATION "Q2 pre-registration amendment"), for ONE
# checkpoint, outside a lane, fixed argmax-classes protocol, 100 games each:
#   (b) vs CP7      -Drl.opponent=cp7 -Drl.aiSkill=6 -Drl.stopTurn=60
#   (a) head-to-head vs another checkpoint (only when <opp ckpt> is given):
#       -Drl.opponent=rl -Drl.oppPort=<port+1>, the opponent served by a second frozen
#       eval-mode server (argmax over classes); seats alternate by episode parity.
#   bash rl/hard_battery.sh <ckpt> <out dir> <label> [opp ckpt] [server port=7948] [driver port=7914]
# Writes <out>/probe_CP7_<label>.txt, <out>/probe_H2H_<label>.txt and prints one HARD| line
# per battery (wins/episodes with Wilson). Skips a probe whose file exists.
[ -f ~/.profile ] && . ~/.profile
set -u
CK=${1:?ckpt}; OUT=${2:?out}; LB=${3:?label}; OPPCK=${4:-}; PORT=${5:-7948}; DPORT=${6:-7914}
G=${G:-100}; RL=/home/user/CardGuru/rl; FEATS=$RL/e2_features.tsv
EVALFLAGS="-Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true"
SRV="--sdim 32 --cdim 94 --arch v7 --threads 1 --frozen --device cuda --logit-bound 5 --argmax-classes"
mkdir -p $OUT; export RL_DRIVER_PORT=$DPORT
cp $RL/W0Base.dck /home/user/mage/Mage.Tests/
start() {   # $1 port $2 ckpt $3 log
    pkill -f "policy_serve[r].py --port $1" 2>/dev/null; sleep 1; : > $3
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $1 --ckpt "$2" --seed 0 $SRV > $3 2>&1 &
    local t=0
    until grep -q "policy server" $3; do sleep 2; t=$((t+2)); if [ $t -ge 180 ] || grep -q Traceback $3; then echo "HARD|FAILED|server $1"; tail -3 $3; exit 1; fi; done
}
wil() { python3 -c "
import math; k=$1; n=$2; z=1.96; p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print('%d/%d = %.3f [%.3f,%.3f]' % (k, n, p, max(0,c-h), min(1,c+h)))"; }
report() {   # $1 tag $2 file
    local w=$(grep -o 'wins=[0-9]*' $2 | head -1 | cut -d= -f2); local e=$(grep -o 'episodes=[0-9]*' $2 | head -1 | cut -d= -f2)
    echo "HARD|$1|ck=$(basename $CK)|label=$LB|$(wil ${w:-0} ${e:-1})|$(grep -o 'losses=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $2 | paste -sd' ')"
}
start $PORT "$CK" $OUT/server_${LB}.log
cd /home/user/mage
f=$OUT/probe_CP7_${LB}.txt
if [ ! -s $f ]; then
    RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
        -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT -Drl.opponent=cp7 -Drl.aiSkill=6 \
        -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 $EVALFLAGS \
        -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=910000 -Drl.report=0 -Drl.out=$f > $OUT/driver_CP7_${LB}.log 2>&1
fi
report CP7 $f
if [ -n "$OPPCK" ]; then
    OPORT=$((PORT + 1))
    start $OPORT "$OPPCK" $OUT/oppserver_${LB}.log
    f=$OUT/probe_H2H_${LB}.txt
    if [ ! -s $f ]; then
        RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
            -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT -Drl.opponent=rl -Drl.oppPort=$OPORT \
            -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 $EVALFLAGS \
            -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=920000 -Drl.report=0 -Drl.out=$f > $OUT/driver_H2H_${LB}.log 2>&1
    fi
    report H2H $f
    pkill -f "policy_serve[r].py --port $OPORT" 2>/dev/null
fi
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "HARD|done|$LB|$(date -u +%FT%TZ)"
