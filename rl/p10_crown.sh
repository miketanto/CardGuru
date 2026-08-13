#!/bin/bash
# Phase 10 action #1: crown the champion. Three independent eval lanes,
# run as separate background tasks (they share nothing but the CPU).
#   bash rl/p10_crown.sh d1_500       500g ck_6144 vs D1, mirror
#   bash rl/p10_crown.sh h2h          200g vs 7c ck_1536, then ck_3072
#   bash rl/p10_crown.sh arch         100g vs D0 x redrush/ramp/sweep
# All sequential (eval protocol), fresh servers, unique ports per lane.
set -u
LANE=$1
CG=/home/user/CardGuru
CHAMP=/tmp/rl_p7_lstmattn_s0/p7b_champion.pt
OUT=/tmp/p10_crown
mkdir -p $OUT
cd /home/user/mage

serve() { # ckpt port log
    pkill -f "policy_serve[r].py --port $2" 2>/dev/null; sleep 1
    python3 $CG/rl/policy_server.py --port $2 --ckpt $1 --seed 0 \
        --arch lstmattn --cdim 91 > $3 2>&1 &
    echo $!
    until grep -q "policy server" $3 2>/dev/null; do sleep 1; done
}

run() { # episodes opponent extra outfile
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m -Dmage.playableCache=on" \
        -DfailIfNoTests=false -Drl.episodes=$1 \
        -Drl.agent=rl -Drl.policy=socket \
        -Drl.cardFeatures=$CG/rl/e2_features.tsv \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=BenchDimir.dck -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.report=0 \
        -Drl.opponent=$2 $3 -Drl.out=$4 > /dev/null 2>&1
}

case $LANE in
d1_500)
    P=$(serve $CHAMP 9340 $OUT/s9340.log)
    run 500 search "-Drl.port=9340 -Drl.searchPlies=1 -Drl.searchBreadth=8 -Drl.seed=950100" \
        $OUT/d1_500.txt
    kill $P 2>/dev/null
    echo "CROWN|d1_500|$(grep -o 'win_rate=[0-9.]*' $OUT/d1_500.txt | tail -1)"
    ;;
h2h)
    for OPP in 1536 3072; do
        PA=$(serve $CHAMP 9342 $OUT/s9342.log)
        PB=$(serve /tmp/p10_crown/c7c_${OPP}.pt 9343 $OUT/s9343.log)
        run 200 rl "-Drl.port=9342 -Drl.oppPort=9343 -Drl.seed=95120$((OPP/1536))" \
            $OUT/h2h_${OPP}.txt
        kill $PA $PB 2>/dev/null
        echo "CROWN|h2h_${OPP}|$(grep -o 'win_rate=[0-9.]*' $OUT/h2h_${OPP}.txt | tail -1)"
    done
    ;;
arch)
    for ROW in M3RedRush M3GreenRamp P7cSweepControl; do
        P=$(serve $CHAMP 9344 $OUT/s9344.log)
        run 100 heuristic "-Drl.port=9344 -Drl.oppDeck=${ROW}.dck -Drl.seed=950300" \
            $OUT/arch_${ROW}.txt
        kill $P 2>/dev/null
        echo "CROWN|arch_${ROW}|$(grep -o 'win_rate=[0-9.]*' $OUT/arch_${ROW}.txt | tail -1)"
    done
    ;;
esac
echo "CROWN_DONE|$LANE"
