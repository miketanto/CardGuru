#!/bin/bash
# Re-run gate 1 on instances whose +delta solve ran out of CLOCK rather
# than out of answer.
#
# Why this exists: gate 1 adds filler, and replays roughly triple per two
# extra cards while each replay also gets longer, so a wall-clock budget
# sized for generation is far too small for the gate. The first gate-1
# pass raised subgame.replayCap to 200,000 and left subgame.solveSecs at
# its 90 s default - so 11 of 28 instances came back at exactly 90.0 s
# with an empty optimal set, which is NOT a failed gate, it is no
# measurement at all. Reporting those as instability would have been a
# fabricated finding.
#
#   rl/subgame_gate1_retry.sh <retryFile> <outdir> [delta] [budgetSecs] [shards]
set -eu
FAM=$1
OUT=${2:-/home/user/CardGuru/rl/artifacts/subgame}
DELTA=${3:-2}
BUDGET=${4:-900}
SHARDS=${5:-3}
MAGE=/home/user/mage/Mage.Tests
POOL=/home/user/CardGuru/rl/artifacts/subgame/pool_vanilla_v1.tsv
CP="target/test-classes:target/classes:$(cat /tmp/cp.txt)"

HDR=$(head -1 "$FAM")
TMP=$(mktemp -d)
grep '^INST' "$FAM" | split -n r/$SHARDS -d - "$TMP/part"
for p in "$TMP"/part*; do
  { echo "$HDR"; cat "$p"; } > "$p.tsv"
done

cd "$MAGE"
i=0
for p in "$TMP"/part*.tsv; do
  # stagger: three JVMs opening the H2 card DB at once lose a lock race
  # and the loser dies while the others run on
  [ "$i" -gt 0 ] && sleep 25
  java -Dsubgame.replayCap=2000000 -Dsubgame.solveSecs="$BUDGET" -cp "$CP" \
    org.mage.test.benchmark.rl.SubgameFamily gate1 "$POOL" "$p" "$DELTA" \
    > "$OUT/gate1retry_d${DELTA}_$i.tsv" 2> "$OUT/gate1retry_d${DELTA}_$i.err" &
  i=$((i + 1))
done
wait
echo "GATE1RETRY|DONE|$OUT"
