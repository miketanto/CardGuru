#!/bin/bash
# Phase 5a loopback: engine v7 (driver 7911) -> policy_server.py --arch v7 with
# the real card_emb_v8 / deck_ctx_v1, 100+ consults, no refusals; then the two
# refusals the gate asks for: a v6 driver (7910) against the v7 server, and the
# v7 driver against a server holding a different card_emb version.
#   bash rl/live_check_5a.sh [episodes] [port]
[ -f ~/.profile ] && . ~/.profile
set -u
EP=${1:-10}; PORT=${2:-7785}
CG=/home/user/CardGuru; RL=$CG/rl
OUT=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/wire3a
CKPT=/tmp/v7_init.pt
[ -f $CKPT ] || python3 $RL/p10_init_net.py --arch v7 --out $CKPT

start_server() {   # $1 = extra server args, $2 = log
    cd $CG
    RL_TORCH_THREADS=4 python3 $RL/policy_server.py --arch v7 --ckpt $CKPT --device cpu \
        --port $PORT --seed 0 --frozen $1 > $2 2>&1 &
    SRV=$!
    for _ in $(seq 1 90); do grep -q "policy server" $2 2>/dev/null && return 0; sleep 2; done
    echo "5A|server failed"; tail -5 $2; kill $SRV; exit 1
}
run_job() {        # $1 = driver port, $2 = encoderV, $3 = log
    cd /home/user/mage
    RL_PERSIST=1 RL_DRIVER_PORT=$1 timeout 1500 bash $RL/run_driver.sh \
        -Drl.episodes=$EP -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
        -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.encoderV=$2 -Drl.blockAudit=true -Drl.attackAudit=true \
        -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 \
        -Drl.mode=eval -Drl.seed=920000 -Drl.report=0 -Drl.out=$OUT/5a.probe.txt > $3 2>&1
    echo "rc=$?"
}

echo "== 1. loopback: v7 driver -> v7 server (card_emb_v8, deck_ctx_v1)"
start_server "" $OUT/5a.server1.log
run_job 7911 7 $OUT/5a.driver1.log
grep -o 'RL|ipc|[^ ]*\|agent_consults_per_ep=[0-9.]*\|episodes=[0-9]*|wins=[0-9]*|losses=[0-9]*' $OUT/5a.driver1.log | tr '\n' ' '; echo
grep -c 'refus\|HANDSHAKE\|Traceback' $OUT/5a.server1.log
echo "== 2. refusal: v6 driver -> v7 server"
run_job 7910 6 $OUT/5a.driver2.log
grep -o 'refused the handshake[^"]*"[^"]*"\|RLJOB|error[^|]*' $OUT/5a.driver2.log | head -2 | cut -c1-200
grep -i 'handshake\|refus' $OUT/5a.server1.log | head -2 | cut -c1-200
kill $SRV 2>/dev/null; wait $SRV 2>/dev/null
echo "== 3. refusal: v7 driver (card_emb_v8) -> v7 server whose checkpoint carries card_emb_v6"
[ -f /tmp/v7_init_v6.pt ] || python3 $RL/p10_init_net.py --arch v7 --card-emb card_emb_v6 --out /tmp/v7_init_v6.pt > /dev/null 2>&1
CKPT=/tmp/v7_init_v6.pt
start_server "--card-emb card_emb_v6" $OUT/5a.server3.log
run_job 7911 7 $OUT/5a.driver3.log
grep -o 'refused the handshake[^"]*"[^"]*"\|RLJOB|error[^|]*' $OUT/5a.driver3.log | head -2 | cut -c1-200
grep -i 'handshake\|refus\|mismatch' $OUT/5a.server3.log | head -2 | cut -c1-200
kill $SRV 2>/dev/null; wait $SRV 2>/dev/null
echo "5A|DONE"
