#!/bin/bash
# Phase 10 action 4.4 — the pilot's exam: 200g vs the project champion.
#
#   agent seat = the trained pilot, piloting its archetype deck X
#   opp   seat = ck_6144 (p7b_champion.pt), piloting BenchDimir
#
# Plus the two references that make the number mean something:
#   base = the SAME matchup with D0 in the pilot's seat (the scripted
#          lower bound the 7c matrix was built on) — the lift
#          (pilot - base) is the answer to "how loose was that bound".
# Both are eval mode, sequential, argmax on both policy seats.
#
# Usage: bash rl/p10_pilot_match.sh <name> <deck> <pilotCkpt> \
#            <aport> <oport> [games=200] [baseGames=100]
set -u
NAME=$1; DECK=$2; CKPT=$3; APORT=$4; OPORT=$5
G=${6:-200}; BG=${7:-100}
RL=/home/user/CardGuru/rl
ARCH=lstmattn; CDIM=91
FEATS=$RL/e2_features.tsv
CHAMP=${P10_CHAMP:-/tmp/rl_p7_lstmattn_s0/p7b_champion.pt}
CDECK=BenchDimir.dck
OUT=/tmp/rl_p10_matches
mkdir -p $OUT

start_server() {  # $1 ckpt $2 port $3 log
    local try
    for try in 1 2 3; do
        rm -f $3
        python3 $RL/policy_server.py --port $2 --ckpt "$1" \
            --seed 0 --cdim $CDIM --arch $ARCH > $3 2>&1 &
        echo $! > $OUT/.srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" $3 2>/dev/null && { up=1; break; }
            grep -q "Traceback" $3 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat $OUT/.srvpid) 2>/dev/null; wait $(cat $OUT/.srvpid) 2>/dev/null
        grep -q "Address already in use" $3 2>/dev/null || break
    done
    echo "P10M_FAILED|server_never_started|$3"; cat $3; exit 1
}
stop_server() { kill $1 2>/dev/null; wait $1 2>/dev/null; }
field() { grep -o "$2=[0-9.]*" "$1" 2>/dev/null | head -1 | cut -d= -f2; }

cd /home/user/mage
pkill -f "policy_serve[r].py --port $APORT" 2>/dev/null
pkill -f "policy_serve[r].py --port $OPORT" 2>/dev/null
sleep 1

# ---- 1. the pilot vs the champion
F=$OUT/champ_${NAME}.txt
if [ ! -s "$F" ]; then
    start_server "$CKPT" $APORT $OUT/aserver.log;  ASRV=$(cat $OUT/.srvpid)
    start_server "$CHAMP" $OPORT $OUT/oserver.log; OSRV=$(cat $OUT/.srvpid)
    RL_PERSIST=${P10_PERSIST:-1} RL_AUTOSTART=0 bash $RL/run_driver.sh \
        -Drl.episodes=$G \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=rl -Drl.oppPort=$OPORT \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$CDECK -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=955000 -Drl.report=0 \
        -Drl.out=$F > /dev/null 2>&1
    stop_server $ASRV; stop_server $OSRV
fi

# ---- 2. the scripted lower bound: D0 in the pilot's seat, same matchup.
# Expressed from the champion's side (agent=champion on Dimir, opponent=D0
# on X) because that is exactly how the 7c/Phase 10 matrix rows were
# measured; base_wr below is converted back to the pilot seat's view.
B=$OUT/base_${NAME}.txt
if [ ! -s "$B" ]; then
    start_server "$CHAMP" $APORT $OUT/aserver.log; ASRV=$(cat $OUT/.srvpid)
    RL_PERSIST=${P10_PERSIST:-1} RL_AUTOSTART=0 bash $RL/run_driver.sh \
        -Drl.episodes=$BG \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
        -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$CDECK -Drl.oppDeck=$DECK -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=951000 -Drl.report=0 \
        -Drl.out=$B > /dev/null 2>&1
    stop_server $ASRV
fi

CW=$(field $F win_rate); CD=$(grep -o 'draws=[0-9]*' $F | head -1 | cut -d= -f2)
BW=$(field $B win_rate)
BASE_PILOT=$(python3 -c "print('%.4f' % (1 - $BW))" 2>/dev/null)
echo "P10MATCH|pilot=$NAME|deck=$DECK|games=$G|pilot_vs_champ=${CW}|draws=${CD:-0}|stalls=$(field $F stalls)|turns=$(field $F turns_per_ep)|blocks=$(field $F blocksDeclared)|blockOpps=$(field $F blockOpportunities)|d0_pilot_baseline=${BASE_PILOT}|champ_vs_d0_${NAME}=${BW}" \
    | tee -a $OUT/results.txt
