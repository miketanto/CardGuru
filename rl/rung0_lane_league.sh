#!/bin/bash
# Rung 0 LEAGUE lane (OVERNIGHT-7D A4): a copy of rl/rung0_lane.sh whose
# TRAINING opponent is a frozen RL checkpoint (the C5 league mechanism:
# -Drl.opponent=rl -Drl.oppPort=$OPP_PORT, served by an eval-mode policy
# server on OPP_PORT) instead of the heuristic. Everything else is the
# original lane on purpose: same batteries (D0 / D1 / TWIN, 100 games,
# argmax over classes when R0_SRVEXTRA says so), same chunking, same
# checkpoint bookkeeping - the training opponent is the only thing that
# moves, so L1 (this lane) reads against L0 (rung0_lane.sh from the same
# checkpoint, same episode budget).
#
#   R0_INIT=/path/ck.pt          start from this checkpoint (copied to
#                                $OUT/init.pt; the original lane regenerates
#                                init.pt unconditionally). Its "episodes"
#                                counter is kept, so `trained` starts there
#                                and the budget is ABSOLUTE: from ck_2048
#                                with budget 3072 the rows are labelled
#                                2560 and 3072. R0_BATTERY_START=1 runs the
#                                battery once at the start (the +0 row).
#   R0_OPP_CKPTS=a.pt,b.pt       frozen opponents, one per 512-block in
#                                turn (block i uses entry i mod n); each
#                                block's choice is logged as R0_OPP|.
#   R0_OPP_SPEC="kind:arg:deck,..." (Phase 8 A2) one entry per 512-block in turn
#                                (block i uses entry i mod n): kind = heuristic |
#                                cp7 (rl.aiSkill R0_CP7_SKILL, default 6) | rl
#                                (arg = the frozen checkpoint served on OPP_PORT);
#                                deck = the OPPONENT's .dck (-Drl.oppDeck), the
#                                agent keeps $BASE. Overrides R0_OPP_CKPTS, which
#                                is the old form "rl:a:$BASE.dck,rl:b:$BASE.dck".
#                                Each block logs R0_OPP|kind=..|arg=..|deck=..
#   R0_OPP_PORT (7960)           the opponent server's port
#   RL_DRIVER_PORT (7912)        the driver JVM this lane owns (never 7910:
#                                that is the C1/D-PPO lane's; the original
#                                lane's `pkill [R]LDriverServer` would have
#                                killed every JVM - this one stops only its
#                                own port).
#   R0_PORT (7950)               the lane's own policy server port
# The opponent seat is an RLPlayer whose consults go to OPP_PORT with hello
# mode "eval": the frozen server answers argmax (over classes with
# --argmax-classes, which R0_OPP_SRVEXTRA carries) and never updates
# (--frozen). rl.oppEncoderV is left at the default (= rl.encoderV).
set -u
BASE=${1:?usage: rung0_lane_league.sh <BASE> <TWIN> [budget] [seed]}
TWIN=${2:?}
BUDGET=${3:-4096}
SEED=${4:-0}
RL=/home/user/CardGuru/rl
PORT=${R0_PORT:-7950}
OPP_PORT=${R0_OPP_PORT:-7960}
DPORT=${RL_DRIVER_PORT:-7912}
export RL_DRIVER_PORT=$DPORT
EVERY=${R0_EVERY:-512}      # battery cadence
CHUNK=${R0_CHUNK:-64}       # episodes per driver job
EVAL_G=${R0_EVAL_G:-100}
CP7_G=${R0_CP7_G:-50}
LR=${R0_LR:-3e-4}
CONC=${R0_CONC:-4}
FEATS=$RL/e2_features.tsv
ENC=${R0_ENCODER_V:-2}
if [ "$ENC" = "1" ]; then SDIM=24; CDIM=91; else SDIM=32; CDIM=94; fi
ENCFLAGS="-Drl.encoderV=$ENC -Drl.blockAudit=true"
ARCH=lstmattn
V6FLAGS=""
if [ "$ENC" -ge 6 ] 2>/dev/null; then
    ARCH=entattn
    V6FLAGS="--gdim 16 --edim 48 --emax ${R0_EMAX:-96}"
    [ "${R0_RELATIONS:-1}" = "0" ] && V6FLAGS="$V6FLAGS --r0"
    [ -n "${R0_EMAX:-}" ] && ENCFLAGS="$ENCFLAGS -Drl.entityMax=$R0_EMAX"
fi
if [ "$ENC" = "7" ]; then           # v7 (V7-IMPLEMENTATION-PLAN.md): its own net, no v6 flags
    ARCH=v7
    V6FLAGS=""
fi
EVALFLAGS="$ENCFLAGS -Drl.attackAudit=true"
SRVEXTRA=""
[ "$ENC" -ge 4 ] 2>/dev/null && SRVEXTRA="--max-k 64"
[ "$ENC" -ge 5 ] 2>/dev/null && SRVEXTRA="--max-k 96"
[ "$ENC" = "7" ] && SRVEXTRA=""
SRVEXTRA="$SRVEXTRA ${R0_SRVEXTRA:-}"
# the frozen opponent's server flags: inference-side only (device, bound,
# argmax classes); no optimiser knobs apply to a --frozen server
OPP_SRVEXTRA="${R0_OPP_SRVEXTRA:---device cuda --logit-bound 5 --argmax-classes}"
OUT=${R0_OUT:-/tmp/rl_league_${BASE}_v${ENC}_s${SEED}}
mkdir -p $OUT

for D in $BASE $TWIN; do cp $RL/$D.dck /home/user/mage/Mage.Tests/; done

# ONLY this lane's driver JVM is restarted (rl.encoderV is class-init; a
# JVM that served another arm cannot serve this one). The original lane's
# blanket pkill would take 7910/7911 down with it.
bash $RL/driver_server.sh stop $DPORT > /dev/null 2>&1
sleep 2

INIT=$OUT/init.pt
if [ -n "${R0_INIT:-}" ]; then
    [ -s "$R0_INIT" ] || { echo "R0_FAILED|init|$R0_INIT missing"; exit 1; }
    cp "$R0_INIT" $INIT
    echo "R0_INIT|from=$R0_INIT|episodes=$(python3 -c "
import torch
print(int(torch.load('$INIT',map_location='cpu',weights_only=False).get('episodes',0)))" 2>/dev/null)"
else
    INITEXTRA=""
    [ "$ARCH" = "entattn" ] && INITEXTRA="--gdim 16 --edim 48"
    [ "${R0_RELATIONS:-1}" = "0" ] && [ "$ARCH" = "entattn" ] && INITEXTRA="$INITEXTRA --r0"
    python3 $RL/p10_init_net.py --out $INIT --seed $((10 + SEED)) --sdim $SDIM \
        --cdim $CDIM --arch $ARCH $INITEXTRA 2>/dev/null | tail -1
fi
CKPT=$OUT/agent.pt
[ -s $CKPT ] || cp $INIT $CKPT

start_server() {   # $1 extra-flags
    pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
    [ -s $OUT/server.log ] && cat $OUT/server.log >> $OUT/server_all.log
    # TRUNCATE SYNCHRONOUSLY before the launch (7d L0 NA rows): the background
    # job's own `> server.log` happens in the child after the fork, so the
    # first poll below could still read the OLD server's "policy server" line,
    # return at once, and send the probes into a server that had not bound yet.
    : > $OUT/server.log
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py \
        --port $PORT --ckpt $CKPT --seed $SEED --sdim $SDIM --cdim $CDIM --arch $ARCH \
        --threads $CONC --log $OUT/train.csv \
        $SRVEXTRA $V6FLAGS ${1:-} > $OUT/server.log 2>&1 &
    local t=0
    while [ $t -lt 90 ]; do
        grep -q "policy server" $OUT/server.log 2>/dev/null && return 0
        grep -q "Traceback" $OUT/server.log 2>/dev/null && break
        sleep 2; t=$((t + 2))
    done
    echo "R0_FAILED|server|$OUT/server.log"; tail -5 $OUT/server.log; exit 1
}
stop_server() { pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null; sleep 1; }

# the frozen league opponent on OPP_PORT: eval-mode hello from the driver's
# opponent seat -> argmax; --frozen -> never updates, never saves
start_opp_server() {   # $1 ckpt
    pkill -f "policy_serve[r].py --port $OPP_PORT" 2>/dev/null
    [ -s $OUT/opp_server.log ] && cat $OUT/opp_server.log >> $OUT/opp_server_all.log
    : > $OUT/opp_server.log            # the same race as start_server
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py \
        --port $OPP_PORT --ckpt "$1" --seed $((SEED + 500)) --sdim $SDIM --cdim $CDIM --arch $ARCH \
        --threads $CONC --frozen $OPP_SRVEXTRA $V6FLAGS > $OUT/opp_server.log 2>&1 &
    local t=0
    while [ $t -lt 90 ]; do
        grep -q "policy server" $OUT/opp_server.log 2>/dev/null && return 0
        grep -q "Traceback" $OUT/opp_server.log 2>/dev/null && break
        sleep 2; t=$((t + 2))
    done
    echo "R0_FAILED|opp_server|$OUT/opp_server.log"; tail -5 $OUT/opp_server.log; exit 1
}
stop_opp_server() { pkill -f "policy_serve[r].py --port $OPP_PORT" 2>/dev/null; sleep 1; }

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
    local line="R0|$BASE|s$SEED|trained=$tr|ck_eps=$ck_eps"
    stop_server                     # eval must not learn from its own games
    start_server                    # (no --lr => inference only)
    local spec
    for spec in "heuristic|$BASE|D0" "search|$BASE|D1" "heuristic|$TWIN|TWIN"; do
        IFS='|' read -r OPP DK LB <<< "$spec"
        # R0_ROWS / R0_ROWS_FINAL (Phase 8 amendment): the battery rows to run (default
        # all three; R0_ROWS_FINAL applies at trained >= BUDGET); a skipped row prints LB=skip
        local rows=${R0_ROWS:-"D0 D1 TWIN"}; [ "$tr" -ge "$BUDGET" ] && rows=${R0_ROWS_FINAL:-$rows}
        case " $rows " in *" $LB "*) ;; *) line="$line|$LB=skip"; continue ;; esac
        # R0_EVAL_G_INTERIM (Phase 8 two-tier rule): games per row at every point BEFORE
        # the final one (development probes); the final point (trained >= BUDGET) uses EVAL_G
        local g=$EVAL_G; [ "$tr" -lt "$BUDGET" ] && g=${R0_EVAL_G_INTERIM:-$EVAL_G}
        local f=$OUT/probe_${LB}_${tr}.txt
        probe "$f" "$OPP" "$DK" "$g" $((900000 + tr))
        local wr=$(field $f win_rate)
        line="$line|$LB=${wr:-NA} $(band $g ${wr:-0})|games=$g"
    done
    local bo=$(field $OUT/probe_D0_${tr}.txt blockOpportunities)
    local bd=$(field $OUT/probe_D0_${tr}.txt blocksDeclared)
    local bc=$(field $OUT/probe_D0_${tr}.txt blockCombats)
    local bopt=$(field $OUT/probe_D0_${tr}.txt blockOptimal)
    local bgap=$(field $OUT/probe_D0_${tr}.txt blockScoreGap)
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
start_trained=$trained
echo "R0_START|$BASE|seed=$SEED|budget=$BUDGET|resume_at=$trained|out=$OUT|league=${R0_OPP_SPEC:-${R0_OPP_CKPTS:-none}}|driver=$DPORT"

if [ "$trained" -eq 0 ] || { [ "${R0_BATTERY_START:-0}" = "1" ] && [ ! -s $OUT/probe_D0_${trained}.txt ]; }; then
    battery $trained
fi

# the opponent roster (R0_OPP_SPEC, else R0_OPP_CKPTS in the old rl-only form)
if [ -n "${R0_OPP_SPEC:-}" ]; then
    IFS=',' read -r -a OPPS <<< "$R0_OPP_SPEC"
else
    IFS=',' read -r -a CKS <<< "${R0_OPP_CKPTS:-}"
    OPPS=(); for c in "${CKS[@]}"; do [ -n "$c" ] && OPPS+=("rl:$c:$BASE.dck"); done
fi
[ ${#OPPS[@]} -gt 0 ] || { echo "R0_FAILED|no opponent roster (R0_OPP_SPEC or R0_OPP_CKPTS)"; exit 1; }
for e in "${OPPS[@]}"; do d=${e##*:}; d=${d%.dck}; [ -n "$d" ] && { cp $RL/$d.dck /home/user/mage/Mage.Tests/ || { echo "R0_FAILED|opp deck missing: $RL/$d.dck"; exit 1; }; }; done
block=0
while [ "$trained" -lt "$BUDGET" ]; do
    stop_server
    start_server "--lr $LR"
    local_end=$((trained + EVERY))
    [ "$local_end" -gt "$BUDGET" ] && local_end=$BUDGET
    # this block's frozen opponent (resume-safe: the block index is derived
    # from the trained counter, not from how often this loop ran)
    block=$(( (trained - start_trained) / EVERY ))
    entry=${OPPS[$(( block % ${#OPPS[@]} ))]}
    KIND=${entry%%:*}; rest=${entry#*:}; OPPCK=${rest%:*}; ODECK=${rest##*:}; ODECK=${ODECK%.dck}
    [ -n "$ODECK" ] || ODECK=$BASE
    stop_opp_server
    case "$KIND" in
        rl)        [ -s "$OPPCK" ] || { echo "R0_FAILED|opp ckpt missing: $OPPCK"; exit 1; }
                   start_opp_server "$OPPCK"; OPPFLAGS="-Drl.opponent=rl -Drl.oppPort=$OPP_PORT" ;;
        heuristic) OPPFLAGS="-Drl.opponent=heuristic" ;;
        cp7)       OPPFLAGS="-Drl.opponent=cp7 -Drl.aiSkill=${R0_CP7_SKILL:-6}" ;;
        *)         echo "R0_FAILED|unknown opponent kind: $KIND (entry $entry)"; exit 1 ;;
    esac
    echo "R0_OPP|trained=$trained|block=$block|kind=$KIND|arg=$OPPCK|deck=$ODECK.dck"
    while [ "$trained" -lt "$local_end" ]; do
        RL_PERSIST=1 RL_AUTOSTART=1 RL_CONC=$CONC timeout 3600 \
        bash $RL/run_driver.sh \
            -Drl.episodes=$CHUNK -Drl.agent=rl -Drl.policy=socket \
            -Drl.port=$PORT $OPPFLAGS \
            -Drl.searchPlies=1 -Drl.searchBreadth=8 \
            -Drl.cardFeatures=$FEATS -Drl.noYields=true \
            -Drl.consultBudget=4000 $ENCFLAGS -Drl.deck=$BASE.dck \
            -Drl.oppDeck=$ODECK.dck -Drl.stopTurn=60 -Drl.mode=train \
            -Drl.seed=$((80000000 + SEED * 1000000 + trained)) \
            -Drl.report=0 2>&1 | grep '^RL|summary\|^RLJOB|error\|^RL_DRIVER' >> $OUT/jobs.log
        # jobs.log (7d): the per-job RL|summary lines (wins/losses/draws/stalls
        # per training chunk) survive; they used to go to /dev/null.
        trained=$((trained + CHUNK))
    done
    stop_opp_server
    battery $trained
done

if [ "$CP7_G" -gt 0 ]; then
    stop_server
    start_server
    probe "$OUT/probe_CP7_final.txt" cp7 "$BASE" "$CP7_G" 950000
    wr=$(field $OUT/probe_CP7_final.txt win_rate)
    echo "R0|$BASE|s$SEED|FINAL|CP7=${wr:-NA} $(band $CP7_G ${wr:-0})|games=$CP7_G"
    stop_server
fi
stop_opp_server
echo "R0_DONE|$BASE|s$SEED|trained=$trained|out=$OUT"
