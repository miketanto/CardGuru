# NL→DSL consistency: can we drop the compiler, or make it deterministic?

The question, as raised: *the problem is consistency of NL→DSL — can we replace that
layer with vector search / embeddings (the Cardmystic approach), or make it
deterministic some other way, maybe a custom attention model? What does the
literature offer?*

Short answer, up front:

- **No, embeddings cannot replace the DSL layer.** There is now a *theoretical*
  reason, not just an empirical one, and our own ablation already measured the gap
  (109 vs 1,123 cards).
- **Yes, the layer can be made near-deterministic** — but by moving the entropy
  *out* of the generation step, not by replacing the model. Four levers, in
  increasing order of effort: execution-consensus, semantic caching, retrieval of
  exemplars + ontology slice, and finally a synthesized corpus that can either feed
  retrieval or distil into a small fine-tuned parser.
- **"Custom attention model" is the wrong shape of answer**, and the literature is
  unusually clear about why: the architectural tricks that bespoke semantic-parsing
  models existed to provide (grammar decoders, copy/pointer nets) are now available
  as *decoding constraints* on any model — and we already get their guarantee for
  free from `cardguru/validate.py`.
- **The first thing to build is the measurement**, because we have never measured
  consistency at all. Everything below is unfalsifiable until we do.

---

## 0. What we actually have, and what we've actually measured

The current compiler (`cardguru/nl_compiler.py`) is: a hand-written `DSL_SPEC`
(~50 lines), a truncated vocabulary dump (top-80 APIs, top-60 trigger modes, top-40
static modes, top-34 replacement events, top-80 keywords, top-100 param keys), six
static few-shot examples, an ontology validator as a hard gate, and bounded retry on
validation errors plus a zero-hit signal.

Measured so far (`research/agent-compiler-poc.md`, `research/agent-compiler-round2.md`):

| metric | result |
|---|---|
| DSL validity, first pass | 28/28 — **the ontology gate has never once fired on a dev query** |
| Witness-correct, first pass | 23/28 |
| Witness-correct, after automatic-signal retries | 26/28 |
| Residual failures | d12 (Fog), q1 (`DamageAll`), q2 (`ReplaceCounter`), d13 (`ChangeType` vs `ValidCards`) — all *vocabulary-idiom* errors |

Two things fall out of that table that shape everything below.

**First: validity is a solved problem and semantics is not.** 28/28 first-pass
validity means the validator gate is currently doing zero work — every failure we
have is a *semantically wrong but perfectly well-formed* query. Any technique whose
contribution is "guarantee well-formed output" (grammar-constrained decoding,
structured outputs, a grammar-based decoder architecture) buys us **nothing**, because
we already have that property. This is worth stating loudly because it eliminates a
large and superficially attractive branch of the literature. It also matches the ACL
2025 finding on grammar-constrained decoding directly: GCD improves syntactic
correctness, but *"semantic errors not captured by Context-Free Grammars continue to
pose challenges"* — and there is even a reported trade-off where unconstrained
generation from larger models occasionally beats constrained decoding.

**Second: we have never measured consistency.** Every number above is single-sample,
single-phrasing, pass/fail-on-a-witness. We have no measurement of:

- **paraphrase variance** — same intent, five phrasings, does the result set move?
- **sampling variance** — same phrasing, five samples, does the result set move?
- **prompt-drift variance** — does adding an idiom line to `DSL_SPEC` for d12 silently
  change the compiled query for d3?

That third one is the quiet killer. `DSL_SPEC` has grown a hand-written idiom line
after every eval round (the `*All` variants after round 1, `ReplaceCounter` after
round 1, `Fog` queued after round 2). That is a manually-maintained schema-linking
table, it scales linearly with the ontology's long tail, and every edit to it is an
unmeasured global perturbation of the compiler's behaviour. We are, right now,
tuning a system whose variance we cannot see.

---

## 1. Can vector search replace the DSL layer? No.

The Cardmystic-shaped proposal is: embed every card's text, embed the user's
question, return nearest neighbours; no DSL, no compiler, no consistency problem.
Cardmystic itself uses ColBERT (late-interaction, multi-vector) for semantic search
and ALS for deck recommendation, per [their about page](https://cardmystic.com/about).
It's a good product for what it does. It cannot do what CardGuru does, for three
independent reasons.

**(a) There is a hard theoretical ceiling on what a single-vector retriever can
return.** Weller, Boratko, Naim and Lee (Google DeepMind / JHU, 2025) connect
retrieval to learning-theory rank bounds: for a fixed embedding dimension *d*, the
number of top-*k* document subsets that can be returned by *any* query is bounded —
there exist combinatorial sets of documents that **no** single-vector embedding model
can ever return as a top-*k* result, regardless of training. They confirm this even
when directly optimising embeddings on the test set, then build **LIMIT**, a
deliberately trivial-looking dataset ("who likes Quokkas?") on which most SOTA
single-vector models fail to reach **20% recall@100**.

Our queries are exactly the combinatorial kind: `all`/`any`/`not` over node
predicates plus reachability constraints. "Sagas whose chapters tutor onto the
battlefield **and** don't sacrifice themselves" is a set-combination query. This is
the failure mode the theorem describes.

**(b) Negation and conjunction collapse in embedding space.** The QUEST and NevIR
line of work documents that dense retrievers treat logically contradictory queries
("A AND B" vs "A NOT B") as near-identical, and that BM25 frequently *beats* dense
retrievers on logically-composed queries. Our DSL's whole value is the operators.

**(c) It retrieves over the wrong substrate, and this is our entire moat.**
Embeddings run over oracle *text*. CardGuru runs over Forge ability *graphs* — the
level at which `DamageAll`/`ValidPlayers` and `DealDamage`/`Defined` are the same
concept and `DB$ ChangeZone` splits into mechanically distinct effects. We already
ran this ablation (`research/agent-compiler-round2.md`): the text-level baseline
found every famous witness card and **~10% of the mechanically-true set** (109 names
vs 1,123 graph hits), with zero provenance. A ColBERT retriever would land somewhere
above 109 and far below 1,123, still with no evidence subgraph to show, and still
going to zero on cards printed after its training data — which is the day-one moat.

**Verdict:** vector search is a *recall-shaped* tool and our problem is
*precision-and-provenance-shaped*. It cannot be the retriever. It is, however,
extremely useful one layer up.

---

## 2. Where vectors *do* belong: on the question side, not the card side

Three places, all cheap, all drop-in, all with literature support.

### 2.1 Dynamic exemplar retrieval (replaces the six static few-shots)

Right now every question — Sagas, counterspells, fog, mass bounce — gets the same
six `EXAMPLES`. The text-to-SQL literature is consistent that retrieved,
question-similar exemplars beat fixed ones: XRICL (Shi et al., Findings of EMNLP
2022) builds retrieve-and-rerank exemplar selection and reports gains in exact-match
and token-sequence accuracy; the broader retrieval-augmented-ICL line reproduces this
across settings.

Concretely: keep a growing bank of `(question, validated DSL, hit count, verified?)`
records — we already generate these on every eval round and every `ask` invocation —
embed the questions, retrieve top-*k* at compile time.

The consistency argument is the interesting one, and it's stronger than the accuracy
argument: **a retrieval bank is a memory, and a memory is what makes a system
converge.** Once "cards that exile from library and let you play them" is in the
bank with a verified query, every future paraphrase of it pulls that exemplar and
compiles to (nearly) the same thing. Variance today is high partly *because* the
system has no way to remember that it already answered this.

### 2.2 Ontology-slice retrieval (fixes the real failure mode)

All four of our residual failures are the same bug: the model picked a plausible
token from a truncated vocabulary list because the *right* token wasn't advertised or
wasn't explained (`Fog` has its own API; zone-changes use `ChangeType` not
`ValidCards`; `ReplaceCounter` not `MultiplyCounter`; `DamageAll` not `DealDamage`).

That is precisely **schema linking**, which the text-to-SQL literature identifies as
*the* bottleneck. RESDSQL (Li et al., AAAI 2023) decouples schema linking from
skeleton parsing with a ranking cross-encoder that filters schema items; DIN-SQL
makes schema linking the first and most critical of four modules. LinkAlign and
successors push this to large schemas where the schema no longer fits the context —
which is exactly our situation: we have far more API/mode/param tokens than the
top-N truncation shows the model.

Proposal: build a **retrievable idiom lexicon** instead of a hand-edited `DSL_SPEC`.
For each ontology token, mine (from the corpus, not by hand) a record:

```
{ "token": "Fog", "kind": "api", "freq": 412,
  "gloss": "prevents all combat damage this turn",
  "example_cards": ["Fog", "Holy Day", "Darkness"],
  "confusable_with": ["PreventDamage", "PreventDamageAll"] }
```

Embed the glosses, retrieve top-*k* per question, inject only those. This turns our
linearly-growing hand-maintained spec into mined data, shrinks the prompt, and
directly attacks the class of error we actually have. The `confusable_with` field is
the highest-value part: it's the machine-generated version of every line we've hand-
added to `DSL_SPEC` so far.

**Note we already have the miner.** `cardguru/gaps.py` signatures every card's
structures over the closed ontology and ranks unexplained clusters; `induction.py`
compiles declarative concept drafts and validates them against example cards and
counterexamples before admitting them. The lexicon is the same machinery pointed at
a different output.

### 2.3 Semantic caching of the head of the query distribution

Embed the question; if cosine similarity to a previously-answered question exceeds τ,
reuse that question's **frozen** DSL rather than recompiling. Query distributions are
Zipfian (the same reason our hook distribution is — 612 `makes_tokens`, 610
`puts_counters`, ...), so a few hundred frozen entries plausibly cover most traffic.

This is the only technique on this page that delivers *literal* determinism: same
question → byte-identical query → byte-identical result set, forever, with no model
call. It is also the cheapest thing here, and it composes with everything else. The
risk is τ: too loose and near-miss questions silently get the wrong frozen query.
Mitigation is to make cache hits *visible* in the response (we already stamp tier
labels per `plan/architecture.md` §2) and to require a verified witness before an
entry is frozen.

---

## 3. The big lever: invert the direction (DSL→NL), don't just improve NL→DSL

This is the recommendation I'd actually push, and it is the one where CardGuru has an
advantage almost no semantic-parsing project has.

The canonical technique is **Overnight** (Wang, Berant & Liang, ACL 2015): rather
than collecting NL and annotating it with logical forms, *generate logical forms from
a grammar*, render each to a stilted **canonical utterance**, then paraphrase the
utterances into natural language. **Genie** (Campagna et al., PLDI 2019) industrialised
this — developers write templates, Genie synthesises data plus crowdsourced
paraphrases and augmentation, and trains a parser. **AutoQA** (Xu et al., EMNLP 2020)
removed the crowdworkers: automatic paraphrasing with a *filtered auto-paraphraser*
(keep a paraphrase only if it round-trips back to the same logical form) reached
62.9% logical-form accuracy on real questions — only **6.4 points below** a model
trained on expert annotations plus crowdsourced paraphrases, and 16.4 points above
the best zero-shot models.

Why this fits CardGuru unusually well — three preconditions that are normally the
hard part, and we already have all three:

1. **The ontology is closed and mined.** We can enumerate the DSL grammar's terminals
   exactly. `gaps.py` already enumerates *structural signatures actually present in the
   pool*, which is far better than enumerating the raw cross-product — it gives us the
   queries that correspond to real card mechanics rather than combinatorial noise.
2. **Every generated query is executable in milliseconds** over 34,519 faces. So each
   synthesized `(canonical utterance, DSL)` pair comes with its **result set** for
   free. That is supervision *and* a filter: drop queries returning 0 hits (vacuous)
   or ~all hits (trivial); keep the informative middle.
3. **We have a filter for paraphrase quality that AutoQA had to approximate.** AutoQA
   round-trips paraphrases through a parser and checks logical-form equality. We can
   do better: round-trip and check **result-set equality**, which is the correct
   equivalence relation (two structurally different queries with the same hit set
   *are* the same query). Cheap, exact, no parser needed.

Output: a corpus of tens of thousands of `(natural question, DSL, result set)` triples
with **zero human annotation**. That corpus is simultaneously:

- the retrieval bank for §2.1,
- the training set for §4,
- the test set for §6 (paraphrase clusters are consistency test cases *by construction*),
- and a gap detector — DSL structures for which the paraphraser produces no natural
  phrasing are structures no user will ever ask for, which is useful product signal.

**What would kill it:** if LLM-generated paraphrases cluster in a narrow register that
doesn't match how players actually talk ("a trigger on combat damage to a player"
vs "when it connects"), the corpus trains/retrieves for the wrong distribution. Genie
addressed this with a small set of *real* validation inputs, and we should do the same
— our existing `eval/nl_questions_*.json` sets are exactly that, and must stay held out
from synthesis.

---

## 4. "A custom attention model" — what the literature actually says

The honest answer: **a bespoke architecture is not the lever, but a small fine-tuned
parser might be.** These are different proposals and it's worth separating them.

**Bespoke attention architectures are obsolete for this.** The 2016–2019 semantic
parsing literature built custom models specifically to enforce structure — grammar-
constrained decoders, copy/pointer networks for out-of-vocabulary tokens, coarse-to-
fine sketch decoders. Every one of those architectural properties is now obtainable
as a *decoding constraint* over any model, without a custom model. And, per §0, we
don't need it: our validity is already 28/28. Building a custom attention model to
guarantee well-formed JSON would be paying a large research cost for a property we
already have.

**A small fine-tuned parser is a real option, for a different reason: determinism.**
A fine-tuned seq2seq at temperature 0 has no prompt, so it has no prompt-drift
variance; it has no vocabulary truncation, because the ontology is baked into its
output vocabulary; it costs ~nothing per query; and it is *reproducible* — the same
weights give the same query forever, which is the property being asked for. AutoQA's
result (within 6.4 points of human-annotated training, using only synthetic data) is
the evidence that this is reachable from §3's corpus alone.

The sane sequencing is **distillation, not replacement**: run the LLM compiler with
§2's retrieval, accumulate verified `(question, DSL)` pairs, add §3's synthetic corpus,
fine-tune a small model, and route to it only where it agrees with the LLM on held-out
data. Keep the LLM for the tail. This is the standard "big model for the tail, small
model for the head" split, and the head is where consistency complaints live.

**One structural idea worth stealing regardless of model choice:** RESDSQL's decoupling
of *skeleton* from *slots*. Predict the DSL **shape** first (`chain(from: T, to: A)` vs
`node` vs `all[...]`) — a low-entropy decision over maybe a dozen shapes, easily made
consistent — then fill the api/mode/param slots from a retrieved ontology slice. One-shot
generation of the whole nested JSON couples a stable decision to an unstable one; splitting
them means paraphrase noise can only perturb the slots, not the structure. This is
implementable today inside the existing compiler, with no new model.

---

## 5. Determinism by construction: consensus over *execution*, not over text

The single most underused asset here: **our queries are cheap to run.** Milliseconds
over the whole pool. That makes execution the arbiter.

**Execution-guided decoding** (Wang et al., 2018) discards partial programs whose
execution fails. **LEVER** learns to verify generated programs by their execution
results. The **MBR-for-SQL** line makes the key observation for us: different queries
can produce identical results while differing structurally, so majority voting over
*query text* is the wrong operation — semantic equivalence must be measured at the
**execution level**, framed as minimum-Bayes-risk decoding over an execution-similarity
metric. CSC-SQL and related work push corrective self-consistency further.

Applied here, that's a small, concrete change:

1. Sample *k* compilations (k=3–5) at nonzero temperature.
2. Execute all of them (cheap).
3. Cluster by **result set** — Jaccard over returned face IDs, not JSON equality.
4. Return the largest cluster's query.
5. **Emit the cluster agreement as a confidence signal.**

Step 5 is the product-relevant part. Perfect agreement → answer confidently. A 2/2/1
split → the question was genuinely ambiguous, and the right UX is to show both
readings ("cards that exile from the library" — did you mean impulse-draw, or any
library-to-exile effect?). That converts a consistency *defect* into a disambiguation
*feature*, and it slots directly into the visible-uncertainty posture already in
`plan/architecture.md` §2.

Also worth generalising: the existing "0 hits → retry" loop is already a primitive
execution signal. The full set is richer — 0 hits, suspiciously many hits (>5% of the
pool), hits that don't intersect a retrieved text-baseline's top names (a *good* use for
an embedding index!), and disagreement across samples.

---

## 6. What to build first: the consistency benchmark that doesn't exist

Nothing above is falsifiable until we can measure the thing being complained about.
This is the Dr.Spider protocol (Chang et al., ICLR 2023 — NLQ-perturbation test sets,
on which even PICARD dropped 14 points) and Spider-Syn (Gan et al., ACL 2021 —
synonym substitution) adapted to our setting.

Design:

- **Intents**: ~40, drawn from existing eval sets plus §3's synthesis.
- **Paraphrases**: 5 per intent — player-register, judge-register, verbose, terse,
  synonym-substituted. Authored/checked by hand; this is the one place human effort is
  well spent.
- **Samples**: 3 per paraphrase.
- **Metrics** (all at the result-set level, per the MBR argument):
  - `PC@k` — **paraphrase consistency**: mean pairwise Jaccard of result sets across
    the 5 paraphrases of one intent. *This is the headline number.*
  - `SC@k` — **sampling consistency**: same, across 3 samples of one paraphrase.
    Isolates model nondeterminism from phrasing sensitivity.
  - `DSL-EM` — exact query match, reported but **not optimised** (structurally different
    queries can be semantically identical; treating EM as the target would push us to
    the wrong invariance).
  - `ΔPC` on spec edits — re-run after every `DSL_SPEC` change, to catch the drift we're
    currently blind to.

Cost is bounded: 40 × 5 × 3 = 600 compilations, each a cached-prefix call. That is a
few dollars and an afternoon, and it turns "consistency feels bad" into a number that
every proposal above can be scored against.

**Prediction, on the record:** I expect `SC` to be high (~0.9 Jaccard — the vocabulary
gate plus a strong model constrains sampling variance a lot) and `PC` to be
meaningfully lower (~0.6–0.75), with the variance concentrated in *which* ontology
token gets chosen rather than in query structure. If that's right, §2.2
(ontology-slice retrieval) and §4's skeleton/slot split are the highest-value fixes and
§5 is the cheap safety net. If instead `SC` is also low, the fix ordering flips and §5
becomes urgent. Either way, we'd know.

---

## 7. Recommended sequence

| # | Move | Effort | What it buys | Risk if skipped |
|---|---|---|---|---|
| 1 | **Consistency benchmark** (§6) | S | A number for `PC`/`SC`; drift detection on `DSL_SPEC` edits | Everything below is guesswork |
| 2 | **Execution consensus, k=3** (§5) | S | Variance suppression today; free ambiguity signal for the UI | Cheapest win left on the table |
| 3 | **Semantic cache of verified queries** (§2.3) | S | Literal determinism on the head of the distribution | Recompiling answers we've already verified |
| 4 | **Ontology-slice retrieval + mined idiom lexicon** (§2.2) | M | Attacks the actual failure class; retires the hand-grown `DSL_SPEC` | Hand-maintained spec grows forever, unmeasured |
| 5 | **Exemplar retrieval from a growing verified bank** (§2.1) | M | Accuracy + convergence over time | System keeps forgetting what it solved |
| 6 | **Grammar→canonical-utterance→paraphrase corpus** (§3) | L | Retrieval bank, training set, test set, gap detector — all at once | The one asset that unlocks everything else |
| 7 | **Skeleton/slot decomposition** (§4) | M | Structural stability decoupled from token choice | Paraphrase noise keeps perturbing query shape |
| 8 | **Distil a small fine-tuned parser on 6** (§4) | L | Reproducible, ~free, no prompt drift, head-of-distribution | Only worth it once 6 exists and 1 says it's needed |

Items 1–3 are days, not weeks, and 1–2 are independently useful regardless of which
direction the rest goes. Item 6 is the strategic bet.

**The thing not to build:** a bespoke attention architecture, or a pure vector-search
replacement for the DSL. The first solves a problem we don't have (validity); the
second is blocked by a theorem *and* by our own measured 10%-recall ablation.

---

## References

- Weller, Boratko, Naim, Lee — *On the Theoretical Limitations of Embedding-Based Retrieval* ([arXiv 2508.21038](https://arxiv.org/pdf/2508.21038), [LIMIT dataset](https://github.com/google-deepmind/limit))
- Wang, Berant, Liang — *Building a Semantic Parser Overnight*, ACL 2015 ([pdf](https://nlp.stanford.edu/pubs/wang-berant-liang-acl2015.pdf))
- Campagna, Xu, Moradshahi, Socher, Lam — *Genie: A Generator of Natural Language Semantic Parsers for Virtual Assistant Commands*, PLDI 2019 ([arXiv 1904.09020](https://arxiv.org/pdf/1904.09020), [toolkit](https://github.com/stanford-oval/genie-toolkit))
- Xu, Semnani, Campagna, Lam — *AutoQA: From Databases To QA Semantic Parsers With Only Synthetic Training Data*, EMNLP 2020 ([arXiv 2010.04806](https://arxiv.org/abs/2010.04806), [Schema2QA docs](https://stanford-oval.github.io/schema2qa/doc/run.html))
- Shi et al. — *XRICL: Cross-lingual Retrieval-Augmented In-Context Learning for Text-to-SQL Semantic Parsing*, Findings of EMNLP 2022 ([ACL Anthology](https://aclanthology.org/2022.findings-emnlp.384/))
- Li et al. — *RESDSQL: Decoupling Schema Linking and Skeleton Parsing for Text-to-SQL* ([arXiv 2302.05965](https://arxiv.org/pdf/2302.05965))
- *LinkAlign: Scalable Schema Linking for Real-World Large-Scale Multi-Database Text-to-SQL* ([arXiv 2503.18596](https://arxiv.org/html/2503.18596v4))
- Gan et al. — *Towards Robustness of Text-to-SQL Models against Synonym Substitution* (Spider-Syn), ACL 2021 ([ACL Anthology](https://aclanthology.org/2021.acl-long.195/))
- Chang et al. — *Dr.Spider: A Diagnostic Evaluation Benchmark towards Text-to-SQL Robustness*, ICLR 2023 ([OpenReview](https://openreview.net/pdf?id=Wc5bmZZU9cy))
- Wang et al. — *Robust Text-to-SQL Generation with Execution-Guided Decoding* ([arXiv 1807.03100](https://arxiv.org/abs/1807.03100))
- *Exploring Minimum Bayes Risk Decoding for Text-to-SQL* ([OpenReview](https://openreview.net/pdf/97e88e51d519cebe85d64fc997e3fd3bc9b97b37.pdf)); *Query and Conquer: Execution-Guided SQL Generation* ([arXiv 2503.24364](https://arxiv.org/pdf/2503.24364))
- Raspanti, Ozcelebi, Holenderski — *Grammar-Constrained Decoding Makes Large Language Models Better Logical Parsers*, ACL 2025 Industry Track ([ACL Anthology](https://aclanthology.org/2025.acl-industry.34/))
- CardMystic — ColBERT-based MTG semantic search ([about page](https://cardmystic.com/about))
- Prior CardGuru work this builds on: `research/agent-compiler-poc.md`, `research/agent-compiler-round2.md`, `plan/architecture.md` §2, `plan/uncertainties.md` §1/§3
