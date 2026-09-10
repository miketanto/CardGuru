#!/bin/bash
# Deck-value check (DECK-VALUE-CHECK.md): scripted heuristic in both
# seats, 500 games per pair in two seat orders, Wilson intervals.
# Run inside WSL when no lane is using the machine. Sequential on purpose.
#
#   bash rl/deck_value_check.sh
#   R_DV_GAMES=100 bash rl/deck_value_check.sh     # smoke only
set -u
source "$HOME/.profile" 2>/dev/null
RL=/home/user/CardGuru/rl
OUT=${R_DV_OUT:-/tmp/rl_deckvalue}
GAMES=${R_DV_GAMES:-500}          # per pair, split across two seat orders
HALF=$((GAMES / 2))
mkdir -p "$OUT"

# Override for follow-ups (DECK-VALUE-CHECK.md §7), e.g.
#   R_DV_PAIRS="B2Mid:B0Base B3Open:B0Base B3Open:B1Narrow" R_DV_OUT=/tmp/rl_deckvalue2 ...
PAIRS=${R_DV_PAIRS:-"B0Base:B0Base B1Narrow:B0Base B1Fast:B0Base B1Narrow:B1Fast"}

# rl.cardFeatures / rl.encoderV are class-init constants of the persistent
# driver JVM: one left running by a lane refuses a job with different
# flags ("rl.cardFeatures is fixed for the life of this JVM"). Start
# fresh; RL_AUTOSTART brings up a JVM for this job's flags.
pkill -f "[R]LDriverServer" 2>/dev/null
sleep 2

run() {   # $1 agent deck  $2 opp deck  $3 seed  $4 out file
    [ -s "$4" ] && return 0
    RL_PERSIST=1 RL_AUTOSTART=1 timeout 3600 bash $RL/run_driver.sh \
        -Drl.episodes=$HALF -Drl.agent=heuristic -Drl.opponent=heuristic \
        -Drl.deck=$1.dck -Drl.oppDeck=$2.dck -Drl.mode=eval \
        -Drl.seed=$3 -Drl.stopTurn=60 -Drl.report=0 -Drl.out=$4 \
        > "$4.stdout" 2>&1
}

echo "DECKVALUE|start|games_per_pair=$GAMES|$(date -Is)"
seed=770001
for p in $PAIRS; do
    A=${p%%:*}; B=${p##*:}
    run $A $B $seed       "$OUT/${A}_vs_${B}_AB.txt"; seed=$((seed + 1))
    run $B $A $seed       "$OUT/${A}_vs_${B}_BA.txt"; seed=$((seed + 1))
done

python3 - "$OUT" $PAIRS <<'EOF'
import math, re, sys
out, pairs = sys.argv[1], sys.argv[2:]
def field(path, key):
    try:
        m = re.search(key + r"=(\d+)", open(path).read())
        return int(m.group(1)) if m else None
    except FileNotFoundError:
        return None
def wilson(k, n, z=1.96):
    if not n: return (0.0, 0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (p, c - h, c + h)
print("| pair | A-seat wins/n | B-seat wins/n | pooled p(A wins) | Wilson 95% |")
print("|---|---|---|---|---|")
for pr in pairs:
    A, B = pr.split(":")
    ab = f"{out}/{A}_vs_{B}_AB.txt"; ba = f"{out}/{A}_vs_{B}_BA.txt"
    # AB: A is the agent seat -> A wins = wins. BA: B is the agent seat -> A wins = losses.
    w1, n1 = field(ab, "wins"), field(ab, "episodes")
    l2, n2 = field(ba, "losses"), field(ba, "episodes")
    if None in (w1, n1, l2, n2):
        print(f"| {A} vs {B} | missing | missing | — | — |"); continue
    k, n = w1 + l2, n1 + n2
    p, lo, hi = wilson(k, n)
    print(f"| {A} vs {B} | {w1}/{n1} | {l2}/{n2} | {p:.3f} ({k}/{n}) | [{lo:.3f}, {hi:.3f}] |")
EOF
echo "DECKVALUE|end|$(date -Is)"
