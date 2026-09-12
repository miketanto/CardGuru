#!/bin/bash
# Compile the lane-b worktree's Java into the engine (no driver restart here:
# stop/start drivers with rl/driver_server.sh so a running arm is never
# killed by a compile). Like rl/sync_engine_src.sh but sourced from the
# worktree and without the pkill.
[ -f ~/.profile ] && . ~/.profile
set -eu
LB=${LANE_B:-/mnt/c/Users/sutanto4/Documents/CardGuru-lane-b}
MAGE=/home/user/mage
[ -f "$MAGE/.rl_ready" ] || { echo "engine not built - run rl/setup_engine.sh"; exit 1; }
cp "$LB"/rl/xmage-src/*.java "$MAGE/Mage.Tests/src/test/java/org/mage/test/benchmark/rl/"
cd "$MAGE"
mvn -q -pl Mage.Tests -DskipTests -o test-compile 2>&1 | grep -v '^\[INFO\]' | head -40
echo "SYNC|OK|Mage.Tests recompiled from $LB"
