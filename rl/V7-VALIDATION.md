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

## 4g (part 2) — `policy_server.py --arch v7`, PPO plumbing (Lane C, 2026-09-11 16:30)

What landed: `--arch v7` in `rl/policy_server.py` (handshake through
`v7_obs.check_hello_v7`, consults through `parse_consult` → `compact` →
`V7Policy.forward` with a per-session LSTM state, PPO over buffers of
`V7Obs` replayed as true-BPTT windows with `--tbptt`/`--ep-batch`, the
inference batcher, `--frozen` = no optimiser, checkpoints carrying the
WIRE-V7 dims record + the net's config); `rl/v7_deckctx.py` (WIRE §5
deck context from `deck_ctx_v1` at hello, `--deck-ctx auto|none|<dir>`);
`p10_init_net.py --arch v7`; `update_profile.py --arch v7` (+ `UPDMEM`
peak-RSS line) and `consult_cost.py --arch v7`; `tests/test_v7_server.py`
(10 tests, in `v7_check.py`).

| gate | required | measured | result |
|---|---|---|---|
| handshake | v7 server refuses a v6 hello and a wrong card table; v6 server refuses `wire:7`; reason reaches the driver as `{"ok":0,"err":…}` | `test_handshake_refusals`, `test_server_process_end_to_end` (the real process, two connections) | pass |
| serving | fixture consults answered in range; LSTM state advances per consult, resets at `end`; broken consult refused with the wire's reason | `test_serve_memory_and_buffer`; eval mode stores nothing | pass |
| training | `UPDATE_EPISODES` episodes → one PPO update that moves policy/critic/adapter parameters and **not** the belief module or the card rows; checkpoint reloads by `Trainer` (dims + config) and by `V7Policy.load`; disagreeing dims record refused | `test_update_moves_policy_not_belief_and_checkpoints` (3 episodes, tbptt 3, ep-batch 2 → several windows and groups) | pass |
| `--frozen` | no optimiser, nothing stored, nothing written | `test_frozen_has_no_optimiser_and_never_saves` | pass |
| batcher | a batch of several consults equals one-at-a-time forwards (logits, value, state) to 1e-5 | `test_batcher_matches_sequential` | pass |
| deck context | D vectors and per-id overrides reach the forward; an override for an id nobody has changes nothing | `test_deck_context_reaches_forward`; `deck_ctx_v1` loads, results cached per list | pass |
| `RL_DUMP_BUF` | the v7 buffer round-trips for the profiler | `test_dump_buf_round_trips` | pass |
| v6 untouched | `entattn_check.py` summary identical to `baseline.md` | `v7_check.py`: 15 checks, 0 failures, 78 s (`V6-SAME` 23 checks / 1 known failure, as before) | pass |
| init checkpoint | `p10_init_net.py --arch v7` mints a Trainer-loadable file | 17,379,335 params (policy-trainable 15,599,621), 87.8 MB, loads by `Trainer` and `V7Policy.load` | pass |
| memory gate | `update_profile.py` peak RSS within the 16 GB cgroup at 5,000 steps, real size, cuda | **NOT RUN** — GPU held by the embedder sweep. CPU smoke only: 2 encoder / 1 value layer, 176 synthetic steps, tbptt 8, ep-batch 2: 472 ms/step, RSS 1.67 GB | open |
| consult cost | `consult_cost.py --arch v7 --device cuda` | **NOT RUN** (same reason). CPU smoke, full-size net, 51 tokens: fwd1 32.6 ms, fwd4 16.4 ms/row, parse 0.18 ms, full validation 0.52 ms, json 0.16 ms | open |

Notes and what these numbers cannot support:

- The CPU rows are smoke tests of the code path, not the gate: the gate is
  the real size on cuda at 5,000 steps, to be run when `nvidia-smi` shows
  the GPU idle and appended here as a correction row. The 472 ms/step CPU
  figure is per-step collate + forward + backward at 2 layers and says
  nothing about the cuda rate.
- **At init the encoder is an exact identity** (attention output
  projections and FFN output layers are zero-initialised in `v7_encoder`,
  by design from 4c): entity, opponent and edge content cannot reach the
  logits or the value until those weights move. A probe of "does X reach
  the policy" on an untrained net must first perturb `blk.att.out.weight`
  (the deck-context test does); a flat early learning curve is not
  evidence that a channel is dead. Pre-registered accordingly.
- The privileged v6 `oe` rows go to the critic whenever the driver emits
  them (no `--oracle` flag on v7: the value trunk is separate by design,
  4e). The leak gate in `rl/probes/leak.py` is what proves the policy path
  never reads them; it is re-run under 3d.
- The belief module is forward-only here (its features attach to the
  opponent tokens; the PPO optimiser owns none of its parameters). Its
  training is Phase 6.
- WIRE validation runs in full on the first 100 consults of every
  connection (`--v7-validate`), then the cheap parse. That matches gate
  3a's "100 recorded consults"; a driver bug after consult 100 is caught
  only by the parse's own shape checks.
- Buffer entries are compact `V7Obs` (`v7_obs.compact`: int8 edges, uint8
  refers, v6 lists dropped) — ~15 KB per typical consult, so a 5,000-step
  buffer is ~75 MB; the memory gate is about the per-window activations,
  not the buffer.


## 1d — sweep config (b): script-structure GNN + stability recipe — **FAIL** (Lane A, 2026-09-12 11:10); c and d backlogged

`rl/cardemb/sweep.sh` config b = config a with `--struct script` (the
ability-script channel instead of the hashed tree). Four seeds trained
(~2 h each; held-out recall@1 0.957 / 0.959 / 0.958 / 0.956 against
a's 0.928 / 0.929 / 0.928 / 0.924, the best training metric of any
run), artifact = per-slice Procrustes mean of seeds 0+1, G3 against the
mean of seeds 2+3. Full table in `rl/artifacts/cardemb_sweep/RESULTS.md`.

| gate | threshold | measured (held-out) | result |
|---|---|---|---|
| G1 mv / power / toughness | ≥ 0.9 | 0.993 / 0.996 / 0.993 | pass |
| G1 colours, types | ≥ 0.97 | 1.000, 1.000 | pass |
| G1 keywords (11, f1) | ≥ 0.8 | **min 0.516 (reach)**; a had 0.817 | **FAIL** |
| G1 answer classes (5, f1) | ≥ 0.8 | **min 0.723 (ans_minus_toughness)**; a had 0.725 | **FAIL** |
| G2 Cancel / Counterspell | ≥ 0.85 | 0.982 | pass |
| G2 Spell Snare / Force Spike | Spike ∉ Snare top-10 | **rank 11** (a: 28) | **FAIL** |
| G2 functional reprints | 10/10 | 10/10 | pass |
| G2 swap pairs | ≥ 14/16 within 500, median ≤ 50 | 15/16, **median 52** | **FAIL** |
| G3 artifact(0+1) vs artifact(2+3) top-10 Jaccard | ≥ 0.40, same G2 verdicts | 0.773 but **G2 verdicts differ between halves** | **FAIL** |

Reading: the script channel makes the text↔graph objective easier
(recall@1 up three points) and the embedding more seed-stable (0.773 vs
0.680), but what it stabilises is less of the mechanical detail the
gates ask for — two keyword probes and the Snare/Spike separation are
worse than a, not better. Recall@1 is not a gate and this is the second
run where it moved opposite to the gates (v7 was the first). `card_emb_v8`
(config a) stays the accepted artifact.

**Decision (user, 2026-09-12):** configs c and d (the BCE pos_weight
readout, 2 h + 8 h of GPU) are **backlogged**, not run: `sweep2.sh` was
stopped before it started them so the GPU goes to the v7 4g cuda gates
and Phase 5. The pre-registered prediction for c/d in the config-(a)
row stands untested; if the embedder is revisited, run c first
(`bash rl/cardemb/sweep2.sh c`) and compare against this row and a's.

### 4g (part 2) — correction: the two cuda gates (Lane C, 2026-09-12 03:22 WSL clock; GPU idle after the embedder sweep)

`rl/artifacts/v7/cuda_gates_4g.sh`, log `rl/artifacts/v7/cuda_gates_4g.log`.

| gate | required | measured | result |
|---|---|---|---|
| memory gate | `update_profile.py threads --arch v7 --synth --steps 5000 --device cuda --threads 1`: peak RSS within the 16 GB cgroup | `UPDMEM|rss_max_mb=2044|cuda_peak_mb=11360`; 4,984 buffered steps / 90 episodes, defaults `--tbptt 32 --ep-batch 4` | pass on RSS; **cuda peak is at the card's limit** (11.4 of 12 GB on the RTX 3060) |
| update time (not a gate, recorded) | — | `UPDTHREADS|threads=1|update_s=2899.61|ms_per_step=581.78` — **48 minutes for one 5,000-step update**, slower per step than the 2-layer CPU smoke (472 ms) | the number to fix before Phase 7 |
| consult cost | `consult_cost.py --arch v7 --device cuda` | `CONSULT|entities=18|k=2|tokens=51|wire_bytes=12849|json_ms=0.16|obs_ms=0.20|validate_ms=0.51|fwd1_ms=16.91|fwd8_ms=16.91|fwd8_per_row_ms=2.11|sample_ms=0.83|total_single_ms=18.10|python_share=7%` | recorded; 18 ms per consult single, 2.1 ms per row batched by 8 |

What these numbers cannot support: the 582 ms/step is one configuration
(`tbptt 32`, `ep-batch 4`, threads 1) at a cuda peak that leaves ~0.6 GB
free, which is where the caching allocator starts freeing and
re-allocating every window; it says nothing about the rate at a smaller
window. Pre-registered follow-up, run next: the same profile at
`--tbptt 16 --ep-batch 2 --steps 1000` (`cuda_gates_4g_b.sh`); if
ms/step falls by more than the 2× the smaller window alone explains,
the allocator was the cost and the server defaults move to the knob
that fits; if not, the per-window activation cost of the 6-layer
encoder over ~50 tokens is the cost and the Phase 7 update budget has
to be set from it. Neither outcome changes any 4g gate verdict. The 16.9
ms cuda forward per consult (v6 entattn number in `baseline.md` for
comparison) is the serving cost Phase 5d's throughput protocol measures
end to end.

### 4g (part 2) — the pre-registered window follow-up (Lane C, 2026-09-12 03:42 WSL clock)

`rl/artifacts/v7/cuda_gates_4g_b.sh`, log `cuda_gates_4g_b.log`; 1,000 synthetic steps, real size, cuda, threads 1.

| config | ms/step | update_s | cuda peak MB | RSS MB |
|---|---|---|---|---|
| `--tbptt 16 --ep-batch 2` | **489** | 477 | **2,854** | 1,805 |
| `--tbptt 32 --ep-batch 4` (the defaults) | 589 | 575 | 11,367 | 1,814 |

Reading: the smaller window takes the cuda peak from the card's limit to
a quarter of it and removes 17 % of the step time — less than the 2×
the window alone could explain, so the allocator was not the cost; the
per-window activation cost of the 6-layer encoder is. Two consequences,
both recorded rather than acted on here: (1) the server's `--tbptt` /
`--ep-batch` defaults should move to 16 / 2 — same rate, 8.5 GB of
headroom for the inference batcher and a driver JVM on the same card;
(2) a 5,000-step update costs ~40 minutes at either setting, which is
the number Phase 7's update budget (and any decision on a smaller
encoder for rung 0) has to be set from. Neither changes a 4g verdict;
the memory gate passes at both settings.

## 5a — loopback and refusals (Lanes B + C, 2026-09-12 19:45; driver `v7/lane-b` 9792354, server `v7/lane-d`)

`rl/live_check_5a.sh` (on lane-b): `policy_server.py --arch v7 --frozen`
on cpu with the real `card_emb_v8` and `deck_ctx_v1`, an init checkpoint
from `p10_init_net.py --arch v7`, W0Base eval games from the persistent
v7 driver (port 7911, `-Drl.encoderV=7`, the 3d tracker on the wire).

| gate | required | measured | result |
|---|---|---|---|
| loopback | 100 consults, no refusals | 10 games, **190 consults**, 0 refusals, 0 tracebacks, driver rc 0; avg round trip 22.6 ms (cpu, full net) | pass |
| handshake refuses a v6 driver | reason on both sides | v6 driver (port 7910, `-Drl.encoderV=6`) → driver: `policy server refused the handshake: {"ok":0,...}`, job rc 1; server: `HANDSHAKE MISMATCH: server is --arch v7 but the driver hello carries wire=None ... Run the driver with -Drl.encoderV=7` | pass |
| handshake refuses a wrong `card_emb` | reason on both sides | server started on a checkpoint minted with `--card-emb card_emb_v6` (`p10_init_net.py`; the server also refuses to *start* when `--card-emb` disagrees with the checkpoint's table) → driver rc 1 with the refusal; server: `HANDSHAKE MISMATCH: engine card_emb 'card_emb_v8' vs server 'card_emb_v6'` | pass |

What this cannot support: nothing about play (the init net's encoder
is an identity; every game is a loss by passing, as pre-registered). It
is the plumbing gate for 5b–5e: real dumps for the faithfulness probe,
the end-to-end leak gates, the throughput protocol, and replay.

### 4g (part 2) — where the update time goes (torch profiler, 2026-09-12 06:55 WSL clock)

`rl/artifacts/v7/cuda_profile_4g.sh` (`update_profile.py profile --arch v7 --synth --steps 60 --device cuda --tbptt 16 --ep-batch 2`; a 400-step profile was OOM-killed at rc 137 — the profiler's event store, not the update). Log `cuda_profile_4g.log`.

| measure | value |
|---|---|
| ms/step (54 steps, 1 episode) | 416 |
| kernel launches per step | 9,935 (median launch 2.4 µs) |
| GPU busy | 69 % of the update wall time |
| **`indexing_backward_kernel` (`aten::_index_put_impl_`, `IndexBackward0`)** | **13.23 s of 15.52 s kernel time = 85.3 %** |
| next: `aten::mm` / `addmm` / `bmm` (the linear and attention matmuls) | 4.0 % / 2.3 % / 1.6 % |

The op is one line: `rl/v7_encoder.py` `EdgeAttention.forward`,
`logits + table[edges].permute(...)` — the edge-type attention bias
gathered from an 8 × heads parameter table by a `[B, T, T]` integer
index. Its backward is `index_put_(accumulate=True)` over B·T² indices
per layer (up to ~90k for 300 tokens), implemented in PyTorch by a
sort-and-segment kernel; it runs in all 6 policy-encoder layers and the 4
value-trunk layers on every timestep of every window. The matmuls that
are the network's actual arithmetic are 8 % of GPU time. Fix
(pre-registered, not applied here): compute the bias as a one-hot matmul,
`F.one_hot(edges, n_edge).to(dtype) @ table` (or `F.embedding`), whose
backward is a dense reduction; mathematically identical, so the 4c
exactness gates and `v7_check.py` must stay all-pass, and the expected
effect is the step time falling to the matmul-bound floor (a large
factor, measured after the change, not predicted here).

### 4g (part 2) — correction: the edge-bias gather fixed, and the knob that fits (Lane C, 2026-09-12 08:20 WSL clock)

Change: `rl/v7_encoder.py` `EdgeAttention.forward` computes the edge-type
bias as a one-hot matmul (`F.one_hot(edges, n_edge) @ table`) instead of
`table[edges]`. Mathematically identical (one nonzero term per pair);
`rl/v7_check.py` **15 checks, 0 failures** after the change (the 4c
exactness gates and V6-SAME included). `policy_server.py` defaults move
to `--tbptt 16 --ep-batch 4`. Logs: `cuda_profile_4g_after.log`,
script `cuda_profile_4g_after.sh`.

| profile (cuda, real size, threads 1) | before | after |
|---|---|---|
| 60-step, tbptt 16 / ep-batch 2: GPU kernel time | 15.5 s | **2.55 s** |
| same: top op | index backward 85 % | `aten::mm` (matmuls) |
| same: GPU busy | 69 % | **9.9 %** (now CPU / launch-bound: 9,613 launches per step) |
| same: ms/step, unprofiled warm-up | 406 | 243 |
| 1,000-step, tbptt 16 / ep-batch 2 | 489 ms/step, cuda peak 2.85 GB | — |
| 1,000-step, tbptt 32 / ep-batch 4 (old defaults) | 589 ms/step, 11.4 GB | — |
| **1,000-step, tbptt 16 / ep-batch 4 (new defaults)** | — | **64 ms/step, cuda peak 7.4 GB, RSS 1.8 GB** |
| 1,000-step, tbptt 16 / ep-batch 8 | — | 216 ms/step, cuda peak **15.6 GB** (over the 12 GB card: spilled to host memory over PCIe — not a usable setting) |

Reading: the gather's backward was the 85 %; with it gone the update
is launch-bound at small batches (GPU idle 90 % at one row per
forward), and the batch lever works exactly as far as the card allows:
ep-batch 4 gives **9× the original rate** (582 → 64 ms/step; a
5,000-step update ≈ 5 min instead of 48) inside 7.4 GB, ep-batch 8
exceeds the card and loses most of the gain to spilling. Memory scales
with ep-batch × tbptt × T² attention activations across 10 layers, so
ep-batch 4 / tbptt 16 is the fit on the RTX 3060 at the synthetic
buffer's ~300-token boards; real rung-0 boards (~20 entities) will fit
more. Pre-registered next levers, none applied: fused attention
(`scaled_dot_product_attention` with the bias as the additive mask),
`torch.compile` on the block, encoding a window's timesteps in one batch
with the LSTM run afterwards, and collating a window once on the device
instead of per timestep. What these numbers cannot support: real-data
rates (synthetic buffer, one thread) and any claim about learning.

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

## 3d — opponent knowledge tracker (Lane B, 2026-09-12 17:40; branch `v7/lane-b`)

What landed: `rl/xmage-src/RLKnowledgeWatcher.java`, an engine watcher
(`WatcherScope.GAME`, registered by `EpisodeRunner` before the deal and
lazily by `RLPlayer` as a fallback; copied with the game state by the
engine's reflective watcher copy, so its state is lists and maps of
immutable values and `Copyable` records). It builds, from public events
only: **hand slots** (origin opening / drawn / returned-from-a-public-zone /
tutored-or-other, age, identity-known, seen), the **remaining deck** (the
open decklist minus every card of theirs whose identity is public),
and the **opponent-action history** (cast, activate, attack, block,
declined to block with an untapped creature, passed with mana up on my
turn). WIRE §2g tokens `v7_opp_hand[_name]`, `v7_opp_deck[_name]`,
`v7_opp_actions` / `v7_opp_action_refers`, plus `v7_oe_hand` (the true
hand, `-Drl.oracle` only, WIRE §4) and `v7_ctr.handDrift` /
`oppHandTrunc`. Tools: `rl/wire_check_3d.py`, `rl/wire_trace_3d.py`,
`-Drl.trackerDebug=<file>` (an event-model diagnostic), `rl/drivers_3d.sh`
(port 7912 = v7 + oracle; `rl.oracle` is class-init like `rl.encoderV`),
and on lane-d `rl/v7_leak_real.py` (the 0d leak gate over a real
recording).

**The event model, measured** (`-Drl.trackerDebug`, one W0Base game): the
opening hand is dealt as seven `DREW_CARD` events with **no**
`ZONE_CHANGE`, before any step begins (`getTurnStepType() == null`);
a normal draw fires `DREW_CARD` *and* `ZONE_CHANGE LIBRARY>HAND`; a cast
fires `ZONE_CHANGE HAND>STACK` and then `SPELL_CAST`; a land play fires
`ZONE_CHANGE HAND>BATTLEFIELD`. The tracker takes hand entries from
`DREW_CARD` and `ZONE_CHANGE` (deduplicated by the card handle), hand
exits from `ZONE_CHANGE` only, and public identity from any entry into a
public zone, from `SPELL_CAST`, and from the engine's revealed /
looked-at sets polled on every event. Two earlier readings of this
model (reconcile on the first event; remove the slot on `SPELL_CAST`)
each produced a measurable drift and were corrected from the trace, not
from reasoning.

| gate | required | measured | result |
|---|---|---|---|
| **leak gate** (`rl/probes/leak.py` levels 1–3 on real `-Drl.oracle` recordings, hidden keys `oe` + `v7_oe_hand`, encoder woken) | policy-path parse identical without the hidden keys; logits bit-identical under a hidden-content swap; critic moves | W0Base 136 consults: L1 pass, L2 max Δlogit **0.0**, L3 max Δvalue 0.069; W4Inst spell-first 300 consults: pass / 0.0 / 0.075; B1Fast 169: pass / 0.0 / 0.136 | pass |
| consistency: known ⊆ truth | every known slot name is in the true hand (multiset), every consult | **0 violations** over 1,277 oracle-labelled consults — but 0 known slots too (next row) | pass, vacuous |
| slot count = the opponent's hand size | every consult | 0 violations over 1,413 consults (three oracle decks + one plain W0Base run); `handDrift` **0**, `oppHandTrunc` 0 | pass |
| remaining deck | Σ remaining = library + unknown hand slots; counts ≤ decklist | mean gap **0.00** cards on every recording (from the fraction field; the ÷4 count field saturates at 4, so 20 Plains read as 4 there) | pass |
| action tokens | one-hot, newest first, referents in the token space | 0 violations; types seen: cast, attack, passed-with-mana-up, declined-to-block (W0Base 51 rows); activate and block 0 on these decks and policies | pass |
| v6 arm after 3d | unchanged | `v6_new5` vs the two unpatched-build runs: the tapped-land noise class only (17 / 9 lines, column sums equal) | pass |
| live serving | `policy_server.py --arch v7` accepts the opponent keys | see the live-check line below | — |

Behaviour counters (the record): hand slots by origin over the four
runs — opening 2,528, drawn 1,470, returned 0, other 0; **known fraction
0.000**: the W-series, B1Fast and W4Inst decks have no reveal, no
return-to-hand and no tutor, so the identity-known path (`known`, `seen`,
`v7_opp_hand_name`) and the tutored origin are **not exercised** and the
known ⊆ truth gate is vacuous on this evidence. The path exists and is
covered by construction (identity is written only from a public zone
entry, `SPELL_CAST`, or the engine's revealed / looked-at sets); the
decks that exercise it (a bounce or regrowth effect, a reveal) belong to
5b's coverage run, and if 5b has none, a constructed scenario is owed
before 5b closes. What the leak gate cannot support: it proves the policy
path carries nothing that changes with the true hand; that the tracker
never reads the true hand is construction plus the vacuous consistency
gate, not a measurement, until the known path is exercised.

Live check after 3d (`rl/live_check_3a.sh 10 7781 cpu`, tracker keys on the wire, no oracle): handshake accepted, 10 eval games, driver rc 0, 181 consults answered, 0 refusals — the server parses `v7_opp_*` from a real driver.

## 3e — dump and replay (Lane B, 2026-09-12 19:10; branch `v7/lane-b`)

What landed: `-Drl.wireDump=<file>` in `SocketPolicyClient` — the v7
dump format is **the wire itself**: every hello, consult and end line as
sent and every reply as received, appended byte for byte, opened per
connection from the job flag (no JVM restart; record with concurrency
1). The driver summary (`RL|summary ... fallbacks=`) now carries
`v7RefersFallback`, `v7MetaMissing` and `v7UnknownId` next to
`entityTrunc` / `entityUnknown` (`v7UnknownId` is defined 0: ids are not
emitted, WIRE rule 4; the server's `unresolvedName` is the live count,
0 on every recording so far). `rl/replay_3e.sh` plays the same 20
seeded games twice and compares.

| gate | required | measured | result |
|---|---|---|---|
| dump = wire | the driver-side dump is byte-identical to the echo server's recording of the same run | 5 games (seed 900100), 252 lines each, `cmp` equal — hello, ack, 120 consults, replies, end lines | pass |
| replay over 20 games | byte-equal | 20 games × 2 runs (seed 900100, first-non-pass policy, W0Base): **477 consults each, per-game consult counts equal, 5 of 20 games byte-identical, 384 of 477 consult lines byte-identical**; every differing field is the §3a noise class — `e[*][16]/[20]/[21]` and their v7 mirrors `v7_ent[*][22]/[55]/[56]` (which of several identical opponent Plains is tapped, column sums equal on every line) and `v7_cand_refers[*][0]` on 24 lines (the mana-ability candidate refers to the other identical Plains; column sums equal) | pass within the engine's own noise; **not byte-equal**, and cannot be until the engine's mana-payment choice among identical lands is put on the seeded stream (an engine change, outside Lane B) |
| counters | `entityTrunc`, `unknownId` reported | `entityTrunc` 0, `v7RefersFallback` 0, `v7MetaMissing` 0, `v7UnknownId` 0 on the 5-game dump check | pass |

The pre-registered gate said byte-equal over 20 games. It is not met
literally and the reason is measured, not argued: two runs of the
**unpatched v6 build** differ in the same columns (§3a control row), and
a v6 replay through `rung0_replay.sh` compares the `RLGAME` transcript,
which does not carry which land was tapped. The residual is confined to
tapped-derived columns on opponent lands whose per-line sums agree; every
other byte of 477 consults is equal. If exact replay is wanted, the fix
is `ManaUtil`/auto-payment ordering in the engine, and it would make the
v6 arm reproducible too.

## 5b — faithfulness on real dumps and the coverage run (2026-09-12 14:30; branch `v7/lane-d`)

**How the consults were produced (the decision the 19:50 note asked
for):** the echo policy on the RL seat (`rl/wire_echo_server.py`) against
the heuristic opponent, not a shadow emission from a SearchPlayer seat —
the emitter under test is the one that will serve training, and a shadow
path would be a second emitter with its own faithfulness question. Three
echo policies per deck (`PICK=1` first non-pass, `PICK=99` last candidate =
largest attack subset / block assignment, `PREFER=2,1 BUDGET=300`
spell-first), eight decks (W0Base W1Fly W4Inst W5Trick B1Fast W3Sorc
BenchDimir P8Faeries — the last two carry planeswalkers, tokens, counters,
flash, ninjutsu, counterspells, animated lands, a transforming DFC), on
the oracle JVM (7912, `-Drl.encoderV=7 -Drl.oracle=true`, so 5c reuses the
recordings). `rl/record_5b.sh` (8 games each) + `rl/record_5b_r2.sh` (6
games, fresh seeds): **48 recordings, 13,171 consults, 336 games**. Extras
(`rl/record_5b_extra.sh`, `_dbg.sh`, `_dbg3.sh`): a constructed keyword deck
`rl/KW7Probe.dck` (haste, first strike, double strike, trample, menace,
reach, defender, shroud, protection, prowess, an X spell), `-Drl.noYields=false`
runs, and `WIRE_ECHO_PASS_MAIN1=1` runs (the echo policy passes main 1 so
lands and spells are played in main 2 with combat damage still marked).
The probe set is **56 recordings, 15,866 consults, 385 games**; the
manifest with every seed and md5 is `rl/artifacts/v7/5b_manifest.txt`
(recordings gitignored, regenerable). Every consult validates
(`v7_obs.parse_consult` validates on load); `rl/wire_check_3b.py` over the
48: **0 v6 disagreements, 0 identity failures** (`rl/artifacts/v7/5b_check3b.txt`).

**Instrument** (`rl/v7_faith_real.py`, thresholds fixed in its docstring
and committed at a3e9289 before the first run): per-field linear readout
(`rl/probes/faithfulness.py`) on the L3 token-builder output and on the L4
encoder output with the encoder woken as in `rl/v7_leak_real.py` (att.out
and ffn[-1] at std 0.05, edge-bias rows at std 1.0; at init L4 = L3
exactly). Game-grouped 20 % hold-out; entity readouts per zone (4b has one
MLPSkip per zone, so one linear map across zones is not implied by the
architecture); a field is "not exercised" below 20 minority rows overall
or 10 on the held-out games. Edges: balanced pairs, features
[x_i, x_j, x_i·x_j], L4 only (L3 tokens never see edges). Thresholds:
L3 binary/cat ≥ 0.99, real R² ≥ 0.95; L4 ≥ 0.95 / ≥ 0.90; edges ≥ 0.90;
consult-level ≥ 0.90 / ≥ 0.95. Full tables: `rl/artifacts/v7/5b_faith.md`
(+ `.json`).

| gate | required | measured | result |
|---|---|---|---|
| every field after L3 | ≥ threshold on held-out games | **135 pass, 0 fail, 31 not exercised** (game 24, players 16, entity 62 + identity, candidate 8 + 4 groups, opp hand 8 + identity, opp deck 6 + identity, opp actions 8); every exercised binary and cat field at 1.000, every real ≥ 0.999 | pass |
| every field after L4 | ≥ threshold | **127 pass, 8 FAIL**: `game.n_cand` R² 0.856, `players.exile` 0.728, `players.pool_R` 0.814 (105 rows), `players.pool_C` 0.862 (208), `ent.ctr_p1p1` 0.470 (204), `ent.stack_pos` 0.892 (281), `cand.ATTACK.crack_back` 0.876 (n 119), `cand.BLOCK.blockers_used` 0.832 (n 108); all 8 are reals with a small wire scale (÷32, ÷10, ÷5, ÷4) or few rows; every binary and cat field passes (keyword bits 0.999–1.0, identity 1.0 in every zone, loyalty 0.961, tokens 1.0) | **FAIL on 8 of 135** |
| every edge after L4 | balanced acc ≥ 0.90 | attacking_player 0.999 (4,108 positives), targets 0.989 (361), controls 0.997 (20,074), **can_block 1.000 (1,141)**, stack_above 1.000 (281), refers_to 0.984, referred_by 0.986; blocks / blocked_by / attached_to not exercised (no consult inside combat after blocks; no auras or equipment on any deck) | pass, 3 not exercised |
| known-card set | per-name acc ≥ 0.95 (L4, pooled readout) | 3 names exercised (the ninjutsu-returned cards on BenchDimir / P8Faeries), mean **0.982**; per-token `opp_hand.known` 1.0, `identity` 1.0 at L3 and L4 | pass |
| remaining-deck multiset | per-name count R² ≥ 0.90 (L4, pooled readout) | pooled linear readout mean R² **0.10** over 66 names → FAIL; per token (the multiset *is* the token set) `opp_deck.identity` 1.0 / `count` 1.0 / `fraction` 1.0 / `mv` 1.0 at L3, 1.0 / 0.976 / 0.976 / 0.998 at L4 | **FAIL as pre-registered; pass per token** |
| instant-speed threat count | R² ≥ 0.90 (L4 pooled) | **0.931** (distinct remaining instant-speed cards castable with their open mana now; 5,505 exercised consults) | pass |

What the two FAIL rows can and cannot support. The pooled per-name
count is not linearly readable from linear-skip tokens by construction:
count enters each token additively, so a mean over tokens carries the
identity set and the total count but not their product; that readout
was a bad pre-registration, and the per-token row is the evidence that
the multiset is on the wire and carried — it is recorded as written, not
moved. The eight L4 real fields are the small-magnitude ones; the L4
instrument is a *randomly woken* encoder whose perturbation is of the
order of those fields' scale, so this row cannot separate "the
architecture loses them" from "the wake noise buries them". A diagnostic
at wake std 0.02 is appended below; the pre-registered follow-up is the
same probe on the 7a checkpoint after training (if a field is still
below threshold on a trained net, that is an architecture finding).

**Coverage census** (`rl/artifacts/v7/5b_check3b.txt`, 166k entity rows;
3b's zero-row fields, in order). Exercised now: loyalty 518 · +1/+1
counters 698 · −1/−1 161 · loyalty counters 518 · other counters 71 ·
tokens 3,741 · other-permanent type 12,368 · deathtouch 3,856 · lifelink
3,248 · hexproof 66 · ninjutsu 4,466 · stack modes 1,609 / controller
1,590 / is-ability 458; the **granted-ability path** (v7 reads live
abilities, v6 the printed table): Soulstone Sanctuary vigilance 489 rows,
Restless Reef deathtouch 192, Cecil transformed deathtouch 207 / lifelink
649, Kaito hexproof 66, and The Wondrous Wasp flying 32 rows where the
printed table has no flying (the table is wrong, the engine is right —
see finding 2). The constructed deck adds haste 416 · first strike 394 ·
double strike 509 · trample 1,262 · menace 685 · reach 1,024 · defender
655 · shroud 384 · protection 1,025 · prowess 416, each recovered at
1.000 after L3 and ≥ 0.999 after L4. **Still not exercised**, with the
reason: ward (no ward card in the deck; the same `V7_KW` class loop as the
other 17 bits); damage marked (5 rows, all v6-agreeing: a consult only
sees marked damage in main 2 of the RL seat's own turn on its surviving
attackers, and the heuristic blocks 9 % of the time); blocking (21 rows,
v6-agreeing); **lethal-as-is is 0 at every consult by construction**
(state-based actions run before priority, so a creature with lethal
damage is never on the battlefield when the policy is asked — a WIRE §2d
amendment: drop or redefine idx 57); stack X and the candidate's X-chosen
slot (Stonecoil Serpent was cast, 181 battlefield rows with X > 0, but no
consult happens while an X spell of the RL seat is on the stack, and the
candidate row is built before X is chosen — the slot cannot be filled by
the generator as it stands); player idx 14 cards-drawn-this-turn (open
item, still 0); poison; face-down; exile / library-known / command zones;
opp-hand origin "tutored/other"; opp-action "other"; candidate type
OTHER; TARGET life-if-player; ATTACK lethal (27 rows, under the held-out
minimum); BLOCK defender-dies.

**Findings, in the open.**
1. **Tracker: phantom known slot on a transforming double-faced card.**
   `rl/wire_check_3d.py` over the 48: `handDrift` max 9 and 22
   known-not-in-truth consults on two recordings (5b_BenchDimir_p1, _p99);
   the returned-to-hand origin (403 slots, all known) is exercised for the
   first time, so the 3d "known ⊆ truth" gate is no longer vacuous — and it
   failed. Traced with the id diagnostic added to `-Drl.trackerDebug`
   (`rl/artifacts/v7/wire3a/5bx_td_p99.log`): Cecil, Dark Knight returned by
   Kaito's ninjutsu as `BATTLEFIELD>HAND tid=43a68e5c`, cast again as
   `HAND>STACK tid=f6a8b9b8` — the permanent's id is not the card's id for
   a DFC, so the slot was never matched, `reconcile()` evicted a real
   unknown slot instead, and the known Cecil slot outlived the card by
   seven turns. Fix: slots keyed by `Card.getMainCard().getId()`
   (`RLKnowledgeWatcher.mainId`, on zone changes and draws). Pre-registered:
   changes only `v7_opp_hand*` on games with a returned DFC; the v6 arm and
   every other v7 field are untouched. Re-check after the fix: see the
   line appended below.
2. **31 BLOCK candidates are engine-illegal pairs** (`5b_check3c.txt`: a
   flying attacker — The Wondrous Wasp, Pestermite, Faerie Vandal — assigned
   to a ground blocker). The `can_block` edge is right (engine legality);
   `RLPlayer.jointBlocks` enumerates `assign[b]` over every attacker with no
   `canBlock` filter (the pairwise `block1` site filters) and the
   declaration loop silently skips the illegal pair, so the policy can
   "choose" a block that does not happen. 3c saw 0 because its decks had no
   flyer facing a ground blocker in a joint consult. Not fixed here: it
   changes the v6 arm's candidate set, so it is its own commit with its own
   v6-identity row (pre-registered: no v7 field changes; only consults
   with an illegal joint assignment lose candidates).
3. **XMage's own AI throws on the keyword deck** (`AI can't find good
   blocker combination`, the heuristic opponent choosing blocks against
   menace / trample attackers): the KW7Probe jobs ended with rc 1 after
   2, 4 and 0 complete games. An opponent-side engine limitation to keep in
   mind for the 7b deck.
4. `-Drl.noYields=true` (the recording default) is the *every-window*
   setting; `false` enables the hand-crafted yields. The driver server
   refuses a job whose value differs from the JVM's pinned one — as it
   should.

**Tracker re-check after the fix** (`rl/record_5b_fix.sh`: compile,
restart 7912, re-record 5b_BenchDimir_p1 / _p99 under their original
seeds, `rl/wire_check_3d.py` per file and pooled →
`rl/artifacts/v7/5b_check3d_fixed.txt`): over **17,918 oracle-labelled
consults** (48 + the extras), `handDrift` max **0** on every file,
`oppHandTrunc` 0, **517 returned slots, all identity-known, 0
known-not-in-truth** — the 3d consistency gate "known ⊆ truth" is now
measured, not vacuous; slot count = hand size on every consult; deck
accounting mean |gap| 0.09 (the ÷4 count saturation). Known fraction
0.009 overall: the only known-identity path these decks exercise is
return-to-hand; reveal and tutor origins remain unexercised (origin
"tutored/other" 0 rows).

**5b verdict.** L3 carries every exercised field exactly; L4 (random
wake) carries every binary and cat field and every edge, and loses
precision on eight small-scale reals at the pre-registered bar — a FAIL
row, with the trained-checkpoint follow-up pre-registered; the
consult-level pooled deck-count readout FAILs by construction while the
per-token multiset passes. Coverage: 10 keywords, loyalty, counters,
tokens, the granted-ability path and the tracker's known path are
exercised for the first time; lethal-as-is is dead by construction; ward,
damage marked, blocking, stack X remain unexercised with the reasons
above. One emitter defect found and fixed (tracker DFC handle), one
candidate-generator defect found and deferred (illegal joint blocks).
Nothing here blocks 5c–5e; 5c reuses these recordings.

**L4 instrument diagnostic (not a gate; the bar above stays where it
was).** The same probe with the wake at std 0.02 instead of 0.05
(`--wake 0.02`, `rl/artifacts/v7/5b_faith_wake002.md`): L4 **134 pass,
1 FAIL** (`game.n_cand` R² 0.889, still under 0.90); the other seven
reals recover above threshold. So seven of the eight L4 failures scale
with the size of the random perturbation, which is what "the wake noise
buries a small-scale field" predicts and what "the block structure loses
it" does not; `n_cand` (÷32, mostly 1–5 candidates) is the one field
under the bar at both settings. The trained-checkpoint probe at 7a is the
measurement that settles it.

## 5c — leak gates end to end on the 5b recordings (2026-09-12 21:15; branch `v7/lane-d`)

Plan §2 row 5c: "leak gates end to end: oracle, tracker, belief — all
three pass". All three are run or cited on the 5b recordings (oracle JVM
7912, `-Drl.encoderV=7 -Drl.oracle=true`, `rl/artifacts/v7/5b_manifest.txt`):
every file matching `5b*.jsonl` — **63 recordings** = the 48 of rounds
1–2 (13,171 consults) + the 15 extras (KW7Probe, `noYields=false`,
main-1-pass, and three `trackerDebug` re-recordings of 5b_BenchDimir_p99
under its own seed, which duplicate its games — see the confound line
under the belief gate). Pre-registration commit 097bc4a (both scripts,
thresholds in the docstrings) precedes the first run.

**Oracle** — `rl/run_5c_leak.sh` → `rl/v7_leak_real.py` per recording,
every consult (`--limit 2000`), `rl/probes/leak.py` levels 1–3 with the
hidden keys `oe` + `v7_oe_hand`, encoder woken (att.out / ffn[-1] std
0.05), 2 layers; one line per recording in `rl/artifacts/v7/5c_leak.txt`.
3d measured this instrument on one W0Base recording of 136 consults; 5c
is the same instrument over every oracle-labelled consult of every 5b
recording (8 decks + KW7Probe, 3 echo policies, the extras).

| gate | required | measured | result |
|---|---|---|---|
| level 1: policy-path parse identical with and without the hidden keys | every consult | **63 recordings, 19,379 consults, first_bad none** on every recording | pass |
| level 2: policy logits bit-identical under a hidden-content swap (tol 1e-6) | every consult, woken net | max Δlogit **0.0** on every recording (19,379 consults) | pass |
| level 3: the critic moves under the same swap (min 1e-4) | every recording | moved on every recording; smallest per-recording max movement 0.059 | pass |

**Tracker** — the gate is 3d's "known ⊆ truth" (every known slot's name
is in the true hand, multiset), which was **vacuous at 3d** (0 known
slots over 1,277 consults) and is **measured at 5b** after the DFC fix
(`rl/artifacts/v7/5b_check3d_fixed.txt`): 17,918 oracle-labelled
consults, `handDrift` max 0 on every file, `oppHandTrunc` 0, 517 returned
slots all identity-known, **0 known-not-in-truth**; slot count = hand size
on every consult. No new run here: 5c cites that measurement as the
tracker gate — pass. What it cannot support: the only known-identity path
exercised is return-to-hand; reveal and tutor origins are 0 rows. Two
pre-fix recordings are in the 5c set (5bx_BenchDimir_m2 and the dbg
extras record before the fix): the belief label census below finds the
phantom-slot defect on 5bx_BenchDimir_m2 — 3 consults with Cecil, Dark
Knight in the true hand, no known slot, and not among the remaining
tokens — the §5b finding-1 signature, on a recording made before the
fix, not a new defect.

**Belief** — `rl/v7_belief_real.py` (`rl/artifacts/v7/5c_belief.txt` +
`.json`): 4f's four gates on real consults with labels from `v7_oe_hand`.
19,379 oracle-labelled consults, 441 games, game-grouped 20 % hold-out
(15,281 / 4,098 consults), 60,285 true cards; BeliefModule d 256, 2
layers, Adam 3e-4, 1,500 steps of 64 on cuda, random card table (as the
oracle gate), untrained builders. Labels: slot target = the remaining-deck
token of the true card in that slot (known slots first, the rest in
deck-token order — one of the equivalent permutations); P(in hand) target
per remaining token; next-draw target −1 everywhere (the next draw is not
on the wire, so that loss term is identically 0 here).

| gate | required (fixed at 097bc4a) | measured | result |
|---|---|---|---|
| B1 leak with belief ON | logits bit-identical (tol 1e-6) under the `oe` / `v7_oe_hand` swap with the belief features attached, ≥ 200 real consults | **2,520 consults** (40 per recording), max Δlogit **0.0**, 2,248 non-degenerate logit rows | pass |
| B2 stop-gradient on real inputs | every builder grad None/0, some belief grad ≠ 0 after `loss.backward()` on a real minibatch | builders 0, belief non-zero | pass |
| B3 held-out slot log-lik of the true hand vs uniform-over-remaining | margin ≥ 0.3 nats | **−2.350 vs −2.589: +0.239** (11,876 held-out slots; train −2.221); vs the multiset prior −2.556: **+0.206** | **FAIL as pre-registered** |
| B4 known slots: pointer mass on the true token | ≥ 0.95 | 153 held-out known slots, mean mass **0.082** (uniform over ~13 tokens ≈ 0.077) | **FAIL — and ill-posed, below** |
| reported, not gated: P(in hand) | — | held-out BCE 0.341 vs base-rate BCE 0.441 (base rate 0.161), rank AUC **0.828** | — |

What the two FAIL rows can and cannot support.

*B3.* The module learns a real signal on real inputs: it beats uniform
and the multiset prior on the held-out games, and P(in hand) has AUC 0.83
against 0.5 — the mechanism (legal tokens in, its own loss, features
out) works on the wire as recorded. The 0.3-nat bar was borrowed from 4f,
where the planted rule is deterministic and the attainable margin is
unbounded; on real hands the attainable margin is bounded by how
predictable the hidden hand is from the public state, which nobody
measured before fixing the bar. It is recorded as a FAIL against the bar
as written, not moved. Phase 6 sets its bar from a baseline measured on
the same data (the multiset prior, and a count-only model), not from
uniform. Confound, in the module's favour: the three `trackerDebug`
re-recordings duplicate 5b_BenchDimir_p99's games (≈ 1,450 of 19,379
consults), and a duplicated game can sit in train and in the hold-out —
that can only inflate the held-out margin, so it cannot rescue the FAIL;
the run on the 48 non-duplicate recordings is appended below.
Training was not converged at 1,500 steps (loss still falling); the
longer-training diagnostic is appended below, labelled a diagnostic.

*B4.* The pre-registration assumed a known slot's card is among the
remaining-deck tokens. It is not, by the WIRE §2f definition: remaining =
decklist minus every card seen, and a returned-to-hand card has been
seen. The label census shows it: 167 true cards have no remaining token,
**164 of them the returned known cards** (Cecil, Dark Knight 118, Elektra,
Daughter of the Hand 49); the 153 held-out known slots that did get a
target got it only because another copy of the same name was still in
the library — the pointer was asked "which remaining copy is this card",
a question with no right answer, and it answers at chance. So B4 as
written is not a measurement of the module; the identity of a known slot
is on its own token (5b: `opp_hand.identity` 1.0 at L3 and L4) and needs
no belief. Design consequence for Phase 6, recorded here so it is not
lost: the pointer loss must exclude known slots (mask `slot_target` to −1
when `identity known` = 1), and the attach for a known slot should carry
its identity, not a pointer expectation. Not changed in `v7_belief.py`
in this row (it is a Phase 6 change with its own gate).

**5c verdict.** Oracle: pass on every consult of every recording. Tracker: pass, as measured
at 5b (cited, not re-run). Belief: the two mechanism gates pass on real
inputs (no leak with the features on, no gradient into the builders);
the two predictive gates FAIL as pre-registered — B3 by 0.06 nats against
a bar not calibrated to real data, B4 by construction of the label. Plan
row 5c said "all three pass"; the belief gate does not, and the row stays
open on that until Phase 6 measures it properly. The recordings, both
scripts and the JSON reports are on disk; recordings gitignored
(regenerate from the manifest).

**B3 on the 48 non-duplicate recordings** (`rl/run_5c_belief_clean.sh`,
rounds 1–2 only, same seed and steps; `rl/artifacts/v7/5c_belief_clean.txt`):
13,118 oracle-labelled consults, 336 games, 8,846 held-out slots —
held-out log-lik **−2.373 vs uniform −2.542: +0.169** (paired SE 0.011),
vs the multiset prior −2.508: **+0.135** (SE 0.010); train −2.127; P(in
hand) BCE 0.362 vs 0.459, AUC 0.847; B4 139 known slots, mass 0.070;
B1 240 consults, Δlogit 0.0. So the duplicated games did inflate the gate
run's margin (0.239 → 0.169) — the FAIL against 0.3 stands on either
set, the signal over uniform and over the multiset prior is 12–15
standard errors on either set, and the train / held-out gap (0.25 nats)
says the 2-layer module on a random card table is overfitting games
rather than short of capacity. All 52 unmatched true cards on this set
are the returned known cards (none from the phantom-slot defect: the
pre-fix recording is not in it).

**Longer-training diagnostic** (`rl/run_5c_belief_diag.sh`: 6,000 steps,
seed 1, the 63-file set; `rl/artifacts/v7/5c_belief_diag.txt` — a
diagnostic, the bar is unchanged): held-out log-lik **−3.149 vs uniform
−2.501: −0.65 nats, worse than uniform** (SE 0.030), train −1.466; P(in
hand) AUC 0.835 (unchanged); 78 held-out known slots at mass 0.53 (the
pointer memorised name-matching on train, which is the wrong target for
a known slot, see B4). So the 1,500-step result was not
training-limited: four times the steps takes the module from +0.24 to
−0.65 against uniform. The held-out signal in real hidden hands (from a
random card table and the public tokens) is small, and the 2-layer
module memorises games past it. What this fixes for Phase 6: the belief
loss needs early stopping on held-out games (or dropout / weight decay,
both 0 now) and a bar set from the multiset prior, not from uniform; the
gate row for Phase 6 pre-registers those before it runs.

**Oracle gate, closed** (`rl/artifacts/v7/5c_leak.txt`, 63 lines): every
recording passes all three levels; the run was cut once by a session end
and resumed (the runner skips recordings already gated), so the file has
two start stamps. What it cannot support: it proves the policy path
carries nothing that changes with the true hand or the critic rows; that
the tracker itself does not read the truth is the "known ⊆ truth" gate
above plus construction (3d).

**Gameplay sample** for the record, from the same recordings
(`rl/artifacts/v7/5b_gameplay_sample.md`): the echo policies' pooled win
rates against the heuristic (p1 8/112, p99 6/112, sf 3/112, Wilson
intervals in the file) and one attack consult (5b_P8Faeries_p1, game 6,
turn 32) where CombatMath marks two of 17 attack subsets lethal and the
first-non-pass policy sends a single 1/1, winning on turn 48 instead.

## 5d — throughput, v7 vs v6 on cuda, end to end (pre-registration 2026-09-12 22:05; branch `v7/lane-d`)

**Protocol** = `rl/THROUGHPUT-LOCAL.md` §2 unchanged: `rung0_lane.sh
B0Base B0Twin 256 0`, conc4, `R0_EVERY=256 R0_CHUNK=64 R0_EVAL_G=4
R0_CP7_G=0`, `R0_SRVEXTRA="--device cuda"`, `UPDATE_EPISODES=32` → 8
`train.csv` rows; eps/s over rows 1→8 (224 episodes, after the JIT
warm-up); update seconds = col 9; memory sampled every 5 s; one run per
arm, seed 0, fresh driver JVM per arm. Two arms, run back to back on
the same day (`rl/run_5d.sh`): **v6** = `R0_ENCODER_V=6` (entattn, the
§7 conc4-cuda reference arm, rerun so the comparison is same-day), **v7**
= `R0_ENCODER_V=7` (new lane branch: `--arch v7`, no v6 flags, server
defaults tbptt 16 / ep-batch 4, belief module on, card_emb_v8, deck
context). The v7 driver emits the full wire (12.8 KB per consult at 18
entities, `consult_cost.py`) on top of the v6 rows the critic still
receives.

**Component numbers known before the run** (`rl/consult_cost.py --arch
v7 --device cuda`, GPU idle, 51 tokens): fwd1 **14.8 ms**, fwd8 15.8 ms
= 1.97 ms/row (flat in B, so the T4 batcher that was flat for v6 should
pay for v7), parse 0.19, validate 0.49, json 0.15, sample 0.78, total
single 15.9 ms, Python share 7 %. v6 on the same lane held 5.16 ms per
consult (§7). Prediction: v7 play ≈ 1/3 of v6's consults/s unbatched.
§4g: update 64 ms per optimiser step at tbptt 16 / ep-batch 4 on
synthetic windows, cuda peak 7.4 GB.

**Budget, fixed before the run** (plan §2 row 5d: "consults/s within a
pre-set budget of v6"):

| quantity | v6 arm (same day) | v7 must be | why |
|---|---|---|---|
| play consults/s (stored consults ÷ (window − update s)) | measured | **≥ 1/3 of v6** | the per-consult forward predicts exactly 1/3; below it something other than the forward is the cost |
| update ms per stored consult | measured | **≤ 3× v6** | the §4g rate at the fitted knob |
| cuda peak (nvidia-smi) / host peak used | measured | **≤ 11 GB / ≤ 12 GB** | the 12 GB card, the 16 GB machine |
| lane integrity | `R0_DONE`, `ck_eps=256`, no `R0_FAILED`, no server restart mid-run | same | a run that died is not a rate |
| eps/s | measured | reported, **not gated** (n = 1 noise is 1.8×, §11.4 item 5; untrained v6 and v7 nets play different-length episodes) | |

Pre-registered: this row cannot say anything about learning (both nets
are untrained; §3.2 — sampled trajectories, not a replay); eps/s
differences under 2× do not rank the arms; `consults_per_ep` and
`turns_per_ep` are reported so that an eps/s gap can be split into
per-consult cost and episode length. If v7 is over budget, the
pre-registered levers in order: the batcher (`--batch-max 4`, built and
gated in §11 and flat for v6 because v6's forward was cheap), then the
§4g correction-row levers (SDPA with the bias as additive mask,
torch.compile on the block, window-batched encoding, device-side
collation). Results appended below.

**5d results** (2026-09-12 21:32; `rl/run_5d.sh`, artifacts in
`rl/artifacts/v7/5d/{v6,v7}/`, quantities by `rl/tp_5d.py`). Both arms
`R0_DONE`, `ck_eps=256`, no `R0_FAILED`, 8 rows each, 0 server errors or
refusals; window = rows 1→8, 224 episodes.

| quantity | v6 (same day) | v7 | ratio | budget | result |
|---|---|---|---|---|---|
| play consults/s | 182.5 | **50.7** | 0.28 | ≥ 1/3 (60.8) | **FAIL** (just under) |
| update ms per stored consult | 10.82 | **58.8** | 5.4× | ≤ 3× (32.5) | **FAIL** |
| update s mean (max) | 33.3 (51.8) | 62.3 (129.8, the first update) | | | |
| update share of window | 66 % | 75 % | | | |
| held per consult (last server's `RLLOCK`) | 3.78 ms | 17.8 ms | 4.7× | | |
| eps/s | 0.609 | 0.455 | 0.75 | reported | |
| consults per episode | 100.8 | **28.0** | 0.28 | reported | see below |
| stored consults, rows 2–8 | 22,573 | 6,267 | | | |
| cuda peak / host peak used / JVM / server MB | 3,699 / 3,942 / 2,143 / 2,267 | **2,337** / 4,885 / 1,743 / 3,306 | | ≤ 11 GB / ≤ 12 GB | pass |

The v6 arm reproduces §7 per consult (10.5 → 10.8 ms update, 190 → 182
consults/s play); its eps/s is 0.61 not 1.12 because these games ran
101 consults per episode against §7's 57 — the reason the budget is on
per-consult quantities.

**Verdict: 5d FAIL on both per-consult budgets.** The per-consult forward
predicted the play ratio (1/3 predicted, 0.28 measured — the remainder
is the held time: 17.8 ms per consult against a 15.9 ms single forward,
so play is serialized forward, as v6's was). The update is 5.4× v6 per
stored consult, above the 3× the §4g synthetic rate implied: at 64 ms
per optimiser step over 64 window-consults the update should cost ~1 ms
per consult per epoch; 58.8 ms per stored consult says the lane's
update does far more work per consult than the synthetic profile — the
PPO epoch count, the window padding on short real episodes (28 consults
per episode against tbptt 16 / ep-batch 4), or the 3 %-of-consults
first-update warm-up (130 s) being repeated per server start. Not
diagnosed here; it is the first thing 5d's follow-up profiles
(`update_profile.py --arch v7` on the recorded lane windows, not
synthetic ones). Memory is a non-issue (2.3 GB cuda peak, 4× under the
card), which means the batcher and a larger ep-batch are both open.

What eps/s cannot support: v7's 0.455 against 0.609 is 0.75, inside the
1.8× n = 1 noise, and the two nets play different games — **the
untrained v7 net's episodes hold 28 consults against v6's 101**, and its
4-game eval batteries at 0 and at 256 episodes show `attacks=0/0
blocks=0/0` (no attack or block opportunity in 8 games: no creature of
the RL seat ever on the battlefield; turns 13.5 / 12.0 = it dies on
schedule). That is an observation from 8 games, not a result; it says
the v7 init policy's argmax is PASS-like on real consults, and the
consult mix v7 was timed on (empty boards, few candidates) is *cheaper*
than v6's, so the per-consult ratios above are lower bounds on v7's
cost, not upper. Pre-registered for 7a: log policy entropy and the
candidate-type histogram of the chosen actions per update; check the
init net's logit distribution over candidate types on the 5b consults
before training (a PASS bias at init is a heads-init finding, not a
learning one).

Pre-registered levers, in order, none run here: (1) `--batch-max 4`
(§11: built, gated, flat for v6; v7's forward is flat in B — fwd8 = 1.97
ms/row against fwd1 14.8 — so at conc4 it should take play from ~50
toward ~150 consults/s); (2) profile the lane update on real windows
and fix the per-consult excess; (3) the §4g correction-row levers. 5d
is recorded as FAIL; the plan's gate for `v7-p5` is not met on
throughput, and the tag waits on (1)–(2) or a stated decision to train
at this rate (256 episodes cost 12 min end to end; a 2k-episode rung is
~1.6 h — affordable for 7a as a smoke).

**Checkpoint census on real consults** (`rl/v7_init_logits.py`, 1,238
consults from four 5b recordings, memoryless scoring, cuda) — the
pre-registered check above, done the same evening:

| checkpoint | argmax = PASS when a non-PASS candidate exists | mean P(PASS) | mean entropy (nats) | mean top-1 − top-2 logit gap | argmax by type (chosen / consults offering it) |
|---|---|---|---|---|---|
| `init.pt` (0 episodes) | **1,033 / 1,108** | 0.534 | 0.902 | 0.39 | PASS 1163/1176 · LAND 0/177 · SPELL 13/191 · ACTIVATE 0/781 · TARGET 62/62 · ATTACK 0/47 · BLOCK 0/27 |
| `ck_256.pt` (256 episodes, lr 3e-4) | **0 / 1,108** | 0.105 | 0.352 | **98.4** | PASS 130/1176 · LAND 177/177 · SPELL 14/191 · ACTIVATE 781/781 · TARGET 62/62 · ATTACK 47/47 · BLOCK 27/27 |

So the init net is PASS-biased by construction (PASS wins the argmax on
93 % of consults that offer anything else, with a soft 0.39-nat gap —
that is the 28-consult episodes and the empty boards in the 5d v7 arm),
and 256 episodes of PPO took it to the opposite corner: never pass,
always the first LAND / ACTIVATE / ATTACK / BLOCK on offer, with a 98-nat
logit gap and entropy 0.35 — a collapse, not a curve. `ACTIVATE 781/781`
is the tell: the untrained agent activates every mana ability offered,
which is how a game burns its consult budget without a creature ever
attacking (the 256-episode battery: `attacks=0/0`). Both are 7a's
findings to act on, recorded here because they came out of the 5d run:
(a) the PASS bias at init is a heads-init property (the PASS candidate
row is all zeros after its type one-hot, WIRE §2f, so it scores the
candidate MLP's bias alone), to be measured on the init net before 7a's
first update and either accepted as the starting point or removed by
centring the candidate scorer; (b) a 98-nat gap after 8 updates at lr
3e-4 with 4 PPO epochs on a 17 M-parameter net says the logit scale is
unbounded and the clip is not holding it — 7a pre-registers per-update
entropy, max |logit|, grad norm and the chosen-type histogram, and a
learning-rate / logit-scale decision before any 2k-episode run.
