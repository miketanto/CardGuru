#!/bin/bash
# 5d levers (V7-VALIDATION §5d pre-registration): the same B0Base/B0Twin 256-episode lane
# as rl/run_5d.sh, on the mana-ability-filter build (both arms, so the consult budget is
# the same on each side), three arms:
#   v6    = ENC 6 control on the filter build
#   v7    = ENC 7, --device cuda (5d as run)
#   v7bm  = ENC 7, --device cuda --batch-max 4 (the play-side lever)
# RL_DUMP_BUF captures the first update's real buffer of each v7 arm for
# rl/update_profile.py --arch v7 (the update-side question). Quantities: rl/tp_5d.py <dir>.
# Resumable: an arm with a train.csv in $ART is skipped.
# Launch: setsid nohup bash rl/run_5d_bm.sh > /mnt/c/.../rl/artifacts/v7/5d/run_5d_bm.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/5d
mkdir -p $ART
memlog() {
    while [ -f "$1/.running" ]; do
        used=$(free -m | awk '/Mem:/{print $3}')
        jvm=$(ps -C java -o rss= | awk '{s+=$1} END{print int(s/1024)}')
        srv=$(ps -eo rss,args | awk '/policy_serve[r].py/{s+=$1} END{print int(s/1024)}')
        gpu=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
        echo "$(date +%s) used=$used jvm=$jvm srv=$srv gpu=${gpu:-NA}" >> "$1/mem.log"
        sleep 5
    done
}
run_arm() {   # $1 tag  $2 encoder version  $3 server extra
    local OUT=/tmp/rl_5d_$1
    if [ -s $ART/$1/train.csv ]; then echo "5D|arm=$1|skip=done"; return; fi
    rm -rf $OUT; mkdir -p $OUT; touch $OUT/.running
    memlog $OUT &
    local MP=$!
    echo "5D|arm=$1|enc=$2|extra=$3|start=$(date -u +%FT%TZ)"
    RL_DUMP_BUF=$OUT/rl_buf.pt \
    R0_ENCODER_V=$2 R0_EVERY=256 R0_CHUNK=64 R0_EVAL_G=4 R0_CP7_G=0 R0_CONC=4 \
    R0_SRVEXTRA="--device cuda $3" R0_OUT=$OUT RL_LOCK_STATS=1 \
    bash $RL/rung0_lane.sh B0Base B0Twin 256 0 > $OUT/lane.log 2>&1
    echo "5D|arm=$1|rc=$?|end=$(date -u +%FT%TZ)"
    rm -f $OUT/.running; wait $MP 2>/dev/null
    [ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
    mkdir -p $ART/$1; cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $OUT/mem.log $ART/$1/ 2>/dev/null
    grep -h 'RL|summary\|RL|ipc' /tmp/rl_p9/driver_server_*.log 2>/dev/null | tail -4 > $ART/$1/driver_tail.txt
    python3 $RL/tp_5d.py $ART/$1 2>&1 | tail -12 > $ART/$1/tp.txt
    grep 'R0_\|R0|' $OUT/lane.log | tail -3
}
run_arm v6f 6 ""
run_arm v7f 7 ""
run_arm v7bm 7 "--batch-max 4"
echo "5D|done=$(date -u +%FT%TZ)"
