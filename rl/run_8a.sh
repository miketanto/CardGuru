#!/bin/bash
# Phase 8a (rl/PHASE8-DECKS.md, V7-VALIDATION "Phase 8 pre-registration"): the C1
# recipe EXACTLY (lr 3e-5, 1 epoch, logit bound 5, AdamW wd 0.01 on the heads,
# --adv-norm auto --target-kl 0.02 --argmax-classes; mana-ability filter + attack-budget
# build) on BenchDimir vs the heuristic, 1,024 episodes, seeds 0 then 1, batteries at
# 512 and 1024 (D0 / D1 / TWIN = a second D0 sample: TWIN deck = BenchDimir, 100 games
# each), LAND + SPELL (P(cast)) + type census on ck_512/ck_1024 over the Dimir census set,
# jobs.log kept, then the six-row cross-deck suite (rl/battery_xdeck.sh) on ck_1024.
# Resumable per seed (lane resume_at; a seed with census.txt is skipped; the suite skips
# rows whose probe exists). Lane state /tmp/rl_8a_s<seed>, driver 7910 / server 7940
# (rung0_lane.sh defaults), suite on 7947 / 7913 AFTER the lane (memory rule).
# Launch (inside one wsl call, keepalive alive):
#   setsid nohup bash rl/run_8a.sh > /mnt/c/.../rl/artifacts/v7/8a/run_8a.log 2>&1 < /dev/null &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/8a
REC="$RL/artifacts/v7/wire3a/7c_BenchDimir_p1.jsonl $RL/artifacts/v7/wire3a/7c_BenchDimir_p99.jsonl $RL/artifacts/v7/wire3a/7c_BenchDimir_sf.jsonl"
SEEDS=${SEEDS:-"0"}   # amendment: seed 1 (SEEDS="0 1", resumable) only if seed 0's 1024 reading is worth confirming
mkdir -p $ART
run_seed() {   # $1 seed
    local OUT=/tmp/rl_8a_s$1
    if [ -s $ART/s$1/census.txt ]; then echo "8A|seed=$1|skip=done"; else
    mkdir -p $OUT
    echo "8A|seed=$1|start=$(date -u +%FT%TZ)"
    R0_ENCODER_V=7 R0_EVERY=512 R0_CHUNK=64 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 R0_ROWS="D0" R0_ROWS_FINAL="D0 D1" \
    R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm auto --target-kl 0.02 --argmax-classes" \
    R0_OUT=$OUT RL_LOCK_STATS=1 \
    bash $RL/rung0_lane.sh BenchDimir BenchDimir 1024 $1 >> $OUT/lane.log 2>&1
    echo "8A|seed=$1|rc=$?|end=$(date -u +%FT%TZ)"
    [ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
    mkdir -p $ART/s$1; cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $OUT/jobs.log $ART/s$1/ 2>/dev/null
    cp $OUT/probe_*.txt $ART/s$1/ 2>/dev/null
    grep -h '^TRAIN|\|^KL|' $OUT/server_all.log > $ART/s$1/train_lines.txt
    grep -h '^R0|' $OUT/lane.log > $ART/s$1/battery.txt
    grep -ho 'attackBudgetHit=[0-9]*' $OUT/probe_*.txt 2>/dev/null | sort | uniq -c > $ART/s$1/budget_hits.txt
    for ck in 512 1024; do
        [ -f $OUT/ck_$ck.pt ] || continue
        python3 $RL/v7_init_logits.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu --limit 1500 $REC 2>&1 | grep '^INITLOGITS' | sed "s/^/ck_$ck /"
        python3 $RL/v7_land_census.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu $REC 2>&1 | grep 'lands>=3\|lands=[0-3]|' | sed "s/^/ck_$ck /"
        python3 $RL/v7_land_census.py --type SPELL --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu $REC 2>&1 | grep 'lands>=3\|lands=[0-5]|' | sed "s/^/ck_$ck /"
    done > $ART/s$1/census_all.txt
    grep 'ck_1024' $ART/s$1/census_all.txt > $ART/s$1/census.txt
    cp $OUT/ck_512.pt $OUT/ck_1024.pt $ART/s$1/ 2>/dev/null
    grep 'R0_\|R0|' $OUT/lane.log | tail -2 | cut -c1-200
    fi
    if [ -f $ART/s$1/ck_1024.pt ] && ! grep -q 'XDECK|done' $ART/s$1/suite.txt 2>/dev/null; then
        echo "8A|seed=$1|suite_start=$(date -u +%FT%TZ)"
        bash $RL/battery_xdeck.sh $ART/s$1/ck_1024.pt BenchDimir $ART/s$1/suite 7947 7913 2>&1 | grep '^XDECK' | tee $ART/s$1/suite.txt
    fi
}
for s in $SEEDS; do run_seed $s; done
echo "8A|done=$(date -u +%FT%TZ)"
