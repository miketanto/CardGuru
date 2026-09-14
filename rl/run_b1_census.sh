#!/bin/bash
# Phase 11 B1: baseline census recordings, one at a time (rl/PHASE11-DRILL.md Part B1).
# 50 argmax games vs the heuristic (seed 11000) and 25 vs CP7 (seed 11500), own mirror, for
# M_D_s1end, M_D_04096 (Phase 10 final), M_L_s1end, M_L_03840 (Phase 10 final), via
# rl/record_census.sh (server 7947, proxy 7948, driver 7913). Resumable: a tag whose counts file
# already carries census lines is skipped.
# Prints B1|start, per recording the CENSUSREC| / DC| / LC| lines, then B1|done|<utc>.
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
POOL=$LB/rl/artifacts/v7/10/pool
OUT=$LB/rl/artifacts/v7/11
cd /home/user/CardGuru || exit 1
echo "B1|start|$(date -u +%FT%TZ)"
for spec in "M_D_s1end BenchDimir" "M_D_04096 BenchDimir" "M_L_s1end G1Landfall" "M_L_03840 G1Landfall"; do
    set -- $spec; CK=$1; DECK=$2
    for og in "heuristic 50 11000" "cp7 25 11500"; do
        set -- $og; OPP=$1; G=$2; SEED=$3
        TAG=b1_${CK}_${OPP}
        if grep -q '^DC|\|^LC|' $OUT/rec_$TAG.counts.txt 2>/dev/null; then echo "B1|skip|$TAG"; continue; fi
        bash $LB/rl/record_census.sh $POOL/$CK.pt $DECK $OPP $G $TAG $SEED 2>&1 | grep -a '^CENSUSREC|\|^DC|\|^LC|\|Exception'
    done
done
echo "B1|done|$(date -u +%FT%TZ)"
