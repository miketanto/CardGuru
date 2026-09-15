#!/bin/bash
# Phase 14 D2b companion: bc.pt's TWO-STAGE level vs CP7 at the D2a rung skill, 100 games, BenchDimir,
# row seed 930000 - the comparison row for D2b's two-stage level (D2a measures bc.pt sampled only).
#   SKILL=<n> bash rl/run_14bcts.sh
# One frozen server + one driver JVM (7946 / 7915), so it fits beside the D2b lane (1 + 1) under the
# box rule. Resumable: battery_x14.sh skips a row whose probe file exists.
# Output: rl/artifacts/v7/14/d2a/bc_twostage.log (XDECK| line), probes under d2a/bc_ts_s<SKILL>/.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
SKILL=${SKILL:?set SKILL to the D2a rung}
RL=/home/user/CardGuru/rl
A=$RL/artifacts/v7/14/d2a
CK=$RL/artifacts/v7/13/bc/bc.pt
TWO="--device cuda --logit-bound 5 --argmax-classes --argmax-two-stage"
mkdir -p $A
echo "BCTS|start|$(date -u +%FT%TZ)|skill=$SKILL" >> $A/bc_twostage.log
SKILL=$SKILL G=100 ROWS="cp7:BenchDimir" SRVEXTRA="$TWO" \
    bash $RL/battery_x14.sh $CK BenchDimir $A/bc_ts_s$SKILL 7946 7915 >> $A/bc_twostage.log 2>&1
echo "BCTS|done|$(date -u +%FT%TZ)" >> $A/bc_twostage.log
