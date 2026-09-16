#!/bin/bash
# Generate-solve-filter a T1 subgame family, sharded across JVMs.
#
# Every shard draws from the SAME stream (same seed, same admission
# tests) and solves only the instances whose admitted index is its own,
# so the union of shards is exactly the single-JVM run - sharding cannot
# change which boards enter the family.
#
#   rl/subgame_gen.sh <seed> <nAdmitted> <shards> <outdir>
set -eu
SEED=${1:-11}
N=${2:-150}
SHARDS=${3:-3}
OUT=${4:-/home/user/CardGuru/rl/artifacts/subgame}
CAP=${CAP:-12000}
MAGE=/home/user/mage/Mage.Tests
POOL=/home/user/CardGuru/rl/artifacts/subgame/pool_vanilla_v1.tsv

mkdir -p "$OUT"
cd "$MAGE"
CP="target/test-classes:target/classes:$(cat /tmp/cp.txt)"

for s in $(seq 0 $((SHARDS - 1))); do
  java -Dsubgame.replayCap="$CAP" -cp "$CP" \
    org.mage.test.benchmark.rl.SubgameFamily \
    gen "$POOL" "$SEED" "$N" "$s" "$SHARDS" \
    > "$OUT/gen_s${SEED}_sh${s}.tsv" 2> "$OUT/gen_s${SEED}_sh${s}.err" &
done
wait
echo "GEN|DONE|$OUT"
