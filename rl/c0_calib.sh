#!/bin/bash
# Phase 5 C0: SearchPlayerIP calibration. Scripted-vs-scripted matches
# (no policy server). Protocol matches PHASE4-LADDER: BenchDimir mirror,
# stopTurn 80, fixed eval seed blocks, agent alternates play/draw.
# Usage: bash rl/c0_calib.sh <agentKind> <plies> <breadth> <detK> \
#            <opponent: heuristic|search> <games> <seed> <tag>
# Opponent search is always D1 (1x8). Summary appends to /tmp/rl_p5_c0/.
set -u
AGENT=$1; PLIES=$2; BREADTH=$3; K=$4; OPP=$5; GAMES=$6; SEED=$7; TAG=$8
OUT=/tmp/rl_p5_c0
mkdir -p $OUT
cd /home/user/mage
mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
    -DfailIfNoTests=false -Drl.episodes=$GAMES \
    -Drl.agent=$AGENT -Drl.agentPlies=$PLIES -Drl.agentBreadth=$BREADTH \
    -Drl.agentDetK=$K \
    -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.policy=random -Drl.deck=BenchDimir.dck -Drl.stopTurn=80 \
    -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 \
    -Drl.out=$OUT/c0_${TAG}.txt > /dev/null 2>&1
line=$(tail -1 $OUT/c0_${TAG}.txt 2>/dev/null)
if [ -z "$line" ]; then
    echo "C0_FAILED|tag=$TAG|no_summary_line"
    exit 1
fi
echo "C0|agent=${AGENT}_p${PLIES}x${BREADTH}k${K}|opp=$OPP|tag=$TAG|$line" \
    | tee -a $OUT/c0_log.txt
