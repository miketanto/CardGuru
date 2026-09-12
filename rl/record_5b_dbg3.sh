#!/bin/bash
# 5b: the drifting BenchDimir game with the id diagnostic (fresh JVM so the
# job's rl.noYields=true matches the pinned value), then main-1-passing
# recordings on the decks with bigger bodies / an instant, for damage marked.
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
MAN=$LB/rl/artifacts/v7/5b_manifest.txt
echo "# 5b dbg3 $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
bash $LB/rl/drivers_3d_dbg.sh /tmp/td_p99.txt >/dev/null 2>&1 || { echo "dbg restart failed" >> $MAN; exit 1; }
DECK=BenchDimir PICK=99 EXTRA="-Drl.oracle=true -Drl.trackerDebug=/tmp/td_p99.txt" bash $LB/rl/wire_record.sh 5bx_BenchDimir_p99dbg3 7782 7 7912 8 907100 | head -1 >> $MAN
cp /tmp/td_p99.txt $LB/rl/artifacts/v7/wire3a/5bx_td_p99.log 2>>$MAN
for D in W4Inst BenchDimir P8Faeries; do
    WIRE_ECHO_PASS_MAIN1=1 DECK=$D PICK=99 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5bx_${D}_m2 7782 7 7912 8 912000 | head -1 >> $MAN
done
echo "# done dbg3 $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
