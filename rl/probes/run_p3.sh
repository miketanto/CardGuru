#!/bin/bash
# Phase 9 / P3: instant-speed fraction for CP7 (Dimir), DIM (Dimir), the heuristic (opponent rows), and the 7d1b W0Base CP7 reference.
cd /home/user/CardGuru || exit 1
A=rl/artifacts/v7
python3 rl/probes/instant_speed.py --out $A/9 "CP7_dimir=$A/9/rec_cp7_dimir*.jsonl" "DIM_dimir=$A/9/rec_dim_dimir*.jsonl" "CP7_W0Base_7d1b=$A/7d1b/7d1b_s74*.jsonl"
