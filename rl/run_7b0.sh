#!/bin/bash
# 7a arm B0: the B arms' init policy (the same seed-0 init.pt as B1-B4, copied to
# rl/artifacts/v7/7a/B0/init.pt), frozen (no updates), sampled as in training
# (-Drl.mode=train), 128 episodes W0Base vs heuristic, conc4, on the filter build:
# the random-policy win-rate baseline that the pre-registered 5 % bar (A2's uniform
# policy, mana sink present) no longer measures. Output: rl/artifacts/v7/7a/B0/.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7a/B0
OUT=/tmp/rl_7a_B0; rm -rf $OUT; mkdir -p $OUT
PORT=7946
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT --ckpt $ART/init.pt \
    --seed 0 --sdim 32 --cdim 94 --arch v7 --threads 4 --log $OUT/train.csv \
    --device cuda --frozen --logit-bound 5 > $OUT/server.log 2>&1 &
t=0
until grep -q "policy server" $OUT/server.log 2>/dev/null; do
    sleep 2; t=$((t + 2))
    if [ $t -ge 120 ] || grep -q Traceback $OUT/server.log 2>/dev/null; then
        echo "7B0|server failed"; tail -3 $OUT/server.log; exit 1
    fi
done
echo "7B0|start=$(date -u +%FT%TZ)"
cp $RL/W0Base.dck /home/user/mage/Mage.Tests/ 2>/dev/null
for i in 0 1; do
    RL_PERSIST=1 RL_AUTOSTART=1 RL_CONC=4 timeout 3600 bash $RL/run_driver.sh \
        -Drl.episodes=64 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
        -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.encoderV=7 -Drl.blockAudit=true -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck \
        -Drl.stopTurn=60 -Drl.mode=train -Drl.seed=$((90000000 + i * 64)) -Drl.report=0 \
        -Drl.out=$OUT/probe.txt > /dev/null 2>&1
    echo "7B0|chunk=$i|rc=$?"
done
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
cp $OUT/probe.txt $OUT/server.log $ART/ 2>/dev/null
grep -o 'episodes=[0-9]*\|wins=[0-9]*\|win_rate=[0-9.]*' $OUT/probe.txt | paste -sd' '
echo "7B0|done=$(date -u +%FT%TZ)"
