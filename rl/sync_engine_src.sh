#!/bin/bash
# Re-overlay rl/xmage-src into the built checkout and recompile ONLY
# Mage.Tests. The reactor install is the slow part of setup_engine.sh
# and nothing in it changes when an rl/ source does, so an edit to
# RLPlayer/StateEncoder costs a Mage.Tests compile, not a full build.
set -eu
RL=/home/user/CardGuru/rl
MAGE=/home/user/mage
[ -f "$MAGE/.rl_ready" ] || { echo "engine not built - run rl/setup_engine.sh"; exit 1; }

# a driver JVM pins rl.encoderV and friends at class init AND holds the
# old classes open; recompiling under a live server is how you get a
# mixed-class run that looks like a result
pkill -f "[R]LDriverServer" 2>/dev/null || true
sleep 1

cp "$RL"/xmage-src/*.java \
   "$MAGE/Mage.Tests/src/test/java/org/mage/test/benchmark/rl/"
cp "$RL"/*.dck "$MAGE/Mage.Tests/" 2>/dev/null || true

cd "$MAGE"
mvn -q -pl Mage.Tests -DskipTests -o test-compile
echo "SYNC|OK|Mage.Tests recompiled"
