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


## 3a — wire skeleton behind `-Drl.encoderV=7` (Lane B, 2026-09-12 11:50; branch `v7/lane-b`)

What landed (`rl/xmage-src`, all additive, nothing under `ENCODER_V < 7`
changes): `StateEncoder` carries the WIRE-V7 widths as constants, a
`CandMeta` (candidate type + the UUIDs a candidate acts on) and a `V7`
block on `EntityView` built only when `ENCODER_V >= 7` — game token idx
0–11, the two player rows (life, poison, hand, library, graveyard, exile,
mana pool by colour, untapped sources, lands, permanents), one entity row
per v6 entity minus the two player rows (zone one-hot, mine, face-down,
stack position; idx 10–63 are 3b and stay 0), `v7_ent_name` /
`v7_ent_token`, and the v6 relations shifted into the token index space.
`RLPlayer` builds a `CandMeta` at every one of the seven consult sites
(prio, target, targetCard, attack1, atkjoint, block1, blkjoint) and
passes it through a new 4-arg `PolicyClient.choose`; `SocketPolicyClient`
emits the hello keys and, per consult, the v6 line plus the `v7_*` keys
through one shared v6 writer. Recording and checking tools:
`rl/wire_echo_server.py` (records the raw wire, answers a fixed pick),
`rl/wire_record.sh`, `rl/wire_diff.py` (first differing field, or every
differing column with its per-line column sum), `rl/wire_census.py`
(behaviour counters + name resolution), `rl/live_check_3a.sh`,
`rl/sync_lane_b.sh`, `rl/drivers_3a.sh` (7910 = v6 arm, 7911 = v7 arm).

Design decisions written into the code, stated here so 3b–3e inherit
them: token index = v6 entity index + 1 (the player rows are v6 rows 0
and 1 by `ORDER`, so one shift maps the edge list and the two index
spaces cannot drift); the entity list in 3a IS the v6 list, so
`entityTrunc` is the v6 counter and `v7_emax` = 160 is only the buffer
bound (≤ 94 rows are ever emitted); decision type of a consult = the
most frequent non-PASS candidate type; `ACTIVATE` = any playable that is
neither a spell nor a land play (mana abilities included, as in v6's
playable list); the empty attack subset and the all-unassigned block
option are typed PASS; a non-PASS candidate whose referents are not
emitted entities refers to the acting player's token and is counted
(`v7_ctr.refersFallback`; `metaMissing` counts consults from an unmapped
site); `v7_decks` is not sent yet (5a), so game idx 22–23 are 0.

| gate | required | measured | result |
|---|---|---|---|
| schema on recorded consults | 100 consults pass `rl/wire_validate.py` | `v7_pass` (5 games, always-pass agent): **101 consults ok**; `v7_pick1` (first non-pass candidate every time): **136 consults ok** | pass |
| v6 arm byte-identical to the unpatched build | same seeded games, old build vs new build, every byte | 3 games / 63 consults / 134 lines: 18 lines differ, **only** `e[*][16]` tapped, `e[*][20]` canAttack, `e[*][21]` canBlock on opponent lands; the tapped column sum is equal on every differing line (which of several identical Plains was tapped, not how many); `g`, `r`, `c`, hello, replies identical | pass, within the engine's own noise (next row) |
| control: the unpatched build against itself | two runs on one JVM, same seeds | 14 lines differ, the same three columns, same column-sum pattern; the new build against itself: 18 lines, same | the residual is pre-existing: the heuristic opponent's choice among identical untapped lands is not on the seeded stream (UUID order) |
| v7 arm's v6 keys equal the v6 arm | `wire_diff.py --ignore-keys <v7 keys>` | 14 lines, the same three columns only | pass |
| referent coverage (3c's gate, measured early) | every non-PASS candidate refers to an entity or player token | 448/448 and 174/174 (6 + 6 are TARGET-a-player); `refersFallback` 0, `metaMissing` 0, `entityTrunc` 0 | pass |
| names resolve (WIRE rule 4) | 0 unresolved through `cards_v1` | 3,719 entity rows, 10 distinct names, **0 unresolved** (W0Base) | pass |
| live handshake and serving | `policy_server.py --arch v7 --frozen` with `p10_init_net.py --arch v7` (17,379,335 params), cpu, 10 eval games | accepted; 181 consults answered, 0 refusals, avg round trip 20.7 ms on cpu; driver rc 0 | pass |

Behaviour counters (`wire_census.py`; the record, not a result):

| recording | consults | ent/consult (max) | edges/consult | k mean (max) | candidate types | decision types |
|---|---|---|---|---|---|---|
| v7_pass | 101 | 14.5 (24) | 5.5 | 5.2 (8) | LAND 250, TARGET 198, PASS 74 | LAND 54, TARGET 27, PASS 20 |
| v7_pick1 | 136 | 16.6 (26) | 9.6 | 2.3 (5) | PASS 133, ACTIVATE 82, LAND 75, TARGET 6, SPELL 5, BLOCK 4, ATTACK 2 | ACTIVATE 78, LAND 26, PASS 19, SPELL 4, BLOCK 4, TARGET 3, ATTACK 2 |

Edge types seen: 2 (attacking_player) and 4 (controls) only — W0Base
against a passing or first-candidate agent produces no blocks, targets on
the stack, or attachments. Types 6 and 7 are 3c.

What these numbers cannot support: nothing about the policy (the init
net's encoder is an identity and every logit is equal, so the live-check
agent chose index 0 — PASS — at every consult and took 0 actions per
game, as pre-registered: 10 games of an untrained net are a plumbing
check, not a level). Entity idx 10–63 and the candidate afterstate slots
are 0 until 3b, so a faithfulness probe on these recordings would recover
only zone, side, stack position, identity and the v6 keys. The TARGET
consults reached even by an always-passing agent (27 of 101) are v6
behaviour (forced choices), not examined here. The recordings are
regenerable (`rl/wire_record.sh`, seed 900000) and gitignored.

## 3b — fields and operators (Lane B, 2026-09-12 13:30; branch `v7/lane-b`)

What landed: every entity row idx 10–63 of WIRE §2d — body now and printed
(`MageInt.getBaseValue`), damage, toughness remaining, loyalty, counters
(+1/+1, −1/−1, loyalty, other), status bits, turns on battlefield, type
bits, the 18 keyword bits **read off the object's abilities now**
(`getAbilities(game)`, subclass-aware, so granted and lost abilities count;
v6 reads the printed table), the operators (castable now = the engine's own
`canActivate` on the spell or land-play ability of a card in my hand; mana
left if cast = untapped lands − mana value, an estimate stated as such;
legal targets for the first target; can attack / can block; would die to
SBA as-is = creature with toughness − damage ≤ 0 or deathtouched), the
stack-only slots (X via `CardUtil.getSourceCostsTagX`, modes chosen,
controller is me, is ability). Candidate afterstates (WIRE §2f idx 8–39)
for LAND / SPELL / ACTIVATE (mana left after, targets, instant- or
sorcery-speed, flash, stack depth), TARGET (player · me · life · creature ·
P/T · mine), ATTACK (the `CombatMath.AttackOption` fields in the §2f
order), BLOCK (the `CombatMath.Outcome` of the joint assignment; block1
uses the pairwise outcome). PASS / OTHER afterstates stay 0 (reserved;
the pass afterstate is deferred, design §6) — the joint sites *could*
supply one (damage taken if I do not block, bodies retained if I do not
attack) and a first cut did, which the checker now rejects; that is a
WIRE amendment to propose, not a 3b change. Player row idx 14 (cards
drawn this turn) is still 0, and the §2c width-21 extension (untapped
sources by colour) is **not** done: it changes `v7_dims.player` and so
both consumers, and belongs in one cross-lane commit with the server.

Evidence: `rl/wire_check_3b.py` over ten recordings (`rl/record_3b.sh`;
six decks with the first-non-pass policy, four with the last-candidate
policy, 5 games each, seed 900000), **1,562 consults, 12,838 entity rows**,
all ten streams `wire_validate.py` ok, names 0 unresolved (22 distinct).

| gate | required | measured | result |
|---|---|---|---|
| agreement with the v6 row on the same entity, every field v6 also carries (17 fields: power, toughness, damage, toughness left, mv, tapped, sick, attacking, blocking, entered, token, creature, land, can attack, can block, instant/sorcery on the stack) | 0 disagreements | **0 over 12,838 rows** | pass |
| keyword bits vs the printed table (14 shared bits) | mismatches listed by name | **0** — no card on these decks gains or loses a keyword, so live-abilities and printed agree; the granted-ability case is not exercised | pass, not exercised for grants |
| identities v6 does not carry | toughness left = toughness − damage; lethal-as-is ⇒ toughness left ≤ 0; castable only on my hand; stack position only on the stack; TARGET player xor object; ATTACK opp life after = opp life − damage dealt, my life after = my life − crack-back; BLOCK life after = life − damage taken; LAND is sorcery-speed; speed one-hot; PASS afterstate all 0 | **0 failures** | pass |
| v6 arm after 3b | identical to the unpatched build | `v6_new3` is **byte-identical** to one of the two unpatched-build runs (`v6_old2a`, same md5) and differs from the other only in the tapped-land columns (the §3a noise) | pass |

Exercised on these decks (rows with a non-zero value, out of 12,838):
power / toughness / printed 11,939 · tapped 9,352 · sick 3,046 · attacking
511 · entered 685 · instant 681 · sorcery 218 · flying 140 · vigilance
162 · castable 3,369 · mana left 2,561 · legal targets 169 · can attack
3,301 · can block 5,338 · stack modes / mine 8; candidate afterstates:
ACTIVATE 971, LAND 770, SPELL 49, TARGET 60, ATTACK 21, BLOCK 28.

**Not exercised** (0 rows, so nothing here is checked beyond compiling
and the zero being correct): damage marked, blocking, loyalty and every
counter, tokens, other-permanent type, 16 of 18 keywords, lethal-as-is,
stack X, stack is-ability. The pre-registered 3b gate asked for one
constructed `Mage.Tests` scenario per operator; this row substitutes
observed scenarios from real games with a v6 cross-check, which covers
the operators the rung decks can produce and leaves the rest untested.
5b's 10k heuristic-vs-heuristic consults are the coverage run; any field
still at 0 rows there gets a constructed scenario before 5b closes.

## 3c — edges and referents (Lane B, 2026-09-12 15:10; branch `v7/lane-b`)

What landed: WIRE §2e types 6 and 7 appended to the shifted v6 edge list in
`StateEncoder.v7Block` — `can_block` (legal blocker → attacker by the
engine's `Permanent.canBlock`, emitted only in a declare-blockers consult
where I am the defending player, i.e. the consults whose block candidates
come from the same test) and `stack_above` (each stack object → the one
directly below it, in `game.getStack()`'s top-first order; a truncated
object breaks the chain rather than bridging it). `refers_to` (every
candidate's entity indices) and the stack modes / X slots landed in 3a and
3b. Recording policies for the evidence: `wire_echo_server.py --pick N`
and `--prefer-type 2,1` (cast a spell whenever one is castable, else play
a land), `rl/wire_check_3c.py`.

| gate | required | measured | result |
|---|---|---|---|
| every edge endpoint valid | inside the token space, every consult | 0 out of range over 2,955 consults / 41,000+ edges (also the validator's own check: every stream ok) | pass |
| `refers_to` coverage | 100 % of non-PASS candidates over 1,000 consults | **100 %** — 1,999 / 1,999 (ten 3b recordings, 1,562 consults), 2,497 / 2,497 (spell-first W4Inst, 972 consults), 1,022 / 1,022 (two spell-first runs, 221 consults); `refersFallback` 0 everywhere | pass |
| `can_block` agrees with the candidate builder | every BLOCK candidate's (blocker, attacker) pair is a `can_block` edge of the same consult; edges only in defending declare-blockers consults; src my untapped creature, dst an attacking creature | 0 failures: 66 edges / 28 BLOCK candidates (3b set), 246 / 63 (spell-first W4Inst), 8 / 3 (last-candidate W4Inst) | pass |
| `stack_above` chain | src and dst on the stack, dst one position deeper, n − 1 edges for n objects | 0 failures on the **2** consults that had two objects on the stack (spell-first W4Inst); every other recording had ≤ 1 | pass, barely exercised |

Coverage note that is a finding: a consult with two or more objects on
the stack is rare under these policies — 2 of 972 with the spell-first
policy, 0 of 2,000+ otherwise — because the agent is only consulted with
a non-empty stack when it holds priority with a castable instant or a
mana ability (103 of 1,599 consults in a longer spell-first run had a
non-empty stack, 26 of 972 had the agent's own object on it). The
stack-only fields and `stack_above` therefore rest on a handful of rows
until 5b's 10k-consult coverage run; if that run still shows < 100
two-object consults, a constructed scenario is owed.

3b coverage update from the spell-first recording (972 consults, W4Inst,
`--consultBudget 300`): damage marked 24 rows, blocking 33, stack modes
62, stack mine 26, SPELL afterstates 42 — **0 v6 disagreements, 0 failed
identities**, after one checker correction: v6 stack rows carry no
creature/land type bit (v7 reads the source card), so the type
comparison now skips stack rows like the body comparison already did.
A first spell-first run without a consult budget ran 1,599 consults in
one game before it was stopped (the policy casts every castable instant
every consult); recordings for coverage use `BUDGET=300`.
