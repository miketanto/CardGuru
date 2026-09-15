#!/bin/bash
# Phase 13a recording runner: two lanes in parallel until >= TARGET labelled consults
# (y >= 0, all kinds) over rl/artifacts/v7/13/rec/rec13_*.jsonl.
#   lane H: CP7 teacher vs the heuristic, driver 7911, echo 7784, seeds 13000+
#   lane C: CP7 teacher vs CP7 (mirror),  driver 7912, echo 7785, seeds 13500+
# Jobs of EP games (default 50), BenchDimir mirror, seats by episode parity.
# Resumable: a job whose REC13|<tag>| line is in counts.txt and whose jsonl exists is
# skipped. Stop early: touch rl/artifacts/v7/13/rec/STOP (checked between jobs).
# Log: this script's stdout (launch with > rl/artifacts/v7/13/rec/run_13a.log).
# Needs drivers 7911 and 7912 up with the v7 flags (rl/driver_server.sh start).
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
OUT=/mnt/c/Users/sutanto4/Documents/CardGuru/rl/artifacts/v7/13/rec
TARGET=${TARGET:-66000}; EP=${EP:-50}; MAXJOBS=${MAXJOBS:-40}
mkdir -p $OUT
echo "RUN13A|start=$(date -u +%FT%TZ)|target=$TARGET|ep=$EP|maxjobs=$MAXJOBS"

total() {
    cat $OUT/rec13_*.jsonl 2>/dev/null | grep -c '"y":[0-9]'
}

lane() {
    local L=$1 DPORT=$2 EPORT=$3 OPP=$4 SEED0=$5
    local job=0 tag seed
    while [ $job -lt $MAXJOBS ]; do
        [ -f $OUT/STOP ] && { echo "RUN13A|lane=$L|stop_file"; break; }
        [ $(total) -ge $TARGET ] && { echo "RUN13A|lane=$L|target_reached"; break; }
        seed=$((SEED0 + job))
        tag=rec13_${L}_s$seed
        if [ -s $OUT/$tag.jsonl ] && grep -q "REC13|$tag|" $OUT/counts.txt 2>/dev/null; then
            echo "RUN13A|lane=$L|skip=$tag"
        else
            bash $RL/record_13a.sh $tag $EPORT $EP $seed $DPORT $OPP | tee -a $OUT/counts.txt
        fi
        echo "RUN13A|lane=$L|job=$job|labelled_total=$(total)|$(date -u +%FT%TZ)"
        job=$((job + 1))
    done
}

lane H 7911 7784 heuristic 13000 &
PH=$!
lane C 7912 7785 cp7 13500 &
PC=$!
wait $PH $PC
echo "RUN13A|done=$(date -u +%FT%TZ)|labelled_total=$(total)"
