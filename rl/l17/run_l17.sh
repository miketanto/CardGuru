#!/bin/bash
# L17 fidelity trial driver (run inside WSL).
#   bash rl/l17/run_l17.sh TAG SELECTOR...
#   e.g. bash rl/l17/run_l17.sh debug20 --games 0-19
#        bash rl/l17/run_l17.sh s200 --sample 200 --seed 17
#        L17_GUIDE=1 bash rl/l17/run_l17.sh s200g --sample 200 --seed 17   (log-guided hidden choices)
# Compiles L17Rebuild.java against the existing /home/user/mage build (pin
# 7554968c + phase9; classpath in rl/l17/classpath.txt = the Mage.Tests test
# classpath), builds specs, runs the JVM in batches of 50 games (the Java side
# skips games already finished, so a restart costs nothing), then analyzes.
# Needs a run dir with db/ and config/ copied from Mage.Tests and "RB Aggro.dck".
#
# Resource caps (local 11 GB WSL box shared with Phase 13, 2026-09-15): one
# harness JVM at a time, -Xmx1536m -XX:+UseSerialGC, nice -n 15; before every
# batch of 50 games, pause 10 min while MemAvailable < 2000 MB or swap used > 1 GB.
set -u
TAG=$1; shift
REPO=$(cd "$(dirname "$0")/../.." && pwd)
RUN=${L17_RUN:-/home/miketanto/l17run}
CP=$(tr '\n' ':' < "$REPO/rl/l17/classpath.txt")
GUIDE=${L17_GUIDE:-0}
[ "$GUIDE" = "1" ] && GFLAG="-Dl17.guide=true" || GFLAG="-Dl17.guide=false"
mkdir -p "$RUN/classes"
javac -nowarn -encoding UTF-8 -d "$RUN/classes" -cp "$CP" "$REPO/rl/l17/L17Rebuild.java" || exit 1
[ -f "$RUN/spec_$TAG.tsv" ] || python3 "$REPO/rl/l17/build_specs.py" "$RUN/spec_$TAG.tsv" "$@" || exit 1
cd "$RUN" || exit 1

mem_ok() {
  local avail swapt swapf
  avail=$(awk '/^MemAvailable/ {print int($2/1024)}' /proc/meminfo)
  swapt=$(awk '/^SwapTotal/ {print int($2/1024)}' /proc/meminfo)
  swapf=$(awk '/^SwapFree/ {print int($2/1024)}' /proc/meminfo)
  echo "$(date +%T) mem avail=${avail}MB swap_used=$((swapt - swapf))MB" >> "$RUN/progress_$TAG.log"
  [ "$avail" -ge 2000 ] && [ $((swapt - swapf)) -le 1024 ]
}

fails=0
for i in $(seq 1 400); do
  until mem_ok; do sleep 600; done
  nice -n 15 java -Xmx1536m -XX:+UseSerialGC -Dfile.encoding=UTF-8 -Dl17.timeoutMs=${L17_TIMEOUT_MS:-120000} $GFLAG \
       -cp "$RUN/classes:$CP" org.mage.test.l17.L17Rebuild "$RUN/spec_$TAG.tsv" "$RUN/out_$TAG.tsv" 50 \
       >> "$RUN/java_$TAG.log" 2>&1
  rc=$?
  echo "$(date +%T) batch $i rc=$rc games_done=$(grep -c '^Z' "$RUN/out_$TAG.tsv")" >> "$RUN/progress_$TAG.log"
  [ $rc -eq 0 ] && break
  if [ $rc -ne 3 ] && [ $rc -ne 4 ]; then fails=$((fails + 1)); [ $fails -ge 5 ] && break; fi
done
python3 "$REPO/rl/l17/analyze.py" "$RUN/spec_$TAG.tsv" "$RUN/out_$TAG.tsv" --tag "$TAG" > "$RUN/summary_$TAG.txt"
echo "L17DONE $TAG" >> "$RUN/progress_$TAG.log"
