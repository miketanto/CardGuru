#!/bin/bash
# Reproduce the L0 battery refusal: on a fresh driver JVM (7914) + a frozen server
# (7948, ck_2560), run (1) one TRAINING job with the lane's exact training flags
# (mode=train, conc 4, 4 episodes), then (2) the lane's exact PROBE flags (mode=eval,
# attackAudit, 2 episodes) with the client's output CAPTURED - the lane sends it to
# /dev/null, which is why the cause of the NA rows was never seen.
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl; OUT=/tmp/rl_repro; mkdir -p $OUT; rm -f $OUT/*.txt
FEATS=$RL/e2_features.tsv; PORT=7948; export RL_DRIVER_PORT=7914
bash $RL/driver_server.sh stop 7914 > /dev/null 2>&1
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT --ckpt /tmp/rl_7l_L0/ck_2560.pt --seed 0 \
    --sdim 32 --cdim 94 --arch v7 --threads 4 --frozen --device cuda --logit-bound 5 --argmax-classes > $OUT/server.log 2>&1 &
until grep -q "policy server" $OUT/server.log; do sleep 2; grep -q Traceback $OUT/server.log && { tail -3 $OUT/server.log; exit 1; }; done
cd /home/user/mage
echo "REPRO|train job"
RL_PERSIST=1 RL_AUTOSTART=1 RL_CONC=4 timeout 900 bash $RL/run_driver.sh \
    -Drl.episodes=4 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT -Drl.opponent=heuristic \
    -Drl.searchPlies=1 -Drl.searchBreadth=8 -Drl.cardFeatures=$FEATS -Drl.noYields=true \
    -Drl.consultBudget=4000 -Drl.encoderV=7 -Drl.blockAudit=true -Drl.deck=W0Base.dck \
    -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 -Drl.mode=train -Drl.seed=80002048 -Drl.report=0 2>&1 | grep -o 'RL|summary|episodes=[0-9]*\|RLJOB|[a-z]*|.\{0,200\}' | head -3
echo "REPRO|probe job (lane flags)"
RL_PERSIST=1 RL_AUTOSTART=1 timeout 900 bash $RL/run_driver.sh \
    -Drl.episodes=2 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 \
    -Drl.mode=eval -Drl.seed=902560 -Drl.report=0 -Drl.out=$OUT/probe.txt 2>&1 | grep -o 'RL|summary|episodes=[0-9]*\|RLJOB|[a-z]*|.\{0,300\}\|Exception.\{0,200\}' | head -4
echo "REPRO|probe rc=${PIPESTATUS[0]} out=$(ls -s $OUT/probe.txt 2>/dev/null)"
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
bash $RL/driver_server.sh stop 7914 > /dev/null 2>&1
echo "REPRO|done"
