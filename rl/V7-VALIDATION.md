# v7 validation — gate readouts

*Every phase gate in `V7-IMPLEMENTATION-PLAN.md` §2 appends its numbers
here. A gate is a number in this file, never a sentence in chat. Append
only; corrections are marked as corrections.*

## 0b — card index `rl/artifacts/cards_v1` (Lane A, 2026-09-10)

Source: Forge pin `670429bf` (2026-08-06) → `data/dataset.jsonl.gz`
(34,519 faces, 7 s) → `rl/cards/build_index.py` (5 s).

| gate | required | measured | result |
|---|---|---|---|
| card faces indexed | ≥ 33,000 | 34,642 (34,519 pin + 123 post-pin overlay; first build the same day read 34,521 with a 2-script overlay) | pass |
| token scripts indexed | resolved via tokenscripts | 836 | pass |
| unknown names across every `.dck` in `rl/` and list in `decks/` | 0 | 0 of 38 decks (1,540 lines) | pass |
| card names shared by >1 card script | (report) | 0 | — |
| faces with a non-zero graph readout | (report) | 34,218 / 35,357 | — |

Caveats recorded in `rl/artifacts/cards_v1/README.md`: 123 cards postdate
the pin (two of them, `Defense Force Aggressor` and `Head of Security`,
are in XMage ladder decks; the rest let 2026 MTGO lists resolve) and come
from Forge `639f8d98` via `rl/cards/extra_scripts/` (its README lists them); token names
are not unique across tokenscripts (bare name → first script,
`token:<script>` is exact); transform back faces carry `mv = null`.

## 1a — embedder data layer `rl/cardemb/data.py` (Lane A, 2026-09-10)

| gate | required | measured | result |
|---|---|---|---|
| ladder cards round-trip the printed channel (`printed_decode(printed_encode(f)) == printed_expected(f)`) | every card in the 38 decks | 491 / 491 distinct deck lines; also 35,478 / 35,478 faces | pass |
| held-out split written to disk | 10 % by name (script-grouped for multi-face) | `rl/artifacts/card_emb_v1/split.json`: 3,532 / 35,478 = 10.0 %, faces of one script never straddle | pass |
| text channel carries no raw number and no self-name | all faces checked (first 5,000 in the unit test) | 0 violations | pass |

Channel dims: text = string (type line + bucketed oracle), printed = 83
floats (`PRINTED_DIM`), graph = 68 floats (`rl/e2_extract.py`).
Test: `python -m pytest tests/test_cardemb_data.py` (5 passed, 5 s).

## 2a — deck context `rl/deckctx/model.py` (Lane A, 2026-09-10)

| gate | required | measured | result |
|---|---|---|---|
| permutation equivariance of c'ᵢ and invariance of D | ≤ 1e-6 | max abs diff 0 to 1e-12 (float64, `tests/test_deckctx.py`) | pass |
| copy-count sensitivity | > 0 | changing one card's copies moves its c'ᵢ and D; the other deck in the batch unchanged | pass |
| relation bias used | outputs change when the enabler→payoff bias is zeroed | > 0 | pass |
| identity init (2b fallback) | c'ᵢ == e_card exactly | max abs diff 0 | pass |

Untrained module; no number here is a result about decks. 2b/2c follow the 0c go/no-go.

## 1d — card embedder `card_emb_v1` — **FAIL** (Lane A, 2026-09-10 17:35)

Seed 0, 30 epochs, `rl/cardemb/train_contrastive.py` defaults (supervised
InfoNCE keyed on the structure vector). Final retrieval r@1 train 0.774 /
held-out 0.735, r@10 0.987 / 0.966 (4,096-card pools). Gates from
`rl/cardemb/gates.py` (pre-registered in commit 929e5b2):

| gate | threshold | measured (held-out) | train | result |
|---|---|---|---|---|
| G1 mv probe acc | ≥ 0.9 | 0.980 | 0.992 | pass |
| G1 power probe acc | ≥ 0.9 | 0.985 | 0.993 | pass |
| G1 toughness probe acc | ≥ 0.9 | 0.986 | 0.994 | pass |
| G1 colours (5 probes, acc) | each ≥ 0.97 | min 0.998 (color_W) | min 0.999 | pass |
| G1 types (6 probes, acc) | each ≥ 0.97 | min 1.000 (type_Sorcery) | min 1.000 | pass (3 skipped: too few positives) |
| G1 keywords (11 probes, f1) | each ≥ 0.8 | min 0.978 (kw_reach) | min 0.987 | pass (7 skipped: too few positives) |
| G1 answer classes (5 probes, f1) | each ≥ 0.8 | min 0.913 (ans_destroy_target) | min 0.949 | pass (4 skipped: too few positives) |
| G2 Cancel / Counterspell cos | ≥ 0.85 | 0.998 | | pass |
| G2 Spell Snare / Force Spike cos | ≤ 0.848, Spike ∉ Snare top-10 | 0.957, in top-10: True | | **FAIL** |
| G2 functional reprints in top-3 | all 10 | 10 / 10 | | pass |
| G2 P8 swap pairs cos | min ≥ μ+2σ = 0.502, mean ≥ μ+4σ = 0.874 | min 0.479, mean 0.790 (random μ 0.130 σ 0.186) | | **FAIL** |
| G3 seed 0 vs 1 top-10 Jaccard | ≥ 0.4, same G2 verdicts | 0.479, identical: True (added 18:03 when seed 1 finished) | | pass |
| **card_emb_v1 overall** | all of the above | | | **FAIL** |

Diagnosis (a property of the objective, not of training length): Spell
Snare and Force Spike have the same 68-column readout and the same
printed fields, so the supervised-contrastive loss keyed on the
structure vector made them *positives of each other*; the text encoder
is trained only to predict structure, so whatever text says beyond
structure is discarded. That is exactly the "condition breadth" PHASE-E3
found only a text channel can carry. The version is dead per the
pre-registration; nothing tunes the thresholds. Files kept for the
record: `rl/artifacts/card_emb_v1/{gates.json, index.json, train_seed0.log}`;
`emb.pt`/`model.pt` are not committed (failed version, 18 + 92 MB).

Next version (`card_emb_v2`, same gates, same thresholds): positives are
the same card only, cards with an identical structure vector are masked
out of the InfoNCE denominator (neither positive nor negative), and a
relational-distillation term anchors the fine-tuned text view's
similarity structure to the frozen pretrained encoder's, so text-only
distinctions survive the fine-tune.

## 0c — decklist corpus `rl/artifacts/decklists_v1` — **GO** (Lane A, 2026-09-10 17:56)

Source: mtgo.com published event decklists, month archives 2026-07 and
2026-09 (2026-08 was throttled to 0 events on the first pass; its rerun
is in progress and will be appended as a correction row, not folded in
silently). Fetch: 607 event pages, 571 fetched, 24 failed after 3
attempts, 12 pre-existing. Build: `rl/decklists/build_corpus.py`.

| gate | required | measured | result |
|---|---|---|---|
| unique constructed lists with every name resolved (strict gate) | ≥ 3,000 | **8,035** (845 held out by event) | **GO** |
| lists total / unique mainboards | (report) | 13,085 / 8,430 | — |
| mainboard slots unresolved against `cards_v1` | (report) | 757 / 512,439 = 0.15 % (31 names, all from a set newer than Forge `639f8d98`) | — |
| formats (unique lists) | (report) | modern 3,027 · pauper 1,336 · legacy 1,152 · standard 1,045 · pioneer 635 · premodern 587 · vintage 465 · duel-commander 108 (excluded from the gate: singleton) · ladder 37 | — |

Consequence (plan §2): masked-card-in-deck (1c) and deck-context
pretraining (2b) are **in**. What this corpus cannot support: any claim
about the XMage ladder decks' archetypes (37 of 8,035 lists), or about
formats the RL decks are not drawn from; it is a pretraining corpus for
L1, not an evaluation set.

## 1d — card embedder `card_emb_v2` — **FAIL** on the swap-pair bar (Lane A, 2026-09-10 18:10)

Seed 0, 30 epochs, `--positives same --distill 10` (commit 8aa280e). Final
retrieval r@1 train 0.776 / held-out 0.740. Same gates file, same thresholds:

| gate | threshold | measured (held-out) | train | result |
|---|---|---|---|---|
| G1 mv / power / toughness probe acc | ≥ 0.9 | 0.949 / 0.969 / 0.963 | 0.965 / 0.983 / 0.978 | pass |
| G1 colours (5), types (6), keywords (11), answer classes (5) | ≥ 0.97 acc / ≥ 0.8 f1 | min 0.995 / 0.999 / 0.966 / 0.925 | | pass |
| G2 Cancel / Counterspell cos | ≥ 0.85 | 0.999 (rank 1) | | pass |
| G2 Spell Snare / Force Spike | ≤ 0.849, Spike ∉ Snare top-10 | **0.839, rank 31** (v1: 0.957, rank ≤ 10) | | **pass** |
| G2 functional reprints in top-3 | all 10 | 10 / 10 | | pass |
| G2 P8 swap pairs cos | min ≥ μ+2σ = 0.618, mean ≥ μ+4σ = 0.867 | min 0.547, mean 0.757 (random μ 0.370 σ 0.124) | | **FAIL** |
| G3 seed 0 vs 1 top-10 Jaccard | ≥ 0.4, same G2 verdicts | 0.424, identical: True (added 18:33 when seed 1 finished) | | pass |
| (info) rank-based swap gate as pre-registered for v3+, applied to v2 for information only | ≥ 14/16 within 500, median ≤ 50 | 13/16, median 66 | | would fail |

The v2 objective did what it was built for: the text-only distinction
survives (Snare/Spike). The remaining failure is on the swap-pair bar,
and the per-pair readout says the bar, not the embedding, is the
problem in 13 of 16 pairs:

| pair | cos | partner's rank among 35,478 (a→b, b→a) |
|---|---|---|
| Spell Pierce / Concerted Defense | 0.901 | 10, 2 |
| Spell Pierce / Stubborn Denial | 0.874 | 22, 5 |
| Spell Snare / Dispel | 0.868 | 12, 40 |
| Bitter Triumph / Easy Prey | 0.828 | 14, 10 |
| We Say Thee Nay! / Don't Make a Sound | 0.821 | 63, 57 |
| We Say Thee Nay! / Clash of Wills | 0.812 | 77, 68 |
| Shoot the Sheriff / Cradle to Grave | 0.810 | 26, 39 |
| Bitter Triumph / Go for the Throat | 0.795 | 33, 80 |
| Spyglass Siren / Faerie Miscreant | 0.782 | 48, 78 |
| Shoot the Sheriff / Eliminate | 0.771 | 48, 28 |
| Spyglass Siren / Faerie Seer | 0.726 | 292, 96 |
| The Wondrous Wasp / Plumecreed Escort | 0.703 | 377, 240 |
| Floodpits Drowner / Zephyr Sentinel | 0.676 | 169, 297 |
| Elektra, Daughter of the Hand / Fathom Fleet Cutthroat | 0.608 | 2736, 1110 |
| Requiting Hex / Cut Down | 0.547 | 1659, 2099 |
| Elektra, Daughter of the Hand / Ravenous Chupacabra | 0.590 | 3449, 2352 |

**Correction to the gate, in the open.** The pre-registered swap bar was
written in cosine units relative to random pairs (μ + kσ). That form is
not scale-free: v1's space had μ = 0.13, v2's (anchored to MiniLM's
geometry) has μ = 0.37, so the same k demands cos 0.867 — above the
≥ 0.70 near-duplicate band PHASE-E3 used for Cancel/Counterspell-class
pairs. A bar that a functional near-reprint would fail is mis-specified.
From v3 on the swap gate is rank-based (scale-free), pre-registered here
before v3 exists and NOT applied retroactively to v2's verdict:

- every pair: partner within the top-500 (1.4 %) in both directions, for
  at least 14 of 16 pairs;
- median of the 32 directed ranks ≤ 50.

v2 would fail that too (13 of 16), so it is not a bar tuned to pass v2.
The three failing pairs share a cause visible in the text channel:
`Elektra, Daughter of the Hand` is mostly Sneak reminder text, and
Requiting Hex is mostly blight reminder text, so the anchored text view
puts them near other reminder-heavy cards rather than near their
mechanical twins. v3 therefore changes two things, both stated before
training: (1) parenthetical reminder text is stripped from the text
channel (`rl/cardemb/data.py`), (2) `--distill 3` instead of 10 so the
structure channels carry more of e_card's geometry. Same recipe
otherwise, seeds 0 and 1.

