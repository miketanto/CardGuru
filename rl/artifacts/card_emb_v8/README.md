# card_emb_v8 — the shared card embedder (v7 L0), accepted 2026-09-11

*Contract for consumers (Lane C token builder, Lane A deck context, the
belief module). A change to this file is a commit that names them.
Versions v1–v7 failed the gates and are recorded in `rl/V7-VALIDATION.md`
§1d; v8 is accepted with one stated deviation (below).*

## Files

| file | what | shape |
|---|---|---|
| `emb.pt` | `e_card` for every face id of `cards_v1` — **the** embedding: per-slice orthogonal-Procrustes mean of two training seeds (`rl/cardemb/average.py`) | FloatTensor `[35478, 128]` |
| `emb_seed1.pt` | the same recipe on two other seeds — determinism gate only, never consumed | `[35478, 128]` |
| `index.json` | version, `cards_version`, pin, block layout, training args, seed-0 retrieval metrics | |
| `split.json` | the 10 % held-out card ids (by script), fixed before training | |
| `gates.json` | the 1d acceptance readout (`rl/cardemb/gates.py`) | |
| `train_seed{0..3}.log` | one line per epoch, four seeds | |
| weights | **not committed** (92 MB per seed); rebuilt by `rl/cardemb/sweep.sh a` (~2 h for four seeds on the RTX 3060) | |

Row `i` of `emb.pt` is `cards_v1` face id `i`; resolve names through
`rl/artifacts/cards_v1/index.json` (`names`: normalised name → id,
`token:<script>` for tokens, `A // B` → front face).

## The vector is block-structured — consumers may rely on this

`e_card[0:48]` text slice · `[48:80]` ability-tree slice · `[80:96]`
readout-bag slice · `[96:128]` printed-fields slice. Each slice is
standardised (zero mean, unit variance across its own dimensions), so a
cosine on the whole vector is the width-weighted mean of the per-slice
cosines (37.5 % text, 25 % tree, 12.5 % bag, 25 % printed). A linear
probe on the vector recovers mana value, P/T, colours and types at
0.99–1.00 (gate G1); the tree slice was trained to reconstruct the
68-column readout (`rl/e2_extract.py` order) and the bag slice too.

## How a consumer uses it

- **Frozen.** Load `emb.pt`, never fine-tune it inside a run (design
  decision 1). The one trainable piece is a `Linear(128, 128)` adapter
  owned by the consumer; every checkpoint records `card_emb_v8`.
- **Unknown card** (name not in `cards_v1`): zero row plus the unknown
  flag, exactly as the v6 engine does with `e2_features`.
- **Tokens** are rows too (836 tokenscripts), keyed `token:<script>`.
- The 68-column readout and the 83 printed fields are still emitted
  separately by the engine; the embedding does not replace them.

## What it is

Three channels (`rl/cardemb/data.py`, `rl/cardemb/tree.py`): oracle
text (type line + oracle, reminder text stripped, self-name → CARDNAME,
numbers bucketed, mana symbols as tokens) through a fine-tuned
MiniLM-L6; the Forge ability tree (nodes: kind / api / mode / keyword +
hashed (param key, value piece) pairs; typed edges as attention bias; 2
layers, param-piece dropout 0.2) plus the 68-column readout bag; 83
explicit printed fields. Objective (`rl/cardemb/train_contrastive.py`):
symmetric InfoNCE between the text view and the structure view with
same-card positives and structurally identical cards masked from the
denominator; relational distillation (weight 10) of the text view and
of the text and tree slices to the frozen pretrained geometry;
reconstruction losses (weight 1) from the tree and bag slices to the
readout and from the printed slice to the printed fields. Stability
recipe from the literature (`rl/CARDEMB-RESEARCH.md` §2b): text LR
2e-5 with layer-wise decay 0.85, 10 % warmup, 40 epochs, batch 256;
artifact = mean of two seeds after per-slice Procrustes alignment
(§2a). Trained on the 90 % split, gated on the held-out 10 %.

## Gates (`rl/V7-VALIDATION.md` §1d "sweep config (a)")

| gate | measured |
|---|---|
| G1 mv / power / toughness probe acc (held-out) | 0.993 / 0.997 / 0.994 |
| G1 colours, types, keywords (f1), answer classes (f1) | 1.000, 1.000, min 0.817, **min 0.725 (ans_minus_toughness, 33 positives; threshold 0.80)** |
| G2 Cancel / Counterspell cos | 0.983 |
| G2 Spell Snare / Force Spike | rank 28 of 35,478 |
| G2 functional reprints in top-3 | 10 / 10 |
| G2 P8 swap pairs within top-500 / median directed rank | 16 / 16, 29 |
| G3 artifact vs independent artifact, top-10 Jaccard | 0.680 (single seeds 0.623) |

**Stated deviation.** One of 33 G1 probes is below its pre-registered
threshold (a rare mechanical bit, F1 interval ≈ ±0.15 at 33 positives;
the same bit is emitted exactly in the readout the policy also
receives). Accepted by the user on 2026-09-11 on those grounds; sweep
configs c/d (positive-weighted BCE readout reconstruction) continue in
the background and, if one passes every gate, become v9 as a drop-in.

## Pre-registered: what this artifact cannot do

Move any RL number. Nothing consumes it before Phase 4.
