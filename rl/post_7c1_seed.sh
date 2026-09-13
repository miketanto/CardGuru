#!/bin/bash
# Post-process one C1 seed (the tail of run_seed in rl/run_7c1.sh, extracted so a
# seed whose parent runner was stopped - rl/stop_c1_parent.sh - still gets its
# artifact directory), plus the probe_*.txt copies summ_7c1.py reads for the
# attackBudgetHit column.   Usage: bash rl/post_7c1_seed.sh <seed>
# Idempotent: re-running overwrites the derived files from the same /tmp state.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1
REC="$RL/artifacts/v7/wire3a/7c_W0Base_p1.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_p99.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_sf.jsonl"
S=${1:?seed}
OUT=/tmp/rl_7c1_s$S
[ -d $OUT ] || { echo "POST7C1|seed=$S|missing=$OUT"; exit 1; }
echo "POST7C1|seed=$S|start=$(date -u +%FT%TZ)"
# the lane appends server.log to server_all.log on every restart, but the LAST
# server lifetime (the 2048 battery's) is only in server.log
if [ -s $OUT/server.log ] && ! grep -qxF "$(tail -n1 $OUT/server.log)" $OUT/server_all.log 2>/dev/null; then
    cat $OUT/server.log >> $OUT/server_all.log
fi
mkdir -p $ART/s$S
cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $ART/s$S/ 2>/dev/null
cp $OUT/probe_*.txt $ART/s$S/ 2>/dev/null
grep -h '^TRAIN|\|^KL|' $OUT/server_all.log > $ART/s$S/train_lines.txt
grep -h '^R0|' $OUT/lane.log > $ART/s$S/battery.txt
grep -ho 'attackBudgetHit=[0-9]*' $OUT/probe_*.txt 2>/dev/null | sort | uniq -c > $ART/s$S/budget_hits.txt
for ck in 512 1024 1536 2048; do
    [ -f $OUT/ck_$ck.pt ] || continue
    python3 $RL/v7_init_logits.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu --limit 1500 $REC 2>&1 | grep '^INITLOGITS' | sed "s/^/ck_$ck /"
    python3 $RL/v7_land_census.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu $REC 2>&1 | grep 'lands>=3\|lands=[0-3]|' | sed "s/^/ck_$ck /"
done > $ART/s$S/census_all.txt
grep 'ck_2048' $ART/s$S/census_all.txt > $ART/s$S/census.txt
cp $OUT/ck_2048.pt $ART/s$S/ 2>/dev/null
echo "POST7C1|seed=$S|rows=$(wc -l < $ART/s$S/battery.txt)|census_lines=$(wc -l < $ART/s$S/census_all.txt)|end=$(date -u +%FT%TZ)"
grep 'R0_\|R0|' $OUT/lane.log | tail -2 | cut -c1-160
