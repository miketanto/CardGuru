#!/bin/bash
# Phase 15 A4L: the whole transfer ladder, one rung at a time, unattended.
#   bash rl/run_15a4.sh [first_rung_index, default 0]
# Per rung, in order, each step SKIPPED when its output already exists (so a crash
# costs one step, not the night):
#   1. record  rl/run_15rec.sh <deck> 1000 <seed base>     (two driver JVMs, no GPU)
#   2. drivers stopped (rl/driver_server.sh stop 7911/7912) so the GPU steps own the RAM
#   3. gate    rl/gate_15rec.sh <deck> -> the deck's gate.txt; the kinds that PASS are
#              the kinds cloned (13a's own convention), recorded per rung
#   4. clone   rl/v7_bc.py on the rung's recording only  -> bc_<deck>.pt
#   5. joint   rl/v7_bc.py on rung 0 + this rung         -> bcj_<deck>.pt  (skipped for rung 0)
#   6. eval    rl/p15_a4.py with ZERO=bc_W0Base.pt RUNG=bc_<deck>.pt JOINT=bcj_<deck>.pt
# Lines: RUN15A4|... ; artifacts under rl/artifacts/v7/15/{rec,a4}/.
# Never run this while another GPU trainer is up: step 4/5 are GPU trainers.
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
A=$LB/rl/artifacts/v7/15
INIT=$LB/rl/artifacts/v7/13/init_on_s13.pt
mkdir -p $A/a4 $A/rec
cd /home/user/CardGuru

# rung index | deck | aspect cards (comma separated; empty for rung 0)
RUNGS=(
"W0Base|"
"W1Fly|Leonin Skyhunter"
"W1Fst|Head of Security"
"W1Vig|Sun Sentinel"
"W1Lif|Mesa Unicorn"
"W1Ctrl|Shrine Keeper"
"W2FlyLif|Leonin Skyhunter,Mesa Unicorn"
"W2Ctrl|Shrine Keeper,Traveling Philosopher"
"W3Sorc|Take Vengeance"
"W4Inst|Swift Response"
"W5Trick|Aegis of the Heavens"
)
START=${1:-0}
echo "RUN15A4|start=$(date -u +%FT%TZ)|rungs=${#RUNGS[@]}|from=$START"

for i in "${!RUNGS[@]}"; do
    [ "$i" -lt "$START" ] && continue
    IFS='|' read -r DECK ASPECT <<< "${RUNGS[$i]}"
    O=$A/rec/$DECK
    SEED=$((15000 + i * 1000))
    echo "RUN15A4|rung=$i|deck=$DECK|aspect=$ASPECT|seed=$SEED|$(date -u +%FT%TZ)"
    [ -f $A/a4/STOP ] && { echo "RUN15A4|stopfile"; break; }

    # 1. record
    if [ -f $O/DONE ]; then
        echo "RUN15A4|$DECK|record|skip"
    else
        bash $RL/run_15rec.sh $DECK 1000 $SEED 2>&1 | grep -v '^REC15|.*rc=0' | tail -5
    fi
    # 2. drivers down before any GPU step
    for p in 7911 7912; do bash $RL/driver_server.sh stop $p > /dev/null 2>&1; done
    sleep 2

    # 3. gate
    if [ -s $O/gate.txt ] && grep -q '^REC13GATE|' $O/gate.txt; then
        echo "RUN15A4|$DECK|gate|skip"
    else
        bash $RL/gate_15rec.sh $DECK
    fi
    OWN=$(grep '^REC13GATE|' $O/gate.txt 2>/dev/null | grep 'gate=pass' \
          | sed 's/.*kind=\([a-z]*\)|.*/\1/' | paste -sd,)
    echo "RUN15A4|$DECK|gate|own_passing=$OWN"
    # The kind set is FIXED ACROSS RUNGS (decided in PHASE15-ARCH STATE before any rung
    # was cloned): rung 0's passing kinds. A per-rung kind set would clone different
    # decision kinds on different rungs and the rungs would not be comparable. Each
    # rung's OWN gate is still recorded above and goes into its row.
    if [ -z "${KINDS:-}" ]; then
        KINDS=$OWN
        echo "RUN15A4|fixed_kinds=$KINDS|from=$DECK"
    fi
    [ -z "$KINDS" ] && { echo "RUN15A4|$DECK|gate|NO KINDS PASS - rung skipped"; continue; }
    for k in ${KINDS//,/ }; do
        echo "$OWN" | grep -q "$k" || echo "RUN15A4|$DECK|gate|WARN kind $k fails this rung's own gate but is cloned (fixed set)"
    done

    # 4. rung-specific clone
    CK=$A/a4/bc_$DECK.pt
    if [ -s $CK ]; then
        echo "RUN15A4|$DECK|clone|skip"
    else
        python3 $RL/v7_bc.py --init $INIT --out $CK --device cuda --kinds $KINDS \
            $O/rec15_${DECK}_*.jsonl > $A/a4/bc_$DECK.log 2>&1
        echo "RUN15A4|$DECK|clone|rc=$?|$(grep '^BC|saved' $A/a4/bc_$DECK.log | cut -c1-160)"
    fi

    # 5. joint clone (rung 0 + this rung); rung 0 has none
    CJ=$A/a4/bcj_$DECK.pt
    if [ "$i" = 0 ]; then
        echo "RUN15A4|$DECK|joint|n/a"
    elif [ -s $CJ ]; then
        echo "RUN15A4|$DECK|joint|skip"
    elif [ -d $A/rec/W0Base ]; then
        python3 $RL/v7_bc.py --init $INIT --out $CJ --device cuda --kinds $KINDS \
            $A/rec/W0Base/rec15_W0Base_*.jsonl $O/rec15_${DECK}_*.jsonl > $A/a4/bcj_$DECK.log 2>&1
        echo "RUN15A4|$DECK|joint|rc=$?|$(grep '^BC|saved' $A/a4/bcj_$DECK.log | cut -c1-160)"
    fi

    # 6. eval on THIS rung's held-out games
    if [ -s $A/a4/a4_$DECK.json ]; then
        echo "RUN15A4|$DECK|eval|skip"
    else
        CKS="--ckpt ZERO=$A/a4/bc_W0Base.pt --ckpt RUNG=$CK"
        [ -s $CJ ] && CKS="$CKS --ckpt JOINT=$CJ"
        python3 $RL/p15_a4.py --rung $DECK --aspect-cards "$ASPECT" $CKS --out $A/a4 --device cuda \
            $O/rec15_${DECK}_*.jsonl > $A/a4/eval_$DECK.log 2>&1
        echo "RUN15A4|$DECK|eval|rc=$?"
        grep '^A4|.*pop=' $A/a4/eval_$DECK.log | grep -v 'kind=' | sed 's/^/RUN15A4|'"$DECK"'|/'
    fi
    echo "RUN15A4|rung=$i|deck=$DECK|done=$(date -u +%FT%TZ)"
done
echo "RUN15A4|done=$(date -u +%FT%TZ)"
