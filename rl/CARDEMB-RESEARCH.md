# Card embedder — what the literature says about our failures (2026-09-10)

*Written after seven versions (`V7-VALIDATION.md` §1d) and before v8. Every
next step below cites the work it comes from; nothing is a hunch.*

## 1. The problems we measured

| symptom | version | number |
|---|---|---|
| fine-tuned text view merges Spell Snare / Force Spike when the structure view cannot tell them apart | v1 | cos 0.957 |
| fused vector never trained; random mix of channels | v1–v5 | v5 struct mv-probe 0.997 vs fused 0.707 |
| hashed-tree GNN separates conditions but scatters mechanical twins | v5 | Requiting Hex / Cut Down rank 27,422 in the tree view |
| block-structured fused vector passes every content gate but seed-to-seed top-10 overlap is 0.369 (< 0.40) | v6 | text slice 0.238, tree slice 0.263, bag 0.647, printed 0.855 |
| decoding the frozen text embedding from a slice makes the slice the frozen embedding, which is too coarse | v7 | Snare/Spike rank 6 |

## 2. What is known

### 2a. Nearest-neighbour instability across seeds is universal

- Hellrich & Hahn (2016) first reported that word embeddings trained with
  identical settings and different seeds have substantially different
  nearest neighbours. Wendlandt, Kummerfeld & Mihalcea (NAACL 2018,
  [arXiv 1804.09692](https://arxiv.org/abs/1804.09692)) define stability
  exactly as our G3 does — overlap of the ten nearest neighbours across
  spaces — and find 70–80 % for frequent words, **below 40 % for rare
  ones**, rising with dimension and data size.
- Antoniak & Mimno (TACL 2018, [paper](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00008/43418))
  recommend **never relying on a single embedding model for distances;
  average over multiple runs**.
- May et al. (2020, [arXiv 2003.04983](https://arxiv.org/abs/2003.04983))
  measure downstream instability and find it falls log-linearly with
  embedding memory (dimension × precision): doubling dimension ≈ −1.2
  points; kNN overlap is a valid predictor of downstream instability.
- Moschella et al. (ICLR 2023 oral, [arXiv 2209.15430](https://arxiv.org/abs/2209.15430))
  show independently trained latent spaces differ mostly by a
  quasi-isometry and propose relative representations (cosines to a
  fixed anchor set) as an invariant coordinate system; even so, their
  kNN Jaccard between spaces is **0.34–0.41**.

Implication: 35k cards, most of them "rare" (one text each), in 128
dimensions, is exactly the regime where top-10 overlap of 0.40 is hard.
The gate stands as written, but the remedy the field uses is
**averaging aligned runs**, not another loss. A two-seed artifact
(orthogonal-Procrustes-aligned, averaged, re-normalised per slice) is
the literature's answer; G3 is then measured between two *independent*
two-seed artifacts (four seeds), which is stricter than what we ran.

### 2b. Fine-tuning a pretrained transformer is unstable, and the remedies are known

- Dodge et al. (2020) and Mosbach et al. (ICLR 2021,
  [arXiv 2006.04884](https://arxiv.org/abs/2006.04884)): instability is
  an optimisation problem (vanishing gradients), not forgetting; a small
  learning rate with bias-corrected Adam and **more iterations** removes
  most seed variance.
- "Measuring the Instability of Fine-Tuning" (2023,
  [arXiv 2302.07778](https://arxiv.org/abs/2302.07778)) measures
  *representational* instability (CKA, Procrustes distance across seeds)
  and finds **re-initialising the top layers** most effective, layer-wise
  learning-rate decay (LLRD) generally helpful, Mixout / weight decay to
  pretrained not.
- Kumar et al. (ICLR 2022, [arXiv 2202.10054](https://arxiv.org/abs/2202.10054)):
  full fine-tuning distorts pretrained features; linear-probe-then-
  fine-tune preserves them. Our relational distillation to the frozen
  encoder is a soft form of the same idea and is why v2+ kept Snare/Spike
  apart in the text view.
- Wortsman et al. (ICML 2022, [model soups](https://proceedings.mlr.press/v162/wortsman22a.html)):
  weights of models fine-tuned from the same initialisation can be
  averaged; the soup is more robust than any member.

Implication: the text slice (0.238) gets the recipe — lower text LR,
LLRD, longer schedule — and the artifact-level averaging above.

### 2c. Structure + text: serialise the structure into the transformer

- UniXcoder (ACL 2022, [arXiv 2203.03850](https://arxiv.org/abs/2203.03850))
  flattens the AST into a token sequence (`<node,left> … <node,right>`)
  and feeds *comment + flattened AST* to one encoder; contrastive
  positives come from dropout; the AST is used in pretraining and
  dropped at inference. GraphCodeBERT adds data-flow edges to attention.
  Ablation: AST gives +1.8 F1 on clone detection.
- MoleculeSTM (Nat. Mach. Intell. 2023, [arXiv 2212.10789](https://arxiv.org/abs/2212.10789)):
  two encoders (GIN graph, SciBERT text), InfoNCE / EBM-NCE, and
  **end-to-end fine-tuning of both encoders matters** ("substantial
  gains" over frozen encoders); property prediction by fine-tuning.
- Huynh et al. (WACV 2022, [false negative cancellation](https://arxiv.org/abs/2011.11765))
  and Khosla et al. (SupCon 2020): false negatives can be *eliminated*
  or *attracted*; attraction keyed on a coarse label is what merged
  Snare and Spike in v1, elimination is what v2+ does.
- Veit et al. (CVPR 2017, [Conditional Similarity Networks](https://arxiv.org/abs/1603.07810)):
  one embedding with disjoint subspaces for different notions of
  similarity, each trained by its own objective — the design our
  block-structured `e_card` (v6) converged on.

Implication: our tree GNN is a randomly initialised encoder over 16k
hashed buckets — the component the literature would not build. The
Forge script is *already* a serialisation of the tree
(`A:SP$ Counter | ValidTgts$ Card.cmcEQ2`). The grounded move is
UniXcoder's: **flatten the ability tree into tokens and read it with the
pretrained transformer**, sharing weights with the oracle-text view.
Conditions become literal tokens; no per-seed random table exists.

### 2d. Prior card-embedding work

- Bertram, Müller et al. (2024, [arXiv 2407.05879](https://arxiv.org/abs/2407.05879)),
  Magic drafting with generalised representations: sentence-transformer
  text embedding + hand features reach 33.6 % top-1 on unseen sets vs
  23.8 % random and 42.9 % with meta-statistics; the authors conclude
  models "use shallow features like colour" rather than rich semantics.
- Zuin et al. / card2vec (Hearthstone, MTG): embeddings from deck
  co-occurrence alone — our masked-card objective (1c) is that signal.
- ByteRL (Hearthstone, arXiv 2303.05197): card text through a language
  model plus attributes, consumed by the policy — the design we follow.

Implication: no prior card work gates on conditions or seed stability;
our G2/G3 are stricter than the field. Text embeddings alone are the
weak channel everywhere they were tried.

## 3. Decisions for v8, in order of evidence

1. **Structure view = the serialised ability script read by the shared
   pretrained encoder** (2c). Tree GNN retired. The 68-column readout
   and the 83 printed fields stay as explicit channels. Same InfoNCE
   (text ↔ script) with structure-identical cards masked (v2+), same
   relational distillation, same block-structured `e_card`
   (text 48 | script 32 | bag 16 | printed 32) with reconstruction
   targets on the script, bag and printed slices and relational
   anchoring on the text and script slices.
2. **Fine-tuning recipe for stability** (2b): text encoder LR 2e-5 with
   LLRD 0.85, 10 % warmup, 40 epochs.
3. **Artifact = average of two seeds after per-slice orthogonal
   Procrustes alignment** (2a). G3 is measured between two independent
   two-seed artifacts (seeds 0+1 vs 2+3). Gates otherwise unchanged.

Run plan (overnight, `rl/cardemb/sweep.sh`): (a) v6 recipe + step 2 +
step 3 only — isolates the stability remedies; (b) steps 1+2+3. Each
run writes gates, per-view and per-slice diagnostics to
`rl/artifacts/cardemb_sweep/RESULTS.md`; nothing is accepted by the
script — acceptance is a row in `V7-VALIDATION.md` written by a person.

What none of this can show: whether any of it helps the policy. That
is Phase 5.
