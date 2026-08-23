#!/bin/bash
# Oracle guiding, A/B'd on the quantity it is supposed to move.
#
#   nohup bash rl/oracle_ab.sh > /tmp/oracle_ab.log 2>&1 &
#
# THE READOUT IS EXPLAINED VARIANCE, NOT A WIN RATE. With terminal-only
# reward and GAE, every non-terminal residual is gamma*V(s') - V(s), so
# the critic IS the dense credit path; EV = 1 - Var(mc - V)/Var(mc)
# against the actual per-consult-discounted outcome says how much of the
# return that path explains. If privileged information does not move EV,
# the mechanism did not fire and no win-rate run is earned.
#
# Baseline first, then oracle, on the SAME starting checkpoint and the
# same episode budget. Sequential because -Drl.oracle is a class-init
# constant: a driver JVM that served one arm cannot serve the other, so
# it is killed between them (HANDOFF-ENCODER-V6.md §5).
#
# Uses B1Narrow's ck_1024, which is pristine at 1024/32. B1Fast's was
# mutated by a probe that trained it (B1-TIMING-AB.md §7a).
set -u
RL=/home/user/CardGuru/rl
CKPT=${ORACLE_CKPT:-/tmp/rl_b1narrow/ck_1024.pt}
DECK=${ORACLE_DECK:-B1Narrow}
EPS=${ORACLE_EPS:-256}

arm() {   # $1 = 0|1 oracle
    echo "=== ARM oracle=$1 === $(date -u +%H:%M:%S)"
    pkill -f "[R]LDriverServer" 2>/dev/null
    sleep 3
    EV_ORACLE=$1 timeout 7200 bash $RL/ev_probe.sh "$CKPT" "$DECK" "$EPS" 7993
    echo "=== ARM oracle=$1 exit=$? === $(date -u +%H:%M:%S)"
}

arm 0
arm 1
echo "ORACLE_AB_DONE $(date -u +%H:%M:%S)"
