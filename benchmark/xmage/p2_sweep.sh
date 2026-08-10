#!/bin/bash
# Phase 2 archetype sweep: 4 decks x {perwindow, yields} x 200 games,
# plus yield-equivalence on control (the counterspell predicate risk).
set -u
cd /home/user/mage
OUT=/tmp/p2_results
mkdir -p $OUT
for deck in BenchBurn BenchMidrange BenchControl BenchTriggers; do
    for mode in perwindow yields; do
        y=false; [ "$mode" = "yields" ] && y=true
        label="${deck#Bench}_${mode}"
        echo "=== $label $(date +%H:%M:%S)"
        timeout 1200 mvn -q -pl Mage.Tests surefire:test \
            -Dtest='P2DecisionDensityBenchmark#benchDensity' \
            -DfailIfNoTests=false \
            -Dbench.deck=${deck}.dck -Dbench.games=200 -Dbench.warmup=5 \
            -Dbench.yields=$y -Dbench.label=$label \
            -Dbench.out=$OUT/${label}.txt > $OUT/${label}.log 2>&1
        tail -c 200 $OUT/${label}.txt 2>/dev/null | head -2
    done
done
echo "=== equivalence: control $(date +%H:%M:%S)"
timeout 1200 mvn -q -pl Mage.Tests surefire:test \
    -Dtest='P2DecisionDensityBenchmark#yieldEquivalence' \
    -DfailIfNoTests=false -Dbench.deck=BenchControl.dck -Dbench.games=50 \
    > $OUT/equiv_control.log 2>&1
grep -o 'BENCH|P2.equivalence[^<]*' Mage.Tests/target/surefire-reports/TEST-org.mage.test.benchmark.P2DecisionDensityBenchmark.xml | head -1 > $OUT/equiv_control.txt
grep -o 'message="[^"]\{0,200\}' Mage.Tests/target/surefire-reports/TEST-org.mage.test.benchmark.P2DecisionDensityBenchmark.xml | head -1 >> $OUT/equiv_control.txt
echo DONE
