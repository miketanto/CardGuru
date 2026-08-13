#!/bin/bash
# Phase 7c pre-flight: budget-test every candidate archetype deck, then
# screen it against the FROZEN starting agent to fix the easiest-first
# curriculum order.
#
# Two stages, both mandated by the kickoff:
#  1. budget test - 4 episodes per deck. The M3 hard rule: never trust a
#     new deck until it has actually run (the Gurmag delve incident OOM'd
#     a 4.5G heap mid-game). A deck that hangs, OOMs, or burns its
#     consult budget is dropped here, not at 2am.
#  2. screen - $SCREEN_G games vs D0 piloting the deck, agent on
#     BenchDimir, argmax. Order = agent win rate DESCENDING, i.e.
#     easiest archetype first.
#
# Writes rl/p7c_curriculum.tsv: order<TAB>name<TAB>deck<TAB>kind<TAB>elo
# The seeded elo is a rough pool prior from the screen result against the
# agent's known 916 rating; the lane recomputes ratings at every
# checkpoint anyway.
#
# Usage: bash rl/p7c_screen.sh <agentPort> [initCkpt]
set -u
APORT=${1:-7801}
INIT=${2:-/tmp/rl_p7_lstmattn_s0/p7_final.pt}
RL=/home/user/CardGuru/rl
OUT=/tmp/rl_p7c_screen
ARCH=lstmattn
CDIM=91
DECK=BenchDimir.dck
FEATS=$RL/e2_features.tsv
SELF_ELO=${P7C_SELF_ELO:-916}
SCREEN_G=${P7C_SCREEN_G:-40}
mkdir -p $OUT

# candidate pool: the four archetype axes the kickoff names, plus a
# plain small-creature aggro deck as the gentle on-ramp.
CANDIDATES=(
  "wweenie|M3WhiteWeenie.dck|mono-white small-creature aggro"
  "redrush|M3RedRush.dck|mono-red fast aggro with reach"
  "tokens|M3SelesnyaTokens.dck|go-wide tokens (blocking math)"
  "skies|M3BlueSkies.dck|blue flash/tempo fliers"
  "ramp|M3GreenRamp.dck|green ramp, big top-end"
  "sweep|P7cSweepControl.dck|azorius sweepers + counters"
)

start_server() {
    local try
    for try in 1 2 3; do
        rm -f $OUT/server.log
        python3 $RL/policy_server.py --port $APORT --ckpt "$INIT" \
            --seed 0 --cdim $CDIM --arch $ARCH > $OUT/server.log 2>&1 &
        echo $! > $OUT/.srvpid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" $OUT/server.log 2>/dev/null && { up=1; break; }
            grep -q "Traceback" $OUT/server.log 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat $OUT/.srvpid) 2>/dev/null; wait $(cat $OUT/.srvpid) 2>/dev/null
        grep -q "Address already in use" $OUT/server.log 2>/dev/null || break
    done
    echo "SCREEN_FAILED|server_never_started"; cat $OUT/server.log; exit 1
}
stop_server() { kill $1 2>/dev/null; wait $1 2>/dev/null; }

run() {  # $1 out $2 deck $3 episodes $4 seed
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=$3 \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=$APORT \
        -Drl.opponent=heuristic -Drl.cardFeatures=$FEATS \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=$DECK -Drl.oppDeck=$2 -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$4 -Drl.report=0 \
        -Drl.out=$1 > /dev/null 2>&1
}

cd /home/user/mage
echo "=== stage 1: budget test (4 episodes each) ==="
GOOD=()
for C in "${CANDIDATES[@]}"; do
    IFS='|' read -r NAME DCK DESC <<< "$C"
    F=$OUT/budget_${NAME}.txt
    rm -f $F
    start_server; SRV=$(cat $OUT/.srvpid)
    SECONDS=0
    run $F $DCK 4 940000
    EL=$SECONDS
    stop_server $SRV
    if [ ! -s "$F" ]; then
        echo "DROP|$NAME|$DCK|budget test produced no summary (${EL}s)"
        continue
    fi
    CONS=$(grep -o 'agent_consults_per_ep=[0-9.]*' $F | cut -d= -f2)
    TURNS=$(grep -o 'turns_per_ep=[0-9.]*' $F | cut -d= -f2)
    echo "OK|$NAME|$DCK|consults/ep=$CONS|turns/ep=$TURNS|${EL}s|$DESC"
    GOOD+=("$C")
done

echo "=== stage 2: screen vs frozen agent (${SCREEN_G}g each) ==="
: > $OUT/screen.txt
for C in "${GOOD[@]}"; do
    IFS='|' read -r NAME DCK DESC <<< "$C"
    F=$OUT/screen_${NAME}.txt
    if [ ! -s "$F" ]; then
        start_server; SRV=$(cat $OUT/.srvpid)
        run $F $DCK $SCREEN_G 952000
        stop_server $SRV
    fi
    WR=$(grep -o 'win_rate=[0-9.]*' $F | head -1 | cut -d= -f2)
    ST=$(grep -o 'stalls=[0-9]*' $F | head -1 | cut -d= -f2)
    BD=$(grep -o 'blocksDeclared=[0-9]*' $F | cut -d= -f2)
    BO=$(grep -o 'blockOpportunities=[0-9]*' $F | cut -d= -f2)
    echo -e "${WR:-0}\t${NAME}\t${DCK}\t${DESC}\tstalls=${ST:-0}\tblocks=${BD:-0}/${BO:-0}" \
        >> $OUT/screen.txt
    echo "SCREEN|$NAME|win_rate=${WR:-NA}|stalls=${ST:-0}|blocks=${BD:-0}/${BO:-0}"
done

# easiest first = highest agent win rate first. Seed each row's pool Elo
# from the screen: elo = self + 400*log10((1-wr)/wr), clamped.
sort -rn $OUT/screen.txt | awk -v self=$SELF_ELO 'BEGIN{OFS="\t"; print "#order","name","deck","kind","elo"}
{
  wr=$1; if (wr<0.03) wr=0.03; if (wr>0.97) wr=0.97;
  elo = self + 400*log((1-wr)/wr)/log(10);
  if (elo < self-400) elo = self-400; if (elo > self+400) elo = self+400;
  printf "%d\t%s\t%s\t%s\t%d\n", NR, $2, $3, "heuristic", elo;
}' > $RL/p7c_curriculum.tsv

echo "=== curriculum (easiest first) ==="
cat $RL/p7c_curriculum.tsv
