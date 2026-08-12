#!/bin/bash
# Restore committed RL artifacts into the /tmp layout the rl/ scripts
# expect. Safe to re-run; existing files are overwritten with the
# committed versions, and datasets are decompressed in place.
set -eu
SRC=$(dirname "$0")/artifacts/tmp
[ -d "$SRC" ] || { echo "no artifacts tree at $SRC"; exit 1; }
cp -rv "$SRC"/. /tmp/
for gz in /tmp/rl_p5_c1/*.ndjson.gz; do
    [ -f "$gz" ] || continue
    gunzip -kf "$gz"
done
echo "restored. checkpoints + curves under /tmp/rl_*, datasets unpacked."
