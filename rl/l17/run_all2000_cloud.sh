#!/bin/bash
# The full 2,000-game runs. Only the readings that looked promising on the 200-game
# sample are worth the wall time: `resync` (whose per-turn fidelity is a new
# measurement, not a re-score of the go/no-go), plus `base` and `choice` as the two
# turns-matched rows to compare it against.
set -u
REPO=$(cd "$(dirname "$0")/../.." && pwd)
export JAVA_TOOL_OPTIONS=""
bash "$REPO/rl/l17/run_l17_cloud.sh" all2000_cloud --all
L17_VARIANT=choice bash "$REPO/rl/l17/run_l17_cloud.sh" all2000_choice_cloud --all
L17_VARIANT=resync bash "$REPO/rl/l17/run_l17_cloud.sh" all2000_resync_cloud --all
python3 "$REPO/rl/l17/perturn.py" /home/user/l17run/spec_all2000_resync_cloud.tsv \
        /home/user/l17run/out_all2000_resync_cloud.tsv --tag all2000_resync_cloud \
        > /home/user/l17run/perturn_all2000_resync_cloud.txt
python3 "$REPO/rl/l17/cascade.py" /home/user/l17run/spec_all2000_cloud.tsv \
        /home/user/l17run/out_all2000_cloud.tsv --tag all2000_cloud \
        > /home/user/l17run/cascade_all2000_cloud.txt
echo ALL2000_DONE
