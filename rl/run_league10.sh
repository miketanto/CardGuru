#!/bin/bash
# Phase 10 B1: the league controller, detached (rl/PHASE10-LEAGUE.md).
# Launch (inside ONE wsl call, keepalive session already open):
#   setsid nohup bash rl/run_league10.sh > /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/10/league10.log 2>&1 < /dev/null &
# Extra args pass through to rl/league10.py (e.g. the smoke's --tag smoke ...).
# Resumable: rerun the same line; clean stop: touch rl/artifacts/v7/10/STOP.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
echo "L10|wrapper|start=$(date -u +%FT%TZ)|args=$*"
python3 -u rl/league10.py "$@"
echo "L10|wrapper|rc=$?|end=$(date -u +%FT%TZ)"
