#!/bin/bash
# E2 end-to-end smoke: wider net (cdim 91) + feature table + socket IPC.
set -u
OUT=/tmp/rl_e2smoke
mkdir -p $OUT
pkill -f "policy_server.py --port 8890" 2>/dev/null
python3 /home/user/CardGuru/rl/policy_server.py --port 8890 \
    --ckpt $OUT/e2.pt --seed 0 --cdim 91 > $OUT/server.log 2>&1 &
SERVER=$!
for i in $(seq 1 100); do
    grep -q "policy server" $OUT/server.log 2>/dev/null && break
    grep -q "Traceback" $OUT/server.log 2>/dev/null && { cat $OUT/server.log; exit 1; }
done
cd /home/user/mage
mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
    -DfailIfNoTests=false -Drl.episodes=4 \
    -Drl.opponent=heuristic -Drl.policy=socket -Drl.port=8890 \
    -Drl.mode=train -Drl.deck=BenchDimir.dck -Drl.seed=777100 \
    -Drl.stopTurn=80 -Drl.report=0 \
    -Drl.cardFeatures=/home/user/CardGuru/rl/e2_features.tsv \
    > /dev/null 2>&1
grep -o 'RL|summary[^"<]*' \
    Mage.Tests/target/surefire-reports/TEST-org.mage.test.benchmark.rl.RLEpisodeDriver.xml \
    | head -1
kill $SERVER 2>/dev/null
echo "SMOKE_DONE"
