#!/bin/bash
# Phase 10 B2 (rl/PHASE10-LEAGUE.md): evaluation after the controller stops, ONE job at a
# time (one frozen server + one JVM; the H2H uses two servers). Resumable: every row whose
# probe file exists is skipped by the tools. Final = each main's latest pool snapshot
# (state.json); s1end = pool/<main>_s1end.pt when stage 2 happened.
#   setsid nohup bash rl/p10_eval.sh > /mnt/c/.../rl/artifacts/v7/10/eval/eval.log 2>&1 < /dev/null &
# Prints E10|<job>|... lines (the tools' XDECK| / HARD| / P1| lines prefixed) and E10|done.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
A=$LB/rl/artifacts/v7/10
E=$A/eval
mkdir -p $E
for d in W0Base BenchDimir G1Landfall BenchBurn HoldoutControl HoldoutMidrange W1Fly W1Lif W1Fst W1Vig; do
    cp $RL/$d.dck /home/user/mage/Mage.Tests/ || echo "E10|FAILED|deck $d"
done
latest() { python3 -c "
import json; s=json.load(open('$A/state.json')); n=s['learners']['$1']['latest']; print(s['snaps'][n]['path'] if n else '')"; }
declare -A DECK=([M_W]=W0Base [M_D]=BenchDimir [M_L]=G1Landfall)
echo "E10|start=$(date -u +%FT%TZ)"
# 1. home: vs the heuristic on the own mirror (100) and vs CP7 on the own deck (100)
for m in M_W M_D M_L; do
    ck=$(latest $m); [ -s "$ck" ] || { echo "E10|home|$m|no snapshot"; continue; }
    echo "E10|final|$m|$ck"
    G=100 ROWS="heuristic:${DECK[$m]} cp7:${DECK[$m]}" bash $RL/battery_xdeck.sh "$ck" ${DECK[$m]} $E/${m}_final_home 7948 7914 2>&1 | grep '^XDECK' | grep -v pooled | sed "s/^/E10|home|$m|/"
done
# 2. unseen opponents (heuristic on BenchBurn / HoldoutControl / HoldoutMidrange, 50 each), final and s1end
for m in M_W M_D M_L; do
    for which in final s1end; do
        if [ $which = final ]; then ck=$(latest $m); else ck=$A/pool/${m}_s1end.pt; fi
        [ -s "$ck" ] || { echo "E10|unseen|$m|$which|no checkpoint"; continue; }
        G=50 ROWS="heuristic:BenchBurn heuristic:HoldoutControl heuristic:HoldoutMidrange" \
            bash $RL/battery_xdeck.sh "$ck" ${DECK[$m]} $E/${m}_${which}_unseen 7948 7914 2>&1 | grep '^XDECK' | sed "s/^/E10|unseen|$m|$which|/"
    done
done
# 3. cross matrix: final mains vs each other, own decks, 50 per pair
for pr in "M_W M_D" "M_W M_L" "M_D M_L"; do
    set -- $pr; a=$(latest $1); b=$(latest $2)
    [ -s "$a" ] && [ -s "$b" ] || { echo "E10|cross|$1|$2|missing"; continue; }
    G=50 bash $RL/p10_h2h.sh "$a" ${DECK[$1]} "$b" ${DECK[$2]} $E/cross ${1}_vs_${2} 7948 7914 2>&1 | grep '^HARD' | sed "s/^/E10|cross|/"
done
bash $RL/driver_server.sh stop 7914 > /dev/null 2>&1
# 4. keyword decks for M_W: agent on W1X vs the heuristic on W0Base (50 each) + the heuristic's own shift
ck=$(latest M_W)
for kd in W1Fly W1Lif W1Fst W1Vig; do
    [ -s "$ck" ] && G=50 ROWS="heuristic:W0Base" bash $RL/battery_xdeck.sh "$ck" $kd $E/M_W_kw_$kd 7948 7914 2>&1 | grep '^XDECK' | grep -v pooled | sed "s/^/E10|kw|M_W|/"
done
bash $RL/driver_server.sh start 7914 "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7" > /dev/null 2>&1
cd /home/user/mage
for kd in W0Base W1Fly W1Lif W1Fst W1Vig; do
    f=$E/heur_kw_${kd}.txt
    [ -s $f ] || RL_PERSIST=1 RL_DRIVER_PORT=7914 timeout 3600 bash $RL/run_driver.sh -Drl.episodes=50 -Drl.agent=heuristic -Drl.opponent=heuristic \
        -Drl.searchPlies=1 -Drl.searchBreadth=8 -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.encoderV=7 -Drl.blockAudit=true -Drl.attackAudit=true -Drl.deck=$kd.dck -Drl.oppDeck=W0Base.dck -Drl.stopTurn=60 \
        -Drl.mode=eval -Drl.seed=940000 -Drl.report=0 -Drl.out=$f > $E/heur_kw_${kd}.driver.log 2>&1
    echo "E10|kwref|heuristic|$kd|$(grep -o 'wins=[0-9]*\|episodes=[0-9]*\|win_rate=[0-9.]*' $f | paste -sd' ')"
done
bash $RL/driver_server.sh stop 7914 > /dev/null 2>&1
cd /home/user/CardGuru
# 5. card use: P1 card-swap on the three final mains vs the fresh flag-ON net (A2's init_on.pt)
if ! grep -q '^P1|M_L|reading' $E/p1/cardswap_summary.txt 2>/dev/null; then
    python3 rl/p10_cardswap.py --out $E/p1 --ckpt FRESH_ON=$A/a2/init_on.pt \
        --ckpt M_W=$(latest M_W) --ckpt M_D=$(latest M_D) --ckpt M_L=$(latest M_L) \
        "$LB/rl/artifacts/v7/wire3a/7c_W0Base_*.jsonl" "$LB/rl/artifacts/v7/wire3a/7c_BenchDimir_*.jsonl" > $E/p1_run.log 2>&1
fi
grep -h '^P1|[A-Z_]*|\(text\|pt\|type\)|' $E/p1/cardswap_summary.txt 2>/dev/null | cut -d'|' -f1-4 | sed 's/^/E10|p1|/'
echo "E10|done=$(date -u +%FT%TZ)"
