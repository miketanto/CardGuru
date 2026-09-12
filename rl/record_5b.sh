#!/bin/bash
# 5b coverage recordings (V7-IMPLEMENTATION-PLAN §2 Phase 5b).
# The driver emits consults only for the RL seat, so "heuristic-vs-heuristic"
# is produced as the echo policy (rl/wire_echo_server.py) on the RL seat vs
# the heuristic opponent, over 8 decks x 3 echo policies x 8 games each, on
# the oracle JVM (port 7912, -Drl.encoderV=7 -Drl.oracle=true) so the same
# recordings serve 5c.  Policies:
#   PICK=1        first non-pass candidate (lands, first spell, first attack/block)
#   PICK=99       last candidate (largest attack subset / block assignment)
#   PREFER=2,1    spell-first, then land (BUDGET=300: it casts every instant
#                 at every consult) - exercises the stack and instants
# Seeds are distinct per (deck, policy) so the game-grouped hold-out never
# sees the same game twice.  Output: rl/artifacts/v7/wire3a/5b_<deck>_<pol>.jsonl
# (gitignored) + rl/artifacts/v7/5b_manifest.txt (committed).
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
MAN=$LB/rl/artifacts/v7/5b_manifest.txt
EP=${EP:-8}
bash $LB/rl/drivers_3d.sh || { echo "drivers_3d failed" >> $MAN; exit 1; }
echo "# 5b recordings $(date -u +%Y-%m-%dT%H:%MZ) EP=$EP port 7912 (v7+oracle) echo policies p1/p99/sf" > $MAN
i=0
for D in W0Base W1Fly W4Inst W5Trick B1Fast W3Sorc BenchDimir P8Faeries; do
    i=$((i+1))
    DECK=$D PICK=1  EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b_${D}_p1  7782 7 7912 $EP $((900000 + 1000*i))       | head -1 >> $MAN
    DECK=$D PICK=99 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b_${D}_p99 7782 7 7912 $EP $((900000 + 1000*i + 100)) | head -1 >> $MAN
    DECK=$D PICK=1 PREFER=2,1 BUDGET=300 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b_${D}_sf 7782 7 7912 $EP $((900000 + 1000*i + 200)) | head -1 >> $MAN
done
echo "# done $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
