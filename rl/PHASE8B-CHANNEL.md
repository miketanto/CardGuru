# Phase 8b — is the card channel load-bearing, and can deck diversity make it compositional?

Follow-up to `rl/PHASE8-TRANSFER.md`, which found (a) perfect zero-shot
transfer on 12-card feature-matched swaps, (b) an encoding-independent
drop on a full-archetype rebuild, and concluded the policies' competence
rides mostly on structural features. Phase 8b tests that conclusion
directly and then attacks the transfer lever it implies.

## Step 1 — feature-scramble diagnostic (the conclusion was wrong)

attn_desp evaluated on its own training deck (BenchDimir, 200g, seed
970000) with its feature file corrupted at eval time
(`rl/p8b_scramble.py`):

| features | vs D0 | vs D1 |
|---|---|---|
| normal (baseline) | .640 | .445 |
| scrambled (derangement over all 35,390 rows) | **.260** | **.100** |
| zeroed (every card = unknown vector) | **.345** | **.240** |

The card channel is **massively load-bearing** — scrambling it drops
the policy 38 points below its baseline and far below the D0-mirror
floor (.386). Phase 8's "structural channel carries everything"
inference is dead: the net reads card features intensely.

The reconciliation with Phase 8's data is that the net appears to use
feature vectors as **local identifiers, not compositional semantics**:

- near-identical vectors (12-card swaps at d=0–4) → same treatment →
  perfect transfer;
- a fully novel archetype → unfamiliar vector *combinations* → the
  e0-equal drop;
- scrambled vectors → identifiers broken → collapse;
- zeroed beats scrambled (.345 > .260): a consistent "unknown" is less
  damaging than 60 *wrong* identities.

## Step 2 — deck-randomized fine-tune (overnight, negative)

If the features are read as identifiers because one training deck lets
structure be memorized, training where every episode uses a different
deck should force compositional use — and the E0 control cannot follow
(unseen names are arbitrary buckets). Three lanes, self-play league,
lr 1e-4, 64-ep chunks, probes every 256 eps (100g, seed 950000):

- **attn s0**: attn_desp on 24 generated BenchDimir variants
  (`rl/p8b_pool.py`, 8–14 copies swapped each, eval decks + their
  replacement cards held out);
- **e0 s0**: e0_champ, identical regimen (control);
- **attn s1 (user-directed)**: pool extended with six pin-era Standard
  meta approximations (`rl/p8b_meta.py`: mono-red mice, boros aggro,
  golgari midrange, dimir bounce, domain-lite, azorius tempo; the live
  Aug-2026 meta post-dates the engine pin and deck sites are
  egress-blocked, so these are late-2025 reconstructions); odd chunks
  play vs **D0-piloted** meta mirrors, even chunks self-play on the
  variant pool.

Curves (`rl/p8b_logs/`), ~2,000–2,560 eps per lane over ~7h (one
container restart survived; lanes resume from `trained.txt`):

| lane | bench D1 t=0 → trough → last | faeries D0 t=0 → last |
|---|---|---|
| attn s0 | .48 → .23 (768) → .40 (1792) | .47 → .43 |
| attn s1 meta | .48 → .21 (1536) → .34 (1792) | .47 → .45 |
| e0 s0 | .59 → — → .48 (2560) | .50 → .50 |

Both attn lanes **destabilized immediately** (a ~15–25 point dip
within 256–768 eps) and only partially recovered; the e0 control was
flat for 1,792 eps before sagging. **No lane improved its transfer
probe.** The instability asymmetry is itself evidence for the
identifier story: randomized decks are a much larger input shift for a
feature-reading net than for a hash net, and on-policy fine-tuning
amplifies the damage (worse play → worse data).

### Final 200g re-eval (fine-tuned nets, same protocol as Phase 8)

| net | BenchDimir D0 (was) | BenchDimir D1 (was) | Faeries D0 (was) | Faeries D1 (was) |
|---|---|---|---|---|
| p8b_attn (s0 final) | REEVAL_ATTN_BD0 (.640) | REEVAL_ATTN_BD1 (.445) | REEVAL_ATTN_FD0 (.485) | REEVAL_ATTN_FD1 (.370) |
| p8b_attn_meta (s1 final) | REEVAL_META_BD0 (.640) | REEVAL_META_BD1 (.445) | REEVAL_META_FD0 (.485) | REEVAL_META_FD1 (.370) |
| p8b_e0 (control final) | REEVAL_E0_BD0 (.670) | REEVAL_E0_BD1 (.425) | REEVAL_E0_FD0 (.470) | REEVAL_E0_FD1 (.365) |

REEVAL_SUMMARY

## Verdict

1. **The card channel is load-bearing** (scramble: −.38 vs D0) — Phase
   8's structural-channel conclusion is overturned; the transfer null
   is re-explained as identifier-style feature use.
2. **~2k episodes of deck-randomized fine-tuning does not convert
   identifiers into compositional semantics** — it destabilizes the
   policy first, and neither the variant pool nor D0-piloted meta
   mirrors improved held-out-archetype transfer at this budget.
3. The meta-augmented lane was no better than the pure variant lane on
   transfer (and noisier vs D1) — opponent-deck diversity via D0
   pilots is not the missing ingredient either, at this scale.
4. Consistent with M3 (diversity from *scratch* produced the only
   E2-vs-E0 daylight ever), the surviving hypotheses for real
   transfer are: **train with deck diversity from initialization**
   (not as a fine-tune shock), lower-lr / longer-budget adaptation,
   and **condition-aware feature dims** — with the scramble result
   now guaranteeing the features are at least read.

## Reproduction

```
python3 rl/p8b_scramble.py                    # corrupted TSVs
P8_FEATS=/tmp/rl_p8b/e2_scrambled.tsv bash rl/p8_eval.sh ...
python3 rl/p8b_pool.py                        # 24 training variants
python3 rl/p8b_meta.py                        # 6 meta approximations
bash rl/p8b_lane.sh attn 0 9101 9102 <init> 4096
P8B_META_LIST=$(cat rl/p8b_meta/meta_list.txt) \
    bash rl/p8b_lane.sh attn 1 9121 9122 <init> 4096
```
