#!/bin/bash
# 7a arms A0/A1/A2 (V7-VALIDATION.md "7a pre-registration"): 256 episodes each, W0Base vs heuristic,
# cuda, conc4; census on ck_256 after each. Launch: setsid nohup bash rl/run_7a.sh > /tmp/run_7a.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7a
REC="$RL/artifacts/v7/wire3a/5b_W0Base_p1.jsonl $RL/artifacts/v7/wire3a/5b_B1Fast_sf.jsonl $RL/artifacts/v7/wire3a/5b_W4Inst_p99.jsonl $RL/artifacts/v7/wire3a/5b_BenchDimir_p1.jsonl"
mkdir -p $ART
run_arm() {   # $1 arm  $2 lr  $3 server extra  $4 census extra
    local OUT=/tmp/rl_7a_$1
    rm -rf $OUT; mkdir -p $OUT
    echo "7A|arm=$1|lr=$2|extra=$3|start=$(date -u +%FT%TZ)"
    R0_ENCODER_V=7 R0_EVERY=256 R0_CHUNK=64 R0_EVAL_G=4 R0_CP7_G=0 R0_CONC=4 R0_LR=$2 \
    R0_SRVEXTRA="--device cuda $3" R0_OUT=$OUT RL_LOCK_STATS=1 \
    bash $RL/rung0_lane.sh W0Base W0Twin 256 0 > $OUT/lane.log 2>&1
    echo "7A|arm=$1|rc=$?|end=$(date -u +%FT%TZ)"
    [ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
    mkdir -p $ART/$1; cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $ART/$1/ 2>/dev/null
    grep -h '^TRAIN|' $OUT/server_all.log > $ART/$1/train_lines.txt
    python3 $RL/v7_init_logits.py --ckpt $OUT/ck_256.pt $4 --limit 1500 $REC 2>&1 | grep '^INITLOGITS' > $ART/$1/census.txt
    cp $OUT/ck_256.pt $ART/$1/ck_256.pt 2>/dev/null
    grep 'R0_\|R0|' $OUT/lane.log | tail -3
}
run_arm A0 3e-4 "" ""
run_arm A1 3e-5 "--epochs 1" ""
run_arm A2 3e-5 "--epochs 1 --logit-bound 5" "--logit-bound 5"
echo "7A|done=$(date -u +%FT%TZ)"
