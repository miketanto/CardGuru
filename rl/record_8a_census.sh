#!/bin/bash
# Phase 8 A1: the Dimir census set - three echo policies (p1 / p99 / spell-first)
# x 8 games on BenchDimir vs the heuristic, driver 7911 (v7 flags), the exact
# 7c_W0Base pattern (rl/artifacts/v7/7c_record.sh). Output rl/artifacts/v7/wire3a/7c_BenchDimir_{p1,p99,sf}.jsonl
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
for P in 1 99; do DECK=BenchDimir PICK=$P bash $LB/rl/wire_record.sh 7c_BenchDimir_p$P 7784 7 7911 8 | head -1; done
DECK=BenchDimir PICK=1 PREFER=2,1 BUDGET=300 bash $LB/rl/wire_record.sh 7c_BenchDimir_sf 7784 7 7911 8 | head -1
echo REC_DONE
