#!/bin/bash
# Phase 8 zero-shot matrix: {attn_desp, attn_bc, e0_champ} x
# {BenchDimir + 3 swap variants} x {D0, D1}, 200g each, argmax.
# Resumable: pairings already in /tmp/rl_p8/eval_log.txt are skipped, so
# the script can be relaunched after any interruption.
# Usage: bash rl/p8_matrix.sh [games=200] [port=9020]
set -u
G=${1:-200}
PORT=${2:-9020}
OUT=/tmp/rl_p8
mkdir -p $OUT
touch $OUT/eval_log.txt

POLICIES=(
  "attn_desp|attn|/tmp/rl_c6_attn_s7/attn_desp_final.pt"
  "attn_bc|attn|/tmp/rl_p5_c1/student_e2attn.pt"
  "e0_champ|e0|/tmp/rl_league_bc_s0/e0_league_final.pt"
)
# deck|seed  (one fixed eval seed per deck, shared by every policy/ruler)
DECKS=(
  "BenchDimir|970000"
  "P8SwapInteraction|971000"
  "P8SwapThreats|972000"
  "P8SwapMixed|973000"
)

for P in "${POLICIES[@]}"; do
  IFS='|' read -r PN PA PC <<< "$P"
  for D in "${DECKS[@]}"; do
    IFS='|' read -r DN DS <<< "$D"
    for OPP in heuristic search; do
      grep -q "P8EVAL|policy=$PN|opp=$OPP|deck=$DN|" $OUT/eval_log.txt \
        && { echo "skip $PN $OPP $DN"; continue; }
      bash /home/user/CardGuru/rl/p8_eval.sh "$PN" "$PA" "$PC" "$OPP" \
        "$DN.dck" "$G" "$DS" "$PORT" || echo "P8MATRIX_FAILED|$PN|$OPP|$DN"
    done
  done
done
echo P8MATRIX_DONE
