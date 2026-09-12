#!/bin/bash
# 4g follow-up (pre-registered in V7-VALIDATION.md §4g correction): the same
# update profile at a smaller BPTT window and episode batch, 1,000 steps, to
# separate allocator thrash at the cuda limit from the per-window cost.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
LOG=rl/artifacts/v7/cuda_gates_4g_b.log
echo "$(date +%H:%M:%S) START $(nvidia-smi --query-gpu=memory.used --format=csv,noheader)" >> $LOG
for cfg in "--tbptt 16 --ep-batch 2" "--tbptt 32 --ep-batch 4"; do
    echo "=== update_profile threads --arch v7 --synth --steps 1000 --device cuda --threads 1 $cfg" >> $LOG
    python3 rl/update_profile.py threads --arch v7 --synth --steps 1000 --device cuda --threads 1 $cfg >> $LOG 2>&1
    echo "rc=$?" >> $LOG
done
echo "$(date +%H:%M:%S) DONE" >> $LOG
