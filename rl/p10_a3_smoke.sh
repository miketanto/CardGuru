#!/bin/bash
# Phase 10 A3 smoke (rl/PHASE10-LEAGUE.md): rl/G1Landfall.dck on its own driver JVM
# (default 7913; 7911 may belong to the Phase 9 probe) - 20 games heuristic vs
# heuristic mirror (games end, no exceptions, turns), then a 4-game v7 wire
# recording through the echo server (wire_validate + unknown-card count).
# Out: rl/artifacts/v7/10/a3/.  Usage: bash rl/p10_a3_smoke.sh [driver port] [echo port]
[ -f ~/.profile ] && . ~/.profile
DPORT=${1:-7913}; EPORT=${2:-7785}
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
OUT=$LB/rl/artifacts/v7/10/a3
mkdir -p $OUT
cp $RL/G1Landfall.dck /home/user/mage/Mage.Tests/
bash $RL/driver_server.sh start $DPORT "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7" > /dev/null 2>&1
cd /home/user/mage
RL_PERSIST=1 RL_DRIVER_PORT=$DPORT timeout 1800 bash $RL/run_driver.sh \
    -Drl.episodes=20 -Drl.agent=heuristic -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true \
    -Drl.deck=G1Landfall.dck -Drl.oppDeck=G1Landfall.dck -Drl.stopTurn=60 \
    -Drl.mode=eval -Drl.seed=10300 -Drl.report=0 -Drl.out=$OUT/heur_mirror.txt \
    > $OUT/heur_mirror.driver.log 2>&1
echo "A3|mirror|rc=$?|$(grep -o 'win_rate=[0-9.]*\|turns_per_ep=[0-9.]*\|episodes=[0-9]*\|draws=[0-9]*\|stalls=[0-9]*' $OUT/heur_mirror.txt 2>/dev/null | tr '\n' '|')"
echo "A3|mirror|exceptions_driver_log=$(grep -c 'Exception' $OUT/heur_mirror.driver.log)|exceptions_jvm_log=$(grep -c 'Exception' /tmp/rl_p9/driver_server_${DPORT}.log 2>/dev/null)"
cd $LB
DECK=G1Landfall PICK=1 bash $LB/rl/wire_record.sh p10_G1Landfall_wire $EPORT 7 $DPORT 4 910300 > /dev/null 2>&1
F=$LB/rl/artifacts/v7/wire3a/p10_G1Landfall_wire.jsonl
echo "A3|wire|$(grep -o 'win_rate=[0-9.]*\|turns_per_ep=[0-9.]*' $LB/rl/artifacts/v7/wire3a/p10_G1Landfall_wire.probe.txt 2>/dev/null | tr '\n' '|')"
python3 $RL/wire_validate.py $F 2>&1 | tail -2 | sed 's/^/A3|validate|/'
python3 - "$F" <<'EOF'
import collections, json, sys
sys.path.insert(0, "/home/user/CardGuru/rl")
import v7_obs as V
ids = V.CardIds(); hello = None; seen = collections.Counter(); unk = collections.Counter(); n = 0
for line in open(sys.argv[1]):
    m = json.loads(line)
    if m.get("t") == "hello":
        hello = m
    if m.get("t") != "consult":
        continue
    o = V.parse_consult(m, ids, hello); n += 1
    for nm, i in zip(o.ent_name, o.ent_id.tolist()):
        if nm == "?":
            continue
        seen[nm] += 1
        if i < 0:
            unk[nm] += 1
print("A3|ids|consults=%d|distinct_names=%d|unknown_names=%d|unknown=%s" % (n, len(seen), len(unk), ",".join(sorted(unk)) or "none"))
EOF
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "A3|done"
