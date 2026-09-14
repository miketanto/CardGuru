#!/bin/bash
# Copy the full debug transcripts (RLGAME blocks) of the NEXT drill-down census of one main
# out of the census driver's server log before the following census overwrites it.
#   bash rl/grab_census_transcripts.sh <main, e.g. M_D> <after block n, e.g. 6>
# Waits for an "L11|check|<main>|n=<k>" line with k > <after>, then copies
# /tmp/rl_p9/driver_server_7913.log's RLGAME blocks to
# rl/artifacts/v7/11/drill/transcripts_<main>_n<k>.txt. Read-only on everything else.
set -u
M=${1:?main}; AFTER=${2:?after block}
LOG=/home/user/CardGuru/rl/artifacts/v7/11/drill/league11.log
SRC=/tmp/rl_p9/driver_server_7913.log
OUTD=/home/user/CardGuru/rl/artifacts/v7/11/drill
echo "GRAB|wait|$M|after=$AFTER|$(date -u +%FT%TZ)"
while true; do
    k=$(grep -o "L11|check|$M|n=[0-9]*" $LOG 2>/dev/null | grep -o '[0-9]*$' | awk -v a=$AFTER '$1>a' | tail -n 1)
    [ -n "$k" ] && break
    sleep 10
done
out=$OUTD/transcripts_${M}_n$(printf '%03d' $k).txt
awk '/^RLGAME\|/{on=1} on{print} /^RLGAME_END/{on=0}' $SRC > $out
n=$(grep -c '^RLGAME|' $out)
w=$(grep -c '^RLGAME|reward=1' $out)
echo "GRAB|done|$M|n=$k|games=$n|wins=$w|file=$out|$(date -u +%FT%TZ)"
