#!/bin/bash
# 4-game smoke of rl/rung0_lane_league.sh after the start_server race fix: from C1 s0
# ck_2048, ONE 64-episode league chunk (frozen opponents ck_1024/ck_2048), batteries of
# 4 games at +0 and after the chunk (the battery-after-training path that produced the
# NA rows). Own ports (7951 / 7960), driver 7912, state /tmp/rl_7l_smoke.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
rm -rf /tmp/rl_7l_smoke
R0_ENCODER_V=7 R0_EVERY=64 R0_CHUNK=64 R0_EVAL_G=4 R0_CP7_G=0 R0_CONC=4 R0_LR=3e-5 RL_LOCK_STATS=1 \
RL_DRIVER_PORT=7912 R0_BATTERY_START=1 R0_PORT=7951 R0_OPP_PORT=7960 \
R0_INIT=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s0/ck_2048.pt \
R0_OPP_CKPTS=/tmp/rl_7c1_s0/ck_1024.pt,/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/7c1/s0/ck_2048.pt \
R0_SRVEXTRA="--device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm auto --target-kl 0.02 --argmax-classes" \
R0_OUT=/tmp/rl_7l_smoke bash rl/rung0_lane_league.sh W0Base W0Twin 2112 0 2>&1 | grep '^R0'
echo "SMOKEL|rc=${PIPESTATUS[0]}|opp_conns=$(grep -c 'conn:' /tmp/rl_7l_smoke/opp_server_all.log /tmp/rl_7l_smoke/opp_server.log 2>/dev/null | paste -sd' ')|train_lines=$(grep -c '^TRAIN' /tmp/rl_7l_smoke/server_all.log 2>/dev/null)|$(grep -o 'wins=[0-9]*\|episodes=[0-9]*' /tmp/rl_7l_smoke/probe_D0_2112.txt 2>/dev/null | paste -sd' ')"
