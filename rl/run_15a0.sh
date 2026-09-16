#!/bin/bash
# Phase 15 A0 (rl/PHASE15-ARCH.md): the memorisation test, one GPU process.
# 40 games round-robin over the two 13a lanes (H = CP7 vs the heuristic,
# C = the CP7 mirror), 2,000 labelled consults, 40 epochs, no weight decay,
# no early stop; then the value head on the same 40 games' outcomes.
# Resumable: if a0.json exists the run is skipped.
#   bash rl/run_15a0.sh   (launch detached; log rl/artifacts/v7/15/a0/run.log)
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
O=$LB/rl/artifacts/v7/15/a0
mkdir -p $O
cd /home/user/CardGuru
echo "A15|start|$(date -u +%FT%TZ)"
if [ -s $O/a0.json ]; then
    echo "A15|a0|skip"
else
    python3 $RL/p15_a0.py --init $LB/rl/artifacts/v7/13/init_on_s13.pt \
        --out $O --device cuda --games 40 --consults 2000 --epochs 40 \
        $LB/rl/artifacts/v7/13/rec/rec13_H_s13000.jsonl \
        $LB/rl/artifacts/v7/13/rec/rec13_C_s13500.jsonl > $O/a0.log 2>&1
    echo "A15|a0|rc=$?"
fi
grep '^A0|READING\|^A0|policy_final|n=\|^A0|value_final\|^A0|value_data\|^A0|grad_after\|^A0|data' $O/a0.log 2>/dev/null
echo "A15|done|$(date -u +%FT%TZ)"
