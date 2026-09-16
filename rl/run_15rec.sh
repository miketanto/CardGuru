#!/bin/bash
# Phase 15 A4L recording runner: the 13a job shape (two lanes in parallel) on one
# ladder deck, until GAMES games are recorded.
#   bash rl/run_15rec.sh <deck> [games, default 1000] [seed base, default 15000]
#   lane H: CP7 teacher vs the heuristic, driver 7911, echo 7784, seeds BASE+0..
#   lane C: CP7 teacher vs CP7 (mirror),  driver 7912, echo 7785, seeds BASE+500..
# Jobs of EP games (default 50), the deck's own mirror, seats by episode parity.
# RESUMABLE and IDEMPOTENT: a job whose REC15|<tag>| line is in the deck's
# counts.txt and whose jsonl exists is skipped; a deck whose DONE file exists
# exits immediately. Stop early: touch rl/artifacts/v7/15/rec/<deck>/STOP.
# Starts the two driver JVMs if they are not up and leaves them up (the caller
# stops them with rl/stop_15rec.sh); no policy server is involved, so this runs
# beside one GPU trainer within the box rule.
[ -f ~/.profile ] && . ~/.profile
set -u
RL=/home/user/CardGuru/rl
LB=/mnt/c/Users/sutanto4/Documents/CardGuru
DECK=${1:?deck}
GAMES=${2:-1000}
BASE=${3:-15000}
EP=${EP:-50}
OUT=$LB/rl/artifacts/v7/15/rec/$DECK
mkdir -p $OUT
[ -f $RL/$DECK.dck ] || { echo "RUN15REC|$DECK|no deck file"; exit 2; }
if [ -f $OUT/DONE ]; then echo "RUN15REC|$DECK|already_done"; exit 0; fi
echo "RUN15REC|start=$(date -u +%FT%TZ)|deck=$DECK|games=$GAMES|ep=$EP|base=$BASE"

ends() { cat $OUT/*.jsonl 2>/dev/null | grep -c '"t":"end"'; }

for P in 7911 7912; do
    if ! pgrep -f "RLDriverServe[r] --port $P" > /dev/null; then
        bash $RL/driver_server.sh start $P "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7" \
            || { echo "RUN15REC|$DECK|driver $P failed"; exit 1; }
    fi
done

lane() {
    local L=$1 DPORT=$2 EPORT=$3 OPP=$4 SEED0=$5 NJOB=$6
    local job=0 tag seed
    while [ $job -lt $NJOB ]; do
        [ -f $OUT/STOP ] && { echo "RUN15REC|$DECK|lane=$L|stop_file"; break; }
        seed=$((SEED0 + job))
        tag=rec15_${DECK}_${L}_s$seed
        if [ -s $OUT/$tag.jsonl ] && grep -q "REC15|$tag|" $OUT/counts.txt 2>/dev/null; then
            echo "RUN15REC|$DECK|lane=$L|skip=$tag"
        else
            bash $RL/record_15.sh $DECK $tag $EPORT $EP $seed $DPORT $OPP | tee -a $OUT/counts.txt
        fi
        job=$((job + 1))
    done
}

HALF=$(( GAMES / 2 ))
NJ=$(( (HALF + EP - 1) / EP ))
lane H 7911 7784 heuristic $BASE $NJ &
PH=$!
lane C 7912 7785 cp7 $((BASE + 500)) $NJ &
PC=$!
wait $PH $PC
E=$(ends)
echo "RUN15REC|$DECK|games_recorded=$E|labelled=$(cat $OUT/*.jsonl 2>/dev/null | grep -c '"y":[0-9]')|$(date -u +%FT%TZ)"
[ "$E" -ge "$(( GAMES - EP ))" ] && touch $OUT/DONE
echo "RUN15REC|done=$(date -u +%FT%TZ)|deck=$DECK"
