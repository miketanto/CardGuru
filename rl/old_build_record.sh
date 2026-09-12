#!/bin/bash
# Control for the 3a byte-identity gate: compile the UNPATCHED engine sources
# (main checkout, /home/user/CardGuru/rl/xmage-src = v6 as merged) and record
# the same seeded games twice on one driver JVM, so the run-to-run noise of
# the old build is measured with the same tool as the old-vs-new difference.
# Afterwards re-run rl/sync_lane_b.sh + rl/drivers_3a.sh to return to lane-b.
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru-lane-b
bash $RL/sync_engine_src.sh || exit 1          # copies main's rl/xmage-src, kills drivers, recompiles
bash $RL/driver_server.sh stop 7911
bash $RL/driver_server.sh start 7910 "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on" || exit 1
bash $LB/rl/wire_record.sh v6_old2a 7777 6 7910 3 | head -1
bash $LB/rl/wire_record.sh v6_old2b 7777 6 7910 3 | head -1
