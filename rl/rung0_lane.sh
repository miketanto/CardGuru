#!/bin/bash
# Rung 0 of the curriculum ladder — one lane, either branch.
#
#   bash rl/rung0_lane.sh W0Base W0Twin 4096 0     # white / combat
#   bash rl/rung0_lane.sh B0Base B0Twin 4096 0     # black / threat
#
# Deliberately small. The flagship lane carries ~30 knobs (league, pool,
# PFSP, gating, deck schedules) because it was answering a question about
# league design. Rung 0 is answering "can a from-scratch net learn combat
# in a game with no keywords, no instants and no removal", so the lane is
# a fixed opponent, a fixed deck, and a battery. Anything that could
# explain a result other than learning has been removed rather than
# configured.
#
# WHAT IS FIXED, AND WHY
#   opponent = D0 (scripted heuristic), never adapts. POOLED-ANALYSIS
#     found every prior run plateaued against a fixed population; here
#     that is the intended reading, not a bug - we want to see WHERE a
#     minimal game saturates, and the ceiling above D0 is measured by the
#     battery rather than trained against.
#   agent deck = opponent deck = <BASE>, a mirror, so a win is skill and
#     not a deck edge (the gate showed every ladder mirror inside +-.155
#     of .5 at 40 games).
#   terminal reward only, LR 3e-4, lstmattn cdim 91 - the flagship's
#     from-scratch settings, so rung 0 is comparable to prior phases.
#
# WHAT IS MEASURED
#   vs D0    on <BASE>   the training opponent - learning curve
#   vs D1    on <BASE>   1-ply search. Phase 4 recorded terminal-reward
#                        PPO failing to beat it; rung 0 is the smallest
#                        game in which to re-ask that.
#   vs D0    on <TWIN>   TRANSFER. Same costs, same stat lines, no shared
#                        card. A drop here is card-identity dependence
#                        with no strategic story available.
#   vs CP7   on <BASE>   XMage's shipped alpha-beta AI, held out, never
#                        trained against (PHASE12-XMAGE-AI.md). Run once
#                        at the end - it is a test set, not a signal.
#
# EVERY REPORTED NUMBER IS SEQUENTIAL. Training runs at conc4; the
# battery leaves RL_CONC unset so ratings stay reproducible.
set -u
BASE=${1:?usage: rung0_lane.sh <BASE> <TWIN> [budget] [seed]}
TWIN=${2:?}
BUDGET=${3:-4096}
SEED=${4:-0}
RL=/home/user/CardGuru/rl
OUT=${R0_OUT:-/tmp/rl_rung0_${BASE}_s${SEED}}
PORT=${R0_PORT:-$((7940 + SEED))}
EVERY=${R0_EVERY:-512}      # battery cadence
CHUNK=${R0_CHUNK:-64}       # episodes per driver job
EVAL_G=${R0_EVAL_G:-100}
CP7_G=${R0_CP7_G:-50}
LR=${R0_LR:-3e-4}
CONC=${R0_CONC:-4}
FEATS=$RL/e2_features.tsv
mkdir -p $OUT

for D in $BASE $TWIN; do cp $RL/$D.dck /home/user/mage/Mage.Tests/; done

INIT=$OUT/init.pt
python3 $RL/p10_init_net.py --out $INIT --seed $((10 + SEED)) 2>/dev/null | tail -1
CKPT=$OUT/agent.pt
[ -s $CKPT ] || cp $INIT $CKPT

# RL_TORCH_THREADS=1 is not optional: three separate branches hit torch
# intra-op oversubscription independently and it is worth 1.54x at conc4
# (POOLED-ANALYSIS.md section 3), more than the verified engine patch.
start_server() {   # $1 extra-flags
    pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py \
        --port $PORT --ckpt $CKPT --seed $SEED --cdim 91 --arch lstmattn \
        --threads $CONC ${1:-} > $OUT/server.log 2>&1 &
    local t=0
    while [ $t -lt 90 ]; do
        grep -q "policy server" $OUT/server.log 2>/dev/null && return 0
        grep -q "Traceback" $OUT/server.log 2>/dev/null && break
        sleep 2; t=$((t + 2))
    done
    echo "R0_FAILED|server|$OUT/server.log"; tail -5 $OUT/server.log; exit 1
}
stop_server() { pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1; }

field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

probe() {   # $1 out $2 opponent $3 deck $4 games $5 seed
    [ -s "$1" ] && return 0
    RL_PERSIST=1 RL_AUTOSTART=1 timeout 5400 bash $RL/run_driver.sh \
        -Drl.episodes=$4 -Drl.agent=rl -Drl.policy=socket -Drl.port=$PORT \
        -Drl.opponent=$2 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$FEATS -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$3.dck -Drl.oppDeck=$3.dck -Drl.stopTurn=60 \
        -Drl.mode=eval -Drl.seed=$5 -Drl.report=0 -Drl.out=$1 \
        > /dev/null 2>&1
}

# 95% band, printed with every rate so nobody reads 100 games as exact
band() { python3 -c "
import math,sys
n=float('$1' or 1); p=float('$2' or 0)
print('%.3f' % (1.96*math.sqrt(max(p*(1-p),1e-9)/n)))"; }

battery() {   # $1 trained
    local tr=$1
    # separate statement: bash expands every word of a `local` line before
    # assigning any of them, so "$tr" here would be unbound under set -u
    local line="R0|$BASE|s$SEED|trained=$tr"
    stop_server                     # eval must not learn from its own games
    start_server                    # (no --lr => inference only)
    local spec
    for spec in "heuristic|$BASE|D0" "search|$BASE|D1" "heuristic|$TWIN|TWIN"; do
        IFS='|' read -r OPP DK LB <<< "$spec"
        local f=$OUT/probe_${LB}_${tr}.txt
        probe "$f" "$OPP" "$DK" "$EVAL_G" $((900000 + tr))
        local wr=$(field $f win_rate)
        line="$line|$LB=${wr:-NA}+-$(band $EVAL_G ${wr:-0})"
    done
    local bo=$(field $OUT/probe_D0_${tr}.txt blockOpportunities)
    local bd=$(field $OUT/probe_D0_${tr}.txt blocksDeclared)
    line="$line|blocks=${bd:-0}/${bo:-0}|turns=$(field $OUT/probe_D0_${tr}.txt turns_per_ep)"
    echo "$line"
    cp $CKPT $OUT/ck_${tr}.pt
    stop_server
}

trained=$(python3 -c "
import torch,sys
try: print(int(torch.load('$CKPT',map_location='cpu',weights_only=False).get('episodes',0)))
except Exception: print(0)" 2>/dev/null || echo 0)
echo "R0_START|$BASE|seed=$SEED|budget=$BUDGET|resume_at=$trained|out=$OUT"

[ "$trained" -eq 0 ] && battery 0

while [ "$trained" -lt "$BUDGET" ]; do
    stop_server
    start_server "--lr $LR"
    local_end=$((trained + EVERY))
    [ "$local_end" -gt "$BUDGET" ] && local_end=$BUDGET
    while [ "$trained" -lt "$local_end" ]; do
        RL_PERSIST=1 RL_AUTOSTART=1 RL_CONC=$CONC timeout 3600 \
        bash $RL/run_driver.sh \
            -Drl.episodes=$CHUNK -Drl.agent=rl -Drl.policy=socket \
            -Drl.port=$PORT -Drl.opponent=heuristic \
            -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS -Drl.noYields=true \
            -Drl.consultBudget=4000 -Drl.deck=$BASE.dck \
            -Drl.oppDeck=$BASE.dck -Drl.stopTurn=60 -Drl.mode=train \
            -Drl.seed=$((80000000 + SEED * 1000000 + trained)) \
            -Drl.report=0 > /dev/null 2>&1
        trained=$((trained + CHUNK))
    done
    battery $trained
done

# The held-out instrument, once, at the end. Training against it would
# destroy the only externally uncontaminated number this project has.
stop_server
start_server
probe "$OUT/probe_CP7_final.txt" cp7 "$BASE" "$CP7_G" 950000
wr=$(field $OUT/probe_CP7_final.txt win_rate)
echo "R0|$BASE|s$SEED|FINAL|CP7=${wr:-NA}+-$(band $CP7_G ${wr:-0})|games=$CP7_G"
stop_server
echo "R0_DONE|$BASE|s$SEED|trained=$trained|out=$OUT"
