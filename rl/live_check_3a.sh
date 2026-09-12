#!/bin/bash
# Gate 3a live check: the v7 driver (port 7911, -Drl.encoderV=7) against the
# real policy_server.py --arch v7 (lane-d Python in /home/user/CardGuru) with a
# freshly minted init checkpoint, N eval games. A handshake refusal prints its
# reason on both sides; a consult the server rejects closes the connection and
# the driver names it.
#   bash rl/live_check_3a.sh [episodes] [server port] [device]
[ -f ~/.profile ] && . ~/.profile
set -u
EP=${1:-10}; PORT=${2:-7781}; DEV=${3:-cpu}
CG=/home/user/CardGuru
RL=$CG/rl
OUT=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/wire3a
CKPT=/tmp/v7_init.pt
[ -f $CKPT ] || python3 $RL/p10_init_net.py --arch v7 --out $CKPT
cd $CG
RL_TORCH_THREADS=4 python3 $RL/policy_server.py --arch v7 --ckpt $CKPT --device $DEV \
    --port $PORT --seed 0 --frozen > $OUT/live.server.log 2>&1 &
SRV=$!
t=0
while [ $t -lt 180 ]; do
    grep -q "policy server" $OUT/live.server.log 2>/dev/null && break
    grep -q "Traceback" $OUT/live.server.log 2>/dev/null && { echo "LIVE|server failed"; tail -8 $OUT/live.server.log; kill $SRV; exit 1; }
    sleep 2; t=$((t + 2))
done
grep "policy server" $OUT/live.server.log | head -1
cd /home/user/mage
RL_PERSIST=1 RL_DRIVER_PORT=7911 timeout 1500 bash $RL/run_driver.sh \
    -Drl.episodes=$EP -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
    -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true \
    -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 \
    -Drl.mode=eval -Drl.seed=910000 -Drl.report=0 -Drl.out=$OUT/live.probe.txt \
    > $OUT/live.driver.log 2>&1
RC=$?
kill $SRV 2>/dev/null; wait $SRV 2>/dev/null
echo "LIVE|rc=$RC"
grep -h 'RL|summary' $OUT/live.driver.log | grep -o 'episodes=[0-9]*|wins=[0-9]*|losses=[0-9]*|draws=[0-9]*|stalls=[0-9]*|win_rate=[0-9.]*\|agent_consults_per_ep=[0-9.]*\|agent_actions_per_ep=[0-9.]*\|turns_per_ep=[0-9.]*' | tr '\n' ' '; echo
grep -h 'Exception\|refused\|RLJOB|error\|closed mid-consult' $OUT/live.driver.log | head -3
grep -h 'HANDSHAKE\|Traceback\|refus\|unresolved\|stats' $OUT/live.server.log | head -5
