#!/bin/bash
# 7d: a lane battery row can come out NA (all three probe jobs refused by the driver
# in 0.0 s; seen on L0 at 2560 while three lanes shared the box - cause not captured,
# the lane discards the client's RLJOB|error line). The checkpoint is on disk, so the
# point is recovered by re-running the battery outside the lane with the same game
# seeds:  bash rl/fill_na_batteries.sh <lane dir> <out dir> [server port=7948] [driver port=7914]
# For every R0| row of <lane dir>/lane.log with D0=NA and a ck_<tr>.pt, runs
# rl/battery_ck.sh into <out dir> (skips probes that exist) and appends the row to
# <out dir>/rows.txt. Does not touch the lane.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
LANE=${1:?lane dir}; OUT=${2:?out dir}; PORT=${3:-7948}; DPORT=${4:-7914}
mkdir -p $OUT
for tr in $(grep -o 'trained=[0-9]*|ck_eps=[0-9]*|D0=NA' $LANE/lane.log | cut -d'|' -f1 | cut -d= -f2 | sort -un); do
    [ -s $LANE/ck_$tr.pt ] || { echo "FILLNA|no ckpt for $tr"; continue; }
    if grep -q "trained=$tr|" $OUT/rows.txt 2>/dev/null; then echo "FILLNA|skip|$tr"; continue; fi
    line=$(bash $RL/battery_ck.sh $LANE/ck_$tr.pt $OUT $tr $PORT $DPORT | grep '^R0|')
    echo "$line" | tee -a $OUT/rows.txt
done
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
echo "FILLNA|done|$LANE"
