#!/bin/bash
# What is the CEILING against D0 on a rung-0 deck?
#
# The rung-0 agent plateaus at ~.78 vs D0 and ~.79 vs D1, flat from 1919
# episodes. Two readings of that, and they have opposite consequences:
#
#   A. .78 is roughly the variance ceiling. W0Base is a MIRROR - both
#      players have the same 60 cards - so some fraction of games is
#      decided by the opening hand and the draw order no matter how well
#      either side plays. If so the agent has essentially solved rung 0,
#      the remaining seeds are confirmation rather than discovery, and
#      the ladder should move to rung 1.
#
#   B. .78 is a learning limit and a stronger player would score higher.
#      Then rung 0 has headroom, and the plateau is about the method
#      (terminal reward, no search, fixed opponent) rather than the game.
#
# The probe: put players of KNOWN, DIFFERENT strength in the same seat
# against the same D0 and see where the curve tops out.
#
#   D0  vs D0    symmetric, must come out ~.5 - a control on the harness
#   D1  vs D0    1-ply search
#   CP7 vs D0    depth-6 alpha-beta, 5000 nodes, XMage's shipped AI
#
# CP7 cannot be the agent (rl.agent has no cp7 kind), so it is run as the
# OPPONENT and the rate is inverted: CP7's score is 1 - D0's score, with
# draws at half. Same trick makes the D1 row comparable.
#
# If CP7 lands near .8 too, the ceiling is the deck and reading A holds.
# If CP7 lands near .95, reading B holds and our .78 is our own limit.
#
# Usage: bash rl/rung0_ceiling.sh [DECK=W0Base] [games=100] [cp7_games=60]
set -u
DECK=${1:-W0Base}
G=${2:-100}
GC=${3:-60}
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_rung0_ceiling
mkdir -p $OUT
cp $RL/$DECK.dck /home/user/mage/Mage.Tests/ 2>/dev/null

probe() {   # $1 out $2 opponent $3 games [$4 plies]
    [ -s "$1" ] && return 0
    RL_PERSIST=1 RL_AUTOSTART=1 timeout 7200 bash $RL/run_driver.sh \
        -Drl.episodes=$3 -Drl.agent=heuristic \
        -Drl.opponent=$2 -Drl.searchPlies=${4:-1} -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
        -Drl.consultBudget=4000 -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck \
        -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=960000 -Drl.report=0 \
        -Drl.out=$1 > /dev/null 2>&1
}

report() {  # $1 file $2 label
    python3 - "$1" "$2" <<'PY'
import math, re, sys
path, label = sys.argv[1], sys.argv[2]
try:
    t = open(path).read()
except OSError:
    print("  %-10s NO RESULT" % label); raise SystemExit
def f(k):
    m = re.search(r"\b%s=([0-9.]+)" % k, t)
    return float(m.group(1)) if m else 0.0
n, w, d, st = f("episodes"), f("wins"), f("draws"), f("stalls")
if not n:
    print("  %-10s NO RESULT" % label); raise SystemExit
# the file is D0's score; the row we want is the OPPONENT's
k = n - w - 0.5 * d
p = k / n
z = 1.96
den = 1 + z * z / n
c = (p + z * z / (2 * n)) / den
h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
print("  %-10s %.3f [%.3f,%.3f]  n=%d  stalls=%d  turns=%.1f"
      % (label, p, max(0, c - h), min(1, c + h), n, st, f("turns_per_ep")))
PY
}

cd /home/user/mage
echo "R0CEIL|deck=$DECK|score is the OPPONENT's, draws at half"
probe $OUT/${DECK}_D0.txt  heuristic $G ; report $OUT/${DECK}_D0.txt  "D0 vs D0"
probe $OUT/${DECK}_D1.txt  search    $G ; report $OUT/${DECK}_D1.txt  "D1 vs D0"
probe $OUT/${DECK}_CP7.txt cp7       $GC; report $OUT/${DECK}_CP7.txt "CP7 vs D0"

# DEPTH LADDER. The rows above say the two search instruments do WORSE
# than our learned agent, which is consistent with the mirror imposing a
# variance ceiling - but it is also consistent with these particular
# searchers being badly suited to the deck. Varying only the ply count
# separates the two: if depth buys nothing, the game is not rewarding
# lookahead and the ceiling reading strengthens; if 3-ply jumps well
# above .78, the ceiling is higher than our agent reaches and the
# plateau is ours after all. Same seat, same breadth, same opponent -
# only the depth moves.
for P in 2 3; do
    probe $OUT/${DECK}_D1p${P}.txt search $GC $P
    report $OUT/${DECK}_D1p${P}.txt "D1(${P}ply) vs D0"
done
echo "R0CEIL_DONE"
