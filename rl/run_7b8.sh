#!/bin/bash
# 7a arm B8 (V7-VALIDATION "B8 pre-registration"): B2's recipe + --adv-norm auto,
# W0Base vs heuristic, 256 episodes, seed 0, conc4, cuda; census + land census on ck_256.
# Waits for 7c (rl/run_7c.sh) to release the GPU. Resumable (skips if census.txt exists).
# Launch: setsid nohup bash rl/run_7b8.sh > <artifacts>/7a/run_7b8.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7a
REC="$RL/artifacts/v7/wire3a/5b_W0Base_p1.jsonl $RL/artifacts/v7/wire3a/5b_B1Fast_sf.jsonl $RL/artifacts/v7/wire3a/5b_W4Inst_p99.jsonl $RL/artifacts/v7/wire3a/5b_BenchDimir_p1.jsonl"
LREC="$RL/artifacts/v7/wire3a/7c_W0Base_p1.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_p99.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_sf.jsonl"
while pgrep -f "run_7[c].sh" > /dev/null; do sleep 60; done
ARM=B8; OUT=/tmp/rl_7a_$ARM
if [ -s $ART/$ARM/census.txt ]; then echo "7A|arm=$ARM|skip=done"; exit 0; fi
rm -rf $OUT; mkdir -p $OUT $ART/$ARM
echo "7A|arm=$ARM|start=$(date -u +%FT%TZ)"
R0_ENCODER_V=7 R0_EVERY=256 R0_CHUNK=64 R0_EVAL_G=4 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 \
R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm auto" \
R0_OUT=$OUT RL_LOCK_STATS=1 \
bash $RL/rung0_lane.sh W0Base W0Twin 256 0 > $OUT/lane.log 2>&1
echo "7A|arm=$ARM|rc=$?|end=$(date -u +%FT%TZ)"
[ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $ART/$ARM/ 2>/dev/null
grep -h '^TRAIN|' $OUT/server_all.log > $ART/$ARM/train_lines.txt
python3 $RL/v7_init_logits.py --ckpt $OUT/ck_256.pt --logit-bound 5 --limit 1500 $REC 2>&1 | grep '^INITLOGITS' > $ART/$ARM/census.txt
python3 $RL/v7_land_census.py --device cpu --logit-bound 5 --ckpt $OUT/ck_256.pt $LREC 2>&1 | grep LANDCENSUS > $ART/$ARM/land_census.txt
cp $OUT/ck_256.pt $ART/$ARM/ 2>/dev/null
grep 'R0_\|R0|' $OUT/lane.log | tail -2
echo "7A|done=$(date -u +%FT%TZ)"
