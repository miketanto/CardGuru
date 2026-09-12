#!/bin/bash
# 5b round 2: the same decks and echo policies as rl/record_5b.sh with fresh
# seeds (+500) and EP games each, tags 5b2_*, appended to the manifest.
# Assumes the oracle JVM on 7912 is already up (rl/drivers_3d.sh).
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
MAN=$LB/rl/artifacts/v7/5b_manifest.txt
EP=${EP:-6}
echo "# 5b round 2 $(date -u +%Y-%m-%dT%H:%MZ) EP=$EP seeds +500" >> $MAN
i=0
for D in W0Base W1Fly W4Inst W5Trick B1Fast W3Sorc BenchDimir P8Faeries; do
    i=$((i+1))
    DECK=$D PICK=1  EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b2_${D}_p1  7782 7 7912 $EP $((900500 + 1000*i))       | head -1 >> $MAN
    DECK=$D PICK=99 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b2_${D}_p99 7782 7 7912 $EP $((900500 + 1000*i + 100)) | head -1 >> $MAN
    DECK=$D PICK=1 PREFER=2,1 BUDGET=300 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b2_${D}_sf 7782 7 7912 $EP $((900500 + 1000*i + 200)) | head -1 >> $MAN
done
echo "# done round 2 $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
