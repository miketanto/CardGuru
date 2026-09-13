#!/bin/bash
# Phase 8 A2 smoke of rl/rung0_lane_league.sh R0_OPP_SPEC: from C1 s0 ck_2048, three
# 64-episode blocks (R0_EVERY=64) rotating heuristic:BenchDimir / cp7:BenchBurn /
# rl(ck_2048):BenchDimir, batteries of 4 games at +0 and after each block. Own ports
# (7951 / 7960), driver 7912, state /tmp/rl_8_smoke. Prints the R0 lines and, per
# training job, the opponent and oppDeck the driver reported (jobs.log).
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
rm -rf /tmp/rl_8_smoke
CK=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s0/ck_2048.pt
R0_ENCODER_V=7 R0_EVERY=64 R0_CHUNK=64 R0_EVAL_G=4 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 RL_LOCK_STATS=1 \
RL_DRIVER_PORT=7912 R0_BATTERY_START=1 R0_PORT=7951 R0_OPP_PORT=7960 \
R0_INIT=$CK \
R0_OPP_SPEC="heuristic::BenchDimir.dck,cp7::BenchBurn.dck,rl:$CK:BenchDimir.dck" \
R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm auto --target-kl 0.02 --argmax-classes" \
R0_OUT=/tmp/rl_8_smoke bash rl/rung0_lane_league.sh W0Base W0Twin 2240 0 2>&1 | grep '^R0' | cut -c1-220
echo "SMOKEX|rc=${PIPESTATUS[0]}|opp_conns=$(grep -c 'conn:' /tmp/rl_8_smoke/opp_server_all.log /tmp/rl_8_smoke/opp_server.log 2>/dev/null | paste -sd' ')|train_lines=$(grep -c '^TRAIN' /tmp/rl_8_smoke/server_all.log 2>/dev/null)"
grep -o 'wins=[0-9]*\|episodes=[0-9]*\|stalls=[0-9]*\|opponent=[a-z0-9]*\|oppDeck=[A-Za-z0-9]*.dck\|games_per_sec=[0-9.]*' /tmp/rl_8_smoke/jobs.log | paste -sd' ' | sed 's/episodes=/\nJOB episodes=/g'
