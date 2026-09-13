#!/bin/bash
# 7d piece (1b): record the CP7 teacher seat on the v7 wire through the echo server.
#   bash rl/record_cp7.sh <tag> <echo port> <episodes> <seed> [driver port=7911]
# The teacher seat (rl.agent=cp7, CP7TeacherPlayer) plays W0Base vs the heuristic,
# seats alternating by episode parity; every priority consult it would have made as
# the RL seat is sent to the echo server WITH the label y (the candidate CP7 acted
# on); the echo reply is ignored. Concurrency 1 so games do not interleave in the
# file (the {"t":"end"} lines segment games for v7_bc.py's hold-out).
# Output: rl/artifacts/v7/7d1b/<tag>.jsonl (gitignored) + .probe.txt + .driver.log.
[ -f ~/.profile ] && . ~/.profile
set -u
TAG=$1; PORT=$2; EP=${3:-100}; SEED=${4:-7300}; DPORT=${5:-7911}
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
OUT=$LB/rl/artifacts/v7/7d1b
mkdir -p $OUT
rm -f $OUT/$TAG.jsonl
python3 $LB/rl/wire_echo_server.py --port $PORT --out $OUT/$TAG.jsonl --max-conns 1 --pick 0 \
    > $OUT/$TAG.echo.log 2>&1 &
ECHO_PID=$!
sleep 1
cp $RL/W0Base.dck /home/user/mage/Mage.Tests/ 2>/dev/null; cd /home/user/mage
RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=$DPORT timeout 3600 bash $RL/run_driver.sh \
    -Drl.episodes=$EP -Drl.agent=cp7 -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=${BUDGET:-300} \
    -Drl.encoderV=7 -Drl.blockAudit=true \
    -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 \
    -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 -Drl.out=$OUT/$TAG.probe.txt ${EXTRA:-} \
    > $OUT/$TAG.driver.log 2>&1
RC=$?
kill $ECHO_PID 2>/dev/null
wait $ECHO_PID 2>/dev/null
NC=$(grep -c '"t":"consult"' $OUT/$TAG.jsonl)
NY=$(grep -c '"y":' $OUT/$TAG.jsonl)
NNEG=$(grep -c '"y":-1' $OUT/$TAG.jsonl)
NEND=$(grep -c '"t":"end"' $OUT/$TAG.jsonl)
echo "RECORD|$TAG|rc=$RC|episodes=$EP|consults=$NC|labelled=$NY|y_neg=$NNEG|ends=$NEND|$(grep -o 'fallbacks={[^}]*}' $OUT/$TAG.probe.txt 2>/dev/null | head -1 | grep -o 'teacher[A-Za-z]*=[0-9]*\|autoPassEmpty=[0-9]*\|windows=[0-9]*' | paste -sd' ')|$(grep -o 'wins=[0-9]*\|losses=[0-9]*\|win_rate=[0-9.]*' $OUT/$TAG.probe.txt 2>/dev/null | paste -sd' ')"
grep -h 'Exception\|refused\|RLJOB|error' $OUT/$TAG.driver.log | head -3
