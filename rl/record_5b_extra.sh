#!/bin/bash
# 5b extras, in one detached run (each JVM restart pins class-init constants
# from its FIRST job, so the order matters):
#   1. 7912 restarted with -Drl.trackerDebug; first job = the drifting
#      recording 5b_BenchDimir_p99 (seed 907100) replayed -> /tmp/td_p99.txt
#   2. 7912 restarted again; first job carries -Drl.noYields=false so the RL
#      seat is consulted inside combat (damage marked, blocking, lethal-as-is
#      are only visible there): W0Base and B1Fast, PICK=99
#   3. the constructed keyword deck rl/KW7Probe.dck (first strike, double
#      strike, protection, defender, haste, prowess, menace, reach, trample,
#      shroud, an X spell), PICK=1 and spell-first
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
MAN=$LB/rl/artifacts/v7/5b_manifest.txt
echo "# 5b extras $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
bash $LB/rl/drivers_3d_dbg.sh /tmp/td_p99.txt >/dev/null 2>&1 || { echo "dbg restart 1 failed" >> $MAN; exit 1; }
DECK=BenchDimir PICK=99 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5bx_BenchDimir_p99dbg 7782 7 7912 8 907100 | head -1 >> $MAN
cp /tmp/td_p99.txt $LB/rl/artifacts/v7/wire3a/5bx_td_p99.log
bash $LB/rl/drivers_3d_dbg.sh /tmp/td_ny.txt >/dev/null 2>&1 || { echo "dbg restart 2 failed" >> $MAN; exit 1; }
for D in W0Base B1Fast; do
    DECK=$D PICK=99 EXTRA="-Drl.oracle=true -Drl.noYields=false" bash $LB/rl/wire_record.sh 5bx_${D}_ny 7782 7 7912 8 910000 | head -1 >> $MAN
done
DECK=KW7Probe PICK=1 EXTRA="-Drl.oracle=true -Drl.noYields=false" bash $LB/rl/wire_record.sh 5bx_KW7Probe_p1 7782 7 7912 8 911000 | head -1 >> $MAN
DECK=KW7Probe PICK=1 PREFER=2,1 BUDGET=300 EXTRA="-Drl.oracle=true -Drl.noYields=false" bash $LB/rl/wire_record.sh 5bx_KW7Probe_sf 7782 7 7912 8 911200 | head -1 >> $MAN
DECK=KW7Probe PICK=99 EXTRA="-Drl.oracle=true -Drl.noYields=false" bash $LB/rl/wire_record.sh 5bx_KW7Probe_p99 7782 7 7912 8 911100 | head -1 >> $MAN
echo "# done extras $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
