#!/bin/bash
# Phase 14 D2a (rl/PHASE14-DIAG.md): bc.pt SAMPLED levels vs CP7 skill 1 and skill 3 on BenchDimir,
# 100 games each, row seed 930000 (the seed of bc.pt's skill-6 sampled level in 13b).
# Two frozen servers + two driver JVMs in parallel (box rule: <= 2 + 2): skill 1 on 7949/7914,
# skill 3 on 7947/7913. Resumable: battery_p14s.sh skips a row whose probe file exists.
# Output: rl/artifacts/v7/14/d2a/run.log (XDECKS|...|skill=N| lines), probe files under s1/ s3/.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
A=/home/user/CardGuru/rl/artifacts/v7/14/d2a
CK=/home/user/CardGuru/rl/artifacts/v7/13/bc/bc.pt
mkdir -p $A
echo "D2A|start|$(date -u +%FT%TZ)" >> $A/run.log
( SKILL=1 G=100 ROWS="cp7:BenchDimir" bash rl/battery_p14s.sh $CK BenchDimir $A/s1 7949 7914 >> $A/run_s1.log 2>&1 ) &
sleep 30
( SKILL=3 G=100 ROWS="cp7:BenchDimir" bash rl/battery_p14s.sh $CK BenchDimir $A/s3 7947 7913 >> $A/run_s3.log 2>&1 ) &
wait
cat $A/run_s1.log $A/run_s3.log | grep '^XDECKS|ck' >> $A/run.log
echo "D2A|done|$(date -u +%FT%TZ)" >> $A/run.log
