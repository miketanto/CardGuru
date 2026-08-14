#!/bin/bash
# Push rung-0 lane state to the branch every time a battery lands.
#
# The repo working tree lives in the SAME container as /tmp, so copying
# into rl/artifacts is not protection - only a push is. Phase 10 learned
# this the expensive way: the container was reclaimed during an idle gap
# and ~1400 trained episodes went with /tmp.
#
# Unlike p10_autosync.sh this reads progress from the lane's own output
# (the newest ck_*.pt) rather than a trained.txt, because the rung-0 lane
# does not write one and editing a running bash script has corrupted a
# run here before.
#
# Usage: bash rl/rung0_autosync.sh <BASE> [poll_sec]
set -u
BASE=${1:?usage: rung0_autosync.sh <BASE> [poll_sec]}
POLL=${2:-120}
CG=/home/user/CardGuru
DST=$CG/rl/artifacts/rung0/$BASE
BRANCH=$(cd $CG && git rev-parse --abbrev-ref HEAD)
mkdir -p $DST
LAST=""

while true; do
    mkdir -p $DST
    STATE=""
    for d in /tmp/rl_rung0_${BASE}_s[0-9]*; do
        [ -d "$d" ] || continue
        s=$(basename $d)
        mkdir -p $DST/$s
        # probe summaries are small and are the actual result; the net is
        # 5MB, so only the LATEST checkpoint is carried, not every one
        cp $d/probe_*.txt $DST/$s/ 2>/dev/null
        newest=$(ls -t $d/ck_*.pt 2>/dev/null | head -1)
        [ -n "$newest" ] && cp "$newest" $DST/$s/latest.pt 2>/dev/null
        STATE="$STATE $s:$(ls $d/probe_D0_*.txt 2>/dev/null | wc -l)"
    done
    # Regenerate the report ONLY when a battery has landed. Rewriting it
    # every poll left the working tree permanently dirty between syncs -
    # the file changes even when nothing has, so `git status` was never
    # clean and a real uncommitted change would have hidden in the noise.
    if [ "$STATE" != "$LAST" ] && [ -n "$STATE" ]; then
        cp /tmp/rl_rung0_${BASE}_sweep.out $DST/sweep.out 2>/dev/null
        python3 $CG/rl/rung0_report.py --base "$BASE" > $DST/report.txt 2>&1
        (
          flock 9
          cd $CG
          git add -A rl/artifacts/rung0 > /dev/null 2>&1
          if ! git diff --cached --quiet; then
              git commit -q -m "rung0 autosync:$STATE

Batteries pushed as they land so a reclaimed container costs one
interval rather than the run (see rl/rung0_autosync.sh).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Th7YSKqnRg7kEtEetSNBdk" \
                 > /dev/null 2>&1
              for i in 1 2 3; do
                  git push origin "$BRANCH" > /dev/null 2>&1 && break
                  sleep $((2 ** i))
              done
          fi
        ) 9>/tmp/.cardguru_git.lock
        LAST="$STATE"
    fi
    sleep $POLL
done
