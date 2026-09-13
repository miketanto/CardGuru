#!/bin/bash
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
while pgrep -f "chai[n].sh" > /dev/null; do sleep 20; done
echo "5D|rerun v7f $(date -u +%FT%TZ)"
bash rl/run_5d_bm.sh
