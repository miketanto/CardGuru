#!/bin/bash
# 7d piece (1a): teacher choice. Pure-Java games on driver 7911 (started alone
# beforehand with the v7 recording flags; RL_AUTOSTART=0 so a wrong JVM is never
# started here). No policy server, no RL seat. Seats alternate play/draw by
# episode parity inside the driver. Resumable: a non-empty out file is skipped.
#   cp7_vs_heur:   heuristic AGENT vs cp7 OPPONENT (the driver has no cp7 agent
#                  kind) -> CP7's rate = losses / episodes.
#   search_pXbY:   the project's search teacher as AGENT vs the heuristic.
set -u
CG=/home/user/CardGuru; RL=$CG/rl; ART=$RL/artifacts/v7/7d1; mkdir -p $ART
export RL_PERSIST=1 RL_AUTOSTART=0 RL_DRIVER_PORT=7911 RL_CONC=${RL_CONC:-2}
job() {   # $1 out, rest -D flags
    local out=$1; shift
    if [ -s "$out" ]; then echo "7D1|skip=$out"; return; fi
    echo "7D1|start=$(basename $out)|$(date -u +%FT%TZ)"
    timeout 10800 bash $RL/run_driver.sh "$@" \
        -Drl.deck=W0Base.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 \
        -Drl.mode=eval -Drl.report=0 -Drl.out=$out > /dev/null 2>&1
    local rc=$?
    echo "7D1|done=$(basename $out)|rc=$rc|$(grep -o 'RL|summary|[^ ]*' $out 2>/dev/null | head -n1 | cut -d'|' -f3-8)|$(date -u +%FT%TZ)"
}
job $ART/cp7_vs_heur.txt        -Drl.episodes=100 -Drl.agent=heuristic -Drl.opponent=cp7 -Drl.seed=7100
job $ART/search_p1b8_vs_heur.txt -Drl.episodes=100 -Drl.agent=search -Drl.agentPlies=1 -Drl.agentBreadth=8 -Drl.opponent=heuristic -Drl.seed=7100
job $ART/search_p2b8_vs_heur.txt -Drl.episodes=100 -Drl.agent=search -Drl.agentPlies=2 -Drl.agentBreadth=8 -Drl.opponent=heuristic -Drl.seed=7100
# controls (added after the first three landed: p1b8 and p2b8 were identical, 37/100, turns 12.9)
job $ART/heur_vs_heur.txt        -Drl.episodes=100 -Drl.agent=heuristic -Drl.opponent=heuristic -Drl.seed=7100
job $ART/search_p1b16_vs_heur.txt -Drl.episodes=100 -Drl.agent=search -Drl.agentPlies=1 -Drl.agentBreadth=16 -Drl.opponent=heuristic -Drl.seed=7100
job $ART/search_p3b8_vs_heur.txt  -Drl.episodes=100 -Drl.agent=search -Drl.agentPlies=3 -Drl.agentBreadth=8 -Drl.opponent=heuristic -Drl.seed=7100
job $ART/search_p1b8_vs_heur_s7200.txt -Drl.episodes=100 -Drl.agent=search -Drl.agentPlies=1 -Drl.agentBreadth=8 -Drl.opponent=heuristic -Drl.seed=7200
echo "7D1|all_done|$(date -u +%FT%TZ)"
