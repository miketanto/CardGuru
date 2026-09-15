#!/bin/bash
# L17 fidelity trial driver, cloud instance (this repo's remote session).
#
#   bash rl/l17/run_l17_cloud.sh TAG SELECTOR...
#   e.g. bash rl/l17/run_l17_cloud.sh s200_cloud --sample 200 --seed 17
#        L17_GUIDE=1 bash rl/l17/run_l17_cloud.sh s200g_cloud --sample 200 --seed 17
#        L17_VARIANT=abil bash rl/l17/run_l17_cloud.sh s200_abil --sample 200 --seed 17
#
# Same pipeline as run_l17.sh (which was written for the local 11 GB WSL box
# shared with Phase 13). Differences, all environment:
#   * classpath is rl/l17/classpath_cloud.txt, regenerated on this box with
#     `mvn dependency:build-classpath` -- the same 125 artifacts as the local
#     file, only $HOME differs;
#   * the container is not shared with a training run, so the MemAvailable
#     gate and `nice -n 15` are dropped and the heap is -Xmx3g;
#   * batches of 100 games (the Java side skips games that already have a Z
#     line, so a restart costs nothing).
#
# L17_VARIANT selects the rebuilder variant (see L17Rebuild.java VARIANT):
#   base | abil | choice | oppo | order | resync | all
set -u
TAG=$1; shift
REPO=$(cd "$(dirname "$0")/../.." && pwd)
RUN=${L17_RUN:-/home/user/l17run}
CP=$(tr '\n' ':' < "$REPO/rl/l17/classpath_cloud.txt")
GUIDE=${L17_GUIDE:-0}
VARIANT=${L17_VARIANT:-base}
[ "$GUIDE" = "1" ] && GFLAG="-Dl17.guide=true" || GFLAG="-Dl17.guide=false"
mkdir -p "$RUN/classes"
javac -nowarn -encoding UTF-8 -d "$RUN/classes" -cp "$CP" "$REPO/rl/l17/L17Rebuild.java" || exit 1
[ -f "$RUN/spec_$TAG.tsv" ] || python3 "$REPO/rl/l17/build_specs.py" "$RUN/spec_$TAG.tsv" "$@" || exit 1
cd "$RUN" || exit 1

fails=0
for i in $(seq 1 400); do
  java -Xmx3g -Dfile.encoding=UTF-8 -Dl17.timeoutMs=${L17_TIMEOUT_MS:-120000} \
       $GFLAG -Dl17.variant="$VARIANT" \
       -cp "$RUN/classes:$CP" org.mage.test.l17.L17Rebuild "$RUN/spec_$TAG.tsv" "$RUN/out_$TAG.tsv" 100 \
       >> "$RUN/java_$TAG.log" 2>&1
  rc=$?
  echo "$(date +%T) batch $i rc=$rc games_done=$(grep -c '^Z' "$RUN/out_$TAG.tsv")" >> "$RUN/progress_$TAG.log"
  [ $rc -eq 0 ] && break
  if [ $rc -ne 3 ] && [ $rc -ne 4 ]; then fails=$((fails + 1)); [ $fails -ge 5 ] && break; fi
done
python3 "$REPO/rl/l17/analyze.py" "$RUN/spec_$TAG.tsv" "$RUN/out_$TAG.tsv" --tag "$TAG" > "$RUN/summary_$TAG.txt"
echo "L17DONE $TAG" >> "$RUN/progress_$TAG.log"
