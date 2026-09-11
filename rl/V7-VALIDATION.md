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

## 0c — correction: August added (Lane A, 2026-09-10 18:42)

The 2026-08 month archive (451 events) was fetched on a rerun after the
first pass had been throttled to 0. The corpus was rebuilt; the gate row
above (8,035) is superseded by this one, both stand in the file:

| gate | required | measured | result |
|---|---|---|---|
| unique constructed lists with every name resolved | ≥ 3,000 | **12,612** (1,236 held out by event) | **GO** |
| events / lists total / unique mainboards | (report) | 1,008 / 21,654 / 13,354 | — |
| slots unresolved | (report) | 1,229 / 815,512 = 0.15 % (35 names) | — |
| formats | (report) | modern 4,788 · standard 1,903 · pauper 1,868 · legacy 1,828 · pioneer 1,032 · premodern 820 · vintage 763 · duel-commander 263 | — |

50 of 1,058 event pages failed after 3 attempts (no embedded data; mostly
duel-commander league pages). The corpus file is the one masked-card
training (1c/2b) reads; it is final for v7 unless a correction row says otherwise.

## 1d — card embedder `card_emb_v3` — **FAIL** (Lane A, 2026-09-10 18:45)

Seed 0, reminder text stripped, `--positives same --distill 3`. Retrieval
r@1 train 0.773 / held-out 0.742. Seed 1 was stopped: a failed version
needs no determinism record.

| gate | threshold | measured (held-out) | result |
|---|---|---|---|
| G1 (all 33 probes) | as above | mv 0.968, power 0.971, toughness 0.971; colours ≥ 0.997; types ≥ 0.999; keywords f1 ≥ 0.976; answers f1 ≥ 0.951 | pass |
| G2 Cancel / Counterspell | ≥ 0.85 | 0.998 | pass |
| G2 Spell Snare / Force Spike | cos ≤ 0.848 and Spike ∉ Snare top-10 | **0.912**, not in top-10 (Snare's top-5: Mental Misstep, Minor Misstep, Thoughtbind, Disdainful Stroke, Nix; Spike's: Jwari Disruption, Mana Tithe, Quench, It'll Quench Ya!, Convolute) | **FAIL** on the cosine part |
| G2 functional reprints | 10/10 | 10/10 | pass |
| G2 swap pairs (rank-based) | ≥ 14/16 within 500, median ≤ 50 | **13/16**, median 46 | **FAIL** |

The three pairs outside 500 are the same three as in v2 (Elektra ×2,
Requiting Hex), improved but not enough (a→b ranks 1654 / 1078 / 786;
b→a 474 / 285 / 904). Lowering the distillation weight from 10 to 3 let
structure pull Snare and Spike back together in cosine (0.839 → 0.912)
while their neighbourhoods stayed the right families.

**Correction to the gate, in the open, for v4 on.** The Snare/Spike
cosine margin has exactly the scale-dependence already identified for
the swap bar (it is a cosine offset from Cancel/Counterspell); the
rank part of the same gate is the scale-free statement of "apart". From
v4 the gate is rank-only (Force Spike not in Spell Snare's top-10), the
cosine margin is reported as information. v3 would still fail v4's
gates (swap pairs 13/16), so this correction rescues nothing.

**v4, stated before training:** the v2 recipe (`--distill 10`, which
passed Snare/Spike with margin under both forms) plus the reminder-text
stripping introduced in v3. One variable relative to v2. If v4 fails
the swap gate on the same three pairs, the next lever is the text
model (`paraphrase-mpnet-base-v2`), not the loss.

## 1d — card embedder `card_emb_v4` — **FAIL** (Lane A, 2026-09-10 19:00)

Seed 0, v2 recipe (`--positives same --distill 10`) + reminder text
stripped. G1 pass (mv 0.949, power 0.967, toughness 0.962; all binary
probes above threshold). Cancel/Counterspell 0.999. Snare/Spike rank 43,
cos 0.841 (pass under both the rank-only gate and the old cosine bar).
Functional reprints 10/10. **Swap pairs 12/16 within 500, median 73 —
FAIL**, and worse than v2 (13/16, median 66). Stripping reminder text
did not move the Elektra / Requiting Hex pairs; the text encoder is not
the lever. Seed 1 stopped.

What v1–v4 establish together: with a 68-column readout bag as the
only structural channel, conditions (mana value ≤ 2, unless pays {1},
ETB destroy) are carried by text alone, and a MiniLM text view cannot
be both fine enough to separate Snare from Spike and robust enough to
put Elektra next to Chupacabra. Next version changes the structural
channel, not the loss and not the text model.

**v5, stated before training:** the ability tree itself as the graph
channel (`rl/cardemb/tree.py`, `TreeEncoder` in `model.py`): node
tokens from kind / api / mode / keyword plus (param key, value-piece)
pairs with numbers bucketed, edge-type attention bias, 2 layers, pooled
to 128 and concatenated into the structure view next to the readout bag
and the printed fields. Structure keys for the objective come from the
canonical tree (31,881 distinct of 35,478 vs 26,324 with the bag; Snare
and Spike now differ, Cancel and Counterspell still coincide). Loss and
distillation as v2 (`--positives same --distill 10`), reminder text
stripped as v3/v4. Same gates.

## 1d — card embedder `card_emb_v5` (ability-tree channel) — **FAIL** (Lane A, 2026-09-10 19:22)

Seed 0, v4 recipe + `--tree`. Retrieval r@1 held-out **0.932** (v2–v4:
0.74): with the tree in the structure view, text has a distinct target
per card. Gates:

| gate | threshold | measured (held-out) | result |
|---|---|---|---|
| G1 mv / power / toughness probe acc | ≥ 0.9 | **0.708 / 0.889 / 0.888** | **FAIL** |
| G1 colours | each ≥ 0.97 | min **0.962** (R) | **FAIL** |
| G1 types / keywords / answer classes | ≥ 0.97 / f1 ≥ 0.8 | 0.999 / 0.933 / 0.817 | pass |
| G2 Cancel / Counterspell | ≥ 0.85 | 0.999 | pass |
| G2 Spell Snare / Force Spike | Spike ∉ Snare top-10 | rank 34, cos **0.730** (best of any version) | pass |
| G2 functional reprints | 10/10 | 10/10 | pass |
| G2 swap pairs | ≥ 14/16 within 500, median ≤ 50 | 13/16, median **102** | **FAIL** |

Two new failures, both pointing the same way. The printed fields are
no longer linearly recoverable from `e_card`: the fused projection
(text 128 + bag 128 + printed 32 + tree 128 → 128) is free to spend its
capacity on the tree, and nothing in the loss asks the fused vector to
keep the printed one-hots readable — in v1–v4 they survived only
because the structure view was mostly printed + bag. And the swap pairs
got worse while retrieval got much better: hashed param pieces make
31,881 of 35,478 trees distinct, so the structure view can behave like
a per-card lookup, and neighbourhoods reflect token overlap rather
than mechanical similarity. Seed 1 stopped. Per-view diagnostics
(tree view alone, text view alone) follow before v6 is specified.

### Per-view diagnostics, v5 and v2 (`rl/cardemb/diag_views.py`, 19:30)

| version / view | dim | mv probe | colour R probe | Snare→Spike rank | swap within 500 | swap median |
|---|---|---|---|---|---|---|
| v5 text | 128 | 0.318 | 0.831 | 64 | 10/16 | 166 |
| v5 struct (bag+printed+tree) | 288 | 0.997 | 1.000 | 30 | 12/16 | 94 |
| v5 tree alone | 128 | 0.297 | 0.736 | 32 | 9/16 | 190 |
| **v5 e_card** | 128 | 0.707 | 0.962 | 33 | 13/16 | 102 |
| v2 text | 128 | 0.349 | 0.866 | 60 | 11/16 | 64 |
| v2 struct (bag+printed) | 160 | 0.998 | 1.000 | **1** | **16/16** | **1** |
| **v2 e_card** | 128 | 0.944 | 0.997 | 40 | 13/16 | 72 |

Three things this table settles:

1. **`e_card` was never trained, in any version (v1–v5).** The losses act
   on the contrastive heads and the text view; the fusing projection
   (`fuse`, `norm`) gets no gradient, so `e_card` has been a random
   linear mix of the channel features, dominated by whichever channel
   has the largest norm. v5's structure view reads mv at 0.997 and its
   fused vector at 0.707. This is a defect in the embedder, recorded as
   such; every gate result above stands (they measured what consumers
   would have received), but the diagnosis in the v2–v4 rows that
   attributed swap-pair failures to the text encoder is only half the
   story — the blend was uncontrolled.
2. The bag view alone puts all 16 swap pairs at rank 1 (they *are*
   identical bags) and cannot separate Snare from Spike (rank 1). The
   tree view alone separates them (rank 32) but scatters mechanically
   similar cards (Requiting Hex / Cut Down at 27,422), because the
   text↔tree contrastive objective rewards discrimination, not
   smoothness over mechanics, and hashed param pieces make near-lookup
   possible.
3. The text view alone is the weakest on both counts in every version.

**v6, specified before training (same gates):**

- `e_card` is block-structured, each slice its own linear projection
  followed by its own LayerNorm: text 48 | tree 32 | bag 16 | printed 32
  (= 128). Cosine on `e_card` is then the width-weighted mean of the
  per-slice cosines (37.5 % text, 25 % tree, 12.5 % bag, 25 % printed),
  a stated blend instead of an accident of norms.
- Reconstruction losses give the fused slices gradient and make them
  mean what they are named: the tree slice must predict the 68-column
  readout (MSE, weight 1); the printed slice must predict the 83 printed
  floats (MSE, weight 1). The readout is a deterministic function of the
  tree, so this asks the tree encoder to organise by mechanics first
  and conditions second.
- Param-piece dropout 0.2 in the tree encoder during training, against
  lookup behaviour.
- Everything else as v5 (`--positives same --distill 10 --tree`,
  reminder text stripped). Prediction: G1 restored by construction; swap
  pairs ≥ 14/16 because the bag and printed slices carry half the blend
  and rank those pairs at 1; Snare/Spike stays apart because the text
  and tree slices order cards *within* a shared bag.

## 1d — card embedder `card_emb_v6` — seed 0 passes G1 and G2; G3 pending (Lane A, 2026-09-10 19:52)

Seed 0, v5 recipe + `--fuse blocks --aux 1.0 --piece-dropout 0.2`.
Retrieval r@1 train 0.944. Gates as pre-registered (rank-based G2):

| gate | threshold | measured (held-out) | train | result |
|---|---|---|---|---|
| G1 mv / power / toughness probe acc | ≥ 0.9 | **0.993 / 0.995 / 0.995** | 0.999 / 1.000 / 1.000 | pass |
| G1 colours (5), types (6), keywords (11), answer classes (5) | ≥ 0.97 acc / ≥ 0.8 f1 | min 1.000 / 1.000 / 0.955 / 0.902 | | pass |
| G2 Cancel / Counterspell cos | ≥ 0.85 | 0.984 | | pass |
| G2 Spell Snare / Force Spike | Spike ∉ Snare top-10 | rank 19 (cos 0.920; old cosine bar would fail — informational) | | pass |
| G2 functional reprints in top-3 | 10/10 | 10/10 | | pass |
| G2 swap pairs | ≥ 14/16 within 500, median ≤ 50 | **14/16, median 26** | | pass |
| G3 determinism | Jaccard ≥ 0.4, same verdicts | seed 1 training | | pending |

Per-view (`diag_views.py`): e_card mv 0.993 / colour 1.000 / Snare→Spike 19 /
swap 14/16 median 26; struct view 0.991 / 1.000 / 41 / 14/16 median 84;
tree view alone 0.299 / 0.723 / 43 / 12/16 median 158; text view 0.326 /
0.835 / 79 / 11/16 median 162. The fused vector is now better than any
single view on every column, which is what the block blend plus
reconstruction losses were built to do. The two pairs still outside 500:
Spyglass Siren / Faerie Seer (1081, 831) and Requiting Hex / Cut Down
(270, 822). The pre-registered prediction for v6 (G1 restored by
construction, swap ≥ 14/16, Snare/Spike apart) held on seed 0.

Not yet a frozen artifact: the version is accepted only when seed 1's
G3 row is appended below.

## 1c / 2b — masked-card-in-deck, `rl/artifacts/deck_ctx_v1` (Lane A, 2026-09-10 20:01)

`rl/cardemb/train_masked.py` on `card_emb_v6/emb.pt` (frozen; v6 accepted
on G1/G2, G3 pending at the time — if G3 fails this row is rerun), corpus
`decklists_v1` (11,376 train / 1,236 held-out clean lists, held out by
event), 15 % of distinct cards masked per deck, vocabulary = 3,519 cards
seen in training lists, 20 epochs, 24 s/epoch.

| gate | baseline | measured (held-out, 4,141 masked slots) | result |
|---|---|---|---|
| masked top-1 | most-frequent card 0.020; per-format 0.025 | **0.407** | pass (20× the stronger baseline) |
| masked top-10 | 0.129; per-format 0.164 | **0.727** | pass |
| train top-1 / top-10 (7,114 slots) | | 0.407 / 0.730 | no train/held-out gap |

Caveats: the frequency baselines are weak by construction (they are the
plan's stated comparison, not a strong model); a per-archetype
nearest-list baseline would be the honest next comparison and is not
run. Copy counts of masked cards stay visible (design: count is an L1
feature). Vocabulary restriction means a masked card outside the 3,519
is never predictable (12.5 % of slots, excluded from n).

## 2c — role probe on c'ᵢ (Lane A, 2026-09-10 20:03)

`rl/deckctx/probe_roles.py` (thresholds pre-registered 17:25, commit
fcff38a), model `deck_ctx_v1/model_seed0.pt`, probes fit on 3,000 train
(deck, card) rows, scored on 769 held-out rows:

| label | held-out pos/neg | c'ᵢ probe bal-acc | e_card probe (reference) | identity-init c'ᵢ (2b fallback) | threshold | result |
|---|---|---|---|---|---|---|
| wincon | 200/569 | 0.982 | 0.996 | 0.996 | ≥ 0.85 | pass |
| answer | 120/649 | 0.960 | 0.987 | 0.987 | ≥ 0.80 | pass |
| enabler | 359/410 | **0.814** | 0.720 | 0.720 | ≥ 0.70 | pass |

What the context adds is the relational label: *enabler* (is this card
the enabler side of a synergy edge in this deck) rises from 0.72 to
0.81; the card-intrinsic labels are already in e_card and lose a little
to the mixing. The held-out row count (769) is small; the enabler
number's Wilson 95 % interval is roughly ±0.03.

### 1d — `card_emb_v6` G3 — **FAIL** (20:12)

| gate | threshold | measured | result |
|---|---|---|---|
| G3 seed 0 vs seed 1 top-10 Jaccard (2,000 random cards) | ≥ 0.40 | **0.369** | **FAIL** |
| G3 same G2 verdicts on both seeds | identical | identical (all pass on seed 1 too) | pass |

v6 is therefore not accepted (v1: 0.479, v2: 0.424 on the same gate).
The two seeds agree on every gate verdict but not on fine neighbourhood
structure. Per-slice seed overlap follows to locate the instability
before v7 is specified; the deck-context rows above (1c/2b/2c) were run
on v6 seed 0 and will be rerun on the accepted version.

### Per-slice seed overlap, v6 (top-10 Jaccard, 2,000 cards; 20:15)

| vector | Jaccard seed 0 vs 1 |
|---|---|
| whole e_card (the G3 number) | 0.369 |
| text slice [0:48] | **0.238** |
| tree slice [48:80] | 0.263 |
| bag slice [80:96] | 0.647 |
| printed slice [96:128] | 0.855 |
| whole without the text slice | **0.426** (would pass) |
| whole without tree / bag / printed | 0.318 / 0.327 / 0.341 |

The two slices with a reconstruction loss (printed, tree) are the
stable ones relative to their content; the two without (text, bag) are
random per-seed projections of trained features — the same defect as
the untrained fuse of v1–v5, in smaller form — and the text slice at
37.5 % of the blend drags the whole under 0.40.

**v7, specified before training (same gates):** every slice gets a
deterministic reconstruction target, weight 1 each, alongside v6's two:
the text slice must decode the frozen pretrained MiniLM embedding of
the card (384-d, the same for every seed), the bag slice must decode the
68-column readout. Nothing else changes (`--fuse blocks --aux 1.0
--piece-dropout 0.2 --distill 10 --tree`). Prediction: text-slice
overlap rises well above 0.24 because its target is seed-independent,
the whole clears 0.40, and the G1/G2 verdicts are unchanged (the slices'
contents are the same information, better anchored). If G3 still fails,
the next lever is the tree slice (0.263): a fitted vocabulary instead of
hashed pieces, so its input embedding table is not a per-seed random
draw over 16k buckets.

## 1d — card embedder `card_emb_v7` — **FAIL** on G2 (Lane A, 2026-09-10 20:38)

Seed 0, v6 + a reconstruction target for every slice (text slice →
frozen MiniLM embedding, bag slice → readout). Seed 1 stopped.

| gate | threshold | measured | result |
|---|---|---|---|
| G1 mv / colours | ≥ 0.9 / ≥ 0.97 | 0.994 / 1.000 | pass |
| G2 Cancel / Counterspell | ≥ 0.85 | 0.983 | pass |
| G2 Spell Snare / Force Spike | Spike ∉ Snare top-10 | **rank 6, cos 0.997** (v6: rank 19) | **FAIL** |
| G2 functional reprints in top-3 | 10/10 | **8/10** | **FAIL** |
| G2 swap pairs | ≥ 14/16 within 500, median ≤ 50 | 16/16, median 14 (best of any version) | pass |

Anchoring the text slice to the frozen pretrained embedding made that
slice *be* the frozen embedding, and the frozen encoder puts Snare and
Spike together — the coarse text geometry PHASE-E3 already measured.
Seed stability and condition sensitivity in the text slice were traded
against each other; the swap pairs (which reward coarse similarity)
improved for the same reason. This is the point at which iterating on
G3 stops producing an embedder that is better for the policy.

**Decision required, recorded here for the user:** (a) accept v6 with
its G3 deviation stated (0.369 vs the pre-registered 0.40; both seeds
reach identical verdicts on every G1/G2 gate), or (b) continue. The
lane's recommendation is (a): G3's threshold is a proxy set blind, the
verdicts agree, and v6's remaining defects (text and bag slices
untrained) are harmless to a consumer that learns an adapter, which is
every consumer in the design. Consumers would record `card_emb_v6`.

**Decision (user, 20:42): keep iterating.**

**v8, specified before training (same gates):** each slice's target must
be both seed-independent and condition-bearing — v7 showed a target
that is only the former (the frozen embedding) erases conditions.

- text slice: relational distillation to the frozen encoder's in-batch
  cosine matrix (the same objective the text *view* has had since v2,
  weight 10), instead of v7's direct decode. Relational anchoring left
  Snare/Spike at rank 79 in the view; decoding collapsed them to 6.
- tree slice: reconstructs, in addition to the 68-column readout, the
  tree's own token bag — a 2,048-bucket multi-hot of its hashed param
  pieces and node ids (BCE, weight 1). Seed-independent by
  construction and it contains the conditions (`cmcEQ2`, `UnlessCost`).
- bag slice: reconstructs the 68-column readout (weight 1), as in v7.
- everything else as v6 (`--fuse blocks --aux 1.0 --piece-dropout 0.2
  --distill 10 --tree`).

Prediction: text-slice overlap rises from 0.24 toward the view's own
seed agreement, tree-slice overlap rises from 0.26, whole ≥ 0.40;
Snare/Spike stays outside the top-10; swap pairs ≥ 14/16. Risk stated:
the token-bag target could make the tree slice lookup-like and cost
swap-pair smoothness; the readout target and piece dropout are the
counterweights. If v8 fails G3 with G2 intact, the next lever is the
text encoder's learning rate (3e-5 → 1e-5, fewer trainable layers), the
remaining seed-dependent component.

## 1d — sweep config (a): v6 structure + stability recipe + 2-seed averaged artifact — **FAIL on one probe** (Lane A, 2026-09-11 00:05)

`rl/cardemb/sweep.sh` config a (CARDEMB-RESEARCH.md §3 steps 2–3 only):
hashed-tree GNN as in v6, `--lr-text 2e-5 --llrd 0.85 --warmup 0.10
--epochs 40`, artifact = per-slice Procrustes mean of seeds 0+1, G3
against the mean of seeds 2+3. Four seeds trained (24 min each).

| gate | threshold | measured (held-out) | result |
|---|---|---|---|
| G1 mv / power / toughness | ≥ 0.9 | 0.993 / 0.997 / 0.994 | pass |
| G1 colours, types | ≥ 0.97 | 1.000, 1.000 | pass |
| G1 keywords (11, f1) | ≥ 0.8 | min 0.817 (first strike, 42 positives) | pass |
| G1 answer classes (5, f1) | ≥ 0.8 | **min 0.725 (ans_minus_toughness, 33 positives)**; v6 had 0.943 | **FAIL** |
| G2 Cancel / Counterspell | ≥ 0.85 | 0.983 | pass |
| G2 Spell Snare / Force Spike | Spike ∉ Snare top-10 | rank 28 | pass |
| G2 functional reprints | 10/10 | 10/10 | pass |
| G2 swap pairs | ≥ 14/16 within 500, median ≤ 50 | **16/16, median 29** | pass |
| G3 artifact(0+1) vs artifact(2+3) top-10 Jaccard | ≥ 0.40 | **0.680** (raw single seeds 0.623; v6 was 0.369) | pass |

Per-slice overlap (artifact vs artifact): text 0.734, tree 0.475, bag
0.796, printed 0.872. The stability recipe alone (before averaging)
raised seed overlap from 0.369 to 0.623 — the literature's prediction
(CARDEMB-RESEARCH.md §2b) held; averaging added a further 0.06.

The single failing probe is a rare mechanical bit (33 held-out
positives; Wilson 95 % on F1 roughly ±0.15). The raw single seed fails
it too (0.733), so it is the recipe, not the averaging: a smaller,
layer-decayed text learning rate leaves less rare mechanical detail in
the text slice, and the readout reconstruction on the tree slice is a
plain MSE, which under-weights a column with 1 % positives. Stated
before running: **configs c = a + BCE-with-logits readout
reconstruction with per-column pos_weight = neg/pos (clamped at 50),
the standard imbalanced multi-label loss, and d = b + the same**
(`rl/cardemb/sweep2.sh`, queued behind b). Prediction: the rare answer
classes and keywords return above 0.8 with G2/G3 unchanged in verdict.

## 1d — **`card_emb_v8` ACCEPTED with a stated deviation** (Lane A, 2026-09-11 08:20)

Decision by the user (2026-09-11): sweep config (a) is frozen as
`rl/artifacts/card_emb_v8`. It passes G2 (all four) and G3 (0.680) and
32 of 33 G1 probes; the one below threshold is `ans_minus_toughness`
F1 0.725 vs 0.80 on 33 held-out positives (interval ≈ ±0.15), a bit the
policy also receives exactly through the 68-column readout. Grounds:
every consumer learns an adapter on a frozen embedding, so presence and
stability of information are what matter; this is the first version
that is reproducible across seeds. This is a deviation from the
pre-registration, recorded here rather than by moving the bar. Sweep
configs c/d continue; a full pass becomes v9 as a drop-in.

Consumers record `card_emb_v8`. `rl/artifacts/card_emb_v6/` is a failed
version kept for the record.

## 1c / 2b — correction: deck context retrained on the accepted `card_emb_v8` (Lane A, 2026-09-11 07:49)

Same recipe as the provisional run above (which used the failed v6);
this row supersedes it. `deck_ctx_v1/model_seed0.pt` is now the v8-based
model.

| gate | baseline | measured (held-out, 4,141 masked slots) | result |
|---|---|---|---|
| masked top-1 | most-frequent 0.020; per-format 0.025 | **0.409** (v6-based: 0.407) | pass |
| masked top-10 | 0.129; per-format 0.164 | **0.746** (v6-based: 0.727) | pass |
| train top-1 / top-10 (7,114 slots) | | 0.411 / 0.743 — no train/held-out gap | — |

## 2c — correction: role probe on the v8-based deck context (Lane A, 2026-09-11 07:51)

| label | held-out pos/neg | c'ᵢ probe bal-acc | e_card (v8) reference | threshold | result |
|---|---|---|---|---|---|
| wincon | 200/569 | 0.987 | 0.997 | ≥ 0.85 | pass |
| answer | 120/649 | 0.969 | 0.989 | ≥ 0.80 | pass |
| enabler | 359/410 | **0.770** (v6-based: 0.814) | 0.696 | ≥ 0.70 | pass |

The context still adds on the relational label (enabler 0.70 → 0.77 over
raw e_card) and gives back a little on card-intrinsic ones. The enabler
number moved down by 0.044 from the v6-based run; with 769 held-out
rows that is within the ±0.03 interval stated above plus the change of
embedder, and it clears the pre-registered 0.70. Phase 2 gates stand.

## 0a — wire contract `rl/WIRE-V7.md`, fixtures, validator (Lane D, 2026-09-11 09:05)

| gate | required | measured | result |
|---|---|---|---|
| validator passes on every fixture | all | 7 valid streams (one per decision type; 20 consults + replies each; the last 3 with opponent tokens): 140/140 consults accepted | pass |
| a deliberately broken fixture is rejected with the field named | each | 14/14 broken streams rejected; each message names the key and position (e.g. `v7_cand_refers[1]: empty for non-PASS candidate (type 2)`, `v7_edges[4]: type 8 >= v7_rtypes 8`) | pass |
| unit test | | `tests/test_wire_v7.py`: 22 passed | pass |

Files: `rl/WIRE-V7.md` (the contract; v6 keys unchanged, `v7_*` groups
appended, append-only tables), `rl/wire_validate.py` (structural +
semantic checks, `--emit-schema`), `rl/wire_fixtures.py` →
`rl/fixtures/v7/{valid_*,broken_*}.jsonl`, `schema.json`. Consumers:
Lane B (`encoderV=7` emitter, gate 3a runs the validator on 100 recorded
consults), Lane C (`V7Obs` parser, gate 4a parses every fixture and
refuses every broken one).

## 0d — probe harness `rl/probes/faithfulness.py`, `rl/probes/leak.py` (Lane D, 2026-09-11 09:30)

| gate | required | measured | result |
|---|---|---|---|
| faithfulness self-test recovers planted fields | 1.0 | synthetic tokens (60 games × 40 tokens, 64-d, fixed nonlinear stage), 6 planted fields, game-grouped 20 % hold-out: binaries 1.000 / 1.000 / 1.000, 5-class 1.000, reals R² 0.995 / 0.998 | pass |
| faithfulness self-test refuses a dropped field | chance | the 5-class field zeroed at the input: held-out 0.183 vs chance 0.215 → FAIL reported; the other five still 1.0 | pass |
| leak self-test refuses a planted leak | refuse | policy reading one hidden bit: level 2 max \|Δlogit\| = 0.500 → refused; clean policy: 0.0 → passes; a consumer that ignores the channel → refused at level 3 (max \|Δ\| = 0.0) | pass |

`leak.py` generalises `oracle_gate.py` levels 1–3 to any hidden channel
(`hidden_keys`, a policy-path `parse`, `logits`, a privileged
`consumer`, and a `swap` that changes only the hidden content).
Level 2 is a *swap* test, not presence/absence: a tracker that copied
one bit of the true hand into a "legal" field would pass
present/absent and fail swap. Consumers: Lane B gate 3d, Lane C gates
4b/4c/4e/4f.

## 4a — server-side wire parse `rl/v7_obs.py` (Lane C, 2026-09-11 09:50)

| gate | required | measured | result |
|---|---|---|---|
| fixtures parse | every valid fixture | 7 × 20 consults → `V7Obs` (typed edge matrix over the token space, `refers_to` multi-hot, masks); names resolved to `cards_v1` ids 2,576 / 2,576 | pass |
| every malformed fixture refused with the reason | 13 (the reply-range fixture is the server's own output, checked by `wire_validate.py`) | 13/13 refused, message names key and position; handshake refuses a missing `wire`, a dims mismatch, and a `card_emb` mismatch | pass |
| `entattn_check.py` unchanged | bit-identical | `rl/v7_obs.py` is not imported by the v6 path; `policy_server.py` untouched on this branch (same 23 checks / same pre-existing R0-NOBIAS as `rl/artifacts/v7/baseline.md`) | pass |
| unit tests | | `tests/test_v7_obs.py`: 22 passed | pass |

`collate()` pads to common sizes with boolean masks per group; the
checkpoint `dims` record is `dims_record(hello)` (wire, v7_dims, rtypes,
ctypes, zones, card_emb, d_c). Consumers: 4b token builders (next).

## 4b — token builders `rl/v7_net.py` (Lane C, 2026-09-11 10:20)

| gate | required | measured | result |
|---|---|---|---|
| shape tests | per group `[B, n, 256]`, masked padding zero, finite | `tests/test_v7_net.py` on 140 fixture consults: game [B,1], players [B,2], ent [B,N], cand [B,K], opponent groups; padded tokens exactly 0 | pass |
| faithfulness probe after L3 (untrained builder, random card table) | every planted field recovered | zone 1.000 (chance 0.42) · mine 0.996 · tapped 0.992 · power R² 0.955 · mana value R² 0.940 · candidate type 1.0; thresholds for this **untrained** check: 0.99 binary/cat, 0.90 real | pass |
| adapter starts as identity; unknown id → zero row + flag | exact | exact | pass |

Two findings on the way, both recorded in the code: an MLP-only builder
at random init already attenuated planted fields (tapped, power R² 0.89);
the builder is now `MLP(x) + Linear(x)` with the body's output layer
zero-initialised, so an untrained token is exactly the linear image of
its inputs and nonlinear facts are learned on top. The probe's fits are
regularised (ridge α = 1, logistic C = 1) after the α = 1e-3 fit
overfit 256-d tokens on 2,400 samples. **The same probe must be rerun on
the trained checkpoint (Phase 5) at the module defaults (0.99 / 0.95):
this row establishes the architecture, not a training run.**

## 4c — state-graph encoder `rl/v7_encoder.py` (Lane C, 2026-09-11 10:50)

One pre-LN transformer over every token group in one sequence (game, players,
entities, candidates, opponent hand / deck / actions), edge-typed attention
bias (wire types 0–7 plus `refers_to` / `referred_by` for candidate and
opponent-action tokens), stack-depth embedding, d 256 × 8 heads × 6 layers,
FFN 1024, no pooling.

| gate | required | measured (`tests/test_v7_encoder.py`, fixtures, float64) | result |
|---|---|---|---|
| zero-edge arm equals plain attention | exactly (R0 precedent) | `torch.equal` on the full sequence with all edges zero vs `use_edges=False` (the no-edge bias row is a fixed zero buffer); with edges present the output differs (> 1e-6) | pass |
| permutation equivariance | ≤ 1e-6 | entities and candidates permuted per row, edge matrix / `refers` permuted consistently: max abs diff ≤ 1e-6 on entity, candidate and game tokens | pass |
| masking | padding never changes a real token | 5 padding entities appended: real-token outputs ≤ 1e-6 from reference, padding outputs exactly 0 | pass |
| faithfulness probe after L4 (untrained) | every planted field | identity at init (`allclose` to the builder tokens), so the 4b numbers reproduce: zone 1.000 · mine 0.996 · tapped 0.992 · power R² 0.955 · mv R² 0.940 | pass |

As with 4b, the attention output projection and FFN output layer are
zero-initialised so the untrained encoder is the identity; the probe at
init establishes the architecture, and must be rerun on the trained net
at the module defaults (0.99 / 0.95) in Phase 5.

## 4d — heads and memory `rl/v7_heads.py` (Lane C, 2026-09-11 11:20)

Pointer MLP per candidate token + bilinear term with the game token, masked
softmax; LSTMCell on the game token with the memory path residual on it
(`game_vec = g + Linear(h)`, zero-initialised, so at init the game vector is
exactly the encoded game token).

| gate | required | measured (`tests/test_v7_heads.py`) | result |
|---|---|---|---|
| logits invariant to padding | exact on real candidates, −∞ on padding | 4 padding candidates + 4 padding entities appended: real logits ≤ 1e-6 from reference, padding −∞, softmax sums to 1 over real | pass |
| candidate-count probe from the game token | linear readout | 700 generated consults, untrained encoder (architecture at init): R² ≥ 0.9 | pass |
| memory carries information across consults | planted bit recoverable at t+1 | bit planted on 16 dims of the game token at t, memory path woken (random 0.1); logistic probe on the t+1 game vector ≥ 0.9 (chance 0.52); t+1 vector differs with vs without state | pass |

The two probe gates needed hundreds of consults (a 256-d linear probe on
42 samples is meaningless); the test generates 700 in memory with
`wire_fixtures.valid_stream`. Untrained-architecture caveat as 4b/4c.

## 4e — value trunk `rl/v7_value.py` and the leak gate (Lane C, 2026-09-11 11:40)

Own token builders (sharing only the frozen card table), own 4-layer
encoder, privileged rows (`oe`, and the true opponent hand `v7_oe_hand`
from 3d) enter as extra tokens here and nowhere else; value from the
encoded game token.

| gate | required | measured (`tests/test_v7_value.py`, `rl/probes/leak.py`) | result |
|---|---|---|---|
| level 1 — wire | policy-path parse identical with / without the privileged keys | identical on 12 consults (`V7Obs` tensors never include `oe` / `v7_oe_hand`) | pass |
| level 2 — net | policy logits bit-identical under a swap of privileged content | max \|Δlogit\| = **0.0** | pass |
| level 3 — consumer | the critic moves under the same swap | max \|Δvalue\| = 0.035 (≥ 1e-4) | pass |
| planted leak refused | | a policy reading one `oe` value: level 2 max \|Δlogit\| > 1e-3 → refused | pass |

## 4f — belief module `rl/v7_belief.py` (Lane C, 2026-09-11 12:00)

Separate 2-layer transformer over the legal opponent tokens (hand slots,
remaining deck, actions) and the game token; per-slot pointer over the
remaining-deck tokens, per-card P(in hand) and P(next draw); outputs
attached as features to the opponent tokens; own loss and optimiser;
every input detached (stop-gradient into the shared builders).

| gate | required | measured (`tests/test_v7_belief.py`) | result |
|---|---|---|---|
| `--belief off` → net bit-identical to 4e | `torch.equal` | logits `torch.equal` with the module off; differ (> 1e-9) with it on | pass |
| loss never reaches a policy parameter | zero grads on shared builders | after `belief.loss(...).backward()`: every builder parameter grad None/0; belief params non-zero | pass |
| leak gate with belief on | policy logits invariant to privileged swap | identical logits on 8 consults under `oe` / `v7_oe_hand` swaps | pass |
| beats uniform-over-remaining on a planted rule | held-out log-lik > baseline | −1.31 vs −2.54 after 150 steps on 36 consults (12 held out) | pass |

The real gate (Phase 6) is the held-out log-likelihood of the TRUE hand
from self-play labels; this row shows the mechanism works, not that the
game's hidden hands are predictable.

## 4g (part 1) — `rl/v7_policy.py`, `rl/v7_check.py` (Lane C, 2026-09-11 12:30)

| gate | required | measured | result |
|---|---|---|---|
| assembled policy runs on fixtures | logits [B,K] (−∞ on padding), value [B], game vector, LSTM state | `tests/test_v7_policy.py`: shapes and finiteness on 4 generated consults | pass |
| checkpoint `dims` record | a disagreeing record is refused with the reason, before anything is built | `ent=63` in a saved record → `ValueError("dims record ...")` | pass |
| `--frozen` | no trainable parameter | `policy_parameters() == []`, every `requires_grad` False | pass |
| `rl/v7_check.py` collects every gate | exit 1 on any failure | 14 checks: wire ok/bad, parse, both probe self-tests, 8 pytest suites, `V6-SAME` (entattn_check summary identical to `baseline.md`: 23 checks / 1 known failure) — all pass, 65 s | pass |

Parameter count at d 256 / 6 encoder layers / 4 value layers (card table
excluded): total 17.4 M, policy-trainable 15.6 M, belief 1.8 M, critic 6.9 M.
Still to do in 4g: the PPO plumbing inside `policy_server.py` behind
`--arch v7` (V7Obs buffers, BPTT windows, batcher, `p10_init_net.py --arch
v7`), and the memory gate (`update_profile.py` at 5,000 steps within the
16 GB cgroup; `consult_cost.py` on an idle GPU).

