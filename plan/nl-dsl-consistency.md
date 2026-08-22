# Plan — NL→DSL consistency (search compiler hardening)

Scope: the `ask` path only — `cardguru/nl_compiler.py`, the vocabulary it is given, and
the loop around it. Not adjudication (Phase 2b has its own compiler and its own eval);
not the graph, the index, or the DSL semantics, all of which are proven.

Research basis: `research/nl-to-dsl-consistency.md`. Two findings drive the whole plan:

1. **Validity is already solved** (28/28 first-pass; the ontology gate has never fired).
   Every residual failure is a well-formed query that chose the wrong ontology token.
   So anything whose contribution is "guarantee well-formed output" is worth zero here.
2. **Consistency has never been measured.** Every number in the repo is single-sample,
   single-phrasing, witness pass/fail. We do not know the variance we are complaining
   about, and `DSL_SPEC` has grown a hand-written idiom line after every eval round with
   no drift check.

Consequence for sequencing: **measurement is Phase C0 and it is not optional.** Phases
C1–C7 each carry a pre-committed decision rule scored against C0's numbers, in the style
of `plan/eval.md` §D. Nothing here ships on vibes.

## Roadmap placement

This is Phase 1.4 hardening — it sits after the NL compiler exists (it does) and it
blocks nothing else. It runs parallel to the breadth surfaces. It shares no artifacts
with Phase 2b except the lesson; the held-out RulesGuru corpus stays unread throughout,
and the consistency intent set is a *new* frozen set, disjoint from every existing one.

## Pre-committed decision rules

Committed before C0 produces a single number, so that no phase can be justified after
the fact:

- **R1 — The headline metric is `PC` (paraphrase consistency): mean pairwise Jaccard of
  *result sets* across paraphrases of one intent.** Result sets, not query JSON:
  structurally different queries with identical hit sets *are* the same query, and
  optimising exact-match would push us toward the wrong invariance.
- **R2 — `PC` is never reported alone.** A compiler that always returns `{}` scores
  PC = 1.0. Every `PC` figure ships next to `agreement@witness`, and the gating variant
  is `PC_correct` (consistency measured only over paraphrases that found the witness).
- **R3 — Ambiguous intents are scored inverted.** On the labeled `H09` (underspecified)
  stratum, high consistency is a *failure*: the correct behaviour is detecting that the
  question has two readings. Those intents are excluded from headline `PC` and scored by
  whether the disagreement signal separates them from the rest.
- **R4 — Any change to `DSL_SPEC`, `EXAMPLES`, the vocabulary truncation, or the model
  requires a re-run and a `ΔPC` line in the commit message.** This is the drift check we
  currently do not have.
- **R5 — A phase ships only if it moves the stratum it was designed to move.**
  Ontology-slice retrieval is justified by the idiom-alternation stratum (`H02`), not by
  aggregate `PC`. A phase that improves the aggregate while flat on its target stratum
  is presumed to be noise or prompt-lottery, and does not ship.
- **R6 — The intent set is frozen and hashed before the first scoring run** (per
  `plan/eval.md` §B.2). Any later edit is a new benchmark version with its own numbers;
  old numbers are not carried forward.

## Phases

### C0 — Instrument and freeze *(days)*

Build the thing that makes every later claim checkable.

1. `eval/consistency/intents.json` — 40 intents × 5 paraphrases, stratified per
   `eval/consistency-set-outline.md`. **Review, then freeze and hash.**
2. `eval/consistency.py` — harness: for each paraphrase, compile *k* times, execute each
   compiled query against the index, record `(paraphrase, sample, DSL, result-set hash,
   hit count, witness found?, absent-foil returned?)`. Response caching so re-runs are
   free; prompt-cached system block so cost is bounded.
3. `eval/consistency/report.md` — baseline, stratified by every axis in the outline.

Metrics emitted: `PC`, `PC_correct`, `SC` (sampling consistency: same paraphrase, *k*
samples), `agreement@witness`, `modal-query rate` (fraction of compilations landing in
the largest result-set-equivalence cluster), `foil rate`, all sliced by DSL shape,
hazard class, and result-set size regime.

Cost: 40 × 5 × 3 = 600 compilations against a cached system prefix. Single-digit dollars.

**Kill criterion:** none — this is measurement. **Exit condition:** the numbers exist and
are committed.

**Recorded prediction** (from the research doc, so C0 can falsify it): `SC` ≈ 0.9,
`PC` ≈ 0.6–0.75, variance concentrated in token choice rather than query structure. If
`SC` also comes in low, C1 becomes urgent and C3 drops down the order.

### C1 — Execution consensus *(days)*

Sample *k*=3 at nonzero temperature, execute all (milliseconds over 34,519 faces),
cluster by result-set Jaccard, return the modal cluster's query, and **emit cluster
disagreement as a confidence signal** carried into the response tier label that
`plan/architecture.md` §2 already requires.

**Decision rule:** adopt if `PC_correct` improves ≥5 points at ≤3× compile cost **and**
the disagreement score separates the `H09` ambiguity stratum from the rest (R3).
**Kill:** gain <5 points → do not pay 3× per query; keep *k*=1 and lean on C2.

Also generalise the existing retry signal while here: today only `hits == 0` triggers a
retry. The full set is `hits == 0`, `hits > 5%` of the pool, and cross-sample
disagreement.

### C2 — Frozen-query cache *(days)*

Embed the question; on cosine similarity > τ to a **verified** prior question, reuse its
frozen DSL with no model call. The only lever here that yields literal determinism.

**Decision rule:** τ chosen on the `H10` (compositional novelty) and adversarial
near-miss pairs to hold false-hit rate <1% at a useful hit rate. Cache hits are labeled
in the response. Entries are frozen only after a verified witness.
**Kill:** no τ achieves that → ship exact-string-match caching only, which is still worth
having for the head of the distribution.

### C3 — Mined idiom lexicon + ontology-slice retrieval *(weeks)*

Replace the top-N vocabulary truncation and the hand-grown `DSL_SPEC` idiom lines with
retrieved, mined records: `{token, kind, freq, gloss, example_cards, confusable_with}`.
`cardguru/gaps.py` already signatures every card's structures over the closed ontology;
`cardguru/induction.py` already gates declarative concepts against examples and
counterexamples. Same machinery, new output.

Validation gate, before the lexicon is used: each gloss must **round-trip** — retrieving
on the gloss returns its own token in the top-*k*. Glosses that don't are rejected, not
patched.

**Decision rule (R5):** ships only if the `H02` idiom-alternation stratum improves.
**Kill:** if gold-token retrieval recall is *worse* than the current top-80 dump, the
truncation was never the bottleneck — revert, and move C6 up the order.

### C4 — Exemplar bank + retrieval *(weeks)*

Growing bank of `(question, validated DSL, hit count, verified?)` — C0–C3 produce these
as a side effect, as does every `ask` invocation. Embed the questions, retrieve top-*k*
at compile time in place of the six static `EXAMPLES`.

The consistency argument outranks the accuracy one: a bank is a memory, and a memory is
what makes a system converge on its own past answers.

**Decision rule:** ships if `PC_correct` improves without regression on `H10`
(novel compositions must not collapse onto the nearest exemplar).
**Kill:** `H10` regresses → the bank is over-anchoring; restrict retrieval to
high-similarity hits only, or fall back to static exemplars plus C3.

### C5 — Corpus synthesis, DSL→NL *(weeks; the strategic bet)*

Overnight → Genie → AutoQA, adapted. Enumerate DSL queries from `gaps.py` structural
signatures (real mechanics, not the combinatorial cross-product), render canonical
utterances, LLM-paraphrase, and filter each paraphrase by **result-set round-trip
equality** — a stronger and cheaper filter than AutoQA's parser round-trip, available to
us because our queries execute in milliseconds. Drop queries with 0 hits (vacuous) or
~pool-size hits (trivial).

Yields, from one artifact: the C4 retrieval bank at scale, the C7 training set, a much
larger consistency test set, and a gap detector (DSL structures no paraphraser can
phrase naturally are structures no user will ask for).

**Decision rule — register check, run *before* any downstream use:** a classifier trained
to separate synthetic questions from the held-out real ones (`eval/nl_questions_*.json`,
which stay out of synthesis) must be near chance, **and** retrieval from the synthetic
bank must improve `PC_correct` on the *real* intent set.
**Kill:** register check fails → the corpus is a distribution mismatch dressed as data.
Use it for coverage analysis only and do not proceed to C7.

### C6 — Skeleton/slot decomposition *(weeks; conditional)*

RESDSQL's decoupling, applied to our DSL: predict the query *shape* first (`node` vs
`chain` vs `chain`-with-list vs `all`/`any`/`not` composition — a dozen low-entropy
options), then fill api/mode/param slots from the C3 retrieved slice. One-shot generation
of the whole nested JSON couples a stable decision to an unstable one.

**Trigger:** C0 shows variance in query *structure*, not just token choice (i.e. the
recorded prediction was wrong). If variance is token-only, C3 already covers it and this
phase is skipped.

### C7 — Distil a small parser *(long; conditional)*

Fine-tune a small seq2seq on C5's corpus plus the C4 verified bank. The argument is
determinism, not accuracy: temperature 0, no prompt, therefore no prompt-drift variance;
ontology baked into the output vocabulary; reproducible weights; ~free per query. AutoQA
landed within 6.4 points of human-annotated training using synthetic data alone.

Route to it only where it agrees with the LLM compiler on held-out data; LLM keeps the
tail. **Gated on:** C5 passing its register check **and** C0/C4 showing residual variance
large enough to be worth the weight.

## Sequence and cost

| Phase | Effort | Depends on | Target stratum | Ships if |
|---|---|---|---|---|
| C0 instrument + freeze | S (days) | — | all | always — it is the measurement |
| C1 execution consensus | S (days) | C0 | `H09`, `SC` | ≥5 pt `PC_correct`, ambiguity separated |
| C2 frozen-query cache | S (days) | C0 | head of distribution | false-hit <1% at useful hit rate |
| C3 idiom lexicon + slice retrieval | M (weeks) | C0 | `H02` | `H02` improves; gold-token recall beats top-80 |
| C4 exemplar bank | M (weeks) | C0, C3 | `PC_correct` | improves without `H10` regression |
| C5 corpus synthesis | L (weeks) | C3 | everything downstream | register check near chance |
| C6 skeleton/slot | M (weeks) | C0, C3 | structural variance | only if C0 shows structural variance |
| C7 distil small parser | L | C5, C4 | determinism | C5 passes; residual variance justifies it |

C0–C2 are days and are independently useful regardless of where the rest goes. C5 is the
bet. C6 and C7 are explicitly conditional and may never run.

## Standing rules

- Re-run the consistency benchmark on every `DSL_SPEC` / `EXAMPLES` / vocabulary / model
  change; put `ΔPC` in the commit message (R4).
- The intent set is frozen and hashed; edits create a new version (R6).
- RulesGuru stays unread. The consistency set is disjoint from `nl_questions_poc`,
  `nl_questions_dev`, `nl_questions_adversarial`, the 20-query benchmark, and the
  compiler's own `EXAMPLES`.
- Every synthetic artifact (C5) records its generator provenance and version tuple, per
  `plan/architecture.md` §4.
- Stratum results are published even when they are bad; a phase that fails its decision
  rule gets its negative result written up, same as the ablations.

## Explicitly out of scope

- **Replacing the DSL with vector search.** Blocked by a rank-bound result on
  single-vector retrieval *and* by our own measured 10%-recall flat baseline
  (`research/nl-to-dsl-consistency.md` §1). Not revisited.
- **Grammar-constrained decoding / structured-output schemas.** They guarantee validity,
  which is already 28/28. Zero expected gain, and the ACL 2025 result notes larger models
  sometimes do *worse* under constraint.
- **A bespoke attention architecture.** The structural properties such models were built
  to provide are now decoding constraints, and we don't need them anyway. C7's small
  model is a distillation target, not a research architecture.
- Adjudication / NL→scenario compilation — Phase 2b, separate eval, separate plan.
