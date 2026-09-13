#!/bin/bash
# Stop driver JVMs that no lane uses (each is 3.4 GB RSS on an 11 GB box).
#   bash rl/stop_idle_drivers.sh <port>...
[ -f ~/.profile ] && . ~/.profile
for p in "$@"; do bash /home/user/CardGuru/rl/driver_server.sh stop $p > /dev/null 2>&1; echo "driver $p stopped"; done
sleep 2
echo "left: $(pgrep -fa 'RLDriverServe[r]' | grep -o 'port [0-9]*' | tr '\n' ' ') avail_mb=$(free -m | awk '/Mem/{print $7}')"
