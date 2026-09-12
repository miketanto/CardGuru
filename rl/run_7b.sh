#!/bin/bash
# 7a arms B1-B4 (V7-VALIDATION.md §7a "pre-registered next arms"): 256 episodes each,
# W0Base vs heuristic, cuda, conc4, lr 3e-5, 1 PPO epoch, logit bound 5 (= A2), on the
# build with the mana-ability filter (default since the 7a amendment; every B arm has it).
#   B1 = A2 + the filter        B2 = B1 + AdamW weight decay 0.01 on the heads
#   B3 = B1 + heads on SGD-momentum lr 1e-3 (trunk Adam 3e-5)   B4 = B1 + entropy coef 0.1
# Census on ck_256 after each. Launch: setsid nohup bash rl/run_7b.sh > /tmp/run_7b.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7a
REC="$RL/artifacts/v7/wire3a/5b_W0Base_p1.jsonl $RL/artifacts/v7/wire3a/5b_B1Fast_sf.jsonl $RL/artifacts/v7/wire3a/5b_W4Inst_p99.jsonl $RL/artifacts/v7/wire3a/5b_BenchDimir_p1.jsonl"
mkdir -p $ART
run_arm() {   # $1 arm  $2 lr  $3 server extra  $4 census extra
    local OUT=/tmp/rl_7a_$1
    if [ -f $ART/$1/census.txt ] && [ -s $ART/$1/census.txt ]; then
        echo "7A|arm=$1|skip=done"; return
    fi
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
B="--epochs 1 --logit-bound 5"
run_arm B1 3e-5 "$B" "--logit-bound 5"
run_arm B2 3e-5 "$B --weight-decay 0.01" "--logit-bound 5"
run_arm B3 3e-5 "$B --heads-opt sgd --heads-lr 1e-3" "--logit-bound 5"
run_arm B4 3e-5 "$B --ent-coef 0.1" "--logit-bound 5"
echo "7A|done=$(date -u +%FT%TZ)"
