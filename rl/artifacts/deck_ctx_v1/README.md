# deck_ctx_v1 — deck context L1, pretrained on decklists_v1

*Contract for consumers (Lane C token builder: per-game `c'_i` and `D`;
the belief module reads the same posterior). A change to this file is a
commit that names them.*

## Files

| file | what |
|---|---|
| `model_seed0.pt` | `{"model": DeckContext state_dict, "head": MaskedHead state_dict, "mask_row", "vocab", "config", "args"}` (3.4 MB, committed) |
| `index_seed0.json` | args, corpus sizes, vocabulary size, final train / held-out metrics |
| `probe_roles_model_seed0.json`, `probe_roles_identity.json` | the 2c readout, trained and identity-init |
| `train_masked_seed0.log` | one line per epoch |
| `decks_cache.pt` | per-deck (ids, counts, fingerprint bias) tensors for the corpus — gitignored, rebuilt by `train_masked.py` |

## What it computes

`rl/deckctx/model.py::DeckContext` (config in the checkpoint: d_c 128,
d 128, 4 heads, FFN 256, 2 layers). Inputs per deck: `E` = `card_emb_v6`
rows of the distinct cards, `counts` = copies, `bias` = enabler→payoff
weights from `cardguru.fingerprint.build_fingerprint` (built by
`rl/deckctx/data.py::deck_tensors`), `mask`. Outputs `c'_i` (per card,
residual on `e_card`, so an untrained module is the identity) and `D`
(pooled). Permutation-equivariant / invariant to 1e-6 (gate 2a).

Run it once per game per side (design L1): my deck, and the opponent's
open decklist in v1. The `MaskedHead` in the checkpoint is training
scaffolding, not part of the game-time contract.

## Gates (rl/V7-VALIDATION.md §1c/2b, §2c)

| gate | measured |
|---|---|
| masked-card held-out top-1 / top-10 (vocab 3,519) | 0.407 / 0.727 vs frequency baseline 0.020 / 0.129 |
| role probe on c'ᵢ, held-out decks: wincon / answer / enabler | 0.982 / 0.960 / 0.814 (e_card reference 0.996 / 0.987 / 0.720) |

## Dependencies, pinned

`card_emb_v6/emb.pt` (frozen), `decklists_v1/decklists.jsonl.gz` (commit
f403ddb), `cards_v1` (Forge pin 670429bf + 123-script overlay).

## Pre-registered: what this artifact cannot do

Move any RL number; nothing consumes it before Phase 4. Its masked-card
number says nothing about the XMage ladder decks (36 of 12,612 lists).
