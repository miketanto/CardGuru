#!/bin/bash
# 5d: throughput v7 vs v6 on cuda, THROUGHPUT-LOCAL.md §2 protocol, two arms back to back.
# Output: /tmp/rl_5d_v6, /tmp/rl_5d_v7 (train.csv, server.log, server_all.log, mem.log, lane.log)
# then copied to rl/artifacts/v7/5d/. Launch: setsid nohup bash rl/run_5d.sh > /tmp/run_5d.log 2>&1 &
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/5d
mkdir -p $ART
memlog() {   # $1 out dir; samples every 5 s until the lane's marker file disappears
    while [ -f "$1/.running" ]; do
        used=$(free -m | awk '/Mem:/{print $3}')
        jvm=$(ps -C java -o rss= | awk '{s+=$1} END{print int(s/1024)}')
        srv=$(ps -eo rss,args | awk '/policy_serve[r].py/{s+=$1} END{print int(s/1024)}')
        gpu=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
        echo "$(date +%s) used=$used jvm=$jvm srv=$srv gpu=${gpu:-NA}" >> "$1/mem.log"
        sleep 5
    done
}
run_arm() {   # $1 = encoder version
    local OUT=/tmp/rl_5d_v$1
    rm -rf $OUT; mkdir -p $OUT; touch $OUT/.running
    memlog $OUT &
    local MP=$!
    echo "5D|arm=v$1|start=$(date -u +%FT%TZ)"
    R0_ENCODER_V=$1 R0_EVERY=256 R0_CHUNK=64 R0_EVAL_G=4 R0_CP7_G=0 R0_CONC=4 \
    R0_SRVEXTRA="--device cuda" R0_OUT=$OUT RL_LOCK_STATS=1 \
    bash $RL/rung0_lane.sh B0Base B0Twin 256 0 > $OUT/lane.log 2>&1
    echo "5D|arm=v$1|rc=$?|end=$(date -u +%FT%TZ)"
    rm -f $OUT/.running; wait $MP 2>/dev/null
    [ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
    mkdir -p $ART/v$1; cp $OUT/train.csv $OUT/lane.log $OUT/server_all.log $OUT/mem.log $ART/v$1/ 2>/dev/null
    grep -h 'RL|summary\|RL|ipc' /tmp/rl_p9/driver_server_*.log 2>/dev/null | tail -4 > $ART/v$1/driver_tail.txt
    grep 'R0_\|R0|' $OUT/lane.log | tail -5
}
run_arm 6
run_arm 7
echo "5D|done=$(date -u +%FT%TZ)"
