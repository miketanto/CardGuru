#!/bin/bash
# Compile the lane-b worktree's Java into the engine (no driver restart here:
# stop/start drivers with rl/driver_server.sh so a running arm is never
# killed by a compile). Like rl/sync_engine_src.sh but sourced from the
# worktree and without the pkill.
[ -f ~/.profile ] && . ~/.profile
set -eu
LB=${LANE_B:-/mnt/c/Users/sutanto4/Documents/CardGuru}
MAGE=/home/user/mage
[ -f "$MAGE/.rl_ready" ] || { echo "engine not built - run rl/setup_engine.sh"; exit 1; }
cp "$LB"/rl/xmage-src/*.java "$MAGE/Mage.Tests/src/test/java/org/mage/test/benchmark/rl/"
cd "$MAGE"
RC=0
mvn -q -pl Mage.Tests -DskipTests -o test-compile > /tmp/sync_lane_b.log 2>&1 || RC=$?
grep -v '^\[INFO\]' /tmp/sync_lane_b.log | head -40
[ $RC = 0 ] || { echo "SYNC|FAIL|compile rc=$RC"; exit 1; }
echo "SYNC|OK|Mage.Tests recompiled from $LB"
