# C0 results — the baseline, and what it kills

Phase C0 of `plan/nl-dsl-consistency.md`, complete. Instrumentation findings are in
`C0-findings.md`; this is the measurement.

**Run:** 150 compilations — 10 laddered intents × 5 paraphrase rungs × 3 samples.
LLM stage via in-session agents against the verbatim production system prompt
(`build_system_prompt`, 9,680 chars), the route both prior compiler rounds used.
Batches partitioned **by rung**, so no compiler instance ever saw two paraphrases of one
intent and could not trivially agree with itself. Index: Forge `7ba1a393`, 34,611 faces.

## Headline

| metric | value | predicted |
|---|---|---|
| **PC** (paraphrase consistency) | **0.509** | 0.6–0.75 ❌ |
| **PC_correct** | 0.492 | — |
| **agreement@witness** | 0.925 | — |
| **SC** (sampling consistency) | **0.784** | ~0.9 ❌ |
| foil rate | 0.008 | ~0 ✓ |
| compile failures | **0 / 150** | — |
| inverted disagreement (I26) | 0.400 | should be high ❌ |

Per-sample PC: 0.474 / 0.511 / 0.543 (spread 0.069) — the run-to-run spread of the
metric itself, useful for judging whether a future ΔPC is signal.

The recorded prediction was **wrong on both magnitudes** and right on direction: SC > PC,
variance concentrated in phrasing rather than sampling. Decomposed, phrasing accounts for
**58%** of the residual disagreement and resampling for 42%.

**Validity remains perfect: 0 compile failures in 150.** The ontology gate has still never
fired. Everything below is a semantic failure inside a well-formed query — which is the
premise the whole plan was built on, now confirmed at 3× the previous sample size.

## C1 (execution consensus) — KILLED on its own pre-committed rule

C1's rule: *adopt if `PC_correct` improves ≥5 points at ≤3× compile cost **and** the
disagreement score separates the H09 ambiguity stratum.* Both halves measured directly
against this data:

**(a) Consensus gain — fails.**

| metric | k=1 (mean of 3) | k=3 modal | Δ |
|---|---|---|---|
| PC | 0.509 | 0.509 | −0.000 |
| PC_correct | 0.488 | 0.492 | **+0.004** |
| agreement@witness | 0.925 | 0.925 | +0.000 |

**+0.4 points against a 5-point bar.** Modal consensus over three samples buys essentially
nothing, for 3× the cost. The reason is visible in the numbers: within a rung the three
samples frequently produce three *distinct* result sets, so the "mode" is a 1/1/1 tie
broken arbitrarily. Consensus needs its samples to cluster, and they do not.

**(b) Ambiguity separation — fails, and inverts.**

I26 ("cards that exile things", four legitimate readings) ranks **8th of 10** by
disagreement at 0.400, *below* the headline mean of 0.578:

```
1. I22  0.933      6. I08  0.600
2. I10  0.867      7. I12  0.400
3. I18  0.733      8. I26  0.400  <- the ambiguous one
4. I11  0.667      9. I04  0.267
5. I40  0.667     10. I36  0.067
```

Six well-specified intents disagree *more* than the four-way-ambiguous one. The
disagreement signal is not merely uninformative about ambiguity — it points the wrong way.
Shipping it as a confidence indicator would tell users we are least sure exactly when we
are most nearly right.

**Verdict: do not build C1 as specified.** Per its kill criterion, keep k=1 and lean on C2.

One thing this does *not* kill: consensus over *self-generated paraphrases* of the user's
question (compile several rewordings, cluster those). That attacks the 58% share rather
than the 42% share, and is untested. It is a new proposal, not a rescue of C1.

## C3 (ontology-slice retrieval) — direct hit

The strongest single result of the run. All five rungs compiled "damage to each opponent"
with param `ValidPlayer`. `DamageAll` uses `ValidPlayers`. Both are real ontology tokens:

| token | freq | rank of 1,206 | in prompt? |
|---|---|---|---|
| `ValidPlayer` | 3,130 | 25 | **yes** |
| `ValidPlayers` | 163 | **159** | **no** |

`build_system_prompt` emits `param_keys[:100]`. **The correct token is past the cutoff and
was never in the prompt.** The frequency-sorted list put a plausible wrong answer at rank
25 and hid the right one. The compiled query validates clean and returns **0 hits** — a
silent wrong answer, caused by the prompt's truncation.

This is C3's predicted failure mode with a reproduction, and it generalises: 1,106 of
1,206 param keys are invisible to the compiler on every question.

## What the strata say

| id | H | PC | SC | note |
|---|---|---|---|---|
| I10 | H00 | 0.197 | 0.617 | worst PC in the set, on a *plain* intent |
| I11 | H02 | 0.271 | **0.557** | lowest SC — flagship encoding coin-flip is unstable run-to-run |
| I18 | H05 | 0.307 | 0.926 | largest gap (+0.619), but blocked by the `role` bug — measures a fallback |
| I22 | H06 | 0.403 | 0.616 | timing-as-card-type; also the only foil leak |
| I40 | H02 | 0.458 | 0.689 | three-encoding family |
| I08 | H03 | 0.560 | 0.953 | |
| I12 | H02 | 0.640 | 0.958 | |
| I04 | H01 | 0.573 | 0.778 | `Cost` regex is comparatively stable |
| I26 | H09 | **0.933** | 0.867 | ⟲ most consistent row in the set — the exact inverse of correct |
| I36 | H12 | 0.600 | 0.800 | reclassify: not a false premise (see findings §4) |

Two readings worth stating plainly:

- **High recall, low consistency.** agreement@witness 0.925 against PC 0.509: the compiler
  reliably finds the witness while returning very different sets around it. Users would see
  the card they were thinking of every time, and a different supporting cast every time.
- **R2 was load-bearing.** `PC_correct` (0.492) sits *below* `PC` (0.509) here, so the
  guard is not decorative in the smoke-test sense — but the sample-0 slice showed the
  textbook case (`PC_correct` 1.0 at agreement 0.467). Never ship one without the other.

## Revised phase ordering

| phase | was | now | why |
|---|---|---|---|
| C3 idiom lexicon + slice retrieval | 4th | **1st** | the only measured root cause; `ValidPlayers` reproduces it |
| C2 frozen-query cache | 3rd | 2nd | untouched by this run; still the only literal-determinism lever, and now the fallback C1 was supposed to make unnecessary |
| fix `hook`/`role` in `QUERY_OPS` | — | **prerequisite** | 2 of 40 intents unscoreable; the S9 control cannot be measured until it lands |
| C4 exemplar bank | 5th | 3rd | unchanged in kind; benefits from C3's lexicon |
| C1 execution consensus | 2nd | **dropped** | failed both halves of its rule |
| C6 skeleton/slot | conditional | **triggered** | C0 was to trigger it only if variance were structural. I10 at PC 0.197 with rung sizes 0–154 is structural, not token-level |
| C5 corpus synthesis | the bet | unchanged | |

## Caveats on this run

- **10 intents, not 40.** Only the laddered subset was scoreable. Strata are n=1 to n=3;
  the per-hazard numbers are directional, not estimates.
- **Batched compilation.** Each agent compiled 10 questions in one context, where
  production does one call per question. Questions were mechanically distinct, but this is
  a deviation from the production contract and plausibly *inflates* consistency.
- **No retry loop.** Production retries on validation error; with 0 failures in 150 it
  would never have fired here.
- **Agents are not the API compiler.** Same prompt, same vocabulary, same output contract,
  different harness. Treat absolute values as indicative and Δ-values across arms as the
  real currency.
- **Not frozen.** R6 freeze still pending the remaining 30 ladders, so these are `v1-draft`
  numbers and a v2 re-hash is expected.
