#!/bin/bash
# The oracle arm for 3d: rl.oracle is a class-init constant like rl.encoderV,
# so -Drl.oracle=true needs its own JVM. Port 7912 = v7 + oracle. The v6 arm
# on 7910 is stopped first to keep three JVMs from sharing 11 GB with the GPU
# job; rl/drivers_3a.sh brings 7910/7911 back.
[ -f ~/.profile ] && . ~/.profile
RL=/home/user/CardGuru/rl
FLAGS="-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on"
bash $RL/driver_server.sh stop 7910
bash $RL/driver_server.sh stop 7912
bash $RL/driver_server.sh start 7912 "$FLAGS -Drl.encoderV=7 -Drl.oracle=true" || exit 1
python3 $RL/driver_client.py --port 7912 --ping
