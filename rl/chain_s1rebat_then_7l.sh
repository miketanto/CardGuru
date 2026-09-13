#!/bin/bash
# Memory rule (11 GB box: a JVM is 3.4 GB, a server 1.7 GB): the C1 s1 ck_2048
# re-battery (server 7947 / driver 7913, ~12 min) runs ALONE first, then the L1 lane
# (rl/run_7l.sh: L0 is skipped, its census.txt exists) - L1 needs a JVM + two servers.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
ART=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/rebattery
mkdir -p $ART/s1
if ! grep -q 'trained=2048|' $ART/s1/rows.txt 2>/dev/null; then
    echo "CHAIN|rebat_s1_2048|start=$(date -u +%FT%TZ)"
    line=$(bash rl/battery_ck.sh /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s1/ck_2048.pt $ART/s1 2048 7947 7913 | grep '^R0|')
    echo "s1 $line" | tee -a $ART/s1/rows.txt
    bash rl/driver_server.sh stop 7913 > /dev/null 2>&1
fi
echo "CHAIN|launch_7l|$(date -u +%FT%TZ)|avail_mb=$(free -m | awk '/Mem/{print $7}')"
bash rl/run_7l.sh >> /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7l/run_7l.log 2>&1
echo "CHAIN|7l_done|$(date -u +%FT%TZ)"
