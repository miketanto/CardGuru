#!/bin/bash
# Phase 12: how do our agents do against XMage's OWN advanced AIs?
#
# Every instrument this project has used is something we wrote:
# HeuristicPlayer (D0) extends XMage's ComputerPlayer - the BASIC shipped
# AI - and SearchPlayer (D1) extends HeuristicPlayer. XMage also ships
# ComputerPlayer6/7 (Mage.Player.AI.MAD) and ComputerPlayerMCTS
# (Mage.Player.AIMCTS), and in ten phases neither has ever appeared in a
# measurement. So "ck_6144 reached D1 parity" says nothing about whether
# the agent beats the AI a person actually plays against.
#
# CP7/MCTS need a Match behind the game (SimulatedPlayer2 reads
# MatchPlayer); EpisodeRunner now builds a fake one for those two
# opponent kinds only, exactly as XMage's own test framework does.
#
# Usage: bash rl/p12_xmage_ai_bench.sh [games=50] [mcts_games=10]
set -u
G=${1:-50}
GM=${2:-10}
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_p12/aibench
mkdir -p $OUT

# name|ckpt|port
AGENTS=(
  "ck_6144|/tmp/rl_p7_lstmattn_s0/p7b_champion.pt|7891"
  "p10_final|/tmp/rl_p10_flagship_s0/p10_final.pt|7893"
)

start_agent() {  # $1 ckpt $2 port $3 log
    pkill -f "policy_serve[r].py --port $2" 2>/dev/null
    sleep 1
    RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port $2 \
        --ckpt "$1" --seed 0 --cdim 91 --arch lstmattn --threads 4 \
        > "$3" 2>&1 &
    local t=0
    while [ $t -lt 60 ]; do
        grep -q "policy server" "$3" 2>/dev/null && return 0
        sleep 2; t=$((t + 2))
    done
    echo "AIBENCH_FAILED|server $2"; return 1
}

probe() {   # $1 out $2 port $3 opponent $4 games $5 seed
    [ -s "$1" ] && return 0
    RL_PERSIST=1 timeout 5400 bash $RL/run_driver.sh \
        -Drl.episodes=$4 -Drl.agent=rl -Drl.policy=socket -Drl.port=$2 \
        -Drl.opponent=$3 -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
        -Drl.consultBudget=4000 -Drl.deck=BenchDimir.dck \
        -Drl.oppDeck=BenchDimir.dck -Drl.stopTurn=80 -Drl.mode=eval \
        -Drl.seed=$5 -Drl.report=0 -Drl.out=$1 > /dev/null 2>&1
}

field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

cd /home/user/mage
for A in "${AGENTS[@]}"; do
    IFS='|' read -r NAME CK PORT <<< "$A"
    [ -f "$CK" ] || { echo "AIBENCH_SKIP|$NAME|missing $CK"; continue; }
    start_agent "$CK" "$PORT" "$OUT/${NAME}_srv.log" || continue
    # D1 control first (fast) so every row has a same-session reference
    for SPEC in "search|$G|D1" "cp7|$G|CP7" "mcts|$GM|MCTS"; do
        IFS='|' read -r OPP N LABEL <<< "$SPEC"
        F=$OUT/${NAME}_vs_${LABEL}.txt
        probe "$F" "$PORT" "$OPP" "$N" 950000
        if [ -s "$F" ]; then
            echo "AIBENCH|agent=$NAME|opp=$LABEL|games=$(field $F episodes)|win_rate=$(field $F win_rate)|gps=$(field $F games_per_sec)|turns=$(field $F turns_per_ep)"
        else
            echo "AIBENCH|agent=$NAME|opp=$LABEL|NO_RESULT"
        fi
    done
    pkill -f "policy_serve[r].py --port $PORT" 2>/dev/null
done
echo "AIBENCH_DONE"
