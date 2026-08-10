#!/bin/bash
# B4: parallel process scaling for B3RandomPolicyBenchmark.
# Launches P concurrent surefire JVMs, each running GAMES games, with
# separate report dirs; samples peak RSS; prints per-P summary lines.
set -u
cd /home/user/mage
GAMES=${GAMES:-15}
for P in 1 2 4 8; do
    rm -rf /tmp/b4_reports_${P}
    pids=()
    t0=$(date +%s.%N)
    for i in $(seq 1 $P); do
        mkdir -p /tmp/b4_reports_${P}/p${i}
        mvn -q -pl Mage.Tests surefire:test -Dtest=B3RandomPolicyBenchmark \
            -DfailIfNoTests=false -Dbench.games=${GAMES} -Dbench.warmup=3 \
            -Dbench.seed=$((1000 * i)) \
            -Dbench.out=/tmp/b4_reports_${P}/p${i}/bench.txt \
            > /tmp/b4_reports_${P}/p${i}/stdout.log 2>&1 &
        pids+=($!)
    done
    # sample java RSS while running
    maxrss=0
    while :; do
        alive=0
        for pid in "${pids[@]}"; do kill -0 "$pid" 2>/dev/null && alive=1; done
        [ "$alive" = "0" ] && break
        rss=$(ps -eo rss,comm | awk '/java/ {s+=$1} END {print s+0}')
        [ "$rss" -gt "$maxrss" ] && maxrss=$rss
        sleep 2
    done
    t1=$(date +%s.%N)
    wall=$(echo "$t1 $t0" | awk '{printf "%.1f", $1-$2}')
    total_gps=0
    for i in $(seq 1 $P); do
        gps=$(grep -ho 'games_per_sec=[0-9.]*' /tmp/b4_reports_${P}/p${i}/bench.txt 2>/dev/null | head -1 | cut -d= -f2)
        [ -z "$gps" ] && gps=$(python3 -c "
import re,glob
for f in glob.glob('/tmp/b4_reports_${P}/p${i}/TEST-*.xml'):
    m=re.search(r'games_per_sec=([0-9.]+)', open(f).read())
    print(m.group(1) if m else 0); break" 2>/dev/null)
        total_gps=$(echo "$total_gps ${gps:-0}" | awk '{print $1+$2}')
    done
    echo "B4|P=${P}|aggregate_games_per_sec=${total_gps}|wall_sec=${wall}|peak_java_rss_mb=$((maxrss/1024))"
done
