#!/bin/bash
# 5b: compile the id diagnostic into the watcher, restart 7912 with the debug
# flag, first job = W4Inst with -Drl.noYields=false (pins NO_YIELDS=false: the
# RL seat is consulted on the opponent's turn with damaged blockers on board),
# then the drifting BenchDimir game with -Drl.trackerDebug on the job.
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
MAN=$LB/rl/artifacts/v7/5b_manifest.txt
echo "# 5b dbg2 $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
bash $LB/rl/sync_lane_b.sh > /tmp/sync_5b.log 2>&1 || { echo "compile failed (see /tmp/sync_5b.log)" >> $MAN; exit 1; }
bash $LB/rl/drivers_3d_dbg.sh /tmp/td_p99.txt >/dev/null 2>&1 || { echo "dbg restart failed" >> $MAN; exit 1; }
DECK=W4Inst PICK=99 EXTRA="-Drl.oracle=true -Drl.noYields=false" bash $LB/rl/wire_record.sh 5bx_W4Inst_ny 7782 7 7912 8 913000 | head -1 >> $MAN
DECK=BenchDimir PICK=99 EXTRA="-Drl.oracle=true -Drl.trackerDebug=/tmp/td_p99.txt" bash $LB/rl/wire_record.sh 5bx_BenchDimir_p99dbg3 7782 7 7912 8 907100 | head -1 >> $MAN
cp /tmp/td_p99.txt $LB/rl/artifacts/v7/wire3a/5bx_td_p99.log 2>>$MAN
echo "# done dbg2 $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
