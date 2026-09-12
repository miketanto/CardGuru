#!/bin/bash
# 5b: (1) the tracker drift reproduced with the event diagnostic ON THE JOB
# (the driver server does not forward JVM-level -Drl.* to a class initialised
# during a job: -Drl.trackerDebug must be in EXTRA and the JVM fresh);
# (2) main-1-passing recordings (WIRE_ECHO_PASS_MAIN1=1) so damage marked is
# visible at main-2 consults.  Waits for rl/record_5b_extra.sh to finish.
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
MAN=$LB/rl/artifacts/v7/5b_manifest.txt
until grep -q '# done extras\|failed' $MAN; do sleep 5; done
echo "# 5b dbg+main2 $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
bash $LB/rl/drivers_3d_dbg.sh /tmp/td_p99.txt >/dev/null 2>&1 || { echo "dbg restart failed" >> $MAN; exit 1; }
DECK=BenchDimir PICK=99 EXTRA="-Drl.oracle=true -Drl.trackerDebug=/tmp/td_p99.txt" bash $LB/rl/wire_record.sh 5bx_BenchDimir_p99dbg2 7782 7 7912 8 907100 | head -1 >> $MAN
cp /tmp/td_p99.txt $LB/rl/artifacts/v7/wire3a/5bx_td_p99.log 2>>$MAN
for D in W0Base B1Fast W1Fly; do
    WIRE_ECHO_PASS_MAIN1=1 DECK=$D PICK=99 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5bx_${D}_m2 7782 7 7912 8 912000 | head -1 >> $MAN
done
echo "# done dbg+main2 $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
