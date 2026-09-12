#!/bin/bash
# Record the raw policy wire of N seeded eval games through wire_echo_server.py.
#   bash rl/wire_record.sh <tag> <echo port> <encoderV> <driver port> [episodes] [seed]
# Output: rl/artifacts/v7/wire3a/<tag>.jsonl (+ .driver.log, .echo.log, .probe.txt)
# The job flags are the v6-baseline smoke's (rl/artifacts/v7/baseline.md), so the
# pinned properties match a driver JVM that first served that smoke.
[ -f ~/.profile ] && . ~/.profile
set -u
TAG=$1; PORT=$2; ENC=$3; DPORT=$4; EP=${5:-3}; SEED=${6:-900000}; DECK=${DECK:-W0Base}
LB=${LANE_B:-/mnt/c/Users/sutanto4/Documents/CardGuru-lane-b}
RL=/home/user/CardGuru/rl
OUT=$LB/rl/artifacts/v7/wire3a
mkdir -p $OUT
rm -f $OUT/$TAG.jsonl
python3 $LB/rl/wire_echo_server.py --port $PORT --out $OUT/$TAG.jsonl --max-conns 1 --pick ${PICK:-0} \
    > $OUT/$TAG.echo.log 2>&1 &
ECHO_PID=$!
sleep 1
cp $RL/$DECK.dck /home/user/mage/Mage.Tests/ 2>/dev/null; cd /home/user/mage
RL_PERSIST=1 RL_DRIVER_PORT=$DPORT timeout 1500 bash $RL/run_driver.sh \
    -Drl.episodes=$EP -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=$ENC -Drl.blockAudit=true -Drl.attackAudit=true \
    -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck -Drl.stopTurn=60 \
    -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 -Drl.out=$OUT/$TAG.probe.txt \
    > $OUT/$TAG.driver.log 2>&1
RC=$?
kill $ECHO_PID 2>/dev/null
wait $ECHO_PID 2>/dev/null
echo "RECORD|$TAG|rc=$RC|lines=$(wc -l < $OUT/$TAG.jsonl)|consults=$(grep -c '"t":"consult"' $OUT/$TAG.jsonl)|md5=$(md5sum $OUT/$TAG.jsonl | cut -c1-12)"
grep -h 'RL|summary\|Exception\|refused\|RLJOB|error' $OUT/$TAG.driver.log | head -3
