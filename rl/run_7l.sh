#!/bin/bash
# 7d league arms L0 / L1 (V7-VALIDATION "7d overnight pre-registration", Q2), both
# from C1 seed 0's ck_2048.pt, 1,024 more episodes each (absolute budget 3072, rows
# at 2048 (+0, R0_BATTERY_START) / 2560 / 3072), one seed each, C1's recipe.
#   L0 = rung0_lane.sh (vs the heuristic; the same-compute control)   port 7950
#   L1 = rung0_lane_league.sh vs frozen C1 s0 checkpoints per 512-block: block 0 =
#        ck_1024, block 1 = ck_2048 (R0_OPP|... lines say which)            port 7951 / opp 7960
# Both own driver 7912 (never 7910/7911). Sequential: L0 then L1. Resumable.
# Launch: setsid nohup bash rl/run_7l.sh > <artifacts>/7l/run_7l.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7l
INIT=${INIT:-/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s0/ck_2048.pt}
OPP1=${OPP1:-/tmp/rl_7c1_s0/ck_1024.pt}
OPP2=${OPP2:-/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s0/ck_2048.pt}
mkdir -p $ART
for f in "$INIT" "$OPP1" "$OPP2"; do [ -s "$f" ] || { echo "7L|FAILED|missing $f"; exit 1; }; done
COMMON="R0_ENCODER_V=7 R0_EVERY=512 R0_CHUNK=64 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 RL_LOCK_STATS=1 RL_DRIVER_PORT=7912 R0_BATTERY_START=1"
SRV="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm auto --target-kl 0.02 --argmax-classes"
run_arm() {   # $1 arm  $2 lane script  $3 port  $4 extra env (string)
    local OUT=/tmp/rl_7l_$1
    if [ -s $ART/$1/census.txt ]; then echo "7L|arm=$1|skip=done"; return; fi
    mkdir -p $OUT
    echo "7L|arm=$1|start=$(date -u +%FT%TZ)|init=$INIT"
    env $COMMON R0_INIT=$INIT R0_PORT=$3 R0_SRVEXTRA="$SRV" R0_OUT=$OUT $4 \
        bash $RL/$2 W0Base W0Twin 3072 0 >> $OUT/lane.log 2>&1
    echo "7L|arm=$1|rc=$?|end=$(date -u +%FT%TZ)"
    bash $RL/post_lane_seed.sh $OUT $ART/$1 "2048 2560 3072"
    grep 'R0_\|R0|' $OUT/lane.log | tail -2 | cut -c1-200
}
run_arm L0 rung0_lane.sh 7950 ""
run_arm L1 rung0_lane_league.sh 7951 "R0_OPP_PORT=7960 R0_OPP_CKPTS=$OPP1,$OPP2"
echo "7L|done=$(date -u +%FT%TZ)"
