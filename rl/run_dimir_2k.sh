#!/bin/bash
# BenchDimir v6: 1024 -> 2048, battery every 512 (so 1536 and 2048).
#
# EVAL_G goes 10 -> 100. The 0/512/1024 trend (D0 .00/.20/.40,
# D1 .00/.00/.20, TWIN .00/.20/.40) is monotone on all three arms, but
# every one of those rates is 10 games: .40 there is [.17,.69] Wilson,
# which cannot distinguish 1024 from 1536. At 100 games .40 is [.31,.50].
#
# The lane only fires a battery at the END of each 512-block, so resuming
# at 1024 produces no 1024 row at the new sample size. ANCHOR below is
# that row: the same three probes against the same ck_1024 weights, at
# 100 games, so the 1536/2048 rows have something comparable to move away
# from. Without it the first honest comparison would be 1536-vs-2048.
set -u
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_dimir_v6
FEATS=$RL/e2_features.tsv
G=100
APORT=7996

pkill -f "[R]LDriverServer" 2>/dev/null
pkill -f "policy_serve[r].py --port $APORT" 2>/dev/null
sleep 2

echo "=== ANCHOR ck_1024 @ ${G}g $(date +%H:%M:%S) ==="
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $APORT \
    --ckpt $OUT/ck_1024.pt --seed 0 --sdim 32 --cdim 94 --arch entattn \
    --gdim 16 --edim 48 --emax 96 --max-k 96 --threads 4 \
    > /tmp/dimir2k_anchor_srv.log 2>&1 &
for i in $(seq 1 45); do
    grep -q "policy server" /tmp/dimir2k_anchor_srv.log 2>/dev/null && break
    sleep 2
done
grep -q "policy server" /tmp/dimir2k_anchor_srv.log || { echo ANCHOR_SRV_FAILED; tail -5 /tmp/dimir2k_anchor_srv.log; exit 1; }

for spec in "heuristic|BenchDimir|D0" "search|BenchDimir|D1" "heuristic|BenchDimir|TWIN"; do
    IFS='|' read -r OPP DK LB <<< "$spec"
    F=$OUT/probe_${LB}_1024_g${G}.txt
    RL_PERSIST=1 RL_AUTOSTART=1 timeout 5400 bash $RL/run_driver.sh \
        -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=$OPP -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.encoderV=6 -Drl.blockAudit=true -Drl.attackAudit=true \
        -Drl.deck=$DK.dck -Drl.oppDeck=$DK.dck -Drl.stopTurn=60 \
        -Drl.mode=eval -Drl.seed=$((900000 + 1024)) -Drl.report=0 -Drl.out=$F \
        > /dev/null 2>&1
    echo "ANCHOR|$LB=$(grep -o 'win_rate=[0-9.]*' $F | cut -d= -f2)|n=$G"
done
pkill -f "policy_serve[r].py --port $APORT" 2>/dev/null
pkill -f "[R]LDriverServer" 2>/dev/null
sleep 2

echo "=== LANE 1024 -> 2048 $(date +%H:%M:%S) ==="
R0_ENCODER_V=6 R0_OUT=$OUT R0_EVERY=512 R0_EVAL_G=$G \
    R0_CP7_G=0 R0_PORT=7995 \
    bash $RL/rung0_lane.sh BenchDimir BenchDimir 2048 0
echo "=== DIMIR 2K DONE $(date +%H:%M:%S) ==="
