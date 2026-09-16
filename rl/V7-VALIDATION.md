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

## 5e — replay end to end on the merged build (2026-09-12 22:20; branch `v7/lane-d`)

`rl/replay_3e.sh 20` on the one-lane build (driver 7911 restarted by
`rl/drivers_3a.sh` after the 5d lane; W0Base, first-non-pass echo policy,
seed 900100, 20 games × 2 runs; recordings `replay_A/B.jsonl` +
`replay_A.dump.jsonl`, gitignored).

| gate | required | measured | result |
|---|---|---|---|
| dump = wire | driver-side dump byte-identical to the echo recording | `IDENTICAL` (996 lines, 477 consults) | pass |
| replay over 20 games | byte-equal | 477 consults per run, per-game consult counts equal; **102 of 996 lines differ**; every differing entity row is a **land** (212 rows, 0 non-land), in columns 22 tapped · 55 can-attack · 56 can-block only; the v6 `e` rows differ on the same lines (95) and `v7_cand_refers` on 9 (the order of referenced lands) | **not byte-equal; the 3a/3e residual class, no new class** |

**Correction to §3e, in the open.** §3e wrote that the residual is confined
to tapped-derived columns "whose per-line sums agree". Measured here: the
tapped and can-block column sums agree on every differing line, but the
can-attack sum over land rows **differs on 61 of the 102 lines** (`wire_diff
--all`: `.v7_ent[*][55] column-sum DIFFERS 61`). The rows are still only
lands and the columns still only the three tapped-derived ones, so the
class is the same (which of several identical lands the engine's
auto-payment taps is not seeded); why can-attack on a land follows the
choice while can-block does not is not explained here (a land that
entered this turn versus one that did not is the candidate, unverified).
The statement to carry: **the residual is the engine's mana-payment
order among identical lands, visible only in three tapped-derived columns
of land rows; no creature, stack, hand, candidate-feature or opponent-token
byte differs across 477 consults.** If exact replay is wanted the fix is
in the engine's `ManaUtil` ordering, as §3e said.

## Phase 5 verdict and the tag (2026-09-12 22:25)

| row | result |
|---|---|
| 5a loopback and refusals | pass |
| 5b faithfulness on real dumps | L3 pass; L4 8 small-scale reals FAIL at the random wake (instrument-limited; 7a checkpoint probe pre-registered) |
| 5c leak gates | oracle pass (19,379 consults); tracker pass; belief B1/B2 pass, **B3/B4 FAIL** as pre-registered |
| 5d throughput | **FAIL** both per-consult budgets (play 0.28× v6, update 5.4× v6); memory fine |
| 5e replay | dump = wire pass; replay not byte-equal, the 3a residual class only |

The plan's `v7-p5` tag marks "every gate passed". Three rows carry a
FAIL, so **the tag is withheld**; what is true is that every piece is
exercised end to end on real games and the failures are measured and
bounded. Whether to run 7a (256 episodes, ~12 min at 5d's rate) before
the throughput levers is a decision for the next session, taken in the
open: the 5d follow-up (batcher, real-window update profile) and the 7a
smoke do not block each other, and 7a's pre-registration now includes
the init PASS bias and the logit-collapse census above.

## 7a pre-registration — is the 5d collapse structural or the learning rate? (2026-09-12 22:50)

`rl/v7_logit_velocity.py`: from `init.pt`, on a fixed batch of 64 real
consults (W0Base, B1Fast; each with ≥ 2 candidates), on-policy Adam steps
over `policy_parameters()` on the loss the 5d run produced (advantage −1
on every sampled action, the first-epoch PPO gradient), three learning
rates from the same init. Mean top-1 − top-2 logit gap in nats (`max |logit|`
in brackets) after k steps:

| lr | step 0 | 1 | 2 | 4 | 8 | entropy at 8 | grad norm at 8 |
|---|---|---|---|---|---|---|---|
| 3e-5 | 0.50 (0.7) | 3.4 (2.9) | 3.9 | 5.2 | **5.0** (4.4) | 0.31 | 5.3 |
| 1e-4 | 0.50 | 9.0 (7.8) | 16.6 | 27.6 | **41.9** (38.1) | 0.01 | 0.14 |
| 3e-4 | 0.50 | **20.5** (18.2) | 12.8 | 77.1 | **165** (157) | 0.00 | 0.02 |

Reading, against the pre-registered one in the script's docstring:

1. **The velocity is Adam step-size × parameter count on an unbounded
   scorer.** One step at 3e-4 moves the gap by 20 nats; at 1e-4 by 9; at
   3e-5 by 3.4 — monotone in lr, sub-linear (6 : 2.6 : 1 for 10 : 3.3 : 1).
   The init gradient norm is 9.2; after the softmax saturates it falls to
   0.02–0.14 and stays there: the collapse is a **one-way door** — once
   the gap is tens of nats the gradient (and PPO's clip, whose ratio is 1
   on a deterministic policy) can no longer pull it back, and the 0.01
   entropy bonus is far too small. That is the 5d `ck_256` state (gap 98).
2. **A lane update is ~113 Adam steps** (1,808 stored consults ÷ 64
   window-consults per step × 4 epochs), so even 3e-5's 3–5 nats per
   step is not safe by itself; its plateau at ~5 nats over 8 steps
   (entropy 0.31, gradient alive) is the one encouraging number, and it
   is 8 steps, not 113.
3. So "only LR" is **not shown**, and the structural half is measured:
   the candidate scorer's logits are unbounded and the 15.6 M-parameter
   Adam step moves them by nats per step at any lr a v6 lane used (v6:
   0.7 M policy parameters, trained at 3e-4 without this). lr reduces the
   velocity roughly in proportion; nothing in the current heads bounds
   the destination.

Pre-registered 7a arms (256 episodes each, W0Base vs heuristic, cuda; a
census with `rl/v7_init_logits.py` on `ck_256` and per-update entropy /
max |logit| / grad norm / chosen-type histogram on the TRAIN line, added
before the first arm runs):

| arm | change | predicted |
|---|---|---|
| A0 | lr 3e-4 (5d as run) | collapse by update 1–2 (gap > 20) — the control |
| A1 | lr 3e-5, 1 PPO epoch | gap grows but stays < 20 over 8 updates; may still drift |
| A2 | lr 3e-5 + bounded logits (scorer output scaled to a fixed range, e.g. `tanh` × 5 or a LayerNorm before the scorer, chosen and gated so the init gap is unchanged and `v7_check.py` passes) | gap < 5 at 256, entropy > 0.3, P(PASS) between 0.05 and 0.9 |

"Not collapsed" is defined now as: gap at `ck_256` < 5 nats, mean
entropy > 0.3 nats, argmax-PASS fraction on the census between 5 % and
90 %. If A1 passes that, lr suffices in practice for this budget and A2
is a robustness change; if only A2 passes, the collapse is structural
and the bound is part of the architecture. If neither passes, the PASS
constant-row design (WIRE §2f) is the next suspect and gets its own arm.
None of this is a learning result; all three arms are pre-registered as
unable to beat v6 on rung 0.

## 7a — rung-0 smoke, three pre-registered arms (2026-09-12 23:20; branch `v7/lane-d`)

`rl/run_7a.sh`: W0Base vs heuristic, 256 episodes each, conc4, cuda,
`--arch v7`, seed 0; per-update instrumentation on the TRAIN line
(entropy · max |logit| · pre-clip grad norm · chosen-type counts, commit
e70d3aa); census `rl/v7_init_logits.py` on `ck_256` over 1,238 real
consults; artifacts `rl/artifacts/v7/7a/{A0,A1,A2}/` (train_lines.txt,
census.txt, lane.log, ck_256.pt). Chosen types are PASS/LAND/SPELL/
ACTIVATE/TARGET/ATTACK/BLOCK per 32-episode batch.

| arm | setting | update 1 → 8: entropy | max \|logit\| | grad norm (pre-clip) | chosen types at update 8 | training wins / 256 | census at 256: gap, argmax-PASS, entropy | verdict vs the pre-registered "not collapsed" |
|---|---|---|---|---|---|---|---|---|
| A0 | lr 3e-4, 4 epochs (5d as run) | 0.10 → 0.14 | 177 → 348 | 39 → 0.17 | 812/588/**0**/1960/120/**0**/**0** | 1 | **212 nats**, 41/1108, 0.37 | collapsed by update 1 (predicted) |
| A1 | lr 3e-5, 1 epoch | 0.27 → 0.05 | 42 → 485 | 34 → 0.08 | 471/**0/0/0**/171/**0/0** | 0 | **540 nats**, 1046/1108, 0.005 | collapsed by update 2, to always-PASS |
| A2 | lr 3e-5, 1 epoch, logit bound 5 | 0.49 → 0.88 | 5.0 (pinned) | 35 → 3.6 | 725/154/108/469/29/33/65 | **13** | **0.000 nats** (every finite logit at the bound: ties), argmax = first candidate = PASS 1176/1176, 0.93 | not a runaway; **saturated to uniform** |

**What the arms establish.**
1. **Not the learning rate.** A1 at a tenth of the lr and a quarter of
   the epochs collapsed as completely as A0, in the other direction, and
   its logits kept climbing (373 → 485 over updates 4–8) while the
   pre-clip gradient norm was 0.08–0.5: Adam's normalised step moves
   every parameter ~lr per step whatever the gradient, so once the
   direction is set the magnitude runs regardless of lr. The grad-norm
   clip at 0.5 is inert under Adam for the same reason.
2. **The bound stops the magnitude, not the drift.** A2's pre-activation
   logits ran to the tanh's rails on both sides — the census finds every
   finite logit equal (gap 0.000), i.e. a uniform policy over
   candidates, entropy 0.93 of a ~ln 5 maximum. Its 13 training wins
   (5 %) and the mixed chosen-type counts are what a uniform-random policy
   gets on W0Base against the heuristic, not learning; the deterministic
   battery (argmax on ties = candidate 0 = PASS) shows 0 attacks for the
   same reason. A2 meets the letter of "not collapsed" (gap < 5, entropy
   > 0.3) and fails its intent (argmax-PASS 94 %, by ties).
3. **Correction, in the open.** The velocity diagnostic and the chat
   discussion said the loss was "advantage −1 on every sampled action"
   because every game is lost. `_update_v7` normalises advantages per
   batch (zero mean, unit std, line 890), so in an all-lost batch the
   sign is set by GAE's timestep structure and the critic's values
   (early actions positive, late negative), not by the outcome. The
   drift's *direction* is therefore an artefact of position in the
   game and of the critic's transient, which is why A0 and A1 landed in
   different corners; the velocity numbers stand (they measured
   magnitude per step, and A0's update 1 reproduced them: 177 nats).

**Behaviour the collapse selects** (recorded because it is a finding
about the action space): A0's policy plays a land, then activates a
land's mana ability at every consult until every land is tapped, casts
nothing, attacks and blocks nothing — ~50 ACTIVATE choices per game
against 4–5 real decisions. Every ACTIVATE candidate on W0Base is a
Plains mana ability (126 of 209 consults in `5b_W0Base_p1` offer one):
`RLPlayer` builds the candidate list from XMage's `getPlayable(game,
true)` with only the illegal-land-drop filter, and XMage auto-pays mana
on cast, so tapping a land by hand floats mana that empties at end of
step — a null action that costs one consult, present in v6's candidate
set too ("v6 changes what the agent sees, never what it can choose").
**Amendment owed**: drop `a.isManaAbility()` candidates in
`RLPlayer.consult` (own commit, v6-identity row, as jointBlocks); it
removes the collapse's cheapest sink and cuts consults per episode.

**Pre-registered next arms** (none run; each 12 min): (B1) A2 + the
mana-ability filter; (B2) A2 + AdamW weight decay 0.01 on the heads
(a restoring force the bound lacks); (B3) A2 with the heads on SGD-momentum
at lr 1e-3 while the trunk stays on Adam 3e-5 (removes the normalised
step where the logits are made); (B4) entropy coefficient 0.1 with the
bound (so the rails are not the maximum-entropy state). "Learning" at
this rung is defined now: training win rate over the last 4 batches
above the uniform-random 5 % with a Wilson interval clear of it (≥ 128
games), argmax-PASS fraction on the census between 5 % and 90 % with a
gap > 0.5 nats, and attacks declared > 0 in the deterministic battery.
Pre-registered as before: no arm can beat v6 on rung 0 beyond noise.

## 7a amendment — mana-ability filter in `RLPlayer.priority` (2026-09-13 00:40; branch `v7/lane-d`)

**Change.** `RLPlayer.priority` drops every candidate with
`a.isManaAbility()` right after the phantom-land-drop filter, before the
empty-check (so a window that offered only mana abilities is now an
`autoPassEmpty` window with no consult). `-Drl.manaCands=true` restores the
old set; it is an instance field read per job (like `rl.consultBudget`),
not a class-init constant, so it goes on the job line and needs no JVM
restart. The per-game count reaches the summary as
`fallbacks=... manaCandsDropped=N`. The v6 arm shares the site (one
`getPlayable` call, before the encoder branch), so v6's candidate set
changes identically — as pre-registered, "own commit, v6-identity row".

Why it is not a no-op to leave in: XMage auto-pays on cast, so a
hand-activated land mana ability floats mana that empties at end of step
**and leaves the land tapped** — null at best, a wasted land for the turn
at worst, and one consult either way. It was the cheapest sink of the 7a
collapse (A0: ~50 ACTIVATE choices per game).

**Pre-registered (before the recordings):** the filter cannot change any
win rate of an argmax eval probe on the mono-colour decks except through
the consult budget (fewer consults per game); it removes the ACTIVATE
consults from the A0-style collapse; a payment sub-consult (offered only
when the untapped sources are heterogeneous, candidate 0 = engine default)
is deferred until the bench decks train. Win rates are **not** measured
here (they need ≥ 100 games; the first battery on the new build is the
B arms' deterministic eval, 4 games — too few to say anything).

**v6-identity evidence** (`rl/run_manacands.sh` → `rl/manacands_check.py`,
`rl/artifacts/v7/manacands/{check.txt,check3b.txt,run.log}`; recordings
`rl/artifacts/v7/wire3a/mcL_{on,on2,off}_<deck>.jsonl`, gitignored). Driver
7911 (v7) on the compiled build, 4 seeded games per recording, echo policy
`PREFER=1` (play the first land drop, else PASS: lands reach the
battlefield so mana abilities are offered, none is ever chosen). ON =
`-Drl.manaCands=true` recorded **twice** (the same-build run-to-run
residual is the control), OFF = default.

| deck | consults ON | consults OFF | windows that vanished | candidates removed | of which land mana abilities | `manaCandsDropped` (probe) | control ON vs ON2 |
|---|---|---|---|---|---|---|---|
| W0Base | 423 | 78 | 345 | 401 | 401 | 401 | 423/423 aligned, 0 removed |
| BenchDimir | 611 | 506 | 105 | 1,661 | 1,661 | 1,661 | 611/611, 0 |
| B1Fast | 514 | 261 | 253 | 486 | 486 | 486 | 514/514, 0 |

Candidate-type census (PASS · LAND · SPELL · ACTIVATE · TARGET), ON → OFF:
W0Base 421·58·228·**401**·4 → 76·58·228·**0**·4; BenchDimir
600·45·1601·**1981**·76 → 495·45·1601·**320**·76 (the 320 survivors are the
creature-land / non-mana activations); B1Fast 510·60·443·**486**·20 →
257·60·443·**0**·20. LAND, SPELL and TARGET counts are identical on every
deck; only PASS rows (one per consult) and ACTIVATE rows move.

What differs between ON and OFF beyond the removed rows, by (key, column):
* the control residual (present in ON vs ON2 as well): `v7_ent` idx 22 /
  55 / 56 (tapped, can-attack, can-block) on identical-land rows — the 5e
  replay residual (engine payment order among identical lands); W0Base
  control 220/144/220 rows, filter 36/24/36;
* fields defined by the candidate list or the consult count, which move by
  construction: game token idx 20 (K), 21 (consults so far), 12–19
  (decision type; BenchDimir only, 242 consults whose first candidate was a
  mana ability and is now a spell), opp-action idx 7 (consult age). The
  checker names them `derived_only` and fails on anything else: nothing
  else differs on any deck (`MC|PASS|fails=0` ×3).
* `rl/wire_check_3b.py` over the six `mcL_*` recordings plus
  `mc_p1_off_W0Base`: **0 v6 disagreements, 0 failed identities**.

A PICK=1 recording under the default (`mc_p1_off_W0Base`, 3 games, 139
consults) offers PASS 124 · LAND 78 · SPELL 72 · TARGET 4 · ATTACK 95 ·
BLOCK 49 and **no ACTIVATE at all** on W0Base — against 126 of 209 consults
offering a Plains mana ability in `5b_W0Base_p1` (the old set).

Method note, in the open: the first attempt (`run_pick0.log`) used an
always-pass echo policy; it aligned 63/63 consults on W0Base with 0 removed
because a seat that never plays a land is never offered a mana ability —
vacuous, replaced by the prefer-land policy above. Same-flag recordings of
the same seed are **not** byte-identical (the residual above); the
identity claim is therefore "OFF = ON minus the mana abilities, up to the
residual two ON runs already show", which is what the control column
establishes. The ENC=6 driver (7910) recordings in `run_pick0.log` are
the vacuous kind and are not evidence for the v6 arm; the v6 candidate
rows (`c`) of the v7 recordings are, and they align row for row.

What this cannot support: any statement about play strength or the
collapse (B1 measures that); the filter's effect on decks with mana
abilities that have side effects (none in the bench set); the payment
choice on BenchDimir / P8Faeries (39–49 % of consults per §7a), which the
engine now makes alone until the deferred sub-consult exists.

### 7a — B arms: baseline correction pre-registered before any B result is read (2026-09-13 01:20)

B1's first TRAIN line (32 games played by the init policy before update 1,
on the filter build) reports 6 wins — 0.19, Wilson [0.09, 0.36] — where the
§7a "learning" definition set the bar at "above the uniform-random 5 %".
That 5 % was A2's uniform policy *with* the mana-ability sink; removing the
sink changes what a near-uniform policy does (every sampled action is now a
land, a spell, an attack or a block), so the bar is stale on this build
and 32 games cannot replace it. Pre-registered now, before B1 finishes:

* **B0** (`rl/run_7b0.sh`): the B arms' own init checkpoint, frozen,
  sampled as in training, 128 games W0Base vs heuristic on the filter
  build. Its Wilson interval is the "wins" bar for B1–B4: an arm "learns"
  on the wins criterion only if its last-4-batch rate (128 games) has a
  Wilson interval clear of B0's. The census and battery criteria stand
  as written. B0 cannot inform the collapse question (it never updates).
* The B arms' first-batch rows are not independent evidence of B0's rate
  (same init, same driver seed schedule); B0 uses its own seeds.
* Nothing in this correction moves a bar for a result already read: no B
  row exists yet.

## 7a — arms B0–B4 (2026-09-13 00:25; branch `v7/lane-d`)

`rl/run_7b.sh` (B1–B4) and `rl/run_7b0.sh` (B0), all on the mana-ability-filter
build; artifacts `rl/artifacts/v7/7a/{B0,B1,B2,B3,B4}/`, rows by
`rl/summ_7a.py`. Common recipe = A2: W0Base vs heuristic, 256 episodes,
conc4, cuda, seed 0, lr 3e-5, 1 PPO epoch, logit bound 5. B0 = the same
seed-0 `init.pt` frozen (`--frozen`), sampled as in training, 128 games
(seeds 90000000 / 90000064, 74 s).

| arm | change on A2 (+ filter) | entropy 1→8 | max \|logit\| | grad norm 1→8 | chosen types at 8 (PASS/LAND/SPELL/ACT/TGT/ATK/BLK) | wins/256 | last 4 batches, Wilson | census ck_256: gap · argmax-PASS · entropy | battery at 256 | tests |
|---|---|---|---|---|---|---|---|---|---|---|
| B0 | init policy, frozen, sampled | – | – | – | – | 19/128 | **0.148 [0.097, 0.220]** = the wins bar | – | – | – |
| B1 | filter only | 0.67 → 0.53 | 5 → 5 | 41.7 → 0.10 | 455/0/0/0/171/0/0 | 6 | 0/128 = 0.000 [0.000, 0.029] | 1.81 · 1046/1108 (0.94) · 0.73 | attacks 0/0, turns 12 | none |
| B2 | AdamW, wd 0.01 on the heads | 0.93 → 0.65 | 3 → 4 | 31.0 → 7.6 | 409/152/260/0/24/149/197 | 66 | **43/128 = 0.336 [0.260, 0.421]** | 1.26 · 126/1108 (0.11) · 0.66 | **attacks 16/22, blocks 24/25**, TWIN 1/4, turns 21 | **wins · census · attacks** |
| B3 | heads on SGD-momentum lr 1e-3, trunk Adam 3e-5 | 0.90 → 0.88 | 3 → 3 | 29.6 → 5.4 | 420/255/377/0/18/168/237 | 120 | **83/128 = 0.648 [0.562, 0.726]** | 0.91 · 47/1108 (**0.04**) · 0.76 | **attacks 0/840**, blocks 86/177, ATKOPT 25/104, turns 60 (cap) | wins only |
| B4 | entropy coef 0.1 | 0.66 → 0.54 | 5 → 5 | 42.9 → 0.08 | 451/0/0/0/171/0/0 | 5 | 0/128 = 0.000 [0.000, 0.029] | 5.39 · 1046/1108 (0.94) · 0.32 | attacks 0/0, turns 12 | none |

The B1–B4 first batches (played by the init policy before update 1) sum
to 6 + 3 + 6 + 5 = 20/128 = 0.156, consistent with B0; they were not used
as the bar (same init, correlated seed schedule; pre-registered above).

**What the arms establish.**
1. **The sink was not the drift.** B1 (filter alone) repeats A2's fate in
   A1's direction: always-PASS from update 2, gradient norm 0.10 at
   update 8, the bound holding the gap at 1.8 nats with PASS on top.
   B4's trajectory is B1's to two decimals: an entropy coefficient of
   0.1 does not change where the policy goes (the rails are where a
   bounded scorer under Adam ends up regardless of the bonus).
2. **The optimiser on the heads is the variable.** Both arms that change
   it keep the gradient alive (5–8 at update 8 against 0.1), keep the
   logits off the rail (max |logit| 3–4 under a bound of 5), keep the
   policy mixed (entropy 0.65 / 0.88, every candidate type chosen), and
   win sampled games against the heuristic with intervals clear of B0:
   B2 0.336 [0.260, 0.421], B3 0.648 [0.562, 0.726] vs 0.148 [0.097,
   0.220]. This is the first v7 policy in the project that wins more as
   it trains.
3. **Sampled and argmax behaviour split B2 from B3.** B2's argmax
   attacks (16 of 22 chances), blocks (24 of 25) and passes on 11 % of
   census consults with a 1.26-nat gap — the three pre-registered tests
   are met, so B2 "learns" in the §7a sense. B3's sampled policy attacks
   168 times in its last batch and wins 65 %, but its argmax never
   attacks (0 of 840 chances; the engine's own optimiser found 25 of 104
   attack windows worth taking; battery games run to the turn-60 cap,
   which is why the arm took 42 min) and passes on only 4 % of census
   consults (floor 5 %): the PASS bias flipped to never-pass at
   priority while ATTACK is positive-probability but never top-1
   (census ATTACK argmax 0/47). Two of three tests fail; recorded as
   "wins only", not moved.
4. **Pre-registered "cannot", confirmed:** no arm beats v6 on rung 0.
   The deterministic D0/D1 batteries are 0/4 for every arm (four games:
   no level, by rule). B2's TWIN 1/4 is likewise not a level.

**Reading for the 7a question.** The collapse is structural in the
optimiser–scorer pairing — Adam's normalised step on the head parameters
of an unbounded (A0/A1) or bounded (A2/B1/B4) scorer — and not the lr
(A1), not the bound alone (A2), not the entropy bonus (B4), not the
action-space sink alone (B1). Decoupling the heads (decay toward zero,
or a step proportional to the gradient) is what changes the outcome.

**What this cannot support.** One seed per arm, 256 episodes; the win
rates are *training* rates (sampled, vs heuristic, the policy's own
games), not an eval level; B2 vs B3 (0.336 vs 0.648) is not a ranking
— one seed each, different failure modes under argmax. The B0 bar
holds for this init and this build only. Consults per episode moved
with play (B3's last batches store 46 per episode against B1's 28), so
the 5d throughput numbers do not transfer to these arms without a
re-measurement (the 5d lever run that follows uses B0Base, as 5d did).

**Pre-registered next arms** (none run): B2 and B3 with two more seeds
each (pool only finished seeds; 3 × 128 last-batch games per arm) —
does the argmax-attacks split hold across seeds or is it seed 0; B5 =
SGD heads + wd 0.01 (both levers); B6 = B2 with the census's PASS-bias
centring (candidate-scorer mean subtracted) if the argmax-PASS
fraction is what separates B3's sampled and argmax policies. "Learning"
keeps the §7a definition with the B0 bar; the 2k rung waits for a
recipe that passes it on three seeds.

## 5d follow-up — the first lever (`--batch-max 4`) and the filter build (2026-09-13 00:45; branch `v7/lane-d`)

`rl/run_5d_bm.sh`: the 5d lane (B0Base/B0Twin, 256 episodes, conc4, cuda,
lane defaults lr 3e-4 / 4 epochs / no bound) on the mana-ability-filter
build, three arms, quantities by `rl/tp_5d.py` over the 8 TRAIN rows
(`rl/artifacts/v7/5d/{v6f,v7f,v7bm}/`). v7f's first launch failed at
start (every driver job got `Connection refused` from the policy server
that had just printed ready; `R0_FAILED` episode mismatch 256 vs 0); the
rerun 12 min later ran clean, so it is recorded as a transient, not a
build fault. The 5d rows are repeated for the comparison.

| arm | build | play consults/s | update ms per stored consult | update share of wall | episodes/s | consults per episode | server RSS peak MB | GPU peak MB |
|---|---|---|---|---|---|---|---|---|
| 5d v6 | no filter | 182.5 | 10.8 | – | 0.609 | 101 | – | – |
| 5d v7 | no filter | 50.7 | 58.8 | – | 0.455 | 28 | – | 2,300 |
| v6f | filter | 152.2 | 8.6 | 0.57 | **2.06** | 32.0 | 1,887 | 2,219 |
| v7f | filter | 47.0 | 57.8 | 0.73 | 0.40 | 31.6 | 3,237 | 2,858 |
| v7bm | filter, `--batch-max 4` | **71.3** | 58.0 | 0.81 | 0.43 | 32.3 | 3,136 | 2,826 |

Against the §5d budgets (per-consult, v7 relative to v6 on the same build):

| budget | 5d | now (v7f) | now (v7bm) |
|---|---|---|---|
| play ≥ 1/3 of v6 | 0.28 FAIL | 0.31 FAIL | **0.47 pass** |
| update ≤ 3× v6 | 5.4× FAIL | 6.7× FAIL | 6.7× FAIL |

1. **The batcher does what was pre-registered and no more.** Play rises
   1.52× (47.0 → 71.3 consults/s) and the update cost does not move
   (57.8 → 58.0 ms per stored consult — the batcher is play-side). It
   brings play inside the budget but at less than half the predicted
   "toward ~150": with conc4 at most four consults are ever in flight, so
   the batch is ≤ 4 and the per-call latency floor (network + Java
   encode) stays. Episodes per second barely move (0.40 → 0.43) because
   the update is now 81 % of wall time.
2. **The filter changed v6's throughput far more than any lever changed
   v7's.** v6 episodes hold 32 consults instead of 101 (the ~70 mana
   consults per game are gone), so v6 runs 2.06 episodes/s against 0.61
   — 3.4× — while its per-consult play cost is roughly unchanged (152 vs
   182 consults/s, a 512-consult window is a noisier estimate at 32
   consults per episode). v7's consults per episode were 28 on 5d and are 32
   here. Per-episode, v7 is now 0.21× v6, not 0.75×.
3. **The update ratio got worse, not better**, because v6's update got
   cheaper per consult on this build (10.8 → 8.6 ms) and v7's did not
   (58.8 → 57.8). The 6.7× is the same 5.4× question with a smaller
   denominator; the answer is on the update side, pre-registered as lever
   (2): `rl/update_profile.py profile --arch v7 --device cuda --buf
   rl/artifacts/v7/5d/<arm>/rl_buf.pt` (the first update's real buffer,
   dumped by RL_DUMP_BUF; copied from /tmp, gitignored).

Battery aside, not a result (four games each): v6f wins D0/D1 4/4 with
52/54 attacks as v6 always has; v7f, the A0 recipe (lr 3e-4, 4 epochs,
unbounded) on B0Base with the filter, also shows D0/D1 4/4 and 52/64
attacks at 256 episodes, where the same recipe on W0Base without the
filter (A0) collapsed into the sink. Four games say nothing about a level;
it is noted because it is the first time an unbounded v7 arm attacked at
all, and it is a B0Base game (short, damage-race) not W0Base.

Cannot support: any per-consult claim finer than the 512-consult windows
(one seed, 8 rows); the play number for v7bm at conc > 4 (untested; conc8
would let the batch reach 8 and is the obvious next play-side arm, but
THROUGHPUT-LOCAL §7 measured conc4 as the CPU limit on this machine); the
update-side levers, which need the profile run first.

**Argmax play, two games of B2 `ck_256` vs the heuristic, W0Base, `rl.debug` transcript (seeds 4242/4243, both lost at turns 14 and 17; scratch run, transcript in /tmp/rl_play_B2/driver.log, WSL-local):** plays a land on its first two land turns and never a third; casts one two-mana creature per turn while two Plains cover it; blocks every turn it is attacked, always the solver's block (audit MATCH throughout); declares no attack — and, correction on re-reading the log, never HAD an attack window: the attack audit (on, prints whenever an attacker is available) fired 0 times, every creature being summoning-sick on its own turn and traded in a block the turn after; in game 1 it stopped casting after turn 5 and died on an empty board, in game 2 it traded one creature into a block per turn until outgrown. A two-land, one-creature-a-turn wall. Consistent with the census argmax LAND 51/177 (the third land loses to PASS); the census ATTACK 47/47 says the argmax attacks whenever an attack is offered, and these two games offered none. The battery attacks (16/22) are against D0/D1/TWIN, not the heuristic. Two games: a description, not a level.

## 7c pre-registration — the B2 recipe unchanged to 2,048 episodes, three seeds (2026-09-13 01:35)

Question (from the B2 play note): is the two-land wall undertraining or
the scorer's PASS rank plus late-game credit? `rl/run_7c.sh`: B2's recipe
exactly (lr 3e-5, 1 PPO epoch, logit bound 5, AdamW wd 0.01 on the heads,
filter build), W0Base vs heuristic, 2,048 episodes, seeds 0/1/2 in
sequence, battery every 512 episodes with the lane defaults (100 argmax
games per opponent D0/D1/TWIN, CP7 off), census on `ck_512..2048` over a
filter-build consult set (`7c_W0Base_{p1,p99,sf}`, recorded on 7911 with the
three echo policies, 8 games each) and the new `rl/v7_land_census.py`
(P(LAND) and argmax-LAND by lands in play, on consults that offer a land).

Pre-registered readings, decided before seed 0's first battery:
* **Undertraining** if, by 2,048, the sampled last-4-batch win rate keeps
  rising across the four 512-points on ≥ 2 of 3 seeds AND the argmax
  battery vs D0 rises with it (Wilson intervals of consecutive points
  overlapping is fine; the last point must be clear of the first) AND the
  land census shows argmax-LAND at 3+ lands in play above 50 %.
* **Rank / credit** if the sampled rate rises while the argmax D0 rate
  stays inside its 512-point interval and argmax-LAND at 3+ lands stays
  under 50 % — then B6 (scorer centring) and a credit change are the next
  arms, not more episodes.
* Anything else is "neither shown"; recorded as such.

Cannot do: beat v6 on rung 0 (v6's 2k level on W0Base is the LEVELSET
figure; a v7 point inside v6's interval would be noise, not parity, on one
seed — three seeds pooled is the minimum for any such claim and it is not
the question here); say anything about other decks; separate the two
non-training signatures from each other (B6 alone does that).
Levels: the batteries are 100 games per opponent per point, so each is a
level by the project rule; the sampled training rate is a curve, not a
level. Pool only finished seeds.

### 7c — land census of the 7a checkpoints, and a pre-registration amendment (2026-09-13 02:40, before seed 0's first battery)

`rl/v7_land_census.py` over `7c_W0Base_{p1,p99,sf}` (filter build, 8 games
each, 1,101 consults, 313 offering a land; `rl/artifacts/v7/7c/land_census_7a.txt`):
on every consult that offers a LAND candidate, the summed probability of
playing a land and whether the argmax is a land, by lands the agent
controls (player token idx 13).

| lands in play | consults | init P(land) · argmax-land | B2 ck_256 | B3 ck_256 |
|---|---|---|---|---|
| 0 | 24 | 0.63 · 0 | 0.86 · 24 | 0.96 · 24 |
| 1 | 28 | 0.57 · 0 | 0.60 · 14 | 0.77 · 22 |
| 2 | 42 | 0.41 · 0 | 0.24 · 0 | 0.44 · 18 |
| 3 | 40 | 0.38 · 0 | 0.16 · 0 | 0.37 · 16 |
| 4–6 | 101 | 0.35 · 0 | 0.08 · 0 | 0.36 · 49 |
| 7–14 | 78 | 0.36 · 0 | 0.03 · 0 | 0.55 · 71 |
| ≥ 3 pooled | 219 | 0.36 · 0.000 | **0.08 · 0.000** | 0.43 · 0.621 |

1. **B2's third-land refusal is a learned probability, not a rank
   artefact.** P(land) falls monotonically with lands in play, 0.86 →
   0.24 at two lands → 0.02 at nine, while P(PASS) rises to 0.97. Lands
   in play is a proxy for turn; this is the late-game-negative-advantage
   signature (§7a correction: batch-normalised GAE gives late actions
   negative advantage in a mostly-lost batch) written into the policy.
   Sampled, B2 still plays a third land 16 % of the time, which is why
   the sampled rate is 34 % and the argmax wall loses. B3 is the other
   corner: P(land) rises again past six lands and its argmax keeps
   playing lands (62 % at ≥ 3) — and never attacks.
2. **Identical cards split the softmax mass — a structural bias of the
   argmax battery.** The init at zero lands puts 0.63 on "play a land"
   and 0.37 on PASS yet never argmaxes a land: three Plains in hand are
   three LAND candidates (WIRE §2f, one per playable), each below the
   single PASS row. Any action offered as k identical copies needs k
   times PASS's share to win the rank. This is the mechanism behind the
   init's "argmax PASS on 93 %" and it biases every deterministic
   battery against lands (and against identical creatures) relative to
   the sampled policy. Pre-registered fix, not run: **B7 — argmax over
   candidate classes** (sum probabilities over candidates with the same
   card and rule before taking the argmax; eval-side only, no training
   change; the training sampler is unaffected because sampling already
   sums mass). It cannot change a sampled rate; it can only move argmax
   batteries, and it is expected to move the init's argmax-PASS fraction
   most.

**Pre-registration amendment to 7c** (in the open, before seed 0's first
battery at 512 — the lane had no update yet, only the trained=0 battery, when this was
written): the "argmax-LAND at 3+ lands above 50 %" criterion is confounded
by item 2; the equivalent unconfounded criterion is **P(land) at ≥ 3
lands above 0.5** (summed over land candidates), read from
`v7_land_census.py` on each `ck_512..2048`. Both are recorded; the P(land)
one decides.

### B8 pre-registration — stop centring advantages in constant-outcome batches (2026-09-13 03:20, before any 7c battery beyond trained=0 was read)

Mechanism (§7a correction, 7c land census): `_update_v7` normalises
advantages to zero mean / unit std per batch. In a batch whose episode
outcomes are all −1 the centring leaves only the GAE timestep structure
and the critic transient, so early actions get positive advantage and
late actions negative whatever they were — a fake, position-dependent
gradient. B2 learned it as P(land) falling monotonically with lands in
play. Batching is not the problem; centring across a degenerate batch is.

Change (commit with this row): `policy_server.py --adv-norm
{batch,std,auto,none}`, default `batch` = the recipe through 7c (so the
running 7c lane, which restarts its server from disk, is untouched).
`std` scales by the std and never centres; `auto` centres only when the
batch's outcomes vary; `none` is raw GAE. Unit test `test_norm_adv_modes`
(an all-lost batch: `batch` flips the early actions positive, `std`/`auto`
keep every sign, `auto` centres once outcomes vary).

Arm B8 = B2's recipe + `--adv-norm auto`, W0Base, 256 episodes, seed 0,
then 2,048 on three seeds if the 256 census reads as predicted (`rl/run_7b.sh`
pattern; runs after 7c releases the GPU).

Pre-registered predictions:
* P(land) at ≥ 3 lands on the filter-build census set does **not** fall
  with lands in play at ck_256 (B2's 0.86 → 0.08 was the signature; B8's
  curve is predicted flat or rising past 2 lands, ≥ 0.3 at ≥ 3 lands);
* the sampled last-4-batch win rate is not worse than B2's 0.336 [0.260,
  0.421] (interval overlap suffices — "not worse", not "better");
* argmax-PASS on the census stays in [5 %, 90 %] with a gap > 0.5.
Cannot: raise the update speed; fix the k-copy argmax bias (B7); beat
v6 on rung 0; say anything from one seed beyond "the signature moved".
If `auto` never centres in 256 episodes (no batch with a win), the arm is
equivalent to `std` and is recorded as such.

### 7d plan — behaviour cloning from XMage's strongest AI, then PPO (agreed 2026-09-13 03:20; not started)

Why: the terminal reward carries no information while every game is
lost; a warm start that wins sometimes gives the batch outcome variance,
which is what every normalisation scheme needs and what the critic
needs. v6 imitation from the search teacher reached 0.36–0.40 vs the
heuristic (PHASE5-VERDICT C1), so it is a start, not a ceiling; anvil's
BC → self-play loop worked at scale.

Pieces, in order, each its own row: (1) a recording of consults with the
teacher's chosen candidate index — XMage ComputerPlayer7 (the alpha-beta
AI the lane calls CP7) on the RL seat with the v7 wire dumped and the
choice logged (the `shadowLabel` / `imitateOut` path exists for the v6
search teacher; the v7 version must record the wire message plus the
chosen index, ≥ 20k consults over the bench decks, both seats); (2)
`v7_bc.py`: cross-entropy over candidates on those consults through the
same V7Policy (heads + encoder + adapter; belief off), held-out games for
early stopping, the land census and the argmax-type census as the
behaviour counters, a 100-game argmax battery vs the heuristic as the
level; (3) PPO from the BC checkpoint with B2's optimiser and `--adv-norm
auto`, three seeds, the 7c readings. Pre-registered cannot: BC alone
cannot beat its teacher (it copies CP7's mistakes and its consult budget
is CP7's); the k-copy argmax bias applies to BC too (B7 first). Decision
owed before (1): CP7 as the teacher vs the project's own search teacher
(`rl.agent=search`, plies/breadth), measured by their heuristic win rate
over 100 games each on W0Base.

### 7c interruption — the attack search has no total budget (2026-09-13 03:45; fixed, resumed)

Seed 0 trained 512 episodes (16 updates: batch win rate 0.25 → 0.78, last four 84/128, entropy 0.79, max |logit| 4.1, grad norm 3.3, all action types chosen) and then hung in the trained=512 battery: the driver JVM at 100 % CPU for 25 min, the server idle. Thread dump: `RLPlayer.selectAttackers` → `CombatMath.bestAttack` → the defender-reply `enumerate`. The attack candidates are priced by a one-ply search, up to `rl.attackCap` 4,096 subsets each with a `rl.attackReplyCap` 200,000-leaf reply — 8 × 10⁸ combat resolutions on one consult when both boards are wide. It runs in every game (training too), and no earlier policy ever kept a wide board, so it never showed. Fix (this commit): `rl.attackTotalCap` (default 2,000,000 leaves per call) across all subsets; once spent, the remaining subsets stay in the option list (the candidate **set** never changes) but are priced under a 200-leaf reply cap; `BestAttack.budgetHit` → `fallbacks=... attackBudgetHit=N` in the summary. Pre-registered: no consult whose search stays under the budget changes in any field (same code path); the count of budget hits per battery is recorded with the 7c row, and a consult that hits it has less exact ATTACK afterstates than before, which the row must carry. Resumed from `agent.pt` at 512 (the lane reads `episodes` from the checkpoint); the trained=0 probes are cached, so the seed continues at the 512 battery on the fixed engine. Same-recipe noise noted: this seed at 256 episodes had batch rates 0.34–0.62 where arm B2 (identical recipe, different engine scheduling) had 0.19–0.28 — one seed is not a curve.

## C1 pre-registration — the fixed recipe to 2,048 episodes, three seeds (2026-09-13 04:10; 7c stopped, B8 superseded)

Decision (chat, 2026-09-13 04:00): stop 7c (seed 0 at 512 episodes on B2's
recipe, resumed once after the attack-budget fix; its 16 updates are in
`rl/artifacts/v7/7c/` and the "7c interruption" note) and make the loop
fixes first, then run the three seeds on the fixed recipe. B8's isolated
test of `--adv-norm auto` is superseded by C1 and kept as an ablation to
run later; its pre-registration stands unchanged.

Fixes landed with this row, each behind a flag whose default is the old
behaviour, tested (`test_norm_adv_modes`, `test_argmax_classes_sums_identical_candidates`,
server tests, `v7_check.py`):
* `--adv-norm auto` — centre advantages only when the batch's outcomes vary (B8 row).
* `--target-kl 0.02` — the v7 update stops once the mean approximate KL
  (old log-prob − new) over the samples seen so far passes 0.02; one `KL|`
  line per update reports the KL and whether it stopped. With 1 PPO epoch
  this bounds how far one update can move the policy; it is the trust
  region PPO's ratio clip cannot provide once a policy is deterministic.
* `--argmax-classes` — evaluation argmax over candidate classes (same type,
  afterstate row and referent card names; B7). Training sampling unchanged.
* Engine: `rl.attackTotalCap` (already in, af89167).

C1 = B2's optimiser + the three flags, `rl/run_7c1.sh`: W0Base vs heuristic,
2,048 episodes, seeds 0/1/2, batteries of 100 games per opponent every
512, census + land census on every `ck_512..2048`, `attackBudgetHit`
counts per battery.

Pre-registered readings (the 7c readings, restated for C1):
* **Trains:** sampled last-4-batch win rate rises across the four
  512-points on ≥ 2 of 3 seeds, the last point's interval clear of the
  first; argmax D0 battery rises with it.
* **Third land:** P(land) at ≥ 3 lands on the census set ≥ 0.5 at ck_2048
  on ≥ 2 of 3 seeds (the B2 signature was 0.08).
* **Not collapsed** at every point: argmax-PASS in [5 %, 90 %], gap > 0.5,
  entropy > 0.3, max |logit| < 5.
* **KL budget:** the fraction of updates stopped by the KL budget is
  reported; if it is 0 the flag was inert and is recorded as such.
Cannot: attribute an effect to one flag (that is B8 and the later
ablations); beat v6 on rung 0 — the LEVELSET v6 figure on W0Base is the
comparison, three seeds pooled, and parity on one seed is noise; say
anything about other decks. Levels only from ≥ 100 games per point per
seed; pool only finished seeds.

**C1 first update, stated before the 512 battery (03:38 WSL clock):** `KL|update=1|approx_kl=0.3253|samples=236|stopped=1` — the first window step already moved the policy 0.33 nats mean KL (16× the budget), so the update took one step and stopped; batch 1 win rate 0.094, entropy 1.01, max |logit| 1.9. This is the §7a logit-velocity finding seen from the KL side: one Adam step at lr 3e-5 is a large policy move. The budget will bind on every update, so C1 trains at ~1 optimiser step per 32 episodes (~64 steps over 2,048) where B2 took ~28 per update. Pre-stated follow-up, not a moved bar: if seed 0's batch win rate at 512 is below 7c seed 0's on the same games (0.62 at 256, 0.78 at 512, no budget), the KL budget starved the optimiser and **C2 = C1 with `--target-kl 0.1`** (and, if still binding on every update, a per-step KL check inside the window loop rather than a stop) is the next arm; C1's reading is then "budget too tight", not "fixes failed". If seed 0 matches or exceeds 7c at 512 with the third land back, the budget is doing its job.

## 7d piece (1a) pre-registration — teacher choice, CP7 vs the search teacher (2026-09-13 05:05; C1 seed 0 at 256 episodes, GPU busy)

The 7d plan owes one decision before any recording: is the teacher XMage's
ComputerPlayer7 (the lane's `cp7` opponent, `rl.aiSkill` 6) or the
project's search teacher (`rl.agent=search`, one-ply / breadth-8 by
default)? Measured now, while C1 holds the GPU, as pure-Java games on
driver 7911 (`rl/run_7d1.sh`, artifacts `rl/artifacts/v7/7d1/`): W0Base
mirror, 100 games each, `rl.stopTurn` 60, seats alternating play/draw by
episode parity, seed 7100, concurrency 2 (the lane keeps its conc4; 16
cores, load 2.5 before launch).

* `cp7_vs_heur`: the driver has no CP7 *agent* kind, so CP7 sits in the
  opponent seat against the heuristic as agent; CP7's rate is
  `losses / episodes` of that summary. Seats alternate, so the seat swap
  is not a confound beyond the usual play/draw parity.
* `search_p1b8_vs_heur` and `search_p2b8_vs_heur`: the search teacher as
  agent at plies 1 / breadth 8 (the driver defaults, the setting the v6
  imitation used per PHASE5-VERDICT C1) and plies 2 / breadth 8.

Pre-registered reading: the teacher is the one whose Wilson interval vs
the heuristic is higher and clear of the other's; if the intervals
overlap, the cheaper one per game (games per second in the summary)
wins, because piece (1b) needs ≥ 20k consults. Draws and stalls are
carried, not folded into wins.
Cannot: say anything about either teacher on the RL seat with a consult
budget (the recording in piece (1b) adds that); say anything about the
bench decks; rank CP7 against the search teacher head to head (not run).
Loads: three jobs on 7911 share the CPU with the C1 lane, so C1's wall
time per seed is not comparable to 7c's; its results are unaffected
(`rl.attackTotalCap` is a leaf count, not a timer).

## 7d piece (1a) — teacher choice: CP7 is the teacher (2026-09-13 05:20; branch `v7/lane-d`)

`rl/run_7d1.sh` on driver 7911, artifacts `rl/artifacts/v7/7d1/`, W0Base
mirror, 100 games per arm, seats alternating, seed 7100 unless named,
concurrency 2 beside the C1 lane. The three pre-registered arms plus four
controls added after the first three landed (in the open: p1b8 and p2b8
came back identical, 37/100 with 12.9 turns per game, and the first
reading was "the plies flag is ignored" — the node counter says otherwise,
see item 2). "Teacher wins" for the CP7 row is `losses` of the heuristic
agent's summary, CP7 being in the opponent seat.

| arm | teacher wins/100 | Wilson | games/s (conc 2) | turns/game | search decisions | search nodes |
|---|---|---|---|---|---|---|
| **cp7_vs_heur** (CP7, `rl.aiSkill` 6) | **68/100** | **[0.583, 0.763]** | 3.2 | 18.2 | – | – |
| heur_vs_heur (control) | 50/100 | [0.404, 0.596] | 12.0 | 12.7 | – | – |
| search p1b8 | 37/100 | [0.282, 0.468] | 11.4 | 12.9 | 802 | 2,529 |
| search p1b16 | 37/100 | [0.282, 0.468] | 9.6 | 12.9 | 802 | 2,529 |
| search p2b8 | 37/100 | [0.282, 0.468] | 10.1 | 12.9 | 802 | 5,860 |
| search p3b8 | 37/100 | [0.282, 0.468] | 8.5 | 12.9 | 802 | 5,860 |
| search p1b8, seed 7200 | 41/100 | [0.319, 0.508] | 10.1 | 12.7 | 781 | – |

1. **CP7 is the teacher by the pre-registered criterion.** Its interval
   [0.58, 0.76] is clear of every search arm (best 0.41 [0.32, 0.51]) and
   of the heuristic mirror. Cost: 0.6 s per game at concurrency 2 on a
   loaded machine; at ~32 consults per filter-build game a 20k-consult
   recording is ~650 games, minutes not hours.
2. **The search teacher loses to the plain heuristic on W0Base**, 37/100
   [0.28, 0.47] against the mirror's 50/100 [0.40, 0.60], and no search
   knob moves it: plies 1/2/3 and breadth 8/16 give the same 37 wins
   and the same 12.9 turns per game on the same seed. The node counter
   shows the flags are honoured (2,529 → 5,860 nodes for plies 2; plies 3
   evaluates the same 5,860 as plies 2, so the search stops at two plies
   on this deck — a property of `valueStatic`, not measured further) and
   the search fires on ~8 decisions per game (802 / 100); the rest of the
   game is the heuristic. On a mono-white creature deck the one-ply
   static score picks the same ability at every depth, and that pick is
   worse than D0's own rule. The seed-7200 repeat (41/100) is inside the
   seed-7100 interval. This is consistent with PHASE5-VERDICT C1's v6
   imitation reaching 0.36–0.40: the student matched a teacher that
   plays at ~0.37.
3. Confounds carried: CP7 was measured from the opponent seat (the driver
   has no CP7 agent kind; seats alternate so play/draw is balanced, and
   the control mirror is 50/100); the machine was shared with the C1
   lane (speeds are relative, not the THROUGHPUT-LOCAL protocol); CP7 at
   `rl.aiSkill` 6 only; W0Base only.

**Cannot** (pre-registered): say anything about either teacher on the RL
seat under a consult budget; anything about the bench decks; rank CP7
against the search teacher head to head (not run). Piece (1b) now needs a
`rl.agent=cp7` seat in `EpisodeRunner` that dumps the v7 wire with CP7's
chosen candidate index — a Java change, so it waits for the lane to idle
(never recompile while a lane runs).

Addendum to 7d piece (1a), in the open (05:40): `rl/RUNG0-CEILING-TEST.md`
already had these two players in the same seat vs D0 on W0Base — 1-ply
search .410 [.319, .508], CP7 .650 [.524, .758] (n=60) — and LEVELSET's
".614 over the heuristic" for the search opponent is the multi-deck
figure with the caveat "a worse pilot than the heuristic on four of six
archetype decks". The 7d1 numbers (search .37/.41, CP7 .68) replicate the
ceiling-test rows on this build; they are not a new finding about the
search teacher, and the decision stands.

## C1 — seed 0 interim at 512 and 1024 episodes (2026-09-13 05:45; seed 0 still running; not the C1 row)

Read from `/tmp/rl_7c1_s0/` while the lane runs; the C1 row waits for
three finished seeds. Recorded now because the pre-stated C2 trigger is
read at seed 0's 512 point.

**Sampled curve, seed 0** (batch of 32 episodes per update; `rl/artifacts/v7/7c1/s0/` gets `train_lines.txt` at seed end):

| updates | episodes | batch win rates | last-4 wins | entropy | max \|logit\| | KL-stopped |
|---|---|---|---|---|---|---|
| 1–8 | 256 | .09 .28 .06 .00 .00 .00 .09 .00 | 3/128 = 0.023 [0.008, 0.067] | 1.01 → 0.39 | 1.9 → 4.6 | 5/8 |
| 9–16 | 512 | .53 .56 .84 .78 .78 .72 .91 .94 | **107/128 = 0.836 [0.762, 0.890]** | 0.49–0.64 | 4.6 → 4.93 | 1/8 |
| 17–32 | 1024 | .78–.91, no trend | 110/128 = 0.859 [0.788, 0.909] | 0.56–0.69 | 4.74 → **5.00** (updates 30–32) | 1/16 |

Consults per episode ran 27 → 70 through the dead stretch (updates 4–8:
long games, 250+ blocks and < 30 attacks per batch — the B3 wall, sampled)
and back to ~40 once the policy started winning (attacks 113–170 per
batch from update 11). The first eight batches are the C2 question:
after the first three KL-bound single steps (KL 0.33 / 0.17 / 0.03) the
batch went to zero wins for five updates, during which `--adv-norm auto`
does not centre (no outcome variance) and every advantage is negative;
the policy climbed out at update 9 without any intervention.

**Argmax battery at 512** (100 games per opponent, `--argmax-classes`,
levels by the project rule): **D0 0.77 [0.678, 0.842]**, D1 0.80 [0.711,
0.867], TWIN 0.79 [0.700, 0.858]; blocks 1611/2081, BLOCKOPT 758/815,
attacks 1227/5049, ATKOPT 913/1409, under/over 390/84, 35.5 turns;
`attackBudgetHit` 47 / 46 / 40 per 100-game battery (so ~45 % of games
had at least one consult priced under the 200-leaf reply cap — carried,
not corrected).

**Census at `ck_512`** (`rl/artifacts/v7/7c1/s0/census_512.txt`, the
7c_W0Base p1/p99/sf set, 1,101 consults): argmax-PASS when another
candidate exists 149/1070 = **14 %**, mean top gap **3.55** nats, entropy
0.64; argmax types LAND 204/313, SPELL 368/368, ATTACK 130/279, BLOCK
207/207. Land census: P(land) 1.00 at zero lands, 0.85 at one, 0.53 at
two, 0.48 at three, 0.45 at four, then rising to 0.75 at six and 1.00 at
nine or more; **P(land) at ≥ 3 lands = 0.70** (argmax-land 140/219), and
P(PASS) on land-offering consults is 0.000 at every land count — the dip
at 3–4 lands is SPELL winning the argmax (24 of 40 consults), not PASS.
B2's signature at the same point was 0.08 falling monotonically.

**Readings, seed 0 only (the pre-registered ones are decided at 2,048 on
three seeds):**
* C2 trigger — **not fired.** Seed 0's batch rate at 512 (0.94, last four
  0.836) is above 7c seed 0's 0.78 on the same recipe without the budget;
  the KL budget bound 5 of the first 8 updates and 2 of the next 24. The
  budget is not starving the optimiser; `rl/run_7c2.sh` is staged and not
  launched.
* Third land: 0.70 at ck_512 against the 0.5 bar (the bar is read at
  ck_2048).
* Not collapsed at 512: all four clauses hold (14 %, 3.55, 0.64, 4.93).
  At 1024 the logit clause is **at the bound** — max |logit| 5.00 on
  updates 30–32 — while entropy stays 0.64–0.69 and every type is chosen;
  whether the census at ck_1024 keeps the other three is read when its
  battery lands.
* Context, not a comparison (one seed): v6's rung-0 W0Base curve
  (`rl/artifacts/rung0/W0Base/report.txt`) is D0 0.568 [0.519, 0.615]
  at 512 pooled over two seeds, 0.78 at 1,407–1,919, 0.705 at 2,111 (seed
  0 alone). C1 seed 0's 0.77 at 512 has an interval clear of v6's 512
  point; the pre-registered "cannot" (parity on one seed is noise; three
  seeds pooled before any comparison) stands.

Cannot: any of the above as a level for C1 (one seed); attribute the
recovery to a flag (B8 and the ablations); the 1024 census (pending).

### 7d piece (1b) design — CP7 teacher recording on the v7 wire (pre-registered 2026-09-13 06:05; Java not started, the lane owns the engine until C1 finishes)

What exists: the v7 consult is assembled by `RLPlayer.consultInner` from
`StateEncoder.encodeEntityView(game, me, opp)`, the candidate rows plus
`CandMeta` (afterstates via `v7AfterPlayable`), `phi(game)`, and
`SocketPolicyClient.choose(view, cands, phi, meta)`; the recording is
server-side (the policy server's recorder, as for the 5b/7c sets). The
v6 teacher path (`shadowLabel`) computed a static search label inside the
RL seat's consult; CP7 is a whole `Player` whose choice comes out of
`ComputerPlayer6.simulatePriority` and is applied by `act()` — one or
more `activateAbility` calls per priority window — so the label has to be
read *after* CP7 acts while the consult state is taken *before*.

Design (one Java commit + one wire amendment, after the lane idles):
1. `CP7TeacherPlayer extends mage.player.ai.ComputerPlayer7`, agent kind
   `rl.agent=cp7` in `EpisodeRunner` (mirrors the opponent branch:
   `RangeOfInfluence.ONE`, `rl.aiSkill` 6, the fake match). Overrides
   `priority(game)`: (a) build the candidate list exactly as
   `RLPlayer.priority` does (same `getPlayable`, phantom-land and
   mana-ability filters, same ordering) and the pre-action consult (view,
   cands, meta); (b) `super.priority(game)`; (c) an overridden
   `activateAbility` records the FIRST ability CP7 activates in this
   window, keyed `sourceId|rule` as `shadowLabel` does; (d) send the
   consult with label `y` = that candidate's index (0 = CP7 passed, −1 =
   CP7 acted on something outside the candidate set, e.g. a mana
   ability), reply ignored. Extra activations in the same window are
   counted (`teacherMultiAct`), not labelled.
2. Joint sites: `RLPlayer.selectAttackers` / `selectBlockers` candidates
   come from `CombatMath` (`jointAttacks` / `jointBlocks`); CP7's
   `selectAttackers` / `selectBlockers` declare through the game. The
   teacher player builds the same joint candidate list before delegating
   to CP7, then reads the declared set from the game and labels the
   candidate whose set matches (−1 if none; counted `teacherJointMiss`).
   If the joint builders cannot be lifted out of `RLPlayer` cheaply the
   first recording is priority-only and BC trains the priority head only,
   with the attack/block heads left at init — stated in the row either way.
3. Wire: consults gain an optional integer `y` (teacher label) and hello
   gains `teacher: "cp7"`; absent = unchanged v7 contract (WIRE-V7 §8
   entry with the commit; `wire_validate` accepts and ignores `y`).
   The opponent-knowledge tracker is attached the way `RLPlayer` attaches
   it (`ensureTracker` = `RLKnowledgeWatcher.ensure(game, me, opp, oppDeckInfo)`, static), so §2g fields match an RL-seat consult.
4. Recording: bench decks (W0Base first, then the 5b deck set), both
   seats via the driver's play/draw parity, `rl.consultBudget` 300, ≥ 20k
   labelled consults; `rl/artifacts/v7/7d1b/` (gitignored jsonl),
   counters in the summary: consults, labelled, `y=-1`, multi-act,
   joint-miss. Faithfulness: `rl/probes/faithfulness.py` on 100 consults
   of the recording (the 5b gate) — a CP7-seat consult must pass the same
   gate as an RL-seat one.

Pre-registered readings for the recording row: fraction labelled (−1
excluded) ≥ 0.9 of consults, else the candidate set is not CP7's action
space and BC is not attempted on it; CP7's label type census (PASS / LAND
/ SPELL / ATTACK / BLOCK shares) recorded as the target the BC census is
read against. Cannot: change CP7's strength (it is what it is, 0.68 on
W0Base); make the RL seat's consult budget CP7's (CP7 sees every window;
the recording counts windows the RL seat would have auto-passed as
`autoPassEmpty` and skips them the same way); say anything about BC
(piece 2).

**Seed 0 at 1024 (06:15):** battery D0 **0.81 [0.722, 0.875]**, D1 0.79
[0.700, 0.858], TWIN 0.75 [0.657, 0.825]; blocks 1877/2570, BLOCKOPT
806/869, attacks 1429/7267, ATKOPT 879/1648, under/over 548/149, 40.3
turns. Census at `ck_1024` (`census_1024.txt`): argmax-PASS 148/1070 =
14 %, gap 2.99, entropy 0.63, argmax types unchanged from 512 (LAND
204/313, ATTACK 132/279, BLOCK 206/207); P(land) at ≥ 3 lands **0.73**
(argmax-land 140/219), the 3–4-land dip now 0.54 / 0.50 with SPELL still
the argmax there. So the three census clauses of "not collapsed" hold at
1024 while max |logit| sits on the bound (5.00 at updates 30–32): the
bound is clipping, the policy is not on a rail. **`attackBudgetHit` rose
to 170 / 166 / 185 per 100-game battery** (from 47 / 46 / 40 at 512):
games are longer (40 turns) and boards wider, so ~1.7 consults per game
now price ATTACK candidates under the 200-leaf reply cap — the exactness
of the attack afterstates is degrading as the policy gets better at
keeping a board, and the row carries it; a per-consult count (not per
game) is the better counter and is not yet emitted. D0 at 512 → 1024:
0.77 → 0.81, intervals overlapping (no claim). Levels stand as one
seed's points; the C1 row waits for seeds 1 and 2.

**Seed 0 at 1536 (07:05):** D0 **0.83 [0.745, 0.891]**, D1 0.82 [0.733,
0.883], TWIN 0.83 [0.745, 0.891]; turns 31.1 (down from 40.3), attacks
1258/4179, blocks 1377/1686, under/over 330/303. Census `ck_1536`:
argmax-PASS **61/1070 = 5.7 %** (inside [5 %, 90 %] but at the floor — the
PASS share is falling 14 → 14 → 6 %, watched at 2048), gap 2.57, entropy
0.75, P(land) at ≥ 3 lands 0.74. `attackBudgetHit` 44 / 35 / 65 (the
1024 spike tracked game length, not a monotone trend). D0 512 → 1536:
0.77 → 0.81 → 0.83, every consecutive pair overlapping.

## C1 — seed 0 complete (2026-09-13 07:40; seeds 1 and 2 running; the C1 row is written when all three are in)

`python3 rl/summ_7c1.py rl/artifacts/v7/7c1/s0` (64 updates; probes
copied into `s0/` so the budget-hit column maps):

| point | D0 | D1 | TWIN | turns | sampled last-4 | argmax-PASS | gap | entropy | P(land) ≥ 3 | budget hits |
|---|---|---|---|---|---|---|---|---|---|---|
| 512 | 0.77 [0.678, 0.842] | 0.80 [0.711, 0.867] | 0.79 [0.700, 0.858] | 35.5 | 107/128 = 0.836 [0.762, 0.890] | 14 % | 3.55 | 0.64 | 0.70 | 47 / 46 / 40 |
| 1024 | 0.81 [0.722, 0.875] | 0.79 [0.700, 0.858] | 0.75 [0.657, 0.825] | 40.3 | 110/128 = 0.859 [0.789, 0.909] | 14 % | 2.99 | 0.63 | 0.73 | 170 / 166 / 185 |
| 1536 | 0.83 [0.745, 0.891] | 0.82 [0.733, 0.883] | 0.83 [0.745, 0.891] | 31.1 | 82/128 = 0.641 [0.555, 0.719] | 6 % | 2.56 | 0.75 | 0.74 | 44 / 35 / 65 |
| 2048 | **0.85 [0.767, 0.907]** | 0.85 [0.767, 0.907] | 0.88 [0.802, 0.930] | 34.8 | 102/128 = 0.797 [0.719, 0.857] | 10 % | 1.70 | 0.76 | **0.72** | 114–122 |

Seed 0 against the four pre-registered readings (each decided on three seeds):
* **Trains — the sampled clause is NOT met, the argmax clause is.** The
  sampled last-4 rate was already 0.84 at 512 and did not rise (0.86,
  0.64, 0.80; last not clear of first); the argmax D0 level rose at every
  point, 0.77 → 0.81 → 0.83 → 0.85, consecutive intervals overlapping and
  the 2048 interval [0.767, 0.907] overlapping the 512 one [0.678,
  0.842]. The reading was written for a slowly climbing curve (the 7c
  "undertraining" question); this seed reached its sampled plateau
  inside the first 512 episodes, then the argmax battery kept improving
  while the sampled rate wandered — the sampled rate is against the
  heuristic with exploration noise (entropy 0.6–0.8), the battery is
  argmax over classes; the two are not the same quantity. Recorded as
  "sampled flat from 512, argmax rising, neither clear" — not as a pass.
* **Third land — met** on this seed: P(land) at ≥ 3 lands 0.72 at
  ck_2048 (0.70 / 0.73 / 0.74 / 0.72 along the way; B2 was 0.08).
* **Not collapsed — met at every point** on the census clauses
  (argmax-PASS 14 / 14 / 6 / 10 %, gap 3.55 → 1.70, entropy 0.63–0.76);
  max |logit| touched the bound (5.00) inside the 512–1024 stretch and sat
  at 4.98–4.99 after. The gap is shrinking (3.55 → 1.70) while entropy
  rises: the policy is getting *less* deterministic with training, which
  is the opposite of the 7a rail.
* **KL budget — active, not binding:** 13 of 64 updates stopped (0.20),
  5 of them in the first 8.
* Attack budget: 114–122 hits per 100-game battery at 2048; the exactness
  caveat on ATTACK afterstates stands for every C1 level.

Context, not a claim (one seed; the v6 comparison waits for three): v6's
rung-0 W0Base D0 levels were 0.568 at 512 (two seeds pooled), 0.78 at
1,407–1,919 and 0.705 at 2,111 (seed 0); C1 seed 0's 0.85 [0.767, 0.907]
at 2048 has an interval clear of v6's 2,111 point (0.705 [0.638, 0.764])
and of v6's 512 point. Whether that survives pooling is the C1 row's
question. Cannot: attribute the recovery from the dead stretch to a flag;
say anything about other decks; call the 2048 level a v7 level (one seed).

## 7d overnight — correction in the open: `--argmax-classes` is INERT on the v7 path (found 2026-09-13 08:40 next-session clock; WSL 01:35, C1 seed 1 at its 512 battery)

While writing the league lane (OVERNIGHT-7D A4) the eval branch of
`Trainer.act_v7` in `rl/policy_server.py` turned out to be a plain
`torch.argmax(logits[0])`; `_argmax_classes` (B7) is called only from the
v6 `Trainer.act` path (line ~867). The flag was tested on the function
(`test_argmax_classes_sums_identical_candidates`) and never on the v7
serving path, so **every C1 battery (seeds 0 and 1, every 512-point) and
the 7c/B-row batteries that said "argmax over classes" were plain-argmax
batteries.** The B7 pre-registration ("identical cards split softmax
mass; the argmax is biased against k-copy actions") therefore still
describes the batteries as run. Nothing in the C1 census or land-census
rows is affected (those tools score the checkpoints directly); the levels
stand as plain-argmax levels and are relabelled so in the C1 two-seed row.
Fix (Phase B, server-side, after the seed-1 lane idles): apply
`_argmax_classes` in `act_v7`'s eval branch behind the same flag, plus a
test that drives a fixture consult with two identical candidates through
`act_v7(sample=False)` with the flag on and off. Consequence for tonight's
comparison: D-PPO / L0 / L1 batteries run on the fixed server, so the
**C1 checkpoints (s0, s1: `ck_512..2048.pt` under /tmp and `ck_2048.pt`
in the artifacts) are re-batteried on the fixed server in Phase C** (100
games per opponent per point, same seeds) before the Q1 reading, and both
protocols are reported. Cannot: say tonight which way the fix moves a
level (B7's prediction is "up on LAND-copy windows"; it is a prediction).

## 7d overnight pre-registration — D-BC, D-PPO (Q1) and the league L0/L1 (Q2) (2026-09-13 08:45 next-session clock; runbook `rl/OVERNIGHT-7D.md`)

Decision (chat, runbook header): C1 stops after seed 1 (`rl/stop_c1_parent.sh`);
seeds 0 and 1 are the no-IL baseline; seed 2 is owed and resumable. The
Java for piece (1b) is `rl/xmage-src/CP7TeacherPlayer.java` +
`rl.agent=cp7` in `EpisodeRunner` + the per-consult `y` / hello
`teacher:"cp7"` in `SocketPolicyClient` (9e24145, source only until the
lane idles). **Priority-only**: CP7's combat goes through
`ComputerPlayer6.declareAttackers/declareBlockers` and lifting
`RLPlayer.jointAttacks/jointBlocks` out of `RLPlayer` blind (no compile
while the lane owns the engine) was judged not cheap; a cp7-seat recording
therefore holds priority consults only (no atkjoint/blkjoint consults at
all), and BC trains the shared candidate head on priority windows only -
the attack/block behaviour of bc.pt is the init's. Stated here, before
the recording, as the design row allowed.

* **Recording (piece 1b)** — `rl/record_7d1b.sh`: echo policy on the
  teacher seat (`-Drl.agent=cp7 -Drl.opponent=heuristic`, W0Base mirror,
  both seats by episode parity, `rl.consultBudget` 300, driver 7911 with
  the v7 flags), several seeded jobs until ≥ 20k labelled consults;
  artifacts `rl/artifacts/v7/7d1b/` (jsonl gitignored, counts committed).
  Readings as in the design row: labelled fraction (y ≥ 0) ≥ 0.9 of
  consults, else no BC; `teacherMultiAct` and `teacherOutside` reported;
  CP7's label type census (PASS/LAND/SPELL shares) = the target the BC
  census is read against; `wire_validate` on 100 consults; the 5b
  faithfulness gate (`rl/v7_faith_real.py`) on the recording. Cannot:
  change CP7's strength (0.68 vs D0 on W0Base, piece 1a); label combat.
* **D-BC** — `rl/v7_bc.py` (e863751): init = a P10INIT v7 init (seed 10,
  cdim 94, the lane's shape), AdamW with the B2/C1 decay on the heads,
  10 % of GAMES held out, early stopping on held-out CE, memoryless
  scoring (fresh heads state per consult, as `v7_init_logits.py`), logit
  bound 5. Readings: held-out top-1 agreement and type agreement
  (reported, no bar); the BC battery = the D-PPO lane's battery at
  trained=0 (100 games each D0/D1/TWIN on the fixed argmax-classes server)
  - expected ≤ CP7's 0.68 vs D0; type census + land census on bc.pt
  against the label census. Cannot: beat CP7; say anything off W0Base;
  move the attack/block heads (priority-only labels).
* **D-PPO (Q1)** — `rl/run_7d3.sh` = `run_7c1.sh` with `R0_INIT=bc.pt`
  (the `R0_INIT` hook added to `rung0_lane.sh` in Phase B: copy the given
  checkpoint to `$OUT/init.pt` instead of regenerating it; bc.pt carries
  episodes=0 so the lane counts from 0), C1's exact flags, 2,048 episodes,
  seeds 0 and 1, batteries every 512, artifacts `rl/artifacts/v7/7d3/s<seed>/`.
  **Readings, pooled two seeds vs C1's pooled two seeds (200 games per
  opponent per point), both on the fixed argmax-classes server (C1's
  checkpoints re-batteried, see the correction above):** "IL helps" if
  D-PPO's pooled D0 at 2048 has a Wilson interval clear above C1's, OR
  D-PPO's pooled D0 at 512 is clear above C1's 512 (a faster start,
  stated separately); "IL hurts" if clear below at 2048; else "no
  difference shown at n=200". Also: the first-8-batch sampled wins (C1
  seed 0: 14/256 - does BC remove the dead stretch), the land census per
  ck, the KL-stopped fraction. Cannot: separate BC's effect from its
  consult budget or from the priority-only labels; generalise off W0Base;
  call any of it a level from < 2 finished seeds; compare against C1's
  plain-argmax batteries as if they were the same protocol.
* **L0 / L1 (Q2)** — `rl/run_7l.sh`, both from C1 seed 0 `ck_2048.pt`
  (`rl/artifacts/v7/7c1/s0/ck_2048.pt`), 1,024 more episodes each, one
  seed each, driver 7912, own ports (7950/7951, opponent 7960); the
  battery is run at the start (+0 row, trained=2048) and at 2560 / 3072
  (absolute labels; +512 / +1024 relative). **L0** = `rung0_lane.sh` with
  `R0_INIT` vs the heuristic (the same-compute control); **L1** =
  `rung0_lane_league.sh` vs frozen C1 checkpoints alternating per
  512-block: block 0 = C1 s0 `ck_1024.pt`, block 1 = C1 s0 `ck_2048.pt`
  (the lane logs `R0_OPP|` per block), the opponent served frozen /
  eval-mode / argmax over classes. Readings: L1's D0 / D1 / TWIN at 3072 vs
  L0's at 3072 (100 games each; one seed, so only "clear of" counts and
  the row says one seed); L1's sampled rate against its league opponent
  per 512-block (from the TRAIN lines) as the behaviour counter; land
  census at 2560 / 3072 for both. Cannot: claim a league level from one
  seed; say anything about self-play from scratch; separate "a stronger
  opponent" from "a different opponent" (the frozen checkpoint is both).

What none of this can move, stated in advance: the attack-budget caveat
(`attackBudgetHit`) on every ATTACK afterstate; the 5d update-cost FAIL;
the plain-argmax k-copy bias of every battery run BEFORE the Phase B fix.
GPU: D-PPO and the L lanes share the 12 GB card (C1 peaked 4.9 GB); if the
second lane OOMs or D-PPO's update time doubles, L0/L1 run after D-PPO and
the row says so.

## C1 — two seeds (2026-09-13 09:40 next-session clock; WSL 03:40; seed 2 OWED, not run: the runner was stopped by decision after seed 1, `rl/stop_c1_parent.sh`, OVERNIGHT-7D)

**This is a two-seed row.** The pre-registration asked for three seeds; C1 seed 2 is
resumable (`rl/run_7c1.sh` skips finished seeds) and every "≥ 2 of 3 seeds" clause is
read here as "on both seeds / on one of two", stated as such. **Battery protocol:
plain argmax** — the `--argmax-classes` flag was inert on the v7 serving path for every
battery in this row (correction row "7d overnight — correction in the open"); the
class-argmax re-battery of these checkpoints is a Phase C item and gets its own row.
`python3 rl/summ_7c1.py rl/artifacts/v7/7c1/s0 rl/artifacts/v7/7c1/s1`; seed 1's
artifacts are `rl/artifacts/v7/7c1/s1/` (post-processed by `rl/post_7c1_seed.sh 1`).

Seed 1 (64 updates, KL stopped 5/64):

| point | D0 | D1 | TWIN | turns | sampled last-4 | argmax-PASS | gap | entropy | P(land) ≥ 3 | budget hits |
|---|---|---|---|---|---|---|---|---|---|---|
| 512 | 0.61 [0.512, 0.700] | 0.61 [0.512, 0.700] | 0.58 [0.482, 0.672] | 48.8 | 92/128 = 0.719 [0.635, 0.789] | 18 % | 1.62 | 0.83 | 0.49 | 564 / 546 / 597 |
| 1024 | **0.49 [0.394, 0.587]** | 0.51 [0.413, 0.606] | 0.46 [0.366, 0.557] | 47.4 | 90/128 = 0.703 [0.619, 0.775] | 20 % | 1.64 | 0.76 | 0.44 | 400 / 385 / 421 |
| 1536 | 0.78 [0.689, 0.850] | 0.86 [0.779, 0.915] | 0.78 [0.689, 0.850] | 42.7 | 110/128 = 0.859 [0.789, 0.909] | 21 % | 1.86 | 0.71 | 0.36 | 284 / 279 / 287 |
| 2048 | **0.85 [0.767, 0.907]** | 0.82 [0.733, 0.883] | 0.88 [0.802, 0.930] | 31.5 | 107/128 = 0.836 [0.762, 0.890] | 18 % | 1.00 | 0.84 | **0.38** | 63 / 58 / 77 |

Pooled over the two finished seeds (200 games per opponent per point; seed 0's
points are in "C1 — seed 0 complete"):

| point | D0 | D1 | TWIN |
|---|---|---|---|
| 512 | 138/200 = 0.690 [0.623, 0.750] | 141/200 = 0.705 [0.638, 0.764] | 137/200 = 0.685 [0.618, 0.745] |
| 1024 | 130/200 = 0.650 [0.582, 0.713] | 130/200 = 0.650 [0.582, 0.713] | 121/200 = 0.605 [0.536, 0.670] |
| 1536 | 161/200 = 0.805 [0.745, 0.854] | 168/200 = 0.840 [0.783, 0.884] | 161/200 = 0.805 [0.745, 0.854] |
| 2048 | **170/200 = 0.850 [0.794, 0.893]** | 167/200 = 0.835 [0.777, 0.880] | 176/200 = 0.880 [0.828, 0.918] |

The four pre-registered readings, on two seeds:
* **Trains — sampled clause NOT met on either seed; argmax clause met on
  both, but not monotone on seed 1.** Sampled last-4 rates: seed 0 0.84 →
  0.80 (flat from 512), seed 1 0.72 → 0.70 → 0.86 → 0.84 (last not clear
  of first). Argmax D0: seed 0 0.77 → 0.85 (rising at every point), seed
  1 0.61 → **0.49** → 0.78 → 0.85 — a dip at 1024 whose interval [0.394,
  0.587] is clear BELOW its own 2048 point and below seed 0's 1024 point
  [0.722, 0.875]; then a recovery to the same 0.85 as seed 0. Pooled D0
  2048 [0.794, 0.893] is clear of pooled 512 [0.623, 0.750]: the level
  rises from 512 to 2048 on the pooled read, through a pooled 1024 dip
  (0.65) that seed 1 alone produces. Recorded as "rises 512 → 2048 on
  both seeds' endpoints; the path is not monotone (seed 1's 1024 dip);
  the sampled rate is flat" — not a pass of the clause as written.
* **Third land — met on ONE of two seeds.** Seed 0 0.72 at ck_2048; seed
  1 0.49 → 0.44 → 0.36 → **0.38** (argmax-land at ≥ 3 lands 0.64 → 0.22),
  i.e. the B2 signature (unlearning the third land as a probability)
  returns on seed 1 *while its argmax D0 reaches 0.85*: on W0Base a policy
  can win at this level with two lands and a curve of 2-drops (the B2
  argmax play note), so the land census is not a proxy for the level. The
  clause fails on this seed and the row says so.
* **Not collapsed — met on both seeds at every point:** argmax-PASS 14 /
  14 / 6 / 10 % (s0) and 18 / 20 / 21 / 18 % (s1), gap 3.55 → 1.70 and
  1.62 → 1.00, entropy 0.63–0.84; max |logit| touched the bound (5.00)
  only on seed 0 at 1024.
* **KL budget — active on both, binding more on seed 0:** 13/64 (0.20)
  vs 5/64 (0.08) updates stopped; seeds 0/1 first-update approx KL 0.33
  / 0.11. Not inert.

Behaviour counters carried: the first-8-batch sampled wins are **16/256
(seed 0) vs 137/256 (seed 1)** — seed 0's dead stretch (four all-lost
batches) did not happen on seed 1, which won from batch 3 on; pooled
153/512 = 0.299 [0.261, 0.340]. Seed 1's games are LONG at 512–1536 (47–49
turns vs seed 0's 31–40) with `attackBudgetHit` 546–597 per 100-game
battery at 512 (seed 0: 40–47): the seed-1 policy held wide boards early,
and ~5–6 consults per game priced ATTACK candidates under the reply cap;
the exactness caveat on ATTACK afterstates is largest exactly where seed
1's levels are lowest, and the row cannot separate the two.

**Against v6 on rung 0 (the LEVELSET comparison, two seeds pooled, plain
argmax both):** v6's W0Base D0 was 0.568 at 512 (two seeds pooled), 0.78
at 1,407–1,919 and 0.705 [0.638, 0.764] at 2,111 (seed 0,
`rl/artifacts/rung0/W0Base/report.txt`). C1 pooled D0 at 2048, 0.850
[0.794, 0.893], is clear of v6's 2,111 point; C1 pooled 512 (0.690
[0.623, 0.750]) is clear of v6's 512 (0.568, its interval not on file
here). Two seeds, not three: this is the strongest statement the row can
make and it is "v7 C1 is above v6's seed-0 rung-0 level at 2k on W0Base,
two seeds pooled, 200 games, plain argmax" — not a v7 level, not a claim
about other decks. Cannot: attribute anything to one flag (B8/B6
ablations owed); read the 1024 dip as anything but one seed's path;
compare with class-argmax batteries until the Phase C re-battery is in.

## 7d piece (1b) — recording: 20,735 CP7-labelled priority consults on W0Base (2026-09-13 10:00 next-session clock; WSL 03:55; branch `v7/lane-d`)

Build: the Phase B engine (CP7TeacherPlayer / `rl.agent=cp7`, 9e24145 +
this commit's compile), driver 7911 with the v7 flags. `rl/record_7d1b.sh`
→ `rl/record_cp7.sh`: 14 jobs × 100 games, seeds 7400–7413, W0Base mirror
vs the heuristic, seats alternating by episode parity, `rl.consultBudget`
300, concurrency 1, echo policy (reply ignored). Artifacts
`rl/artifacts/v7/7d1b/7d1b_s<seed>.jsonl` (gitignored), `counts.txt`,
`record_7d1b.log`, per-job `.probe.txt`. Smoke first (`rl/smoke_cp7.sh`, 4
games): hello carries `teacher:"cp7"`, every consult carries `y`,
`wire_validate` ok, faithfulness probe on the 60 consults L3 25/1 (a
not-exercised-scale artefact of 60 rows) / L4 26/0.

| counter (pooled over 1,400 games) | value |
|---|---|
| windows (priority calls on the teacher seat) | 255,655 |
| autoPassEmpty (no candidate after the filters; no consult) | 234,920 |
| manaCandsDropped | 139,734 |
| **teacherConsults = teacherLabelled** | **20,735** (14.8 per game) |
| teacherPassed (y = 0) | **0** |
| teacherOutside (y = −1) | 0 |
| teacherMultiAct | 0 |
| teacherBudgetSkipped | 0 |
| CP7 wins / losses / draws / stalls | 958 / 442 / 0 / 0 → **0.684 [0.659, 0.708]** |
| `wire_validate` on `7d1b_s7400.jsonl` | ok, 1,488 consults |

**Labelled fraction 20,735 / 20,735 = 1.00 (gate ≥ 0.9: pass).** Label
type census — the target the BC census is read against: **LAND 8,564
(41.3 %), SPELL 12,171 (58.7 %), PASS 0, ACTIVATE 0.** Offered: PASS in
every consult, LAND in 10,552, SPELL in 14,766; k = 2 in 7,122 consults,
3 in 4,684, 4 in 4,522, 5 in 2,919, 6–8 in 1,488. Two things the census
says before BC: (1) **CP7 never passes a window it can act in** on
W0Base (0 of 20,735) — so BC's target is "always play something", and
PASS is only ever the label-free alternative; a BC policy cannot learn
*when* to hold from this teacher, only *what* to play; (2) ACTIVATE is
never offered (the mana-ability filter removes every activation W0Base
has), so the priority head is trained on LAND-vs-SPELL-vs-(never)PASS.
CP7's pooled rate 0.684 replicates piece (1a)'s 0.68 [0.58, 0.76] at
n=1,400. Priority-only, as pre-registered: no atkjoint/blkjoint consults
exist in these files. Cannot: label combat; say anything about a
budgeted RL seat (the teacher sees every window, 15 consults per game
where the C1 policy makes 30–100 — the RL seat's extra consults are the
combat and target sites and the windows where it passes); generalise off
W0Base.

## 7d piece (2) — BC: CP7's type, not its card (2026-09-13 10:20 next-session clock; WSL 04:10; branch `v7/lane-d`)

`python3 rl/v7_bc.py --init /tmp/rl_7c1_s0/init.pt --out rl/artifacts/v7/7d2/bc.pt
--device cuda rl/artifacts/v7/7d1b/7d1b_s*.jsonl` (defaults: lr 1e-4, AdamW wd
0.01 on the heads, batch 32, logit bound 5, 10 % of games held out, patience 3);
`bc.log`, `census.txt` in `rl/artifacts/v7/7d2/` (bc.pt gitignored). Data:
20,735 labelled consults / 1,400 games → 18,669 train / 2,066 held-out (140
games). 188 s wall.

| epoch | train CE | train top-1 | held-out CE | held-out top-1 | held-out type agreement |
|---|---|---|---|---|---|
| 0 (init) | – | – | 1.2429 | 0.168 | 0.307 |
| 1 | 0.7119 | 0.601 | **0.7131** | **0.606** | **0.887** |
| 2–4 | 0.7092 | 0.602 | 0.7131 | 0.606 | 0.887 |

Early stop at epoch 4 (best = 1); bc.pt = epoch 1. **The copy ceiling** (the
label is one index among identical candidates — same type, afterstate row and
referent names, the B7 class key): mean log(#copies of the labelled class)
over the 20,735 consults = **0.280 nats**, and the label is the first index
of its class on **0.833** of consults (2.76 classes per consult on average).
BC stopped at 0.713 nats / 0.606 — well short of 0.280 / 0.833 — while its
type agreement is 0.887: **BC learned CP7's decision TYPE (land vs spell)
and not which card**; within the LAND / SPELL classes it does not follow
CP7's choice (which creature to cast, which land) beyond chance-of-first.
The flat CE from epoch 1 on (0.7092 to four decimals for three epochs) says
the optimiser found a type-level rule immediately and nothing further at lr
1e-4; a card-level fit is either not in this net's reach from a memoryless
consult or needs a different schedule — not settled here (a second BC with
lr 3e-4 / no early stop is the obvious follow-up, not run tonight).

Census on bc.pt (`v7_init_logits.py`, 1,101 real consults; init in the same
file for reference): **argmax-PASS 0/1070** (init 708/1070), P(PASS) 0.03,
entropy 0.58 nats, gap 3.96; argmax types LAND 224/313, SPELL 348/368,
TARGET 12/12, **ATTACK 279/279, BLOCK 207/207** — the shared candidate head
generalised "never pass" from the priority labels to the never-labelled
combat sites, so bc.pt attacks and blocks with everything offered. Land
census: P(land) at ≥ 3 lands **0.80** (argmax-land 160/219), 1.00 / 0.92 /
0.70 / 0.67 at 0 / 1 / 2 / 3 lands in play — the third land is CP7's habit
and BC has it.

**BC battery** (= the D-PPO lane's trained=0 row, `rl/artifacts/v7/7d3/`
seed 0, **fixed argmax-classes protocol**, 100 games each): **D0 0.58
[0.482, 0.672]**, D1 0.59 [0.492, 0.681], TWIN 0.57 [0.472, 0.663]; attacks
935/1013 (under 0 / over 218), blocks 855/893 (BLOCKOPT 605/697), 20.6
turns. Below CP7's 0.684 [0.659, 0.708] as pre-registered ("expected ≤
CP7"), and far above the init (0.00 at trained=0 in C1) — a type-level
"always play a land, always cast, always attack, always block" policy is
worth ~0.58 vs the heuristic on W0Base. Same-deck TWIN 0.57: no card-identity
dependence visible (it never learned card identity). Cannot: beat CP7 (it
does not); attribute the 0.58 to imitation of CP7's *choices* (the CE says
it is CP7's *types*); say anything off W0Base; separate the combat
behaviour (untrained, generalised) from the priority behaviour in the
level. What this changes for Q1: D-PPO starts from a policy that already
wins 0.58 on argmax and never passes — the dead stretch (C1 seed 0's
16/256) is the first counter to read.

## 7d L0 — the same-compute control from C1 s0 ck_2048, +1,024 vs the heuristic (2026-09-13 12:40 next-session clock; WSL 06:35; fixed argmax-classes protocol; one seed)

`rl/run_7l.sh` arm L0 = `rung0_lane.sh` with `R0_INIT` = C1 s0 `ck_2048.pt`,
budget 3072 (absolute), C1's recipe, driver 7912 / server 7950; artifacts
`rl/artifacts/v7/7l/L0/` (32 updates, KL stopped 2/32). **Two of its three
battery rows came out NA, and the cause is a race in the lane script, not
the driver:** `start_server()` appends the old `server.log` to
`server_all.log` and launches the new server with `> $OUT/server.log` *in
the background job*; that truncation happens in the child after the fork,
so the parent's first poll (`grep -q "policy server" server.log`) can still
read the OLD (training) server's ready line, return at once, and send the
three probe jobs into a server that has not bound yet - each is refused in
0.0 s (driver 7912 jobs 12-14 and 24-26, `rc=1|sec=0.0`, no connection ever
reaching the battery server, whose log is empty because the lane's
`stop_server` killed it 2 s later: `server.log` mtime 06:18:07, the NA row
06:18:09). It needs the old log to contain the ready line (so never the
first battery of a lane - the +0 row and every C1 trained=0 row were safe)
and the parent to win the fork race, which it did twice under this
night's load and never in C1's 16 batteries. Fix: truncate synchronously
(`: > $OUT/server.log`) before the launch - applied to
`rung0_lane_league.sh` now, owed to `rung0_lane.sh` when no lane runs it
(D-PPO's remaining batteries carry the same exposure; any NA row is
recovered from its `ck_<N>.pt` with `rl/fill_na_batteries.sh`, same game
seeds). The L0 points are recovered the same way (`rl/recover_L0.sh` →
`rl/battery_ck.sh` on ck_2560 / ck_3072, server 7948 / driver 7914, one at a
time under the memory rule) and appended below when they land.

| point | D0 | D1 | TWIN | sampled last-4 | argmax-PASS | gap | entropy | P(land) ≥ 3 |
|---|---|---|---|---|---|---|---|---|
| 2048 (+0) | 0.86 [0.779, 0.915] | 0.87 [0.790, 0.922] | 0.88 [0.802, 0.930] | – | 10 % | 1.70 | 0.76 | 0.72 |
| 2560 (+512) | *lane NA → recovered below* | | | 102/128 = 0.797 [0.719, 0.857] | 11 % | 2.38 | 0.66 | 0.75 |
| 3072 (+1024) | *lane NA → recovered below* | | | 111/128 = 0.867 [0.798, 0.915] | 7 % | 2.69 | 0.68 | 0.74 |

Sampled rate 0.80 → 0.87 (overlapping); third land 0.74 at 3072; not
collapsed; KL 2/32. Aside from the RLLOCK line of the block-2 server:
`wait_share=95.0%` (13,189 s waited on the server lock across 21,901
calls, 602 ms per call) - three lanes' servers and JVMs on an 11 GB box
were serialising on memory, not on the GPU (the machine swapped between
WSL 05:05 and 06:04; one training chunk took 3,810 s). L1 was stopped
before it trained (`rl/stop_7l.sh`) and restarts from the same ck_2048 on
the fixed league script once memory allows (a JVM is 3.4 GB RSS, a server
1.7 GB: D-PPO + L1 + L1's opponent server = 3 servers + 2 JVMs ≈ 12 GB, so
L1 waits for D-PPO to end).

**L0 recovered rows** (`rl/recover_L0.sh` → `rl/battery_ck.sh`, same game seeds as
the lane, fixed argmax-classes protocol, 100 games each; `rl/artifacts/v7/7l/L0_rebat/`):

| point | D0 | D1 | TWIN |
|---|---|---|---|
| 2048 (+0) | 0.86 [0.779, 0.915] | 0.87 [0.790, 0.922] | 0.88 [0.802, 0.930] |
| 2560 (+512) | **0.92 [0.850, 0.959]** | 0.92 [0.850, 0.959] | 0.84 [0.756, 0.899] |
| 3072 (+1024) | **0.91 [0.838, 0.952]** | 0.92 [0.850, 0.959] | 0.90 [0.826, 0.945] |

L0 (+1024 more episodes vs the heuristic from C1 s0 ck_2048) sits at 0.91–0.92
against the heuristic family, the +1024 intervals overlapping the +0 ones. One seed.

## Q2 pre-registration amendment — the heuristic-family batteries cannot decide Q2 (2026-09-13 13:20 next-session clock; WSL 07:15; written BEFORE L1 trains)

The control L0 is at 0.91–0.92 vs D0/D1 at +512/+1024, so a 100-game
battery of L1 against the same family could be "clear above" only at
> 0.96: the pre-registered Q2 reading (L1's D0/D1/TWIN at +1024 vs L0's)
is at the ceiling of its instrument and is **reported but cannot decide**.
Deciding comparison, added now, both arms at +1024 (ck_3072), fixed
protocol, 100 games each, `rl/hard_battery.sh`:
* **(a) head-to-head** L1 ck_3072 vs L0 ck_3072 — `rl.opponent=rl` with the
  opponent served by a second frozen eval-mode server (argmax over
  classes; the C5 league mechanism), seats alternating by episode parity;
  L1's win rate with Wilson; 0.5 [0.40, 0.60] = no difference.
* **(b) vs CP7** (`rl.opponent=cp7`, `rl.aiSkill` 6, `rl.stopTurn` 60) for
  each arm — CP7 is 0.68 vs the heuristic (piece 1a), the harder
  yardstick; the rung-0 v6 policy's 7/10 vs CP7 was never a level.
Reading: **"league helps" only if (a) is clear above 0.5 AND (b) L1 > L0
with intervals clear; otherwise "no difference shown"**. Cannot: one
seed; W0Base only; the league opponents are the policy's own ancestors
(C1 s0 ck_1024 / ck_2048) — a weak league; (b) also measures CP7's
non-heuristic play, which neither arm trained against. L0's (b) runs now
(only D-PPO s0 trains: two servers); L0's (a) needs L1's ck_3072.

## 7d D-PPO — seed 0: PPO from bc.pt with C1's recipe (2026-09-13 13:50 next-session clock; WSL 07:45; ONE seed — seed 1 owed, `rl/run_7d3.sh` resumable; fixed argmax-classes protocol)

`rl/run_7d3.sh` seed 0 (parent stopped after seed 0 by decision,
`rl/stop_7d3_parent.sh`; post-processed by `rl/wait_7d3_s0.sh`): `R0_INIT` =
`rl/artifacts/v7/7d2/bc.pt`, C1's flags, 2,048 episodes, 64 updates, KL
stopped 10/64; artifacts `rl/artifacts/v7/7d3/s0/` (no NA rows).

| point | D0 | D1 | TWIN | turns | sampled last-4 | argmax-PASS | gap | entropy | argmax-LAND ≥ 3 lands | ATTACK argmax | budget hits |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 (bc.pt) | 0.58 [0.482, 0.672] | 0.59 [0.492, 0.681] | 0.57 [0.472, 0.663] | 20.6 | – | 0 % | 3.96 | 0.57 | 0.73 | 279/279 | – |
| 512 | 0.69 [0.594, 0.772] | 0.77 [0.678, 0.842] | 0.66 [0.563, 0.745] | 21.5 | 87/128 = 0.680 [0.595, 0.754] | 2 % | 3.12 | 0.72 | 0.80 | 261/279 | – |
| 1024 | **0.50 [0.404, 0.596]** | 0.50 [0.404, 0.596] | 0.45 [0.356, 0.548] | **46.9** | 101/128 = 0.789 [0.710, 0.851] | 18 % | 3.54 | 0.71 | 0.65 | **82/279** | 284 / 287 / 284 |
| 1536 | 0.71 [0.615, 0.790] | 0.76 [0.668, 0.833] | 0.67 [0.573, 0.754] | 20.5 | 91/128 = 0.711 [0.627, 0.782] | 0 % | 3.57 | 0.72 | 0.94 | 279/279 | – |
| 2048 | **0.68 [0.583, 0.763]** | 0.73 [0.636, 0.807] | 0.72 [0.625, 0.799] | 21.9 | 90/128 = 0.703 [0.619, 0.775] | **0 %** | 3.58 | 0.72 | 0.95 | 279/279 | 3 / 3 / 7 |

("argmax-LAND ≥ 3 lands" = `argmax_land_frac` of the land census; its
`p_land_mean` printed 0.801 at every checkpoint including bc.pt, which is a
tool artefact to look at, not a reading. max |logit| sat on the bound 5.00
at every point.)

**Q1 on one seed — "IL hurts", as pre-registered, one seed.** D-PPO s0's
D0 at 2048, 0.68 [0.583, 0.763], is clear BELOW C1's pooled two-seed 0.850
[0.794, 0.893] (plain argmax; C1 s0 under the fixed protocol is 0.86
[0.779, 0.915], also clear). At 512 D-PPO's 0.69 [0.594, 0.772] overlaps
C1's pooled 512 (0.690 [0.623, 0.750]) — no faster start. The one-seed
caveat is real: C1's own seed 1 dipped to 0.49 at 1024 and recovered to
0.85 by 2048; D-PPO s0 dipped to 0.50 at 1024 and recovered only to 0.68.
Two seeds decide; this seed says IL hurt.

What BC seeded and what PPO did with it:
* **The dead stretch is gone:** first-8-batch sampled wins **163/256**
  (C1 s0 16/256, s1 137/256) — BC's "always act" start wins from batch 1
  (0.59, 0.44, 0.66 ...). That is the one thing BC unambiguously bought.
* **The sampled curve is flat at ~0.70 from 512** (0.68 / 0.79 / 0.71 /
  0.70) while C1's seeds reached 0.84–0.86; the argmax level never passed
  0.71 after 512. Chosen-type counts per update (PASS/LAND/SPELL/ACT/TGT/
  ATK/BLK): update 1 14/54/88/0/2/52/55 → update 64 93/236/342/0/19/182/237
  — the policy's sampled behaviour stayed BC-shaped throughout (lands and
  spells whenever offered, attack and block on most offers).
* **Rigidity, not collapse in the 7a sense:** entropy 0.72, gap 3.6, but
  argmax-PASS **0 %** at 1536 and 2048 (below the 5 % floor of the "not
  collapsed" clause — the clause FAILS at those points and at ck_0; the
  bc.pt census was 0 % too), LAND 301/313 and ATTACK 279/279 / BLOCK
  207/207 at 2048: it plays a land on every offer, attacks with every
  offered set, blocks on every offer; games last 22 turns (C1 s0/s1:
  31–35). The 1024 dip is the exception that shows the mechanism: at
  ck_1024 the argmax stopped attacking (82/279) and passed 18 %, games
  went to 47 turns and the level fell to 0.50 — the same "stop attacking,
  stall" shape as C1 s1's 1024 dip — then it snapped back to the BC
  attack-everything rule and the level came back only to 0.68–0.71.
* **The candidate mechanism** (stated as the hypothesis for seed 1, not
  a finding): BC installed a saturated type-level prior (logits on the
  bound, gap 3.6 nats, PASS never) that PPO at lr 3e-5 under the KL
  budget (10/64 stopped) could not unlearn — C1's from-scratch seeds
  found selective attacking (C1 s0 attacks 1429/7267 offers at 1024 and
  1258/4179 at 1536 in its batteries; D-PPO 279/279 in the census) and win 0.85; the
  BC-started seed never left "attack everything". Third land: 0.95 at
  2048 (CP7's habit, kept).
* Attack budget: 3 / 3 / 7 hits at 2048 (short games, small boards) —
  the exactness caveat is small here.

Cannot: call this the two-seed Q1 answer (seed 1 owed); separate BC's
type-only fit (piece 2: CE 0.71 vs the 0.28 ceiling) from "IL as such" —
a card-level BC might seed differently; separate the priority-only labels
(combat heads never imitated, then generalised to attack-everything) from
the imitation itself; generalise off W0Base. Pre-registered cannots stand
(consult budget, k-copy bias — under the fixed protocol here).

## C1 — correction in the open: the two seeds' ck_2048 under the FIXED argmax-classes protocol (2026-09-13 14:20 next-session clock; WSL 08:15)

`rl/rebattery_c1.sh` / `rl/chain_s1rebat_then_7l.sh` → `rl/battery_ck.sh` (same
game seeds as the lane's batteries, 100 games per opponent; rows in
`rl/artifacts/v7/7c1/rebattery/s<seed>/rows.txt`):

| seed, ck_2048 | protocol | D0 | D1 | TWIN |
|---|---|---|---|---|
| s0 | plain argmax (lane) | 0.85 [0.767, 0.907] | 0.85 [0.767, 0.907] | 0.88 [0.802, 0.930] |
| s0 | argmax over classes | 0.86 [0.779, 0.915] | 0.87 [0.790, 0.922] | 0.88 [0.802, 0.930] |
| s1 | plain argmax (lane) | 0.85 [0.767, 0.907] | 0.82 [0.733, 0.883] | 0.88 [0.802, 0.930] |
| s1 | argmax over classes | 0.86 [0.779, 0.915] | 0.83 [0.745, 0.891] | 0.89 [0.814, 0.937] |
| **pooled, fixed protocol** | argmax over classes | **172/200 = 0.860 [0.805, 0.901]** | 170/200 = 0.850 [0.794, 0.893] | 177/200 = 0.885 [0.833, 0.922] |

The fix moves nothing at 2048 (every paired difference is 0–2 games out of
100): B7's prediction that the plain argmax was biased against k-copy
actions is not visible at this level of training — by 2048 the policy's
argmax on land-copy windows is already a land (census argmax-LAND 0.72 /
0.38 at ≥ 3 lands is about *whether*, not *which copy*). The C1 two-seed
level stands at **0.86 [0.805, 0.901]** under the fixed protocol (0.850
[0.794, 0.893] plain), and the D-PPO seed-0 Q1 reading is unchanged: 0.68
[0.583, 0.763] is clear below both. The 512/1024/1536 re-batteries are
still owed (resumable, `rl/rebattery_c1.sh`, after the lanes). Cannot: say
the flag is inert in general (the B7 mechanism lives in early checkpoints
and in bc.pt-like policies, not tested here).

## 7d Q2 — L1 (league) vs L0 (heuristic) from C1 s0 ck_2048, +1,024 episodes each (2026-09-13 16:30 next-session clock; WSL 11:25; ONE seed each; fixed argmax-classes protocol)

L1 = `rl/rung0_lane_league.sh` (frozen opponents C1 s0 ck_1024 for block 0,
ck_2048 for block 1; argmax over classes, eval-mode hello), L0 =
`rung0_lane.sh` vs the heuristic; both C1's recipe, driver 7912, artifacts
`rl/artifacts/v7/7l/{L0,L1}/`, L0's +512/+1024 rows recovered (`L0_rebat/`).
Hard batteries `rl/artifacts/v7/7l/hard/` (`rl/hard_battery.sh`).

| point | L0 D0 | L0 D1 | L0 TWIN | L1 D0 | L1 D1 | L1 TWIN | L1 turns / under-over |
|---|---|---|---|---|---|---|---|
| 2048 (+0) | 0.86 [0.779, 0.915] | 0.87 [0.790, 0.922] | 0.88 [0.802, 0.930] | 0.86 [0.779, 0.915] | 0.87 [0.790, 0.922] | 0.88 [0.802, 0.930] | 34.9 / 466-192 |
| 2560 (+512) | 0.92 [0.850, 0.959] | 0.92 [0.850, 0.959] | 0.84 [0.756, 0.899] | 0.87 [0.790, 0.922] | 0.88 [0.802, 0.930] | 0.88 [0.802, 0.930] | 36.4 / 420-52 |
| 3072 (+1024) | **0.91 [0.838, 0.952]** | 0.92 [0.850, 0.959] | 0.90 [0.826, 0.945] | **0.68 [0.583, 0.763]** | 0.66 [0.563, 0.745] | 0.58 [0.482, 0.672] | 44.5 / 594-34 |

| deciding battery at +1024 (ck_3072), 100 games | L0 | L1 |
|---|---|---|
| (b) vs CP7 (aiSkill 6) | **80/100 = 0.80 [0.711, 0.867]** (6 losses, 14 stalls, 44 turns) | **67/100 = 0.67 [0.573, 0.754]** (27 losses, 6 stalls, 39 turns) |
| (a) head-to-head, L1's rate | – | **76/100 = 0.76 [0.668, 0.833]** (2 losses, **22 stalls**, 46 turns) |

Sampled league curve (TRAIN lines, L1): block 0 vs ck_1024 (updates
65–80) **0.00–0.09** on every batch; block 1 vs ck_2048 (81–96) 0.34 → 0.78
(0.34, 0.47, 0.53, 0.34, 0.31, 0.47, 0.72, 0.72, 0.66, 0.41, 0.72, 0.69,
0.75, 0.66, 0.78, 0.78). The block-0 zeros cannot be separated into losses
and turn-cap stalls: the lane discarded the per-job `RL|summary` lines
(fixed in both lane scripts after this run: `jobs.log`); the 40-turn
boards of ck_1024 (C1 s0's 1024 point was 40.3 turns) make stalls the
likely reading, not losses. Census: argmax-PASS 12 % → 19 %, gap 1.59 →
3.07, entropy 0.80 → 0.55, argmax-LAND at ≥ 3 lands 0.81 / 0.81; KL 4/32.

**Reading against the pre-registration (one seed):**
* Heuristic family (reported, cannot decide): L1's +1024 D0 0.68 [0.583,
  0.763] is clear **below** L0's 0.91 [0.838, 0.952] and below L1's own
  +0 / +512 (0.86 / 0.87): **a regression, not "flat"** - L1 got worse
  against D0, D1 and TWIN during block 1 while its sampled rate against
  its frozen ancestor rose 0.34 → 0.78; games went to 44.5 turns with
  under-attacks 594 vs 34 over (it stopped attacking into the heuristic).
* (a) head-to-head: L1 beats L0 0.76 [0.668, 0.833] - clear above 0.5 -
  with only 2 losses and **22 stalls** at 46 turns: what it learned
  against ck_2048 transfers to ck_2048's sibling L0 (same ancestor, +1024
  vs the heuristic), and a quarter of those games hit the turn cap.
* (b) vs CP7: L1 0.67 [0.573, 0.754] vs L0 0.80 [0.711, 0.867] - L1
  below, intervals overlapping (L0's lower bound 0.711 < L1's upper 0.754):
  not clear, and pointing down.
* **Verdict: NOT "league helps"** (it needed (a) clear above 0.5 AND (b)
  L1 clear above L0; (b) fails). On the CP7 yardstick "no difference
  shown" (one seed, n=100, L1 below); on the heuristic family "league
  hurts" (clear). The whole pattern - wins against the family it trained
  against (its ancestors and their sibling), loses ground against every
  opponent it did not - is the self-play overfit signature on a
  two-ancestor league whose opponents are the policy's own line.

Cannot: one seed per arm (no level, only "clear of" at n=100); a
two-ancestor league of the policy's own ancestors (weak, unweighted
opponent sampling: block 0 = ck_1024, block 1 = ck_2048, no PFSP); W0Base
only; separate "a stronger opponent" from "a different opponent"; read
the block-0 zeros as losses (stalls likely, not recorded); the head-to-head
stalls (22) are a quarter of its games - the 0.76 is a rate over games
including 22 draws at the cap, reported as such. The H2H opponent server
and the lane's league servers use argmax over classes; the training-time
opponent was argmax too (eval hello) - a deterministic opponent, which is
part of why one policy can overfit it.

## 7d Q1 — D-PPO two seeds vs C1 two seeds: "IL hurts" at n=200, marginally (2026-09-13 18:55 next-session clock; WSL 13:50; fixed argmax-classes protocol on both sides)

`rl/run_7d3.sh` seeds 0 and 1 (`rl/artifacts/v7/7d3/s{0,1}/`; seed 1: 64
updates, KL stopped 2/64, no NA rows), both from `bc.pt`, C1's recipe.
`python3 rl/summ_7c1.py rl/artifacts/v7/7d3/s0 rl/artifacts/v7/7d3/s1`.

| point | D-PPO s0 D0 | D-PPO s1 D0 | **D-PPO pooled D0** | **C1 pooled D0 (fixed protocol)** | pooled D1 (D-PPO / C1) | pooled TWIN (D-PPO / C1) |
|---|---|---|---|---|---|---|
| 512 | 0.69 [0.594, 0.772] | 0.80 [0.711, 0.867] | 149/200 = 0.745 [0.680, 0.800] | 138/200 = 0.690 [0.623, 0.750] | 0.790 [0.728, 0.841] / 0.720 [0.654, 0.778] | 0.695 [0.628, 0.755] / 0.680 [0.612, 0.741] |
| 1024 | 0.50 [0.404, 0.596] | 0.70 [0.604, 0.781] | 120/200 = 0.600 [0.531, 0.665] | (s0 0.79 fixed; s1 re-battery pending) | – | – |
| 1536 | 0.71 [0.615, 0.790] | 0.76 [0.668, 0.833] | 147/200 = 0.735 | (pending) | – | – |
| 2048 | 0.68 [0.583, 0.763] | 0.81 [0.722, 0.875] | **149/200 = 0.745 [0.680, 0.800]** | **172/200 = 0.860 [0.805, 0.901]** | 0.755 [0.691, 0.809] / 0.850 [0.794, 0.893] | 0.745 [0.680, 0.800] / 0.885 [0.833, 0.922] |

(C1's fixed-protocol 512 rows are the re-battery's: s0 0.78, s1 0.60 - the
plain-argmax lane rows were 0.77 / 0.61. The 1024/1536 rows of the
re-battery were still running when this was written; the 2048 comparison
is complete on both sides.)

**Pre-registered reading at 2048: "IL hurts" — D-PPO's pooled D0 0.745
[0.680, 0.800] is clear below C1's 0.860 [0.805, 0.901], by 0.005 of
interval.** That is the reading as written, and it is marginal: one more
D-PPO win in 200 games (0.750 [0.685, 0.805]) would overlap. D1 and TWIN
say the same with more room (0.755 vs 0.850, 0.745 vs 0.885 - both clear).
At 512 the "faster start" clause is not met either: 0.745 vs 0.690,
overlapping (D-PPO numerically above). Per seed at n=100 the two D-PPO
seeds disagree in magnitude (s0 0.68, s1 0.81) where C1's two agree (0.86,
0.86): s1's 0.81 [0.722, 0.875] alone overlaps C1's seeds; the verdict
comes from pooling and from s0.

Behaviour, both seeds (the mechanism, still a hypothesis at two seeds):
* **BC removes the dead stretch on both seeds:** first-8-batch sampled
  wins 163/256 (s0) and 165/256 (s1) - pooled 328/512 = 0.641 [0.598,
  0.681] - vs C1's 16/256 and 137/256.
* **The clone's argmax never moved on seed 1:** the ck_2048 type census of
  s1 is IDENTICAL to bc.pt's on the 1,101-consult census set (PASS 0/1070,
  LAND 224/313, SPELL 348/368, ATTACK 279/279, BLOCK 207/207, gap 3.86,
  entropy 0.72, argmax-LAND at ≥ 3 lands 0.73) while its battery rose 0.58
  → 0.81; s0's moved to LAND 301/313 / SPELL 271/368 (attack/block
  unchanged at all-offers). Whatever PPO changed lives in the sampled
  policy and in decisions off this census set (combat sets, targets), not
  in the argmax on these windows.
* **Over-attacking, C1's opposite:** at 2048 the D0 battery's under/over
  counts are 46/283 (s0) and 138/371 (s1) - the clone attacks into bad
  boards - where C1's seeds under-attack (458/178, 337/163); ATKOPT
  413/744 (s0), 363/1089 (s1); games 22 / 30 turns vs C1's 31–35. The
  type-level clone of a teacher that "always acts" carried "always
  attack" into the combat head it was never trained on, and PPO under the
  KL budget (10/64, 2/64 stopped) did not undo it in 2,048 episodes.
* Not collapsed in the 7a sense (entropy 0.72, gap 3.6–3.9) but rigid:
  argmax-PASS 0 % at 1536/2048 on both seeds (the census clause's 5 %
  floor fails, as it did for bc.pt); max |logit| on the bound throughout.

Cannot: call it more than "IL hurts at n=200 by a hair" (two seeds, the
margin is one game); generalise off W0Base or past CP7 skill 6 as the
teacher; separate the three confounds the pre-registration named -
priority-only labels (combat never imitated, then generalised to
attack-everything), the type-level clone (CE 0.71 vs the 0.28 ceiling:
CP7's card choices were never learned), and the consult budget - from
"imitation as such"; a card-level clone or joint-site labels could seed a
different start. The one thing IL bought that survives every caveat is
the first 256 episodes (0.64 vs 0.30 sampled).

**C1 early checkpoints under the fixed protocol (`rl/rebattery_c1.sh`, done 2026-09-13 18:44Z; same game seeds as the lane):**

| seed | point | plain argmax (lane) D0 | argmax over classes D0 | D1 / TWIN (classes) |
|---|---|---|---|---|
| s0 | 512 | 0.77 [0.678, 0.842] | 0.78 [0.689, 0.850] | 0.83 / 0.80 |
| s0 | 1024 | 0.81 [0.722, 0.875] | 0.79 [0.700, 0.858] | 0.83 / 0.79 |
| s0 | 1536 | 0.83 [0.745, 0.891] | 0.88 [0.802, 0.930] | 0.84 / 0.82 |
| s1 | 512 | 0.61 [0.512, 0.700] | 0.60 [0.502, 0.691] | 0.61 / 0.56 |
| s1 | 1024 | 0.49 [0.394, 0.587] | 0.50 [0.404, 0.596] | 0.53 / 0.44 |
| s1 | 1536 | 0.78 [0.689, 0.850] | 0.80 [0.711, 0.867] | 0.86 / 0.78 |

Every fixed-protocol point sits inside its plain-argmax interval: **the
protocol correction moves nothing at any C1 point**, early checkpoints
included — B7's k-copy prediction is not visible on these policies at
n=100. The C1 rows stand as levels under either protocol.

## Phase 8 pre-registration — a real deck (8a, Dimir) and a diverse cross-deck league (8b) (2026-09-13 17:20 next-session clock; WSL 17:15; runbook `rl/PHASE8-DECKS.md`; written BEFORE any 8a battery)

Why: every v7 number so far is W0Base (a mono-white creature mirror) and
the one league tried (L1) was two frozen ancestors of the policy itself,
which it overfit to. Two questions, in order: **Q3** does the C1 recipe
train on BenchDimir (removal, instants, payment choices) and where does it
land against v6's Dimir result; **Q4** does a league of diverse strategies
across decks (mono-white aggro, Dimir midrange, Burn) improve a W0Base
policy where the ancestors-only league hurt it.

Preparation landed with this row (Phase A of the runbook): the Dimir
census set `7c_BenchDimir_{p1,p99,sf}.jsonl` (903 consults, 8 games per
echo policy, driver 7911); `rl/v7_land_census.py --type SPELL` (P(cast)
and argmax-SPELL by lands in play; LAND output unchanged); the league
lane's `R0_OPP_SPEC="kind:arg:deck,..."` (heuristic / cp7 skill 6 / rl
frozen checkpoint, the opponent's deck per entry, one entry per block in
turn, `R0_OPP|` per block; `-Drl.oppDeck` carries the opponent's deck and
the consults' `v7_opp_deck_name` carries that deck's cards — checked on a
4-game W0Base-vs-BenchDimir echo job, `wire_validate` ok); the cross-deck
suite `rl/battery_xdeck.sh` (six rows: vs the heuristic and vs CP7, each on
W0Base / BenchDimir / BenchBurn, 100 games per row, fixed argmax-classes
protocol, stalls reported, one server + one JVM). Every battery in Phase 8
is under the fixed protocol (`--argmax-classes` on the serving path).

Reference points: v6 Dimir (`rl/DIMIR-V6-2K-RESULT.md`, entattn, one seed,
D0 and TWIN = two samples of the same matchup): D0 **.555 [.486, .622]** at
1024, .585 at 2048; D1 .290 at 1024. v7 C1 on W0Base: D0 0.86 [0.81, 0.90]
pooled 2 seeds at 2048; L0 (+1024 vs the heuristic from C1 s0 ck_2048)
0.91 vs D0, 0.80 vs CP7; L1 (ancestors league) 0.68 vs D0, 0.67 vs CP7.

**8a — Dimir** (`rl/run_8a.sh`): the C1 recipe exactly (lr 3e-5, 1 epoch,
logit bound 5, AdamW wd 0.01 on the heads, `--adv-norm auto --target-kl
0.02 --argmax-classes`, mana-ability filter + attack-budget build) on
`rung0_lane.sh BenchDimir BenchDimir 1024 <seed>`, seeds 0 then 1,
batteries at 512 and 1024 (D0 / D1 / TWIN = a second D0 sample, 100 games
each), LAND + SPELL + type census on ck_512 / ck_1024 over the Dimir census
set, `jobs.log` kept (stalls per chunk), the suite on each ck_1024.
Readings:
* **Trains on Dimir** if the pooled two-seed D0 at 1024 (200 games) is
  clear above 0.5 AND the sampled last-4-batch rate at 1024 is clear of
  the first-4 (per seed, then pooled).
* **vs v6**: whether the pooled D0 interval at 1024 is above / overlapping
  / below v6's .555 [.486, .622] (one seed, 100 games, D0 alone; v6's
  D0+TWIN pooled .478 at 1024 is the second yardstick). Parity is a
  finding: v6 needed a deck-specific encoder, v7 is the deck-agnostic one.
* **Not collapsed** as in C1, at 512 and 1024: argmax-PASS in [5 %, 90 %],
  gap > 0.5, entropy > 0.3, max |logit| inside the bound (on the bound =
  clipping, carried as in C1).
* **Behaviour** (counters, not a bar): P(land) at >= 3 lands (the third
  land, 0.5 bar as in C1), P(cast) by lands (SPELLCENSUS), the TARGET
  census (does removal get pointed at creatures), the D0 battery's
  under/over and BLOCKOPT, turns per game, stalls.
* **Throughput**: episodes per hour in the first 512 (the runbook
  expected ~3-4x slower than W0Base from 126 consults per game; the echo
  recordings show ~37 consults per game, so the estimate is open); if a
  seed to 1024 exceeds 6 h the run drops to one seed and says so.
Cannots: beat v6 at 2048 (not run); the payment sub-consult is still the
engine's; CP7's Dimir strength is not calibrated (the suite gives it as a
by-product); one deck says nothing about Burn; two seeds at 100 games per
point give a level, not a curve.

**8b — diverse league** (`rl/run_8b.sh`): **L2** = L0 ck_3072 (the W0Base
policy after C1 + 1024 heuristic episodes) continued +1024 episodes on
W0Base with `R0_OPP_SPEC` rotating per 256-block (`R0_EVERY=256`, four
blocks, batteries at every block): `heuristic::BenchDimir.dck`,
`cp7::BenchBurn.dck`, `rl:<8a s0 ck_1024>:BenchDimir.dck`,
`heuristic::BenchBurn.dck`. **Control = L0** (already run: the same
checkpoint +1024 vs the heuristic on W0Base; its ck_4096 does not exist,
so the control is L0 ck_3072 itself = the same starting point +0, and the
comparison is "did the league move the suite"). Yardstick = the suite on
L0 ck_3072 and on L2 ck_4096 (600 games each, pooled and per row) + the
home battery (D0 / D1 / TWIN on W0Base) + head-to-head L2 vs L0 ck_3072
(100 games, stalls separate, `rl/hard_battery.sh` H2H path).
Readings:
* **Diverse league helps** if L2's pooled suite rate (600 games) is clear
  above L0 ck_3072's AND L2's home D0 is not clear below L0's +1024 row
  (0.91 [0.838, 0.952]).
* **Hurts** if the pooled suite is clear below L0's.
* Else "no difference shown at n=600" — and then the per-row table says
  which rows moved (a cross-deck gain paid for by a home loss is a
  finding, not a null).
Cannots: one seed; the pool is fixed-strength (no PFSP, no refresh); the
trainee plays one deck (deck-general play is 8c); CP7 on Burn is CP7's
Burn, not a trained Burn policy; L2's +1024 on mixed opponents is not
compute-matched to L0's +1024 on the heuristic in *games against the
heuristic*, only in episodes; the head-to-head is the L1 instrument and
carries its stall caveat.

**8c (only if 8a "trains on Dimir" and time remains)**: L2d = 8a s0
ck_1024 continued +1024 on BenchDimir with the same rotating spec (the
W0Base entry = `rl:<L0 ck_3072>:W0Base.dck`), against its own control =
8a s0 ck_1024 continued +1024 vs the heuristic on BenchDimir, same
yardstick (suite + home battery + head-to-head). If not run, the reason is
written in the runbook STATE and here.

Pre-stated, what none of this can move: the C1 W0Base level (0.86) and the
Q1/Q2 verdicts; the attack-budget caveat (`attackBudgetHit` carried); the
update cost (58 ms per stored consult).

**Amendment (2026-09-13 17:40 next-session clock; decided by the user
before any Phase B result was read; development-phase budget).** Games
per row stay at 100 (the project rule; n=100 is already +-0.09); the
NUMBER of rows is cut:
1. **8a**: at 512 only D0 (heuristic on BenchDimir); at 1024 D0 and D1;
   TWIN on Dimir is dropped entirely (it is a second D0 sample, not a
   second matchup) — the lane's `R0_ROWS="D0"` / `R0_ROWS_FINAL="D0 D1"`
   knobs (a skipped row prints `LB=skip`). Seed 1 runs only if seed 0's
   1024 reading is worth confirming: clear above 0.5, or inside v6's
   [.486, .622]; the decision is stated in the 8a row. With one seed the
   "trains on Dimir" reading is read on 100 games (a level, not the
   pooled 200 the original text asked for) and says so.
2. **The cross-deck suite is four rows**: the heuristic on W0Base /
   BenchDimir / BenchBurn + CP7 on the checkpoint's home deck only
   (`rl/battery_xdeck.sh` default `ROWS`; 400 games per suite).
3. **8b**: one battery row per block (D0 on the home deck, `R0_ROWS="D0"`),
   the four-row suite on L2's final checkpoint (labelled ck_4096 in the
   lane's absolute count = L0 ck_3072 + 1,024) and on L0 ck_3072, plus
   the head-to-head (`SKIP_CP7=1` in `rl/hard_battery.sh`: no duplicate
   CP7 row). The "helps / hurts" readings are read on the pooled 400-game
   suites instead of 600.
Everything else in the pre-registration stands.

## 8a — seed 0 interim at 512 episodes: the recipe collapses to "land, pass" on Dimir (2026-09-13 18:55 next-session clock; WSL 17:50; seed 0 still running to 1024; not the 8a row)

Read from `/tmp/rl_8a_s0/` while the lane runs (`rl/run_8a.sh`, C1's recipe
on `rung0_lane.sh BenchDimir BenchDimir 1024 0`, amended rows: D0 only at
512). Recorded now because the 512 point is a behaviour finding, not a
level to wait for.

**Battery at 512** (100 games, heuristic on BenchDimir, fixed protocol):
**D0 0/100 = 0.000 [0.000, 0.037]**, 16.6 turns, 0 stalls, `attacks 0/0`,
`blocks 0/0` — the agent had NO attack and NO block opportunity in 100
games: it never had a creature. 124 consults and 157 windows per game
against **3.6 actions per game** (its lands). At trained=0 the same
battery was also 0/100 but with attacks 0/90 and blocks 1/56: the random
init did cast creatures; the trained policy does not.

**Sampled curve, seed 0** (64-episode jobs, `jobs.log`; TRAIN lines):

| job | episodes | wins | stalls | games/s | consults/game | KL-stopped (updates) |
|---|---|---|---|---|---|---|
| 1 | 64 | 3 | 0 | 0.68 | 51 | 4 of 1–8 |
| 2 | 128 | 0 | 1 | 0.37 | 84 | |
| 3 | 192 | 0 | 0 | 0.23 | 115 | |
| 4 | 256 | 0 | 0 | 0.19 | 143 | |
| 5–8 | 512 | 0, 0, 0, 0 | 0, 4, 3, 1 | 0.19–0.20 | 132–150 | 0 of 9–16 |

3/512 sampled wins; entropy 0.18–0.33 on updates 7–10, max |logit| 4.79;
`update_s` 70–90 s for ~4,500 stored consults (~18 ms per consult — the
5d figure was 58 ms). Consults per game rose 51 → 150 while the policy
lost: the losing Dimir policy is consulted MORE (every priority window on
a board it does nothing with), not less.

**Census at `ck_512`** (the Dimir census set, 903 consults):
`INITLOGITS argmax_type PASS=554/790 LAND=190/221 SPELL=0/257 ACTIVATE=0/210
TARGET=112/112 ATTACK=0/111 BLOCK=47/47`; argmax-PASS when another
candidate exists 489/838 = 58 %, mean P(PASS) 0.61, entropy 0.37, gap 3.09.
LAND census: argmax-land 24/24, 27/27, 24/24, 30/30 at 0–3 lands, 0.79 at
≥ 3 (P(land) 0.75). **SPELL census: argmax-SPELL 0 of 257 consults that
offer a spell; P(any SPELL) 0.000 / 0.001 / 0.003 / 0.010 at 1–4 lands,
P(PASS) on those consults 0.67–0.999.** The policy plays every land it
is offered and casts nothing, ever; TARGET 112/112 and BLOCK 47/47 are
argmax on windows it never reaches in play (no spell → no target, no
creature → no block).

**Reading against the pre-registration (interim, one seed, 512 only):**
* "Not collapsed" clauses at 512 — all four hold as written (58 % in
  [5, 90], gap 3.09, entropy 0.37, logits 4.79 < 5). The clauses were
  written for W0Base, where "PASS vs a creature" is the collapse axis;
  on Dimir the axis is SPELL vs PASS, and on that axis the policy IS
  collapsed: argmax-SPELL 0/257. The 8a row will read the census clause
  AND the SPELL census; this paragraph pre-states that the SPELL census
  (argmax-SPELL > 0 when a spell is offered at ≥ 2 lands) is the deciding
  behaviour counter for "not collapsed on Dimir", stated before the 1024
  point is read.
* Mechanism (hypothesis, the B2/C1 signature seen from the spell side):
  after update 1 (3 wins in 64) every batch is all-lost; `--adv-norm auto`
  does not centre a constant-outcome batch, every advantage is negative,
  and the actions the policy took most (its spells) are pushed down
  hardest; PASS inherits the mass; the board empties, games shorten (20 →
  17 turns) and the win probability of a passing policy against the
  heuristic on Dimir is ~0 — no update 9 recovery as on W0Base (where a
  random-ish creature deck still wins 10–30 % of games). The value head
  should absorb a constant −1 return and zero the advantages eventually;
  whether it does by 1024 is what the next point reads.
* Throughput: ~7 min per 64-episode job in the dead stretch (5.3 min of
  play at 0.2 games/s + 80 s update); 1024 episodes ≈ 2 h with batteries
  — under the 6 h bar; seed 1 is a decision, not a cost problem.

**Pre-stated before the 1024 point:** if D0 at 1024 is still 0/100 with
argmax-SPELL 0 on the census, the 8a row reads "does not train on Dimir
from scratch in 1,024 episodes" (a failed gate, not a moved bar) and
seed 1 is NOT run (nothing to confirm at 0/100 — the amendment's rule).
One follow-up arm, pre-registered here and run only after 8b: **8a-e** =
C1's recipe + `--ent-coef 0.01` (the lane's existing knob; the only lever
that acts on the SPELL-vs-PASS collapse without changing the credit
path), one seed to 512, read on the SPELL census (argmax-SPELL > 0) and
the D0 battery (> 0/100) only; it cannot give a level or a v6
comparison. Other levers (batch-centred advantages = B2, a BC warm start
= D-PPO, reward shaping) are named, not run.

**Correction, 15 minutes later (before the 1024 point):** `--ent-coef` defaults to 0.01 in `policy_server.py` (`ENT_COEF = 0.01`; the B4 arm of 7a raised it to 0.1), so C1 — and 8a — already carry 0.01, and "8a-e = C1 + `--ent-coef 0.01`" is the 8a recipe itself: void, withdrawn. The 7a record says the entropy lever alone does not stop this kind of collapse (B4 at 0.1 rode B1's PASS rail to 0/128 with attacks 0/0). The replacement follow-up, pre-registered here with the same scope (one seed to 512, after 8b, read on the SPELL census and a D0 > 0/100 only): **8a-b = C1's recipe with `--adv-norm batch`** — batch centring is the direct antidote to the hypothesised mechanism (an all-lost batch centres to zero advantage instead of pushing every taken action down), so a policy that keeps casting under 8a-b and stops under 8a confirms the mechanism; B2's own failure mode (batch centring manufactures "early good, late bad" once batches mix outcomes, and unlearned the third land on W0Base) is the pre-stated cost and is read on the LAND census. It cannot give a level or a v6 comparison.

**Amendment 2 — the two-tier game budget (2026-09-13 19:10 next-session
clock; decided by the user; replaces the "100 games per row" clause of
Amendment 1, everything else there stands).** Interim battery points
(every point before a run's final one) and every cross-deck suite row
drop to **50 games**, labelled **development probe** with their (wider)
Wilson interval, used for go / no-go only and never called a level; a
run's **final point stays at 100 games per row** and is the only one
called a level; a suite is read **pooled across its four rows (200
games)** as the comparison, its per-row numbers are descriptive. Lane
knob: `R0_EVAL_G_INTERIM=50` (both lane scripts; the `R0|` row now
carries `games=N`); suite knob: `G=50` in `rl/battery_xdeck.sh`.

## 8a — seed 0: STOPPED at 512 by decision; the C1 recipe as-is does not train on Dimir (2026-09-13 19:15 next-session clock; WSL 18:00; one seed; 1024 not run; seed 1 not run)

Decision (user, at the 512 reading): the interim paragraph above is
decisive for "the C1 recipe as-is on BenchDimir" — D0 0/100 [0.000,
0.037], P(SPELL) ≤ 0.01 at every land count, argmax-SPELL 0/257, a
land-and-pass rail with no creature in 100 games — and the 1024 point
cannot rescue an argmax policy that never casts. `rl/stop_8a.sh` stopped
the lane at 512 + 1 job (576 episodes played, 19 updates, KL-stopped
4/19; the ninth job had 1 win in 64 with 175 consults per game). Seed 1
is not run (nothing to confirm at 0/100 — Amendment 1's rule).
Artifacts: `rl/artifacts/v7/8a/s0/` (battery.txt, train_lines.txt,
jobs.log, census_all.txt at ck_512, probe files, STOPPED.txt; ck_512.pt
on disk, not committed).

**Readings against the pre-registration:**
* **Trains on Dimir — NO** (failed gate, not a moved bar): D0 0/100 at
  512 is below 0.5 with the whole interval; the sampled curve is 3/64 then
  0/64 x 7 then 1/64 — the last-4 rate is not clear of the first-4, it is
  below it.
* **vs v6 — not made as pre-registered**: the comparison point was 1024
  (not reached), and v6 has no valid 512 level (its 0 / 512 / 1024
  progression was 10-game probes, retracted in `rl/DIMIR-V6-2K-RESULT.md`
  §0). What can be said: 0/100 at 512 is clear below v6's 1024 interval
  [.486, .622], and a policy that never casts does not reach it at 1024
  either — the deck-agnostic v7 recipe from scratch is below the
  deck-specific v6 on this deck, with the caveat that the points differ.
* **Not collapsed — the four clauses hold and the policy is collapsed**:
  argmax-PASS 58 %, gap 3.09, entropy 0.37, max |logit| 4.79 (all inside
  the clauses); SPELL census argmax-SPELL 0/257, P(SPELL) ≤ 0.010. The
  clauses were built on W0Base's PASS-vs-creature axis; on Dimir the
  collapse axis is SPELL-vs-PASS and the clauses do not see it. Recorded
  as a limitation of the clause set (the SPELL census is the Dimir
  counter from here on), not as a pass.
* **Behaviour**: lands played at every land count (argmax-land 0.79 at
  ≥ 3, P(land) 0.75 — the third land is not the problem here); P(cast)
  ~0; TARGET 112/112 and BLOCK 47/47 on census windows the played policy
  never reaches; 3.6 actions per game against 124 consults; games 16.6
  turns (the heuristic's creatures kill an empty board on schedule).
* **Throughput** (the one thing the runbook asked to measure and write
  down): 0.68 games/s on the first job (51 consults per game, 20.5
  turns) falling to 0.15–0.20 games/s as the rail formed (132–175
  consults per game); ~7 min per 64-episode job in the rail; `update_s`
  70–90 s for ~4,500 stored consults (~18 ms per consult). A 1024-episode
  seed would have been ~2 h — under the 6 h bar; cost was not the reason
  to stop.

**Cannot**: say the recipe cannot train on Dimir with more episodes (not
run: the value head might zero the advantages later); say anything about
a second seed (the collapse is deterministic in mechanism, not shown
twice); separate the three confounds — the all-lost-batch mechanism
(8a-b tests it), the KL budget at 0.02 (8a-c, if 8a-b rails), and the
deck itself (a 20-land midrange deck with no creature on turns 1–2 means
the random init loses every game, so the first batch has no positive
signal at all: the W0Base recipe's first update saw 3–9 % wins).

## 8a-b pre-registration — the mechanism test: C1's recipe + `--adv-norm batch` on Dimir (2026-09-13 19:15 next-session clock; WSL 18:00; written at launch, before any 8a-b probe)

`rl/run_8ab.sh`: C1's recipe with ONE change, `--adv-norm batch` (batch
centring; the B2 form) instead of `auto`, on `rung0_lane.sh BenchDimir
BenchDimir 512 0`, one seed, 512 episodes; two-tier rule: 50-game D0
development probes at 0 and 256, 100-game D0 + D1 at 512 (the level);
LAND + SPELL + type census on ck_256 and ck_512 over the Dimir census
set; `jobs.log` kept. Lane state `/tmp/rl_8ab_s0`, driver 7910 / server
7940; artifacts `rl/artifacts/v7/8ab/s0/`.

Readings, both stated:
* **Escapes the rail** if at ck_512 P(SPELL) at ≥ 3 lands is > 0.1 on the
  SPELL census AND argmax-SPELL > 0 on the type census (8a: 0.011 and
  0/257).
* **Trains** only if D0 at 512 (100 games) is clear above 0.037 (the
  upper bound of 8a's 0/100); "escapes the rail" without "trains" is a
  mechanism finding, not a level.
* Costs read alongside (B2's known failure mode): the LAND census at
  ≥ 3 lands (B2 unlearned the third land under batch centring once
  batches mixed outcomes), and the sampled curve for the "early good,
  late bad" shape.
Consequences, pre-stated: if 8a-b also rails, one more single-change arm
runs before 8b — **8a-c = C1 + `--target-kl 0.1`** (the C2 arm that was
never run; the same lane, `TKL=0.1`, `adv-norm auto`), same readings; if
8a-b trains, its ck_512 is the Dimir `rl:` entry of the 8b pool; if
neither trains, 8b's pool entry `rl:...:BenchDimir.dck` becomes
`cp7::BenchDimir.dck` and the 8b row says why.
Cannot: give a level or a v6 comparison (one seed, 512 episodes, 100
games); attribute an effect to anything but the one flag changed;
generalise to W0Base (where `auto` was chosen over `batch` for B2's
reasons).

## 8a-b — C1's recipe + `--adv-norm batch` on Dimir: escapes the rail and trains at 512 (2026-09-13 19:50 next-session clock; WSL 18:25; ONE seed, 512 episodes; fixed argmax-classes protocol; `rl/artifacts/v7/8ab/s0/`)

`rl/run_8ab.sh` (lane 17:57–18:22 WSL, 25 min for 512 episodes + 250
battery games; 16 updates, KL-stopped 4/16, all in the first five).

| point | games | D0 (heuristic, BenchDimir) | D1 (search) | attacks | blocks | turns |
|---|---|---|---|---|---|---|
| 0 | 50 (dev. probe) | 0/50 = 0.00 [0.000, 0.071] | – | 0/46 | 0/35 | 19.0 |
| 256 | 50 (dev. probe) | 17/50 = 0.34 [0.224, 0.478] | – | 305/325 | 4/98 | 19.5 |
| **512** | **100 (level)** | **41/100 = 0.41 [0.319, 0.508]** | 29/100 = 0.29 [0.210, 0.385] | 668/701 | 5/168 | 18.4 |

0 stalls and 0 draws in every battery; no `attackBudgetHit` (Dimir boards
are small). Sampled curve (32-episode batches, `train_lines.txt`): .19
.50 .31 .31 .22 .38 .41 .38 .25 .22 .44 .34 .44 .38 .13 .44 — first-4
42/128 = 0.328 [0.253, 0.412], last-4 44/128 = 0.344 [0.267, 0.429]:
flat, not clear of each other. Entropy 0.76 → 0.29, max |logit| 1.9 →
4.81; chosen types in the last batch PASS 1545 / LAND 226 / SPELL 342 /
ACTIVATE 58 / TARGET 153 / ATTACK 136 / BLOCK 18.

**Census** (the Dimir set, 903 consults): ck_512 `argmax_type PASS=230/790
LAND=221/221 SPELL=228/257 ACTIVATE=0/210 TARGET=112/112 ATTACK=111/111
BLOCK=1/47`, argmax-PASS when another candidate exists 165/838 = 20 %, gap
2.77, entropy 0.43, P(PASS) 0.24. **SPELL census: argmax-SPELL 175/198 =
0.88 at ≥ 3 lands, P(SPELL) 0.884** (0.99 / 0.92 / 0.94 at 2 / 3 / 4
lands, P(PASS) 0.007). LAND census: argmax-land 146/146, P(land) 0.98 at
≥ 3. The argmax census at ck_512 is identical, count for count, to
ck_256's (P(SPELL) 0.80 → 0.88, gap 1.73 → 2.77, entropy 0.57 → 0.43):
the second 256 episodes sharpened the same argmax on this set.

**Readings, as pre-registered for 8a-b:**
* **Escapes the rail — YES**: P(SPELL) at ≥ 3 lands 0.884 > 0.1 and
  argmax-SPELL 228/257 > 0 (8a: 0.011 and 0/257). Already true at ck_256.
* **Trains — YES** on the 8a-b bar: D0 0.41 [0.319, 0.508] is clear
  above 0.037. On the ORIGINAL 8a bar ("clear above 0.5 and the last-4
  sampled rate clear of the first-4") it is NOT met at 512: the interval
  reaches 0.508 and the sampled curve is flat from the first batch.
  So: a policy that plays Magic on Dimir at 512 episodes, at a level not
  shown above a coin flip against the heuristic, with no visible learning
  after update 2.
* **Mechanism**: the one change was `auto` → `batch` advantage centring.
  8a's second batch was 0/32 (uncentred under `auto`: every advantage
  negative, entropy 0.79 → 0.20 in five updates, spells gone); 8a-b's
  batches never went to zero (min 4/32) and entropy fell to 0.29 over 16
  updates while spells stayed. Caveat: the first batches differed by
  chance before any flag could act (3/32 vs 6/32 wins from the same init
  and game seeds — concurrent play is not replay-deterministic), and 8a's
  0/32 second batch is where the flags diverge; one seed each, so the
  mechanism is shown once, not established.
* **B2's cost, read as pre-stated**: the third land is NOT unlearned here
  (argmax-land 1.00 at ≥ 3 lands vs B2's 0.08 on W0Base); no "early good,
  late bad" shape in 16 updates (flat instead). The lever's known failure
  mode did not appear by 512 on this deck; it is not excluded later.
* **Behaviour**: attacks 668/701 (attacks with everything: under/over
  0/70), blocks 5/168 with BLOCKOPT 64/146 (never blocks — BLOCK 1/47 on
  the census: the combat head learned "attack" and not "block"), D1 0.29
  (the 1-ply search punishes the all-in attacks), 18.4-turn games. TARGET
  112/112 on the census (it points removal when asked); ACTIVATE 0/210.

**vs v6 (context, not the pre-registered comparison)**: v6 Dimir's D0
.555 [.486, .622] is a 1024 point; 8a-b's 0.41 [0.319, 0.508] at 512
lies below it with the intervals touching at the edge (0.508 vs 0.486 —
overlapping). Not comparable as pre-registered (different points, one
seed each); what it says is that the batch-centred v7 recipe at half the
episodes is in v6's neighbourhood, not clearly below.

**Consequence (pre-stated in the 8a-b pre-registration): 8a-b trains →
its ck_512 is the Dimir `rl:` entry of the 8b pool** (`rl/run_8b.sh`
`DIMIR=rl/artifacts/v7/8ab/s0/ck_512.pt`); 8a-c (`--target-kl 0.1`) is
not run.

Cannot: call 0.41 a level for "v7 on Dimir" beyond this one seed and
point; say the recipe keeps training past 512 (flat curve; 1024 not run);
attribute the escape to anything but the centring flag — with the
first-batch caveat above; say anything about W0Base (where `auto` was
chosen for B2's reasons and C1 trained with it); rank 8a-b's Dimir
policy against CP7 (no suite run on it — the suite budget goes to 8b's
two checkpoints).

## 8b / Q4 — L2, the diverse cross-deck league, vs L0: "no difference shown" on the suite, a regression at home, a head-to-head loss (2026-09-13 20:30 next-session clock; WSL 19:20; ONE seed; fixed argmax-classes protocol; Amendment 2 budget; `rl/artifacts/v7/8b/`)

`rl/run_8b.sh` (lane 18:24–18:52 WSL, 28 min for 1,024 episodes + 300
probe games; 32 updates, KL-stopped 4/32; suites and head-to-head to
19:11). L2 = L0 ck_3072 (the W0Base policy after C1 + 1,024 heuristic
episodes) continued +1,024 on W0Base against the pool, one entry per
256-block: heuristic on BenchDimir → CP7 (skill 6) on BenchBurn → the
8a-b Dimir policy (frozen ck_512, 0.41 vs the heuristic) on BenchDimir →
heuristic on BenchBurn. Control = L0 ck_3072 itself (the starting point;
L0's own +1024 heuristic row 0.91 [0.838, 0.952] is the home yardstick).

**The cross-deck suite** (`rl/battery_xdeck.sh`, 50 games per row =
development probes, read POOLED; the agent on W0Base in every row):

| row | L2 ck_4096 | L0 ck_3072 |
|---|---|---|
| vs heuristic, opp W0Base | 40/50 = 0.80 [0.670, 0.888], 24.0 turns | 44/50 = 0.88 [0.762, 0.944], 2 stalls, 32.4 turns |
| vs heuristic, opp BenchDimir | 41/50 = 0.82 [0.692, 0.902], 21.3 turns | 44/50 = 0.88 [0.762, 0.944], 28.7 turns |
| vs heuristic, opp BenchBurn | 38/50 = 0.76 [0.626, 0.857], 14.3 turns | 32/50 = 0.64 [0.501, 0.759], 17.3 turns |
| vs CP7, opp W0Base | 34/50 = 0.68 [0.542, 0.792], 0 stalls, 26.0 turns | 33/50 = 0.66 [0.522, 0.776], **12 stalls**, 41.8 turns |
| **pooled (200 games)** | **153/200 = 0.765 [0.702, 0.818]** | **153/200 = 0.765 [0.702, 0.818]** |

The two pooled suite rates are the same number: 153 wins of 200 each.
Per row (descriptive, 50 games): L2 traded W0Base and Dimir wins (−4,
−3) for Burn wins (+6) and stall-free CP7 games (+1 win, 12 → 0 stalls).

**Home battery** (D0 = heuristic on W0Base, the lane's rows; 50-game
probes per block, 100 at the final point):

| trained | opponent of the block just played | D0 | games | blocks | under/over | turns |
|---|---|---|---|---|---|---|
| 3072 (+0) | – | 0.86 [0.738, 0.930] | 50 | 773/978 | 163/162 | 32.4 |
| 3328 | heuristic, BenchDimir | 0.94 [0.838, 0.979] | 50 | 727/896 | 149/122 | 30.9 |
| 3584 | CP7, BenchBurn | 0.78 [0.648, 0.872] | 50 | 559/679 | 81/88 | 24.1 |
| 3840 | 8a-b Dimir policy, BenchDimir | 0.82 [0.692, 0.902] | 50 | 609/784 | 76/102 | 26.6 |
| **4096 (level)** | heuristic, BenchBurn | **0.73 [0.636, 0.807]** | **100** | 1067/1291 | 118/92 | 23.9 |

L2's home level 0.73 [0.636, 0.807] is clear below L0's +1024 home row
0.91 [0.838, 0.952] — a regression on the home deck, not "flat".

**Head-to-head** (`rl/hard_battery.sh` H2H, 100 games, seats alternate):
L2 ck_4096 vs L0 ck_3072 = **32/100 = 0.32 [0.237, 0.417]**, 48 losses,
**20 stalls** (draws at the 60-turn stop), 43.1 turns per game. L0 wins
the decided games 48–32.

**Per-block sampled rates vs each pool member** (`jobs.log`, 64-episode
jobs, stalls now separable):

| block | pool member | wins per job | block rate | stalls |
|---|---|---|---|---|
| 0 | heuristic on BenchDimir | 49 44 42 45 | 180/256 = 0.70 | 1 |
| 1 | CP7 on BenchBurn | 10 15 15 25 | 65/256 = 0.25 | 0 |
| 2 | 8a-b Dimir policy on BenchDimir | 47 41 48 52 | 188/256 = 0.73 | 0 |
| 3 | heuristic on BenchBurn | 43 33 37 46 | 159/256 = 0.62 | 0 |

No stall wall this time (1 stall in 1,024 training games; L1 had a 0.00–0.09
block against its frozen ancestor). CP7 on Burn is the one member the
policy loses to (0.25, rising 10 → 25 within its block); the 8a-b Dimir
policy is beaten at 0.73 — a weak member, as the pre-registration's
"cannot" foresaw.

**Census at ck_4096** (the W0Base set): argmax PASS 94/1002, LAND
259/313, SPELL 313/368, ATTACK 217/279, BLOCK 206/207; P(land) at ≥ 3
lands 0.74 — identical to L0 ck_3072 except ATTACK 199 → 217 and PASS
111 → 94: the league moved the argmax on 18 attack windows and 17 pass
windows out of 1,002, nothing else on this set. Entropy 0.66, max
|logit| 4.99.

**Reading, as pre-registered (with Amendment 2):**
* **"Diverse league helps"** — NO: the pooled suite is not clear above
  L0's (identical, 153/200 each) and the home D0 IS clear below L0's 0.91.
* **"Hurts"** — NOT SHOWN on the suite (the suites are identical, not
  clear below).
* **Verdict: "no difference shown at n=200" on the cross-deck suite**,
  with a home-deck regression (0.73 vs 0.91, clear) and a head-to-head
  loss (0.32, 20 stalls). The pre-stated tie-break applies: a cross-deck
  gain paid for by a home loss is a finding — here the per-row table says
  the gain is on Burn (+6 of 50, the two rows overlap) and against CP7
  the stalls vanished (12 → 0) at the same win count, while W0Base and
  Dimir rows dropped 4 and 3. The suite's total did not move; its
  composition did.
* **Mechanism note** (counters, L2 4096 vs L0 3072 under the same
  protocol): games got SHORTER (23.9 vs 32.4 turns at home; 26 vs 42 vs
  CP7) and the attack balance flipped from even (under/over 163/162) to
  over-attacking (118/92 at home; the block-2 and block-3 rows 76/102,
  81/88), ATKOPT 613/825 = 0.74 vs 277/613 = 0.45 (more of its attacks are
  the solver's), blocks 1067/1291 = 0.83 vs 773/978 = 0.79. This is not
  L1's signature (L1 stalled: 44-turn games, under/over 594/34, blocks
  down): the cross-deck pool — two Burn blocks and a Dimir policy that
  attacks with everything — taught it to race. Racing wins against Burn
  and ends CP7 games before the 60-turn stop; at home against a
  heuristic that blocks well it loses 18 more games in 100 than L0's
  patient play, and against L0 itself (a policy that blocks 0.79 of
  opportunities) racing loses 48–32 with 20 games stalled out.
* The regression at home is the same *direction* as L1's (0.68) but
  half the size and by a different route; the league mechanism has now
  hurt the home level twice in two configurations.

Cannot: one seed (every number above is a single run; the suite
rows are 50-game probes and only the pooled 200 is compared); the pool
is fixed-strength — no PFSP weighting, no refresh, and the Dimir member
is a 512-episode 0.41 policy, so block 2 was near-free wins; the trainee
plays one deck (deck-general play is 8c); L2's +1024 on mixed opponents
is not compute-matched to L0's +1024 on the heuristic in heuristic games;
the head-to-head is the L1 instrument and carries its stall caveat (20 of
100 games undecided); CP7 on Burn is CP7's Burn.

## 8c — not run (2026-09-13 20:35 next-session clock)

8c (the Dimir trainee continued +1024 with the cross-deck pool, against
its own heuristic-continued control) was conditioned on "8a trains and
time remains". 8a as-is did not train (0/100, the never-cast rail); the
policy that does play Dimir is 8a-b — one seed, 512 episodes, a flat
sampled curve and a 0.41 level whose interval contains 0.5 — not a
foundation for a second-order question; and the league mechanism has now
regressed the home level twice (L1 0.68, L2 0.73 vs L0 0.91) in two
different ways. Running 8c tonight would produce a one-seed number on a
weak trainee about a mechanism that is currently negative at home. It is
owed after the 8a-b second seed and 1024 point, and after a league with
opponent sampling (PFSP) rather than a fixed rotation.

## 9 / P1 — card-swap counterfactual: the v7 candidate scorer is identity-blind, by mechanism (2026-09-14; branch `v7/lane-d`; runbook `rl/PHASE9-PROBES.md`)

`bash rl/probes/run_p1.sh` → `python3 rl/probes/cardswap.py` over the six
pre-registered consult files (`7c_W0Base_{p1,p99,sf}` 1,101 + `7c_BenchDimir_{p1,p99,sf}`
903 = 2,004 consults), five subjects: `init` (`/tmp/rl_7c1_s0/init.pt`, P10INIT seed 10,
copied to `rl/artifacts/v7/9/init.pt`), `C1s0` (7c1 s0 ck_2048), `L0` (7l ck_3072), `BC`
(7d2 bc.pt), `DIM` (8ab s0 ck_512). Same memoryless scoring path as `rl/v7_init_logits.py`
(fresh LSTM state, no deck context, logit bound 5 applied to the raw logits; init's config
carries no bound so 5 is imposed on every subject). Artifacts in `rl/artifacts/v7/9/`:
`pairs_{text,pt,cost,type,sources}.txt`, `cardswap_<subject>.tsv` (one row per swap),
`cardswap_summary.txt`, `p1_run.log`.

**Pairs** (from `rl/artifacts/cards_v1/{fields,oracle}.jsonl.gz`, ids via `v7_obs.CardIds`;
sources = the 28 cards referred by SPELL candidates in the two sets, of which 9 are
creatures with keyword-only text — the nine W0Base vanilla creatures; the Dimir creatures
all carry non-keyword text and get type pairs only): **text 19** (same mana cost, types,
supertypes, P/T; both texts keyword-only; sets differ by 1–2 keywords: lifelink 9,
vigilance 6, first strike 1, first strike+lifelink 1, flying 1, prowess 1), **pt 12**
(|dP|+|dT| = 1, all else equal), **cost 6** (mana value ±1, same colours, all else equal),
**type 120** (same mana cost, non-creature non-land spell without subtypes), ≤ 8 partners
per source. **The pre-registered ≥ 40 pairs is not met for text/pt/cost**: with the
identical-cost-and-type-line definition the corpus holds that few partners for these nine
cards (e.g. 2/2 for {1}{W} with exactly one keyword and nothing else: 5). Kept as
pre-registered rather than loosened; the shortfall is immaterial given the result (every
class, including the 6,704 type swaps, is at floor).

**Swapped fields**: text = `ent_id` (embedding row) + keyword bits 34–51 (variants:
`text_emb` embedding only, `text_kw` bits only); pt = `ent_id` + fields 10, 11, 13, 14, 15;
cost = `ent_id` + field 17; type = `ent_id` + is-creature 29 + type flags 30–33 + P/T
fields zeroed + keyword bits. NOT swapped, by construction: the candidate afterstate row
(`v7_cand[8..]`: mana left after, castable-now, speed flags) — the one place the cost
reaches the scorer, see the control. `self_mana` = a control that changes the candidate's
OWN afterstate field 8 (mana left after) by 1/6, no identity change.

Δp = |p_after − p_before| on the swapped candidate, mean over partners per (consult,
candidate), bootstrap 95 % CI over consults (2,000 resamples); `flip` = the argmax moves to
a candidate of a different (type, card) class; `flip_strict` = a flip between two
candidates whose pre-swap logits differed by > 1e-3 (identical-row candidates tie
*exactly*, so a plain flip counts tie-breaking noise).

| subject | class | n cand / consults / swaps | mean Δp [95 % CI] | mean Δlogit (bounded) | flip | flip_strict |
|---|---|---|---|---|---|---|
| init | text | 322 / 229 / 1,547 | 0.00000 [0.00000, 0.00000] | 0.00000 | 0.000 | 0.000 |
| init | pt | 401 / 276 / 878 | 0.00000 | 0.00000 | 0.000 | 0.000 |
| init | cost | 302 / 220 / 454 | 0.00000 | 0.00000 | 0.000 | 0.000 |
| init | type | 838 / 503 / 6,704 | 0.00000 | 0.00000 | 0.000 | 0.000 |
| init | self_mana | 838 / 503 / 838 | 0.00404 [0.00395, 0.00413] | 0.0205 | 0.135 | 0.080 |
| C1s0 | text | 322 / 229 / 1,547 | 0.00004 [0.00003, 0.00004] | 0.0023 | 0.060 | **0.000** |
| C1s0 | text_emb / text_kw | | 0.00004 / 0.00000 | 0.0020 / 0.0004 | 0.057 / 0.053 | 0.000 / 0.000 |
| C1s0 | pt | 401 / 276 / 878 | 0.00001 [0.00001, 0.00002] | 0.0010 | 0.034 | 0.000 |
| C1s0 | cost | 302 / 220 / 454 | 0.00002 [0.00001, 0.00002] | 0.0012 | 0.018 | 0.000 |
| C1s0 | type | 838 / 503 / 6,704 | 0.00014 [0.00012, 0.00015] | 0.0065 | 0.054 | 0.000 |
| C1s0 | self_mana | 838 / 503 / 838 | 0.00082 [0.00074, 0.00090] | 0.0069 | 0.143 | 0.027 |
| L0 | text | 322 / 229 / 1,547 | 0.00001 [0.00001, 0.00001] | 0.0003 | 0.021 | 0.000 |
| L0 | pt / cost / type | | 0.00000 / 0.00000 / 0.00003 | 0.0001 / 0.0003 / 0.0014 | 0.027 / 0.004 / 0.063 | 0.000 / 0.000 / 0.000 |
| L0 | self_mana | 838 / 503 / 838 | 0.00028 [0.00026, 0.00030] | 0.0021 | 0.146 | 0.038 |
| BC | text / pt / cost / type | as above | 0.00000 (all) | 0.0000 (all; raw 0.011–0.085) | 0.000 | 0.000 |
| BC | self_mana | 838 / 503 / 838 | 0.00000 | 0.0000 (raw 0.139) | 0.000 | 0.000 |
| DIM | text | 322 / 229 / 1,547 | 0.00003 [0.00003, 0.00004] | 0.0017 | 0.074 | 0.000 |
| DIM | text_emb / text_kw | | 0.00003 / 0.00001 | 0.0015 / 0.0003 | 0.076 / 0.059 | 0.000 / 0.000 |
| DIM | pt / cost / type | | 0.00002 / 0.00004 / 0.00007 | 0.0008 / 0.0020 / 0.0036 | 0.054 / 0.042 / 0.072 | 0.000 / 0.000 / 0.000 |
| DIM | self_mana | 838 / 503 / 838 | 0.00296 [0.00273, 0.00321] | 0.0275 | 0.098 | 0.011 |

Yardstick (the scorer's working range on the same consults, bounded logits): mean
top-1/top-2 gap init 0.37, C1s0 1.76, L0 2.82, BC 4.03, DIM 2.74; within-consult logit
s.d. 0.24 / 1.82 / 3.22 / 4.80 / 2.91. The largest identity effect anywhere (C1s0 type
swaps, 0.0065 nats) is 0.4 % of that subject's top gap; the text swaps are 0.01–0.13 %.
BC's raw logits average |43| (bounded 4.0 gap): its tanh bound is saturated, so its Δ under
the bound is exactly 0 and even its raw Δlogit (0.035 text, 0.139 self control) is < 1 %
of its raw scale.

**Tie census** (base scoring, no swap): among pairs of SPELL candidates in the same consult
that name DIFFERENT cards but carry the same afterstate row (e.g. Silvercoat Lion vs Glory
Seeker, Dromoka Warrior vs Blade of the Sixth Pride), n = 219 pairs: mean |Δlogit| =
0.00000 and **219/219 tied to < 1e-4 in every subject** (init, C1s0, L0, BC, DIM); pairs
with different rows (n = 306) differ by 0.05 / 0.036 / 0.020 / 0.000 / 0.28 nats. Every
"flip" in the table is one of these exact ties being broken by a 1e-3 perturbation
(SPELL→SPELL between same-row cards: 93/93 of C1s0's text flips, 114/114 of DIM's), hence
`flip_strict` = 0.000 in every identity class of every subject.

**Mechanism** (`P1|<subject>|mechanism` lines): `StateGraphEncoder` zero-initialises the
attention output projection, the FFN output layer and every per-edge attention-bias row
(the encoder is the identity on the builder tokens at init — `rl/v7_encoder.py` docstring,
a Phase 4c exactness property). After training, mean |W| of `att.out` is 0.00017–0.00052
and of `ffn.out` 0.00019–0.00051 against 0.0313 for the input projections, and the
**`refers_to` edge bias (candidate → its referent) is ≤ 0.0027 in every subject** (init 0;
C1s0 max 0.0016, L0 0.0027, BC 0.0016, DIM 0.0007; all edge types ≤ 0.0027). With the edge
bias at zero, a candidate token attends to the entity tokens with exactly the same weights
as every other candidate of the same row: it receives the consult-wide mixture of
entities, never *its* card. The encoder does move tokens (relative change of the candidate
encoding 0.25–0.99, of the game token 2.0–6.4 — the FFN and the aggregate attention are
live), but nothing in it distinguishes the referent from the rest of the board. The swap
Δlogits above are the referent's change leaking into that shared mixture — which shifts
every candidate of the consult by nearly the same amount, so p barely moves. At the lane's
lr 3e-5 with ~64–100 updates, a zero-initialised bias cannot travel further than ~3e-3;
the wire's identity channel (§2f "identity reaches the candidate through
`v7_cand_refers`") is therefore closed in every checkpoint the project has trained.

**Pre-registered readings, computed as written and then corrected in the open.** The
text-blind / text-sensitive rule compares mean Δp(text) with 0.10× and 0.5× mean Δp(pt).
Computed: init 0/0 (undefined), C1s0 ratio 2.66, L0 2.41, BC undefined (0/0), DIM 1.82 —
the rule would print "text-sensitive" for three subjects. **That reading is void**: its
premise was that a P/T swap moves the scorer and the text swap is compared against it;
the P/T control is itself at floor (≤ 0.00002, strict flips 0/878 in every subject), as
are the cost and type controls. The reading that the numbers support is a fourth one the
pre-registration did not list: **identity-blind** — the scorer reads none of its
referent's text, P/T, cost or type, in any subject, at any level of training. The
training-effect clause (trained text CI vs init's) is likewise void (all intervals sit at
0.0000x; "sharpened" 0.00001 over 0 is not a sharpening). BC, the interesting subject
(supervised card labels), is the clearest case: exactly 0 under its saturated bound,
raw Δlogit < 1 % of its scale — it could not have learned CP7's card because the card
never reached its scorer, which is the mechanism behind the "type, not card" BC row
(top-1 0.606 vs the 0.833 copy ceiling; type agreement 0.887).

What this says about the policies: a v7 policy can condition a SPELL decision only on the
candidate's own row (type, mana left after, targets legal, speed flags, stack position)
and on the game/player tokens plus the consult-wide entity mixture; "which creature to
cast" among same-cost cards is decided by an exact tie, i.e. by candidate order. The
type-level policies (wall-then-race, attack-everything, cast-anything) are what this
network can express. ATTACK / BLOCK / TARGET candidates carry CombatMath / target P/T in
their own afterstate rows, so size-awareness there is possible without identity (P2 tests
it); keyword-awareness is not.

Cannot: say what a *trained* refers bias would buy (no checkpoint has one); attribute the
closed channel to the learning rate vs the zero-init alone (untangled by a run with the
edge biases initialised non-zero, or a larger lr on them — a pre-registrable follow-up,
not run here); reach the 40-pair bar for text/pt/cost (19/12/6, see above); speak to
opponent-hand or deck tokens (not swapped); speak to the belief module (not on this path).
Pre-stated: P4's "training erases / preserves keyword information" will read
"preserved" trivially — the entity tokens are never asked for their keywords by a
candidate, so nothing acts on them either way.

## 9 / P4 — linear probes on the entity tokens: everything is decodable, before and after training (2026-09-14; branch `v7/lane-d`)

`bash rl/probes/run_p4.sh` → `python3 rl/probes/token_probe.py` over the same 2,004
consults; rows = every battlefield creature entity (`v7_ent` zone 0, is-creature) whose
name the corpus knows: **8,386 rows / 1,825 consults / 16 distinct cards** (Kaito,
Soulstone Sanctuary, Restless Reef rows skipped: no printed P/T in the corpus). Labels from
`cards_v1` graph features / printed P/T: flying 802 positives, lifelink 79 (Cecil, Redeemed
Paladin), first strike **0 (not testable: no first-strike creature in either deck)**,
any-keyword 1,770, power bucket {≤1: 583, 2: 4,910, 3: 2,438, ≥4: 455}, toughness bucket
{2,583 / 2,288 / 2,312 / 1,203}. Views: `raw` = the 64-float wire row; `build:init` = the
builder token (card embedding + row through the zone MLP); `enc:<subject>` = the encoder
output token. L2 logistic probe, class-balanced, 5-fold GroupKFold over consults, balanced
accuracy on out-of-fold predictions, bootstrap 95 % CI over consults. Artifacts
`rl/artifacts/v7/9/token_probe_summary.txt`, `p4_run.log`.

| view | flying | lifelink | any-keyword | power bucket | toughness bucket |
|---|---|---|---|---|---|
| raw wire row | 0.999 [0.997, 1.000] | 1.000 | 0.999 [0.997, 1.000] | 1.000 | 1.000 |
| build (init) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| enc: init | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| enc: C1s0 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| enc: L0 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| enc: BC | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| enc: DIM | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

(every CI is [1.000, 1.000] unless shown; first strike not testable.)

**Pre-registered reading, per label and subject: "preserves" everywhere** (every trained
interval overlaps init's; all sit at 1.000). **The raw wire row already carries the
keywords**: `v7_ent` fields 34–51 are the 18 keyword bits after continuous effects (WIRE
§2d) and 14–15 the printed P/T, so the probe is a read-out of explicit input fields, not
of the card embedding — the clause "if the wire has no keyword field ... the only route is
the card embedding" does not apply. The encoder output stays linearly decodable because,
per P1's mechanism line, the encoder is close to the identity plus a per-token FFN on the
builder tokens (att.out / ffn.out weights ≤ 0.0005). As pre-stated in P1, this result is
trivial in the direction that matters: the entity tokens *hold* the keywords in every
subject, and the candidate scorer never *reads* its referent's token (P1), so decodability
here says nothing about use. Cannot: linear decodability is not use; the label set is the
two decks' (16 cards, keyword positives are Spyglass Siren / The Wondrous Wasp for flying
and one transformed Cecil for lifelink), so the probe is far easier than a corpus-wide
one; the granted-vs-printed distinction is not separable on these rows (no pump effects
in play).

## 10 / A1-A2 — the candidate-to-card path behind `--cand-refers-pool`, and the gate (2026-09-14; branch `v7/lane-d`; runbook `rl/PHASE10-LEAGUE.md`)

**A1 (code, ce38ccc).** `v7_net.TokenBuilders(cand_refers_pool=True)`: `refers` ([B, K, T_wire])
restricted to the entity slice (tokens 3..), masked by `ent_mask`, row-normalised, pools the
referents' `[c', unk, ent-fields]` rows — the same `x` the zone MLPs read — into
[B, K, 193]; `cand_ref = Linear(193, 256, bias=False)` with default (non-zero) init adds it to
the candidate token before masking. The same for `opp_act` with `opp_act_refers`
(`opp_act_ref`; cheap, done). Design choices stated: **no bias**, so a candidate with no
entity referent (PASS, a player target) keeps its exact flag-OFF token (tested); the two
layers are drawn from a **forked RNG** (`initial_seed() + 7919`), so every other parameter of
a seeded fresh net equals the flag-OFF net's (tested). Flag OFF: no parameter, no config key,
outputs **bit-identical to HEAD** (golden `tests/fixtures/v7_golden_off.pt` written by
bfd547d; `torch.equal` on logits / value / game_vec). The config key `cand_refers_pool` is
written only when ON; an ON checkpoint rebuilds ON from its config with no flag (a frozen
league opponent server needs none); an OFF checkpoint under the flag loads `strict=False`
and prints the two fresh keys (`V7Policy.load(..., cand_refers_pool=True)`, and `Trainer`
under `policy_server.py --cand-refers-pool`, which also prints `cand_refers_pool=<bool>` at
start). `p10_init_net.py --cand-refers-pool` mints fresh ON inits. Tests 18/18 (4 new),
`rl/v7_check.py` 15/15 failures=0.

**A2 (the gate), `bash rl/p10_a2.sh`** → `rl/artifacts/v7/10/a2/` (`cardswap_summary.txt`,
`cardswap_{OFF,ON}.tsv`, `a2_run.log`). The P1 probe (a frozen copy, `rl/p10_cardswap.py`;
the Phase 9 file untouched) on the same 2,004 consults (W0Base + Dimir sets) and the same
pairs as 9/P1. OFF = `rl/artifacts/v7/9/init.pt` (P10INIT seed 10, the 9/P1 `init`
subject); ON = the **same trunk** + the two new layers (loaded strict=False, saved as
`init_on.pt`), so the only difference is the path.

| subject | text | text_emb | text_kw | pt | cost | type | self_mana (control) |
|---|---|---|---|---|---|---|---|
| OFF mean Δp | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00404 [0.00395, 0.00413] |
| ON mean Δp | **0.05163 [0.04895, 0.05420]** | 0.04716 | 0.00944 | 0.04029 | 0.04318 | 0.06880 | 0.00315 [0.00309, 0.00320] |
| ON flip_strict | 0.127 [0.102, 0.153] | 0.093 | 0.022 | 0.133 | 0.101 | 0.175 | 0.000 |

(n: text 1,547 swaps / 322 candidates / 229 consults; pt 878; cost 454; type 6,704; self 838.)
Per keyword (ON text): first strike 0.034, flying 0.063, lifelink 0.042, prowess 0.043,
vigilance 0.031. Tie census ON: the 219 different-card same-row SPELL pairs that tied
exactly in every 9/P1 subject now differ by mean |Δlogit| 0.273, 0/219 tied. Mechanism line
ON: encoder still the identity at init (att.out / ffn.out / every edge bias 0) — the effect
is the builder path alone, as designed.

**Gate (pre-registered): ON's mean Δp on text-only swaps ≥ 0.01 AND ≥ 10× OFF's → PASSED**
(0.0516, lower bound 0.0490; OFF 0.00000, so the ratio is unbounded). No fix attempt was
needed. Reading: with the flag the untrained scorer is identity-sensitive at every class,
with a text effect ~13× the own-afterstate control (0.0516 / 0.0040 at OFF's control), where
OFF is identity-blind. The keyword-bits-only variant (text_kw 0.0094) is below the bar on
its own: most of the text effect rides on the embedding row, as the pool's input width says
(128 embedding dims vs 18 keyword bits).

Cannot: say the trained league nets will USE the path (that is Q7, after training); say
anything about the P1 pair shortfall (19/12/6 text/pt/cost pairs, below the 40 pre-registered
in Phase 9 — the same pairs, kept); the self_mana control moved 0.0040 → 0.0032 because the
added term changes every referring candidate's token scale (not a fault).

## 9 / P2 — removal targeting on Dimir: size-aware through the afterstate row, text not testable (2026-09-14; branch `v7/lane-d`)

Recordings: the three Dimir echo sets (24 games) plus two fresh DIM argmax recordings on
BenchDimir vs the heuristic (`rl/probes/record_p9.sh dim`: frozen 8ab ck_512 on 7947 with
`--argmax-classes`, the new `rl/probes/record_proxy.py` on 7948 logging the driver's
consults and the server's `{"a":k}` replies, driver 7911 with the v7 flags; 8 + 24 games,
seeds 9100 / 9200; DIM 3–5 and 7–17, 16.4 / 20.3 turns; `rec_dim_dimir{,_b}.jsonl`, not
committed). `bash rl/probes/run_p2.sh` → `rl/probes/target_probe.py`; summary
`rl/artifacts/v7/9/target_probe_summary.txt`. **157 TARGET consults with k ≥ 2 creature
targets** (90 from the DIM recordings, 67 from the echo sets); the equal-P/T-different-text
subset is **n = 6 → "not testable at this n"** (pre-registered stop at n < 30; the Dimir
mirror's creatures are Siren 1/1, Wasp 2/1, Drowner 2/1, Curiosity 4/3, Elektra 3/3,
Cecil 2/3 — the only equal-stat pair is Wasp/Drowner and both carry text). The combat-
optimiser reference was not built (not cheap). Chance = #largest-power targets / k per
consult; diff = P(picks a largest) − chance, bootstrap 95 % CI over consults.

| row | n | P(largest) | chance | diff [95 % CI] | reading | P(opponent's creature ∣ both sides offered) |
|---|---|---|---|---|---|---|
| DIM as recorded (lane server, LSTM state, argmax-classes) | 90 | 0.856 | 0.694 | **+0.162 [0.100, 0.227]** | size-aware | 1.000 (n = 28) |
| DIM, memoryless argmax | 157 | 0.936 | 0.654 | +0.282 [0.233, 0.332] | size-aware | 1.000 (n = 45) |
| BC | 157 | 0.936 | 0.654 | +0.282 [0.233, 0.332] | size-aware | 1.000 |
| init | 157 | 0.879 | 0.654 | +0.225 [0.169, 0.281] | size-aware | 1.000 |
| C1s0 | 157 | 0.624 | 0.654 | −0.030 [−0.086, 0.027] | not size-aware | **0.022** |
| L0 | 157 | 0.631 | 0.654 | −0.023 [−0.079, 0.033] | not size-aware | **0.000** |

The size signal is the TARGET candidate's own afterstate row (`v7_cand[12]` = power ÷ 6,
[14] = mine), which P1 showed is the only thing the scorer reads per candidate: the
*untrained* init is already "size-aware" (a random readout of the power field that
happens to favour the larger), DIM and BC keep that sign, and the two W0Base PPO policies
(C1s0, L0 — trained on a deck with no removal) have drifted to targeting their **own**
creatures (0.02 / 0.00 opponent-side) at chance size. Nothing here is card knowledge:
Cecil, Dark Knight (deathtouch) vs Elektra (3/3) is decided by the power field. Cannot:
say anything about non-creature targets (excluded); test text-awareness (n = 6); separate
"largest power" from "largest toughness" (correlated on these six creatures); attribute
the recorded 0.856 vs memoryless 0.936 gap (LSTM state and the argmax-classes protocol
differ; both are size-aware).

## 9 / P3 — instant-speed play: forced by legality, not chosen (2026-09-14; branch `v7/lane-d`)

> **Correction in the open (2026-09-14, Phase 11 A1):** the instant-speed rule used by this section mis-indexed the main-phase test (`instant_speed.py` reads `v7_game[6]` = declare-blockers and `[10]` = holds-priority instead of `[4]` / `[8]`), so its DIM numbers and the flash reading below are wrong. Corrected numbers and reading: section "11 / A1-A2" (with its "correction to 9 / P3" paragraph) at the end of this file. The table is left as published.

`bash rl/probes/run_p3.sh` → `rl/probes/instant_speed.py`; summary
`rl/artifacts/v7/9/instant_speed_summary.txt`. CP7 on BenchDimir vs the heuristic recorded
through the teacher seat (`record_p9.sh cp7`, `rec_cp7_dimir{,_b}.jsonl`, 8 + 24 games,
seeds 9100 / 9300, CP7 7–1 and 22–2, 16.4 / 16.3 turns, 1,104 labelled consults); DIM =
the P2 recordings (1,969 consults). An "instant-capable cast" = a chosen SPELL whose
referent is an instant (`v7_ent[31]`) or has flash (bit 42); "at instant speed" = the
consult's game token says not the active player, or a non-main step, or a non-empty stack
(in response). Counterspells (We Say Thee Nay!, Spell Pierce, Spell Snare) are legal only
with a spell on the stack, so their timing is forced; they are split out.

| seat | games | casts | instant-capable | at instant speed | fraction (Wilson) | excluding counterspells |
|---|---|---|---|---|---|---|
| CP7 (reference) | 32 | 231 | 148 | 14 | 0.095 [0.057, 0.153] | 6/136 = 0.044 [0.020, 0.093] |
| DIM (8ab ck_512, argmax) | 32 | 333 | 254 | 71 | **0.280 [0.228, 0.338]** | 15/195 = **0.077 [0.047, 0.123]** |
| CP7 on W0Base (7d1b, 1,400 games) | 1,400 | 12,171 | 0 | – | not testable: the deck has no instants | – |
| heuristic (opponent rows) | 64 | 539 | 295 | – | **not measurable** (0/295 first reports find the spell still on the stack: the seat is never consulted while the opponent's spell is pending, so the wire cannot date the cast) | – |

Per card (at instant speed / capable casts): DIM — We Say Thee Nay! **45/45**, Spell Snare
8/11, Spell Pierce 3/3, Requiting Hex 13/49, Bitter Triumph 2/20, Nowhere to Run 0/18,
Shoot the Sheriff 0/5, The Wondrous Wasp **0/34**, Floodpits Drowner **0/48**, Enduring
Curiosity **0/21**; CP7 — We Say Thee Nay! 4/8, Spell Snare 3/3, Spell Pierce 1/1,
Requiting Hex 3/19, Bitter Triumph 2/17, Nowhere to Run 1/12, Wasp 0/31, Drowner 0/36,
Curiosity 0/20. Windows in which an instant-capable cast was offered: DIM 274 (cast in
254 = 93 %), CP7 652 (cast in 148 = 23 %).

**Pre-registered reading**: "instant-aware if DIM's fraction is clear above the
heuristic's" — **not evaluable**: the heuristic's timing is not readable from the wire
(above; its code, `HeuristicPlayer` v3, holds instants reactively and casts flash at the
opponent's end step, but that is not a measurement). Against the reference: DIM's 0.280
is clear above CP7's 0.095, and that gap is the 45/45 We Say Thee Nay! casts — a
counterspell can only be cast at instant speed. **Excluding counterspells DIM is 0.077
[0.047, 0.123] vs CP7 0.044 [0.020, 0.093], overlapping, and every flash creature (103
casts) went down at sorcery speed.** DIM fires an instant-capable card in 93 % of the
windows that offer one: it does not hold, it casts what is castable — the same
"cast-anything" rule as its SPELL play (8a-b row), applied to instants. Reading: **not
instant-aware beyond legality**. Cannot: distinguish "held on purpose" from "had no mana"
(the 7 % non-counter instant-speed casts are not analysed for mana); the n is 32 games per
seat; the heuristic reference is missing for the reason stated.

## Phase 9 verdict (2026-09-14)

**The v7 policy does not read card nuance — it cannot: in every checkpoint (init, C1s0,
L0, BC, DIM) swapping a SPELL candidate's card for a same-cost/same-type/same-P/T card
with different rules text moves its probability by ≤ 0.00004 (P/T, cost and type swaps ≤
0.00014; 0 strict argmax flips in 11,839 identity swaps; 219/219 different-card same-row
candidates exactly tied), because the `refers_to` attention bias that would let a
candidate token look at its own card never left its zero initialisation (≤ 0.0027 after
training).** What the policies do read is the candidate's own afterstate row and the
game token — enough for removal to prefer the larger creature (DIM +0.16 [0.10, 0.23]
over chance) and for instants to be cast when legal (0.077 at instant speed excluding
forced counterspells, vs CP7 0.044), and nothing that depends on which card it is.

## 10 / A3 — the landfall deck `rl/G1Landfall.dck`: smoke (2026-09-14; branch `v7/lane-d`)

60 cards, R/G, 24 lands: 4 Evolving Wilds [ROE:228], 13 Forest [M19:277], 7 Mountain
[FDN:278]; creatures (24, the landfall base): 4 Scythe Leopard [BFZ:188], 4 Plated Geopede
[ZEN:141], 4 Snapping Gnarlid [BFZ:190], 2 Oran-Rief Survivalist [ZEN:174], 2 Lotus Cobra
[ZEN:168], 3 Grazing Gladehart [ZEN:163], 3 Valakut Predator [BFZ:160], 2 Rampaging Baloths
[ZEN:178]; land search (8): 4 Rampant Growth [M10:201], 2 Harrow [ZEN:165], 2 Nissa's
Pilgrimage [ORI:190]; other (4): 2 Adventuring Gear [ZEN:195], 2 Khalni Heart Expedition
[ZEN:167]. Set numbers resolved from the pinned `Mage.Sets` classes (WSL /home/user/mage,
7554968c96); every name is in `rl/artifacts/cards_v1/index.json` (lower-cased keys).
Territorial Baloths (a candidate) has no XMage class; not used. Basics reuse printings
already in the project's decks. Copied to `Mage.Tests/`.

Smoke (`bash rl/p10_a3_smoke.sh 7913 7785`; driver 7913 because the Phase 9 probe held 7911;
artifacts `rl/artifacts/v7/10/a3/`): **20 games heuristic vs heuristic mirror: all end, 9–11
(0.45), 0 draws, 0 stalls, 13.0 turns per game, 0 exceptions** (driver and JVM logs). 4-game
v7 wire recording (echo policy pick 1 vs the heuristic): **wire_validate ok on 136 consults;
all 16 distinct deck cards resolve to an embedding id (0 unknown cards)** — the 3 names
without an id are stack-ability objects (the Baloths / Leopard landfall triggers, the
Survivalist-style sacrifice-search ability), which are not cards. 13 turns vs W0Base's ~23:
the heuristic mirror races (landfall bodies grow on every land drop); stated, not a fault.

Cannot: say anything about how well an RL policy will play it (no reference, first
number is the league's); the heuristic's play of Harrow / Evolving Wilds / Lotus Cobra mana
is the engine AI's (the payment and library-search sub-choices are the engine's for the
RL seat too).

## 10 - pre-registration and Amendment 3 (2026-09-14; the Phase 10 pre-registration is the runbook rl/PHASE10-LEAGUE.md, "Opponent selection per block" and "Pre-registered readings"; this section records the one amendment made while the league ran)

**Amendment 3 (sampling shortfall) — 2026-09-14, WSL ~11:00Z, controller at block 40 / hour ~7; written BEFORE any Q6 number exists**

Found by the main session. `league10.py` draws each block's bucket from
`random.Random(10000 + n).random()`. The generator is sound (29 % of first draws ≥ 0.7 over
5,000 seeds), but which n values happened to land on main blocks left the realized mix well
short of the pre-registered one:

| | main picks | self | pfsp | expl | heur | cross |
|---|---|---|---|---|---|---|
| stage 1 (n 0–26; first blocks excluded) | 18 (6 per main) | 5 | 10 | 3 | **0** (pre-reg. 15 %) | — |
| stage 2 (n 27–39) | 9 (3 per main) | 4 | 2 | 3 | **0** (pre-reg. 10 %) | **0** (pre-reg. 30 %) |

The precomputed draws for n = 40..55 give cross only at n = 40, 41 and 54, and heur only at
n = 48. Stage 2 would therefore have ended at ~14 % cross instead of 30 %, about one
256-episode cross-deck block per main, which is too little for Q6 to mean anything.

**Stage 1 ran with no heuristic anchor at all.** That is a condition, and it goes into the Q5
row. The flat development probes coincide with it: M_D 0.48 → 0.46 and M_L 0.44 → 0.42 at
1024 → 2048, while M_W went 0.74 → 0.70. Stage 2 was forced at hour 5.10 (n = 27) with only
M_W graduated (probe 0.74 [0.604, 0.841] at 1024). So M_W's cross pool is every other main
(the forced rule), and M_D's and M_L's cross pool is M_W.

**Change (stops the controller cleanly after block 40, then resumes it; nothing else moves):**
in stage 2, before the bucket is used, each main gets a quota on its **realized** stage-2
shares (rc-0 rows, a fallback counted as what it fell back to). If its cross share is below
0.30, the pick is forced to cross; else if its heur share is below 0.10, it is forced to
heur; else the MIX2 draw stands. The draw is still consumed, so seeding, PFSP, resolve, the
exploiters and the hour-10 hard stop are identical. Forced picks are logged as
`bucket=cross(quota)` / `heur(quota)`. The quota restores the pre-registered stage-2 shares;
it does not change them. With 3 stage-2 blocks already played per main, the next picks per
main are forced to cross, cross, heur, then sampled; with ~3 h left, most mains reach ≈ 2
cross + 1 heur blocks in stage 2. Q6's confound statement (cross-deck stage + more
episodes; no control arm) is unchanged. The small cross-deck episode count is stated in the
Q6 row whatever it reads.

### 10 — interim card-swap check on the league mains (2026-09-14 12:15Z; league paused by the user for it; NOT the Q7 row)

`rl/p10_cardswap.py` exactly as the A2 gate ran it (the six 7c W0Base + BenchDimir consult sets, 2,004 consults, same pair lists), on the latest pool snapshots M_W_03072, M_D_03072, M_L_02816 against the untrained flag-ON net; CPU, run while the league was still in its last block. Artifacts `rl/artifacts/v7/10/interim_p1/`.

| subject | text-only Δp | its embedding part | keyword bits only | P/T | cost | type | strict argmax flips, text | same-row different-card pairs tied |
|---|---|---|---|---|---|---|---|---|
| untrained, flag ON | 0.052 [0.049, 0.054] | 0.047 | 0.009 | 0.040 | 0.043 | 0.069 | 0.127 | 0 / 219 |
| M_W (W0Base, 3,072 ep) | 0.025 [0.021, 0.029] | 0.024 | 0.001 | 0.010 | 0.010 | 0.084 | 0.186 | 0 / 219 |
| M_D (BenchDimir, 3,072 ep) | **0.218 [0.195, 0.242]** | 0.219 | 0.003 | 0.067 | 0.125 | 0.327 | 0.116 | 0 / 219 |
| M_L (G1Landfall, 2,816 ep) | **0.102 [0.090, 0.116]** | 0.104 | 0.009 | 0.046 | 0.025 | 0.206 | 0.128 | 0 / 219 |

Phase 9's trained mains (flag OFF) were at ≤ 0.00004 on every row with 219/219 ties.

1. **The channel survived training in all three mains.** No pair of different cards offered through the same action row is tied any more (0/219 in every subject; mean |Δlogit| 0.09 / 0.83 / 0.44 for W / D / L), and swapping only a card's text flips the argmax on 12–19 % of affected consults.
2. **Against the pre-registered comparison** (text-only Δp vs the untrained flag-ON net): Dimir and landfall are **above** it with disjoint intervals (4.2× and 2.0×); the white main is **below** it (0.025 vs 0.052, disjoint) while its strict flip rate is higher (0.186 vs 0.127). The trained policies are far sharper than the untrained one (mean top gap 2.3–3.2 nats vs 0.38), so Δp is not scale-free across subjects; the flip rate is the steadier comparison, and on it none of the three has erased text sensitivity.
3. **The signal comes through the card embedding, not the explicit keyword bits**: swapping only the 18 keyword bits moves the trained mains by 0.001–0.009 with 0–4 % flips, while the embedding part carries essentially all of the text effect. Text moves each main more than P/T does (ratios 2.5 / 3.2 / 2.2).

Cannot: sensitivity is not use — this says the policy's output depends on which card it is, not that the dependence is correct play; the consult sets are W0Base and BenchDimir (the landfall main is scored on decks it did not train on); these are mid-run snapshots, and the Q7 row stays with the final checkpoints in the morning evaluation.

## 11 / A1-A2 — the Dimir and landfall census tools, validated on the Phase 9 recordings (2026-09-14; branch `v7/lane-d`; runbook `rl/PHASE11-DRILL.md`)

Tools: `rl/dimir_census.py`, `rl/landfall_census.py` (shared reader: teacher `y` labels, or the `{"a":k}` reply after a consult; an echo server's replies are ignored in teacher files), recorder `rl/record_census.sh` (A3; smoke deferred until Phase 10's evaluation ends). Outputs `rl/artifacts/v7/11/validation/` (summary `.txt` + per-game `.tsv`). Inputs: CP7 in the seat, `rec_cp7_dimir{,_b}.jsonl` (32 games, 29–3, 1,001 labelled consults; 103 unlabelled skipped) and the 8a-b policy (ck_512, argmax, frozen server) `rec_dim_dimir{,_b}.jsonl` (32 games, 10–22, 1,969 consults), BenchDimir vs the heuristic. Step one-hot checked on data: LAND is offered only in the sorcery window, and every LAND-offer consult has `v7_game[4]` (main1, 49) or `[8]` (main2, 4) set.

**Pre-registered first check — is ninjutsu ever OFFERED? Yes, to both seats; not an engine finding, no Java change.** Kaito's ninjutsu (an ACTIVATE candidate whose referent is Kaito in HAND) appears only on the seat's own turn in the declare-blockers or combat-damage step (0 hand-ACTIVATE offers anywhere else). Own declare-blockers consults are rare (CP7 14, DIM 22 of the step census), because the seat is consulted there only when something is playable (`RLPlayer.priority`: an empty `getPlayable` passes without a consult).

| counter | CP7 (reference) | DIM (8a-b ck_512) |
|---|---|---|
| ninjutsu windows (blockers / damage step) | 2 (2 / 0) | 7 (2 / 5) |
| ninjutsu taken | 1/2 = 0.50 [0.09, 0.91] | **0/7 = 0.00 [0.00, 0.35]** |
| attack turns with Kaito in hand and ≥ 3 untapped lands / of those with a blockers-step window | 0 / 0 | 3 / 2 |
| Kaito cast as a spell (of consults offering it) | 30/50, all main 1 | 35/53, all main 1 |
| flash card offered at instant speed → cast | 1/141 = 0.007 [0.001, 0.039] | **96/96 = 1.000 [0.962, 1.000]** |
| flash casts at instant speed (literal rule) | 1/96 = 0.010 [0.002, 0.057] | 96/120 = 0.800 [0.720, 0.862] |
| … of which on the opponent's turn or in response | 1 (Nowhere to Run, in response) | **0/120 = 0.000 [0.000, 0.031]**: own upkeep 51, own draw 43, own damage step 2 |
| counterspell offered → cast | 8/24 = 0.333 [0.180, 0.533] | **56/56 = 1.000 [0.936, 1.000]** |
| removal TARGET consults with ≥ 1 enemy creature | 0 (CP7 chooses targets inside the teacher; no consult, no reference) | 37 |
| highest-power enemy creature chosen | – | 34/37 = 0.919 [0.787, 0.972]; ≥ 2 enemy creatures: +0.192 [+0.077, +0.308] over chance 0.692 (n = 26, bootstrap) |
| tapped target chosen when an untapped one of ≥ power was legal | – | 0/7 |
| creatures cast per game | 3.81 [3.31, 4.31] | 4.19 [3.58, 4.79] |
| own turn of the first creature | 1.97 [1.52, 2.42] | 2.25 [1.64, 2.86] |
| land drops by own turn 4 | 3.56 [3.31, 3.81] | 3.50 [3.16, 3.84] |

Reading (32 games per seat — development-probe scale, not a level): the 8a-b policy is offered ninjutsu and never takes it, casts every counterspell and every flash card the moment it is castable, and aims removal at the largest enemy creature (+0.19 over chance with enemy targets only; P2's +0.162 counted own-side targets too). CP7 took ninjutsu once in two windows and holds counterspells two times in three. Opponent's-turn flash: neither seat was ever offered a flash card on the opponent's turn. 22 DIM opponent-turn priority consults held a flash card with enough untapped lands by count, and every one had only Hidden Lair (colourless, plus a conditional coloured ability), Soulstone Sanctuary (colourless) or Swamps untapped. So no blue source was open and nothing points at the driver: DIM spends its blue mana on its own turn. Cannots: the opportunity counter cannot see whether an attacker went unblocked (an upper bound); "affordable" counts lands, not colours; removal targeting on CP7 is not recordable through the teacher seat.

**Correction to 9 / P3 (in the open).** `rl/probes/instant_speed.py` sets `STEP_MAIN1, STEP_MAIN2 = 4, 8` and then reads `game[2 + STEP_MAIN1]`, i.e. `v7_game[6]` (declare-blockers) and `[10]` (holds priority, 1.0 in 339/375 consults of `rec_dim_dimir.jsonl`), so its "main phase" test was nearly always true, and "at instant speed" collapsed to "not the active player, or the stack is non-empty". Rerun with indices 2 / 6 (a scratchpad copy; the probe file is unchanged): **DIM 207/254 = 0.815 [0.763, 0.858], excluding counterspells 151/195 = 0.774 [0.711, 0.827]** (published 0.280 / 0.077); CP7 unchanged (14/148, 6/136: it casts only in main phases or in response). The published sentence "every flash creature (103 casts) went down at sorcery speed" is wrong. By the literal rule most went down at instant speed, but in DIM's own upkeep and draw step, never on the opponent's turn and never in response. The substantive P3 reading survives in a sharper form: DIM casts what is castable in the first window it gets (its own upkeep), which is neither flash play nor holding. The Phase 11 pre-registration's flash bar ("clear above the Phase 9 floor 0.077") was built on the bug. It is re-based in `rl/PHASE11-DRILL.md` Amendment 1 before any Part B data.

Landfall tool (A2): parse-checked only. There is no G1Landfall recording with a policy's choices yet; the 4-game wire echo `rl/artifacts/v7/wire3a/p10_G1Landfall_wire.jsonl` exercises every counter (land drops, precombat share, land search by step, landfall attacks with and without a prior land drop, block pairs). The `[audit]` parser was run on the two M_L replay transcripts (`rl/artifacts/v7/10/replay/M_L_*`): 9 combats, 8 policy block pairs, 7 small-into-big, of which the solver would not have blocked 5. Real validation = the A3 smoke.

## 10 / league run and Q5 — self-play per deck: home levels (2026-09-14; branch `v7/lane-d`; ONE seed per learner; fixed argmax-classes protocol; `rl/artifacts/v7/10/`)

**The run.** `rl/league10.py` ran from 03:57Z to 14:16Z WSL. The controller clock reached
10.32 h (the hard stop at hour 10 of the original clock, plus the block that was running) in
62 blocks of 256 episodes. It was stopped twice by STOP files, both resumed with the clock
continuing:
- 11:02–11:10Z for Amendment 3 (the stage-2 quota);
- 12:10–12:25Z, a pause the user asked for, for the interim card-swap check and the replays
  (resumed with `--hours 10.2`, recorded in the STATE lines).

| learner | blocks | episodes | training W / N | stalls |
|---|---|---|---|---|
| M_W (W0Base) | 16 | 4,096 | 2,207 / 4,096 | 78 |
| M_D (BenchDimir) | 16 | 4,096 | 1,814 / 4,096 | 10 |
| M_L (G1Landfall) | 15 | 3,840 | 1,768 / 3,840 | 2 |
| X_W / X_D / X_L | 5 each | 1,280 each | 341 / 471 / 398 | 6 / 5 / 0 |

Tables: `results.tsv` (one row per block, including bucket, draw, opponent, W/L/D/S and
probe), `pool.tsv`, `state.json`, `league10.log`. The pool `.pt` files are gitignored.

- M_W graduated at 1,024 (probe 0.74 [0.604, 0.841]); M_D and M_L never did.
- Stage 2 was **forced** at hour 5.10 (n = 27) with only M_W graduated. So M_W's cross pool
  was every other main, and M_D's and M_L's was M_W.
- Main per-block sampled training rates ran 0.10–0.74 (the per-block list is in
  `results.tsv`).

**Stage 1 had effectively no heuristic anchor (Amendment 3).** The draws gave the
heuristic 0 of 18 main picks. One heuristic block happened anyway, as a fallback: n = 5,
M_D, `expl->heur`, before any exploiter snapshot existed. So the realized share is 1/18
against the pre-registered 15 %. In stage 2 the quota produced 2–3 heuristic blocks per
main. This condition belongs to every Q5 reading below.

**Development probes** (50 games vs the heuristic on the own mirror; the first is at
trained = 0):

| main | 0 | 1024 | 2048 | 3072 | 4096 |
|---|---|---|---|---|---|
| M_W | 0.02 [0.004, 0.105] | 0.74 [0.604, 0.841] | 0.70 [0.562, 0.809] | 0.72 [0.583, 0.825] | 0.46 [0.330, 0.596] |
| M_D | 0.02 [0.004, 0.105] | 0.48 [0.348, 0.615] | 0.46 [0.330, 0.596] | 0.58 [0.442, 0.706] | 0.46 [0.330, 0.596] |
| M_L | 0.28 [0.175, 0.417] | 0.44 [0.312, 0.577] | 0.42 [0.294, 0.558] | 0.44 [0.312, 0.577] | (final at 3,840; no probe) |

**Home levels, final snapshots** (`rl/p10_eval.sh`, `eval/eval.log`; 100 games each; the
agent on its own deck):

| main | vs heuristic, own mirror | vs CP7 (skill 6), own deck | turns (heur / CP7) |
|---|---|---|---|
| M_W (M_W_04096) | **0.52 [0.423, 0.615]** | 0.62 [0.522, 0.709] | 13.5 / 20.9 |
| M_D (M_D_04096) | **0.59 [0.492, 0.681]** | 0.17 [0.109, 0.255] | 19.7 / 18.8 |
| M_L (M_L_03840) | **0.49 [0.394, 0.587]** | 0.37 [0.282, 0.468] | 11.8 / 12.5 |

No draws or stalls in any home row.

**Q5, as pre-registered:** "final home rate vs the heuristic clearly above its first
development probe AND at or above the deck's reference where one exists".
- **M_W: NOT met.** It is clear above its first probe (0.52 vs 0.02). It is **clear below**
  the W0Base reference, C1 0.86 [0.81, 0.90].
- **M_D: met.** It is clear above its first probe (0.59 vs 0.02). Its point is above the
  Dimir reference, 8a-b 0.41 [0.319, 0.508], but the intervals overlap by 0.016, so it is
  at or above the reference, not clear above it.
- **M_L: NOT met.** 0.49 against its first probe 0.28 [0.175, 0.417]: the intervals overlap
  (0.394 < 0.417). There is no reference; the heuristic mirror was 0.45 over 20 games (A3).

**M_W is a regression candidate, not flat.** Its three stage-1/early-stage-2 development
probes pool to 108/150 = 0.72 [0.643, 0.786]. The final 100-game home level, 0.52
[0.423, 0.615], is disjoint from that pool, and the 4096 probe is 0.46. The decline
coincides with stage 2. Between probe 3072 and probe 4096 it trained 4 blocks: cross vs
M_D (quota), heur (quota), pfsp, cross vs M_L (quota). Pooling three checkpoints' probes is
not a level. The direct test is M_W_s1end on the same 100-game home battery, which was
**not run: owed**. The same stretch took M_W's text sensitivity from 0.025 to 0.0023 (Q7).
That is a coincidence in time, not a shown cause.

**The same checkpoint, read twice.** M_D_04096 read 0.46 [0.330, 0.596] at 50 games (the
in-league probe) and 0.59 [0.492, 0.681] at 100 (the home battery), on different game seeds.
The intervals overlap; this is the Amendment 2 reason for using 50-game probes only for
development.

**Cannot:**
- one seed per learner; about 4k episodes per main;
- stage 1 ran without an anchor;
- stage 2 was forced with one graduate;
- the league lost 0.25 h to the two stops, both inside the hour-10 clock;
- the landfall deck has no reference;
- CP7 rows are single 100-game levels (M_W beats CP7 more often than it beats the heuristic;
  M_D is weak against CP7, 0.17).

## 10 / Q6 — cross-deck stage vs generalisation: "no difference shown" on the pool; per main one up, one down, one flat; and the cross matrix (2026-09-14; branch `v7/lane-d`; `rl/artifacts/v7/10/eval/`)

**Unseen-opponent suite.** Each main plays its own deck against the heuristic piloting
BenchBurn, HoldoutControl and HoldoutMidrange, 50 games each, pooled 150 per main. The same
game seeds are used for `_s1end` and final, so the rows are paired.
- `_s1end` is the stage-1/2 boundary snapshot, n = 27, 1,792 episodes each.
- Final is +2,304 (M_W, M_D) or +2,048 (M_L) stage-2 episodes on top.

| main | checkpoint | BenchBurn | HoldoutControl | HoldoutMidrange | pooled 150 |
|---|---|---|---|---|---|
| M_W | s1end | 0.82 | 1.00 | 0.50 | 116/150 = 0.773 [0.700, 0.833] |
| M_W | final | 0.48 | 1.00 | 0.58 | 103/150 = 0.687 [0.609, 0.755] |
| M_D | s1end | 0.24 | 0.70 | 0.18 | 56/150 = 0.373 [0.300, 0.453] |
| M_D | final | 0.54 | 0.82 | 0.56 | **96/150 = 0.640 [0.561, 0.712]** |
| M_L | s1end | 0.60 | 0.96 | 0.30 | 93/150 = 0.620 [0.540, 0.694] |
| M_L | final | 0.40 | 0.94 | 0.48 | 91/150 = 0.607 [0.527, 0.681] |

No draws or stalls.

**Pooled over all three mains, 450 games each:**
- `_s1end`: 265/450 = 0.589 [0.543, 0.633]
- final: 290/450 = 0.644 [0.599, 0.687]

**Q6, as pre-registered (on the pool): "no difference shown".** The intervals overlap
(0.599 < 0.633). The home clause cannot be read directly, because `_s1end` home at 100
games was not run. The in-league probes put M_W's final home below its stage-1 probes (the
Q5 regression candidate), so for M_W "home not clear below" is not established.

**Per main** (not the pre-registered reading; stated because the pool hides it):
- **M_D: clear up** (0.373 → 0.640, disjoint). Largest on BenchBurn (0.24 → 0.54) and
  HoldoutMidrange (0.18 → 0.56).
- **M_W: down, overlapping** (0.773 → 0.687). BenchBurn fell 0.82 → 0.48, disjoint at 50
  games each ([0.692, 0.902] vs [0.348, 0.615]).
- **M_L: flat** (0.620 → 0.607). BenchBurn down 0.20, Midrange up 0.18.

**Confounds, stated in advance and now:**
1. **More episodes.** Final has 2,048–2,304 more episodes than `_s1end`. The control
   (exploiter-and-self-only continuation) was not run.
2. **Few cross-deck episodes.** Each main played 3 cross-deck blocks in stage 2 (768
   episodes, a third of its stage-2 episodes), all after Amendment 3's quota. Before the
   quota, the draw gave none.
3. **The anchor came back at the same time.** Stage 2 is also where the heuristic returned
   (2–3 blocks per main, after 1/18 in stage 1). **Every unseen opponent is a heuristic
   pilot**, so M_D's gain is equally consistent with "re-exposure to the heuristic" as with
   "cross-deck play". This one run cannot separate them.
4. One seed.

A positive per-main reading is therefore "stage 2 (cross + anchor + more episodes)", never
"cross-deck".

**Cross matrix** (final mains against each other, each on its own deck, 50 games per pair,
`rl/p10_h2h.sh`, seats alternate):

| A vs B | A's wins | turns | stalls |
|---|---|---|---|
| M_W (W0Base) vs M_D (BenchDimir) | 26/50 = 0.52 [0.385, 0.652] | 17.8 | 0 |
| M_W (W0Base) vs M_L (G1Landfall) | 38/50 = **0.76 [0.626, 0.857]** | 13.8 | 0 |
| M_D (BenchDimir) vs M_L (G1Landfall) | 28/50 = 0.56 [0.423, 0.688] | 17.3 | 0 |

Only W over L is clear of 0.5. The deck and the policy are confounded in every cell (each
main plays only its own deck). Six debug-logged pairing games (one per seating), requested
by the user, are in `rl/artifacts/v7/10/pairs/` (the Dimir Requiting Hex play is in Q7).

**Addendum to Q6 (2026-09-14 ~15:50Z, from Phase 11; the row above is unchanged).** The home level of `M_D_s1end` (1,792 episodes), which this row did not have: **27/100 = 0.270 [0.193, 0.364]** vs the heuristic on the BenchDimir mirror, measured through the evaluation's own path (`rl/battery_xdeck.sh`, G=100, ports 7949 / 7915; `rl/artifacts/v7/11/check_s1end_battery/`). The Phase 11 census recorder agrees (10/50 = 0.20 [0.11, 0.33]; faithfulness check in `rl/PHASE11-DRILL.md` STATE). Against the final's 0.590 [0.492, 0.681], Dimir's stage-2 change is clear at home as well as on the unseen suite (0.373 → 0.640). The s1end snapshot sat in a dip below the 50-game probes of the 1,024 and 2,048 checkpoints (0.48 / 0.46). Reading: **for Dimir the stage-2 gain is general improvement out of a dip, not evidence of cross-deck generalisation specifically**. The Q6 pooled reading ("no difference shown") stands. Cannot: one seed; the dip's cause (the pfsp / self blocks around 1,536–1,792) is not isolated.

## 10 / Q7 — card use: the channel stays open in two of three mains; no keyword use shown (2026-09-14; branch `v7/lane-d`; final snapshots; artifacts `rl/artifacts/v7/10/eval/p1/`, `eval/eval.log`)

**P1 card swap.** `rl/p10_cardswap.py`, run exactly as the A2 gate ran it (2,004 consults,
the same pairs). The final mains are compared with the fresh flag-ON net (A2's
`init_on.pt`). Mean Δp, 95 % bootstrap CI:

| subject | text-only | P/T | type | vs fresh text | pre-registered reading |
|---|---|---|---|---|---|
| FRESH_ON (untrained) | 0.0516 [0.0490, 0.0542] | 0.0403 | 0.0688 | — | — |
| M_W (4,096 ep) | 0.0023 [0.0020, 0.0026] | 0.0010 | 0.0159 | 0.04× | **erased** (disjoint, below) |
| M_D (4,096 ep) | 0.2632 [0.2414, 0.2857] | 0.0651 | 0.2602 | 5.1× | **sharpened** (disjoint, above) |
| M_L (3,840 ep) | 0.0856 [0.0722, 0.1003] | 0.0490 | 0.2370 | 1.7× | **sharpened** (disjoint, above) |

Against the interim check (section "10 — interim card-swap check", 3d4c5dd; same probe,
same consult sets; M_W at 3,072 episodes):

| M_W measure | at 3,072 | final (4,096) |
|---|---|---|
| text-only mean Δp | 0.025 | 0.0023 |
| strict text flips | 0.186 | 0.058 [0.033, 0.087] |
| same-row different-card mean \|Δlogit\| | 0.087 | 0.022 (still 0/219 tied) |
| type flips | 0.167 | 0.167 |
| mean \|raw logit\| | — | 17.7 |

- **M_W's card sensitivity fell by an order of magnitude over its last 1,024 episodes.**
- M_D and M_L kept theirs: text Δp 0.263 and 0.086 (interim 0.218 and 0.102), strict text
  flips 0.062 and 0.097.

**Neither Δp nor the flip rate is scale-free.** Every trained main has a lower strict flip
rate than the fresh net (0.127), because the trained policies are sharper. The ratios
compare sensitivity, not use.

**Reading.** Dimir and landfall preserved or sharpened their card-text sensitivity. The
white main largely lost it during stage 2. That is the same stretch in which its home level
fell from about 0.72 (pooled probes) to 0.52 and its unseen-deck rate from 0.77 to 0.69.
In one seed this is a coincidence, not a demonstrated cause, but it is worth naming.

**Keyword decks** (zero-shot for M_W, 50 games each). The agent is on W1X; the opponent is
the heuristic on W0Base. M_W's reference is its W0Base home, 52/100 = 0.52
[0.423, 0.615]. The heuristic's own shift is the heuristic piloting W1X against the
heuristic on W0Base:

| deck | M_W | heuristic (same pairing) | M_W − W0Base home | heuristic − its W0Base 0.60 |
|---|---|---|---|---|
| W1Fly | 0.60 [0.462, 0.724] | 0.44 [0.312, 0.577] | +0.08 | −0.16 |
| W1Lif | 0.64 [0.501, 0.759] | 0.44 [0.312, 0.577] | +0.12 | −0.16 |
| W1Fst | 0.64 [0.501, 0.759] | 0.58 [0.442, 0.706] | +0.12 | −0.02 |
| W1Vig | 0.54 [0.404, 0.670] | 0.62 [0.482, 0.741] | +0.02 | +0.02 |

**Q7 keyword reading: "uses keyword X" is not shown for any X.** No W1X rate is clear above
the W0Base home rate. Directionally, M_W holds or gains on the flying and lifelink decks,
where the heuristic loses 0.16. That is suggestive at n = 50 with every interval
overlapping, and it sits beside M_W's near-zero final text sensitivity, which argues against
M_W reading its keywords.

**What the transcripts show** (`rl/artifacts/v7/10/replay/`: M_W / M_D / M_L at 3,072 vs the
heuristic and vs CP7, debug-logged; `rl/artifacts/v7/10/pairs/`: the six cross-deck pairing
games of the final mains, both seatings):
- In **both** of its pairing games, the Dimir main casts **Requiting Hex on turn 3 at its own
  Spyglass Siren**. The transcript line is `KILL Spyglass Siren 1/1 (MINE) [of 1, 0 enemy]`:
  the enemy board was empty, so its own creature was the only legal target. The spell reads
  "target creature with mana value 2 or less", any controller; the main session checked this
  in the engine.
- It lost that game against M_W (14 turns) and won it against M_L (15 turns).
- So the SPELL decision to cast removal into an empty enemy board is taken with the
  card-sensitive scorer. **Sensitivity is not use**: M_D has the largest text effect of any
  subject and still makes this play.

**Cannot:**
- the consult sets are W0Base and BenchDimir, so the landfall main is scored off its deck;
- Δp compares sensitivity across policies of different sharpness;
- the keyword decks are 50-game rows;
- there are two pairing transcripts per pair (anecdote, not rate).

## 10 / league health — exploiters (2026-09-14; from `rl/artifacts/v7/10/results.tsv`)

Each exploiter's block win rate against the frozen latest of its main, 256 episodes per
block:

| exploiter | gen 0: block 1 | block 2 | block 3 | block 4 → reset | gen 1: block 1 |
|---|---|---|---|---|---|
| X_W (vs M_W) | 0.14 | 0.11 | 0.40 | 0.32 → reset (4 blocks) | 0.36 (vs M_W_03328) |
| X_D (vs M_D) | **0.61** | 0.52 | 0.35 | 0.36 → reset (4 blocks) | 0.004 (1/256, vs M_D_03584) |
| X_L (vs M_L) | 0.40 | 0.41 | 0.28 | 0.35 → reset (4 blocks) | 0.12 (vs M_L_03840) |

- **Three resets, all by the 4-block rule; none by winning.** No block reached 0.70.
- **None was added to its main's PFSP pool.** Every 4th-block rate was below 0.55.
- Stalls in exploiter blocks: 6 / 5 / 0.

The health counter, as pre-stated ("should fall as mains harden"):
- It falls for X_D (0.61 → 0.36; the Dimir main was beatable early by a fresh net).
- It does not fall monotonically for X_W (0.14 → 0.40 → 0.32) or X_L (flat 0.28–0.41).
- A fresh gen-1 exploiter's first block is far below the gen-0 exploiter's last. That is
  what one 256-episode block from scratch buys, not a hardening measurement.
- **No exploiter beats its final main at ≥ 0.70**, so "exploitable" is not shown. But these
  exploiters had 5 blocks each (1,280 episodes), so this is weak evidence that the mains are
  not exploitable.

**PFSP had little to work with.** Main PFSP pools held only the mains' own past snapshots.
The per-snapshot p values mostly sit near 0.5–0.7, so the (1 − p)² weights stayed close to
uniform.

## Phase 10 verdict (2026-09-14)

Opening the candidate-to-card path (`--cand-refers-pool`) made the untrained scorer
card-sensitive (text Δp 0.052 vs 0.000; gate passed). Fresh per-deck self-play leagues with
it then trained three mains in about 4k episodes each (one seed, stage 1 without a
heuristic anchor). Only the Dimir main meets the pre-registered Q5:

| main | home vs heuristic (100) | reference | note |
|---|---|---|---|
| M_D (Dimir) | 0.59 [0.492, 0.681] | 8a-b 0.41 | meets Q5 |
| M_L (landfall) | 0.49 [0.394, 0.587] | none | not clear above its first probe, 0.28 |
| M_W (W0Base) | 0.52 [0.423, 0.615] | C1 0.86 | clear below the reference; regression candidate from 0.72 pooled stage-1 probes |

The cross-deck stage shows **no difference** on the pre-registered pooled unseen-opponent
suite: 265/450 = 0.589 [0.543, 0.633] at `_s1end` vs 290/450 = 0.644 [0.599, 0.687] final.
The per-main split is M_D clear up (0.37 → 0.64), M_W down (0.77 → 0.69), M_L flat. That
split is confounded by more episodes and by the heuristic anchor returning in stage 2.

Card-text sensitivity was sharpened in M_D (0.263) and M_L (0.086) but largely erased in M_W
(0.0023, during stage 2). No keyword use is shown, and sensitivity is not use: the most
card-sensitive main casts Requiting Hex on its own creature.

## 11 — pre-registration and amendments (2026-09-14; runbook `rl/PHASE11-DRILL.md`, whose "Pre-registered readings" and Amendments 1–3 are the record)

- **Pre-registration** (runbook Part B): the drill-down continuation of M_D and M_L from their Phase 10 state (M_W frozen at M_W_04096 as a cross-deck member; stage-2 mix with the quota; block 256; +4,096 episodes per main). Levels = 100-game probes vs the heuristic on the own mirror at +1,024 / +2,048 / +3,072 / +4,096. Readings: keeps growing / plateau / regresses, and the card-use counters of the A1/A2 census (final vs `M_D_s1end` / `M_L_s1end` vs the CP7 reference).
- **Amendment 1** (before Part B data): the flash bar becomes "flash casts on the opponent's turn or in response, clear above the corrected Phase 9 8a-b level 0/120 [0.000, 0.031]". It was built on P3's mis-indexed rule (correction in "11 / A1-A2").
- **Amendment 2** (before Part B data, from the Phase 10 pairing games): a new counter, removal cast when the only legal targets are the seat's own creatures (offered / taken). A correct policy takes it at 0.
- **Amendment 3** (the user, 16:20Z, after drill blocks 0–2 and before any B2 census): a 50-game heuristic census after every main block, one `L11|check` line each. These are development probes; the 100-game points stay the levels; CP7 census (25 games) at +2,048 / +4,096; the stop moves from controller hour 10 to hour 13 (~04:50Z) to absorb the census overhead; the two saturated landfall counters stay out of the check line until verified.

## 11 — measurement check: Requiting Hex's blight cost vs its destroy target (2026-09-14 ~18:45Z; the self-removal figures stand)

Question (coordinator, from the n009 transcripts): Requiting Hex has an optional additional cost, blight 1 (put a -1/-1 counter on a creature *you control*, gain 2 life), beside "destroy target creature with mana value ≤ 2". RLPlayer's transcript labels **every** creature target the seat picks as `KILL … (MINE) [of N, E enemy: …]` (its target-choice audit, `RLPlayer` ~l.474), so the blight choice prints as a KILL too. Example: seed 11022 t15 "KILL Elektra 3/3 (MINE) [of 3, 0 enemy: Elektra 3/3, Curiosity 4/3, Siren 1/1]" offers creatures with mana value 3 and 4, so it is the blight cost. The destroy target had one legal choice, the seat's own Spyglass Siren. The driver picks a single legal target without a consult. Afterwards the board is "creatures 2-0" with Elektra a 2/2, so the Siren was destroyed and Elektra blighted.

Does the published self-removal counter include blight choices? **No.** The Amendment 2 counter is spell-level: a cast of Requiting Hex, Bitter Triumph or Shoot the Sheriff while every legal destroy target on the battlefield is the seat's own (`self_only` in `rl/dimir_census.py`). It does not read any TARGET consult. Checked against the engine: over every recording below, **0** destroy-target consults offered an enemy creature while the filter said own-only. So 14/19 (Phase 9 8a-b), 23/23 + 7/7 (B1 M_D final vs heuristic / CP7), 24/24 (drill n003), 24/50 (n006) and 28/28 (n009) are casts that destroyed the seat's own creature, and the Phase 10 Q7 pairing-game note stands (the Siren was the only legal destroy target). What *did* include blight is the census line's secondary "target level: first target consult after the cast, own creature chosen" field. It appeared only in the census count files, never in a published table, and is replaced from now on.

Split (the census tool now reports it; destroy vs blight is told apart by the consult's candidates: an own creature with mana value > 2, or a second consult for the same cast, or a sole legal destroy target, means blight):

| recording | RH casts | forced self-destroy (all legal destroy targets own) | destroy-target consults (own chosen) | blight paid through a consult | … on an X/1 (the blight killed it) | … during forced self-destroy casts |
|---|---|---|---|---|---|---|
| Phase 9 8a-b (32 g) | 39 | 10 | 20 (3) | 27 | 18 | 10 |
| B1 M_D final vs heuristic (50 g) | 40 | 13 | 17 (3) | 29 | 13 | 13 |
| B1 M_D final vs CP7 (25 g) | 23 | 4 | 9 (1) | 10 | 5 | 4 |
| B1 M_D_s1end vs heuristic (50 g) | 8 | 2 | 5 (1) | 6 | 2 | 2 |
| drill n003 (50 g) | 45 | 15 | 15 (4) | 30 | 15 | 15 |
| drill n006 (50 g) | 40 | 17 | 8 (1) | 25 | 13 | 17 |
| drill n009 (50 g) | 44 | 18 | 14 (3) | 29 | 15 | 18 |

Reading: the Dimir main pays blight in most of its Requiting Hex casts, and in **every** forced self-destroy cast in these recordings. About half its blights land on an X/1 and kill that creature. So a single forced cast often costs two of its own creatures (the destroyed one and a blighted X/1). Blight is only visible when it is paid through a consult: a single own creature is chosen without one, so these counts are lower bounds. Whether the optional cost is offered as a separate yes/no choice is not measured. Also corrected: the `*_games.tsv` files written by the census before this change have a header 3 names short of their 21 columns (the self-removal columns); the tool writes 21 names from now on.

## 11 / B1 — baseline census of the Phase 10 mains (2026-09-14; 50 argmax games vs the heuristic + 25 vs CP7 per checkpoint, own mirror; development-probe scale)

`rl/run_b1_census.sh` → `rl/record_census.sh` (frozen eval server, record proxy, fresh driver JVM). It is faithful to the evaluation battery: `M_D_s1end` scored 10/50 in the recorder vs 27/100 = 0.270 [0.193, 0.364] through `battery_xdeck.sh`, and `M_D_04096` 25/50 vs the evaluation's 0.590 (section "Addendum to Q6"). Table `rl/artifacts/v7/11/b1_summary.txt`; per row `rec_b1_*.counts.txt`.

| checkpoint vs | win rate | removal cast with only own creatures legal | counterspell cast / offered | flash cast on opp. turn or in response | ninjutsu taken / offered | removal on the biggest enemy | creatures / game |
|---|---|---|---|---|---|---|---|
| M_D_s1end (1,792) vs heuristic | 0.200 [0.112, 0.330] | 2/432 | 4/102 | 9/56 | 3/3 | 2/8 | 2.40 |
| M_D_s1end vs CP7 | 0.000 [0.000, 0.133] | 1/33 | 3/40 | 4/17 | 1/1 | 1/2 | 1.48 |
| M_D final (4,096) vs heuristic | 0.500 [0.366, 0.634] | 23/23 | 54/56 | 1/173 | 6/6 | 37/44 | 4.34 |
| M_D final vs CP7 | 0.280 [0.143, 0.476] | 7/7 | 26/26 | 0/74 | 1/1 | 18/24 | 3.44 |

| checkpoint vs | win rate | small-into-big block pairs (solver would not block) | land search cast / offered | creatures / game |
|---|---|---|---|---|
| M_L_s1end vs heuristic | 0.320 [0.208, 0.458] | 121/187 (43/106) | 127/282 | 5.26 |
| M_L_s1end vs CP7 | 0.320 [0.172, 0.516] | 71/72 (31/63) | 72/135 | 5.12 |
| M_L final (3,840) vs heuristic | 0.580 [0.442, 0.706] | 9/13 (1/6) | 98/248 | 4.12 |
| M_L final vs CP7 | 0.200 [0.089, 0.391] | 13/14 (2/12) | 57/114 | 3.44 |

Reading: between its stage-1 end and its final checkpoint, the Dimir main moved from holding its cards to firing everything castable. That includes destroying its own creature every time removal had only its own creatures as legal targets (30/30; blight is counted separately in "11 — measurement check"). It never casts a flash card on the opponent's turn. The landfall main's final blocks far less (13 small-into-big block pairs in 50 games vs 187), and the blocks it makes are mostly ones the solver agrees with. The precombat land-drop share and landfall-attack counters read 1.000 on every row. They look saturated, are not verified against a transcript, and are not reported.

## 11 / B2 — the drill-down continuation: STOPPED EARLY BY USER DECISION at the +2,048 point (2026-09-14; branch `v7/lane-d`)

Run: `rl/league11.py` (= `rl/league10.py` plus the Phase 11 changes: seeded from the Phase 10 state with the lane dirs copied, M_W frozen at M_W_04096, cross over every other main, 100-game levels every +1,024) via `rl/chain11.sh` after B1.
- It started at 15:50:21Z.
- It was stopped once by stopfile for Amendment 3, the per-block census (`--census-every-block`), and resumed at 16:39Z with `--hours 13`.
- **The user stopped it at ~21:55Z.** The main session killed it mid-block (`rl/stop_drill11.sh`) while exploiter X_D was training. That block, n=26, was lost; no learner state was lost. The last completed blocks are n=24 (M_D, 6,400 episodes) and n=25 (M_L, 6,144).
- Of the 26 blocks, 18 were for the mains. Their opponents: M_D cross 3 / self 3 / pfsp 1 / expl 1 / heur 1; M_L cross 3 / pfsp 3 / self 1 / expl 1 / heur 1. That is **16 of 18 against league-internal opponents, 2 against the heuristic and 0 against CP7**.
- Exploiters X_D and X_L (4 blocks each, mean training win rate 0.13 / 0.18) both reset after 4 blocks without entering a pool.

Artifacts: `rl/artifacts/v7/11/drill/` (league11.log, results.tsv, state.json, census_lines.txt) and `rl/artifacts/v7/11/rec_drill_*`.

**Levels (100 games vs the heuristic, own mirror; the pre-registered yardstick):**

| main | start (P10 evaluation) | +1,024 | +2,048 | +3,072 / +4,096 | vs CP7 (not a pre-registered level) |
|---|---|---|---|---|---|
| M_D | 0.590 [0.492, 0.681] | 0.620 [0.522, 0.709] | 0.590 [0.492, 0.681] | not reached | 0.170 [0.109, 0.255] (P10, 100 g) → 5/25 = 0.20 [0.089, 0.391] at +2,048 |
| M_L | 0.490 [0.394, 0.587] | 0.410 [0.319, 0.508] | 0.530 [0.433, 0.625] | not reached | 0.37 (P10, 100 g) → 3/25 = 0.12 [0.042, 0.300] at +2,048 |

Pre-registered reading: **plateau for both mains** (every point inside the first point's interval), on **two of the four planned points**. The CP7 rows are 25-game checks, not levels.

**Per-block census (Amendment 3; 50 argmax games vs the heuristic after every main block, seed 11000 each time; development probes). This is the main result:**

| M_D block (episodes) | win / 50 | self-destroy cast / offered | counterspell | flash on opp. turn / resp. | ninjutsu | biggest | creatures / game | consults / game |
|---|---|---|---|---|---|---|---|---|
| n3 (4,608) | 27 | 24/24 | 61/61 | 2/166 | 8/10 | 35/42 | 4.60 | 63.5 |
| n6 (4,864) | 22 | 24/50 | 33/148 | 30/123 | 2/12 | 19/26 | 3.50 | 88.2 |
| n9 (5,120) | 24 | 28/28 | 58/61 | 5/172 | 10/10 | 32/37 | 4.46 | 35.9 |
| n12 (5,376) | 29 | 30/32 | 72/85 | 22/162 | 5/6 | 37/44 | 4.26 | 48.4 |
| n15 (5,632) | 29 | 28/38 | 51/83 | 49/107 | 6/6 | 28/38 | 3.10 | 94.9 |
| n18 (5,888) | 23 | 17/43 | 22/127 | 50/57 | 11/11 | 28/34 | 1.90 | 106.4 |
| n21 (6,144) | 30 | 25/40 | 35/88 | 39/153 | 7/8 | 32/41 | 4.14 | 63.7 |
| n21 vs CP7 (25 g) | 5/25 | 12/16 | 15/42 | 12/64 | 2/2 | 10/15 | 3.40 | 69.6 |
| n24 (6,400) | 25 | 25/25 | 61/68 | 6/170 | 6/8 | 35/46 | 4.54 | 61.4 |

| M_L block (episodes) | win / 50 | small-into-big block pairs (solver would not block) | land search cast / offered | creatures / game | consults / game |
|---|---|---|---|---|---|
| n4 (4,352) | 27 | 5/13 (1/2) | 99/231 | 4.08 | 23.4 |
| n7 (4,608) | 28 | 35/57 (12/32) | 112/715 | 4.56 | 35.9 |
| n10 (4,864) | 24 | 92/171 (29/83) | 131/324 | 5.34 | 32.0 |
| n13 (5,120) | 17 | 118/195 (47/108) | 130/294 | 5.40 | 36.4 |
| n16 (5,376) | 21 | 109/183 (36/96) | 121/317 | 5.40 | 33.5 |
| n19 (5,632) | 19 | 79/136 (18/70) | 106/698 | 4.94 | 38.7 |
| n22 (5,888) | 30 | 45/74 (10/39) | 98/576 | 4.70 | 33.0 |
| n22 vs CP7 (25 g) | 3/25 | 35/40 (9/29) | 53/368 | 4.00 | 32.2 |
| n25 (6,144) | 25 | 48/76 (13/43) | 90/1,225 | 4.48 | 46.2 |

Readings:
- **Dimir's card use swung and did not converge.** Its counters went through three full swings between "cast everything" and "hold everything". Cast everything: self-destroy about 1.0, counterspells about 1.0, flash on the opponent's turn about 0.02, 35–64 consults per game (n3, n9, n12, n24). Hold everything: counterspells 0.17–0.61, flash on the opponent's turn up to 0.88, creatures per game down to 1.9, 88–106 consults per game (n6, n15, n18). The self-destroy counter never settled near CP7's 0 (0.40–1.00 across the run; CP7 0/164 in the Phase 9 reference).
- **Landfall's block restraint eroded.** The small-into-big block count went from the Phase 10 final's 13 per 50 games back to the stage-1-end level (171–195 at n10–n16, 76 at n25). The small-into-big share of blocks stayed about 0.6 throughout. So what changed is how often it blocks, not how it picks. Land search swung to being held: the cast count stayed at 90–131 while the offers grew to 1,225.
- **The win rate barely moved through all of this.** It stayed at 22–30 of 50 for M_D and 17–30 of 50 for M_L.

**Leading hypothesis (put forward by the user): self-play drift.**
- About 90 % of the training opponents are league-internal and move with the learner (16 of 18 main blocks here). The only fixed opponent is the heuristic, at about 10 % (2 blocks). CP7 is absent from the training pool. The exploiters never entered a pool in five resets (Phase 10 and here).
- Supporting evidence: in-league win rates of 70–87 % against flat fixed-opponent levels (Phase 10 rows; here M_D beat its own M_D_01792 216/256 = 0.84 in block n9 while its heuristic level stayed at 0.59–0.62). The oscillation of card use between opposite policies with a flat heuristic win rate is what a learner chasing moving opponents would show. The project's best result, L0 (0.91 at +1,024), was a continuation trained against the heuristic only.
- **What it does not prove:** this is one seed per main. There was no control arm on fixed opponents in this phase. The coarse terminal reward (win / loss only) would also flatten the levels on its own. The per-block censuses are 50-game development probes.

Also recorded in Phase 11: the recorder-faithfulness check (5be785c), the Q6 addendum (169d6ba), census transcripts kept per recording (69b0843), the Requiting Hex blight / destroy measurement check (3014f62; the self-destroy figures stand), and the correction to 9 / P3 (d2a8b45).

## Phase 11 verdict (2026-09-14)

**Dimir:** over +2,048 episodes of league continuation its heuristic level did not move (0.59 → 0.62 → 0.59; plateau on two of the four planned points), and against CP7 it stayed low (0.20 [0.089, 0.391] over 25 games at +2,048, vs 0.17 at the start). Its card use did not converge. Per-block censuses swung three times between casting everything (self-destroy about 1.0, counterspells about 1.0, flash on the opponent's turn about 0.02) and holding everything (counterspells 0.17–0.61, flash on the opponent's turn up to 0.88, 1.9 creatures per game). It never stopped destroying its own creatures when removal had only its own targets (0.40–1.00, vs CP7's 0/164).

**Landfall:** also a plateau (0.49 → 0.41 → 0.53 vs the heuristic), and 0.12 [0.042, 0.300] vs CP7 at +2,048. Its Phase 10 block restraint (13 small-into-big pairs per 50 games) eroded back to the stage-1-end level (up to 195), and its land search swung to being held (90 cast of 1,225 offers).

The leading hypothesis is self-play drift: 16 of 18 main blocks faced league-internal opponents that move with the learner, the heuristic was the only fixed opponent, and CP7 was never in the pool. That motivates a CP7 warm start to competence before any self-play league (`rl/PHASE12-CP7.md`). It rests on one seed and no fixed-opponent control, and the coarse terminal reward alone could also flatten the levels.

## 12 — pre-registration, amendments and start points (2026-09-14; runbook `rl/PHASE12-CP7.md`, branch `v7/lane-d`)

Why: the Phase 11 drill-down was stopped by the user (see "Phase 11 verdict"); the leading
hypothesis is self-play drift. Phase 12 warm-starts each deck main against a fixed opponent mix:
75 % CP7 (`rl.aiSkill` 6) / 25 % heuristic on the own mirror, the Phase 10/11 learner recipe
unchanged (lr 3e-5, 1 epoch, logit bound 5, AdamW wd 0.01 on the heads, `--adv-norm batch`,
`--target-kl 0.02`, `--argmax-classes`, `--cand-refers-pool`). **Graduated** = a 100-game level vs
CP7 on the own mirror ≥ 0.70 AND Wilson lower bound ≥ 0.60, measured every 1,024 episodes, with a
50-game heuristic guard at the same points and the 3-deck unseen suite (heuristic on BenchBurn /
HoldoutControl / HoldoutMidrange, 50 each) at the start, at graduation and at the end. The
pre-registered readings (competent / improving vs CP7 / over-fit to CP7 / Dimir card habits converge
/ landfall / the drift-hypothesis test) and the cannots are in the runbook and are not restated here.
Controller `rl/phase12.py` (runner `rl/run_phase12.sh`; `rl/stop_p12.sh`, `rl/kill_p12.sh`); log
`rl/artifacts/v7/12/phase12.log`; `results.tsv`, `levels.tsv`, `census_lines.txt` beside it.

**Amendment 1 (before any data): implementation choices.** The 75/25 mix is realised exactly by the
fixed rotation cp7, heuristic, cp7, cp7 per main (Phase 10's Amendment 3 showed random draws
under-delivering a small bucket). Battery row seeds and the census seed (12500) are fixed, so every
level and every check sees the same deals (points are paired). The start point is CP7 100 +
heuristic 50 (the guard's size) + unseen 150 + the 25-game CP7 census. M_W's unseen rows are Phase
10's own rows of the same checkpoint on the same suite, reused, not re-run. The white check has no
census tool; it uses the block/attack audit lines and `rl/dimir_census.py`'s board line for creatures
per game, a field not validated on W0Base. Snapshots carry no optimiser state, so AdamW starts fresh.

**Amendment 2 (user, ~23:45Z, before any M_D level beyond the start): tonight is Dimir only.** The
controller was stopped gracefully after M_D's first block and its check. No M_L or M_W block had
run. Landfall and white are paused at their start points, with their state saved untouched; their
readings are **deferred, not dropped**. M_D continues with everything else identical (rotation,
checks, levels, guard, graduation rule, seeds, the hour-10.5 stop from the 22:24Z start).
Consequence: tonight's drift-hypothesis test rests on one deck and one seed.

**Start points** (argmax protocol of `rl/battery_xdeck.sh`; the unseen suite pooled over 150):

| main | start snapshot (episodes) | vs CP7, own mirror (100) | vs heuristic, own mirror (50) | unseen suite (150) | BenchBurn / HoldoutControl / HoldoutMidrange |
|---|---|---|---|---|---|
| M_D (BenchDimir) | M_D_06400 (6,400) | 19/100 = 0.190 [0.125, 0.278] | 35/50 = 0.700 [0.562, 0.809] | 98/150 = 0.653 [0.574, 0.725] | 29 / 39 / 30 |
| M_L (G1Landfall) | M_L_06144 (6,144) | 35/100 = 0.350 [0.264, 0.447] | 23/50 = 0.460 [0.330, 0.596] | 93/150 = 0.620 [0.540, 0.694] | 25 / 48 / 20 |
| M_W (W0Base) | M_W_s1end (1,792) | 58/100 = 0.580 [0.482, 0.672] | 33/50 = 0.660 [0.522, 0.776] | 116/150 = 0.773 [0.700, 0.833] | 41 / 50 / 25 (Phase 10 rows) |

**Start checks** (25 CP7 games, own mirror, seed 12500):
- M_D: 4/25. Removal cast with only its own creatures as legal targets 7/7; counterspell windows taken 31/38; flash on the opponent's turn 5/74; ninjutsu 2/3; highest-power enemy chosen 18/24; 3.84 creatures per game.
- M_L: 11/25. Small-into-big blocks 27/32, of which the combat search would not block 15/24; land search cast 42/738; 4.76 creatures per game.
- M_W: 16/25. Blocks matching the combat search 92/119; attacks declared 225/245 windows; attack audit MATCH 104/245; 10.88 creatures per game (field unvalidated for this deck).

What the start points cannot support: a 50-game guard is a development probe, not a level. The M_D
heuristic start (0.70) sits above the Phase 11 100-game level at +1,024 (0.62, 5,120 episodes), but a
different snapshot and different deals are involved, and the intervals overlap. CP7 levels are
paired across points only through the fixed seeds; the policy changes, so the deals diverge after
the first decisions.

Throughput: M_D's first block against CP7 ran 256 episodes in 1,249 s, 738 episodes/h. That is
1.39 h of lane time per 1,024 episodes, plus ~5.5 min per 25-game check and ~0.25 h per level
point.

### 12 / M_D — first level point, +1,024 episodes (2026-09-15 ~01:15Z WSL; Dimir only, Amendment 2)

**Level at 7,424 episodes (+1,024; blocks cp7, heuristic, cp7, cp7):** CP7 on the own mirror
**18/100 = 0.180 [0.117, 0.267]** (0 stalls) against the start's 19/100 = 0.190 [0.125, 0.278].
Heuristic guard 32/50 = 0.640 [0.501, 0.759] against 35/50 = 0.700. Not graduated.

Training blocks (sampled play, the block's own opponent):

| n | opponent | W/L/D/S | win rate | wall |
|---|---|---|---|---|
| 0 | cp7 | 43/213/0/0 | 0.168 | 1,249 s |
| 1 | heuristic | 123/132/1/1 | 0.480 | 503 s |
| 2 | cp7 | 40/216/0/0 | 0.156 | 1,389 s |
| 3 | cp7 | 35/221/0/0 | 0.137 | 1,422 s |

Per-block CP7 checks (25 argmax games, own mirror, seed 12500; start = the start snapshot):

| check | trained | CP7 wins | selfrem (only own legal targets → cast) | counter taken | flash on opp turn | ninjutsu | biggest | creatures/game | consults/game |
|---|---|---|---|---|---|---|---|---|---|
| start | 6,400 | 4/25 | 7/7 | 31/38 | 5/74 | 2/3 | 18/24 | 3.84 | 61.2 |
| n=0 | 6,656 | 7/25 | 8/9 | 32/44 | 3/83 | 3/3 | 23/24 | 4.32 | 68.8 |
| n=1 | 6,912 | 6/25 | 6/115 | 6/88 | 0/73 | 0/0 | 11/12 | 3.72 | 71.3 |
| n=2 | 7,168 | 5/25 | 2/255 | 7/105 | 23/62 | 1/5 | 7/8 | 3.32 | 105.9 |
| n=3 | 7,424 | 4/25 | 5/258 | 3/103 | 8/66 | 1/1 | 13/16 | 3.60 | 85.0 |

**Reading at this point.** Vs CP7 the level is flat after +1,024: 0.19 → 0.18, the intervals
almost identical. The sampled training win rate vs CP7 edged down across the three CP7 blocks
(0.168, 0.156, 0.137), a trend the 256-game blocks cannot separate from noise.

The card counters moved sharply toward "hold" in one step, right after the heuristic block (n=1),
and have stayed there for three checks. Self-destroy is now near CP7's own 0/164: 6/115, 2/255,
5/258. But counterspells are almost never cast (0.07, 0.07, 0.03 of the windows offering one;
CP7 ~0.33), and games are longer (consults per game 69 → 106 → 85).

In the pre-registered terms, one clause is on track and one is off. The selfrem clause (below 0.3
over the last four checks) has three checks in, all below. The counter-selectivity clause
([0.2, 0.5] over the last four) is outside its range at every check since n=1. Creatures per game
has stayed ≥ 3 (3.32–4.32).

**No pre-registered reading fires yet.** This is one level point of up to five tonight, and every
convergence clause needs four checks.

What this cannot support: whether "hold" is a settled habit or the first half of another Phase 11
swing; only the next checks can tell. Also out of reach: whether the heuristic block caused the
step or merely preceded it. The n=0 → n=1 step also coincides with the second block after
AdamW's fresh start (Amendment 1).

The selfrem denominators grew 9 → 115–258. Removal windows where only own creatures were legal
became far more frequent once the policy held its removal, so the rates at n=0 and n=1..3 are on
very different bases.

**Amendment 3 (user, ~02:20Z 2026-09-15): stop extended.** Training for M_D now stops at
controller hour 12 from the 22:24Z start, meaning no new block after ~10:24Z instead of ~08:54Z.
The end phase (final 100-game CP7 level, 50-game heuristic guard, unseen suite) follows as
before. The change was applied at a block boundary: a graceful stop after block n=6 and its check,
then a relaunch with `--mains M_D --hours 12`. No other change: the level cadence (every 1,024
episodes), the rotation, the checks, the seeds and the graduation rule are all unchanged. M_L and
M_W remain paused.

### 12 / M_D — second level point, +2,048 episodes (2026-09-15 ~03:20Z WSL)

**Level at 8,448 episodes (+2,048):** CP7 on the own mirror **9/100 = 0.090 [0.048, 0.162]**
(0 stalls). Heuristic guard **25/50 = 0.500 [0.366, 0.634]**. Not graduated.

| point | trained | CP7 (100) | heuristic guard (50) |
|---|---|---|---|
| start | 6,400 | 19/100 = 0.190 [0.125, 0.278] | 35/50 = 0.700 [0.562, 0.809] |
| +1,024 | 7,424 | 18/100 = 0.180 [0.117, 0.267] | 32/50 = 0.640 [0.501, 0.759] |
| +2,048 | 8,448 | 9/100 = 0.090 [0.048, 0.162] | 25/50 = 0.500 [0.366, 0.634] |

Training blocks n=4..7 (sampled play):

| n | opponent | W/L/D/S | win rate | wall |
|---|---|---|---|---|
| 4 | cp7 | 42/214/0/0 | 0.164 | 1,379 s |
| 5 | heuristic | 155/101/0/0 | 0.605 | 579 s |
| 6 | cp7 | 41/215/0/0 | 0.160 | 1,365 s |
| 7 | cp7 | 45/211/0/0 | 0.176 | 1,348 s |

Per-block CP7 checks n=4..7 (25 argmax games, seed 12500; n=0..3 are in the first-level table
above):

| check | trained | CP7 wins | selfrem | counter taken | flash on opp turn | ninjutsu | biggest | creatures/game | consults/game |
|---|---|---|---|---|---|---|---|---|---|
| n=4 | 7,680 | 6/25 | 4/294 | 3/92 | 9/49 | 0/3 | 11/12 | 3.00 | 97.8 |
| n=5 | 7,936 | 3/25 | 4/57 | 6/95 | 6/47 | 1/11 | 6/7 | 2.88 | 89.8 |
| n=6 | 8,192 | 4/25 | 7/154 | 2/80 | 10/66 | 1/2 | 13/24 | 3.72 | 80.6 |
| n=7 | 8,448 | 2/25 | 1/148 | 6/81 | 8/38 | 1/1 | 9/12 | 2.36 | 100.2 |

**Reading at +2,048, in the pre-registered terms.**

- **Both yardsticks are falling.** CP7: 0.19 → 0.18 → 0.09. Heuristic guard: 0.70 → 0.64 → 0.50.
  Neither is yet clear below its start. The intervals still overlap by a small margin: CP7
  [0.048, 0.162] vs [0.125, 0.278], heuristic [0.366, 0.634] vs [0.562, 0.809]. This is a
  regression in both point estimates, not "flat", and not yet a clear one.
- **"Improving vs CP7" is not met.** The last level is below the first, not above it.
- **"Over-fit to CP7" does not apply.** That reading needs the CP7 level up while a guard falls;
  here the CP7 level itself is falling.
- **Dimir card habits:**
  - The self-destroy clause **is met**: every check from n=1 to n=7 is below 0.3 (0.004–0.05 since
    n=1).
  - The counter-selectivity clause **fails at every check since n=1** (0.02–0.07 of the windows
    offering one, against the [0.2, 0.5] band and CP7's ~0.33).
  - The creatures-per-game clause (≥ 3 over the last four checks) **fails**: 2.88 at n=5 and
    2.36 at n=7.
  - So "card habits converge" is **not met**. The counters have not swung back across their range
    (no Phase 11-style oscillation so far); they have settled on "hold".
- **Shape:** the policy is moving into a long-game "hold" style. It casts less, counters almost
  nothing, takes ~80–100 consults per game against 61–69 at the start and n=0, and loses more to
  both opponents.

**Sampled vs argmax.** Against CP7 the sampled training win rate is flat at ~0.16 over all six CP7
blocks (0.168, 0.156, 0.137, 0.164, 0.160, 0.176), while the argmax level halved. Against the
heuristic the sampled training rate rose (0.480 at n=1, 0.605 at n=5) while the argmax guard fell.
The training signal and the argmax yardsticks are moving apart. This is carried as an observation;
this phase has no pre-registered reading for it.

What this cannot support:
- **One seed and one deck (Amendment 2).** The drift-hypothesis test has two points in, of up to
  five tonight.
- **"Clear below" needs the next point.** A 100-game level and a 50-game guard are not yet enough
  to call the fall clear.
- **The fixed seeds pair the deals only at the first decision.** The levels are not a paired test.
- **The start snapshot is the Phase 11 drill's last point.** Its own trajectory was oscillating
  (see "Phase 11 verdict"), so part of any fall could be that trajectory continuing and not this
  phase's opponent mix.

### 12 / M_D — Amendment 4 diagnostic: the argmax readout on the census states (2026-09-15 ~03:30Z WSL)

**Amendment 4** (pre-registered in `rl/PHASE12-CP7.md` before any result; it adds a measurement,
and the argmax levels and graduation rule are unchanged). Hypothesis: the policy's acting mass is
spread over several distinct candidates, so the argmax-over-classes readout picks PASS / hold even
when P(act) > 0.5. Two parts:
- **(1) Sampled levels** of the three level snapshots. **Paused for memory** at launch: the box
  swapped and the lane's update time rose from ~20 s to 35–37 s. Rescheduled unattended after the
  controller's final `L12|done` (`rl/after_p12.sh`). Box rule from now on: the lane plus at most
  one other model-holding process.
- **(2) The readout on the recorded census consults**, below.

Rescoring used `rl/p12_readout.py`: each 25-game CP7 census recording, scored with the snapshot
that played it, on CPU, bound 5 applied as the server does, and the server's argmax-over-classes
choice recomputed. The recomputed choice **matches the recorded one at 6,160 / 6,160 consults**.

| point (snapshot) | consults offering PASS | argmax PASS | **PASS while P(non-PASS) > 0.5** | of the PASS choices | act rate, argmax | act rate, sampled (mean P(non-PASS)) | creature spell offered: argmax casts | sampled creature mass | non-creature chosen while creature mass > the chosen class |
|---|---|---|---|---|---|---|---|---|---|
| start (6,400) | 1,342 | 0.649 | **205/1,342 = 0.153 [0.135, 0.173]** | 0.235 | 0.351 | 0.594 | 96/119 = 0.807 | 0.530 | 1/119 = 0.008 |
| +1,024 (7,424) | 1,938 | 0.748 | **323/1,938 = 0.167 [0.151, 0.184]** | 0.223 | 0.252 | 0.511 | 90/600 = 0.150 | 0.362 | 65/600 = 0.108 |
| +2,048 (8,448) | 2,341 | 0.870 | **1,001/2,341 = 0.428 [0.408, 0.448]** | 0.492 | 0.130 | 0.553 | 59/1,422 = 0.041 | 0.282 | 124/1,422 = 0.087 |

**What it shows.**
- **The PASS-despite-majority rate rises across the three points.** It is flat to +1,024 and
  jumps at +2,048: 0.153 → 0.167 → 0.428, clear at the last point. At +2,048, half of all PASS
  choices (0.492) are made while the policy puts more than 0.5 on acting.
- **On the same states the policy's acting mass is roughly steady.** The mean summed P(non-PASS)
  goes 0.594 → 0.511 → 0.553, while the argmax readout's act rate falls 0.351 → 0.252 → 0.130. The
  readout, not the distribution, drives most of the "hold" shape the census recorded.
- **The creature-spell fall is only partly a readout effect.** The sampled creature mass also
  falls, 0.53 → 0.36 → 0.28. The "non-creature chosen despite a larger creature mass" case is
  small (0.01, 0.11, 0.09). The argmax readout amplifies a real decline (0.81 → 0.15 → 0.04 argmax
  casts) rather than creating it.

**Reading against the pre-statement.** The pre-stated "argmax artifact" reading needs both halves.
The readout half is **met** (the rate rises). The sampled-level half is **pending** the
rescheduled battery. "Real regression" cannot be ruled out until the sampled levels are in. No
reading is declared yet.

What this cannot support:
- **These are the states argmax play reaches.** At +2,048 there are more consults per game and
  more held-priority states, so the three rows are not the same state set. The act-rate comparison
  is valid within a row, and the across-row trend is a trend of both the policy and its states.
- **One census per point** (25 games, fixed seed 12500), one seed, one deck.

**Amendment 5 (pre-registered ~03:35Z, before any result): a two-stage argmax readout.** It is an
evaluation-only readout. First, act versus pass by summed probability: act if and only if
Σ P(non-PASS) > P(PASS). Then, if acting, the argmax over the acting candidates by class. The
server flag is `--argmax-two-stage`, default off. It is implemented and tested only after
training ends, then run on the same three snapshots and seeds (100 vs CP7 + 50 vs the heuristic),
one evaluation at a time after the sampled battery. Reading: if the two-stage levels track the
sampled levels and both stay flat or rise while the argmax-classes levels fall, the decline is a
readout artifact and argmax-classes is retired for this policy family. If all three fall
together, it is a real regression. The full text is in `rl/PHASE12-CP7.md` Amendment 5.

### 12 / M_D — third level point, +3,072 episodes (2026-09-15 ~05:25Z WSL)

**Level at 9,472 episodes (+3,072):** CP7 on the own mirror **8/100 = 0.080 [0.041, 0.150]**
(0 stalls). Heuristic guard **26/50 = 0.520 [0.385, 0.652]**. Not graduated.

| point | trained | CP7 (100), argmax-classes | heuristic guard (50) |
|---|---|---|---|
| start | 6,400 | 19/100 = 0.190 [0.125, 0.278] | 35/50 = 0.700 [0.562, 0.809] |
| +1,024 | 7,424 | 18/100 = 0.180 [0.117, 0.267] | 32/50 = 0.640 [0.501, 0.759] |
| +2,048 | 8,448 | 9/100 = 0.090 [0.048, 0.162] | 25/50 = 0.500 [0.366, 0.634] |
| +3,072 | 9,472 | 8/100 = 0.080 [0.041, 0.150] | 26/50 = 0.520 [0.385, 0.652] |

Training blocks n=8..11 (sampled play): n=8 cp7 49/207 = 0.191; n=9 heuristic 147/109 = 0.574;
n=10 cp7 43/213 = 0.168; n=11 cp7 26/230 = 0.102 (the lowest CP7 block so far; the earlier ones were
0.137–0.176). Wall ~1,415 s per CP7 block and 552 s per heuristic block.

Per-block CP7 checks n=8..11 (25 argmax games, seed 12500):

| check | trained | CP7 wins | selfrem | counter taken | flash on opp turn | ninjutsu | biggest | creatures/game | consults/game |
|---|---|---|---|---|---|---|---|---|---|
| n=8 | 8,704 | 7/25 | 11/18 | 20/37 | 17/76 | 1/3 | 14/23 | 4.04 | 75.7 |
| n=9 | 8,960 | 5/25 | 9/89 | 14/41 | 3/73 | 0/7 | 11/15 | 4.00 | 72.7 |
| n=10 | 9,216 | 5/25 | 3/154 | 7/88 | 13/62 | 1/1 | 4/7 | 3.24 | 95.5 |
| n=11 | 9,472 | 3/25 | 1/114 | 3/108 | 3/35 | 1/2 | 6/7 | 2.36 | 109.0 |

**Reading at +3,072, in the pre-registered terms.**

- **CP7 argmax level:** 0.19 → 0.18 → 0.09 → 0.08. The last interval [0.041, 0.150] overlaps the
  start's [0.125, 0.278] only at its edge. This is a regression in the point estimate, and not yet
  clear by the non-overlap criterion.
- **Heuristic guard:** 0.70 → 0.64 → 0.50 → 0.52, falling and overlapping the start's interval.
- **"Improving vs CP7" is not met.** "Over-fit to CP7" does not apply.
- **Card habits oscillate again under the fixed opponent.** At n=8 the counters swung back to
  "act": selfrem 11/18 = 0.61 (above the clause's 0.3), counter 20/37 = 0.54 (above the [0.2, 0.5]
  band), creatures 4.04, consults per game 76. By n=10–11 they were back to "hold": selfrem 0.02 /
  0.01, counter 0.08 / 0.03, creatures 3.24 / 2.36, consults per game 96 / 109.
  - This is the runbook's "oscillates": selfrem and counter swing across their ranges again, as in
    Phase 11. So "card habits converge" is not met.
  - The runbook's **drift-hypothesis test** predicted no oscillation under a fixed mix. The Phase 11
    oscillation is therefore **not specific to the league mix**, which **weakens self-play drift as
    the main explanation**.
  - The runbook's alternative is the coarse terminal reward. It is not established here; it is the
    pre-registered next candidate.
- **The Amendment 4 readout artifact applies.** The argmax-classes level increasingly understates
  the sampled policy: PASS against an acting majority rose 0.153 → 0.167 → 0.428 over the first
  three points. The sampled and two-stage reruns after training (Amendments 4 and 5) decide how
  much of the level decline is real.
  - The oscillation itself is seen in the recorded argmax play. How much of it is the readout
    flipping at a near-0.5 act mass, and how much is the distribution moving, is part of what those
    reruns and a readout at the n=8 snapshot could separate. The n=8 readout is not run; noted as
    owed.

What this cannot support:
- One seed and one deck.
- "Clear below the start" still fails narrowly by the overlap criterion.
- The oscillation reading rests on 25-game checks. One swing from n=7 to n=8 to n=11 is recorded,
  not a period.

### 12 / M_D — fourth level point, +4,096 episodes (2026-09-15 ~07:30Z WSL)

**Level at 10,496 episodes (+4,096):** CP7 on the own mirror **31/100 = 0.310 [0.228, 0.406]**
(0 stalls). Heuristic guard **38/50 = 0.760 [0.626, 0.857]**. Not graduated.

| point | trained | CP7 (100), argmax-classes | heuristic guard (50) |
|---|---|---|---|
| start | 6,400 | 19/100 = 0.190 [0.125, 0.278] | 35/50 = 0.700 [0.562, 0.809] |
| +1,024 | 7,424 | 18/100 = 0.180 [0.117, 0.267] | 32/50 = 0.640 [0.501, 0.759] |
| +2,048 | 8,448 | 9/100 = 0.090 [0.048, 0.162] | 25/50 = 0.500 [0.366, 0.634] |
| +3,072 | 9,472 | 8/100 = 0.080 [0.041, 0.150] | 26/50 = 0.520 [0.385, 0.652] |
| +4,096 | 10,496 | 31/100 = 0.310 [0.228, 0.406] | 38/50 = 0.760 [0.626, 0.857] |

Training blocks n=12..15 (sampled play): n=12 cp7 48/208 = 0.188; n=13 heuristic 163/93 = 0.637;
n=14 cp7 49/207 = 0.191; n=15 cp7 63/193 = 0.246. The last is the best sampled CP7 block of the
phase; the earlier CP7 blocks were 0.102–0.191.

Per-block CP7 checks n=12..15 (25 argmax games, seed 12500):

| check | trained | CP7 wins | selfrem | counter taken | flash on opp turn | ninjutsu | biggest | creatures/game | consults/game |
|---|---|---|---|---|---|---|---|---|---|
| n=12 | 9,728 | 7/25 | 3/256 | 4/107 | 20/47 | 3/3 | 3/5 | 2.88 | 118.9 |
| n=13 | 9,984 | 10/25 | 15/132 | 16/114 | 31/86 | 8/8 | 13/18 | 4.84 | 107.9 |
| n=14 | 10,240 | 2/25 | 4/127 | 5/110 | 21/52 | 2/8 | 7/17 | 3.00 | 108.3 |
| n=15 | 10,496 | 6/25 | 7/122 | 14/79 | 34/68 | 1/6 | 19/27 | 3.80 | 96.8 |

**Reading at +4,096, in the pre-registered terms.**

- **The CP7 level reversed:** 0.19 → 0.18 → 0.09 → 0.08 → **0.31**. It is the best of the phase and
  the first point above the start. Its interval [0.228, 0.406] still overlaps the start's
  [0.125, 0.278], so **"improving vs CP7" is not met** by the overlap test.
- **The heuristic guard is also at its best:** 0.76 against the start's 0.70.
- **Card habits keep oscillating check to check.** Counter selectivity goes 0.04 → 0.14 → 0.05 →
  0.18, creatures per game 2.88 → 4.84 → 3.00 → 3.80. Flash on the opponent's turn rose
  (0.43 → 0.50 at n=15, against 0.04–0.26 earlier in the night). Self-destroy stays low except
  0.11 at n=13. Consults per game stay high (97–119).
- **Carried plainly:** one level-to-level swing (0.08 → 0.31 in 1,024 episodes) is as large as the
  whole night's range. That is consistent with the Amendment 4 readout artifact on an oscillating
  policy: which side of the act/pass swing a checkpoint lands on moves its argmax level. **No
  single point is a trend.**
- **What decides it:** the sampled and two-stage reruns on the saved level snapshots (Amendments 4
  and 5). The rerun set now covers the start, 7,424, 8,448, 9,472 and 10,496; `rl/run_p12s.sh` is
  extended, and it runs after the controller's final `L12|done`. The readout at the n=8 snapshot
  (8,704, the act-swing state) is also owed, on its recorded census consults.

What this cannot support:
- A trend from any single level. The whole argmax series is within one 1,024-episode swing.
- One seed and one deck.
- Graduation remains far off by the argmax rule: 31/100 against 70/100.

### 12 / M_D — fifth level point, +5,120 episodes (2026-09-15 ~09:55Z WSL)

**Level at 11,520 episodes (+5,120):** CP7 on the own mirror **33/100 = 0.330 [0.246, 0.427]**
(0 stalls). Heuristic guard **39/50 = 0.780 [0.648, 0.872]**. Not graduated.

| point | trained | CP7 (100), argmax-classes | heuristic guard (50) |
|---|---|---|---|
| start | 6,400 | 19/100 = 0.190 [0.125, 0.278] | 35/50 = 0.700 [0.562, 0.809] |
| +1,024 | 7,424 | 18/100 = 0.180 [0.117, 0.267] | 32/50 = 0.640 [0.501, 0.759] |
| +2,048 | 8,448 | 9/100 = 0.090 [0.048, 0.162] | 25/50 = 0.500 [0.366, 0.634] |
| +3,072 | 9,472 | 8/100 = 0.080 [0.041, 0.150] | 26/50 = 0.520 [0.385, 0.652] |
| +4,096 | 10,496 | 31/100 = 0.310 [0.228, 0.406] | 38/50 = 0.760 [0.626, 0.857] |
| +5,120 | 11,520 | 33/100 = 0.330 [0.246, 0.427] | 39/50 = 0.780 [0.648, 0.872] |

Training blocks n=16..19 (sampled play): n=16 cp7 61/195 = 0.238; n=17 heuristic 172/84 = 0.672;
n=18 cp7 60/196 = 0.234; n=19 cp7 51/205 = 0.199. The sampled CP7 blocks since n=15 (0.20–0.25)
sit above the night's first eleven (0.10–0.19).

Per-block CP7 checks n=16..19 (25 argmax games, seed 12500):

| check | trained | CP7 wins | selfrem | counter taken | flash on opp turn | ninjutsu | biggest | creatures/game | consults/game |
|---|---|---|---|---|---|---|---|---|---|
| n=16 | 10,752 | 6/25 | 16/144 | 47/76 | 15/77 | 0/3 | 18/29 | 4.36 | 88.6 |
| n=17 | 11,008 | 10/25 | 17/148 | 25/72 | 14/80 | 6/8 | 10/13 | 4.24 | 76.7 |
| n=18 | 11,264 | 5/25 | 2/133 | 8/107 | 10/73 | 0/0 | 12/23 | 3.80 | 90.8 |
| n=19 | 11,520 | 9/25 | 11/144 | 23/85 | 12/84 | 2/9 | 7/15 | 4.40 | 88.9 |

**Reading at +5,120, in the pre-registered terms.**

- **CP7 argmax level:** 0.19 → 0.18 → 0.09 → 0.08 → 0.31 → 0.33. The last interval
  [0.246, 0.427] still overlaps the start's [0.125, 0.278] at its edge, so **"improving vs CP7" is
  not met** by the overlap test.
  - *Observation, not a reading:* two consecutive points at 0.31–0.33 after two at 0.08–0.09 make
    a single-checkpoint fluke less likely than at +4,096.
- **Heuristic guard:** at its best, 0.78 against the start's 0.70, overlapping.
- **"Over-fit to CP7" does not apply**, since both yardsticks rose.
- **Card habits over the last four checks (n=16..19):**
  - selfrem is below 0.3 at all four (0.11, 0.11, 0.02, 0.08): **met**.
  - Creatures per game are ≥ 3 at all four (4.36, 4.24, 3.80, 4.40): **met**.
  - Counter selectivity is in [0.2, 0.5] at only **two of four**: 0.62 (above), 0.35, 0.07
    (below), 0.27. **Not met.**
  - Correction in the open: the coordinator's summary said three of four. The recount from the
    check lines is two of four; the clause fails either way.
  - So "card habits converge" is **not met**, on the counter clause alone. The counter's swing from
    0.62 to 0.07 within three checks is itself the "oscillates" pattern.
- **The readout caveat still applies.** The argmax series is what the sampled and two-stage reruns
  (Amendments 4 and 5) will check. 11,520 is added to their snapshot set (`rl/run_p12s.sh`).

What this cannot support:
- A trend. The two recent points sit within one level-to-level swing of the night.
- One seed and one deck.
- Graduation remains far off: 33/100 against 70/100.

### 12 / M_D — end point, 11,776 episodes (+5,376), and the full series (2026-09-15 ~10:50Z WSL)

Training ended at the controller's hour-12 stop (Amendment 3):
`L12|done|reason=hours|blocks=21|h=12.50|graduated=none`. Dimir trained 5,376 episodes
(21 blocks: 16 vs CP7, 5 vs the heuristic). Landfall and white trained 0 (Amendment 2, deferred).

**Last block and check.**
- Block n=20: cp7, 53/203 = 0.207, 1,566 s.
- Check n=20: CP7 2/25. selfrem 5/111, counter 9/101, flash on opp turn 7/65, ninjutsu 0/15,
  biggest 7/15, creatures per game 3.32, consults per game 94.4.

**End point (11,776):**
- CP7 **21/100 = 0.210 [0.142, 0.300]**.
- Heuristic **32/50 = 0.640 [0.501, 0.759]**.
- Unseen suite **95/150 = 0.633 [0.554, 0.706]** (BenchBurn 25/50, HoldoutControl 42/50,
  HoldoutMidrange 28/50). The start's was 98/150 = 0.653 (29 / 39 / 30).

**The argmax-classes level series (the pre-registered yardstick):**

| point | trained | CP7 (100) | heuristic guard (50) | unseen (150) |
|---|---|---|---|---|
| start | 6,400 | 0.190 [0.125, 0.278] | 0.700 | 0.653 [0.574, 0.725] |
| +1,024 | 7,424 | 0.180 [0.117, 0.267] | 0.640 | – |
| +2,048 | 8,448 | 0.090 [0.048, 0.162] | 0.500 | – |
| +3,072 | 9,472 | 0.080 [0.041, 0.150] | 0.520 | – |
| +4,096 | 10,496 | 0.310 [0.228, 0.406] | 0.760 | – |
| +5,120 | 11,520 | 0.330 [0.246, 0.427] | 0.780 | – |
| end +5,376 | 11,776 | 0.210 [0.142, 0.300] | 0.640 | 0.633 [0.554, 0.706] |

Carried plainly:
- **One block moved the level from 0.33 to 0.21.** The last 256 episodes were a single CP7 block
  (sampled 0.207). A drop that size in one block is again the scale of the night's swings. It fits
  a readout that flips with the act/pass balance, not a trained skill lost in 256 episodes.
- **Measured from the first level to the last**, the argmax CP7 level went 0.19 → 0.21, the
  heuristic guard 0.70 → 0.64, and the unseen suite 0.653 → 0.633. All three overlap their start
  intervals.

**Pre-registered readings at the end (argmax yardstick).**
- **Competent:** no. Not graduated.
- **Improving vs CP7:** not met (0.21 against 0.19, overlapping).
- **Over-fit to CP7:** does not apply. The CP7 level did not rise clear, and the guards did not end
  clear below.
- **Card habits converge:** not met, and **"oscillates"**: act swings at n=8, n=13 and n=16–17,
  and hold at n=10–12, n=14, n=18 and n=20.
- **Drift hypothesis test:** under the fixed CP7 / heuristic mix, the levels stayed flat by the
  overlap test and the counters still oscillated. The runbook's own sentence applies: **the drift
  hypothesis is not supported, and the coarse terminal reward is the leading explanation instead**.
  This carries a qualifier that comes after the pre-registration: the Amendment 4 readout shows the
  argmax yardstick itself flips with the act/pass balance. The sampled and two-stage levels
  (Amendments 4 and 5) say whether the flat argmax series hides movement in the policy.

### 12 / M_D — the three readouts per snapshot and the Amendment 4 reading (2026-09-15 ~12:50Z WSL)

The user stopped the remaining evaluations at ~12:40Z (`rl/stop_p12_evals.sh`, main session):
"enough to conclude". The sampled battery (Amendment 4) finished 4 of its 6 snapshots: vs CP7 at
the start, 7,424, 8,448 and 9,472, and vs the heuristic at the first three. The two-stage battery
(Amendment 5), the after-training watcher and the queued CPU readouts (n=8, 11, 15, 19, 20) were
cancelled. **Amendment 5 is recorded as cancelled by the user, not run.** Its flag stays in the
server, default off and tested.

**Levels per snapshot.** "argmax" is the pre-registered argmax-classes readout (the Phase 12 levels);
"sampled" is the same snapshot frozen and sampled as in training (`-Drl.mode=train`, `--frozen`),
with the same seeds.

| snapshot | CP7, argmax (100) | **CP7, sampled (100)** | heuristic, argmax (50) | heuristic, sampled (50) | PASS while P(act) > 0.5 (census readout) |
|---|---|---|---|---|---|
| start 6,400 | 0.190 [0.125, 0.278] | **0.120 [0.070, 0.198]** | 0.700 [0.562, 0.809] | 0.720 [0.583, 0.825] | 0.153 |
| +1,024 7,424 | 0.180 [0.117, 0.267] | **0.110 [0.063, 0.186]** | 0.640 [0.501, 0.759] | 0.580 [0.442, 0.706] | 0.167 |
| +2,048 8,448 | 0.090 [0.048, 0.162] | **0.150 [0.093, 0.233]** | 0.500 [0.366, 0.634] | 0.640 [0.501, 0.759] | 0.428 |
| +3,072 9,472 | 0.080 [0.041, 0.150] | **0.220 [0.150, 0.311]** | 0.520 [0.385, 0.652] | not run | – |
| +4,096 10,496 | 0.310 [0.228, 0.406] | not run | 0.760 [0.626, 0.857] | not run | – |
| +5,120 11,520 | 0.330 [0.246, 0.427] | not run | 0.780 [0.648, 0.872] | not run | – |
| end 11,776 | 0.210 [0.142, 0.300] | not run | 0.640 [0.501, 0.759] | not run | – |

**Amendment 4 reading, as pre-stated.** "Argmax artifact" needs two halves.
- **The readout half is met.** PASS chosen while the policy puts more than 0.5 on acting rises
  0.153 → 0.167 → 0.428 over the three pre-registered points. The sampled act rate on the same
  states stays ~0.55 while the argmax act rate falls 0.35 → 0.13.
- **The win-rate half is met.** Over the same snapshots the sampled CP7 level stays flat, then
  rises: 0.12 → 0.11 → 0.15, then 0.22 at 9,472. Meanwhile the argmax level falls
  0.19 → 0.18 → 0.09 → 0.08.
- **So the reading is "argmax artifact":** the mid-phase argmax decline was a readout artifact, not
  a regression of the policy.
- **"Real regression" is ruled out** for these four snapshots. The sampled levels did not fall with
  the argmax ones.
- **The underlying policy improved modestly against CP7.** Sampled 0.12 at the start against 0.22
  at 9,472. The two intervals ([0.070, 0.198] and [0.150, 0.311]) overlap on [0.150, 0.198], so the
  rise is not clear by the overlap test.
- **Heuristic, sampled:** 0.72 → 0.58 → 0.64, flat within its intervals. The argmax guard's fall to
  0.50 at 8,448 is also not seen in sampled play there (0.64).

**Correction in the open.** The second- and third-level rows above describe "both yardsticks
falling ... a regression in the point estimates". The numbers stand as argmax-readout levels. By
Amendment 4 they are not evidence that the policy regressed: sampled play at those snapshots held
or rose. The later swing up (0.31–0.33) and back (0.21) is likewise the readout's instability, and
it is not measured under sampling.

**Card habits under a fixed opponent.**
- **Oscillation:** across 21 checks the counters swung between "act" (n=0, n=8, n=13, n=16–17) and
  "hold" (n=1–7, n=10–12, n=14, n=18, n=20) without converging. The counter clause failed over
  every last-four window.
- **Self-destroy:** mostly gone. Removal cast with only its own creatures as legal targets went
  from 7/7 (start) to 0.004–0.12 at every check after n=0, except the act swing at n=8 (11/18).
  CP7's own rate is 0/164.
- **Drift hypothesis:** Phase 11's oscillation reappeared with no self-play opponent in the mix, so
  **self-play drift is not the main explanation** of it. The runbook's alternative, the coarse
  terminal reward, remains a candidate; nothing here establishes it.
- **Readout caveat:** the census counters are argmax play too. By Amendment 4 part of each swing is
  the readout flipping near a 0.5 act mass. How much is readout and how much is the distribution
  moving was the owed n=8 readout, which was cancelled.

What the reading cannot say:
- **Two sampled points were not run** (10,496, 11,520 and the end) and the 9,472 heuristic row
  was not run. **The two-stage readout was not run** (cancelled by the user), so whether a
  deterministic readout can recover the sampled level is open.
- **One seed, one deck (Dimir).** Landfall and white are paused at their start points
  (Amendment 2).
- **Far from graduation.** The best sampled level is 0.22 and the best argmax level 0.33, against
  the 0.70 bar.
- **Sampled play is a level of a stochastic player**, not of the deterministic readout the
  graduation rule names. The graduation rule was not changed.
- **A CP7 sampled level of 0.12 at the start, below the argmax 0.19**, means the readouts rank
  differently at different snapshots. There is no single conversion between them.

## Phase 12 verdict (2026-09-15)

Phase 12 ran Dimir alone for the night (Amendments 2 and 3): 5,376 episodes from M_D_06400,
against a fixed mix of 75 % CP7 and 25 % heuristic on its own mirror.

**It did not graduate.** Against CP7, the argmax-classes level went 0.19 → 0.18 → 0.09 → 0.08 →
0.31 → 0.33 → 0.21. The heuristic guard ended at 0.64 (start 0.70), and the unseen suite at 0.633
(start 0.653). All of these overlap their starts.

**The phase's main finding is about the yardstick.** The argmax-classes readout is not a faithful
level for this policy family. As training went on, the policy spread its acting mass over several
distinct candidates, and the class argmax then chose PASS against an acting majority: 15 % of
PASS-offered consults at the start, 43 % at +2,048. Over the same snapshots the sampled policy
held, then rose against CP7 (0.12 → 0.11 → 0.15 → 0.22), while the argmax level fell
(0.19 → 0.08). By the pre-stated Amendment 4 criterion, the mid-phase decline was a readout
artifact, not a regression. Under a fixed opponent the policy improved modestly against CP7; the
rise is not clear by the overlap test and is far from the 0.70 bar.

**The card habits oscillated with no self-play in the mix.** So the Phase 11 swing is not
self-play drift, and the drift hypothesis is not supported as its main explanation. The
self-removal habit is mostly gone.

**The evaluation protocol for this policy family has to be decided before any further level is
read.** The candidates are sampled levels, the two-stage readout, or both. Graduation should not be
judged on argmax-classes alone.

What this cannot support: one seed, one deck; two sampled points and the two-stage readout not run
(cancelled by the user); no claim about landfall or white (paused), or about Phase 13.

## 13a — the recording: 68,500 CP7-labelled consults on BenchDimir, labels on priority, target and joint attack/block (2026-09-15; branch `v7/lane-d`; runbook `rl/PHASE13-BC.md`)

**Build** (compiled with `rl/sync_lane_b.sh`, nothing else on the engine). `rl/xmage-src/JointCands.java`:
RLPlayer's joint attack / block candidate builders (`jointAttacks` / `jointBlocks` + `attackChoiceSet`,
`theirBlockers`) lifted verbatim to package-static; RLPlayer now calls them, so the RL seat and the teacher
build their lists on one code path (the RL seat's behaviour after the lift was compiled, not re-measured in
a paired battery — a cannot below). `CP7TeacherPlayer` (75d1428, b03cf7f): priority labels as in 7d1b;
**target** labels one consult per required target as `policyPickTargets` / `policyPickCards` build them —
targets preset by CP7's search are read at `activateAbility` and labelled **after** the activation (spell or
ability on the stack), triggered / choose-style targets through wrapped `chooseTarget` / `choose`; **joint**
labels: the list is built before CP7 declares, the declared set is read back and matched by body multiset
(exact) or outcome key (alias), else y = −1 (`teacherJointMiss`).

**Time-box.** Target labels took two attempts. Attempt 1 labelled preset targets with the spell still in
**hand** — the targeting object was invisible to the clone and to `dimir_census`' removal counter; that
7-minute recording was stopped and set aside (`rec/attempt1/`, unused). Joint labels: one attempt. Two
defects the smokes found and fixed before the recording: CP7's pass is itself an activated `PassAbility`
(had been read as "outside", 27 of 266 priority consults) — now y = 0; a same-source, same-class fallback
for rule-text differences (`prioAlias`, fired 0 times in the recording).

**Recording** (`rl/run_13a.sh`, 12:59–15:24Z WSL): two lanes, 50-game jobs, BenchDimir mirror, seats by
episode parity, `rl.aiSkill` 6, `rl.consultBudget` 4000; lane H vs the heuristic (15 jobs), lane C the CP7
mirror (10 jobs); every job rc = 0. Artifacts `rl/artifacts/v7/13/rec/` (jsonl gitignored; `counts.txt`,
`summary.txt`, `run_13a.log`).

| decision kind (teacher's own counters) | consults | labelled | fraction | gate ≥ 0.9 | misses |
|---|---|---|---|---|---|
| priority | 51,628 | 51,611 | **1.000** | pass | 17 outside the list |
| target | 6,626 | 6,626 | **1.000** | pass | 0 (3,400 preset + the rest wrapped; 0 optional) |
| joint attack | 6,095 | 5,780 | **0.948** | pass | 315 `teacherJointMiss` (exact 5,780, alias 0) |
| joint block | 4,603 | 4,483 | **0.974** | pass | 120 `teacherJointMiss` (exact 4,419, alias 64) |
| all | 68,952 | **68,500** | 0.993 | | multi-act 0, budget-skipped 0 |

1,250 games, 55.2 consults per game; windows 249,507, of which 197,879 had no candidate after the filters
(auto-pass, no consult). **Priority label census** (the target the BC census is read against): **PASS
28,222 (54.7 %)**, LAND 7,742 (15.0 %), SPELL 10,401 (20.2 %), ACTIVATE 5,246 (10.2 %). On Dimir CP7
passes more than half the windows it can act in (on W0Base it never passed, 7d1b) — this recording can
teach *when to hold*, which the 7d1b one could not. **CP7's level** over the recording (Wilson 95 %): vs the
heuristic **623/750 = 0.831 [0.802, 0.856]**; CP7 mirror 246/500 = 0.492 [0.448, 0.536].

**Gate view, correction in the open.** The first summary tool gated per candidate-type class, where a
PASS-only joint consult (k = 1) falls under "trivial"; that view read blocks 0.884 on the first 100 games and
would have dropped the kind. The pre-registered gate is per decision kind, read from the teacher's
counters (table above); the type view is kept as `REC13SUM|types=` (types block 1,556/1,676 = 0.928,
trivial 3,029/3,196 = 0.948 — 167 of the joint misses are k = 1 consults).

**Joint misses** are CP7 choices outside CombatMath's list: the vanilla model has no evasion, so it can offer
blocks that are illegal and prune the legal alternative as dominated, and it prices attacks with flyers as
if they could be blocked (one logged miss: CP7 attacked with a subset the Pareto filter had dropped). The RL
seat is offered the same list; these decisions are counted, not labelled, and BC drops them.

**Faithfulness** (the 5b gate, 100 consults over 24 games): `wire_validate` ok; L3 53 pass / 0 fail, L4 52 /
1 (`ent.mana_left_if_cast` R² 0.896 vs 0.90 — the 5b "small-scale real at the random wake" class), edges 3 / 0
(`faith13.md`). Context, not the gate: over 25 games (1,271 consults) L3 101 / 7, L4 99 / 9, against an
RL-seat BenchDimir census of 25 games at L3 85 / 0, L4 83 / 2 (`faith_ctrl_p12n012.md`); the teacher's
consults exercise 23 more fields and fail on small-n fields (stack tokens n_test 49, opp-hand age, candidate
counts) or on a sub-slice of grouped fields whose pooled score is ≥ 0.995. Which sub-slice is owed.

**Readings.** Every decision kind passes the 0.9 gate; all four are cloned in 13b. Cannot: make the teacher's
target state identical to the RL seat's (preset-target consults see the spell on the stack with costs already
paid, lands tapped); say the RL seat plays unchanged after the JointCands lift (verbatim move, compiled, not
re-measured); label CP7's choices CombatMath does not offer (435 joint decisions); say anything off
BenchDimir or about CP7 at other skills.

### 13a — addendum: are instant-speed flash decisions recorded? (2026-09-15 ~15:50Z WSL; coordinator's check)

Question (main session): `dimir_census` on `rec13_C_s13500` (50 mirror games) reported opponent-turn windows
recorded but "flash_oppturn: windows on the OPPONENT's turn offering a flash card: 0/0", where the Phase 12
RL seat on the same deck was offered one 60–170 times per 25 games. Recording gap, or CP7 tapping out?

**Candidate-building path: identical.** `CP7TeacherPlayer.priority` builds its list as `RLPlayer.priority`
does (`getPlayable(game, true)`, the phantom-land filter, the mana-ability filter, the name|rule sort); no class
in CP7's chain (ComputerPlayer → 6 → 7) overrides `getPlayable` or the mana-availability path; both seats' drivers
ran `-Dmage.playableCache=on`. A direct test of the playable memo: 60 teacher games vs the heuristic on a side driver with `-Dmage.playableCache=verify` (`rl/artifacts/v7/13/rec/flashtest_verify.*`): `RL|playableMemo|mode=verify|hits=0|misses=123062|mismatches=0` - the memo never served a cached list to the teacher seat (every `getPlayable` freshly computed), so it cannot have hidden a candidate; the flash picture is unchanged there (Enduring Curiosity 15 castable-looking states, offered 0).

**Recording, all 25 files (1,250 games; opponent-turn = `v7_game[1] < 0.5`; `rl/probes/flash13_scan*.py`):**
opponent-turn consults 11,292 of 68,952; a flash card was offered as a SPELL candidate on the opponent's turn
in **141** consults and cast **11** times; on CP7's own turn flash cards were offered 13,853 times and cast
**3,775** times. Opponent-turn priority consults with a flash card in hand: 3,643; with ≥ 2 untapped own lands
918 (offered 141), with ≥ 3 364 (offered 49). CP7 is usually tapped low on the opponent's turn (in a 150-game
sample 52 % of its opponent-turn consults had ≤ 1 untapped land; the RL-seat control 17 %).

**Per card, states where the card is in hand on the opponent's turn with lands ≥ its mana value (and a blue source
for the blue cards), teacher vs the RL-seat control (`rec_p12_M_D_n012_t09728`, 25 games):**

| card | teacher: castable-looking states / offered | RL seat: states / offered | reading |
|---|---|---|---|
| Floodpits Drowner ({1}{U}) | 0 / 0 | 360 / 360 | CP7 never holds it with mana up — it casts it on its own turn |
| The Wondrous Wasp | 21 / **21** | 223 / 223 | offered whenever castable, both seats |
| Nowhere to Run ({1}{B}) | 43 / 0 | 13 / 13 | the teacher's 43 states have only Gloomlake Verge / Hidden Lair / Soulstone Sanctuary untapped: Gloomlake's {B} and Hidden Lair's colours are conditional (XMage `ActivateIfConditionManaAbility`), Sanctuary is colourless — no black mana, correctly not offered; the RL seat's 13 had a Swamp / Watery Grave up |
| Enduring Curiosity ({2}{U}) | 178 / **0** | 135 / **0** | never offered at instant speed to EITHER seat although XMage's card has `FlashAbility` — an engine/card-level fact, not a teacher gap (owed: why; `dimir_census`' FLASH list counts it) |

**Answer.** Not a recording gap: the teacher seat is offered exactly what the RL seat would be offered in the
same state, and the 0/0 in the census comes from CP7's behaviour — it casts its flash creatures in its own main
phase (3,775 own-turn casts vs 11 on the opponent's turn) and is rarely holding a castable flash card with the
right mana open on the opponent's turn. **Consequence for the clone:** these labels carry almost no
instant-speed flash decisions (141 offers, 11 casts in 68,952 consults), so the clone cannot learn draw-go
flash play from CP7; what it can learn is CP7's main-phase flash use and its counterspell timing (counterspells
are offered and taken on the opponent's turn). The phase goes on; the 13b census reads flash-at-instant-speed
against CP7's own ~0 rate, not against the RL seat's Phase 12 rate. Cannot: say why the engine never offers
Enduring Curiosity at instant speed (affects both seats; owed).

**Correction (2026-09-15 ~16:00Z, same session).** The addendum's line 'Enduring Curiosity ... never offered at instant speed to EITHER seat' is wrong as written: `dimir_census` over the full recording counts Enduring Curiosity offered at instant speed 1,684 times (taken 9) - on CP7's OWN turn (non-main steps or a non-empty stack). What the scans show is narrower: it is never offered on the OPPONENT's turn (teacher 0 of 178 castable-looking states, RL seat 0 of 135). The owed question is that one. The answer to the coordinator's question is unchanged (flash on the opponent's turn: offered 141, taken 11 = 0.078 [0.044, 0.134]; all flash casts at instant speed 141/3,786 = 0.037 [0.032, 0.044]).

## 13b — the clone: a fresh card-aware network behaviour-cloned on 68,500 CP7 labels (2026-09-15; branch `v7/lane-d`; runbook `rl/PHASE13-BC.md`)

**Recipe** (`rl/run_13b.sh`, chained after the recording by `rl/chain_13ab.sh`). Init: a **fresh** P10INIT net,
`--cand-refers-pool`, seed 13 (`rl/artifacts/v7/13/init_on_s13.pt`, 17.5 M parameters). `rl/v7_bc.py` with its
defaults, fixed before the run: lr 1e-4, AdamW with decay 0.01 on the heads, batch 32, grad clip 1.0, logit
bound 5, 10 % of **games** held out, early stop on held-out CE with patience 3, one run, seed 0; all four
decision kinds (each passed the 13a gate); y = −1 and PASS-only k = 1 consults dropped. Memoryless scoring
(fresh heads state per consult), as in 7d. Best epoch 6 of 9, 1,299 s on cuda. `bc.pt` gitignored; `bc.log`.

| decision kind | held-out n | held-out CE (floor) | top-1 | copy ceiling | top-1 / ceiling | class top-1 | type | trivial predictor |
|---|---|---|---|---|---|---|---|---|
| priority | 5,677 | 0.318 (0.059) | **0.876** | 0.977 | **0.897** | 0.890 | 0.919 | PASS 0.547 |
| target | 718 | 0.257 (0.049) | 0.889 | 0.960 | 0.926 | 0.918 | 1.000 | index 0 0.623 |
| joint attack | 598 | 0.070 (0.000) | 0.977 | 1.000 | 0.977 | 0.977 | 0.995 | **last candidate 0.924** |
| joint block | 174 | 0.366 (0.000) | 0.799 | 1.000 | 0.799 | 0.799 | 0.828 | position 1 0.517 |
| all | 7,167 | 0.292 | 0.884 | | | 0.898 | 0.932 | |

(Copy ceiling as in 7d: the label is one index among identical candidates — the `_argmax_classes` key — so the
best reachable exact top-1 is the share of labels that are the first index of their class; CE floor = mean
log #copies. Trivial predictor = the best single label position over the whole recording, `rl/bc13_baseline.py`.)
Against Phase 7d's clone (W0Base, priority only): held-out top-1 0.606 against a 0.833 ceiling (0.727 of it),
type agreement 0.887 — this clone's priority top-1 is 0.897 of its ceiling and its class top-1 0.890, so it
follows CP7's card choice, not only its action type, on held-out games. **The attack head's 0.977 is only
0.05 above "take the last candidate"** (CP7's declared attack is the last option of CombatMath's kept list
0.924 of the time) — it cannot be read as learned attack judgement.

**Card-swap** (`rl/p10_cardswap.py`, the 10/A2 pairs and consult sets; `cardswap/cardswap_summary.txt`), mean Δp
with bootstrap 95 % CI:

| swap class | fresh flag-ON init | bc.pt |
|---|---|---|
| **text only** | 0.0430 [0.0405, 0.0456] | **0.0424 [0.0375, 0.0477]** (Δlogit 0.289 vs 0.235; strict flips 0.207 vs 0.119) |
| P/T | 0.018 | 0.025 |
| cost | 0.038 | 0.028 |
| type | 0.099 | 0.104 |
| own-afterstate control | 0.0015 | 0.0153 |

**CP7's reference census** (`dimir_census` over the 1,250 recording games, `census_cp7ref.txt`): self-removal
0.007, counterspells taken when offered 0.472, creatures cast per game 3.84, flash at instant speed 0.037,
ninjutsu taken 0.339, removal on the highest-power enemy 0.975.

**Census of bc.pt** (`rl/record_census.sh bc.pt BenchDimir cp7 25 p13_bc 13700`: argmax-classes play vs CP7,
25 games, the seed of the 13c per-block checks, transcripts kept; `census_bc.txt`), against CP7's reference:

| counter | bc.pt (25 games) | CP7 (1,250 games) | pre-registered clause |
|---|---|---|---|
| removal cast with only own legal targets | 2/120 = **0.017** [0.005, 0.059] | 0.007 | < 0.2 — **met** |
| counterspells taken when offered | 22/35 = **0.629** [0.463, 0.768] | 0.472 [0.446, 0.499] | in [0.2, 0.5] — **not met** (above) |
| creatures cast per game | **3.88** [2.99, 4.77] | 3.84 | ≥ 3 — **met** |
| flash cast at instant speed | 13/75 = 0.173 | 0.037 | — |
| removal on the highest-power enemy | 24/24 | 0.975 | — |
| ninjutsu taken | 2/9 | 0.339 | — |
| games won (a census, not a level) | 10/25 | — | — |

**Levels of bc.pt, three readouts on the same seeds** (`rl/run_13_levels.sh`, row seed 930000, BenchDimir
mirror; frozen server; `rl/artifacts/v7/13/levels/`):

| readout | vs CP7 (100) | vs heuristic (50) |
|---|---|---|
| sampled (`battery_p12s.sh`, -Drl.mode=train) | **33/100 = 0.330 [0.246, 0.427]** | 39/50 = 0.780 [0.648, 0.872] |
| two-stage (`--argmax-two-stage`, flag checked on the live server) | **31/100 = 0.310 [0.228, 0.406]** | 37/50 = 0.740 [0.604, 0.841] |
| argmax-classes (continuity only) | 32/100 = 0.320 [0.237, 0.417] | 37/50 = 0.740 [0.604, 0.841] |

0 stalls in every row; 17.2 turns per game vs CP7. **Script fault, not a failed measurement:** `run_13b.log`
marks the two-stage and argmax rows `L13|FAIL` — `run_13_levels.sh` grepped `^XDECKS` (the prefix of
`battery_p12s.sh`), while `battery_xdeck.sh` prints `XDECK|`; the games ran and the numbers above are read from
the rows' probe files (`probe_*_BenchDimir.txt`). Fixed for reruns (`^XDECKS?|`). The same prefix mismatch, the
other way round, was in the generated 13c controller (phase12's `battery()` kept only `XDECK|` lines, so the
sampled readout would have parsed as 0/0 at every 13c level); fixed in `rl/make_phase13.py` and regenerated
before 13c launched. **The three readouts agree** (0.33 / 0.31 / 0.32 vs CP7): the Phase 12 argmax artifact (PASS
against an acting majority) does not show on the clone. Against Phase 12's Dimir main: sampled 0.330 is clear
above its sampled start 0.120 [0.070, 0.198] (intervals disjoint) and above its best sampled point 0.220 [0.150,
0.311] by the point, overlapping.

**Readings, as pre-registered.**
* **Card-level clone — NOT met by the rule's letter, so "type-level clone again" is the recorded label**, with
  the ceiling fraction stated as the runbook asks: the first clause holds (held-out priority top-1 0.876 =
  **0.897 of its 0.977 copy ceiling**, ≥ 0.8; target 0.926, attack 0.977, block 0.799 of theirs), the second does not (text-only card-swap Δp of bc.pt 0.0424
  [0.0375, 0.0477] vs the fresh flag-ON net's 0.0430 [0.0405, 0.0456]; lower by 0.0006, intervals overlapping).
  What the label cannot carry, stated beside it rather than instead of it: this is not the 7d failure in the
  7d sense — 7d's clone reached 0.727 of its ceiling and a type agreement that exceeded its card agreement by
  0.28; this one's class top-1 (0.890) is within 0.03 of its type agreement (0.919), and on text swaps bc.pt's
  logit shift (0.289 vs 0.235) and argmax flip rate (0.207 vs 0.119) are both higher than the fresh net's; the
  Δp measure is compressed by bc.pt's far sharper logits (mean top gap 4.21 vs 0.35). The pre-registered
  measure was Δp, and on Δp the clause fails.
* **Competent start — NOT met:** sampled 0.330 [0.246, 0.427] and two-stage 0.310 [0.228, 0.406] vs CP7 are both
  below 0.35, with the bar inside both intervals. The clone is nevertheless clear above Phase 12's sampled start
  (0.120 [0.070, 0.198], disjoint) and above its best sampled point (0.220) by the point estimate — 13c starts
  from a policy that already wins a third of its games against CP7 under every readout.
* **Habits cloned — 2 of 3 clauses met:** self-destroy 0.017 (< 0.2), creatures 3.88 per game (≥ 3); counterspells
  0.629 is above the [0.2, 0.5] band (CP7's own 0.472 sits inside it; the clone over-counters on 35 offers).
* **Positional caveat:** the attack head's 0.977 agreement is 0.05 above "take the last candidate" (0.924).

Cannot: exceed its teacher in expectation (a faithful clone in the CP7 mirror sits near 0.5 at best); say
anything off BenchDimir; separate imitation from the positional regularity in the attack labels; say the clone
plays draw-go flash (the teacher does not, 13a addendum); read the census as a level (25 games, argmax).

## 13c — RL against CP7 from the clone: BREAK at 2,048 (2026-09-15; branch `v7/lane-d`; runbook `rl/PHASE13-BC.md` + Amendment 1)

One main (M_B, BenchDimir mirror) from `bc.pt`, Phase 12 recipe (lr 3e-5, 1 epoch, logit bound 5,
AdamW wd 0.01 on heads, `--adv-norm batch`, `--target-kl 0.02`), 75/25 CP7/heuristic rotation, 256-episode
blocks, 100-game CP7 / 50-game heuristic levels every 1,024 in three readouts. Stopped by the
pre-registered make-or-break rule (Amendment 1, committed 27dc99d before any block past 1,024 reported).

| checkpoint | sampled vs CP7 | two-stage vs CP7 | argmax vs CP7 | sampled vs heur | two-stage vs heur | argmax vs heur |
|---|---|---|---|---|---|---|
| bc.pt (13b) | 33/100 = 0.330 [0.246, 0.427] | 31/100 = 0.310 [0.228, 0.406] | 32/100 = 0.320 [0.237, 0.417] | 39/50 = 0.780 [0.648, 0.872] | 37/50 = 0.740 [0.604, 0.841] | 37/50 = 0.740 [0.604, 0.841] |
| 1,024 | 22/100 = 0.220 [0.150, 0.311] | 35/100 = 0.350 [0.264, 0.447] | 39/100 = 0.390 [0.300, 0.488] | 36/50 = 0.720 [0.583, 0.825] | 36/50 = 0.720 [0.583, 0.825] | 37/50 = 0.740 [0.604, 0.841] |
| 2,048 | 29/100 = 0.290 [0.210, 0.385] | 24/100 = 0.240 [0.167, 0.332] | 32/100 = 0.320 [0.237, 0.417] | 31/50 = 0.620 [0.482, 0.741] | 33/50 = 0.660 [0.522, 0.776] | 30/50 = 0.600 [0.462, 0.724] |

Training blocks (sampled play, moving policy): CP7 0→1,024 214/768 = 0.279 [0.248, 0.311] (blocks 0.281 /
0.270 / 0.285); CP7 1,024→2,048 168/768 = 0.219 [0.191, 0.249] (0.211 / 0.238 / 0.207); heuristic blocks
166/256 = 0.648 and 183/256 = 0.715. 25-game argmax checks vs CP7: 0.16, 0.36, 0.44, 0.16, 0.40, 0.56, 0.28, 0.12.

Pre-registered readings:
* **Improves on the clone: not met.**
* **Forgets the clone: not met as defined** (no sampled or two-stage level clearly below bc.pt's; every interval
  overlaps). But it is a **regression, not flat**: at 2,048 all four graduation-readout cells are below bc.pt's
  point estimates, and the CP7 training win rate fell 0.279 → 0.219 with intervals that only touch.
* **Habits hold: not met** — counter selectivity left its band once in the last four checks (0.293, 0.300,
  **0.197**, 0.286; bc.pt 0.629, first 13c check 0.721); self-removal < 0.2 held (≤ 0.025); creatures ≥ 3 held
  (3.52–4.36).
* **Amendment 1: BREAK** (`rl/artifacts/v7/13/c/makebreak.txt`): rule (a) best sampled/two-stage 29/100 < 43;
  rule (b) CP7 training blocks 1,024→2,048 Wilson lower 0.191 ≤ 0.311. STOP touched 2026-09-15 22:49Z; the
  controller finishes block 2,048→2,304 (not part of the verdict). The KL-to-bc.pt remedy was pre-registered
  only for "forgets" and is not triggered by this verdict.

Behaviour (census, 25-game argmax checks): the clearest change from bc.pt is fewer counters — We Say Thee Nay!
offered about twice as often but cast rarely (bc.pt 8/27, 1,024 check 5/58); Spell Snare / Spell Pierce
still taken almost always; flash creatures drift toward main-phase casting (instant-speed share 0.17 → ~0.08,
intervals overlap); removal targeting and board development unchanged. Transcripts (bc.pt vs 1,024 check):
losses end ~turn 17–18 with the learner at ~3 life and CP7 at 12–15 (races lost, not stalls); attacks match the
CombatMath reference 73/81 vs 69/79; legend-rule self-losses 2 per 25 games in both (not a cause).

Learner statistics (server log, by quarter of the 64 updates): value_ev 0.05 / 0.16 / 0.15 / 0.22; approx_kl
mean 0.0012–0.0014 per update (max 0.0032) against the 0.02 target; entropy 0.22–0.25; grad norm 7.2 → 2.8.
**Interpretation (inference, not tested):** a sparse win/loss signal over 60–95 decisions per game, a value
function that explains ≤ 22 % of outcome variance and 64 tiny updates is mostly noise around a good imitation
optimum, so steps away from CP7's choices tend to cost games.

Cannots: one seed; CP7 skill 6 only; 100-game levels resolve ~±0.09; the checks are argmax over 25 games; the
diagnosis above is a reading of the statistics, not an experiment. Candidate next steps (user's decision, none
run): an offline value-fit test on the 13a recordings (can the network predict outcomes at all?), a CP7
skill ladder with the same recipe (is skill 6's search the ceiling?), larger steps with a KL-to-bc.pt anchor,
DAgger-style relabelling of the learner's own states by CP7.

## 14 — diagnostics: can the network predict outcomes (D1), and is CP7 skill 6 the ceiling (D2)? (2026-09-15; branch `v7/lane-d`; runbook `rl/PHASE14-DIAG.md`)

Two diagnostics run after 13c BROKE at 2,048 episodes. Pre-registration (thresholds, readings and the combined
table) is in `rl/PHASE14-DIAG.md`, committed 7b05cde before either ran; nothing below changes a threshold.
D1 (offline value fit) and D2b (1,024 episodes vs a weaker CP7) are appended to this section when they report.

### 14 / D2a — the CP7 skill ladder of the clone (bc.pt, sampled readout, 100 games per rung)

`bc.pt` (the 13b clone) against CP7 on the BenchDimir mirror, sampled play, row seed 930000 — the same seed
as bc.pt's skill-6 row in 13b, so the three rows see the same deals. 0 stalls anywhere.

| CP7 skill | search depth / think time | bc.pt sampled level | turns/ep |
|---|---|---|---|
| 1 | depth 4, 3 s | 23/100 = 0.230 [0.158, 0.322] | 18.8 |
| 3 | depth 4, 9 s | 18/100 = 0.180 [0.117, 0.267] | 18.7 |
| 6 (13b) | depth 6, 18 s | 33/100 = 0.330 [0.246, 0.427] | 17.2 |

**The ladder is inverted: the clone does not do better against a weaker CP7, it does slightly worse.**

**What `rl.aiSkill` actually is** (asked before reading the ladder as a difficulty axis). `-Drl.aiSkill` goes
straight into the CP7 constructor (`rl/xmage-src/EpisodeRunner.java:248-252`, opponent seat; `:178-181`, the 13a
teacher seat), `ComputerPlayer7` forwards it unchanged to its parent
(`Mage.Server.Plugins/Mage.Player.AI.MAD/src/mage/player/ai/ComputerPlayer7.java:23-24`), and the parent binds it
(`.../ComputerPlayer6.java:92-101`): `if (skill < 4) { maxDepth = 4; } else { maxDepth = skill; }`,
`maxThinkTimeSecs = skill * 3`, `maxNodes = MAX_SIMULATED_NODES_PER_CALC` (5000, a constant, line 54). So skill 1
and skill 3 have the **same search depth (4)** and differ only in think time (3 s vs 9 s); skill 6 is depth 6 /
18 s. Nothing about evaluation or candidate pruning changes with skill. The lower two rungs are therefore a
**time** ladder at equal depth, which is consistent with skill 3 (same depth, 3x the time) beating skill 1.

**Reading.** The clone was cloned from CP7 *at skill 6* (13a recorded `rl.agent=cp7 -Drl.aiSkill=6`), so a
lower-skill CP7 is an **off-distribution opponent** — one that behaves differently — rather than a weaker version
of the opponent bc.pt learned to imitate. A shallower, less deliberative CP7 is not easier for this clone.

**Training rung = skill 1**, by the pre-registered rule as written ("if skill 1 is already ≤ 0.35, use 1"; it is
also the lowest of {1, 3} at ≤ 0.70). Stated plainly: the rule's premise — that a weaker CP7 gives the clone
headroom — is contradicted by the measurement, and no threshold was changed after seeing it.

**Cannots.** The three Wilson intervals overlap (skill 1 [0.158, 0.322] vs skill 3 [0.117, 0.267] heavily; skill 1
vs skill 6 [0.246, 0.427] slightly), so 100 games per rung establish "no headroom appears at lower skill", **not**
the order of the rungs. One seed, one deck, sampled readout only. CP7's search is wall-clock limited, so its
effective strength depends on machine load: the two D2a arms ran in parallel (2 servers + 2 JVMs competing) while
the skill-6 reference row ran alone — that confound would have made the skill-1 / skill-3 opponents *weaker* than
their nominal budget, i.e. it pushes opposite to the observed inversion and cannot explain it away.

**Pre-stated before D2b reported** (`rl/PHASE14-DIAG.md` STATE, 23:37Z): because the ladder is inverted, a "does
not climb" at skill 1 cannot be read as "the recipe cannot climb against a weaker opponent" — only as "it does not
climb against this off-distribution opponent, from this start, in 1,024 episodes". Also pre-stated: the training
lane runs 4 concurrent driver jobs while the eval rows run 1–2, and CP7 at skill 1 is limited by wall-clock think
time, so the opponent trained against and the one scored against are not guaranteed to be equally strong.

### 14 / D1 — offline value fit on the 13a recordings: can the network predict outcomes from what it sees?

Every consult with a v7 state in the 25 recordings (68,952 consults, 1,250 games) targets the recorded seat's
final outcome (±1). Hold-out = the 13b split reproduced exactly (`rl/v7_bc.py`: labelled games, sorted,
`Random(0).shuffle`, first 10 %) — 125 games, 7,535 consults, held-out mean r = 0.579, Var = 0.665, 0 draws.
Early stopping uses a validation split of 10 % of the *training* games (`Random(1)`), so the hold-out is never
used for model selection (a deliberate departure from `v7_bc.py`, which early-stops on its hold-out).
Script `rl/p14_d1.py`; log + JSON in `rl/artifacts/v7/14/d1/`. Intervals = 1,000 bootstrap resamples of held-out
GAMES (consults of a game move together). Stage = own-turn number, ceil(global turn / 2): early ≤ 6, mid 7–12,
late ≥ 13.

Models: **N1** = bc.pt's own critic (`rl/v7_value.py` ValueTrunk — its own token builders, its own 4-layer
encoder and value MLP, the path `policy_server.py` trains), trained on the outcome; BC never trained it
(`v7_bc.py` runs `with_value=False`), so it starts from the fresh P10INIT critic. **N2** = the clone's
representation frozen: the game vector the policy heads return, from an untouched load of bc.pt, with a value MLP
of the critic's shape on top. **B0** = logistic regression on ten scalars from the same consults (life, hand size,
lands, non-land permanents — each me and opponent — global turn, my-turn flag; `E[r] = 2p − 1`).

| model | overall EV | overall AUC | early EV / AUC | mid EV / AUC | late EV / AUC |
|---|---|---|---|---|---|
| N1 (critic trained on outcome) | **0.095** [−0.172, 0.256] | 0.788 [0.710, 0.859] | −0.116 / 0.686 | 0.353 / 0.875 | 0.028 / 0.717 |
| N2 (frozen clone representation) | 0.146 [−0.011, 0.228] | 0.761 [0.710, 0.815] | −0.019 / 0.653 | 0.341 / 0.874 | 0.123 / 0.713 |
| B0 (ten scalars) | **0.196** [0.002, 0.315] | 0.799 [0.725, 0.869] | 0.001 / 0.667 | 0.377 / 0.887 | 0.434 / 0.932 |

Paired differences on the held-out games: N1 − B0 = **−0.101** [−0.293, +0.074] EV; N2 − B0 = −0.050
[−0.178, +0.081]; N1 − N2 = −0.051 [−0.212, +0.072]. Stage sizes: early 3,875 consults / 125 games, mid 3,179 /
118, late 481 / 17.

Pre-registered readings:
* **"The encoding can predict outcomes": NOT met.** It needed N1 EV ≥ 0.35 AND N1 − B0 ≥ 0.05; N1 is 0.095 and is
  *below* B0.
* **"Outcomes are barely predictable from observations": MET** (N1 EV 0.095 ≤ 0.25).
* **"If B0 ≥ N1, say so": B0 ≥ N1.** Ten hand-picked counters explain outcome variance at least as well as the
  6.9 M-parameter critic trained on the same states — the network is not using the state better than a handful of
  scalars. The interval on the difference includes 0, so B0 is not *clearly better* either; what is established is
  that the network is not better.

Two further observations, not pre-registered:
* **Rank vs calibration.** All three models have AUC ≈ 0.76–0.80 while EV ≈ 0.10–0.20: the *ordering* of positions
  carries real signal, the squared-error fit does not. A critic used for GAE needs the magnitude, not just the order.
* **The critic overfits fast.** N1's best epoch was 2 of 12 (val_mse 0.5600); by epoch 5 train_mse had fallen
  0.5677 → 0.2346 while val_mse rose to 0.6279. At 1,125 training games this fit is data-limited, not capacity-limited.

Cannots. These are CP7-vs-CP7 and CP7-vs-heuristic positions, **not the learner's own states**, so this bounds what
a critic could learn from *these* recordings, not what the online critic sees. The hold-out pools two opponent
populations — lane H (CP7 vs the heuristic, CP7 winning 0.831) and lane C (the mirror, 0.492) — so part of every
model's explained variance is "which population is this game from", readable from the opponent's deck and play;
that inflates all three EVs relative to a single-opponent setting, and the recordings kept no per-row lane label in
`d1.json`, so the split was not measured. One seed; the late bucket is 481 consults over 17 games and its interval
spans almost the whole range. The target here is the undiscounted ±1 outcome, while the lane's `value_ev` uses a
discounted Monte-Carlo return, so these numbers are not the same quantity as 13c's 0.05–0.22 (they are of similar
size). The critic was given no privileged rows, because the recordings carry none — this is the unprivileged value
path, not the `oe`-fed one `policy_server.py` can build.

**D1 addendum — three readings the row above left implicit.**

*Where B0 wins, and how firmly.* B0's point estimate is the highest of the three at **every** stage, not just
overall: early 0.001 vs N1 −0.116 and N2 −0.019; mid 0.377 vs 0.353 and 0.341; late 0.434 vs 0.028 and 0.123. But
the strength of that statement differs by stage: in **mid** the three sit inside each other's intervals
(B0 [0.182, 0.516], N1 [0.047, 0.553], N2 [0.183, 0.447]) — a three-way tie, not a win; in **late** the bucket is
17 games and nothing is readable; **early** is where B0's advantage is most consistent, and there every model is
near zero anyway. All three paired differences cross zero (N1 − B0 = −0.101 [−0.293, +0.074]; N2 − B0 = −0.050
[−0.178, +0.081]; N1 − N2 = −0.051 [−0.212, +0.072]). So "B0 beats the networks" is a **point-estimate**
statement. What 125 held-out games do establish is the negative: neither network is *better* than ten scalars,
which is what the pre-registered clause asked.

*Consistency with 13c — the online critic was not unusually bad.* 13c's learner statistics gave `value_ev`
0.05 / 0.16 / 0.15 / 0.22 by quarter of its 64 updates. That band sits on top of this offline fit (N1 0.095,
N2 0.146, B0 0.196). The two are not the same quantity — 13c's is a discounted Monte-Carlo return on the
learner's own states, this is the undiscounted ±1 outcome on CP7's states — so this is a consistency reading,
not an equality. Read that way, **the 13c critic was performing near what this encoding supports**, so "the
critic was badly trained" is not the explanation for 13c's failure; the ceiling is low for anything fit to these
observations. This is the single most load-bearing sentence in D1, and it is an inference from two numbers of
similar size, not a measurement of the same number twice.

*Two more cannots.* The hold-out is **125 games**; every interval above is that wide for that reason, and no
stage claim except "mid is where prediction works" survives it. EV is computed against a **stage-mixed variance
denominator** on a ±1 target: the overall column divides by the variance of the whole held-out pool, so a model
that is good only in mid-game (as all three are) scores an overall EV well below its mid-game EV. That is why
N1's overall 0.095 is lower than its mid 0.353, and it is an artefact of the denominator, not a separate finding.

### 14 / D2b — 1,024 episodes of the Phase 13 recipe against CP7 at the rung (skill 1)

From `bc.pt`, the Phase 13 recipe unchanged (lr 3e-5, 1 epoch, logit bound 5, AdamW wd 0.01 on heads,
`--adv-norm batch`, `--target-kl 0.02`), opponent = CP7 at skill 1 **only** (no heuristic blocks), 256-episode
blocks, lane seed 41, runner `rl/run_14d2b.sh`. 0 draws and 0 stalls everywhere.

| training block | episodes | win rate |
|---|---|---|
| 1 (0 → 256) | 69/256 | 0.270 |
| 2 (256 → 512) | 67/256 | 0.262 |
| 3 (512 → 768) | 62/256 | 0.242 |
| 4 (768 → 1,024) | 81/256 | 0.316 |
| pooled 0 → 512 | 136/512 | 0.266 [0.229, 0.306] |
| pooled 512 → 1,024 | 143/512 | 0.279 [0.242, 0.320] |
| whole run | 279/1,024 | 0.272 [0.246, 0.301] |

100-game levels vs CP7 **at skill 1**, both readouts, each against its own same-skill baseline:

| checkpoint | sampled | two-stage |
|---|---|---|
| bc.pt (the start) | 23/100 = 0.230 [0.158, 0.322] | 38/100 = 0.380 [0.291, 0.478] |
| ck_1024 (after 1,024 episodes) | 34/100 = 0.340 [0.255, 0.437] | 33/100 = 0.330 [0.246, 0.427] |

Pre-registered readings:
* **"Climbs against a weaker CP7": NOT met**, on both of its clauses. (a) The sampled level rises 0.230 → 0.340,
  but the Wilson intervals overlap ([0.255, 0.437] vs [0.158, 0.322]), so it is not *clearly* above; the two-stage
  level does not rise at all — 0.330 against the start's 0.380 — so that half of the clause fails in the opposite
  direction. (b) Pooled training blocks 512→1,024 (0.279 [0.242, 0.320]) are not clearly above blocks 0→512
  (0.266 [0.229, 0.306]); the intervals overlap almost entirely.
* **"Does not climb even against a weaker CP7": MET** (the `otherwise` branch), with the caveat pre-stated before
  the run: skill 1 is **off-distribution rather than weaker** (D2a), so this says the recipe does not climb against
  *this* opponent from *this* start in 1,024 episodes — not that it cannot climb against a weaker opponent in general.

**The two readouts disagree in direction, so both are reported** (the Phase 13 evaluation protocol). Sampled says
+0.11, two-stage says −0.05. Note also that bc.pt's own two readouts differ by 0.15 at skill 1 (0.230 sampled vs
0.380 two-stage) where at skill 6 they nearly agreed (0.330 vs 0.310): at this opponent the *readout* choice moves
the number more than 1,024 episodes of training did. No conclusion about "improvement" survives that.

### 14 — combined reading

The runbook's table, entered with D1 = **barely predicts** and D2 = **does not climb**:

> *barely predicts × does not climb* — **the win/loss signal from this encoding is too weak for this RL at this
> scale: a privileged critic, denser rewards, or search.**

That is the row that applies, and both diagnostics point the same way independently: nothing fit to these
observations predicts outcomes better than ten scalars (D1), and 1,024 episodes against a differently-skilled CP7
move neither the levels nor the training win rate (D2b).

**Cannots for section 14 as a whole.** One seed everywhere; 1,024 episodes is short, and a "does not climb" at this
scale is about this recipe at this scale. Every level is 100 games, resolving only about ±0.09 — the sampled
+0.11 is right at that edge, which is why it is not readable as a climb. The CP7 skill ladder is inverted and
below skill 4 only think time varies, so "weaker opponent" was never actually tested; what was tested is a
differently-behaving one. CP7's search is wall-clock limited while the training lane runs 4 concurrent driver jobs
and the eval rows run 1–2, so the opponent trained against and the one scored against are not guaranteed equally
strong (pre-stated, unmeasured). D1's states are CP7's, not the learner's, and its hold-out mixes two opponent
populations. **No behaviour census was run for D2b** (13c had per-block counters), so nothing here says what the
policy changed about its play — only that the outcome numbers did not move.

**D2b addendum — two readings that the tables above do not make on their own.**

*The readouts converged instead of rising, and that is a Phase 12 problem recurring.* At skill 1 the clone's two
readouts disagree by 0.15 (sampled 0.230 [0.158, 0.322], two-stage 0.380 [0.291, 0.478] — barely overlapping),
where at skill 6 they nearly agreed (0.330 vs 0.310). This is the readout-faithfulness problem Phase 12 recorded:
sampled play and the two-stage act/pass decomposition do not measure the same policy, and the gap is opponent-
dependent. After 1,024 episodes the two land on 0.340 and 0.330 — the training moved them **toward each other**,
not up. An "improvement" visible in one readout and absent in the other is a readout artefact until a third
measurement separates them, and none was run here.

*Opponent strength barely moves the training win rate, which is the direct evidence.* CP7 training win rate is
**0.272 [0.246, 0.301] over 1,024 episodes at skill 1**, against **0.279 [0.248, 0.311] over the first 1,024
episodes at skill 6 in 13c** — the same number, at opponents whose search differs by two plies of depth and 6x the
think time. Together with D1 (nothing fit to these observations beats ten scalars), this is what identifies the
block as **the learning signal, not the opponent**: making the opponent different did not change what the learner
extracts per game. It also makes a league premature — a league varies the opponent, which is the axis just shown
not to matter at this scale. What this cannot support: two skills on one deck with one seed, and "the same number"
is an overlap of two intervals, not a demonstration that opponent strength is irrelevant in general.

## 15 — architecture validation: does the network fit, keep card identity, and transfer? (2026-09-16; branch `v7/lane-d`; runbook `rl/PHASE15-ARCH.md`)

Offline supervised work on the 13a recordings and the curriculum ladder; no RL. Pre-registration (thresholds and
readings) is `rl/PHASE15-ARCH.md`, committed before any rung ran (A4L, the transfer ladder, replaced A4 before A4
had run — the old A4 is kept in the file marked superseded). Nothing below changes a threshold.

### 15 / A0 — can it fit at all? PARTIAL against the bar as written; the fail branch's diagnosis is excluded

A deliberate memorisation task (`rl/p15_a0.py`, `rl/run_15a0.sh`): 2,000 labelled consults from 40 games, 40
epochs, AdamW **weight decay 0**, lr 1e-4, batch 32, no early stop, no hold-out; then the value head on the same
40 games' outcomes (2,225 consults, 40 epochs). Init = `rl/artifacts/v7/13/init_on_s13.pt`, the fresh
`--cand-refers-pool` net 13b started from (15.7 M policy parameters). The 40 games are taken **round-robin over
both 13a lanes** (20 from `rec13_H_s13000`, CP7 vs the heuristic; 20 from `rec13_C_s13500`, the CP7 mirror) so the
value half has outcome variance (held r mean 0.255, Var 0.935); a single lane is ~0.83 wins. Scoring is
`rl/v7_bc.py`'s, unchanged — the same parse, the same memoryless per-consult state, the same candidate
cross-entropy 13b used; the value path is `rl/p14_d1.py`'s N1 and its EV, unchanged.

| measure | value | bar |
|---|---|---|
| training CE (pooled copy floor 0.0408) | **0.0476** | — |
| training exact top-1 | **0.9795** | ≥ 0.99 — **not met** |
| training **class** top-1 (the `_argmax_classes` key) | **0.9960** | — |
| training type agreement | 0.9980 | — |
| training value EV (MSE 0.0086, Var(r) 0.9351) | **0.9908** | ≥ 0.95 — **met** |

Per kind (exact top-1 / this slice's exact-top-1 copy ceiling): joint attack 1.000 / 1.000 (n 168), joint block
1.000 / 1.000 (n 54), priority 0.979 / 0.981 (n 1,572), target 0.961 / 0.961 (n 206).

**Why this is PARTIAL and not a fail.** The exact-top-1 metric is capped by the copy ceiling — the label is one
index among identical candidates (13b's measure), and on this slice the pooled exact-top-1 ceiling is **0.9810**.
The pre-registered bar of 0.99 is therefore **above what the metric can reach on this slice, regardless of fit**;
the measured 0.9795 is **0.9984 of that ceiling**, and two of the four kinds sit exactly on their ceiling. The bar
is reported as written and is not met; it is not reinterpreted, and it was not changed after seeing the data.

What the fail branch asked to be checked is checked directly and comes back clean:
* **gradients reach the card path** — grad norms after epoch 1: frozen-table adapter **0.118**, the Phase 10
  candidate-to-card pool `cand_ref` **0.204**, zone MLP 0.033, pointer 0.066 (printed by `p15_a0.py`, not inferred);
* **masking** — the joint attack and block heads reach exactly 1.000 on their own consults;
* **the fit is reached, not merely approached** — training CE 0.0476 against a 0.0408 copy floor, class top-1
  0.9960.

**Decision (logged in `rl/PHASE15-ARCH.md` STATE, made without the user in the loop):** the phase continues to A1.
The runbook's fail branch is "the plumbing is broken … stop the phase and find it"; three independent readings say
it is not broken, and the single clause that misses is a metric ceiling rather than a fit failure. Recorded as
PARTIAL so that the bar stands as written.

**Cannots.** Says nothing about generalisation — nothing was held out, by design. One slice, one seed, one init.
The value EV here is a *memorisation* number on 40 games and is not comparable with 14/D1's held-out 0.095. The
copy ceiling is a property of this slice; a different 40 games would cap the metric somewhere else.

### 15 / A1 — is the fit data-limited or capacity-limited? **DATA-LIMITED by the rule as written — carried entirely by the policy half; the value half is flat**

`rl/p15_a1.py`, two stages. Nested fractions (one `Random(0)` shuffle, prefixes taken, so each fraction is a
doubling of the *same* pool) of the 1,125 training games, scored against **the 13b hold-out reproduced exactly**
(125 games; 7,167 labelled consults for the policy stage, 7,535 for the value stage). Policy stage = 13b's recipe
unchanged (fresh `--cand-refers-pool` init, lr 1e-4, AdamW decay 0.01 on heads, batch 32, ≤ 20 epochs, early stop
on held-out CE, patience 3, seed 0). Value stage = Phase 14 D1's N1 unchanged (bc.pt's critic trained on MSE to
the recorded seat's ±1 outcome, early stop on a validation split of 10 % of the *training* games so the hold-out
is never used for selection; EV = 1 − MSE/Var(r), 1,000 bootstrap resamples of held-out GAMES).

| fraction | train games | train consults | best epoch | held CE | **all top-1** | cls1 | type1 | priority | target | attack | block |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 12.5 % | 141 | 7,375 | 7 | 0.4033 | 0.8436 | 0.8571 | 0.9051 | 0.8415 | 0.8496 | 0.9298 | 0.5920 |
| 25 % | 281 | 14,893 | 5 | 0.3656 | 0.8573 | 0.8721 | 0.9146 | 0.8524 | 0.8872 | 0.9632 | 0.5287 |
| 50 % | 562 | 28,949 | 7 | 0.3191 | 0.8753 | 0.8889 | 0.9290 | 0.8677 | 0.8969 | 0.9699 | 0.7069 |
| **100 %** | 1,125 | 58,304 | 6 | 0.2922 | **0.8871** | 0.9022 | 0.9393 | 0.8793 | 0.8872 | 0.9783 | 0.8276 |

| fraction | train games | **value EV** | EV 95 % (bootstrap over games) | AUC |
|---|---|---|---|---|
| 12.5 % | 141 | −0.0314 | [−0.253, 0.096] | 0.701 |
| 25 % | 281 | −0.0575 | [−0.450, 0.128] | 0.764 |
| 50 % | 562 | **0.0970** | [−0.136, 0.243] | 0.770 |
| **100 %** | 1,125 | **0.0951** | [−0.172, 0.256] | 0.788 |

**Readings, as pre-registered.** The rule is an OR: *data-limited* if the last doubling adds ≥ 0.01 top-1 **or**
≥ 0.03 EV; *saturated* if it adds < 0.01 top-1 **and** < 0.03 EV.
* **Overall: DATA-LIMITED**, on the top-1 clause alone.
* **Policy half — still rising.** Doubling increments in all-kinds top-1 are +0.0137, +0.0180, **+0.0118**:
  monotone, decelerating, and the last one clears 0.01. Priority top-1 rises 0.8415 → 0.8524 → 0.8677 → 0.8793.
* **Value half — flat, and on its own it would read saturated.** The last doubling adds **−0.0019** EV
  (0.0970 → 0.0951), nowhere near +0.03, and the sign is negative. The two halves disagree and are reported
  separately rather than reconciled, as the runbook's "state what a number cannot support" requires.
* **A3 is not triggered by A1** (A3 depends only on A2's reading).

**Both halves reproduce their parent phases, which is the check that this is a measurement and not a tooling
artefact.** Policy 100 % vs 13b's clone (same recipe, same data, same hold-out): all-kinds top-1 0.8871 vs 0.884,
held CE 0.2922 vs 0.2920, cls1 0.9022 vs 0.898, type1 0.9393 vs 0.932, priority 0.8793 vs 0.876, best epoch 6 vs
6 — largest gap 0.004 on a rate, 0.0002 on CE, i.e. single-seed and cuda-nondeterminism scale. Value 100 % vs
Phase 14 D1's N1: EV **0.0951 vs 0.095**, best epoch **2** with val_mse **0.5600** in both, and the same hold-out
(125 games, 7,535 consults, held r̄ 0.579, Var 0.665).

**What this supports, and what it does not.**
* It supports: **more recordings are the cheap fix for the imitation side.** 1,250 BenchDimir games ≈ 2 h of
  engine time (13a), and the ladder decks run ~20× faster; the clone's agreement with CP7 was still climbing at
  the largest set we have.
* It does **not** support the natural next sentence, and the difference matters: **A1 gives no evidence that more
  data fixes the critic.** Phase 14 D1's addendum inferred from the critic's fast overfitting that "at 1,125
  training games this fit is data-limited, not capacity-limited"; A1 tests that inference directly by doubling
  the data, and EV does not move (0.0970 → 0.0951). Read as a **qualification of that D1 remark**: over this
  range, more of the same recordings did not buy the critic anything. The Phase 14 combined verdict ("the win/loss
  signal from this encoding is too weak for this RL at this scale") is untouched by A1 and, if anything, the value
  half is consistent with it.
* **Rank versus calibration again.** AUC rises monotonically with data (0.701 → 0.764 → 0.770 → 0.788) while EV
  does not — the same split Phase 14 D1 recorded (ordering carries signal, squared-error fit does not). A critic
  used for GAE needs the magnitude.

**Cannots.** One seed per point, and the fractions are nested, so the four points are not independent samples.
**Every value interval straddles zero and is ~0.4 wide**: the value half's "flat" is a statement about point
estimates under the pre-registered rule, and the intervals cannot separate any two fractions — that half has
essentially no power, and no claim about the critic should rest on it alone. The policy stage early-stops on the
hold-out (13b's behaviour, kept so the 100 % point is comparable with the published row), which makes every
held-out number here mildly optimistic, equally at every fraction. Nothing here is a win rate or says anything
about winning; the critic's effective sample is games (1,250), not consults. Only BenchDimir.

### 15 / A2 — does the policy network keep card identity? Probe 1 reads "the encoder discards card identity" (the bar as written) and A3 is triggered — but probe 2 disagrees and is reported beside it

Three probes on the SAME clone (`rl/artifacts/v7/13/bc/bc.pt`), each against two controls fixed in advance: the
frozen `card_emb_v8` row (ceiling, loaded once and shared by every arm) and a card-blind clone trained from
`V7Policy(random_table=True)` on the same 68,500 labels with 13b's recipe (floor;
`rl/artifacts/v7/15/a2/bc_random.pt`, best epoch 6). Tooling `rl/p15_a2.py`, `rl/run_15a2.sh`;
`rl/p10_cardswap.py` unchanged.

**A correction that shaped this row, made before any A2 number was read** (STATE 03:01Z, commit d1f810c). Probe 1
as pre-registered splits by GAME, but one recording is one deck, so the held-out games contain the SAME 22 card
identities the probe was fit on; and mana value, power, toughness, the type flags and the 18 keyword bits are
fields of the entity row (WIRE-V7 2d 10-17, 30-33, 34-51) that `v7_net.MLPSkip` is explicitly built to keep
linearly recoverable. The probe as written is therefore SATURATED — measured, not asserted: token 1.0000, frozen
embedding 1.0000, and the card-blind net 0.9792. A probe that a card-blind network passes at 0.98 cannot show
that card identity survives. So the bar as written is reported, and a card-identity split on OFF-WIRE columns
only (the 50 e2 columns the entity row does not carry, plus the 5 colour bits) is reported beside it.

**Probe 1 — representation, on the pre-registered population** (13a: 68,952 consults, 1,250 games, 60,003 probed
hand entities, 22 distinct cards, 6 held-out identities, 15,571 unseen-card entities, 12 informative off-wire
columns):

| | token (BC) | frozen embedding | card-blind floor |
|---|---|---|---|
| bar as written (41 cols, held games) | 1.0000 | 1.0000 | **0.9792** |
| **off-wire, unseen cards** | **0.8590** | **0.8727** | **0.7824** |
| on-wire (2 cols), unseen cards | 0.8515 | 0.7968 | **1.0000** |
| off-wire, seen cards | 1.0000 | 1.0000 | 0.9739 |

* Clause 1 **MET**: 0.8590 / 0.8727 = **0.984** of the embedding's own score (bar 0.80).
* Clause 2 **NOT MET**: the token is **+0.0766** above the card-blind floor (bar >= 0.25), and +0.0766 also
  satisfies the fail branch's "within 0.10 of the random floor".
* **Reading of record: "the encoder discards card identity" — the bar as written. A3 runs.** The two clauses are
  decided by the same number and are not contradictory: the token is near the embedding's ceiling, and so is a
  network that never sees the embedding.
* **On-wire cannot separate the models, and is reported only to show that**: the card-blind net scores 1.0000
  there, because those bits are in the wire. Only the off-wire split carries information.
* `rand_distinct_frac = 0.0` — every probed BenchDimir entity is clamped onto `CardTable`'s shared zero row, so
  this floor is a true card-blind floor, not a partially random-identity one.
* **Two populations are EMPTY here, by construction, and an empty population is not a pass**: `off_deck` = 0
  because probe 1 runs on BenchDimir recordings only, so no card is off-deck; `unseen_id` = 0 because none of
  BenchDimir's 22 cards fall in `card_emb_v8/split.json`'s held-out 10 % — they were all in the embedding's
  training split. Probe 3 exists to fill both.

**Probe 3 — unseen cards, pooled decks** (13a + the ladder's W0Base recording + `wire3a` decks, label-free
loading; 57 distinct cards, 35 held-out identities, 18 informative off-wire columns):

| population | n | token (BC) | ceiling | floor | token/ceiling | token − floor |
|---|---|---|---|---|---|---|
| unseen cards (= off-deck) | 27,576 | **0.9606** | 0.9706 | 0.7897 | 0.990 | **+0.1709** |
| unseen to the EMBEDDING (`split.json`) | 2,506 | 0.9473 | 1.0000 | 0.7338 | 0.947 | +0.2135 |
| seen cards | 32,444 | 1.0000 | 1.0000 | 0.9795 | — | — |

On these wider populations **neither branch fires**: the gap to the floor (+0.171, +0.214) clears the 0.10 discard
clause but misses the 0.25 survival clause. Recorded as **partial**, not bent toward either reading. The
pre-registered clauses attach to probe 1, whose reading stands.

**Probe 2 — behaviour** (`rl/p10_cardswap.py` unchanged, the 10/A2 pair lists and consult sets), mean dp with
bootstrap 95 % CI:

| swap class | fresh flag-ON init | bc.pt | card-blind floor |
|---|---|---|---|
| text only | 0.04298 [0.04054, 0.04556] | **0.04241 [0.03752, 0.04765]** | **0.02887 [0.02483, 0.03336]** |
| **text — embedding row ONLY** | 0.04315 | **0.03975 [0.03476, 0.04511]** | **0.01234 [0.01022, 0.01470]** |
| text — keyword bits only | 0.00352 | 0.00997 | 0.02053 |
| P/T | 0.01760 | 0.02500 | 0.01942 |
| cost | 0.03843 | 0.02843 | 0.00610 |
| type | 0.09934 | 0.10408 | 0.15237 |
| strict flip rate (text) | 0.119 [0.082, 0.157] | **0.207 [0.167, 0.247]** | **0.070 [0.042, 0.098]** |

**Probe 2 contradicts probe 1's floor clause, and that is the most informative thing in this row.** Swapping only
the embedding row moves the clone's probability 3.2x more than it moves the card-blind net's (0.03975 vs 0.01234,
disjoint intervals), and the clone's strict flip rate is triple the floor's (0.207 vs 0.070, disjoint). The
card-blind net's response to text swaps is almost entirely the keyword bits it reads off the wire (text_kw
0.02053 > text_emb 0.01234), which is exactly the confound probe 1's off-wire split was built to remove.
Reproduction check: bc.pt text 0.0424 and fresh 0.0430 are the 13b row's numbers.

**What A2 establishes, taking the three probes together.** Card identity IS present in the network and IS used
behaviourally (probe 2, disjoint from a card-blind control). What the linear probe cannot show is that much extra
mechanical fact survives in the entity token beyond what the wire already carries (probe 1: +0.077 over a
card-blind floor on the pre-registered population, +0.171 pooled). The runbook's own gloss for a pass-on-1 with a
floor-level probe 2 was "identity is present but unused"; what was measured is the reverse, and the honest
statement is that probe 1 is a weak instrument here rather than that identity is absent.

**The phase's central finding so far, from two independent measurements pointing the same way.** (1) The
card-blind clone reaches held-out priority top-1 **0.848** against bc.pt's **0.876** — deleting card identity
entirely costs **0.028**, and nothing at all on blocks (0.810 vs 0.799). (2) Probe 1's token sits only +0.077
above that same card-blind floor. **On this deck, what the network relies on is mostly wire fields, not card
identity.** That qualifies 13b's "card-level clone" discussion: a copy-ceiling fraction cannot separate card
choice from wire fields, and a card-blind control can.

**Cannots.** Probe 1's population has 22 distinct cards and 6 held-out identities over 12 informative columns —
thin, which is why probe 3 pools to 57 and 35. Linear probes LOWER-BOUND what is present: a fail can be
non-linear encoding, and probe 2 shows behaviour that probe 1 does not see. The floor is suspiciously high (0.78
off-wire from a 1,001-row random table) and a majority-class diagnostic is owed to say how much of that is class
imbalance rather than signal — it is added as an addendum, never as a bar. One seed, one clone per arm,
BenchDimir only; none of this is a win rate.

### 15 / A2 addendum — the majority-class diagnostic the row above records as owed

Probe 1's card-blind floor (0.7824 off-wire on unseen cards) was suspiciously high for a network that cannot see
the card table at all, so the obvious question is how much of it is signal and how much is class imbalance: most
off-wire columns are rare mechanics that are 0 for nearly every card. The diagnostic needs no network — predict
each column's TRAINING-set majority class, constant (`majority_baseline` in `rl/p15_a2.py`, a DIAGNOSTIC, never
a bar).

| | off-wire macro accuracy, unseen cards (12 cols, n = 15,571) |
|---|---|
| majority class, no model at all | **0.6537** |
| card-blind floor (RAND token) | 0.7824 |
| A3's auxiliary-loss clone (AUX token) | 0.8232 |
| the clone (BC token) | 0.8590 |
| frozen `card_emb_v8` row (ceiling) | 0.8727 |

Read as the share of the **0.6537 → 0.8727 span** (from "no information" to "the embedding itself"):
the card-blind floor captures **59 %**, AUX **77 %**, and the clone **94 %**. Per-column majority accuracies are
0.80, 0.80, 0.92, 0.74, 0.89, 0.68, 0.28, 0.54, 0.46, 0.89, 0.15, 0.69 — so the columns are indeed imbalanced,
but not uniformly. On seen cards the majority baseline is 0.7894, which is why the seen-card row of probe 1
(1.0000 for token and embedding, 0.9739 card-blind) carries so little information.

**What this settles.** The floor is **not** mostly an artefact of imbalance: imbalance alone buys 0.6537, while a
card-blind network reaches 0.7824, so the wire's entity fields genuinely carry mechanical information about
cards the probe has never seen. And it sharpens A2's central finding rather than softening it: measured against
"no information" instead of against zero, the clone recovers 94 % of what the frozen embedding itself yields,
while a network with no card identity at all already recovers 59 %.

### 15 / A3 — the remedy test: **"the remedy works" by the bar as written; it did not fix what A2 actually found**

Run because A2's probe 1 read "discards". `rl/p15_a3.py`: 13b's recipe unchanged (same fresh
`--cand-refers-pool` init, lr 1e-4, AdamW decay 0.01 on heads, batch 32, clip 1.0, logit bound 5, early stop on
held-out CE with patience 3, seed 0, the 13b hold-out, all four kinds) **plus** the pre-registered auxiliary loss:
a linear head on every encoded entity token predicts that card's 68 `e2_features`, BCE, **weight 0.1 fixed in the
runbook before any A3 data existed**. `rl/v7_bc.py` was deliberately not modified, so 13b stays reproducible and
A2 and the ladder keep calling it. 65,471 labelled consults, 1,250 games, aux coverage 0.942 of probed entities,
early stop at epoch 11 with best epoch 8, 1,680 s.

| | bc.pt (13b) | **bc_aux.pt (A3)** |
|---|---|---|
| held-out CE | 0.2920 | **0.2821** |
| all-kinds top-1 | 0.884 | **0.8846** |
| **priority top-1** | **0.876** | **0.8767** |
| class top-1 / type | 0.898 / 0.932 | 0.8979 / 0.9327 |
| held-out auxiliary BCE | — | **0.0000** (0.0034 after one epoch) |

Probe 1 re-run with all three arms on the same population the "discards" reading was made on (15,571 unseen-card
entities, 12 informative off-wire columns):

| arm | off-wire, unseen cards | fraction of the frozen-embedding ceiling | above the card-blind floor |
|---|---|---|---|
| frozen embedding (ceiling) | 0.8727 | 1.000 | +0.0903 |
| clone `bc.pt` | 0.8590 | 0.984 | **+0.0766** |
| **A3 `bc_aux.pt`** | **0.8232** | **0.943** | **+0.0408** |
| card-blind floor | 0.7824 | 0.896 | — |

**Readings, as pre-registered.**
* **Clause 1 — agreement: MET, at no cost.** Priority top-1 0.8767 against 13b's 0.876 is a drop of **−0.0007**
  (bar: ≤ 0.02). Held-out CE actually improves (0.2821 vs 0.2920).
* **Clause 2 — probe recovery: MET.** 0.8232 / 0.8727 = **0.943** ≥ 0.90.
* **Reading of record: "the remedy works."** Both clauses are met, and the bar is not reinterpreted.

**Why that reading, on its own, would mislead — stated beside it, not instead of it.**
1. **Clause 2 was already satisfied before the remedy.** `bc.pt` sits at **0.984** of the embedding's score; the
   0.90 bar was never the thing A2 failed. A2's failure was the **floor** clause — the token being only +0.0766
   above a network that cannot see cards at all.
2. **On that measure the remedy moved the wrong way.** AUX is **+0.0408** above the card-blind floor, *half* of
   bc.pt's +0.0766. Forcing every entity token to predict its 68 `e2_features` made the token's off-wire probe
   score **worse** (0.8590 → 0.8232), not better.
3. So the honest summary is: **the auxiliary loss is free (it costs no agreement and slightly improves CE) and it
   does not do what it was proposed to do.** The mechanism was certainly active — held-out auxiliary BCE reached
   0.0000, i.e. the tokens do encode the e2 columns — which makes the outcome more informative, not less: the
   columns were made *predictable by a head trained jointly with them* without making them more *linearly
   recoverable by a probe trained afterwards*.
4. On the bar as written (the saturated game-split probe), AUX scores 1.0000, exactly like bc.pt — that probe
   still cannot tell any of these networks apart, and the card-blind net scores 0.9792 on it.

**Checkpoint-selection caveat, recorded because it favours the conservative side.** `p15_a3.py` selects on
held-out CE (13b's rule, inherited deliberately). Held-out top-1 kept climbing after the selected epoch — 0.8919
at epoch 10 against 0.8846 at the saved epoch 8 — so selecting on top-1 would have made the remedy look better on
clause 1. The published number is the CE-selected one.

**Cannots.** One seed, one weight (0.1, fixed in advance and not tuned — a different weight might trade
differently), BenchDimir only, and the probe population is 22 distinct cards with 6 held-out identities over 12
informative columns. Linear probes lower-bound what is present, so "worse probe score" is not "less identity
present"; A2's probe 2 (behaviour) was not re-run on `bc_aux.pt`, so nothing here says whether the remedy changed
card-swap sensitivity, and that is owed. Nothing in A3 is a win rate.

**A3 addendum — probe 2 on `bc_aux.pt`, the item the row above records as owed. It reverses the natural reading.**

`rl/p10_cardswap.py` unchanged, the same pair lists and consult sets as A2's probe 2, `bc.pt` re-run beside it so
the two arms are scored on identical swaps (`rl/artifacts/v7/15/a3/cardswap/`):

| swap class | `bc.pt` (13b clone) | **`bc_aux.pt` (A3)** |
|---|---|---|
| text only | 0.04241 [0.03752, 0.04765] | **0.07001 [0.05801, 0.08195]** |
| **text — embedding row ONLY** | 0.03975 [0.03476, 0.04511] | **0.06730 [0.05522, 0.07956]** |
| text — keyword bits only (wire) | 0.00997 [0.00887, 0.01109] | **0.00604 [0.00524, 0.00682]** |
| P/T | 0.02500 [0.02178, 0.02824] | **0.06550 [0.05448, 0.07659]** |
| cost | 0.02843 [0.02487, 0.03200] | **0.05438 [0.04583, 0.06336]** |
| type | 0.10408 [0.09603, 0.11226] | 0.11201 [0.10191, 0.12120] |
| own-afterstate control | 0.01526 | 0.01879 |
| strict flip rate (text) | 0.207 [0.167, 0.247] | 0.149 [0.111, 0.196] |

**The auxiliary loss did what it was proposed to do — behaviourally.** Swapping only the embedding row moves the
remedied clone's probability **1.7x** more than the un-remedied one (0.06730 vs 0.03975, **disjoint intervals**),
and its sensitivity to P/T and cost roughly doubles, while its response to the wire's keyword bits **falls**
(0.00604 vs 0.00997, disjoint). That is a shift of weight from wire fields toward card identity: the direction
A3 was written to produce.

**And the linear probe cannot see it.** On the same checkpoint the off-wire probe score went the other way
(0.8590 → 0.8232). Both can be true at once: the probe asks whether a linear map from a frozen token recovers
mechanical columns **for card identities it was never fit on**, while the swap asks whether the network's own
decision moves when the identity changes. A representation can become more behaviourally load-bearing and less
linearly legible to a post-hoc probe at the same time — and the auxiliary head being trained *jointly* is exactly
the kind of thing that fits columns on seen cards without making them linearly decodable on unseen ones.

**What this does to A3's reading of record.** Nothing: the bar as written was two clauses, both were met, and
"the remedy works" stands. What changes is the caveat attached to it. The row above says the remedy "did not fix
what A2 actually found" because the floor gap on probe 1 halved; probe 2 says the remedy **did** move card
identity into the decision, measurably and with disjoint intervals. Both are reported. The honest joint statement
is that **probe 1 is the weak instrument here** — the same conclusion A2 reached from the other direction — and
that the case for the auxiliary loss now rests on behaviour rather than on the probe.

**Cannot:** one seed, one weight; the flip rate falls while Δp rises, so the two behavioural measures disagree in
direction and neither is a win rate; nothing here says the remedy helps the agent play better, only that its
decisions depend more on which card it is looking at.

**The two behavioural measures disagree in SIGN, and that belongs here rather than in the cannots.** On embedding-row swaps dp RISES (0.03975 [0.03476, 0.04511] -> 0.06730 [0.05522, 0.07956], disjoint) while the strict flip rate FALLS (0.207 [0.167, 0.247] -> 0.149 [0.111, 0.196]). The two ask different questions: dp is how much probability moves when the card changes, the flip rate is how often the argmax changes. Sharper logits would explain a larger dp with fewer flips, but the yardsticks are nearly equal (mean top gap 4.233 for bc_aux.pt against 4.209 for bc.pt), so sharpness does not account for it. Nothing measured here decides which of the two should be preferred, and the claim "the remedy increased card sensitivity" rests on dp alone; on flips it points the other way. Both are reported, and this disagreement is a standing caveat on the A3 addendum rather than a resolved point.

### 15 / A4L rung 0 — `W0Base`, the base of the ladder (the reference every later rung is measured against)

**Recording** (`rl/run_15rec.sh W0Base 1000`, the 13a job shape: two lanes, CP7 teacher vs the heuristic and the
CP7 mirror, 50-game jobs, seats by play/draw parity): **1,000 games, 31,281 labelled consults**, 20 jobs, every
job rc=0.

**Gate, per decision kind, on the full recording** (`rl/gate_15rec.sh`, the 13a gate):

| kind | consults | labelled | fraction | gate |
|---|---|---|---|---|
| priority | 19,070 | 19,070 | **1.000** | pass |
| target | 594 | 594 | **1.000** | pass |
| joint attack | 10,179 | 6,084 (exact 6,018, alias 66, miss 4,095) | **0.598** | **FAIL** |
| joint block | 9,157 | 5,533 (exact 4,782, alias 751, miss 3,624) | **0.604** | **FAIL** |

13a's convention applies — a kind that fails its gate is not cloned — and the passing set **`prio,target` is fixed
for every rung of the ladder** so rung-to-rung comparisons are comparable. **What that costs is stated here and
repeated in every keyword rung: with joint attack and block uncloned, the white ladder measures only whether the
rung's new card, by its presence, changes PRIORITY and TARGET choice. It says nothing about which blocks are
legal, the math of a trade, the attack-vs-hold-back tradeoff, or the arithmetic of a race — which is what rungs
1a–1d were built to test.** On this deck CP7 declares attack/block sets outside CombatMath's candidate list about
**40 %** of the time (against 5 % / 3 % on BenchDimir in 13a), so this is a property of vanilla-creature decks,
not of the tooling. *(Correction in the open: an earlier partial recording of 437 games gave 0.831 / 0.869 and the
runner derived its fixed kind set from that stale file; the kind set is unchanged, but the figures of record are
the 1,000-game ones above.)*

**Clone** (`rl/v7_bc.py`, 13b's recipe unchanged, the same fresh `--cand-refers-pool` init, kinds `prio,target`):
early stop at epoch 4, **best epoch 1**, held-out CE 0.5758, top-1 0.684, class top-1 0.777, type 0.908. Held-out
CE and every held-out rate are **identical from epoch 1 through epoch 4** while train CE barely moves — the clone
saturates immediately.

**Evaluation** (`rl/p15_a4.py`, the rung's own held-out games: 100 games, 2,902 scored consults). Rung 0 adds no
card, so the **aspect population is empty and `all` = `shared`**; and `ZERO` and `RUNG` are the **same checkpoint**
by construction. Both are correct, not defects.

| measure | n | top-1 | copy ceiling | fraction of ceiling |
|---|---|---|---|---|
| **priority** | 1,773 | **0.6791** | 0.8652 | **0.785** |
| **target** | 62 | **0.8226** | 0.9355 | **0.879** |
| all kinds — **not usable, see below** | 2,902 | 0.5796 | 0.9163 | 0.633 |
| joint attack — **never trained** | 597 | 0.2563 | 1.000 | — |
| joint block — **never trained** | 470 | 0.5830 | 1.000 | — |

Trivial predictor on this population: **0.6151** (best fixed index per kind, chosen on the rung's TRAINING games
and applied unchanged: priority = position 1, target = first, attack/block = last).

**Measurement note that governs every rung row.** `p15_a4.py` scores every decision kind present in the held-out
consults, but the clone is trained on `prio,target` only. The attack and block rows therefore come from heads
that were never trained, and the `all` row mixes them in — which is why `all` (0.5796) sits *below* the trivial
predictor (0.6151). **The rung's numbers are the priority and target rows.** `all` is reported once, here, to
document the artefact, and is not used in any reading.

**Reading — rung 0 is a reference, not a transfer test, and it sets a low bar.** The base clone reaches **0.785**
of its priority copy ceiling, but its priority top-1 (0.6791) is only **+0.064** above a fixed-position rule
(0.6151), and it stopped improving after one epoch. On a sixty-card vanilla white deck there is very little for a
card-aware network to learn beyond "play a land, cast the largest creature affordable", so the headroom any later
rung can demonstrate against this reference is small by construction. That is a property of the ladder's base,
and it will be carried into every rung reading rather than discovered again at each one.

**Cannots.** No transfer claim is made or possible at rung 0 (it is the reference). Two of four decision kinds are
uncloned. One seed, one clone. Top-1 against copy ceilings is not a win rate, and nothing here says how the clone
would play.

**Rung 0 addendum — the anchor is AT the trivial predictor on exact index, and every transfer clause is measured against it.**

Checked rather than assumed: `bc_W0Base.log` shows real training (held CE 0.8170 -> 0.5758, held top-1 0.653 -> 0.684 at epoch 1) and an honest early stop at epoch 4 saving best_epoch 1, so this is not a bug. But the numbers land exactly on the fixed-position rule:

| kind | clone exact top-1 | trivial rule | difference |
|---|---|---|---|
| priority | 0.67908 | 0.67908 (position 1) | **0.00000** |
| target | 0.82258 | 0.82258 (first index) | **0.00000** |

Equal to five decimals on both cloned kinds. The clone IS above trivial on the metrics that ignore ties - class top-1 0.777, type agreement 0.908 - and its priority exact top-1 is 0.785 of its copy ceiling (13b on BenchDimir reached 0.897 of its own). But on exact index the rung-0 anchor is a fixed-position rule.

**What this costs the ladder, stated here because every A4L reading is measured against this anchor.** The pre-registered clause "the shared game transfers" compares zero-shot top-1 on shared consults against the rung-specific clone on the same consults. If both sit at or near a fixed-position rule, that clause can be satisfied by two models that have learned almost nothing - it would be measuring the shared POSITIONAL regularity of the decks, not a shared game. So from rung 1 on, every row reports class top-1 and type agreement beside exact top-1, with the trivial predictor scored BOTH ways, and every reading names the metric it rests on. Where a clause is met on exact index but not on class agreement, the row says so rather than claiming transfer. This is a limitation of the ladder as instantiated on W0Base - a sixty-card vanilla deck whose priority decisions are nearly positional - not a reason to stop, and it sits beside the readings exactly as the uncloned combat kinds do.

### 15 / C — CombatMath candidate coverage: a bound on what any of our policies can express in combat

Raised by the A4L rung-0 gate and recorded here as a finding in its own right, because it bounds every combat result in this project rather than only the A4L rungs. The v7 seat chooses its attack and block sets from CombatMath candidate lists (rl/xmage-src/JointCands.java, lifted verbatim from RLPlayer). The 13a teacher counters measure how often the set CP7 actually declares is IN that list: teacherAtkConsults vs exact+alias, teacherBlkConsults vs exact+alias. A miss is a set our own policy could not have chosen either.

| deck / lane | joint attack | joint block | source |
|---|---|---|---|
| BenchDimir, pooled | 0.948 | 0.974 | 13a, 1,250 games |
| W0Base, pooled | **0.598** | **0.604** | A4L rung 0, 1,000 games |
| W0Base, lane H (CP7 vs heuristic) | 0.833 (2,436/2,923) | 0.867 (2,933/3,383) | per-job counters |
| W0Base, lane C (CP7 mirror) | **0.503** (3,648/7,256) | **0.450** (2,600/5,774) | per-job counters |

**The partial-vs-full discrepancy is explained, not merely noted.** An earlier gate on a partial 437-game W0Base recording read 0.831 / 0.869 and was quoted in three STATE entries before the full recording corrected it to 0.598 / 0.604. The partial sample was drawn almost entirely from the early jobs of lane H, and 0.831 / 0.869 is essentially lane H own rate. So the discrepancy is not sampling noise: coverage is **opponent-dependent**. The mirror lane also produces about 2.5x as many combat consults as the heuristic lane (7,256 vs 2,923 attack consults), so the pooled figure is dominated by the lane where coverage is worst. Job-order shows no trend within a lane (first five H jobs 0.832-0.854 attack; last five C jobs 0.508-0.534).

**What it bounds.** On a pure-creature deck in a competent mirror, about half of the attack sets and more than half of the block assignments that a strong search player actually chooses are OUTSIDE the candidate list our policy selects from. That is a ceiling on expressible combat play, independent of the network, the teacher and the training signal, and it is tightest exactly where combat decisions are most contested. It is therefore a candidate explanation - not a demonstrated one - for combat behaviour previously attributed to the policy: Phase 8 deck results, the Phase 10 league, and the atkaudit GAP / OVER lines read off 13c transcripts all involve seats drawing from this list. Re-reading those rows against per-deck coverage is OWED and is not done here.

**Carried forward:** every A4L rung row from rung 1 on reports its own decks coverage numbers, because they vary by deck and two rungs cannot be compared without them.

**Owed, needs instrumentation (deliberately not built overnight):** which declarations are missed. The teacher counters give only miss COUNTS; naming the kinds - partial attacks, multi-blocks, blocks that trade down - requires logging the candidate list beside the declared set at the consult, which is new engine plumbing. Written down rather than guessed.

**Cannots.** Two decks; the per-lane split is from job counters, not per-consult analysis; alias matches are counted as covered, so these are upper bounds on coverage; and nothing here says the missed sets are better play, only that they are unreachable.

### 15 / A4L rung 1a — `W1Fly` (Leonin Skyhunter, flying): **the aspect is NOT learnable at this rung, which VOIDS its transfer reading**

**Recording**: 1,000 games, 27,663 labelled consults. **Gate** (this deck's own, re-run on the full recording):
priority 17,047/17,047 = **1.000** pass, target 578/578 = **1.000** pass, joint attack 5,443/8,486 = **0.641** FAIL,
joint block 4,595/7,121 = **0.645** FAIL. **CombatMath coverage for this deck is 0.641 / 0.645** (W0Base: 0.598 /
0.604) — carried here because it varies by deck and two rungs cannot be compared without it.

**The limitation this rung inherits, restated rather than footnoted.** `W1Fly` exists to test **flying**, which
changes *which blocks are legal*. With joint attack and block uncloned (they fail the gate), **this rung cannot
measure that at all.** What it measures is whether the flyer's *presence* changes priority and target choice.

**Clones** (13b recipe, kinds `prio,target`): rung clone `bc_W1Fly.pt` best epoch **1** of 4, held CE 0.6239,
top-1 0.632 — it saturates at epoch 1 exactly as rung 0's did. Joint clone `bcj_W1Fly.pt` (W0Base + W1Fly, 2,000
games, 37,289 labelled consults) best epoch **5** of 8, held CE 0.3723, top-1 0.791, class 0.910, type 0.952.

**Evaluation** on W1Fly's own held-out games: 100 games, 2,746 scored consults, **aspect 1,663 / shared 1,083**
(aspect = Leonin Skyhunter in hand, on either battlefield, or a candidate referent). Trivial predictor:
**aspect 0.6356 exact / 0.6909 class**, **shared 0.5753 exact / 0.7073 class**.

| model | pop | kind | n | exact top-1 | ceiling | frac | **class top-1** | **type** |
|---|---|---|---|---|---|---|---|---|
| ZERO (rung-0 clone) | aspect | priority | 1,048 | 0.6489 | 0.8836 | 0.734 | 0.7252 | 0.9017 |
| RUNG (W1Fly clone) | aspect | priority | 1,048 | **0.6489** | 0.8836 | **0.734** | 0.7252 | 0.9017 |
| JOINT (both decks) | aspect | priority | 1,048 | **0.8006** | 0.8836 | **0.906** | 0.9074 | 0.9427 |
| ZERO | shared | priority | 677 | 0.5775 | 0.8139 | 0.710 | 0.7046 | 0.8685 |
| RUNG | shared | priority | 677 | **0.5775** | 0.8139 | **0.710** | 0.7046 | 0.8685 |
| JOINT | shared | priority | 677 | **0.7341** | 0.8139 | **0.902** | 0.9069 | 0.9513 |
| all three | either | target | 51 | 1.0000 | 1.0000 | 1.000 | 1.0000 | 1.0000 |

**ZERO and RUNG are the same numbers to four decimals in every cell but one** (aspect all-kinds 0.5574 vs
0.5562). They are different checkpoints — different files, different held-out CE (0.5758 vs 0.6239) — trained on
**different decks**, and they make the same predictions here. Both have collapsed to the same positional policy.

**Readings, as pre-registered.**
* **"The aspect is learnable at all": NOT MET — and this is the reading that governs the rung.** The
  rung-specific clone reaches **0.734** of its aspect copy ceiling on priority (0.600 on all kinds), against a bar
  of **0.80**. A4L states that a rung failing this clause "says the aspect is not learnable from CP7 labels by
  this network — a stronger finding than a transfer failure, and it makes that rung's transfer reading **void**."
  **Rung 1a's transfer reading is therefore void**, and the two clauses below are recorded only for completeness.
* **"The shared game transfers": met by the letter, and empty.** Zero-shot shared priority 0.5775 against the
  rung clone's 0.5775 is a ratio of **1.000** (bar 0.95). But the two models are the same policy, and neither
  beats the trivial predictor: on exact index they sit at it (shared all-kinds 0.5762 vs trivial 0.5753), and on
  **class agreement they are BELOW it** (0.6556 vs 0.7073; priority 0.7046 vs 0.7400). This is exactly the
  degenerate case the A4L preamble was amended to warn about — the clause is satisfied by two near-trivial models,
  so it measures the decks' shared positional regularity, not a shared game. **This reading rests on exact
  top-1; on class agreement it would fail, and that is stated rather than resolved.**
* **"The aspect does not transfer": NOT met.** Zero-shot aspect exact top-1 (0.5574 all, 0.6489 priority) is not
  ≥ 0.10 below its own shared figure — on priority it is *higher* (0.6489 vs 0.5775).

**"Joint helps", and it is the most informative number here.** Training on both decks nearly **doubles the gap to
the ceiling**: aspect priority 0.8006 (0.906 of ceiling) against the rung clone's 0.6489 (0.734); shared priority
0.7341 (0.902) against 0.5775 (0.710); class agreement 0.907 against 0.725. **The joint clone clears the very
learnability bar the rung clone fails.** The difference between them is not architecture, seed or deck — it is
**1,000 games versus 2,000**.

**Operational consequence, and the most useful thing this rung produced.** A per-rung recording of 1,000 games
does not train a clone that can serve as the "rung-specific" comparand A4L's design requires: at that volume the
clone collapses to a positional rule and fails the learnability clause. This is the ladder meeting **A1's
data-limited finding** from the other side — A1 showed held-out top-1 still rising at 1,125 games on BenchDimir,
and here 1,000 games is visibly not enough. Later rungs are run unchanged (the volume is pre-registered and is not
being altered mid-ladder), but every rung's learnability clause should be expected to fail for the same reason,
and the JOINT column is the one to read.

**Cannots.** Target is 51 held consults and is 1.0000 for every model — it carries nothing. Attack and block are
uncloned, so nothing here touches flying's actual effect on legal blocks. One seed per clone. Top-1 against copy
ceilings is not a win rate. The aspect/shared split is by card presence, not by whether the decision turned on the
aspect.

**Rung 1a amendment — why ZERO and RUNG are identical, and what the JOINT gap actually contrasts.**

SANITY NOTE, checked rather than assumed, because an unexplained identical pair reads as a bug: ZERO and RUNG score identically on aspect priority (both 0.6489 at n=1,048) and on aspect blocks (both 0.5464 at n=291), differing only on attacks (0.2716 vs 0.2654). They are DIFFERENT checkpoints - md5 8f990d59 for bc_W0Base.pt against 70a5c2bf for bc_W1Fly.pt - and bc_W1Fly own held-out priority (0.621 at n=1,725) matches ZERO all-population priority (0.6209) almost exactly. The two clones genuinely behave the same; this is not one file loaded twice. The finding is stronger than the coincidence: training a clone ON the flying deck yields essentially the same priority behaviour as a clone trained without that deck at all.

TRAINING SIZES AND EPOCHS, so the JOINT-vs-RUNG gap is legible as what it is: RUNG = 1,000 games, 17,625 labelled consults, best epoch 1 of 4. JOINT = 2,000 games, 37,289 labelled consults, best epoch 5 of 8. JOINT differs on TWO axes at once - twice the data and five times the epochs before its best - so the gap cannot be read as a deck effect.

AND THE SINGLE-DECK RUNS DID NOT MERELY STOP EARLY - THEY STOPPED MOVING. Per-epoch traces show TRAIN cross-entropy frozen to four decimals from epoch 2 (W1Fly 0.6174, 0.6167, 0.6167, 0.6167; W0Base 0.5572, 0.5535, 0.5535, 0.5535), with held-out CE, top-1, class and type identical across every epoch. That is not an early-stopping rule latching onto a small noisy hold-out: it is optimisation stalling, and MORE PATIENCE CANNOT HELP a loss that is not changing. The joint clone, same recipe, trains normally for eight epochs (train CE 0.4982 to 0.3850, held CE 0.4576 to 0.3723).

HYPOTHESIS, stated as such and not tested here: the heads apply logits = B*tanh(logits/B) with B = 5, the lane logit bound inherited from 13b. A network that saturates that bound has vanishing gradients, which would freeze training exactly as observed, and the smallest, easiest single-deck set saturates fastest. The OWED diagnostic is therefore not more patience but a re-clone with the bound relaxed (--logit-bound 0) or a lower learning rate, reported beside the patience-3 number as a diagnostic and never as a new bar.

WHAT THIS DOES TO THE VERDICT, in the verdict own paragraph rather than below it: the pre-registered clause reads NOT MET on RUNG and that remains the reading of record - but it must be read as "the aspect is not learnable FROM 1,000 GAMES OF THIS DECK BY THIS RECIPE, in a run whose optimisation stalled after one epoch", NOT as evidence that the network cannot represent flying. JOINT reaches 0.8006 on the same 1,048 aspect priority consults (0.906 of ceiling) where RUNG reaches 0.6489 (0.734), and A1 independently reads DATA-LIMITED on this axis (+0.0118 top-1 on its last doubling, still rising at 1,125 games). If the pattern RUNG == ZERO with JOINT much higher repeats on rungs 1b, 1c and 1d, the ladder-level reading will say ONCE that A4L as instantiated measured data volume and an optimisation stall more than aspect transfer - which would be the phase most useful conclusion about the design itself.

**Saturation diagnostic — the stall mechanism, measured (, one forward pass, trains nothing; a DIAGNOSTIC, never a bar).**

The heads apply logits = B*tanh(raw/B) with B = 5. Setting logit_bound = 0 on a loaded checkpoint returns the RAW pre-tanh values, so no model source is touched. Over 1,800 held-out W0Base consults (8,821 real candidate logits):

| checkpoint | mean abs raw | max | share >= 5 | share >= 10 | share >= 20 | train CE trace |
|---|---|---|---|---|---|---|
| bc_W0Base.pt (best epoch 1, FROZEN) | **54.45** | 82.9 | 1.0000 | 1.0000 | **0.9509** | frozen from epoch 2 |
| bcj_W1Fly.pt (best epoch 5, healthy) | **21.30** | 94.2 | 0.9777 | 0.8799 | **0.4636** | improving to epoch 8 |

Top-logit only (the one the argmax rides on): 67.8 mean for the frozen clone against 26.8 for the healthy one.

**Reading.** Both clones are saturated relative to the bound, but by very different margins, and the gradient through the tanh falls exponentially: at raw 54 the factor 1 - tanh^2(54/5) is about 1e-9, at raw 21 it is about 8e-4 - roughly six orders of magnitude. The frozen clone is gradient-dead; the healthy one is merely compressed. This supports the saturation hypothesis as the mechanism behind the A4L single-deck stall.

**And it is REGIME-DEPENDENT, which the free log evidence pins down.** Scanning every Phase 15 training log for a frozen train-CE trace (identical to four decimals over the last three epochs): A0 (2,000 consults, 40 epochs, no early stop, weight decay 0) fell 0.7349 to 0.0565 - NOT frozen; A1 policy fractions 0.6332 to 0.2391 - not frozen; A2 card-blind floor clone 0.5013 to 0.3155 - not frozen; A3 auxiliary-loss clone 0.4628 to 0.2290 - not frozen; the A4L JOINT clone 0.4982 to 0.3850 - not frozen. **Only the two single-deck rung clones froze** (W0Base 0.5535 x3, W1Fly 0.6167 x3). So B = 5 does not freeze training unconditionally - the same bound trained fine on 2,000 consults, on 68,500, and on 37,289. It is the ~17,600-consult single-deck regime that stalls.

**What this implies beyond A4L, stated as a candidate and not a demonstration.** Every clone in this project is trained with this bound, so all of them are compressed to some degree, and the degree is measurable. It is a candidate explanation for 13c tiny per-update KL (about 0.0012 against a 0.02 target), which has so far been attributed to the recipe: if a policy raw logits sit far outside the bound, the BOUNDED logits the update actually moves barely change, and the KL per update is small for a reason that has nothing to do with the learning rate. Testing that means measuring raw logits on 13c checkpoints, which is cheap but is not done here.

**OWED, deliberately not applied tonight:** a re-clone with the bound relaxed (--logit-bound 0) or a lower learning rate, reported beside the patience-3 number. Changing the bound or the head parameterisation mid-ladder would make the rungs incomparable, so the ladder runs unchanged and the fix waits.

**Saturation, measured on all three frozen rung clones — a dose-response, not a single coincidence.**

| checkpoint | state | mean abs raw logit | max | share >= 20 | gradient factor 1-tanh^2(raw/B), B=5 |
|---|---|---|---|---|---|
| bcj_W1Fly.pt (joint, 2,000 games) | trained 8 epochs | **21.3** | 94.2 | 0.4636 | ~8e-4 |
| bc_W0Base.pt | FROZEN at epoch 1 | **54.4** | 82.9 | 0.9509 | ~1e-9 |
| bc_W1Fst.pt | FROZEN at epoch 1 | **90.8** | 155.3 | 0.9905 | ~1e-16 |
| bc_W1Fly.pt | FROZEN at epoch 1 | **109.9** | 157.1 | **1.0000** | ~1e-19 |

Top-logit-only means run higher still (67.8 / 116.3 / 132.9 for the three frozen clones against 26.8 for the joint one). Every single-deck rung clone measured is beyond the bound on 100 percent of its candidate logits, and the three that froze are 2.5x to 5x deeper into saturation than the one that trained normally. The gradient through the tanh dies exponentially in raw/B, so this is a dose-response relationship between saturation depth and the stall, measured on three independent checkpoints rather than inferred from one.

This does not change any pre-registered reading. It sharpens the mechanism: the A4L single-deck regime drives raw logits an order of magnitude past B = 5 within one epoch, after which the head is gradient-dead and training stops even though the loss is far from its floor. The fix remains OWED and unapplied so the rungs stay comparable.

**Saturation across five checkpoints — it is the stall, not the data volume.**

Rung 2 joint clone froze exactly as its single-deck arms did (held CE 0.5862 identical epochs 1-4, train CE 0.5767 from epoch 2, best epoch 1 of 4), which rung 1 joint clone did not. Measuring both settles why:

| checkpoint | trained? | mean abs raw logit | max | share >= 20 |
|---|---|---|---|---|
| bcj_W1Fly.pt (joint, rung 1) | 8 epochs, CE 0.4982 -> 0.3850 | **17.2** | 58.8 | 0.3586 |
| bcj_W1Fst.pt (joint, rung 2) | FROZEN at epoch 1 | **93.0** | 182.8 | **1.0000** |
| bc_W0Base.pt | FROZEN at epoch 1 | 54.4 | 82.9 | 0.9509 |
| bc_W1Fst.pt | FROZEN at epoch 1 | 90.8 | 155.3 | 0.9905 |
| bc_W1Fly.pt | FROZEN at epoch 1 | 109.9 | 157.1 | 1.0000 |

**Every checkpoint that froze sits at mean abs raw logit 54 to 110; both that trained sit at 17 to 21.** The separation is clean across five independent runs and it cuts across the data-volume axis: the two JOINT arms have identical training-set sizes (2,000 games, ~38,000 labelled consults) and identical recipes, yet one trained for eight epochs at mean 17.2 and the other died at epoch 1 at mean 93.0.

**This revises the rung 1a conclusion, in the open.** Rung 1a attributed the JOINT-over-RUNG gap to data volume, supported by A1 reading data-limited. That attribution is now too simple: rung 2 joint arm has the same doubled data and does NOT escape. What separates the runs is whether they escaped saturation, which the doubled, more varied data made more likely on rung 1 but did not guarantee. The honest statement is that **the A4L arms are measuring the interaction of the logit bound with this training regime at least as much as they measure transfer**, and a rung whose arms all froze cannot speak about its aspect at all.

**The OWED --logit-bound 0 re-clone is now the load-bearing diagnostic of this phase**, because it decides whether any A4L arm measured the network rather than the bound. It is still not run tonight: changing the bound mid-ladder would make the rungs incomparable, and the ladder is mid-flight.

### 15 / A4L rung 1b — W1Fst (Head of Security, first strike): ALL THREE ARMS FROZE AND COINCIDE; the rung cannot speak about its aspect

**Recording**: 1,000 games, 30,142 labelled consults. **Gate** (own, full recording): priority 18,647/18,647 = 1.000 pass, target 600/600 = 1.000 pass, joint attack 6,035/10,235 = **0.590** FAIL, joint block 4,860/8,695 = **0.559** FAIL. **CombatMath coverage for this deck: 0.590 / 0.559** - the worst of the three recorded so far (W0Base 0.598/0.604, W1Fly 0.641/0.645).

**The limitation restated, not footnoted:** W1Fst exists to test FIRST STRIKE, which changes the MATH OF A TRADE. With joint attack and block uncloned, this rung cannot measure that at all; it measures only whether the presence of Head of Security shifts priority and target choice.

**Clones - all three froze.** Rung clone bc_W1Fst.pt: best epoch 1 of 4, held CE 0.5823 identical across epochs 1-4, train CE 0.5623 from epoch 2. Joint clone bcj_W1Fst.pt (2,000 games, 38,911 labelled): best epoch 1 of 4, held CE 0.5862 identical across epochs 1-4, train CE 0.5767 from epoch 2 - and it ROSE from 0.5655. Raw-logit saturation: rung clone mean abs 90.8, joint clone 93.0, both with 99-100 percent of logits beyond +/-20.

**Evaluation** on W1Fst held-out games: 100 games, 2,793 consults, aspect 2,122 / shared 671. Trivial predictor: aspect **0.6013 exact / 0.6616 class**, shared **0.6066 exact / 0.7765 class**.

| model | pop | kind | n | exact top-1 | ceiling | frac | class top-1 | type |
|---|---|---|---|---|---|---|---|---|
| ZERO | aspect | priority | 1,353 | 0.6814 | 0.8891 | 0.766 | 0.7568 | 0.9047 |
| RUNG | aspect | priority | 1,353 | **0.6814** | 0.8891 | **0.766** | 0.7568 | 0.9047 |
| JOINT | aspect | priority | 1,353 | **0.6814** | 0.8891 | **0.766** | 0.7568 | 0.9047 |
| ZERO / RUNG / JOINT | shared | priority | 422 | **0.5687** | 0.7725 | 0.736 | 0.7417 | 0.8768 |
| ZERO / RUNG / JOINT | shared | target | 54 | 0.9444 | 1.0000 | 0.944 | 0.9444 | 1.0000 |
| ZERO / RUNG / JOINT | aspect | target | 6 | 0.0000 | 0.6667 | 0.000 | 0.0000 | 1.0000 |

**All three arms coincide to four decimals on priority and on every shared cell.** A clone trained on W0Base, a clone trained on W1Fst, and a clone trained on both make the same predictions. They differ only in the third decimal of the aspect all-kinds figure (0.5551 / 0.5509 / 0.5556), which is carried by untrained attack and block heads.

**Readings, as pre-registered.**
* **"The aspect is learnable at all": NOT MET.** The rung clone reaches 0.766 of its aspect ceiling on priority (0.593 all kinds) against a 0.80 bar. By A4L own rule this VOIDS the rung transfer reading.
* **"The shared game transfers": met by the letter and empty**, for the second rung running - zero-shot shared priority 0.5687 against the rung clone 0.5687 is a ratio of exactly 1.000, because they are the same policy. On exact index the arms sit BELOW the shared trivial predictor (0.6095 all-kinds against 0.6066 is +0.003; priority 0.5687 against a 0.5142 positional rule is above, but class agreement 0.7417 is below the trivial class figure 0.7844).
* **"The aspect does not transfer": NOT met** - zero-shot aspect priority (0.6814) is higher than its shared counterpart (0.5687), not 0.10 below.
* **"Joint helps": NO, and this is the new fact.** On rung 1a the joint arm was far stronger; here it is IDENTICAL to both single-deck arms, and its aspect exact top-1 (0.5556) is BELOW the aspect trivial predictor (0.6013) with class agreement (0.6037) below trivial class (0.6616). The joint arm froze at epoch 1 at mean abs raw logit 93.0.

**What this rung establishes.** Nothing about first strike - it could not, with combat uncloned. What it establishes is about the LADDER: when every arm saturates and freezes at epoch 1, all three collapse onto the same near-trivial policy and the pre-registered clauses become arithmetic on identical numbers. A rung in that state cannot speak about its aspect, and reporting its transfer clauses as if it could would be the artefact the preamble was amended to guard against.

**Cannots.** Aspect target is 6 consults and shared target 54 - both carry nothing. Attack and block are uncloned. One seed per arm. Top-1 against copy ceilings is not a win rate. And for this rung specifically: with all arms frozen and coincident, NO comparison between arms is informative, including the ones that formally pass.

**Rung 1b amendment — the clauses above are NOT INTERPRETABLE for this rung.**

Stated plainly, because reporting them as outcomes would imply they measured something. On this rung every arm is a gradient-dead model:

| arm | best epoch | held CE trace | mean abs raw logit | share >= 20 |
|---|---|---|---|---|
| ZERO (bc_W0Base.pt) | 1 of 4 | flat from epoch 1 | 54.4 | 0.9509 |
| RUNG (bc_W1Fst.pt, md5 54fce56f) | 1 of 4 | flat from epoch 1 | 90.8 | 0.9905 |
| JOINT (bcj_W1Fst.pt, md5 ee115349) | 1 of 4 | flat from epoch 1, train CE ROSE | 93.0 | 1.0000 |

The three are distinct files that converge on the same near-trivial policy, identical to four decimals on priority and on every shared cell. **Therefore: "aspect is learnable at all", "the shared game transfers", "the aspect does not transfer" and "joint helps" are all NOT INTERPRETABLE here.** They are recorded above because they were pre-registered and the arithmetic is what it is, but not one of them measures the aspect, transfer, or the network - each is a comparison between frozen models. Rung 1b measures the FREEZE.

For contrast, rung 1a's joint arm trained normally (best epoch 5, mean abs raw logit 17.2), which is why its JOINT column carried information and this one does not. That difference is the pathology, not the decks.

### 15 / D — the logit bound was freezing training: relaxing it is worth +0.14 held-out top-1 on the same data

The owed diagnostic, run on W1Fly because that rung already had a healthy comparison on record.  with **--logit-bound 0** and nothing else changed: same init (), same seed 0, same 10 % game hold-out, same kinds prio,target, same lr / batch / patience, same 1,000-game recording.

| | bounded (B = 5, the recipe of record) | **unbounded (B = 0)** |
|---|---|---|
| best epoch | **1** of 4 | **12** of 15 |
| held-out CE | 0.6239 | **0.4006** |
| held-out top-1 | 0.632 | **0.775** |
| held-out class top-1 | 0.725 | **0.916** |
| held-out type agreement | 0.892 | **0.951** |
| priority top-1 / class | 0.621 / - | **0.768 / 0.914** |
| train CE | frozen at 0.6167 from epoch 2 | 0.5488 -> 0.4018, still falling at stop |

**+0.143 held-out top-1 and +0.191 class agreement, from one flag.** The bounded run was not merely stopped early - at its best it was 0.14 worse than the same recipe unbounded, and it never moved after epoch 1 because its raw logits sat at mean |109.9| against a bound of 5, where the gradient through B*tanh(raw/B) is ~1e-19.

**What this means for the A4L ladder, and it is not a small correction.** Rungs 0, 1a and 1b were all trained under the bounded recipe, and five of the six clones in them froze. Their ZERO / RUNG / JOINT arms collapsed onto the same near-trivial policy, which is why every pre-registered clause on rung 1b came out as arithmetic on identical numbers. **The first series measured a training pathology, not transfer.**

**What is NOT changed, per the rule pre-registered before this diagnostic was read** (PHASE15-ARCH STATE, 07:23Z): every reading of record already committed for the first series - rungs 0, 1a, 1b and their clauses - **stands as written**. Nothing is re-scored or withdrawn. Any re-run at the relaxed bound is published as a clearly-labelled **second series** beside the first and the two are never pooled.

**Scope beyond A4L, stated as a candidate.** Every clone and every RL checkpoint in this project uses B = 5, including , the 13b clone that 13c trained from. If bc.pt is comparably saturated, then 13c per-update KL of ~0.0012 against a 0.02 target - so far attributed to the recipe - has a mechanical explanation: the bounded logits an update actually moves barely change when the raw logits are an order of magnitude past the bound. That check is cheap and is being run; it is a candidate explanation until it reports.

**Saturation on the published checkpoints — bc.pt is NOT the pathology, which narrows where it lives.**

| checkpoint | bound | mean abs raw logit | max | share >= 20 | gradient factor 1-tanh^2(raw/B) |
|---|---|---|---|---|---|
| **bc.pt (13b clone, best epoch 6 of 9)** | 5 | **7.57** | 26.4 | **0.0095** | ~0.15 - alive |
| bc_W1Fly_nobound.pt (unbounded, best epoch 12) | 0 | 10.16 | 49.2 | 0.1694 | n/a, no tanh |
| bc_W1Fly.pt (bounded twin, FROZEN epoch 1) | 5 | **108.0** | 156.6 | **1.0000** | ~1e-19 - dead |
| bc_W0Base.pt / bc_W1Fst.pt / bcj_W1Fst.pt (frozen) | 5 | 54.4 / 90.8 / 93.0 | 83-183 | 0.95-1.00 | 1e-9 to 1e-16 |
| bcj_W1Fly.pt (joint, trained 8 epochs) | 5 | 21.3 | 94.2 | 0.4636 | ~8e-4 |

**bc.pt sits at 7.6, not at 54-110.** The 13b clone - the one every Phase 13 RL run started from - is only mildly compressed, and its gradient factor of about 0.15 is consistent with the honest nine-epoch training its log shows. So the freeze is **not** a universal property of B = 5, and the published 13b row is not undermined by it.

Also worth stating: the UNBOUNDED clone's raw logits stay small (mean 10.2, max 49), so relaxing the bound did not merely lift a ceiling that the network then ran through - the bounded run's mean of 108 is the anomaly, not the unbounded run's 10.

**What remains open is the 13c RL checkpoints**, not bc.pt: PPO could have driven logits outward during training even from a healthy start. If ck_1024 / ck_2048 sit in the 54-110 band, that is a candidate mechanical explanation for 13c's approx_kl of ~0.0012 against a 0.02 target - a bounded policy whose raw logits are far outside the bound barely moves whatever the update asks for. That would mean 13c's policy could not move rather than chose not to, and the 13c verdict would need an amendment saying so. **The 13c verdict is NOT rewritten here**; this is recorded as a candidate pending the measurement.

**The 13c checkpoints no longer exist, so the 13c question is answered through its twin.**

rl/artifacts/v7/13/c/ retains only logs, levels, census lines and state.json - the .pt files were gitignored and not kept, so ck_1024 / ck_2048 cannot be measured and the 13c saturation question is **unanswerable from its own artifacts**. Recording that plainly rather than leaving a pending measurement that will never arrive.

The substitute is exact in the ways that matter: **rl/artifacts/v7/14/d2b/ck_{256,512,768,1024}.pt** were trained FROM bc.pt with the **Phase 13 recipe unchanged** - lr 3e-5, logit bound 5, --adv-norm batch, --target-kl 0.02 - for 1,024 episodes. Same start point, same recipe, same bound; the one difference is the opponent (CP7 skill 1 rather than skill 6). If PPO under this bound drives raw logits outward, that trajectory will show it.

**bc_aux.pt (A3's auxiliary-loss clone) measures mean abs raw logit 9.09, max 28.8, 7.4 percent beyond +/-20** - the same healthy band as bc.pt (7.57). So every PUBLISHED clone measured so far sits at 7-10, and only the bounded single-deck LADDER clones sit at 54-110. The pathology is specific to that regime, not to the bound as such.

**CORRECTION IN THE OPEN — the saturation explanation for 13c's tiny per-update KL is REFUTED, by the measurement I proposed for it.**

I proposed, in two committed rows, that 13c's approx_kl of ~0.0012 against a 0.02 target might be mechanical: a bounded policy whose raw logits sit far outside the bound barely moves. Measured on the twin run (Phase 14 D2b: same start bc.pt, same Phase 13 recipe, same bound, 1,024 episodes), across 500 held consults of the 13a recordings:

| checkpoint | episodes | mean abs raw logit | max | share >= 20 |
|---|---|---|---|---|
| bc.pt (start) | 0 | 7.57 | 26.4 | 0.0095 |
| ck_256 | 256 | 7.24 | 31.8 | 0.0109 |
| ck_512 | 512 | 7.70 | 34.0 | 0.0136 |
| ck_768 | 768 | 7.86 | 32.1 | 0.0136 |
| ck_1024 | 1,024 | **8.09** | 34.1 | 0.0190 |

**PPO under this bound does not drive logits into saturation.** Over 1,024 episodes the mean moves +0.53 (about 7 percent) and the share beyond +/-20 goes from 1 percent to 2 percent - nothing like the 54-110 band of the frozen ladder clones. The candidate is **withdrawn**: 13c's small per-update KL is not explained by logit saturation, and the recipe-based account in the 13c row stands as written and is not amended.

**What survives, quantified rather than dropped.** At mean abs raw logit ~8 with B = 5, the gradient factor through B*tanh(raw/B) is about 0.15 - updates are compressed roughly 6.7x relative to an unbounded head. That is a real effect on every bounded run in this project and is worth knowing, but it is a constant-factor compression, not the exponential death (1e-9 to 1e-19) that froze the ladder clones. It does not explain a KL two orders of magnitude below target.

**The saturation finding therefore remains scoped exactly to the A4L single-deck ladder regime**, where it is decisive (+0.143 held-out top-1 from relaxing the bound), and does not reach the published Phase 13 rows.

### 15 / A4L rung 1c — W1Vig (Sun Sentinel, vigilance): the most degenerate rung; ALL THREE ARMS IDENTICAL IN EVERY CELL

**Recording**: 1,000 games, 31,121 labelled consults. **Gate** (own, full recording, run before the runner reached its gate step): priority 19,036/19,036 = 1.000 pass, target 569/569 = 1.000 pass, joint attack 6,279/10,290 = **0.610** FAIL, joint block 5,237/8,797 = **0.595** FAIL. **Coverage for this deck: 0.610 / 0.595.**

**The limitation restated:** W1Vig exists to test VIGILANCE, which removes the attack-vs-hold-back tradeoff. With joint attack and block uncloned, this rung cannot measure that at all.

**Clones - both froze.** Rung clone bc_W1Vig.pt: best epoch 1 of 4, held CE 0.5920 identical epochs 1-4, train CE pinned at 0.5498 from epoch 2. Joint clone bcj_W1Vig.pt (2,000 games): best epoch 1 of 4, held CE 0.5568 identical epochs 1-4, train CE pinned at 0.5544. That makes **six frozen clones of the seven trained across the four rungs** - only rung 1a's joint arm ever escaped.

**Evaluation**: 100 held-out games, 2,884 consults, aspect 1,736 / shared 1,148. Trivial predictor: aspect **0.6215 exact / 0.6774 class**, shared **0.6298 / 0.7125**.

| model | pop | kind | n | exact top-1 | ceiling | frac | class | type |
|---|---|---|---|---|---|---|---|---|
| ZERO = RUNG = JOINT | aspect | priority | 1,115 | **0.7085** | 0.8825 | 0.803 | 0.7955 | 0.9256 |
| ZERO = RUNG = JOINT | aspect | all | 1,736 | 0.5968 | 0.9240 | 0.646 | 0.6526 | 0.8548 |
| ZERO = RUNG = JOINT | shared | priority | 685 | 0.5971 | 0.8015 | 0.745 | 0.7358 | 0.8803 |
| ZERO = RUNG = JOINT | shared | all | 1,148 | 0.5897 | 0.8815 | 0.669 | 0.6725 | 0.8598 |
| ZERO = RUNG = JOINT | shared | target | 51 | 1.0000 | 1.0000 | 1.000 | 1.0000 | 1.0000 |

**Every arm is identical to four decimals in EVERY cell** - not merely on priority, as in rung 1b, but on aspect all-kinds too. Three clones trained on different data are one policy.

**And that policy IS the trivial rule.** Its aspect priority exact top-1 is **0.7085**, and the trivial pos-1 predictor on the same consults scores **0.7085** - equal to four decimals, exactly as rung 0's anchor did. On shared priority it is 0.5971 against the trivial 0.5971. The arms are not near-trivial; they ARE the positional rule.

**Readings: NOT INTERPRETABLE, all four.** Aspect-is-learnable would read 0.803 of aspect ceiling - nominally clearing 0.80 - but that number is produced by a frozen model that reproduces a fixed-position rule exactly, so recording it as a pass would be the artefact the preamble warns against. Shared-transfers, aspect-does-not-transfer and joint-helps are each comparisons between one policy and itself. **Rung 1c measures the freeze.**

**Cannots.** Aspect target is 5 consults. Attack and block uncloned. One seed per arm. Nothing here speaks about vigilance.
