# Graph Layer Upgrades: Formalized Research Questions

**Research brief skeleton — August 2026.** Companion to
`nl-to-dsl-research-brief.md`, which covers the *formulation* layer (English →
query). This one covers the layer underneath: the ability-graph representation
and its query evaluator.

**Status: these are questions, not findings.** Nothing here has been verified
against sources. Named prior art is a *starting point to check*, flagged ⚠️
throughout, in the same convention the NL→DSL brief uses. The purpose is to
make each question precise enough to research without re-deriving the context.

**Sequencing rationale.** Formulation is the binding constraint today: all
seven of the owner's failing questions were answerable by the existing graph.
Fixing formulation lifts us to the graph's ceiling; these questions are about
where that ceiling is and how to raise it. Do not start here.

---

## 0. What is already settled — do not re-research

- **Graph beats flat text retrieval.** `research/graph-vs-flat-ablation.md`:
  pre-committed threshold was ≥5 points on an adversarial slice; the graph won
  by **+60 points of witness recall**. BM25 over oracle text was the baseline.
  The graph layer stays. Do not re-litigate representation-vs-text.
- **Structure finds what text cannot.** Across 8 benchmark queries with a text
  baseline: **313 cards found only by structure**, **216 text matches correctly
  rejected** by structure.
- **The search DSL is already separate from Forge's DSL.** `cardguru/querydsl`
  is a query language over the *extracted* graph; Forge syntax is ingestion
  only. (`nl-to-dsl-research-brief.md` §11 lists this as open — it isn't.)
- **Concept-gap mining exists.** `cardguru/gaps.py` computes the residual of
  structural signatures not covered by the concept libraries;
  `cardguru/induction.py` compiles a drafted concept, validates it against
  examples and counterexamples, measures selectivity, and registers it. Any
  proposal for automatic concept discovery must build on these, not replace them.

---

## 1. Taxonomy of the current limits

The blind 40-question benchmark produced 3 unexpressible and 7 partial rows.
Classified by *kind*, because the fixes are unrelated:

| kind | count | example | recoverable? |
|---|---|---|---|
| Unparsed representation | 4 | `ReplaceCount$DamageAmount/Twice` is a string | yes — parser work (RQ3) |
| DSL expressiveness | 2 | no node-scoped negation; no functional classes | yes — language design |
| Goal-vs-mechanism inference | 1 | "so I can untap and reuse" | partly (RQ6) |
| Evaluator scope | 1 | no cross-card joins | yes — evaluator (RQ1) |
| **True semantic holes** | **2** | SBA-vs-sacrifice causation; voluntariness | **no — not in the data** (RQ2) |

**~25% of realistic questions hit some limit; only ~5% hit something
unrecoverable.** That ratio is the single most important number for scoping
this work, and it should be re-measured once the eval harness exists.

---

## RQ1 — Cross-card interaction search

**Question.** Can structural combo/interaction discovery be made tractable over
34,519 single-card graphs, and is it a *search* problem or a *simulation*
problem?

**Our state.** `querydsl.evaluate()` takes one `CardGraph`. There is no join,
no pair enumeration, no notion of a loop. The benchmark row
`infinite-combo-enablers` is marked *unexpressible at the evaluator level, not
the vocabulary level*. Naive pair enumeration is ~600M pairs; triples are out
of reach entirely.

**Why it matters.** "What goes infinite with Kiki-Jiki" is a question real
players ask constantly, and it is the clearest thing the current architecture
cannot do at all. It is also the natural bridge to the adjudication engine: the
graph could *propose* candidate pairs and XMage could *verify* them at ~100ms
each — which would make CardGuru the only tool whose combo claims are executed
rather than crowd-sourced.

**Fields to search.** ⚠️ Subgraph pattern matching and subgraph isomorphism
(VF2 and successors); frequent subgraph mining (gSpan and descendants); graph
database pattern matching (Neo4j Cypher — note `nl-to-dsl-research-brief.md`
already surveys Text2Cypher, so the query-side literature is adjacent);
reachability and model checking; equality saturation / e-graphs (`egg`) for
rewrite-closure over effects.

**Domain prior art to check first.** ⚠️ **Commander Spellbook** is an existing
crowd-sourced MTG combo database with a published data model — the question of
how *it* represents a combo is directly informative, and it may be usable as a
labelled evaluation set for a structural detector. ⚠️ Churchill, Biderman &
Herrick, *Magic: The Gathering is Turing Complete* (2019) is the known formal
result on MTG's computational power and will bound what "detect all infinite
loops" can possibly mean.

**A good answer tells us.** Whether candidate generation can be pruned to a
tractable set by typed effect-interface matching (this card *produces* an untap;
that card *consumes* one) rather than blind enumeration; and whether "infinite"
is decidable structurally or only by simulation with a loop detector.

**Decision criterion.** If candidate generation cannot get below ~10⁵ pairs to
verify, this becomes an engine-first feature, not a graph feature.

---

## RQ2 — Rules-layer causation, and whether we need it

**Question.** Does the search layer need a model of *why* an event happened, or
can that be delegated entirely to the simulator?

**Our state.** Forge records what happened, never why: a creature dying to a
state-based action and to a sacrifice produce an identical `ChangesZone`
trigger. Voluntariness is likewise unrepresented — `OptionalDecider` marks
whether the *controller* may decline, not whether an opponent *chose*. Two
benchmark rows are unexpressible for exactly this reason.

Separately, `research/data/cr_mapping.json` is a **flat token → rule lookup**:
3,317 CR rules parsed, keywords 89% / trigger_modes 92% / apis 84% / replacement
events 96% by node volume — but **`static_modes` has no table at all, 0 of 138**
(`CantBeCast`, `RaiseCost`, `Continuous` all unmapped). It supports citation,
not reasoning. There is no rule hierarchy, no dependency between layers (613)
and replacement effects (614).

**Why it matters — and the counterargument.** Both true holes are *rules*
questions, and rules questions are XMage's job; it resolves them correctly by
executing the game. The division of labour may mean these holes are **fine**.
The research question is whether that delegation is complete or whether
search-time filtering ("find cards that trigger off state-based actions") is a
real product need that simulation cannot serve.

**Fields to search.** ⚠️ Event calculus and situation calculus for
representing causation; operational semantics of games; production-rule
systems (RETE) and Datalog/ASP for layered rule evaluation; legal-knowledge
representation (statutory reasoning has the same "hierarchical numbered rules
with cross-references and dependency" shape as the CR).

**A good answer tells us.** Whether a *partial* rules graph — just the CR
sections the ontology already touches, plus dependency edges — buys anything
beyond citation, or whether the honest answer is "cite from the index, simulate
for the truth."

**Decision criterion.** Build a static-mode CR table regardless (it closes a
measured 0/138 hole and costs little). Build a rules *graph* only if a concrete
product question needs causal filtering at search time.

---

## RQ3 — Lifting embedded value expressions

**Question.** Can Forge's `Count$` / `ReplaceCount$` expression language be
lifted into a typed AST, and what fraction of cards does that unlock?

**Our state.** Furnace of Rath and Torbran are **node-for-node identical** in
the graph; the entire difference is the string `ReplaceCount$DamageAmount/Twice`
vs `/Plus.2`. Same for Doubling Season vs Hardened Scales. The `value` field is
now matchable as a string (added this session), but there is no arithmetic — we
can pattern-match `/Twice`, not *understand* doubling. `research/data/ontology.json`
records 207 distinct `Count$` functions.

The hard part is named in the NL→DSL brief §11: **`Count$` semantics live in
`AbilityUtils.xCount` (Java), not in the card script.** The scripts reference an
interpreter we do not have.

**Why it matters.** It is 4 of the 10 problem benchmark rows — the largest
single recoverable bucket. It is also a prerequisite for the synthetic-corpus
work in the NL→DSL brief §5: canonical NL generation cannot template a card
whose quantity is an opaque string.

**Fields to search.** ⚠️ Lifting/decompilation of embedded DSLs; grammar
inference from examples; symbolic execution and partial evaluation of small
expression languages; abstract interpretation (we need *classification* — "is
this multiplicative?" — more than exact evaluation).

**A good answer tells us.** Whether to (a) hand-write a grammar for the ~207
observed `Count$` forms, (b) infer one from the corpus, or (c) extract semantics
from Forge's Java source as the ground truth. Option (c) is unglamorous and may
be strictly best.

**Decision criterion.** Measure coverage first: what percentage of `Count$`
occurrences are accounted for by the top 20 forms? If it is Zipfian like the
rest of this ontology, a hand-written grammar for the head may capture ~90% and
close the question cheaply.

---

## RQ4 — Hybrid attribute + structural query

**Question.** What is the right architecture for a query that spans the
in-memory ability graph and the relational card store?

**Our state.** `data/cards.sqlite` holds `cmc`, `colors`, `color_identity`,
`legalities`, `rarity` for 38,623 cards at a 99.83% join rate. The evaluator
cannot see any of it. Consequence: "≤3 mana" is a **regex over a mana-cost
string**, and "white or blue" required discovering that colour lives in
`manaCost` and not `types`. Two of the owner's seven failures were downstream
of this.

**Why it matters.** Lowest research risk of anything here and high user-visible
value — it removes a whole class of approximation. It is mostly plumbing, but
the *design* question is real: push structural predicates into SQL, pull
attributes into the evaluator, or keep two engines and intersect.

**Fields to search.** ⚠️ Polystore / federated query architecture; predicate
pushdown and join-order selection across heterogeneous stores; hybrid
dense-sparse retrieval architectures (same shape: two indexes, one answer).

**Decision criterion.** Given corpus size (34.5k), the simplest correct thing —
evaluate structure in memory, intersect with a SQL-derived id set — is very
likely sufficient. Research should mainly confirm there is no reason to be
cleverer.

---

## RQ5 — Graph similarity: what is the right metric?

**Question.** What similarity measure over ability graphs best matches a
player's notion of "cards like X"?

**Our state.** `cardguru/similar.py` derives a card's signature and searches
with it. The ranking heuristic was rewritten **three times in one session**:
param-count (wrong — the generic ETB trigger has the most params and sits on
4,471 cards), then pure selectivity (wrong the other way — picks rare riders
like `Attributes: Plotted`), then band-limited selectivity with greedy
validation. It currently works but is unprincipled, and multi-ability cards
remain genuinely ambiguous (Aven Interrupter exiles a spell *and* taxes; the
tool now exposes the choice rather than guessing).

**Why it matters.** This is the owner's own thesis — *"if we can map
interactions and kinds of cards through graph fingerprints it should house a
very powerful search tool."* Evidence so far supports it (Doubling Season →
Halving Season, derived with no hand-written rule). But the metric is
hand-tuned, and hand-tuned metrics are exactly what a literature exists to
replace.

**Fields to search.** ⚠️ Graph kernels (Weisfeiler-Lehman and variants); graph
edit distance and its approximations; unsupervised graph embeddings (graph2vec,
GNN encoders); learning-to-rank given relevance judgements. Note the corpus is
small (34.5k graphs, median ~3 nodes) — methods designed for million-node
graphs are likely the wrong shape.

**A good answer tells us.** Whether a principled kernel beats our heuristic on
a labelled set, and how to weight *node type* against *effect identity* — the
open product question (should "like Aven Interrupter" return only creatures?).

**Decision criterion.** Needs a labelled similarity set to evaluate against.
⚠️ Candidate free sources: Scryfall community tags, EDHREC theme pages,
"functional reprint" lists. Without labels this question cannot be answered,
only argued.

---

## RQ6 — Automatic induction of functional classes

**Question.** Can the concept libraries (hooks, roles) be induced from the
graph corpus rather than hand-authored one gap at a time?

**Our state.** 49 hooks, all hand-written. This session added exactly one
(`disrupts_spells`) — *after* the owner found the gap, and it took four
structurally unrelated Forge mechanisms (`Counter`, `Airbend`, exile-off-stack,
opponent-facing `RaiseCost`) to cover one player-facing word. `gaps.py` already
computes the residual — signatures no concept explains — and `induction.py`
already gates a drafted concept against examples, counterexamples, and
selectivity. **The mining and validation halves exist; the drafting half is
human.**

**Why it matters.** This is the graph-side twin of the NL→DSL brief's alias
layer (§7), which it argues is the single largest available gain (BIRD's
knowledge-evidence swing: **20 points**). That brief says *mine it, don't
hand-author it*. The two efforts should share a taxonomy: the alias layer maps
*slang → pattern*, this maps *structure → concept*. They meet in the middle.

**Fields to search.** ⚠️ Formal Concept Analysis (Ganter & Wille) — objects ×
attributes → concept lattice is an almost exact fit for cards × graph features;
frequent subgraph mining for candidate patterns; clustering with LLM labelling
of clusters; weak supervision / labelling functions (Snorkel-style) for
combining noisy structural signals into a class.

**A good answer tells us.** Whether concept *discovery* can be automated to the
point where a human only accepts or rejects, and what the precision/recall
tradeoff looks like against the 49 hand-written hooks as a gold set.

**Decision criterion.** We have a natural evaluation: can the pipeline
rediscover the existing 49 hooks from the corpus alone? Anything that cannot is
not ready to propose new ones.

---

## 2. Suggested research order

1. **RQ6** (concept induction) and **RQ3** (value lifting) — largest measured
   buckets, both build on assets that already exist, both unblock the NL→DSL
   work rather than competing with it.
2. **RQ4** (hybrid query) — least research, real user-visible gain; mostly
   confirming the simple design is fine.
3. **RQ5** (similarity metric) — blocked on finding a labelled set; do that
   scouting first.
4. **RQ1** (cross-card) — highest ceiling, highest cost; check Commander
   Spellbook's data model before designing anything.
5. **RQ2** (rules causation) — build the static-mode CR table regardless;
   defer the rules graph until a product question demands it.

## 3. Cross-cutting questions

- Is there prior art on **MTG specifically** as a structured-representation
  problem, beyond the Turing-completeness result? Any parsed-rules or
  card-semantics corpus would change several answers at once.
- Every RQ above wants a labelled evaluation set. Is there one shared source
  (Scryfall tags? EDHREC? Commander Spellbook?) that serves RQ1, RQ5 and RQ6
  together? Finding that is probably worth more than any individual answer.
- Are we solving a problem the card-game-AI literature already solved for
  deckbuilding or drafting agents, in which case their state representations
  are directly informative?
