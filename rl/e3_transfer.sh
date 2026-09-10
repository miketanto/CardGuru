#!/bin/bash
# E3 transfer battery: both encoder arms, three decks, one protocol.
#
# The Phase 8 question, asked of the E3 encoder: does competence learned
# on BenchDimir survive a card swap, and does it survive a whole new
# archetype?
#   BenchDimir          home deck (training distribution)
#   P8SwapInteraction   12 feature-matched cards the nets never saw -
#                       Phase 8's zero-shot probe, and the operational
#                       test of gate G2 (analogs must stay close)
#   P8Faeries           full archetype rebuild - Phase 8b's held-out
#                       transfer probe
#
# Usage: bash rl/e3_transfer.sh <seed> [games=200] [decks...]
# Reads /tmp/rl_{e3,e2}_pilot_s<seed>/{e3,e2}_pilot_final.pt and writes
# /tmp/rl_<arm>_xfer_s<seed>_<deck>/results.txt.
set -u
SEED=${1:-0}
GAMES=${2:-200}
shift 2 2>/dev/null || shift 1 2>/dev/null || true
DECKS=${*:-"BenchDimir.dck P8SwapInteraction.dck P8Faeries.dck"}
CG=/home/user/CardGuru

for arm in e3 e2; do
    NET=/tmp/rl_${arm}_pilot_s${SEED}/${arm}_pilot_final.pt
    if [ ! -f "$NET" ]; then
        echo "E3XFER|missing net for arm=$arm seed=$SEED ($NET)"
        continue
    fi
    for deck in $DECKS; do
        tag=$(basename $deck .dck)
        E3_ARM=$arm E3_DECK=$deck E3_CASES="baseline" \
        E3_OUT=/tmp/rl_${arm}_xfer_s${SEED}_${tag} \
            bash $CG/rl/e3_ablate.sh "$NET" $GAMES $SEED > /dev/null 2>&1
        echo "E3XFER|arm=$arm|seed=$SEED|deck=$tag|$(tail -1 \
            /tmp/rl_${arm}_xfer_s${SEED}_${tag}/results.txt 2>/dev/null)"
    done
done
