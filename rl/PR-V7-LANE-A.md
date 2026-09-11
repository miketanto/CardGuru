# PR text for v7/lane-a -> main (gh is not installed here; open at https://github.com/miketanto/CardGuru/pull/new/v7/lane-a and paste)

## v7 Lane A — Phases 0b, 0c, 1, 2: card index, decklist corpus, card embedder, deck context

All gates are numbers in `rl/V7-VALIDATION.md`; every version that failed is recorded there, not deleted.

### Delivered
- **0b** `rl/artifacts/cards_v1` — 34,642 card faces + 836 tokens from Forge pin 670429bf (+123 post-pin scripts), 0 unknown names over the 38 ladder decks. `rl/cards/build_index.py`.
- **0c GO** `rl/artifacts/decklists_v1` — 12,612 unique, fully resolved constructed lists from 1,008 MTGO events (Jul–Sep 2026). `rl/decklists/{fetch_mtgo,build_corpus}.py`.
- **1a** `rl/cardemb/data.py` + tests: text / printed / graph channels; printed round-trip on all 35,478 faces; 10 % held-out split.
- **1b/1d** `rl/artifacts/card_emb_v8` — the shared card embedder (frozen contract in its README). Block-structured 128-d vector (text 48 | tree 32 | bag 16 | printed 32), 2-seed Procrustes-averaged artifact. Gates: G1 32/33 probes, G2 all (Snare/Spike rank 28, swap pairs 16/16), G3 seed overlap 0.680. **One stated deviation** (rare answer-class probe F1 0.725 vs 0.80), accepted 2026-09-11.
- **2a/2b/2c** `rl/artifacts/deck_ctx_v1` — deck-context transformer (permutation-invariant to 1e-6), masked-card pretraining (held-out top-1 0.41 vs frequency 0.02), role probe (wincon 0.98 / answer 0.96 / enabler 0.81). Rerun on v8 in progress; rows follow.
- `rl/CARDEMB-RESEARCH.md` — the literature review that produced the accepted recipe (seed instability, fine-tuning stability, structure+text encoders, prior card work).

### What changed on `main`
Nothing that runs: all new code is under `rl/cardemb`, `rl/deckctx`, `rl/cards`, `rl/decklists`; no engine or server path is touched. `entattn_check.py` is unaffected.

### Pre-registered
The embedder cannot move any RL number; nothing consumes it before Phase 4.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
