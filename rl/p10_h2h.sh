#!/bin/bash
# Phase 10 B2 cross matrix: head-to-head of two checkpoints, EACH ON ITS OWN DECK
# (rl/hard_battery.sh's H2H with the decks as arguments; hard_battery hardcodes W0Base).
# Fixed argmax-classes protocol: two frozen eval servers (--argmax-classes, bound 5),
# -Drl.opponent=rl -Drl.oppPort=<port+1>; seats alternate by episode parity (engine).
#   bash rl/p10_h2h.sh <ckA> <deckA> <ckB> <deckB> <out dir> <label> [port=7948] [driver=7914]
# Env G (default 50). Writes <out>/probe_H2H_<label>.txt, prints one HARD| line (A's wins, Wilson).
[ -f ~/.profile ] && . ~/.profile
CK=${1:?ckA}; DA=${2:?deckA}; OPPCK=${3:?ckB}; DB=${4:?deckB}; OUT=${5:?out}; LB=${6:?label}; PORT=${7:-7948}; DPORT=${8:-7914}
G=${G:-50}; RL=/home/user/CardGuru/rl; FEATS=$RL/e2_features.tsv
EVALFLAGS="-Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true"
SRV="--sdim 32 --cdim 94 --arch v7 --threads 1 --frozen --device cuda --logit-bound 5 --argmax-classes"
mkdir -p $OUT; export RL_DRIVER_PORT=$DPORT
cp $RL/$DA.dck $RL/$DB.dck /home/user/mage/Mage.Tests/
start() {   # $1 port $2 ckpt $3 log
    pkill -f "policy_serve[r].py --port $1" 2>/dev/null; sleep 1; : > $3
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $1 --ckpt "$2" --seed 0 $SRV > $3 2>&1 &
    local t=0
    until grep -q "policy server" $3; do sleep 2; t=$((t+2)); if [ $t -ge 180 ] || grep -q Traceback $3; then echo "HARD|FAILED|server $1"; tail -3 $3; exit 1; fi; done
}
wil() { python3 -c "
import math; k=$1; n=$2; z=1.96; p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print('%d/%d = %.3f [%.3f,%.3f]' % (k, n, p, max(0,c-h), min(1,c+h)))"; }
f=$OUT/probe_H2H_${LB}.txt
if [ ! -s $f ]; then
    start $PORT "$CK" $OUT/server_${LB}.log
    start $((PORT + 1)) "$OPPCK" $OUT/oppserver_${LB}.log
    cd /home/user/mage
    RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
        -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT -Drl.opponent=rl -Drl.oppPort=$((PORT + 1)) \
        -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 $EVALFLAGS \
        -Drl.deck=$DA.dck -Drl.oppDeck=$DB.dck -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=930000 -Drl.report=0 -Drl.out=$f > $OUT/driver_H2H_${LB}.log 2>&1
    pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
    pkill -f "policy_serve[r].py --port $((PORT + 1))" 2>/dev/null
fi
w=$(grep -o 'wins=[0-9]*' $f | head -1 | cut -d= -f2); e=$(grep -o 'episodes=[0-9]*' $f | head -1 | cut -d= -f2)
echo "HARD|H2H|A=$(basename $CK):$DA|B=$(basename $OPPCK):$DB|label=$LB|$(wil ${w:-0} ${e:-1})|$(grep -o 'losses=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $f | paste -sd' ')"
