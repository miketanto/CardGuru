# C3 ablation — which fix actually moves consistency

Phase C3 of `plan/nl-dsl-consistency.md`, run against the C0 baseline
(`C0-results.md`). Two arms, identical questions, identical harness, one variable:
what vocabulary the prompt carries. Arms deliberately size-matched (~26k chars each)
so prompt *length* is controlled and only its *content* differs.

| arm | prompt vocabulary |
|---|---|
| baseline | `param_keys[:100]`, frequency-ranked — production today |
| **B** | all 1,206 param keys — *visibility* hypothesis |
| **C** | `param_keys[:100]` + mined per-API param table — *disambiguation* hypothesis |

200 compilations (2 arms × 10 intents × 5 rungs × 2 samples), plus the 150-compilation
C0 baseline.

## Result

| arm | PC | PC_correct | agreement@wit | SC | dead-branch |
|---|---|---|---|---|---|
| baseline | 0.445 | 0.464 | 0.912 | 0.766 | 5.4% |
| **B fullvocab** | **0.564** | **0.525** | 0.925 | 0.770 | 1.0% |
| C perapi | 0.440 | 0.453 | 0.912 | 0.790 | 0.8% |

**H02 stratum** (I11, I12, I40 — the target under R5):

| arm | H02 mean PC |
|---|---|
| baseline | 0.456 |
| **B fullvocab** | **0.599** (+0.143) |
| C perapi | 0.421 (−0.035) |

**R5 verdict: arm B ships, arm C does not.** C3's rule was "ships only if the H02
stratum improves." B improves it by 14 points; C slightly degrades it.

## The counter-intuitive part

Both arms fix the diagnosed bug *identically and completely*:

- **Token choice**, I11 `DamageAll` param: baseline **0/5** correct → **5/5** in *both* arms.
- **Dead-branch rate**: 5.4% → 1.0% (B) / 0.8% (C).

But only arm B moves consistency. Arm C fixes correctness and leaves PC flat, twice
independently (s0: +0.001; k=2: −0.005).

So **the token bug and the consistency problem are not the same problem.** Fixing which
param name gets emitted stops the silent-dead-branch failure but does not stop five
paraphrases from producing five different queries. This falsifies the sharpened
hypothesis I went in with — that targeted disambiguation would be the better lever.

A plausible mechanism, untested: arm C produced *more* leaf subqueries than either other
arm (119 vs 104 vs 111). The per-API table may be prompting richer, more elaborate
queries, adding structural variance that cancels the token-level gain. If so the fix is
a better-designed table, not a rejection of disambiguation — this ablation tested one
concrete table (7 keys per API, common keys filtered), not the idea.

## Per-intent

| id | H | baseline | B | C | B−base |
|---|---|---|---|---|---|
| I36 | H12 | 0.600 | 1.000 | 0.600 | **+0.400** |
| I11 | H02 | 0.271 | 0.507 | 0.292 | **+0.236** |
| I40 | H02 | 0.458 | 0.650 | 0.330 | **+0.192** |
| I08 | H03 | 0.560 | 0.720 | 0.640 | +0.159 |
| I10 | H00 | 0.197 | 0.311 | 0.223 | +0.114 |
| I26 | H09 ⟲ | 0.933 | 1.000 | 0.933 | +0.067 ⚠ |
| I04 | H01 | 0.573 | 0.633 | 0.530 | +0.060 |
| I18 | H05 | 0.307 | 0.315 | 0.302 | +0.008 |
| I12 | H02 | 0.640 | 0.640 | 0.640 | 0.000 |
| I22 | H06 | 0.403 | 0.297 | 0.401 | **−0.106** |

Arm B wins 8, ties 1, loses 1. Two rows need reading against their own scoring rule:

- **I26 (⚠, R3 inverted).** Arm B took the four-way-ambiguous intent from 0.933 to a
  *perfect* 1.000. Under R3 that is a regression: the system is now maximally confident
  about the question it should be least confident about. Arm B does nothing for
  ambiguity detection and marginally worsens it.
- **I22 is the only real loss.** Timing-as-card-type (`H06`) got worse with more
  vocabulary — plausibly because a longer param list offers more ways to *invent* a
  mechanical encoding of "instant speed" instead of reaching for the `card` operator.
  Worth watching; one row, so not yet a finding.

## The alternation is systematic, not a one-off

H02 was argued from four known failures and one measured pair. Probing the pool for other
`*All`-versus-singular families:

| concept | `*All` encoding | singular encoding | ∩ | Jaccard |
|---|---|---|---|---|
| damage to each opponent | `DamageAll` 60 | `DealDamage` 200 | 1 | 0.0039 |
| mass creature destruction | `DestroyAll` 336 | `Destroy`+`Defined` 189 | 5 | 0.0096 |
| mass graveyard return | `ChangeZoneAll` 69 | `ChangeZone` 792 | 2 | 0.0023 |
| counters on each creature | `PutCounterAll` 291 | `PutCounter` 3,136 | 32 | 0.0094 |

Four families, all **Jaccard < 0.01**. Picking the wrong side of an `*All` alternation
never degrades a result set — it replaces it. This is a pool-wide structural property of
the Forge ontology, and it is the single best argument for the C3 lexicon.

(`DiscardAll` does not exist — 0 faces — so "each player discards" is a different case
and a good negative control for a future round.)

## Shipped

`build_system_prompt` now emits the full parameter vocabulary by default
(`param_keys_n=None`), with the measurement recorded in its docstring. Prompt grows
9,680 → ~27,000 chars; it sits behind `cache_control: ephemeral`, so the marginal cost is
one cache write per window.

## What this does *not* settle

- **10 intents, strata n=1–3.** H02 is three rows. The 14-point stratum gain rests on
  I11 and I40; I12 was flat.
- **k=2 per arm.** The baseline's own per-sample PC spread is 0.069, so single-arm
  differences under ~0.07 are not separable. Arm B's +0.119 clears that; arm C's −0.005
  is indistinguishable from zero, which is itself the finding.
- **Batched compilation**, as in C0 — 10 questions per context vs one call per question
  in production.
- **PC 0.564 is still not good.** The best arm leaves nearly half the pairwise result-set
  overlap on the table. Vocabulary was one cause and is now largely addressed; the
  residual is structural, which is what C6 exists for.
