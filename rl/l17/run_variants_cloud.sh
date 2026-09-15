#!/bin/bash
# Run every cloud variant on the same 200 seeded games (rl/L17-FIDELITY-CLOUD.md §2),
# one after another. The base run (tag s200_cloud) and the guided run (s200g_cloud)
# are the two comparison rows; resync is a different measurement (rl/l17/perturn.py).
#
#   bash rl/l17/run_variants_cloud.sh [SELECTOR...]        # default: --sample 200 --seed 17
set -u
REPO=$(cd "$(dirname "$0")/../.." && pwd)
SEL=${*:---sample 200 --seed 17}
export JAVA_TOOL_OPTIONS=""

L17_GUIDE=1 bash "$REPO/rl/l17/run_l17_cloud.sh" s200g_cloud $SEL
for v in abil choice oppo order all resync; do
  L17_VARIANT=$v bash "$REPO/rl/l17/run_l17_cloud.sh" "s200_${v}_cloud" $SEL
done
python3 "$REPO/rl/l17/perturn.py" /home/user/l17run/spec_s200_resync_cloud.tsv \
        /home/user/l17run/out_s200_resync_cloud.tsv --tag s200_resync_cloud \
        > /home/user/l17run/perturn_s200_resync_cloud.txt
echo VARIANTS_DONE
