#!/bin/bash
# Phase 8b (rl/PHASE8-DECKS.md, V7-VALIDATION "Phase 8 pre-registration"): L2 = the
# diverse cross-deck league. From L0 ck_3072 (the W0Base policy after C1 + 1,024
# heuristic episodes), +1,024 episodes on W0Base with rl/rung0_lane_league.sh and
# R0_OPP_SPEC rotating per 256-block: heuristic on BenchDimir, CP7 (skill 6) on
# BenchBurn, the 8a seed-0 Dimir policy (frozen, ck_1024) on BenchDimir, the heuristic
# on BenchBurn. C1's recipe; batteries (D0 / D1 / TWIN, 100 games, fixed protocol) at
# +0 and every block; jobs.log kept. Then, one at a time (memory rule): the suite on
# L2 ck_4096, the suite on L0 ck_3072 (the control, once), head-to-head L2 vs L0
# (rl/hard_battery.sh: its CP7-on-W0Base row replicates the suite's, then H2H).
# Own driver 7912, ports 7952 / 7960; state /tmp/rl_8b_L2; artifacts rl/artifacts/v7/8b.
# Resumable (lane resume_at; suites skip rows whose probe exists).
# Launch: setsid nohup bash rl/run_8b.sh > /mnt/c/.../rl/artifacts/v7/8b/run_8b.log 2>&1 < /dev/null &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
ART=$LB/rl/artifacts/v7/8b
INIT=${INIT:-$LB/rl/artifacts/v7/7l/L0/ck_3072.pt}
DIMIR=${DIMIR:-$LB/rl/artifacts/v7/8a/s0/ck_1024.pt}
mkdir -p $ART
for f in "$INIT" "$DIMIR"; do [ -s "$f" ] || { echo "8B|FAILED|missing $f"; exit 1; }; done
OUT=/tmp/rl_8b_L2
if [ -s $ART/L2/census.txt ]; then echo "8B|L2|skip=done"; else
    mkdir -p $OUT
    echo "8B|L2|start=$(date -u +%FT%TZ)|init=$INIT|dimir=$DIMIR"
    R0_ENCODER_V=7 R0_EVERY=256 R0_CHUNK=64 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 RL_LOCK_STATS=1 R0_ROWS="D0" \
    RL_DRIVER_PORT=7912 R0_BATTERY_START=1 R0_PORT=7952 R0_OPP_PORT=7960 \
    R0_INIT=$INIT \
    R0_OPP_SPEC="heuristic::BenchDimir.dck,cp7::BenchBurn.dck,rl:$DIMIR:BenchDimir.dck,heuristic::BenchBurn.dck" \
    R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm auto --target-kl 0.02 --argmax-classes" \
    R0_OUT=$OUT bash $RL/rung0_lane_league.sh W0Base W0Twin 4096 0 >> $OUT/lane.log 2>&1
    echo "8B|L2|rc=$?|end=$(date -u +%FT%TZ)"
    bash $RL/post_lane_seed.sh $OUT $ART/L2 "3072 3328 3584 3840 4096"
    cp $OUT/jobs.log $ART/L2/ 2>/dev/null; grep -h '^R0_OPP' $OUT/lane.log > $ART/L2/opp_blocks.txt
    grep 'R0_\|R0|' $OUT/lane.log | tail -2 | cut -c1-200
fi
suite() {   # $1 ckpt  $2 out dir  $3 label
    if grep -q 'XDECK|done' $2.txt 2>/dev/null; then echo "8B|suite|$3|skip=done"; return; fi
    echo "8B|suite|$3|start=$(date -u +%FT%TZ)"
    bash $RL/battery_xdeck.sh "$1" W0Base $2 7947 7913 2>&1 | grep '^XDECK' | tee $2.txt
}
L2CK=$ART/L2/ck_4096.pt; [ -s $L2CK ] || L2CK=$OUT/ck_4096.pt
suite $L2CK $ART/suite_L2_4096 L2_4096
suite $INIT  $ART/suite_L0_3072 L0_3072
if ! grep -q 'HARD|done' $ART/h2h.txt 2>/dev/null; then
    echo "8B|h2h|start=$(date -u +%FT%TZ)"
    SKIP_CP7=1 bash $RL/hard_battery.sh $L2CK $ART/hard L2_4096 $INIT 7948 7914 2>&1 | grep '^HARD' | tee $ART/h2h.txt
fi
echo "8B|done=$(date -u +%FT%TZ)"
