#!/bin/bash
# 7c: the B2 recipe unchanged to 2,048 episodes on three seeds (V7-VALIDATION "7c
# pre-registration"). W0Base vs heuristic, conc4, cuda, lr 3e-5, 1 PPO epoch, logit
# bound 5, AdamW weight decay 0.01 on the heads, mana-ability-filter build. Battery
# every 512 episodes with the lane defaults (100 games per opponent, CP7 off), census
# on ck_2048 after each seed. Resumable: a seed with census.txt is skipped; a seed
# that died resumes from its /tmp/rl_7c_s<seed> checkpoints (rung0_lane.sh resume_at).
# Launch: setsid nohup bash rl/run_7c.sh > <artifacts>/7c/run_7c.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c
REC="$RL/artifacts/v7/wire3a/7c_W0Base_p1.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_p99.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_sf.jsonl"
mkdir -p $ART
run_seed() {   # $1 seed
    local OUT=/tmp/rl_7c_s$1
    if [ -s $ART/s$1/census.txt ]; then echo "7C|seed=$1|skip=done"; return; fi
    mkdir -p $OUT
    echo "7C|seed=$1|start=$(date -u +%FT%TZ)"
    R0_ENCODER_V=7 R0_EVERY=512 R0_CHUNK=64 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 \
    R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01" \
    R0_OUT=$OUT RL_LOCK_STATS=1 \
    bash $RL/rung0_lane.sh W0Base W0Twin 2048 $1 >> $OUT/lane.log 2>&1
    echo "7C|seed=$1|rc=$?|end=$(date -u +%FT%TZ)"
    [ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
    mkdir -p $ART/s$1; cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $ART/s$1/ 2>/dev/null
    grep -h '^TRAIN|' $OUT/server_all.log > $ART/s$1/train_lines.txt
    grep -h '^R0|' $OUT/lane.log > $ART/s$1/battery.txt
    for ck in 512 1024 1536 2048; do
        [ -f $OUT/ck_$ck.pt ] && python3 $RL/v7_init_logits.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu --limit 1500 $REC 2>&1 | grep '^INITLOGITS' | sed "s/^/ck_$ck /"
    done > $ART/s$1/census_all.txt
    grep 'ck_2048' $ART/s$1/census_all.txt > $ART/s$1/census.txt
    cp $OUT/ck_2048.pt $ART/s$1/ 2>/dev/null
    grep 'R0_\|R0|' $OUT/lane.log | tail -2
}
run_seed 0
run_seed 1
run_seed 2
echo "7C|done=$(date -u +%FT%TZ)"
