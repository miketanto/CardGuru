#!/bin/bash
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru
bash rl/driver_server.sh start 7911 "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7" | tail -1
bash rl/artifacts/v7/7c_record.sh > /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c/record.log 2>&1
cat /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c/record.log
python3 rl/v7_land_census.py --device cpu --logit-bound 5 --ckpt rl/artifacts/v7/7a/B0/init.pt --ckpt rl/artifacts/v7/7a/B2/ck_256.pt --ckpt rl/artifacts/v7/7a/B3/ck_256.pt rl/artifacts/v7/wire3a/7c_W0Base_p1.jsonl rl/artifacts/v7/wire3a/7c_W0Base_p99.jsonl rl/artifacts/v7/wire3a/7c_W0Base_sf.jsonl 2>&1 | grep LANDCENSUS | tee rl/artifacts/v7/7c/land_census_7a.txt
