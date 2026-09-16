#!/bin/bash
# Phase 15 A4L: the 13a labelled-fraction gate on one ladder deck's recording.
#   bash rl/gate_15rec.sh <deck>
# Runs rl/rec13_summary.py (unchanged: the REC13GATE view reads each job's own
# teacher counters out of <tag>.probe.txt, which rl/record_15.sh writes beside
# the jsonl) over every rec15_<deck>_*.jsonl and writes the deck's gate.txt.
# Prints one REC15GATE|<deck>|kinds=... line; exit 0 = every recorded kind
# passes (>= 0.9 labelled), exit 1 = at least one kind FAILs.
# Idempotent: rerunning only rewrites gate.txt.
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
DECK=${1:?deck}
OUT=$LB/rl/artifacts/v7/15/rec/$DECK
ls $OUT/rec15_${DECK}_*.jsonl > /dev/null 2>&1 || { echo "REC15GATE|$DECK|no recordings"; exit 2; }
cd /home/user/CardGuru
python3 $RL/rec13_summary.py $OUT/rec15_${DECK}_*.jsonl > $OUT/gate.txt 2>&1
PASS=$(grep -c 'REC13GATE|.*gate=pass' $OUT/gate.txt)
FAIL=$(grep -c 'REC13GATE|.*gate=FAIL' $OUT/gate.txt)
KINDS=$(grep '^REC13GATE|' $OUT/gate.txt | sed 's/^REC13GATE|//' | paste -sd' ')
GAMES=$(cat $OUT/rec15_${DECK}_*.jsonl 2>/dev/null | grep -c '"t":"end"')
echo "REC15GATE|$DECK|games=$GAMES|pass=$PASS|fail=$FAIL|$KINDS"
[ "$FAIL" = 0 ]
