#!/bin/bash
# Summarise a generate-solve-filter run into the numbers the design's
# gates ask for. Reads the sharded gen_*.tsv files, prints one block.
#
#   rl/subgame_summary.sh <outdir> <seed>
set -eu
OUT=${1:-/home/user/CardGuru/rl/artifacts/subgame}
SEED=${2:-11}
FILES=$(ls "$OUT"/gen_s${SEED}_sh*.tsv 2>/dev/null)
[ -n "$FILES" ] || { echo "no gen files for seed $SEED in $OUT"; exit 1; }

echo "== labels =="
cat $FILES | grep '^INST' | cut -f3 | sort | uniq -c | sort -rn

echo
echo "== admission (per shard; shards draw the same stream) =="
grep -h '^# admission' $FILES || echo "(shards still running)"

echo
echo "== solve cost over all solved boards =="
cat $FILES | grep '^INST' | awk -F'\t' '
  {n++; r+=$15; s+=$16; if ($15>maxr) maxr=$15; if ($16>maxs) maxs=$16}
  END {if (n) printf "boards=%d  meanReplays=%.0f  maxReplays=%d  meanSecs=%.1f  maxSecs=%.1f\n",
        n, r/n, maxr, s/n, maxs}'

echo
echo "== the family (HOLD + SWING: unique optimal class) =="
cat $FILES | grep '^INST' | awk -F'\t' '$3=="HOLD"||$3=="SWING"' |
  awk -F'\t' '{printf "%-12s %-6s A:%s life  %s (%s filler)  |  B:%s life  %s (%s filler)  |  opt=%s rand=%s\n",
       $2,$3,$5,$7,$6,$8,$10,$9,$13,$14}'

echo
echo "== stats-only baselines on the family =="
cat $FILES | grep '^INST' | awk -F'\t' '$3=="HOLD"||$3=="SWING"{print $17}' |
  tr ',' '\n' | awk -F'=' '{tot[$1]++; ok[$1]+=$2}
    END {for (h in tot) printf "%-12s %d/%d = %.3f\n", h, ok[h], tot[h], ok[h]/tot[h]}' |
  sort

echo
echo "== random-play win rate on the family (gate 2) =="
cat $FILES | grep '^INST' | awk -F'\t' '$3=="HOLD"||$3=="SWING"{print $14}' |
  awk '{n++; s+=$1; if (min==""||$1<min) min=$1; if ($1>max) max=$1}
    END {if (n) printf "n=%d  mean=%.3f  min=%.3f  max=%.3f\n", n, s/n, min, max}'
