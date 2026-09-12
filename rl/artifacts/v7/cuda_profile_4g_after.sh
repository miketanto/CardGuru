#!/bin/bash
# After the edge-bias gather fix: the same 60-step profile at tbptt 16 / ep-batch 2
# (apples to apples with cuda_profile_4g.log) and at the new default ep-batch 8.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
LOG=rl/artifacts/v7/cuda_profile_4g_after.log
echo "$(date +%H:%M:%S) START" >> $LOG
for eb in 2 8; do
    echo "=== profile --steps 60 --tbptt 16 --ep-batch $eb" >> $LOG
    python3 rl/update_profile.py profile --arch v7 --synth --steps 60 --device cuda --threads 1 --tbptt 16 --ep-batch $eb >> $LOG 2>&1
    echo "rc=$?" >> $LOG
done
echo "=== threads --steps 1000 --tbptt 16 --ep-batch 8 (memory + rate at the new defaults)" >> $LOG
python3 rl/update_profile.py threads --arch v7 --synth --steps 1000 --device cuda --threads 1 --tbptt 16 --ep-batch 8 >> $LOG 2>&1
echo "rc=$? $(date +%H:%M:%S) DONE" >> $LOG
