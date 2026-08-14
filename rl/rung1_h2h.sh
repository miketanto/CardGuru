#!/bin/bash
# Rung 1: head-to-head between two trained nets on one deck.
#
#   bash rl/rung1_h2h.sh <deck> <ckptA> <ckptB> [games] [seed]
#
# WHY HEAD-TO-HEAD AND NOT WIN RATE VS D0
# ---------------------------------------
# The rung-0 ceiling test found that on these decks nothing we can build
# exceeds ~.78 against D0 - CP7 (depth-6 alpha-beta) manages .65 and
# 1-ply search manages .41. A shared ceiling that low makes "win rate vs
# D0" a blunt instrument for comparing two agents: both can sit near it
# while differing from each other. RUNG0-CEILING-TEST.md has the detail.
#
# So the rung-1 question is asked directly. Both nets play the SAME deck
# against EACH OTHER, and the score is the comparison.
#
# THE MEASUREMENT RUNG 1 ACTUALLY WANTS
# -------------------------------------
# Whether flying was learned, not whether a rung-1 agent is better:
#
#   effect = (W1Fly-trained  vs W0Base-trained, both on W1Fly)
#          - (W1Ctrl-trained vs W0Base-trained, both on W1Ctrl)
#
# W1Ctrl is W0Base with the same four slots swapped to a different
# VANILLA 2/2. It absorbs "trained on a deck whose 2/2s have different
# names", which is the story that would otherwise explain any W1Fly
# advantage. The residual is the keyword. One control run covers all
# four keyword rungs because they all swap the same slot.
#
# WHICH CHECKPOINT
# ----------------
# Pass ck_<n>.pt explicitly, and pass the BEST one, not the last. Seed 0
# of rung 0 peaked at 1919 and regressed to .705 by 2111 - the drift
# signature Phase 10 built champion gating for - so "the final net" is
# the wrong default here. rung0_report.py names the peak.
set -u
DECK=${1:?usage: rung1_h2h.sh <deck> <ckptA> <ckptB> [games] [seed]}
CKA=${2:?}
CKB=${3:?}
G=${4:-200}
SEED=${5:-953000}
RL=/home/user/CardGuru/rl
OUT=${H2H_OUT:-/tmp/rl_rung1_h2h}
PA=${H2H_PORT_A:-7950}
PB=${H2H_PORT_B:-7951}
mkdir -p $OUT
TAG=$(basename $CKA .pt)_vs_$(basename $CKB .pt)_on_$DECK
F=$OUT/$TAG.txt

for c in "$CKA" "$CKB"; do
    [ -f "$c" ] || { echo "H2H_FAILED|missing $c"; exit 1; }
done
cp $RL/$DECK.dck /home/user/mage/Mage.Tests/ 2>/dev/null

start() {   # $1 ckpt $2 port $3 log
    pkill -f "policy_serve[r].py --port $2" 2>/dev/null
    # inference only: no --lr, and the driver runs mode=eval, so neither
    # net learns from the comparison
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py \
        --port $2 --ckpt "$1" --seed 0 --cdim 91 --arch lstmattn \
        --threads 2 > "$3" 2>&1 &
    local t=0
    while [ $t -lt 90 ]; do
        grep -q "policy server" "$3" 2>/dev/null && return 0
        grep -q "Traceback" "$3" 2>/dev/null && break
        sleep 2; t=$((t + 2))
    done
    echo "H2H_FAILED|server $2"; tail -3 "$3"; exit 1
}

if [ ! -s "$F" ]; then
    start "$CKA" $PA $OUT/a.log
    start "$CKB" $PB $OUT/b.log
    cd /home/user/mage
    # sequential: this is a reported number
    RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
        -Drl.episodes=$G -Drl.agent=rl -Drl.policy=socket -Drl.port=$PA \
        -Drl.opponent=rl -Drl.oppPort=$PB \
        -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
        -Drl.consultBudget=4000 -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck \
        -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=$SEED -Drl.report=0 \
        -Drl.out=$F > /dev/null 2>&1
    pkill -f "policy_serve[r].py --port $PA" 2>/dev/null
    pkill -f "policy_serve[r].py --port $PB" 2>/dev/null
fi

python3 - "$F" "$TAG" <<'PY'
import math, re, sys
path, tag = sys.argv[1], sys.argv[2]
try:
    t = open(path).read()
except OSError:
    print("H2H|%s|NO RESULT" % tag); raise SystemExit
def f(k):
    m = re.search(r"\b%s=([0-9.]+)" % k, t)
    return float(m.group(1)) if m else 0.0
n = f("episodes")
if not n:
    print("H2H|%s|NO RESULT" % tag); raise SystemExit
k = f("wins") + 0.5 * f("draws")      # draws at half, as Elo does
p, z = k / n, 1.96
den = 1 + z * z / n
c = (p + z * z / (2 * n)) / den
h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
print("H2H|%s|A=%.3f [%.3f,%.3f]|n=%d|stalls=%d|turns=%.1f"
      % (tag, p, max(0, c - h), min(1, c + h), n, f("stalls"),
         f("turns_per_ep")))
PY
