#!/bin/bash
# Stop the Phase 15 GPU chain(s) and nothing else.
# This file's name (stop_chain15.sh) contains none of the patterns below, so it can
# never match its own shell - the CLAUDE.md rule that a kill script must not be able
# to kill the shell running it.
#   bash rl/stop_chain15.sh            stop the chain wrappers only (a running step
#                                      - a BC train, a probe - is left to finish)
#   bash rl/stop_chain15.sh --steps    also stop the GPU step it is running
# Every chain step is resumable and skipped when its output exists, so stopping here
# costs the step in flight at worst.
set -u
k() { local pat=$1; local pids; pids=$(pgrep -f "$pat"); echo "$pat -> ${pids:-none}"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; }
k 'chain_1[5]\.sh'
if [ "${1:-}" = --steps ]; then
    k 'python3 .*p15_a1\.py'
    k 'python3 .*p15_a2\.py'
    k 'python3 .*p15_a4\.py'
    k 'python3 .*v7_bc\.py'
    k 'run_15a[24]\.sh'
fi
sleep 3
echo "left: chains=$(pgrep -fc 'chain_1[5]\.sh') a1=$(pgrep -fc 'python3 .*p15_a1\.py') a2=$(pgrep -fc 'python3 .*p15_a2\.py') bc=$(pgrep -fc 'python3 .*v7_bc\.py')"
