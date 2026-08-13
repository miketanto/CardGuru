#!/bin/bash
# Phase 10 action 4.4 driver: three upper-bound pilots, sequentially,
# each followed by its 200g match against the project champion.
#
# Everything here is RESUMABLE and idempotent. The container this runs in
# is stopped whenever the session goes idle, which kills the lane and the
# driver JVM but leaves /tmp intact; re-running this script picks up from
# the last completed 64-episode chunk (trained.txt), re-uses every probe
# file that already exists, and skips pilots that are already done.
#
# Usage: bash rl/p10_run_all.sh [budget=4096]
set -u
BUDGET=${1:-4096}
RL=/home/user/CardGuru/rl
LOG=/tmp/p10_run_all.log

# one persistent driver JVM for the whole session
if ! python3 $RL/driver_client.py --port 7910 --ping > /dev/null 2>&1; then
    bash $RL/driver_server.sh start 7910 \
        "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on" \
        >> $LOG 2>&1 || { echo "P10RUN|driver_server_failed"; exit 1; }
fi

# name deck seed aport oport
PILOTS=(
  "sweep|P7cSweepControl.dck|1|7841|7842"
  "tokens|M3SelesnyaTokens.dck|2|7843|7844"
  "wweenie|M3WhiteWeenie.dck|3|7845|7846"
)

for P in "${PILOTS[@]}"; do
    IFS='|' read -r NAME DECK SEED APORT OPORT <<< "$P"
    OUT=/tmp/rl_p10_pilot_${NAME}
    T=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
    if [ "$T" -lt "$BUDGET" ]; then
        echo "P10RUN|starting|$NAME|from=$T|budget=$BUDGET"
        bash $RL/pilot_lane_p10.sh $NAME $DECK $SEED $APORT $OPORT \
            /tmp/rl_p7_scratch_init.pt $BUDGET >> /tmp/p10_${NAME}.log 2>&1
        T=$(cat $OUT/trained.txt 2>/dev/null || echo 0)
        [ "$T" -lt "$BUDGET" ] && { echo "P10RUN|interrupted|$NAME|at=$T"; exit 1; }
    fi
    [ -f $OUT/p10_${NAME}_final.pt ] || cp $OUT/net.pt $OUT/p10_${NAME}_final.pt
    if [ ! -s /tmp/rl_p10_matches/champ_${NAME}.txt ] \
       || [ ! -s /tmp/rl_p10_matches/base_${NAME}.txt ]; then
        echo "P10RUN|match|$NAME"
        bash $RL/p10_pilot_match.sh $NAME $DECK $OUT/p10_${NAME}_final.pt \
            $APORT $OPORT 200 100 2>&1 | tee -a /tmp/p10_${NAME}.log
    fi
    echo "P10RUN|pilot_complete|$NAME"
done
echo "P10RUN|ALL_DONE"
