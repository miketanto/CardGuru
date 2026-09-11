# card_emb_v6 — the shared card embedder (v7 L0)

*Contract for consumers (Lane C token builder, Lane A deck context, the
belief module). A change to this file is a commit that names them.
Versions v1–v5 failed the gates and are recorded in `rl/V7-VALIDATION.md`
§1d; this is the first accepted version.*

## Files

| file | what | shape |
|---|---|---|
| `emb.pt` | `e_card` for every face id of `cards_v1`, seed 0 (**the** embedding) | FloatTensor `[35478, 128]` |
| `emb_seed1.pt` | same, seed 1 — determinism gate only, never consumed | `[35478, 128]` |
| `index.json` | version, `cards_version`, pin, n, d_c, args, final retrieval metrics | |
| `split.json` | the 10 % held-out card ids (by script), fixed before training | |
| `gates.json` | the 1d acceptance readout (`rl/cardemb/gates.py`) | |
| `diag_views.json` | per-view diagnostic (`rl/cardemb/diag_views.py`) | |
| `train_seed*.log` | one line per epoch | |
| `model.pt`, `ckpt_seed*.pt`, `text_anchor.pt` | weights — **not committed** (92 MB each); rebuilt by `train_contrastive.py` in ~20 min on the RTX 3060 | |

Row `i` of `emb.pt` is `cards_v1` face id `i`; resolve names through
`rl/artifacts/cards_v1/index.json` (`names`: normalised name → id,
`token:<script>` for tokens, `A // B` → front face).

## The vector is block-structured — consumers may rely on this

`e_card[0:48]` text slice · `[48:80]` ability-tree slice · `[80:96]`
readout-bag slice · `[96:128]` printed-fields slice. Each slice is its
own linear projection followed by its own LayerNorm, so a cosine on the
whole vector is the width-weighted mean of the per-slice cosines
(37.5 % text, 25 % tree, 12.5 % bag, 25 % printed). A linear probe on
the printed slice recovers mana value, P/T, colours and types at
0.99–1.00 (gate G1); the tree slice was trained to reconstruct the
68-column readout (`rl/e2_extract.py` order), so mechanical families
are linearly readable there too.

## How a consumer uses it

- **Frozen.** Load `emb.pt`, never fine-tune it inside a run (design
  decision 1). The one trainable piece is a `Linear(128, 128)` adapter
  owned by the consumer; every checkpoint records `card_emb_v6`.
- **Unknown card** (name not in `cards_v1`): zero row plus the unknown
  flag, exactly as v6 (the engine) does with `e2_features`; the embedder
  can encode new text at runtime (`CardEmbedder.embed`) but that is not
  part of the v7 wire contract.
- **Tokens** are rows too (836 tokenscripts), keyed `token:<script>`.

## What it is

Three channels (`rl/cardemb/data.py`, `rl/cardemb/tree.py`): oracle text
(type line + oracle, reminder text stripped, self-name → CARDNAME,
numbers bucketed `[N0]..[N8] [N9_10] [N11_15] [N16_20] [N21P]`, mana
symbols `[M2] [MU] [TAP]`, loyalty `[LOYP1]`) through a fine-tuned
MiniLM-L6; the Forge ability tree (nodes: kind / api / mode / keyword +
hashed (param key, value piece) pairs; typed edges as attention bias;
2 layers) plus the 68-column readout bag; 83 explicit printed fields.
Objective (`rl/cardemb/train_contrastive.py`): symmetric InfoNCE between
the text view and the structure view with same-card positives and
structurally identical cards masked from the denominator, relational
distillation (weight 10) of the text view to the frozen pretrained
geometry, and reconstruction losses (weight 1) from the tree slice to
the readout and from the printed slice to the printed fields; tree
param-piece dropout 0.2. 30 epochs, batch 256, ~20 min per seed on the
RTX 3060; trained on the 90 % split, gated on the held-out 10 %.

## Gates (seed 0; G3 in `rl/V7-VALIDATION.md` §1d v6)

| gate | measured |
|---|---|
| G1 mv / power / toughness probe acc (held-out) | 0.993 / 0.995 / 0.995 |
| G1 colours, types, keywords (f1), answer classes (f1) | ≥ 1.000, 1.000, 0.955, 0.902 |
| G2 Cancel / Counterspell cos | 0.984 |
| G2 Spell Snare / Force Spike | rank 19 of 35,478 (cos 0.920) |
| G2 functional reprints in top-3 | 10 / 10 |
| G2 P8 swap pairs within top-500 / median directed rank | 14 / 16, 26 |
| G3 seed 0 vs seed 1 top-10 Jaccard | see V7-VALIDATION.md |

Known limits: two swap pairs sit outside the top-500 (Spyglass Siren /
Faerie Seer; Requiting Hex / Cut Down); the text view alone is the
weakest channel; the tree tokenizer hashes param pieces (no fitted
vocabulary), so unseen params collide harmlessly but are not
interpretable.

## Pre-registered: what this artifact cannot do

Move any RL number. Nothing consumes it before Phase 4.
