#!/bin/bash
# Phase 10 flagship — the convergent run (CHECKPOINT-PHASE10.md 4.2).
#
# One command, so the control arm is the same command with
# P10_DECK_SCHEDULE unset (agent locked to BenchDimir) and a different
# $OUT. Everything else - init, pool seed, gate, cadences, LR - is
# shared, which is what makes the two runs an A/B on the agent-deck
# variable the way 7c was an A/B on the opponent-deck one.
#
#   from-scratch lstmattn (rl/p10_init_net.py, seed 10)
#   BPTT recurrent PPO, LR 3e-4 (7b's scratch setting: no prior to keep)
#   gated PFSP league over the deck-carrying pool (rl/p10_pool_seed.tsv)
#   champion gating every 512 episodes, 50g h2h, ck_6144 seeded champion
#   agent deck rotation: BenchDimir-only -> 4 decks by 8192
#   conc4 fast path for training; every probe that produces a NUMBER WE
#   REPORT stays sequential
#
# Usage: bash rl/p10_flagship.sh [budget=12288] [seed=0]
set -u
BUDGET=${1:-12288}
SEED=${2:-0}
RL=/home/user/CardGuru/rl
INIT=${P10_INIT:-/tmp/rl_p10_scratch_init.pt}

python3 $RL/p10_init_net.py --out "$INIT" 2>/dev/null | tail -1

# --- the league ---------------------------------------------------------
export P7_PFSP=1
export P10_POOL=1
export P10_GATE=1
export P10_GATE_G=50
export P10_POOL_SEED=$RL/p10_pool_seed.tsv
export P10_CHAMPION=/tmp/rl_p7_lstmattn_s0/p7b_champion.pt
export P10_CHAMPION_NAME=p7b_ck6144
export P10_CHAMPION_ELO=1101
# Archetype share, staged. A random-init net cannot learn from games it
# loses 100-0, and every non-mirror row sits near 1000 Elo while the low
# rungs of the ladder (7b ck_0/ck_256/ck_512) are all mirror rows - so
# the deck curriculum opens narrow and widens as the agent can pay for
# it. From 4096 it is 7c's 0.5, i.e. the setting that produced the
# robustness result this run is trying to keep.
export P10_ARCHSHARE=${P10_ARCHSHARE-"0:0.15;1024:0.30;2048:0.40;4096:0.50"}
export P7_LR=${P7_LR:-3e-4}
export P7_RATE=${P7_RATE:-2048}     # full battery + Elo curve cadence
export P7_SNAP=${P7_SNAP:-512}      # snapshot + champion-gate cadence
export P7_CONC=${P7_CONC:-4}
export P7_PERSIST=1
export P7_OUT=${P7_OUT:-/tmp/rl_p10_flagship_s${SEED}}
export P10_MATRIX_DECKS=${P10_MATRIX_DECKS:-P7cSweepControl.dck,M3SelesnyaTokens.dck,M3WhiteWeenie.dck,M3BlueSkies.dck,M3RedRush.dck,M3GreenRamp.dck}

# Agent-side deck rotation (8b's from-init compositional bet), widening
# BenchDimir-heavy -> 4 decks. A deck repeated in a stage is weighted:
# the driver plays episode i with decks[i % n].
#   0     : BenchDimir only              (mirror grounding while the net
#                                         is still learning to play)
#   2048  : 3/4 BenchDimir + DimirBounce (nearest neighbour first)
#   5120  : 2/4 BenchDimir + Bounce + Azorius
#   8192  : 2/5 BenchDimir + Bounce + Azorius + Golgari (4 decks)
export P10_DECK_SCHEDULE=${P10_DECK_SCHEDULE-"0:BenchDimir.dck;2048:BenchDimir.dck,BenchDimir.dck,BenchDimir.dck,P8MetaDimirBounce.dck;5120:BenchDimir.dck,BenchDimir.dck,P8MetaDimirBounce.dck,P8MetaAzorius.dck;8192:BenchDimir.dck,BenchDimir.dck,P8MetaDimirBounce.dck,P8MetaAzorius.dck,P8MetaGolgari.dck"}

echo "P10FLAGSHIP|start|budget=$BUDGET|seed=$SEED|out=$P7_OUT|init=$INIT"
exec bash $RL/league_lane_p7.sh $SEED ${P10_APORT:-7801} ${P10_OPORT:-7802} \
    "$INIT" "$BUDGET"
