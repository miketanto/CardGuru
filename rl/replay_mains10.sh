#!/bin/bash
# Phase 10 replays: one game vs the heuristic and one vs CP7 for each league main's latest
# snapshot, on its own deck (rl/replay_ck.sh). Waits until the league controller and any lane
# have exited (the 11 GB box holds two servers), then runs the three mains one at a time.
[ -f ~/.profile ] && . ~/.profile
cd /home/user/CardGuru || exit 1
P=/home/user/CardGuru/rl/artifacts/v7/10/pool; OUT=/home/user/CardGuru/rl/artifacts/v7/10/replay
echo "RPL10|wait|$(date -u +%FT%TZ)"
while pgrep -f 'league1[0]\.py' > /dev/null || pgrep -f 'rung0_lan[e]' > /dev/null; do sleep 20; done
echo "RPL10|start|$(date -u +%FT%TZ)"
for spec in "M_W:W0Base" "M_D:BenchDimir" "M_L:G1Landfall"; do
    m=${spec%%:*}; deck=${spec#*:}
    ck=$(ls $P/${m}_[0-9]*.pt 2>/dev/null | sort | tail -n 1)
    [ -s "$ck" ] || { echo "RPL10|$m|no snapshot"; continue; }
    echo "RPL10|$m|ckpt=$(basename $ck)|deck=$deck"
    bash rl/replay_ck.sh "$ck" $OUT "${m}_$(basename $ck .pt)" $deck 2>&1 | grep '^REPLAY' | sed "s/^/RPL10|$m|/"
done
echo "RPL10|done|$(date -u +%FT%TZ)"
