#!/bin/bash
# 7d piece (3) = D-PPO (V7-VALIDATION "7d overnight pre-registration"): PPO from the
# BC checkpoint with C1's exact recipe. rl/run_7c1.sh with ART 7d3, state
# /tmp/rl_7d3_s<seed>, and R0_INIT=bc.pt (the rung0_lane.sh hook copies it to
# $OUT/init.pt; bc.pt carries episodes=0 so the lane counts from 0 and its
# trained=0 battery IS the BC battery). Seeds 0 and 1. Resumable per seed.
# Launch: setsid nohup bash rl/run_7d3.sh > <artifacts>/7d3/run_7d3.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7d3
BC=${BC:-/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7d2/bc.pt}
mkdir -p $ART
[ -s "$BC" ] || { echo "7D3|FAILED|no bc.pt at $BC"; exit 1; }
run_seed() {   # $1 seed
    local OUT=/tmp/rl_7d3_s$1
    if [ -s $ART/s$1/census.txt ]; then echo "7D3|seed=$1|skip=done"; return; fi
    mkdir -p $OUT
    echo "7D3|seed=$1|start=$(date -u +%FT%TZ)|init=$BC"
    R0_INIT=$BC \
    R0_ENCODER_V=7 R0_EVERY=512 R0_CHUNK=64 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 \
    R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm auto --target-kl 0.02 --argmax-classes" \
    R0_OUT=$OUT RL_LOCK_STATS=1 \
    bash $RL/rung0_lane.sh W0Base W0Twin 2048 $1 >> $OUT/lane.log 2>&1
    echo "7D3|seed=$1|rc=$?|end=$(date -u +%FT%TZ)"
    bash $RL/post_lane_seed.sh $OUT $ART/s$1 "0 512 1024 1536 2048"
    grep 'R0_\|R0|' $OUT/lane.log | tail -2 | cut -c1-200
}
run_seed 0
run_seed 1
echo "7D3|done=$(date -u +%FT%TZ)"
