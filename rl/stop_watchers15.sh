#!/bin/bash
# Kill leftover Phase 15 WATCHER shells - the until/while loops launched to wait on a
# file or a process count. They do no work, but their argv contains strings like
# p15_a2 / run_15a2 / p15_a1, so any later `pgrep -f` health check matches them and
# reports work that is not running. That is not hypothetical: one such watcher jammed
# chain_15.sh for 20 minutes (its argv matched the chain's own wait pattern), and
# another made a clean box look like it still had a driver up.
#
# This file's name (stop_watchers15) contains none of the patterns below, so it can
# never match its own shell - the CLAUDE.md rule for kill scripts.
#   bash rl/stop_watchers15.sh
set -u
k() { local pat=$1; local pids; pids=$(pgrep -f "$pat"); echo "$pat -> ${pids:-none}"; for p in $pids; do kill -TERM "$p" 2>/dev/null; done; }
# only the waiting shells: an `until ... sleep` or `while ... sleep` loop
k 'until ls .*artifacts/v7/15'
k 'while \[ ! -s .*artifacts/v7/15'
k 'while pgrep -f "p15_'
sleep 2
echo "left: watchers=$(pgrep -fc 'until ls .*artifacts/v7/1[5]|while \[ ! -s .*artifacts/v7/1[5]')"
echo "real work still running: trainers=$(pgrep -fc 'python3 .*p15_[a-z0-9]|python3 .*v7_b[c]\.py') drivers=$(pgrep -fc 'RLDriverServe[r]') servers=$(pgrep -fc 'policy_serve[r]\.py')"
