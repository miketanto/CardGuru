# card_emb_v1 — FAILED version (gate 1d, see rl/V7-VALIDATION.md); the accepted embedder is `rl/artifacts/card_emb_v6/`

*Kept for the record only. Nothing may consume this directory.*

# (original contract text follows, superseded)

*Contract for consumers (Lane C token builder, Lane A deck context, the
belief module). A change to this file is a commit that names them.*

## Files

| file | what | shape |
|---|---|---|
| `emb.pt` | `e_card` for every face id of `cards_v1`, seed 0 (**the** embedding) | FloatTensor `[35478, 128]` |
| `emb_seed1.pt` | same, seed 1 — determinism gate only, never consumed | `[35478, 128]` |
| `model.pt` | state_dict + config + args of the seed-0 embedder (`rl/cardemb/model.py`) | |
| `index.json` | version, `cards_version`, pin, n, d_c, args, final retrieval metrics | |
| `split.json` | the 10 % held-out card ids (by script), fixed before training | |
| `gates.json` | the 1d acceptance readout (`rl/cardemb/gates.py`) | |
| `train_seed*.log` | one line per epoch | |

Row `i` of `emb.pt` is `cards_v1` face id `i`; resolve names through
`rl/artifacts/cards_v1/index.json` (`names`: normalised name → id,
`token:<script>` for tokens, `A // B` → front face).

## How a consumer uses it

- **Frozen.** Load `emb.pt`, never fine-tune it inside a run (design
  decision 1). The one trainable piece is a `Linear(128, 128)` adapter
  owned by the consumer; every checkpoint records `card_emb_v1`.
- **Unknown card** (name not in `cards_v1`): the embedder can encode it
  from text at runtime (`CardEmbedder.embed`), but the wire contract for
  v7 is that the server resolves ids; an unresolved id gets the zero
  row plus the unknown flag, exactly as v6 does with `e2_features`.
- **Tokens** are rows too (836 tokenscripts), keyed `token:<script>`.

## What it is

Three channels (`rl/cardemb/data.py`): oracle text (type line + oracle,
self-name → CARDNAME, numbers bucketed `[N0]..[N8] [N9_10] [N11_15]
[N16_20] [N21P]`, mana symbols `[M2] [MU] [TAP]`, loyalty `[LOYP1]`) through
a fine-tuned MiniLM-L6; the 68-column ability-graph readout
(`rl/e2_extract.py`) through an MLP; 83 explicit printed fields.
Concatenated, projected to 128, LayerNorm. Trained by supervised InfoNCE
between the text view and the structure view on the 90 % train split
(`rl/cardemb/train_contrastive.py`), 30 epochs, ~17 min on the RTX 3060.

## Gates

See `gates.json` and the 1d row in `rl/V7-VALIDATION.md`. Pre-registered
thresholds are in the header of `rl/cardemb/gates.py`.

## Pre-registered: what this artifact cannot do

Move any RL number. Nothing consumes it before Phase 4.
