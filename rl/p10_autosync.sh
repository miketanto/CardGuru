#!/bin/bash
# Phase 10: push the lane's artifacts to the branch every time it
# advances, so a reclaimed container costs one interval instead of a
# checkpoint.
#
# This exists because Phase 10's container WAS reclaimed during an idle
# gap: /tmp went with it, and the ~1400 episodes trained since the last
# checkpoint sync were lost. The repo working tree lives in the same
# container, so syncing to it is not protection - only a PUSH is.
#
# Serialized against the session's own git usage with flock, and it
# commits only when something actually changed.
#
# Usage: bash rl/p10_autosync.sh [outdir] [every_episodes] [poll_sec]
set -u
OUT=${1:-/tmp/rl_p10_flagship_s0}
EVERY=${2:-512}
POLL=${3:-60}
RL=/home/user/CardGuru/rl
BRANCH=$(cd /home/user/CardGuru && git rev-parse --abbrev-ref HEAD)
LAST=-1
while true; do
    T=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    if [ "$T" -ge $((LAST + EVERY)) ] 2>/dev/null; then
        (
          flock 9
          cd /home/user/CardGuru
          bash $RL/p10_sync_artifacts.sh "$OUT" > /dev/null 2>&1
          git add -A rl/artifacts/tmp/$(basename $OUT) > /dev/null 2>&1
          if ! git diff --cached --quiet; then
              git commit -q -m "P10 autosync: lane state at ${T} episodes

Artifacts pushed at gate cadence so a reclaimed container costs one
interval rather than a checkpoint (see rl/p10_autosync.sh).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Th7YSKqnRg7kEtEetSNBdk" \
                 > /dev/null 2>&1
              for i in 1 2 3; do
                  git push origin "$BRANCH" > /dev/null 2>&1 && break
                  sleep $((2 ** i))
              done
              echo "P10AUTOSYNC|trained=${T}|pushed"
          fi
        ) 9>/tmp/.p10_git.lock
        LAST=$T
    fi
    sleep $POLL
done
