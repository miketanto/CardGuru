#!/bin/bash
# ONE game, every consult traced. rl.trace logs a line per decision the
# policy was asked to make - including the k>0 windows where it passed,
# which rl.debug never showed because nothing happened in them.
set -u
RL=/home/user/CardGuru/rl
pkill -f "[R]LDriverServer" 2>/dev/null
pkill -f "policy_serve[r].py --port 7994" 2>/dev/null
sleep 2
RL_TORCH_THREADS=1 setsid nohup python3 $RL/policy_server.py --port 7994 \
    --ckpt /tmp/rl_dimir_v6/ck_1024.pt --seed 0 --cdim 94 --arch entattn \
    --gdim 16 --edim 48 --emax 96 --max-k 96 --threads 1 \
    > /tmp/dimir_trace_srv.log 2>&1 &
for i in $(seq 1 45); do
    grep -q "policy server" /tmp/dimir_trace_srv.log 2>/dev/null && break; sleep 2
done
DRVLOG=/tmp/rl_p9/driver_server_7910.log
: > $DRVLOG 2>/dev/null || true
cd /home/user/mage
RL_PERSIST=1 RL_AUTOSTART=1 timeout 900 bash $RL/run_driver.sh \
    -Drl.episodes=1 -Drl.agent=rl -Drl.policy=socket -Drl.port=7994 \
    -Drl.opponent=heuristic -Drl.searchPlies=1 -Drl.searchBreadth=8 \
    -Drl.cardFeatures=$RL/e2_features.tsv -Drl.noYields=true \
    -Drl.consultBudget=4000 -Drl.encoderV=6 -Drl.blockAudit=true \
    -Drl.debug=true -Drl.trace=true \
    -Drl.deck=BenchDimir.dck -Drl.oppDeck=BenchDimir.dck \
    -Drl.stopTurn=60 -Drl.mode=eval -Drl.seed=980005 -Drl.report=0 \
    -Drl.out=/tmp/dimir_trace_sum.txt > /tmp/dimir_trace_drv.log 2>&1
sed -n '/^RLGAME|/,/^RLGAME_END/p' $DRVLOG > /tmp/dimir_trace.txt
echo "trace lines: $(wc -l < /tmp/dimir_trace.txt)  consults: $(grep -c '\[trace\]' /tmp/dimir_trace.txt)"
grep -o "agent_consults_per_ep=[0-9.]*\|win_rate=[0-9.]*" /tmp/dimir_trace_sum.txt | tr '\n' ' '
pkill -f "policy_serve[r].py --port 7994" 2>/dev/null
echo; echo TRACE_DONE
