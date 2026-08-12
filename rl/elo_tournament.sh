#!/bin/bash
# Phase 6: Elo tournament. Policies meet every scripted anchor (D0, D1,
# D1h - encoding-agnostic Java seats bridge the cdim-38 and cdim-91
# families onto one scale) and every same-family policy. 100g/pairing,
# fixed seed block, argmax, no-yields. Scripted-vs-scripted pairs reuse
# the existing 500g calibrations (fed to the fitter separately).
# Output: /tmp/rl_elo/matches.tsv  (A  B  winsA  draws  games)
# Usage: bash rl/elo_tournament.sh [games_per_pairing=100]
set -u
G=${1:-100}
OUT=/tmp/rl_elo
FEATS=/home/user/CardGuru/rl/e2_features.tsv
ESEED=980000
mkdir -p $OUT

# name|arch|ckpt   (arch e0->cdim38 no feats; attn->cdim91 feats)
POLICIES=(
  "e0_bc|e0|/tmp/rl_p5_c1/student_v3.pt"
  "e0_ppo|e0|/tmp/rl_c2v3_noshape_s0/net.pt"
  "e0_champ|e0|/tmp/rl_league_bc_s0/e0_league_final.pt"
  "attn_bc|attn|/tmp/rl_p5_c1/student_e2attn.pt"
  "attn_v2|attn|/tmp/rl_c6_attn_s0/attn_v2_final.pt"
  "attn_desp|attn|/tmp/rl_c6_attn_s7/attn_desp_final.pt"
)
SCRIPTED=("D0|heuristic" "D1|search" "D1h|searchhold")

serve() {  # $1 ckpt $2 arch $3 port $4 log -> pid in $OUT/.pid
    local CDIM=38; [ "$2" != "e0" ] && CDIM=91
    local try
    for try in 1 2 3; do
        rm -f "$4"
        python3 /home/user/CardGuru/rl/policy_server.py --port $3 \
            --ckpt "$1" --seed 0 --arch $2 --cdim $CDIM > "$4" 2>&1 &
        echo $! > $OUT/.pid
        local up=0; SECONDS=0
        while [ $SECONDS -lt 90 ]; do
            grep -q "policy server" "$4" 2>/dev/null && { up=1; break; }
            grep -q "Traceback" "$4" 2>/dev/null && break
        done
        [ "$up" = "1" ] && return 0
        kill $(cat $OUT/.pid) 2>/dev/null; wait $(cat $OUT/.pid) 2>/dev/null
        grep -q "Address already in use" "$4" 2>/dev/null || break
    done
    echo "ELO_FAILED|server|$1"; cat "$4"; exit 1
}

run_match() {  # $1 tag $2 extra driver args (opponent config) $3 arch $4 feats-flag
    local FEATARG=""
    [ "$3" != "e0" ] && FEATARG="-Drl.cardFeatures=$FEATS"
    cd /home/user/mage
    mvn -q -pl Mage.Tests surefire:test -Dtest='RLEpisodeDriver' \
        -DargLine="-Dfile.encoding=UTF-8 -Xmx4500m" \
        -DfailIfNoTests=false -Drl.episodes=$G \
        -Drl.agent=rl -Drl.policy=socket -Drl.port=9001 $FEATARG \
        $2 \
        -Drl.noYields=true -Drl.consultBudget=4000 \
        -Drl.deck=BenchDimir.dck -Drl.stopTurn=80 \
        -Drl.mode=eval -Drl.seed=$ESEED -Drl.report=0 \
        -Drl.out=$OUT/m_${1}.txt > /dev/null 2>&1
    cd /home/user/CardGuru
}

record() {  # $1 A $2 B $3 tag
    local line=$(tail -1 $OUT/m_${3}.txt 2>/dev/null)
    [ -z "$line" ] && { echo "ELO_FAILED|no_summary|$3"; exit 1; }
    local w=$(echo "$line" | grep -o 'wins=[0-9]*' | cut -d= -f2)
    local d=$(echo "$line" | grep -o 'draws=[0-9]*' | cut -d= -f2)
    echo -e "$1\t$2\t$w\t$d\t$G" >> $OUT/matches.tsv
    echo "ELO|$1 vs $2: $w/$G (draws $d)"
}

: > $OUT/matches.tsv

# policy vs scripted anchors
for P in "${POLICIES[@]}"; do
    IFS='|' read -r PN PA PC <<< "$P"
    [ -f "$PC" ] || { echo "ELO_FAILED|missing ckpt $PC"; exit 1; }
    for S in "${SCRIPTED[@]}"; do
        IFS='|' read -r SN SK <<< "$S"
        serve "$PC" "$PA" 9001 $OUT/s_a.log; SRV=$(cat $OUT/.pid)
        run_match "${PN}_${SN}" "-Drl.opponent=$SK -Drl.searchPlies=1 -Drl.searchBreadth=8" "$PA"
        kill $SRV 2>/dev/null; wait $SRV 2>/dev/null
        record "$PN" "$SN" "${PN}_${SN}"
    done
done

# within-family policy vs policy
pv() {  # $1 A-entry $2 B-entry
    IFS='|' read -r AN AA AC <<< "$1"
    IFS='|' read -r BN BA BC <<< "$2"
    serve "$AC" "$AA" 9001 $OUT/s_a.log; SRVA=$(cat $OUT/.pid)
    serve "$BC" "$BA" 9002 $OUT/s_b.log; SRVB=$(cat $OUT/.pid)
    run_match "${AN}_${BN}" "-Drl.opponent=rl -Drl.oppPort=9002" "$AA"
    kill $SRVA $SRVB 2>/dev/null; wait $SRVA $SRVB 2>/dev/null
    record "$AN" "$BN" "${AN}_${BN}"
}
pv "${POLICIES[0]}" "${POLICIES[1]}"
pv "${POLICIES[0]}" "${POLICIES[2]}"
pv "${POLICIES[1]}" "${POLICIES[2]}"
pv "${POLICIES[3]}" "${POLICIES[4]}"
pv "${POLICIES[3]}" "${POLICIES[5]}"
pv "${POLICIES[4]}" "${POLICIES[5]}"

echo "ELO_TOURNAMENT_DONE"
