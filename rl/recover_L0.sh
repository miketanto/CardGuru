#!/bin/bash
# Recover L0's NA battery points one at a time (server 7948 / driver 7914; same game
# seeds as the lane): ck_2560 then ck_3072 from /tmp/rl_7l_L0/. Resumable.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
OUT=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7l/L0_rebat; mkdir -p $OUT
for tr in 2560 3072; do
    if grep -q "trained=$tr|" $OUT/rows.txt 2>/dev/null; then echo "RECOVER|skip|$tr"; continue; fi
    echo "RECOVER|start|$tr|$(date -u +%FT%TZ)|free_mb=$(free -m | awk '/Mem/{print $7}')"
    bash rl/battery_ck.sh /tmp/rl_7l_L0/ck_$tr.pt $OUT $tr 7948 7914 | grep '^R0|' | tee -a $OUT/rows.txt
done
bash rl/driver_server.sh stop 7914 > /dev/null 2>&1
echo "RECOVER|done|$(date -u +%FT%TZ)"
