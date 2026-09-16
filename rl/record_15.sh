#!/bin/bash
# Phase 15 A4L: one recording job of the CP7 teacher seat on ANY deck of the
# curriculum ladder (rl/PHASE15-ARCH.md A4L).  Identical to rl/record_13a.sh
# (rl.agent=cp7, CP7TeacherPlayer, rl.aiSkill 6, labels on priority / target /
# joint attack / joint block, through the echo server) except that the DECK is
# an argument and the output lands per deck.
#   bash rl/record_15.sh <deck> <tag> <echo port> <episodes> <seed> <driver port> <heuristic|cp7>
# Seats alternate by episode parity. Concurrency 1 per driver so games do not
# interleave in the file ({"t":"end"} segments games).
# Output: rl/artifacts/v7/15/rec/<deck>/<tag>.jsonl (gitignored) + .probe.txt +
# .driver.log; one REC15|... line on stdout with the teacher counters.
[ -f ~/.profile ] && . ~/.profile
set -u
DECK=$1; TAG=$2; PORT=$3; EP=${4:-50}; SEED=${5:-15000}; DPORT=${6:-7911}; OPP=${7:-heuristic}
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
OUT=$LB/rl/artifacts/v7/15/rec/$DECK
mkdir -p $OUT
[ -f $RL/$DECK.dck ] || { echo "REC15|$TAG|no deck $DECK.dck"; exit 2; }
rm -f $OUT/$TAG.jsonl
python3 $LB/rl/wire_echo_server.py --port $PORT --out $OUT/$TAG.jsonl --max-conns 1 --pick 0 \
    > $OUT/$TAG.echo.log 2>&1 &
ECHO_PID=$!
sleep 1
cp $RL/$DECK.dck /home/user/mage/Mage.Tests/ 2>/dev/null; cd /home/user/mage
T0=$(date +%s)
RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=$DPORT timeout ${JOB_TIMEOUT:-7200} bash $RL/run_driver.sh \
    -Drl.episodes=$EP -Drl.agent=cp7 -Drl.aiSkill=6 -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=${BUDGET:-4000} \
    -Drl.encoderV=7 -Drl.blockAudit=true \
    -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck -Drl.stopTurn=60 \
    -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 -Drl.out=$OUT/$TAG.probe.txt ${EXTRA:-} \
    > $OUT/$TAG.driver.log 2>&1
RC=$?
kill $ECHO_PID 2>/dev/null
wait $ECHO_PID 2>/dev/null
NC=$(grep -c '"t":"consult"' $OUT/$TAG.jsonl)
NY=$(grep -c '"y":[0-9]' $OUT/$TAG.jsonl)
NNEG=$(grep -c '"y":-1' $OUT/$TAG.jsonl)
NEND=$(grep -c '"t":"end"' $OUT/$TAG.jsonl)
FB=$(grep -oE 'teacher[A-Za-z]*=[0-9]*|autoPassEmpty=[0-9]*|windows=[0-9]*' $OUT/$TAG.probe.txt 2>/dev/null | awk -F= '{v[$1]=$2} END{for(k in v) printf "%s=%s ", k, v[k]}')
WL=$(grep -o 'wins=[0-9]*\|losses=[0-9]*\|stalls=[0-9]*\|draws=[0-9]*\|turns_per_ep=[0-9.]*' $OUT/$TAG.probe.txt 2>/dev/null | paste -sd' ')
echo "REC15|$TAG|deck=$DECK|opp=$OPP|rc=$RC|episodes=$EP|consults=$NC|labelled=$NY|y_neg=$NNEG|ends=$NEND|wall_s=$(( $(date +%s) - T0 ))|$FB|$WL"
grep -h 'Exception\|refused\|RLJOB|error' $OUT/$TAG.driver.log | head -3
