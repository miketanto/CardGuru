#!/bin/bash
# Gate for the white ladder decks, same shape as the rung-0 red gate.
#
# Two things must hold before any of these decks is worth training on:
#   1. it LOADS - .dck silently loads zero cards on a bad [SET:NUM], and
#      a 0-card deck still "runs", it just produces nonsense;
#   2. it ENDS - vanilla creatures with no removal and no evasion is the
#      classic board-stall configuration, and a stall runs to stopTurn,
#      which turns every terminal reward into a coin flip.
# Both are checked with a scripted D0 mirror, which also gives the seat
# balance (a deck whose mirror is not ~.5 has a structural seat edge and
# would contaminate every measured difference).
#
# Usage: bash rl/wladder_gate.sh [games=40] [decks...]
set -u
G=${1:-40}
shift || true
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_p12/wgate
mkdir -p $OUT
DECKS=("$@")
if [ ${#DECKS[@]} -eq 0 ]; then
    DECKS=(W0Base W0Twin W1Fly W1Fst W1Vig W1Lif W1Ctrl W2FlyLif W2Ctrl \
           W3Sorc W4Inst W5Trick)
fi

for D in "${DECKS[@]}"; do cp "$RL/$D.dck" /home/user/mage/Mage.Tests/; done

printf "%-10s %8s %6s %9s %9s %10s\n" deck stalls draws turns win_rate games/sec
cd /home/user/mage
for D in "${DECKS[@]}"; do
    F=$OUT/$D.txt
    if [ ! -s "$F" ]; then
        RL_PERSIST=1 RL_CONC=4 timeout 3600 bash $RL/run_driver.sh \
            -Drl.episodes=$G -Drl.agent=heuristic -Drl.opponent=heuristic \
            -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
            -Drl.consultBudget=4000 \
            -Drl.deck=$D.dck -Drl.oppDeck=$D.dck -Drl.stopTurn=60 \
            -Drl.mode=eval -Drl.seed=770000 -Drl.report=0 -Drl.out=$F \
            > $OUT/$D.log 2>&1
    fi
    # a deck that failed to load says so in the driver log, and the
    # summary would otherwise look perfectly healthy
    if grep -q "deck load failed" $OUT/$D.log 2>/dev/null; then
        echo "$D DECK_LOAD_FAILED"; continue
    fi
    f() { grep -o "$1=[0-9.]*" "$F" 2>/dev/null | head -1 | cut -d= -f2; }
    ST=$(f stalls)
    printf "%-10s %8s %6s %9s %9s %10s\n" \
        "$D" "${ST:-?}/$G" "$(f draws)" "$(f turns_per_ep)" \
        "$(f win_rate)" "$(f games_per_sec)"
done
echo WGATE_DONE
