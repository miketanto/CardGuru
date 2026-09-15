#!/bin/bash
# Phase 13: chain_13bc.sh blocked on its keepalive step - the WSL-side cmd.exe interop process of
# 'cmd.exe /c start /min wsl -e bash -lc "sleep 64800"' did not return (the keepalive itself started).
# Stop ONLY that interop process (pid given as $1, checked to be that cmd.exe line) so the chain proceeds
# to launch rl/phase13.py. The keepalive's own sleep is a separate process and is not touched.
P=${1:?pid}
if ps -o args= -p "$P" | grep -q 'cmd.exe /c start /min wsl'; then
    kill "$P" && echo "UNBLOCK|killed=$P"
else
    echo "UNBLOCK|pid $P is not the cmd.exe interop line - nothing done"
fi
sleep 2
echo "UNBLOCK|keepalives=$(pgrep -fc 'sleep 6480[0]')"
