#!/bin/bash
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
while pgrep -f "run_7[b].sh" > /dev/null; do sleep 30; done
bash rl/run_7b0.sh >> /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7a/run_7b.log 2>&1
bash rl/run_5d_bm.sh
