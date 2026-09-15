#!/bin/bash
# Phase 14 D2: copy of rl/battery_p12s.sh with the CP7 skill as a parameter (SKILL, default 6); otherwise identical.
# Original header: Phase 12 Amendment 4: the SAMPLED-play counterpart of rl/battery_xdeck.sh (a copy with the play
# mode switched; battery_xdeck.sh is in use by the running controller and is not edited).
# Frozen server (--frozen: samples, stores nothing, no update) + driver -Drl.mode=train
# (sampled as in training, as rl/run_7b0.sh), otherwise battery_xdeck.sh's flags and seeds
# exactly (row i seed 930000 + 1000*i). Ports default 7949 / 7914 (7948 = census proxy).
#   G=100 ROWS="cp7:BenchDimir" bash rl/battery_p12s.sh <ckpt> <agentDeck> <out dir> [port] [dport]
# Prints XDECKS| lines (same fields as XDECK|).
[ -f ~/.profile ] && . ~/.profile
set -u
CK=${1:?ckpt}; ADECK=${2:?agent deck}; OUT=${3:?out dir}; PORT=${4:-7949}; DPORT=${5:-7914}
G=${G:-100}; ROWS=${ROWS:-"cp7:$ADECK"}
RL=/home/user/CardGuru/rl; FEATS=$RL/e2_features.tsv
SRVEXTRA=${SRVEXTRA:---device cuda --logit-bound 5 --argmax-classes}
EVALFLAGS="-Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true"
mkdir -p $OUT; export RL_DRIVER_PORT=$DPORT
cp $RL/$ADECK.dck /home/user/mage/Mage.Tests/ || { echo "XDECKS|FAILED|deck $ADECK"; exit 1; }
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1; : > $OUT/server.log
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT --ckpt "$CK" --seed 0 \
    --sdim 32 --cdim 94 --arch v7 --threads 1 --frozen $SRVEXTRA > $OUT/server.log 2>&1 &
t=0
until grep -q "policy server" $OUT/server.log 2>/dev/null; do
    sleep 2; t=$((t + 2))
    if [ $t -ge 180 ] || grep -q Traceback $OUT/server.log 2>/dev/null; then
        echo "XDECKS|FAILED|server|$OUT/server.log"; tail -3 $OUT/server.log; exit 1
    fi
done
wil() { python3 -c "
import math; k=$1; n=$2; z=1.96; p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print('%d/%d = %.3f [%.3f,%.3f]' % (k, n, p, max(0,c-h), min(1,c+h)))"; }
cd /home/user/mage
i=0
for row in $ROWS; do
    KIND=${row%%:*}; DK=${row##*:}
    f=$OUT/probe_${KIND}_${DK}.txt
    OPPF="-Drl.opponent=$KIND"; [ "$KIND" = cp7 ] && OPPF="$OPPF -Drl.aiSkill=${SKILL:-6}"
    if [ ! -s "$f" ]; then
        RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
            -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT $OPPF \
            -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 $EVALFLAGS \
            -Drl.deck=$ADECK.dck -Drl.oppDeck=$DK.dck -Drl.stopTurn=60 -Drl.mode=train \
            -Drl.seed=$((930000 + 1000 * i)) -Drl.report=0 -Drl.out=$f > $OUT/driver_${KIND}_${DK}.log 2>&1
    fi
    w=$(grep -o 'wins=[0-9]*' $f 2>/dev/null | head -1 | cut -d= -f2); e=$(grep -o 'episodes=[0-9]*' $f 2>/dev/null | head -1 | cut -d= -f2)
    if [ -n "$w" ] && [ -n "$e" ]; then
        echo "XDECKS|ck=$(basename $CK)|agent=$ADECK|vs=$KIND|skill=${SKILL:-6}|oppDeck=$DK|$(wil $w $e)|$(grep -o 'losses=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $f | paste -sd' ')"
    else
        echo "XDECKS|ck=$(basename $CK)|agent=$ADECK|vs=$KIND|skill=${SKILL:-6}|oppDeck=$DK|NA|$(grep -h 'RLJOB|error\|Exception' $OUT/driver_${KIND}_${DK}.log 2>/dev/null | head -1 | cut -c1-120)"
    fi
    i=$((i + 1))
done
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "XDECKS|done|$(basename $CK)|$(date -u +%FT%TZ)"
