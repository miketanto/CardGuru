#!/bin/bash
# 5b: compile the tracker fix (slots keyed by the main card id), restart the
# oracle JVM (plain, rl/drivers_3d.sh), re-record the two drifting round-1
# recordings under their original tags/seeds, then the 3d check over every
# 5b recording -> rl/artifacts/v7/5b_check3d_fixed.txt (per file + pooled).
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
A=$LB/rl/artifacts/v7
MAN=$A/5b_manifest.txt
echo "# 5b tracker fix $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
bash $LB/rl/sync_lane_b.sh > /tmp/sync_5b_fix.log 2>&1 || { echo "compile failed (see /tmp/sync_5b_fix.log)" >> $MAN; exit 1; }
bash $LB/rl/drivers_3d.sh >/dev/null 2>&1 || { echo "drivers_3d restart failed" >> $MAN; exit 1; }
DECK=BenchDimir PICK=1  EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b_BenchDimir_p1  7782 7 7912 8 907000 | head -1 >> $MAN
DECK=BenchDimir PICK=99 EXTRA="-Drl.oracle=true" bash $LB/rl/wire_record.sh 5b_BenchDimir_p99 7782 7 7912 8 907100 | head -1 >> $MAN
cd /home/user/CardGuru
{
  echo "# per file: handDrift max / returned slots / known_not_in_truth"
  for f in $A/wire3a/5b_*.jsonl $A/wire3a/5b2_*.jsonl $A/wire3a/5bx_*_ny.jsonl $A/wire3a/5bx_*_m2.jsonl $A/wire3a/5bx_KW7Probe_*.jsonl; do
    echo "$(basename $f) $(python3 rl/wire_check_3d.py $f 2>&1 | grep -o 'handDrift max=[0-9]*\|returned.: [0-9]*\|known_not_in_truth.: [0-9]*' | sort -u | tr '\n' ' ')"
  done
  echo "# pooled"
  python3 rl/wire_check_3d.py $A/wire3a/5b_*.jsonl $A/wire3a/5b2_*.jsonl $A/wire3a/5bx_*_ny.jsonl $A/wire3a/5bx_*_m2.jsonl $A/wire3a/5bx_KW7Probe_*.jsonl 2>&1
} > $A/5b_check3d_fixed.txt
echo "# done tracker fix $(date -u +%Y-%m-%dT%H:%MZ)" >> $MAN
