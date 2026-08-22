#!/bin/bash
# Collect real candidate emission for the §2a timing-collision gate.
#
#   bash rl/cand_dump.sh [deck] [games] [seed] [out]
#   bash rl/cand_dump.sh B1Fast 12 940001 /tmp/cand_B1Fast.jsonl
#
# Uses -Drl.policy=random (RandomPolicyClient, in-process): the gate
# asks what the EMITTER produces, not what a policy does, so no policy
# server and no torch are needed. A random policy is in fact the better
# collector here - it casts and passes at every step it is offered,
# which is what fills the opponent-turn priority windows a trained
# policy visits once in a thousand chances.
#
# The deck must contain an INSTANT, or no card can appear as a
# candidate in both an own main phase and the opponent's
# declare-attackers step and the gate has nothing to compare. B1Fast
# (4 Cruel Cut) is the ladder rung built for exactly this.
set -u
RL=/home/user/CardGuru/rl
DECK=${1:-B1Fast}
GAMES=${2:-12}
SEED=${3:-940001}
OUT=${4:-/tmp/cand_${DECK}.jsonl}

[ -f /home/user/mage/.rl_ready ] || { echo "engine not built"; exit 1; }

# a persistent driver JVM pins rl.candDump at class init like every
# other rl.* constant, so one that was started without it will never
# write a line
pkill -f "[R]LDriverServer" 2>/dev/null
sleep 2
rm -f "$OUT"
cp "$RL/$DECK.dck" /home/user/mage/Mage.Tests/ 2>/dev/null || true

cd /home/user/mage
timeout 3600 bash $RL/run_driver.sh \
    -Drl.episodes=$GAMES -Drl.agent=rl -Drl.policy=random \
    -Drl.opponent=heuristic -Drl.cardFeatures=$RL/e2_features.tsv \
    -Drl.noYields=true -Drl.consultBudget=4000 \
    -Drl.encoderV=6 -Drl.candDump=$OUT \
    -Drl.deck=$DECK.dck -Drl.oppDeck=$DECK.dck \
    -Drl.stopTurn=60 -Drl.mode=random -Drl.seed=$SEED -Drl.report=0 \
    -Drl.out=/tmp/cand_dump_sum.txt > /tmp/cand_dump_drv.log 2>&1

echo "consults dumped: $(wc -l < $OUT 2>/dev/null || echo 0)  -> $OUT"
grep -o "win_rate=[0-9.]*\|agent_consults_per_ep=[0-9.]*" \
    /tmp/cand_dump_sum.txt 2>/dev/null | tr '\n' ' '
echo
