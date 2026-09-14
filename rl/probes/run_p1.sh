#!/bin/bash
# Phase 9 / P1: card-swap counterfactual on five subjects, W0Base + Dimir consult sets.
cd /home/user/CardGuru || exit 1
A=rl/artifacts/v7
python3 rl/probes/cardswap.py --out $A/9 \
  --ckpt init=$A/9/init.pt --ckpt C1s0=$A/7c1/s0/ck_2048.pt --ckpt L0=$A/7l/L0/ck_3072.pt \
  --ckpt BC=$A/7d2/bc.pt --ckpt DIM=$A/8ab/s0/ck_512.pt \
  "$A/wire3a/7c_W0Base_*.jsonl" "$A/wire3a/7c_BenchDimir_*.jsonl"
