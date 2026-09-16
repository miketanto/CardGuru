#!/bin/bash
# Phase 15: the unattended GPU chain, so no rung waits on a human noticing.
#   bash rl/chain_15.sh    (launch detached; log rl/artifacts/v7/15/chain_15.log)
# Waits for the A1 POLICY stage to exit, then runs, in order, one GPU process at a time:
#   1. A1 value stage   (rl/p15_a1.py --stage value, the D1 critic at the same fractions)
#   2. A2               (rl/run_15a2.sh: card-blind floor clone, probe 1, probe 3, card-swap)
#   3. A4L ladder       (rl/run_15a4.sh: gate -> rung clone -> joint clone -> eval per rung;
#                        its recording steps are skipped for any deck rl/run_15recall.sh
#                        has already finished, and it waits for the recorder to be done)
# Every step is itself resumable (each writes JSONs / checkpoints it then skips), so
# killing this chain costs the step in flight, never the night.
# Stop cleanly: touch rl/artifacts/v7/15/CHAINSTOP (checked between steps).
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
A=$LB/rl/artifacts/v7/15
REC=$LB/rl/artifacts/v7/13/rec
mkdir -p $A
cd /home/user/CardGuru
say() { echo "C15|$*|$(date -u +%FT%TZ)"; }
stop_check() { [ -f $A/CHAINSTOP ] && { say "stopfile"; exit 0; }; return 0; }

say "start"
# 1. wait for the policy stage's OUTPUT (cap 4 h), then run the value stage.
#
# This waits on FILES, never on pgrep. The first version polled
# `pgrep -f "p15_a1.py --stage policy"` and hung for 20 minutes with the box idle,
# because any wrapper shell whose argv merely CONTAINS that string matches it - and one
# did: a `bash -lc timeout 2400 bash -c 'while pgrep -f "p15_a1.py --stage policy" ...'`
# watcher launched from outside this script. That is the CLAUDE.md hazard ("pkill -f
# matches the wrapper shell's own argv") in its polling form, and the [b]racket trick
# does not help, since the text is genuinely present in the other process's argv.
# The four per-fraction JSONs are the stage's real completion signal and cannot be
# spoofed by anyone's command line.
T=0
while [ "$(ls $A/a1/a1_policy_*.json 2>/dev/null | wc -l)" -lt 4 ]; do
    sleep 30; T=$((T + 30))
    [ $T -ge 14400 ] && { say "policy points still incomplete after 4 h - going on anyway"; break; }
done
say "policy stage points=$(ls $A/a1/a1_policy_*.json 2>/dev/null | wc -l)"
stop_check
if [ "$(ls $A/a1/a1_value_*.json 2>/dev/null | wc -l)" -ge 4 ]; then
    say "a1 value|skip"
else
    python3 $RL/p15_a1.py --stage value --ckpt $LB/rl/artifacts/v7/13/bc/bc.pt --out $A/a1 \
        --device cuda $REC/rec13_*.jsonl >> $A/a1/a1_value.log 2>&1
    say "a1 value|rc=$?"
    grep '^A1|.*POINT' $A/a1/a1_value.log | sed 's/^/C15|a1v|/'
fi

# 2. A2
stop_check
bash $RL/run_15a2.sh >> $A/a2/run_15a2.log 2>&1
say "a2|rc=$?"
grep '^A2RUN|' $A/a2/run_15a2.log | tail -20 | sed 's/^/C15|a2|/'

# 3. A4L ladder - wait for the engine-side recorder to finish first so the two never
#    compete for RAM (the recorder is engine-only, the ladder's clone steps are GPU).
stop_check
T=0
while pgrep -f "run_15recal[l]\.sh" > /dev/null; do
    sleep 60; T=$((T + 60)); [ $T -ge 21600 ] && { say "recorder still running after 6 h - starting the ladder anyway"; break; }
done
say "recorder done or timed out|starting ladder"
bash $RL/run_15a4.sh >> $A/a4/run_15a4.log 2>&1
say "a4|rc=$?"
say "done"
