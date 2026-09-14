#!/bin/bash
# Phase 11 B2: the drill-down continuation (rl/PHASE11-DRILL.md Part B2) = rl/league11.py seeded
# from the Phase 10 state (M_D, M_L, X_D, X_L train from their Phase 10 lane state, copied to
# /tmp/rl_11_*; M_W frozen at M_W_04096 as a cross-deck pool member).
# Launch (inside ONE wsl call, keepalive session open):
#   setsid nohup bash rl/run_drill11.sh > /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/11/drill/league11.log 2>&1 < /dev/null &
# Clean stop: touch rl/artifacts/v7/11/drill/STOP. Resumable: rerun the same line (state.json in the art dir wins).
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
echo "L11|wrapper|start=$(date -u +%FT%TZ)|args=$*"
python3 -u rl/league11.py --from-state /mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/10/state.json "$@"
echo "L11|wrapper|rc=$?|end=$(date -u +%FT%TZ)"
