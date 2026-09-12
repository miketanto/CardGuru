#!/bin/bash
# Phase 3a drivers on the freshly compiled engine: 7910 = v6 arm, 7911 = v7 arm.
# rl.encoderV is a class-init constant, so each arm is its own JVM.
[ -f ~/.profile ] && . ~/.profile
RL=/home/user/CardGuru/rl
FLAGS="-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on"
bash $RL/driver_server.sh stop 7910
bash $RL/driver_server.sh stop 7911
bash $RL/driver_server.sh start 7910 "$FLAGS" || exit 1
bash $RL/driver_server.sh start 7911 "$FLAGS -Drl.encoderV=7" || exit 1
python3 $RL/driver_client.py --port 7910 --ping
python3 $RL/driver_client.py --port 7911 --ping
