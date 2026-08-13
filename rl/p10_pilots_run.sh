#!/bin/bash
# Phase 10 (4.4): run this session's three upper-bound pilots, in order,
# resume-safe. Everything it drives is idempotent (trained.txt, atomic
# net.pt, per-checkpoint probe files, the champion-match guard), so this
# can simply be re-run after any interruption -- including the container
# reboot that killed the first skies run at episode 2112 -- and each
# pilot picks up where it stopped.
#
#   bash rl/p10_pilots_run.sh            # 4096 episodes each
#   P10_BUDGET=6144 bash rl/p10_pilots_run.sh
set -u
RL=/home/user/CardGuru/rl
BUDGET=${P10_BUDGET:-4096}
DPORT=${P10_DRIVER_PORT:-7910}

# name|deck|deck power (p7c_pilot_calib.sh screen A)|seed
PILOTS=(
  "skies|M3BlueSkies.dck|0.71|11"
  "redrush|M3RedRush.dck|0.64|12"
  "ramp|M3GreenRamp.dck|0.60|13"
)

ensure_driver() {
    python3 $RL/driver_client.py --port $DPORT --ping > /dev/null 2>&1 && return 0
    bash $RL/driver_server.sh start $DPORT \
        "-Dmage.randomPerThread=true -XX:+UseParallelGC" > /dev/null 2>&1
}

for P in "${PILOTS[@]}"; do
    IFS='|' read -r NAME DECK POW SEED <<< "$P"
    LOG=/tmp/p10_${NAME}.log
    for attempt in $(seq 1 12); do
        grep -q "P10_DONE" $LOG 2>/dev/null && break
        ensure_driver || { echo "P10_SUPERVISOR|no_driver_server"; exit 1; }
        # a killed lane leaves its policy servers holding the ports
        pkill -f "policy_serve[r].py --port 780" 2>/dev/null
        sleep 2
        P10_CONC=${P10_CONC:-3} P10_POWER=$POW \
            bash $RL/p10_pilot_lane.sh $SEED $NAME $DECK 7801 7802 $BUDGET \
            >> $LOG 2>&1
        grep -q "P10_DONE" $LOG 2>/dev/null && break
        echo "P10_SUPERVISOR|restart|$NAME|attempt=$attempt|trained=$(cat /tmp/rl_p10_pilot_${NAME}/trained.txt 2>/dev/null || echo 0)" \
            | tee -a $LOG
        sleep 10
    done
    grep -q "P10_DONE" $LOG 2>/dev/null \
        || { echo "P10_SUPERVISOR|gave_up|$NAME"; exit 1; }
done
echo "P10_ALL_DONE"
