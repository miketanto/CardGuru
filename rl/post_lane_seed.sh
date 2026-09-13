#!/bin/bash
# Generic post-processing of one rung-0 lane directory (the tail of run_seed in
# rl/run_7c1.sh, parameterised): copies logs, extracts TRAIN|/KL| lines, R0| rows,
# attackBudgetHit counts and probe_*.txt, runs the type census + land census on
# every ck_<N>.pt listed, writes census.txt from the LAST ck, copies that ck.
#   bash rl/post_lane_seed.sh <lane dir (/tmp/rl_...)> <artifact dir> <ck list, e.g. "512 1024 1536 2048">
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
REC="$RL/artifacts/v7/wire3a/7c_W0Base_p1.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_p99.jsonl $RL/artifacts/v7/wire3a/7c_W0Base_sf.jsonl"
OUT=${1:?lane dir}; ART=${2:?artifact dir}; CKS=${3:-"512 1024 1536 2048"}
[ -d $OUT ] || { echo "POSTLANE|missing=$OUT"; exit 1; }
echo "POSTLANE|out=$OUT|art=$ART|start=$(date -u +%FT%TZ)"
if [ -s $OUT/server.log ] && ! grep -qxF "$(tail -n1 $OUT/server.log)" $OUT/server_all.log 2>/dev/null; then
    cat $OUT/server.log >> $OUT/server_all.log
fi
if [ -s $OUT/opp_server.log ] && ! grep -qxF "$(tail -n1 $OUT/opp_server.log)" $OUT/opp_server_all.log 2>/dev/null; then
    cat $OUT/opp_server.log >> $OUT/opp_server_all.log
fi
mkdir -p $ART
cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $OUT/opp_server_all.log $ART/ 2>/dev/null
cp $OUT/probe_*.txt $ART/ 2>/dev/null
grep -h '^TRAIN|\|^KL|' $OUT/server_all.log > $ART/train_lines.txt
grep -h '^R0|\|^R0_OPP|\|^R0_INIT|' $OUT/lane.log > $ART/battery.txt
grep -ho 'attackBudgetHit=[0-9]*' $OUT/probe_*.txt 2>/dev/null | sort | uniq -c > $ART/budget_hits.txt
LAST=""
for ck in $CKS; do
    [ -f $OUT/ck_$ck.pt ] || continue
    LAST=$ck
    python3 $RL/v7_init_logits.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu --limit 1500 $REC 2>&1 | grep '^INITLOGITS' | sed "s/^/ck_$ck /"
    python3 $RL/v7_land_census.py --ckpt $OUT/ck_$ck.pt --logit-bound 5 --device cpu $REC 2>&1 | grep 'lands>=3\|lands=[0-3]|' | sed "s/^/ck_$ck /"
done > $ART/census_all.txt
if [ -n "$LAST" ]; then
    grep "ck_$LAST " $ART/census_all.txt > $ART/census.txt
    cp $OUT/ck_$LAST.pt $ART/ 2>/dev/null
fi
echo "POSTLANE|art=$ART|rows=$(wc -l < $ART/battery.txt)|census_lines=$(wc -l < $ART/census_all.txt)|last_ck=$LAST|end=$(date -u +%FT%TZ)"
