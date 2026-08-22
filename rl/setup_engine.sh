#!/bin/bash
# Rebuild the XMage checkout this project's lanes depend on.
#
# The container that ran the v6 work is gone, and /home/user/mage with
# it. Every lane, driver and dump path in rl/ resolves against that
# tree, so nothing that touches the engine runs until it is back.
#
# Recipe is engine-patches/README.md: pin 7554968c, apply
# phase9-engine.patch, overlay rl/xmage-src/ and benchmark/xmage/src/.
#
#   bash rl/setup_engine.sh            # full clone + patch + build
#   ENGINE_SKIP_BUILD=1 bash ...       # clone + patch only
#
# Log: /tmp/engine_setup.log ; marker on success: /home/user/mage/.rl_ready
set -eux

PIN=7554968c
RL=/home/user/CardGuru/rl
BENCH=/home/user/CardGuru/benchmark/xmage/src
MAGE=/home/user/mage

if [ ! -d "$MAGE/.git" ]; then
    rm -rf "$MAGE"
    # blob:none keeps the clone to the trees we actually check out;
    # a full XMage clone is several GB and the session has a fixed
    # disk allowance.
    git clone --filter=blob:none --no-checkout \
        https://github.com/magefree/mage "$MAGE"
fi

cd "$MAGE"
git fetch --filter=blob:none origin "$PIN" || git fetch origin
git checkout -f "$PIN"
git clean -fdx -e Mage.Tests/target -e '*/target'

# 1. engine patches (three files, all flag-gated except the Combat fix)
git apply --verbose "$RL/engine-patches/phase9-engine.patch"

# 2. the RL sources this repo owns
DST="$MAGE/Mage.Tests/src/test/java/org/mage/test/benchmark/rl"
mkdir -p "$DST"
cp "$RL"/xmage-src/*.java "$DST"/

# 3. the benchmark sources (HeuristicPlayer lives here - the opponent)
DST2="$MAGE/Mage.Tests/src/test/java/org/mage/test/benchmark"
mkdir -p "$DST2"
cp "$BENCH"/*.java "$DST2"/

# 4. decks the lanes copy in at run time need a home
cp "$RL"/*.dck "$MAGE/Mage.Tests/" 2>/dev/null || true

if [ "${ENGINE_SKIP_BUILD:-0}" = "1" ]; then
    echo "ENGINE|patched|build skipped"
    exit 0
fi

# 5. build. -DskipTests so the RL driver (a surefire test) is compiled
#    but not run; Mage.Tests needs the full reactor installed first.
cd "$MAGE"
mvn -q -T 1C -DskipTests -Dmaven.javadoc.skip=true install

touch "$MAGE/.rl_ready"
echo "ENGINE|READY|$PIN"
