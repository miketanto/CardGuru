#!/bin/bash
# One debug-logged game between two frozen checkpoints, EACH ON ITS OWN DECK
# (rl/replay_ck.sh's transcript path + rl/p10_h2h.sh's second policy seat).
# The agent seat (A) is the one whose decisions the RLGAME transcript records.
# Fixed protocol: both servers frozen, --argmax-classes, logit bound 5, eval mode.
#   bash rl/replay_pair.sh <ckA> <deckA> <ckB> <deckB> <out dir> <tag> <seed>
# Ports: servers 7947 (A) / 7948 (B), fresh driver JVM 7913 with rl.debug. Run only
# when no lane runs (two servers + one JVM). Absolute <out dir> required (the jobs
# run from /home/user/mage).
[ -f ~/.profile ] && . ~/.profile
set -u
CKA=${1:?ckA}; DA=${2:?deckA}; CKB=${3:?ckB}; DB=${4:?deckB}; OUT=${5:?out}; TAG=${6:?tag}; SEED=${7:?seed}
case "$OUT" in /*) ;; *) echo "PAIR|FAILED|out dir must be absolute"; exit 1 ;; esac
PA=7947; PB=7948; DPORT=7913
RL=/home/user/CardGuru/rl; FEATS=$RL/e2_features.tsv; LOG=/tmp/rl_p9/driver_server_$DPORT.log
SRV="--sdim 32 --cdim 94 --arch v7 --threads 1 --frozen --device cuda --logit-bound 5 --argmax-classes"
mkdir -p $OUT
start() {   # $1 port $2 ckpt $3 log
    pkill -f "policy_serve[r].py --port $1" 2>/dev/null; sleep 1; : > $3
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $1 --ckpt "$2" --seed 0 $SRV > $3 2>&1 &
    local t=0
    until grep -q "policy server" $3; do sleep 2; t=$((t+2)); if [ $t -ge 180 ] || grep -q Traceback $3; then echo "PAIR|FAILED|server $1"; tail -3 $3; exit 1; fi; done
}
start $PA "$CKA" $OUT/${TAG}.serverA.log
start $PB "$CKB" $OUT/${TAG}.serverB.log
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
bash $RL/driver_server.sh start $DPORT "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7 -Drl.debug=true" > /dev/null 2>&1 \
    || { echo "PAIR|FAILED|driver $DPORT"; exit 1; }
cp $RL/$DA.dck $RL/$DB.dck /home/user/mage/Mage.Tests/
f=$OUT/${TAG}.probe.txt
cd /home/user/mage
RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=$DPORT timeout 1800 bash $RL/run_driver.sh \
    -Drl.episodes=1 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PA -Drl.opponent=rl -Drl.oppPort=$PB -Drl.debug=true \
    -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true -Drl.deck=$DA.dck -Drl.oppDeck=$DB.dck \
    -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 -Drl.out=$f > $OUT/${TAG}.driver.log 2>&1
echo "PAIR|$TAG|A=$(basename $CKA):$DA|B=$(basename $CKB):$DB|seed=$SEED|$(grep -o 'wins=[0-9]*\|losses=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $f | paste -sd' ')"
awk '/^RLGAME\|/{blk=""; on=1} on{blk=blk $0 "\n"} /^RLGAME_END/{on=0; last=blk} END{printf "%s", last}' $LOG > $OUT/${TAG}.txt
echo "PAIR|transcript=$OUT/${TAG}.txt|lines=$(wc -l < $OUT/${TAG}.txt)|$(head -1 $OUT/${TAG}.txt | cut -c1-60)"
pkill -f "policy_serve[r].py --port $PA" 2>/dev/null
pkill -f "policy_serve[r].py --port $PB" 2>/dev/null
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
