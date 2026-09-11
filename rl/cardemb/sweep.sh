#!/usr/bin/env bash
# Overnight sweep for the card embedder (CARDEMB-RESEARCH.md §3).
# Each run: 4 seeds -> two independent 2-seed Procrustes-averaged artifacts
# (seeds 0+1 -> emb.pt, seeds 2+3 -> emb_seed1.pt) -> gates.py (G1/G2 on the
# artifact, G3 between the two artifacts) -> slice_jaccard -> RESULTS.md.
# Nothing here accepts a version; acceptance is a row a person writes in
# rl/V7-VALIDATION.md.
#
# Usage (WSL): bash rl/cardemb/sweep.sh            # runs every config below
#              bash rl/cardemb/sweep.sh a           # one config by name
set -u
cd /home/user/CardGuru || exit 1
export CARDGURU_TOKENSCRIPTS=/home/user/forge-src/forge-gui/res/tokenscripts
ROOT=rl/artifacts/cardemb_sweep
mkdir -p "$ROOT"
RES="$ROOT/RESULTS.md"
RECIPE="--fuse blocks --aux 1.0 --distill 10 --lr-text 2e-5 --llrd 0.85 --warmup 0.10 --epochs 40 --batch 256"

declare -A CFG
# (a) v6 structure (hashed-tree GNN) + stability recipe + seed averaging: isolates §2a/§2b
CFG[a]="--struct tree --tree --piece-dropout 0.2 $RECIPE"
# (b) v8 structure (serialised script through the shared encoder) + recipe + averaging: §2c
CFG[b]="--struct script $RECIPE"

run_one() {
  local name=$1; local flags=$2; local out="$ROOT/$name"
  mkdir -p "$out"; cp -n rl/artifacts/card_emb_v1/split.json "$out/split.json"
  echo "$(date +%H:%M:%S) START $name :: $flags" | tee -a "$RES"
  for SEED in 0 1 2 3; do
    if [ ! -f "$out/emb_raw_seed$SEED.pt" ]; then
      python3 rl/cardemb/train_contrastive.py --seed $SEED --out "$out" $flags > "$out/train_seed$SEED.stdout" 2>&1
      echo "$(date +%H:%M:%S) $name seed $SEED exit $?" | tee -a "$RES"
      # train_contrastive names seed 0's export emb.pt and others emb_seedN.pt; keep raw copies
      if [ $SEED -eq 0 ]; then mv -f "$out/emb.pt" "$out/emb_raw_seed0.pt"; mv -f "$out/index.json" "$out/index_raw_seed0.json" 2>/dev/null
      else mv -f "$out/emb_seed$SEED.pt" "$out/emb_raw_seed$SEED.pt"; fi
      rm -f "$out/ckpt_seed$SEED.pt" "$out/model_seed$SEED.pt" "$out/model.pt"
    fi
  done
  python3 rl/cardemb/average.py "$out/emb.pt" "$out/emb_raw_seed0.pt" "$out/emb_raw_seed1.pt" | tee -a "$RES"
  python3 rl/cardemb/average.py "$out/emb_seed1.pt" "$out/emb_raw_seed2.pt" "$out/emb_raw_seed3.pt" | tee -a "$RES"
  {
    echo; echo "## $name  ($(date '+%Y-%m-%d %H:%M'))"; echo; echo "flags: \`$flags\`"; echo
    echo "### gates (artifact = mean of seeds 0+1; G3 vs mean of seeds 2+3)"; echo
    CUDA_VISIBLE_DEVICES="" python3 rl/cardemb/gates.py --art "$out" 2>&1 | grep '^|'
    echo; echo "### per-slice seed overlap (artifact vs artifact)"; echo '```'
    CUDA_VISIBLE_DEVICES="" python3 rl/cardemb/slice_jaccard.py "$out" 2>&1 | grep -v Warning
    echo '```'; echo "### raw single seeds 0 vs 1 (for reference)"; echo '```'
    mkdir -p "$out/raw01"; cp "$out/emb_raw_seed0.pt" "$out/raw01/emb.pt"; cp "$out/emb_raw_seed1.pt" "$out/raw01/emb_seed1.pt"
    CUDA_VISIBLE_DEVICES="" python3 rl/cardemb/slice_jaccard.py "$out/raw01" 2>&1 | grep -v Warning | head -1
    echo '```'
    grep 'epoch=40' "$out"/train_seed*.log 2>/dev/null | cut -c1-200 | sed 's/^/    /'
  } >> "$RES"
  echo "$(date +%H:%M:%S) DONE $name" | tee -a "$RES"
}

if [ $# -gt 0 ]; then
  for n in "$@"; do run_one "$n" "${CFG[$n]}"; done
else
  for n in a b; do run_one "$n" "${CFG[$n]}"; done
fi
echo "$(date +%H:%M:%S) SWEEP COMPLETE" | tee -a "$RES"
