#!/bin/bash
# Gameplay transcripts of one checkpoint (HANDOFF-V7 §K "scratch play transcript"):
# frozen eval-mode server on 7947 (--argmax-classes), a FRESH driver JVM on 7913 with the
# v7 flags + -Drl.debug=true, then 1-game eval jobs with the lane's battery flags:
# seed 6001 vs the heuristic, seed 6002 vs CP7 (rl.aiSkill 6). The RLGAME blocks from
# /tmp/rl_p9/driver_server_7913.log are copied to <out>/<tag>_vs_<opp>_s<seed>.txt.
#   bash rl/replay_ck.sh <ckpt> <out dir> <tag>        (run only when no lane runs)
[ -f ~/.profile ] && . ~/.profile
set -u
CK=${1:?ckpt}; OUT=${2:?out}; TAG=${3:?tag}; PORT=7947; DPORT=7913
RL=/home/user/CardGuru/rl; FEATS=$RL/e2_features.tsv; LOG=/tmp/rl_p9/driver_server_$DPORT.log
mkdir -p $OUT
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
: > $OUT/server.log
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $PORT --ckpt "$CK" --seed 0 \
    --sdim 32 --cdim 94 --arch v7 --threads 1 --frozen --device cuda --logit-bound 5 --argmax-classes > $OUT/server.log 2>&1 &
t=0; until grep -q "policy server" $OUT/server.log; do sleep 2; t=$((t+2)); [ $t -ge 180 ] && { echo "REPLAY|server failed"; exit 1; }; done
bash $RL/driver_server.sh start $DPORT "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7 -Drl.debug=true" > /dev/null 2>&1 || { echo "REPLAY|driver failed"; exit 1; }
cp $RL/W0Base.dck /home/user/mage/Mage.Tests/; cd /home/user/mage
for spec in "heuristic|6001|" "cp7|6002|-Drl.aiSkill=6"; do
    IFS='|' read -r OPP SEED EXTRA <<< "$spec"
    f=$OUT/${TAG}_vs_${OPP}_s${SEED}.probe.txt
    RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=$DPORT timeout 1800 bash $RL/run_driver.sh \
        -Drl.episodes=1 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT -Drl.opponent=$OPP $EXTRA -Drl.debug=true \
        -Drl.searchPlies=1 -Drl.searchBreadth=8 -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck \
        -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 -Drl.out=$f > $OUT/${TAG}_vs_${OPP}_s${SEED}.driver.log 2>&1
    echo "REPLAY|$OPP|seed=$SEED|$(grep -o 'wins=[0-9]*\|losses=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $f | paste -sd' ')"
    # the LAST RLGAME block in the driver log belongs to this game
    awk '/^RLGAME\|/{blk=""; on=1} on{blk=blk $0 "\n"} /^RLGAME_END/{on=0; last=blk} END{printf "%s", last}' $LOG > $OUT/${TAG}_vs_${OPP}_s${SEED}.txt
    echo "REPLAY|transcript=$OUT/${TAG}_vs_${OPP}_s${SEED}.txt|lines=$(wc -l < $OUT/${TAG}_vs_${OPP}_s${SEED}.txt)|$(head -1 $OUT/${TAG}_vs_${OPP}_s${SEED}.txt | cut -c1-80)"
done
pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "REPLAY|done|$(date -u +%FT%TZ)"
