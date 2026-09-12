#!/bin/bash
# Which op costs the update: torch profiler over one v7 update, cuda, 400 steps.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
LOG=rl/artifacts/v7/cuda_profile_4g.log
echo "$(date +%H:%M:%S) START" >> $LOG
python3 rl/update_profile.py profile --arch v7 --synth --steps 60 --device cuda --threads 1 --tbptt 16 --ep-batch 2 >> $LOG 2>&1
echo "rc=$? $(date +%H:%M:%S) DONE" >> $LOG
