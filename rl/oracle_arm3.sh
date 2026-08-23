#!/bin/bash
# The control the oracle A/B needs: a FRESH critic with NO privileged
# input, same architecture, same budget, same starting checkpoint.
#
#   nohup bash rl/oracle_arm3.sh > /tmp/oracle_arm3.log 2>&1 &
#
# WHY. `oracle_ab.sh` compares the policy's own value head - which has
# 1024 episodes of training behind it - against an OracleCritic that
# starts from scratch. That confounds "the critic can see the opponent's
# hand" with "the critic is a new network". This arm runs the same fresh
# OracleCritic with the driver NOT emitting "oe", so:
#
#   arm 1 (or0) : pre-trained policy value head, no oracle   [baseline]
#   arm 2 (or1) : fresh critic, WITH the opponent's hand
#   arm 3 (or2) : fresh critic, WITHOUT it                   [control]
#
# arm2 - arm3 is the privileged-information effect with the
# fresh-network confound removed. arm3 - arm1 prices the confound
# itself, which is worth knowing on its own.
set -u
RL=/home/user/CardGuru/rl
CKPT=${ORACLE_CKPT:-/tmp/rl_b1narrow/ck_1024.pt}
DECK=${ORACLE_DECK:-B1Narrow}
EPS=${ORACLE_EPS:-256}

pkill -f "[R]LDriverServer" 2>/dev/null
sleep 3
echo "=== ARM 3: fresh critic, no oracle === $(date -u +%H:%M:%S)"
# --oracle on the SERVER (so the fresh critic supplies GAE) but the
# driver flag OFF (so it has nothing privileged to read)
EV_ORACLE=0 EV_OUT=/tmp/rl_ev_ck_1024_${DECK}_or2 \
    SRV_FORCE_ORACLE=1 timeout 7200 bash $RL/ev_probe.sh \
    "$CKPT" "$DECK" "$EPS" 7994
echo "=== ARM 3 exit=$? === $(date -u +%H:%M:%S)"
echo "ARM3_DONE"
