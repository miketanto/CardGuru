#!/bin/bash
# Phase 10 cross-deck sample games (user request): one game per ordered pairing of the
# three league mains' latest snapshots, each main on its own deck, so every main's
# decisions are transcribed against both others (6 games). Waits until the league
# controller and its lane have exited; the main session starts the evaluation after.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
P=/home/user/CardGuru/rl/artifacts/v7/10/pool; OUT=/home/user/CardGuru/rl/artifacts/v7/10/pairs
declare -A DECK=([M_W]=W0Base [M_D]=BenchDimir [M_L]=G1Landfall)
echo "PAIRS10|wait|$(date -u +%FT%TZ)"
while pgrep -f 'league1[0]\.py' > /dev/null || pgrep -f 'rung0_lan[e]' > /dev/null; do sleep 20; done
echo "PAIRS10|start|$(date -u +%FT%TZ)"
latest() { ls $P/${1}_[0-9]*.pt 2>/dev/null | sort | tail -n 1; }
seed=7101
for pr in "M_W M_D" "M_D M_W" "M_W M_L" "M_L M_W" "M_D M_L" "M_L M_D"; do
    set -- $pr; a=$1; b=$2; ca=$(latest $a); cb=$(latest $b)
    { [ -s "$ca" ] && [ -s "$cb" ]; } || { echo "PAIRS10|$a-$b|missing snapshot"; continue; }
    bash rl/replay_pair.sh "$ca" ${DECK[$a]} "$cb" ${DECK[$b]} $OUT ${a}_vs_${b} $seed 2>&1 | grep '^PAIR' | sed "s/^/PAIRS10|/"
    seed=$((seed + 1))
done
echo "PAIRS10|done|$(date -u +%FT%TZ)"
