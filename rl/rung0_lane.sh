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
PORT=${R0_PORT:-$((7940 + SEED))}
EVERY=${R0_EVERY:-512}      # battery cadence
CHUNK=${R0_CHUNK:-64}       # episodes per driver job
EVAL_G=${R0_EVAL_G:-100}
CP7_G=${R0_CP7_G:-50}
LR=${R0_LR:-3e-4}
CONC=${R0_CONC:-4}
FEATS=$RL/e2_features.tsv
# Encoder arm. v1 = the original 24-dim encoder (no combat channels, no
# block context, blockers ordered by card name); v2 = the conditioned
# autoregressive encoder. Both run from ONE build - StateEncoder reads
# -Drl.encoderV at class init - so an A/B between them differs in the
# encoder and nothing else.
ENC=${R0_ENCODER_V:-2}
if [ "$ENC" = "1" ]; then SDIM=24; CDIM=91; else SDIM=32; CDIM=94; fi
ENCFLAGS="-Drl.encoderV=$ENC -Drl.blockAudit=true"
# v6 replaces the flat state with entity tokens, so the ARCH changes too
# (ENCODER-V6-BUILD.md §4c/§4e). Everything else about the lane is
# identical on purpose: same opponent, same decks, same budget, same
# candidate width - the state path is the only thing that moves.
# R0_RELATIONS=0 selects the ablation arm (relations dropped), which is
# what separates "entity rows helped" from "relations helped".
ARCH=lstmattn
V6FLAGS=""
if [ "$ENC" -ge 6 ] 2>/dev/null; then
    ARCH=entattn
    V6FLAGS="--gdim 16 --edim 48 --emax ${R0_EMAX:-96}"
    [ "${R0_RELATIONS:-1}" = "0" ] && V6FLAGS="$V6FLAGS --r0"
    [ -n "${R0_EMAX:-}" ] && ENCFLAGS="$ENCFLAGS -Drl.entityMax=$R0_EMAX"
fi
# THE ATTACK AUDIT IS EVAL-ONLY, and that is a cost decision, not a
# style one. It runs a full minimax attack search per combat on top of
# the one the policy may already have run, and measured over 100 eval
# games it was 584 s of a 763 s run - 76% of wall clock, a 4x slowdown.
# blockAudit is cheap enough to leave on everywhere; this one is not,
# and putting it in ENCFLAGS would have quadrupled every training chunk
# for a number nothing reads during training.
EVALFLAGS="$ENCFLAGS -Drl.attackAudit=true"
# v4's candidates are whole assignments, so the server's 40-slot buffer
# is too small - raw enumeration produced 46 distinct outcomes and
# crashed it mid-run. Pareto filtering cuts the set; this is the belt to
# that braces.
SRVEXTRA=""
[ "$ENC" -ge 4 ] 2>/dev/null && SRVEXTRA="--max-k 64"
# v5's ATTACK candidates are whole subsets and rl.attackMaxCands defaults
# to 64, so the buffer has to clear that too or the server drops
# candidates the policy was meant to be choosing between.
[ "$ENC" -ge 5 ] 2>/dev/null && SRVEXTRA="--max-k 96"
OUT=${R0_OUT:-/tmp/rl_rung0_${BASE}_v${ENC}_s${SEED}}
mkdir -p $OUT

for D in $BASE $TWIN; do cp $RL/$D.dck /home/user/mage/Mage.Tests/; done

# The persistent driver JVM fixes rl.encoderV at StateEncoder class-init,
# so a JVM that has already served one arm CANNOT serve the other. Kill it
# here; RL_AUTOSTART=1 brings up a fresh one on this arm's first job.
pkill -f "[R]LDriverServer" 2>/dev/null
sleep 2

INIT=$OUT/init.pt
INITEXTRA=""
[ "$ARCH" = "entattn" ] && INITEXTRA="--gdim 16 --edim 48"
[ "${R0_RELATIONS:-1}" = "0" ] && [ "$ARCH" = "entattn" ] && INITEXTRA="$INITEXTRA --r0"
python3 $RL/p10_init_net.py --out $INIT --seed $((10 + SEED)) --sdim $SDIM \
    --cdim $CDIM --arch $ARCH $INITEXTRA 2>/dev/null | tail -1
CKPT=$OUT/agent.pt
[ -s $CKPT ] || cp $INIT $CKPT

# RL_TORCH_THREADS=1 is not optional: three separate branches hit torch
# intra-op oversubscription independently and it is worth 1.54x at conc4
# (POOLED-ANALYSIS.md section 3), more than the verified engine patch.
start_server() {   # $1 extra-flags
    pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py \
        --port $PORT --ckpt $CKPT --seed $SEED --sdim $SDIM --cdim $CDIM --arch $ARCH \
        --threads $CONC $SRVEXTRA $V6FLAGS ${1:-} > $OUT/server.log 2>&1 &
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
        $EVALFLAGS -Drl.deck=$3.dck -Drl.oppDeck=$3.dck -Drl.stopTurn=60 \
        -Drl.mode=eval -Drl.seed=$5 -Drl.report=0 -Drl.out=$1 \
        > /dev/null 2>&1
}

# 95% interval, printed with every rate so nobody reads 100 games as
# exact. WILSON, not Wald. The Wald half-width this used to print is
# 1.96*sqrt(p(1-p)/n), which is 0.000 at p=0 and at p=1 - so the
# untrained row of every lane log ever written claims perfect certainty
# about 0/100, and the standing rule since then is Wilson everywhere.
# rung0_report.py already carried the correct one; the lane did not.
band() { [ -z "${2:-}" ] && { echo "[NA]"; return; }
python3 -c "
import math
n=float('$1' or 1); p=float('$2' or 0); z=1.96
k=p*n; d=1+z*z/n
c=(p+z*z/(2*n))/d
h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
print('[%.3f,%.3f]' % (max(0.0,c-h), min(1.0,c+h)))"; }

battery() {   # $1 trained
    local tr=$1
    # DID THE SERVER SURVIVE? The lane counts episodes in bash and the
    # net counts them in the checkpoint. They agree unless the policy
    # server died mid-run - which happened: the entattn arm OOM-killed
    # its server at episode 383 of 512, the lane restarted it from the
    # last checkpoint and carried on toward a battery row it would have
    # labelled 512. A row that says 512 while the net saw 383 is worse
    # than no row, so check the two counters and stop.
    local ck_eps
    ck_eps=$(python3 -c "
import torch
try: print(int(torch.load('$CKPT',map_location='cpu',weights_only=False).get('episodes',0)))
except Exception: print(-1)" 2>/dev/null || echo -1)
    if [ "$tr" -gt 0 ] && [ "$((tr - ck_eps))" -gt "$CHUNK" ]; then
        echo "R0_FAILED|episode mismatch: lane counted $tr, checkpoint has"\
             "$ck_eps - the server died mid-run (see $OUT/server.log)"
        exit 1
    fi
    # separate statement: bash expands every word of a `local` line before
    # assigning any of them, so "$tr" here would be unbound under set -u
    local line="R0|$BASE|s$SEED|trained=$tr|ck_eps=$ck_eps"
    stop_server                     # eval must not learn from its own games
    start_server                    # (no --lr => inference only)
    local spec
    for spec in "heuristic|$BASE|D0" "search|$BASE|D1" "heuristic|$TWIN|TWIN"; do
        IFS='|' read -r OPP DK LB <<< "$spec"
        local f=$OUT/probe_${LB}_${tr}.txt
        probe "$f" "$OPP" "$DK" "$EVAL_G" $((900000 + tr))
        local wr=$(field $f win_rate)
        line="$line|$LB=${wr:-NA} $(band $EVAL_G ${wr:-0})"
    done
    local bo=$(field $OUT/probe_D0_${tr}.txt blockOpportunities)
    local bd=$(field $OUT/probe_D0_${tr}.txt blocksDeclared)
    local bc=$(field $OUT/probe_D0_${tr}.txt blockCombats)
    local bopt=$(field $OUT/probe_D0_${tr}.txt blockOptimal)
    local bgap=$(field $OUT/probe_D0_${tr}.txt blockScoreGap)
    # ATTACK side. attacks/attackOpportunities is the rate the joint
    # attack decision exists to move; ATKOPT is measured against a
    # reference that is one combat deep and cannot see that an attacker
    # cannot block next turn, so it over-credits attacking - read it with
    # the attack rate beside it, never alone.
    local ad=$(field $OUT/probe_D0_${tr}.txt attacksDeclared)
    local ao=$(field $OUT/probe_D0_${tr}.txt attackOpportunities)
    local ac=$(field $OUT/probe_D0_${tr}.txt attackCombats)
    local aopt=$(field $OUT/probe_D0_${tr}.txt attackOptimal)
    local aoptca=$(field $OUT/probe_D0_${tr}.txt attackOptimalCA)
    local aund=$(field $OUT/probe_D0_${tr}.txt attackUnder)
    local aov=$(field $OUT/probe_D0_${tr}.txt attackOver)
    line="$line|blocks=${bd:-0}/${bo:-0}|BLOCKOPT=${bopt:-0}/${bc:-0}|gap=${bgap:-0}"
    line="$line|attacks=${ad:-0}/${ao:-0}|ATKOPT=${aopt:-0}/${ac:-0}|ATKOPTCA=${aoptca:-0}/${ac:-0}|under_over=${aund:-0}/${aov:-0}"
    line="$line|turns=$(field $OUT/probe_D0_${tr}.txt turns_per_ep)"
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
            -Drl.consultBudget=4000 $ENCFLAGS -Drl.deck=$BASE.dck \
            -Drl.oppDeck=$BASE.dck -Drl.stopTurn=60 -Drl.mode=train \
            -Drl.seed=$((80000000 + SEED * 1000000 + trained)) \
            -Drl.report=0 > /dev/null 2>&1
        trained=$((trained + CHUNK))
    done
    battery $trained
done

# The held-out instrument, once, at the end. Training against it would
# destroy the only externally uncontaminated number this project has.
#
# R0_CP7_G=0 skips it. CP7 is a slow alpha-beta opponent and the handoff
# already records that 50 games of it is decorative (the same arm gave
# .900 and .500 on consecutive seeds); an A/B between two arms that skips
# it SYMMETRICALLY loses nothing it could have settled.
if [ "$CP7_G" -gt 0 ]; then
    stop_server
    start_server
    probe "$OUT/probe_CP7_final.txt" cp7 "$BASE" "$CP7_G" 950000
    wr=$(field $OUT/probe_CP7_final.txt win_rate)
    echo "R0|$BASE|s$SEED|FINAL|CP7=${wr:-NA} $(band $CP7_G ${wr:-0})|games=$CP7_G"
    stop_server
fi
echo "R0_DONE|$BASE|s$SEED|trained=$trained|out=$OUT"
