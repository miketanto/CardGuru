#!/bin/bash
# Does privileged information predict the outcome better? A SUPERVISED
# probe, with the policy untouched.
#
#   nohup bash rl/oracle_probe_ab.sh > /tmp/oracle_probe.log 2>&1 &
#
# The first attempt wired the fresh critic straight into GAE and it
# diverged (-1.47 -> -6.05): `ret = gae + values` is built from the
# critic's own values, so a randomly-initialised critic trained on ret
# bootstraps off its own noise. Recorded in ORACLE-GUIDING.md.
#
# This asks the question the way it should have been asked first. Both
# arms run --oracle-probe: the critic learns from MONTE-CARLO returns
# (exact, under terminal-only reward) and is SCORED, but never supplies
# GAE - so the policy trajectory is identical in both arms and the ONLY
# difference is what the critic can see.
#
#   probe0 : fresh critic, ordinary observation
#   probe1 : fresh critic, + the opponent's hand
#
# critic_ev is held out: scored on each batch BEFORE training on it.
# If probe1 does not beat probe0, hidden information is not what the
# value function is missing, and the next lever is rollout-delta
# targets, where the signal is measured rather than estimated.
set -u
RL=/home/user/CardGuru/rl
CKPT=${ORACLE_CKPT:-/tmp/rl_b1narrow/ck_1024.pt}
DECK=${ORACLE_DECK:-B1Narrow}
EPS=${ORACLE_EPS:-256}

arm() {   # $1 = 0|1 privileged
    echo "=== PROBE oracle=$1 === $(date -u +%H:%M:%S)"
    pkill -f "[R]LDriverServer" 2>/dev/null
    sleep 3
    if [ "$1" = "1" ]; then
        EV_ORACLE=1 EV_OUT=/tmp/rl_probe_${DECK}_or1 \
            timeout 7200 bash $RL/ev_probe.sh "$CKPT" "$DECK" "$EPS" 7995
    else
        SRV_FORCE_ORACLE=1 EV_OUT=/tmp/rl_probe_${DECK}_or0 \
            timeout 7200 bash $RL/ev_probe.sh "$CKPT" "$DECK" "$EPS" 7995
    fi
    echo "=== PROBE oracle=$1 exit=$? === $(date -u +%H:%M:%S)"
}

arm 0
arm 1
echo "ORACLE_PROBE_DONE $(date -u +%H:%M:%S)"
