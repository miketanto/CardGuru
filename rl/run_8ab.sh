#!/bin/bash
# 8a-b (PHASE8-DECKS STATE 2026-09-13 19:10; V7-VALIDATION "8a-b pre-registration"): the
# mechanism test - C1's recipe with ONE change, --adv-norm batch (batch-centred
# advantages: an all-lost batch centres to zero instead of pushing every taken action
# down), on BenchDimir vs the heuristic, one seed, 512 episodes. Two-tier rule: a
# 50-game D0 development probe at 256 (and at 0), 100-game D0 + D1 at 512 (the level);
# LAND + SPELL + type census on ck_256 / ck_512 over the Dimir census set; jobs.log kept.
# Lane state /tmp/rl_8ab_s0, driver 7910 / server 7940; artifacts rl/artifacts/v7/8ab/s0.
# Launch: setsid nohup bash rl/run_8ab.sh > /mnt/c/.../rl/artifacts/v7/8ab/run_8ab.log 2>&1 < /dev/null &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/8ab
REC="$RL/artifacts/v7/wire3a/7c_BenchDimir_p1.jsonl $RL/artifacts/v7/wire3a/7c_BenchDimir_p99.jsonl $RL/artifacts/v7/wire3a/7c_BenchDimir_sf.jsonl"
ADV=${ADV:-batch}; TAG=${TAG:-8ab}; SEED=${SEED:-0}; EXTRA=${EXTRA:-}
OUT=/tmp/rl_${TAG}_s$SEED
mkdir -p $ART $OUT
if [ -s $ART/s$SEED/census.txt ]; then echo "$TAG|seed=$SEED|skip=done"; exit 0; fi
echo "$TAG|seed=$SEED|start=$(date -u +%FT%TZ)|adv=$ADV|extra=$EXTRA"
R0_ENCODER_V=7 R0_EVERY=256 R0_CHUNK=64 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 \
R0_ROWS="D0" R0_ROWS_FINAL="D0 D1" R0_EVAL_G=100 R0_EVAL_G_INTERIM=50 \
R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm $ADV --target-kl ${TKL:-0.02} --argmax-classes $EXTRA" \
R0_OUT=$OUT RL_LOCK_STATS=1 \
bash $RL/rung0_lane.sh BenchDimir BenchDimir 512 $SEED >> $OUT/lane.log 2>&1
echo "$TAG|seed=$SEED|rc=$?|end=$(date -u +%FT%TZ)"
[ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
mkdir -p $ART/s$SEED; cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $OUT/jobs.log $OUT/probe_*.txt $ART/s$SEED/ 2>/dev/null
grep -h '^TRAIN|\|^KL|' $OUT/server_all.log > $ART/s$SEED/train_lines.txt
grep -h '^R0|' $OUT/lane.log > $ART/s$SEED/battery.txt
grep -ho 'attackBudgetHit=[0-9]*' $OUT/probe_*.txt 2>/dev/null | sort | uniq -c > $ART/s$SEED/budget_hits.txt
for ck in 256 512; do
    [ -f $OUT/ck_$ck.pt ] || continue
    python3 $RL/v7_init_logits.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu --limit 1500 $REC 2>&1 | grep '^INITLOGITS' | sed "s/^/ck_$ck /"
    python3 $RL/v7_land_census.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu $REC 2>&1 | grep 'lands>=3\|lands=[0-3]|' | sed "s/^/ck_$ck /"
    python3 $RL/v7_land_census.py --type SPELL --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu $REC 2>&1 | grep 'lands>=3\|lands=[0-5]|' | sed "s/^/ck_$ck /"
done > $ART/s$SEED/census_all.txt
grep 'ck_512' $ART/s$SEED/census_all.txt > $ART/s$SEED/census.txt
cp $OUT/ck_512.pt $ART/s$SEED/ 2>/dev/null
grep 'R0_\|R0|' $OUT/lane.log | tail -2 | cut -c1-220
echo "$TAG|done=$(date -u +%FT%TZ)"
