#!/bin/bash
# Phase 11 / A3 - census recordings of one checkpoint's argmax play (rl/PHASE11-DRILL.md).
# Frozen eval server on 7947 (--argmax-classes; cand_refers_pool comes from the checkpoint's
# config, the server prints it), rl/probes/record_proxy.py on 7948 logging the driver's consults
# and the server's {"a":k} replies, and a FRESH driver JVM on 7913 with the v7 flags and
# -Drl.debug=true (the [audit] / [atkaudit] transcript lines need it; this JVM serves nothing else).
# Game flags = the league lane's battery probe (EVALFLAGS: encoderV 7, block + attack audit).
#   bash rl/record_census.sh <ckpt> <deck> <heuristic|cp7> <games> <tag> [seed, default 11000]
#   bash rl/record_census.sh stop
# Output (rl/artifacts/v7/11/): rec_<tag>.jsonl (gitignored), rec_<tag>.audit.txt (RLGAME headers +
# audit lines), rec_<tag>.counts.txt (the CENSUSREC line + the census lines for the deck),
# rec_<tag>.{server,proxy,driver}.log, rec_<tag>.probe.txt.
# Prints:  CENSUSREC|<tag>|rc=..|ckpt=..|deck=..|opp=..|games=..|seed=..|consults=..|acts=..|ends=..|wins=.. losses=.. ...|cand_refers_pool=..|rlgame_blocks=..|audit_lines=..
#          then the DC| or LC| census lines, then  CENSUSREC|done|<tag>|<utc>
[ -f ~/.profile ] && . ~/.profile
set -u
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
OUT=$LB/rl/artifacts/v7/11
SPORT=7947; PPORT=7948; DPORT=7913
DLOG=/tmp/rl_p9/driver_server_$DPORT.log

stop_all() {
    pkill -f "policy_serve[r].py --port $SPORT" 2>/dev/null
    pkill -f "record_prox[y].py --port $PPORT" 2>/dev/null
    bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
}
if [ "${1:-}" = stop ]; then
    stop_all; sleep 2
    echo "CENSUSREC|stop|left=$(pgrep -fc "policy_serve[r].py --port $SPORT|record_prox[y].py --port $PPORT")"
    exit 0
fi

CK=${1:?ckpt}; DECK=${2:?deck}; OPP=${3:?opp}; G=${4:?games}; TAG=${5:?tag}; SEED=${6:-11000}
FEATS=$RL/e2_features.tsv
mkdir -p $OUT
case $OPP in
    heuristic) OPPF="-Drl.opponent=heuristic" ;;
    cp7)       OPPF="-Drl.opponent=cp7 -Drl.aiSkill=6" ;;
    *) echo "CENSUSREC|$TAG|bad opponent $OPP"; exit 2 ;;
esac
[ -f "$CK" ] || { echo "CENSUSREC|$TAG|no checkpoint $CK"; exit 2; }

stop_all; sleep 2
P=$OUT/rec_$TAG
: > $P.server.log
cd /home/user/CardGuru
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $SPORT --ckpt "$CK" --seed 0 \
    --sdim 32 --cdim 94 --arch v7 --threads 1 --frozen --device cuda --logit-bound 5 --argmax-classes > $P.server.log 2>&1 &
t=0; until grep -q "policy server" $P.server.log; do sleep 2; t=$((t+2)); [ $t -ge 180 ] && { echo "CENSUSREC|$TAG|server failed"; stop_all; exit 1; }; done
bash $RL/driver_server.sh start $DPORT "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7 -Drl.debug=true" > /dev/null 2>&1 \
    || { echo "CENSUSREC|$TAG|driver failed"; stop_all; exit 1; }
N0=$(wc -l < $DLOG 2>/dev/null || echo 0)
rm -f $P.jsonl
python3 $LB/rl/probes/record_proxy.py --port $PPORT --upstream $SPORT --out $P.jsonl --max-conns 1 > $P.proxy.log 2>&1 &
PP=$!; sleep 1
cp $RL/$DECK.dck /home/user/mage/Mage.Tests/; cd /home/user/mage
RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=$DPORT timeout 7200 bash $RL/run_driver.sh \
    -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PPORT $OPPF -Drl.debug=true \
    -Drl.searchPlies=1 -Drl.searchBreadth=8 -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck \
    -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 -Drl.out=$P.probe.txt > $P.driver.log 2>&1
RC=$?
kill $PP 2>/dev/null; wait $PP 2>/dev/null
tail -n +$((N0 + 1)) $DLOG 2>/dev/null | grep -a '^RLGAME|\|\[audit\]\|\[atkaudit\]' > $P.audit.txt
C=$(grep -c '"t":"consult"' $P.jsonl); A=$(grep -c '^{"a":' $P.jsonl); E=$(grep -c '"t":"end"' $P.jsonl)
WL=$(grep -o 'wins=[0-9]*\|losses=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*\|turns_per_ep=[0-9.]*' $P.probe.txt 2>/dev/null | paste -sd' ')
CRP=$(grep -o 'cand_refers_pool=[A-Za-z]*' $P.server.log | head -1)
RG=$(grep -c '^RLGAME|' $P.audit.txt); AU=$(grep -c '\[audit\]' $P.audit.txt)
echo "CENSUSREC|$TAG|rc=$RC|ckpt=$CK|deck=$DECK|opp=$OPP|games=$G|seed=$SEED|consults=$C|acts=$A|ends=$E|$WL|$CRP|rlgame_blocks=$RG|audit_lines=$AU" | tee $P.counts.txt
grep -h 'Exception\|refused\|RLJOB|error' $P.driver.log | head -3
stop_all
cd /home/user/CardGuru
case $DECK in
    BenchDimir) python3 $LB/rl/dimir_census.py --out $OUT "$TAG=$P.jsonl" | tee -a $P.counts.txt ;;
    G1Landfall) python3 $LB/rl/landfall_census.py --out $OUT "$TAG=$P.jsonl" --audit "$TAG=$P.audit.txt" | tee -a $P.counts.txt ;;
esac
echo "CENSUSREC|done|$TAG|$(date -u +%FT%TZ)"
