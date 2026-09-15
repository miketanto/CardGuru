#!/bin/bash
# Phase 14 D2: copy of rl/battery_xdeck.sh with the CP7 skill as a parameter (SKILL, default 6); otherwise identical.
# Original header: Phase 8 A3: the CROSS-DECK SUITE of one checkpoint, outside a lane, under the fixed
# argmax-classes protocol: four rows (amended from six) of G games (default 100), the agent on <agentDeck>
# in every row, the opponent on W0Base / BenchDimir / BenchBurn, first the heuristic
# then CP7 on the agent's own deck (-Drl.opponent=cp7 -Drl.aiSkill=6, rl.stopTurn 60; stalls reported).
#   bash rl/battery_xdeck.sh <ckpt> <agentDeck> <out dir> [server port=7947] [driver port=7913]
# Env: G (games per row; the smoke uses 4), ROWS ("kind:deck ..." subset, default all six),
#      SRVEXTRA (server flags; default = C1's eval server: --device cuda --logit-bound 5 --argmax-classes).
# One frozen inference server + one driver JVM, rows one after the other (memory rule:
# never beside a second suite). A row whose probe file exists is skipped (resumable).
# Writes <out>/probe_<kind>_<deck>.txt, prints one XDECK| line per row (wins/games with
# Wilson, losses/draws/stalls, turns) and XDECK|pooled over the six rows.
[ -f ~/.profile ] && . ~/.profile
set -u
CK=${1:?ckpt}; ADECK=${2:?agent deck}; OUT=${3:?out dir}; PORT=${4:-7947}; DPORT=${5:-7913}
G=${G:-100}; ROWS=${ROWS:-"heuristic:W0Base heuristic:BenchDimir heuristic:BenchBurn cp7:$ADECK"}   # Phase 8 amendment: four rows, CP7 on the home deck only
RL=/home/user/CardGuru/rl; FEATS=$RL/e2_features.tsv
SRVEXTRA=${SRVEXTRA:---device cuda --logit-bound 5 --argmax-classes}
EVALFLAGS="-Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true"
mkdir -p $OUT; export RL_DRIVER_PORT=$DPORT
for D in $ADECK W0Base BenchDimir BenchBurn; do cp $RL/$D.dck /home/user/mage/Mage.Tests/ || { echo "XDECK|FAILED|deck $D"; exit 1; }; done
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1; : > $OUT/server.log
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT --ckpt "$CK" --seed 0 \
    --sdim 32 --cdim 94 --arch v7 --threads 1 --frozen $SRVEXTRA > $OUT/server.log 2>&1 &
t=0
until grep -q "policy server" $OUT/server.log 2>/dev/null; do
    sleep 2; t=$((t + 2))
    if [ $t -ge 180 ] || grep -q Traceback $OUT/server.log 2>/dev/null; then
        echo "XDECK|FAILED|server|$OUT/server.log"; tail -3 $OUT/server.log; exit 1
    fi
done
wil() { python3 -c "
import math; k=$1; n=$2; z=1.96; p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print('%d/%d = %.3f [%.3f,%.3f]' % (k, n, p, max(0,c-h), min(1,c+h)))"; }
cd /home/user/mage
i=0; TW=0; TG=0
for row in $ROWS; do
    KIND=${row%%:*}; DK=${row##*:}
    f=$OUT/probe_${KIND}_${DK}.txt
    OPPF="-Drl.opponent=$KIND"; [ "$KIND" = cp7 ] && OPPF="$OPPF -Drl.aiSkill=${SKILL:-6}"
    if [ ! -s "$f" ]; then
        RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
            -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT $OPPF \
            -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 $EVALFLAGS \
            -Drl.deck=$ADECK.dck -Drl.oppDeck=$DK.dck -Drl.stopTurn=60 -Drl.mode=eval \
            -Drl.seed=$((930000 + 1000 * i)) -Drl.report=0 -Drl.out=$f > $OUT/driver_${KIND}_${DK}.log 2>&1
    fi
    w=$(grep -o 'wins=[0-9]*' $f 2>/dev/null | head -1 | cut -d= -f2); e=$(grep -o 'episodes=[0-9]*' $f 2>/dev/null | head -1 | cut -d= -f2)
    if [ -n "$w" ] && [ -n "$e" ]; then
        TW=$((TW + w)); TG=$((TG + e))
        echo "XDECK|ck=$(basename $CK)|agent=$ADECK|vs=$KIND|skill=${SKILL:-6}|oppDeck=$DK|$(wil $w $e)|$(grep -o 'losses=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*\|attackBudgetHit=[0-9]*' $f | paste -sd' ')"
    else
        echo "XDECK|ck=$(basename $CK)|agent=$ADECK|vs=$KIND|skill=${SKILL:-6}|oppDeck=$DK|NA|$(grep -h 'RLJOB|error\|Exception' $OUT/driver_${KIND}_${DK}.log 2>/dev/null | head -1 | cut -c1-120)"
    fi
    i=$((i + 1))
done
[ $TG -gt 0 ] && echo "XDECK|pooled|ck=$(basename $CK)|agent=$ADECK|rows=$i|$(wil $TW $TG)"
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "XDECK|done|$(basename $CK)|$(date -u +%FT%TZ)"
