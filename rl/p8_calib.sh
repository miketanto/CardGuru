#!/bin/bash
# Phase 8 calibration: scripted D1 (search 1x8) vs D0 (heuristic) on a
# deck mirror. Both seats encoding-blind. PHASE4-LADDER protocol: stopTurn
# 80, fixed seed, agent alternates play/draw.
# Usage: bash rl/p8_calib.sh <deck.dck> <games> <seed> <tag>
set -u
DECK=$1; GAMES=$2; SEED=$3; TAG=$4
OUT=/tmp/rl_p8
mkdir -p $OUT
cd /home/user/mage
mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
    -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
    -DfailIfNoTests=false -Drl.episodes=$GAMES \
    -Drl.agent=search -Drl.agentPlies=1 -Drl.agentBreadth=8 \
    -Drl.opponent=heuristic \
    -Drl.policy=random -Drl.deck=$DECK -Drl.stopTurn=80 \
    -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 \
    -Drl.out=$OUT/calib_${TAG}.txt > /dev/null 2>&1
line=$(tail -1 $OUT/calib_${TAG}.txt 2>/dev/null)
if [ -z "$line" ]; then
    echo "P8_CALIB_FAILED|tag=$TAG|no_summary_line"
    exit 1
fi
echo "P8CALIB|deck=$DECK|tag=$TAG|$line" | tee -a $OUT/calib_log.txt
