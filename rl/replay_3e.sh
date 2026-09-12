#!/bin/bash
# Gate 3e: replay determinism of the v7 wire. The same 20 seeded eval games are
# played twice on the v7 driver (7911) against the echo policy (first non-pass
# candidate); both the driver-side dump (-Drl.wireDump, written by
# SocketPolicyClient before each round trip) and the echo server's recording
# are kept, so two things are checked: dump == recording (the dump is the
# wire), and run A vs run B (determinism, modulo the engine's own tapped-land
# noise measured in 3a).
#   bash rl/replay_3e.sh [episodes]
[ -f ~/.profile ] && . ~/.profile
LB=/mnt/c/Users/sutanto4/Documents/CardGuru-lane-b
OUT=$LB/rl/artifacts/v7/wire3a
EP=${1:-20}
for run in A B; do
    rm -f $OUT/replay_$run.dump.jsonl
    DECK=W0Base PICK=1 EXTRA="-Drl.wireDump=$OUT/replay_$run.dump.jsonl" \
        bash $LB/rl/wire_record.sh replay_$run 7784 7 7911 $EP 900100 | head -1
done
cd $LB
echo "== dump vs recording (run A)"
python3 rl/wire_diff.py rl/artifacts/v7/wire3a/replay_A.dump.jsonl rl/artifacts/v7/wire3a/replay_A.jsonl --all | tail -3
echo "== run A vs run B"
python3 rl/wire_diff.py rl/artifacts/v7/wire3a/replay_A.jsonl rl/artifacts/v7/wire3a/replay_B.jsonl --all
