#!/bin/bash
# 7912 = v7 + oracle + the tracker's event diagnostic (-Drl.trackerDebug is a
# class-init constant like rl.oracle: it needs its own JVM start).
#   bash rl/drivers_3d_dbg.sh [/tmp/td.txt]
[ -f ~/.profile ] && . ~/.profile
RL=/home/user/CardGuru/rl
OUT=${1:-/tmp/td.txt}
FLAGS="-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on"
bash $RL/driver_server.sh stop 7912
rm -f $OUT
bash $RL/driver_server.sh start 7912 "$FLAGS -Drl.encoderV=7 -Drl.oracle=true -Drl.trackerDebug=$OUT" || exit 1
python3 $RL/driver_client.py --port 7912 --ping
