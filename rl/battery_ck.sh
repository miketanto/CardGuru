#!/bin/bash
# The rung-0 battery of ONE checkpoint, outside a lane (7d: re-battery of the C1
# checkpoints on the argmax-classes-fixed server; a BC checkpoint; any ck_N.pt).
#   bash rl/battery_ck.sh <ckpt> <out dir> <trained label> [server port=7947] [driver port=7913] [BASE=W0Base] [TWIN=W0Twin]
# Same protocol as rung0_lane.sh's battery(): frozen inference server (no --lr,
# --frozen, --device cuda --logit-bound 5 --argmax-classes = R0_SRVEXTRA of C1),
# D0 = heuristic on BASE, D1 = search on BASE, TWIN = heuristic on TWIN, 100 games
# each, eval flags, seed 900000+trained (the SAME game seeds the lane used, so a
# re-battery is paired with the original). Writes <out>/probe_{D0,D1,TWIN}_<tr>.txt
# and prints one R0| line in the lane's format (Wilson).
[ -f ~/.profile ] && . ~/.profile
set -u
CK=${1:?ckpt}; OUT=${2:?out dir}; TR=${3:?trained label}; PORT=${4:-7947}; DPORT=${5:-7913}
BASE=${6:-W0Base}; TWIN=${7:-W0Twin}; EVAL_G=${EVAL_G:-100}
RL=/home/user/CardGuru/rl
SRVEXTRA=${SRVEXTRA:---device cuda --logit-bound 5 --argmax-classes}
FEATS=$RL/e2_features.tsv
EVALFLAGS="-Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true"
mkdir -p $OUT
export RL_DRIVER_PORT=$DPORT
for D in $BASE $TWIN; do cp $RL/$D.dck /home/user/mage/Mage.Tests/; done
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT --ckpt "$CK" --seed 0 \
    --sdim 32 --cdim 94 --arch v7 --threads 1 --frozen $SRVEXTRA > $OUT/server_$TR.log 2>&1 &
t=0
until grep -q "policy server" $OUT/server_$TR.log 2>/dev/null; do
    sleep 2; t=$((t + 2))
    if [ $t -ge 120 ] || grep -q Traceback $OUT/server_$TR.log 2>/dev/null; then
        echo "BATTERY|FAILED|server|$OUT/server_$TR.log"; tail -3 $OUT/server_$TR.log; exit 1
    fi
done
field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }
band() { python3 -c "
import math
n=float('$1'); p=float('$2' or 0); z=1.96
d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print('[%.3f,%.3f]' % (max(0.0,c-h), min(1.0,c+h)))"; }
line="R0|$BASE|ck=$(basename $CK)|trained=$TR"
for spec in "heuristic|$BASE|D0" "search|$BASE|D1" "heuristic|$TWIN|TWIN"; do
    IFS='|' read -r OPP DK LB <<< "$spec"
    f=$OUT/probe_${LB}_${TR}.txt
    if [ ! -s "$f" ]; then
        RL_PERSIST=1 RL_AUTOSTART=1 timeout 5400 bash $RL/run_driver.sh \
            -Drl.episodes=$EVAL_G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
            -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 \
            $EVALFLAGS -Drl.deck=$DK.dck -Drl.oppDeck=$DK.dck -Drl.stopTurn=60 \
            -Drl.mode=eval -Drl.seed=$((900000 + TR)) -Drl.report=0 -Drl.out=$f > /dev/null 2>&1
    fi
    wr=$(field $f win_rate)
    line="$line|$LB=${wr:-NA} $(band $EVAL_G ${wr:-0})"
done
line="$line|attacks=$(field $OUT/probe_D0_${TR}.txt attacksDeclared)/$(field $OUT/probe_D0_${TR}.txt attackOpportunities)|blocks=$(field $OUT/probe_D0_${TR}.txt blocksDeclared)/$(field $OUT/probe_D0_${TR}.txt blockOpportunities)|turns=$(field $OUT/probe_D0_${TR}.txt turns_per_ep)|budget_hits=$(grep -ho 'attackBudgetHit=[0-9]*' $OUT/probe_*_${TR}.txt | cut -d= -f2 | paste -sd/)"
echo "$line"
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
