#!/bin/bash
# Phase 7c: separate DECK power from PILOT skill.
#
# Every archetype row in the curriculum is piloted by D0, and D0's
# competence is deck-dependent - it was validated on BenchDimir and has
# no reason to pilot draw-go control well. So a low agent win rate
# against archetype X is ambiguous: X may be strong, or D0 may simply
# play X badly. Two scripted-only measurements separate the two.
#
#   A) deck power, pilot fixed: D0(X) vs D0(BenchDimir)
#      Both seats equally competent, so the gap is the DECK. ~.50 means
#      X is a fair fight against the agent's deck under equal piloting.
#
#   B) skill headroom:         D1(X) vs D0(X)
#      Same deck both seats, so the gap is the PILOT. Reference: on
#      BenchDimir D1 beats D0 at .614 over 500g (PHASE5-V3/C4). A much
#      larger gap means D0 is leaving unusual value on the table with X.
#
# Both are scripted-vs-scripted: no policy server, no torch, so this can
# run alongside the training lane without contending for the agent port.
#
# Usage: bash rl/p7c_pilot_calib.sh [games=100]
set -u
G=${1:-100}
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_p7c_pilot
MIRROR=BenchDimir.dck
mkdir -p $OUT

DECKS=(
  "dimir|BenchDimir.dck"
  "sweep|P7cSweepControl.dck"
  "tokens|M3SelesnyaTokens.dck"
  "wweenie|M3WhiteWeenie.dck"
  "skies|M3BlueSkies.dck"
  "redrush|M3RedRush.dck"
  "ramp|M3GreenRamp.dck"
)

run() {  # $1 out $2 agentKind $3 agentDeck $4 oppDeck $5 seed
    [ -s "$1" ] && return 0
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx3000m" \
        -DfailIfNoTests=false -Drl.episodes=$G \
        -Drl.agent=$2 -Drl.policy=random \
        -Drl.opponent=heuristic \
        -Drl.agentPlies=1 -Drl.agentBreadth=8 \
        -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$3 -Drl.oppDeck=$4 -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$5 -Drl.report=0 \
        -Drl.out=$1 > /dev/null 2>&1
}

wr() { grep -o 'win_rate=[0-9.]*' "$1" 2>/dev/null | head -1 | cut -d= -f2; }
st() { grep -o 'stalls=[0-9]*' "$1" 2>/dev/null | head -1 | cut -d= -f2; }

cd /home/user/mage
echo "=== A: deck power, pilot fixed at D0 (X vs BenchDimir, ${G}g) ==="
for D in "${DECKS[@]}"; do
    IFS='|' read -r NAME DCK <<< "$D"
    F=$OUT/power_${NAME}.txt
    run $F heuristic $DCK $MIRROR 953000
    echo "PILOT_POWER|deck=$NAME|d0_${NAME}_vs_d0_dimir=$(wr $F)|stalls=$(st $F)"
done

echo "=== B: skill headroom, D1(X) vs D0(X) same deck, ${G}g ==="
for D in "${DECKS[@]}"; do
    IFS='|' read -r NAME DCK <<< "$D"
    F=$OUT/skill_${NAME}.txt
    run $F search $DCK $DCK 954000
    echo "PILOT_SKILL|deck=$NAME|d1_over_d0=$(wr $F)|stalls=$(st $F)"
done
echo "PILOT_CALIB_DONE"
