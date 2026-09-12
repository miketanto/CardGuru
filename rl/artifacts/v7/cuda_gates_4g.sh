#!/bin/bash
# The two open 4g cuda gates (rl/V7-VALIDATION.md §4g part 2), run once the
# GPU is idle. Output: rl/artifacts/v7/cuda_gates_4g.log (UPDMEM / CONSULT lines).
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
LOG=rl/artifacts/v7/cuda_gates_4g.log
echo "$(date +%H:%M:%S) GATES START $(nvidia-smi --query-gpu=memory.used --format=csv,noheader)" >> $LOG
echo "=== update_profile threads --arch v7 --synth --steps 5000 --device cuda --threads 1" >> $LOG
python3 rl/update_profile.py threads --arch v7 --synth --steps 5000 --device cuda --threads 1 >> $LOG 2>&1
echo "rc=$?" >> $LOG
echo "=== consult_cost --arch v7 --device cuda" >> $LOG
python3 rl/consult_cost.py --arch v7 --device cuda >> $LOG 2>&1
echo "rc=$?" >> $LOG
echo "$(date +%H:%M:%S) GATES DONE" >> $LOG
