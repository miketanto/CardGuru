#!/bin/bash
# 7d piece (1b) recording: CP7-labelled priority consults on W0Base (both seats by
# episode parity), sequential seeded jobs of 100 games each through rl/record_cp7.sh
# (echo port 7784, driver 7911 with the v7 flags, conc 1) until >= TARGET labelled
# consults (y >= 0). Artifacts rl/artifacts/v7/7d1b/7d1b_s<seed>.jsonl (gitignored);
# per-job RECORD| lines and the totals in rl/artifacts/v7/7d1b/record_7d1b.log (this
# script's stdout) and counts.txt (committed).
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
OUT=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7d1b
TARGET=${TARGET:-20000}; EP=${EP:-100}; MAXJOBS=${MAXJOBS:-12}
mkdir -p $OUT
echo "REC7D1B|start=$(date -u +%FT%TZ)|target=$TARGET|ep=$EP"
total=0; job=0
while [ $total -lt $TARGET ] && [ $job -lt $MAXJOBS ]; do
    seed=$((7400 + job))
    tag=7d1b_s$seed
    if [ -s $OUT/$tag.jsonl ] && grep -q "RECORD|$tag|" $OUT/counts.txt 2>/dev/null; then
        echo "REC7D1B|skip=$tag"
    else
        bash $RL/record_cp7.sh $tag 7784 $EP $seed 7911 | tee -a $OUT/counts.txt
    fi
    total=$(cat $OUT/7d1b_s*.jsonl | grep -c '"y":[0-9]')
    echo "REC7D1B|job=$job|labelled_total=$total|$(date -u +%FT%TZ)"
    job=$((job + 1))
done
echo "REC7D1B|done=$(date -u +%FT%TZ)|jobs=$job|labelled_total=$total|consults=$(cat $OUT/7d1b_s*.jsonl | grep -c '\"t\":\"consult\"')|y_neg=$(cat $OUT/7d1b_s*.jsonl | grep -c '\"y\":-1')|ends=$(cat $OUT/7d1b_s*.jsonl | grep -c '\"t\":\"end\"')" | tee -a $OUT/counts.txt
