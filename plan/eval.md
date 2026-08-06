# Evaluation design

Goal: measure whether the system answers rules questions correctly, without the
self-graded-homework failure mode the ~90% multi-agent baseline suffers from. Two separate
things are being evaluated and they must not share a leaderboard:

1. **Mechanical search quality** (Phase 1 product) — retrieval metrics.
2. **Interaction adjudication accuracy** (Phase 2/3 product) — answer correctness.

## A. Ground-truth sources (in order of trustworthiness)

| Source | Nature | Access status | Role |
|---|---|---|---|
| Engine-executed scenarios (XMage, cross-checked with Forge) | (state, action) → outcome, machine-verified | both engines in hand; XMage test API verified this session | Ground truth for adjudication; generation of the verified corpus |
| XMage's own regression suite (~2,000 test classes in `Mage.Tests`, incl. `LayerTests`, `HumilityTest`) | judge-reviewed scenario→assertion pairs | cloned | Seed corpus: parse `addCard/castSpell/assert*` into scenario records — thousands of pre-authored, human-reviewed adjudications |
| Official per-card rulings (Scryfall/Gatherer) | WotC-sanctioned English Q&A | Scryfall blocked in this sandbox; available with network allowlisting | Held-out NL eval; also retrieval corpus |
| RulesGuru (rulesguru.org) | judge-authored Q&A, tagged by rule, with an API (`/api/questions/`, documented at rulesguru.org/api/documentation) | site blocked in this sandbox; API exists (verified via search; source at github.com/KingSupernova31/RulesGuru — the live question DB is server-side, not in the repo) | NL benchmark, difficulty-stratified |
| Judge exam practice questions (L1/L2) | expert-authored MCQ | to source; licensing unclear | Small high-quality held-out set |
| Stack Exchange boardgames (mtg tag) | community Q&A, accepted answers | data dumps exist (archive.org); not fetched this session | Long-tail NL questions; noisy — use accepted+highly-voted only |

## B. The anti-gaming rules

The baseline's flaw: it was scored on an eval its authors curated while building the system.
Countermeasures, all cheap:

1. **Hard held-out split by source, not by random row.** Tune on engine-generated scenarios +
   XMage suite + rulings. Hold out RulesGuru and judge-exam questions entirely — never inspect
   them during development, score at the end (and only a frozen snapshot: question IDs fixed
   before first scoring run).
2. **Freeze before first measurement.** The held-out set and the scoring script are committed
   and hashed before the first end-to-end run; any later change is a new benchmark version.
3. **Adversarial slice.** Explicitly over-sample the classes where LLMs are known to be
   confidently wrong: layers (613), dependency, timestamps, replacement-effect ordering (614/616),
   copy effects (707), state-based actions vs. triggers ordering, priority/stack minutiae.
   RulesGuru tags questions by rule, which makes this slice constructible.
4. **Report abstention as a first-class outcome.** Metrics: accuracy on attempted, coverage
   (fraction attempted), and *confidently-wrong rate* (wrong while claiming verified). The
   product promise is "verified or visibly uncertain," so confidently-wrong is the metric to
   drive to ~0, even at the cost of coverage.
5. **No NL leakage into the corpus generator.** The offline verified corpus (Phase 2a) is
   generated from card/ability structure, not from eval questions, so memorizing the corpus
   cannot leak eval answers verbatim.

## C. Metrics

**Adjudication (per question):**
- `exact-outcome accuracy` — final board/stack/life state or MCQ answer matches.
- `verified-answer rate` — fraction where the engine actually executed the scenario
  (vs. fell back to retrieval-only reasoning).
- `confidently-wrong rate` — wrong AND presented as engine-verified. Target ≈ 0; this is the
  kill-signal metric. A wrong answer that the engine executed means either a scenario-compilation
  bug or an engine bug — both must be surfaced, and cross-engine disagreement (XMage vs Forge)
  is the cheap detector.
- Stratify all of the above by: rules area (CR section tag), engine-executed vs not,
  card-implementation status.

**Mechanical search (per query):**
- Build ~50 benchmark queries with hand-verified answer sets (the three from Phase 1 are the
  start). Score precision/recall of returned card sets.
- Comparison baselines: (a) best-effort Scryfall query written by a competent user,
  (b) LLM-over-oracle-text retrieval. The pitch requires beating (a) on expressiveness and
  (b) on precision.

## D. Graph-vs-flat-RAG ablation (the skepticism the brief ordered)

Question: does the knowledge graph earn its complexity over flat retrieval on the same corpus?

- **Corpus held constant:** CR text chunks, rulings, verified scenarios, card records. Same
  chunks in both arms.
- **Arm 1 (flat):** BM25 + embedding hybrid over the corpus; answerer LLM sees top-k.
- **Arm 2 (graph):** same retriever, plus graph expansion (card → ability nodes → mapped CR
  rules → linked scenarios) feeding structured context.
- **Same answerer model/prompting in both arms;** the only variable is retrieval structure.
- Decision rule, committed in advance: if Arm 2 does not beat Arm 1 by ≥5 points on the
  adversarial slice (or reduce confidently-wrong), **cut the graph layer** and keep the
  ability-graph only for search (where Phase 1 already proved it) — not for adjudication context.
- Third arm worth one afternoon: engine-verified answers with *no* retrieval at all, to learn
  how much of the benchmark the engine alone closes.

## E. Benchmark hygiene notes

- Every benchmark row records: CR version, Oracle/card-data snapshot date, engine versions.
  Answers are only comparable at matching versions (see versioning section of architecture doc).
- RulesGuru questions embed card names by template (`[card 1]`); their generator can vary
  cards within a question archetype — useful for contamination-resistant paraphrase testing.
- The NL→scenario compiler (Phase 2b) gets its own intermediate eval: scenario-compilation
  accuracy against hand-written scenario specs for ~100 questions, judged by exact game-state
  match after setup, *before* any adjudication accuracy is claimed.
