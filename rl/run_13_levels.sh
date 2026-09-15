#!/bin/bash
# Phase 13: the THREE-READOUT level of one checkpoint on the Dimir mirror (rl/PHASE13-BC.md,
# "Evaluation protocol"): CP7 G_CP7 (default 100) then heuristic G_H (default 50) games per readout,
# the same row seeds in every readout (battery row 0 seed 930000), one evaluation at a time.
#   sampled   rl/battery_p12s.sh  (frozen server, -Drl.mode=train: sampled as in training), 7949/7914
#   twostage  rl/battery_xdeck.sh, SRVEXTRA '--device cuda --logit-bound 5 --argmax-classes --argmax-two-stage', 7947/7913
#   argmax    rl/battery_xdeck.sh default (argmax-classes; reported for continuity, never decisive), 7947/7913
#   bash rl/run_13_levels.sh <ckpt> <name> [readouts="sampled twostage argmax"]
# Output rl/artifacts/v7/13/levels/<name>_<readout>_<opp>/ ; one line per row appended to
# rl/artifacts/v7/13/levels/levels.txt:  L13|<name>|<readout>|<opp>|XDECKS|...
# Resumable: a row already in levels.txt is skipped.
[ -f ~/.profile ] && . ~/.profile
set -u
CK=$1; NAME=$2; READOUTS=${3:-"sampled twostage argmax"}
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
RL=/home/user/CardGuru/rl
O=$LB/rl/artifacts/v7/13/levels
mkdir -p $O
touch $O/levels.txt
TWO="--device cuda --logit-bound 5 --argmax-classes --argmax-two-stage"
for ro in $READOUTS; do
    for row in cp7:${G_CP7:-100} heuristic:${G_H:-50}; do
        opp=${row%%:*}; g=${row#*:}
        key="L13|$NAME|$ro|$opp|"
        if grep -q "^$key" $O/levels.txt; then echo "L13|skip|$NAME|$ro|$opp"; continue; fi
        d=$O/${NAME}_${ro}_${opp}
        case $ro in
            sampled)  line=$(G=$g ROWS="$opp:BenchDimir" bash $RL/battery_p12s.sh "$CK" BenchDimir $d 2>&1 | grep -E '^XDECKS?|' | grep -v done | tail -1) ;;
            twostage) line=$(G=$g ROWS="$opp:BenchDimir" SRVEXTRA="$TWO" bash $RL/battery_xdeck.sh "$CK" BenchDimir $d 7947 7913 2>&1 | grep -E '^XDECKS?|' | grep -v done | tail -1) ;;
            argmax)   line=$(G=$g ROWS="$opp:BenchDimir" bash $RL/battery_xdeck.sh "$CK" BenchDimir $d 7947 7913 2>&1 | grep -E '^XDECKS?|' | grep -v done | tail -1) ;;
            *) echo "L13|bad_readout|$ro"; continue ;;
        esac
        if [ -n "$line" ]; then echo "$key$line" | tee -a $O/levels.txt; else echo "L13|FAIL|$NAME|$ro|$opp"; fi
    done
done
echo "L13|done|$NAME|$(date -u +%FT%TZ)"
