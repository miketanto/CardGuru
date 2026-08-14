#!/bin/bash
# Rung 0, all seeds, one branch. Sequential on purpose.
#
#   bash rl/rung0_sweep.sh W0Base W0Twin 4096 5      # white / combat
#   bash rl/rung0_sweep.sh B0Base B0Twin 4096 5      # black / threat
#
# Seeds run one at a time rather than in parallel because the box has 4
# cores and each lane already runs the engine at conc4; two lanes would
# oversubscribe exactly the way POOLED-ANALYSIS.md section 3 documents.
#
# Five seeds is not decoration. Every claim in this project that compared
# two separately-trained nets at 1-2 seeds turned out provisional - E3
# beat E2 by +.175 on seed 0 and +.020 on seed 1, and its faeries result
# reversed outright. Between-run variance is the dominant noise source
# here, and rung 0 is the first setting cheap enough to pay for the
# convention the project has asserted since Phase 3 and never once met.
#
# Pooling the per-seed CP7 rows is the other reason: 5 x 50 games gives
# +-.06 on the one externally uncontaminated number this project has,
# against the +-.13 of the single 50-game rows in PHASE12-XMAGE-AI.md.
set -u
BASE=${1:?usage: rung0_sweep.sh <BASE> <TWIN> [budget] [seeds]}
TWIN=${2:?}
BUDGET=${3:-4096}
SEEDS=${4:-5}
RL=/home/user/CardGuru/rl
LOG=${R0_SWEEP_LOG:-/tmp/rl_rung0_${BASE}_sweep.log}

echo "R0_SWEEP_START|$BASE|budget=$BUDGET|seeds=$SEEDS" | tee -a $LOG
for s in $(seq 0 $((SEEDS - 1))); do
    bash $RL/rung0_lane.sh "$BASE" "$TWIN" "$BUDGET" "$s" 2>&1 | tee -a $LOG
done
echo "R0_SWEEP_DONE|$BASE" | tee -a $LOG
