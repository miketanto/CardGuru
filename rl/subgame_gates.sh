#!/bin/bash
# Run the remaining per-family gates over a generated family file.
#
#   gate 1  horizon insensitivity - re-solve every kept instance with
#           +delta filler on both sides; the optimal class must not move
#   gate 3  expressibility - is an optimal action in the candidate list
#           RLPlayer actually selects from, per instance
#
#   rl/subgame_gates.sh <familyFile> <outdir> [delta] [probeSamples]
set -eu
FAM=$1
OUT=${2:-/home/user/CardGuru/rl/artifacts/subgame}
DELTA=${3:-2}
SAMPLES=${4:-200}
MAGE=/home/user/mage/Mage.Tests
POOL=/home/user/CardGuru/rl/artifacts/subgame/pool_vanilla_v1.tsv
CP="target/test-classes:target/classes:$(cat /tmp/cp.txt)"

cd "$MAGE"

# gate 3 needs the v7 candidate generator, which derives CAND_DIM from
# the feature file at class init - without it the arch is a different
# arch (rl/SUBGAME-T1-BUILD.md, wiring notes)
FEAT=-Drl.cardFeatures=/home/user/CardGuru/rl/e2_features.tsv

java -Dsubgame.replayCap=200000 -cp "$CP" \
  org.mage.test.benchmark.rl.SubgameFamily gate1 "$POOL" "$FAM" "$DELTA" \
  > "$OUT/gate1_d${DELTA}.tsv" 2> "$OUT/gate1_d${DELTA}.err" &
G1=$!

java $FEAT -cp "$CP" \
  org.mage.test.benchmark.rl.SubgameFamily probe "$POOL" "$FAM" "$SAMPLES" 0 \
  > "$OUT/gate3_random.tsv" 2> "$OUT/gate3_random.err" &
G3=$!

wait $G1 $G3
echo "GATES|DONE|$OUT"
