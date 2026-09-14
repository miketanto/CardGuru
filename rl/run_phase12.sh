#!/bin/bash
# Phase 12 runner (rl/PHASE12-CP7.md): the controller rl/phase12.py, resumable (state in
# rl/artifacts/v7/12/state.json). Launch detached from ONE wsl call:
#   setsid nohup bash rl/run_phase12.sh [--hours H] >> /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/12/phase12.log 2>&1 < /dev/null &
# Stop gracefully: bash rl/stop_p12.sh (STOP file); hard kill: bash rl/kill_p12.sh.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
echo "# run_phase12 start $(date -u +%FT%TZ) args=$*"
python3 -u rl/phase12.py "$@"
echo "# run_phase12 exit rc=$? $(date -u +%FT%TZ)"
