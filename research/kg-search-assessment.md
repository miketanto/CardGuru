# KG-powered search: what holds, what doesn't, and where the ceiling actually is

CardGuru is a proof of concept for one claim: **that retrieving over a
structured knowledge graph extracted from a domain's own machine-readable
encoding beats retrieving over its prose.** Magic cards are the substrate, but
the substrate is not the point. This note is the scientific accounting — what
is measured, what was tried and rejected, and what a team in another domain
should expect to pay.

Everything below is a measurement with a pointer to the run that produced it.
Where something is unmeasured it says so.

---

## 1. Scoreboard

### Winning

| claim | evidence | where |
|---|---|---|
| **Structure beats text where they diverge** | adversarial slice: witness recall **5/5 vs 2/5**, precision@10 **0.82 vs 0.10** | `graph-vs-flat-ablation.md` |
| Text is serviceable when wording matches | text-friendly dev set: **15/20** flat vs 19/20 graph | same |
| The graph can express the answers | hand-vetted queries **37/37** on the original goldens | `eval_compile --source reference` |
| Execution feedback works | zero-hit repair: **+1.5 to +2.7 questions**, zero-hit queries −65% (Haiku) to −100% (Opus) | handoff §4b |
| Mined structural aliases work | disjunctive families **+9.8pp recall, exact permutation p=0.017** at 7 seeds/arm | `families.md` §9 |
| **The compiler beats expert hand-authoring** | on blind pooled goldens: compiler **76.0%** vs hand-written reference **69.2%** | `benchmark-density.md` §6 |
| Every hit is explainable | each result carries its graph path (`ab1[T:Attacks] -> TrigToken[SVar:Token]`) | product |

That last row is the differentiator text retrieval structurally cannot match,
and it is why the graph layer survived its own ablation.

### Losing

| problem | measurement |
|---|---|
| Absolute recall is ~80%, not ~97% | per-question recall **median 91%, mean 81%**; **6/37 questions below 50%** |
| **Precision is essentially unmeasured** | judged fraction of returned cards: **4.7%** |
| Where precision *is* visible it looks bad | `landfall-payoffs` **9%**, `play-lands-from-graveyard` 16%, `sac-outlet` 11% |
| Result sets are often unusable | median **72**, mean **297**, max **4,980** |
| The residual is a long tail | ~20 golden cards missed across all 7 seeds, **~15 distinct causes**, no common fix |
| Model choice dominates every intervention | Haiku→Opus **+7.5 questions**; best prompt intervention +2.7 |
| Hand-written prompt conventions cost recall | 3 documented instances (below) |

**The single most important caveat in this document:** every metric this project
has ever optimised — `expect_present`, golden recall, the families A/B — is a
**recall** metric. A user's felt experience of a search is dominated by
precision, and `expect_absent` averages four cards per question. We have been
measuring one half and shipping both.

---

## 2. Everything tried, with verdicts

| intervention | verdict | evidence |
|---|---|---|
| Ability-graph retrieval vs BM25 | **KEPT** | +60pts witness recall, 8× precision@10 on adversarial slice |
| Param-shape mining (`shapes.py`) | **KEPT** | resolved the `CantBeCast` 8-meanings failure |
| Zero-hit execution feedback (`repair.py`) | **KEPT, default on** | +1.5–2.7 questions, 0 false positives on 37 known-good queries |
| Disjunctive family mining (`families.py`) | **KEPT** | +9.8pp recall, p=0.017 |
| Benchmark pooling + adjudication | **KEPT** | seeds needed to resolve an effect: **16 → 7** |
| Over-narrow "relaxation" signal (`near_misses`) | **REJECTED** | fires on **24/37 known-good** queries; no threshold separates it — the real defect (61×) sits *below* three correct queries (267×, 206×, 123×) |
| Dead-predicate signal | available, not default | 0 false positives but no measured gain |
| Distributional similarity for families | **REJECTED** | merges antonyms: `GainLife`↔`LoseLife` 0.69, `Taps`↔`Untaps` 0.69 |
| Description inheritance (parent→sub-ability) | **REJECTED** | recovers 2 families, destroys 2; net **4/13 vs 5/13** |
| Raw-volume family ranking | **REJECTED** | promotes structural-English anchors into the digest |
| **BM25 text cross-check for recall** | **REJECTED** | rescues **1 of 20** cards the graph misses (5%); injects 3 false positives |
| Grammar-constrained decoding | **NOT ATTEMPTED — contraindicated** | 0 syntax errors, 40/40 compile. Nothing to fix |
| Exemplar retrieval from solved pairs | **BLOCKED** | the 37 exemplars *are* the eval answers; using them leaks the goldens |

Two of these are worth more than their line. `near_misses` and description
inheritance were both *mechanistically correct* and both lost on measurement —
the effect was real and the side effect was larger. That is the failure mode
this kind of system produces most often.

---

## 3. Where the ceiling actually is

The residual — 20 golden cards no seed ever finds — is not one problem. It is
three, and they need different fixes.

### Class 1: the source encoding abstracts it away (the real ceiling)

```
Smuggler's Copter    K/Crew:   {}      ← empty node
Treasure Cruise      K/Delve:  {}      ← empty node
Kroxa                K/Escape: {}      ← empty node
```

Crew *means* "tap any number of creatures you control with total power N as a
cost". None of that is in the graph. Forge stores the keyword as an opaque
token and the semantics live in the word.

Corpus-wide:

| | |
|---|---|
| keyword (`K`) nodes | **18,199** — 15.0% of all 121,493 nodes |
| of those, **paramless** | **18,199 — 100%** |
| cards carrying ≥1 opaque keyword | **14,274 / 34,519 (41.4%)** |
| distinct opaque keywords | **252** |

**5 of the 20 residual cards (25%) are keyword-opaque.** No amount of mining
the graph recovers them, because the information was never in the graph.

This generalises, and it is the most transferable finding here:

> **A knowledge graph inherits its source's abstraction boundary. Wherever the
> source encoding uses a named macro instead of expanding it, the graph is
> blind — and users ask in terms of the expansion, not the name.**

### Class 2: taxonomy gaps (structure present, vocabulary missing)

```
Monastery Mentor   T/SpellCast  ValidCard: "Card.nonCreature"  → Token
```

The structure is entirely there. The question said "instant or sorcery"; the
card says `nonCreature`, which *subsumes* both. This is a missing subsumption
relation over param values, and it is **derivable from the corpus** — you can
compute which concrete types `Card.nonCreature` covers. Same family of problem
as the disjunctive families already mined, one level down.

### Class 3: the compiler simply chose wrong

Structure present, vocabulary present, query wrong. This is the class the
repair loop and the families block attack, and where the measured gains are.

### Why text doesn't rescue any of this

Of the 20 residual cards, BM25 ranks: **1 in top-30, 5 in 31–200, 7 in
201–2000, 7 beyond 2000 or absent entirely**. Smuggler's Copter and Monastery
Mentor are *absent*. The residual is by construction the set left over after
structure, which is also the set text is worst at. Embeddings would plausibly
rescue the 31–200 band (≈6 cards, e.g. "twice that many" ≈ "double"); they
cannot invent that Crew means tapping.

---

## 4. Does this need hand labelling?

**Yes, in two bounded places, and no in the place that would kill it.**

### It does NOT need per-example annotation

The thing that would make this uneconomic — labelling thousands of instances,
with the cost growing as the corpus grows — is not required, and this is
demonstrated rather than assumed. The largest measured accuracy win from a
derived artefact (**+9.8pp, p=0.017**) came from mining with **zero hand-written
families**. Param shapes, disjunctive families, the substitutability threshold
(chance = 1.0) and the anchor vocabulary were all derived. Adding a Forge set
adds mechanics automatically.

Where the project *did* hand-write, it lost: **all three documented
prompt-convention failures** come from hand-authored `DSL_SPEC` prose —
`landfall-payoffs` leaking Azusa, `flash-permission-static` leaking Quicken, and
the live "hook is narrower than the concept" failure. The repo's own lesson —
*don't add a convention where a fact could be mined* — is supported by every
measurement taken since it was written.

### It DOES need a bounded, one-time knowledge layer

Class 1 needs keyword→structure expansion. That is **252 entries, of which
perhaps 40–60 are procedural** (Crew, Delve, Escape, Flashback, Kicker,
Cycling, Equip, Morph, Ward…); the rest are labels like Flying where the name
*is* the meaning and no expansion is needed.

Crucially, **76% of the 252 have their definition already present in-corpus as
reminder text**:

```
Kicker     -> "You may pay an additional {2} as you cast this spell."
Flashback  -> "You may cast this card from your graveyard for its flashback cost. Then exile it."
Morph      -> "You may cast this card face down as a 2/2 creature for {3}."
```

So even the ceiling is substantially **mineable rather than authored**. This
has not been built or measured — it is the single highest-value untested lever,
and unlike everything else in §2 it targets a class the current system cannot
reach at all.

Cost profile: bounded, one-time, ~O(vocabulary) not O(corpus), and it does not
grow with new sets — a new set adds a handful of keywords, not thousands of
labels.

### It DOES need evaluation ground truth, and this is not optional

The expensive lesson of this project. With ~3 judged cards per question the
benchmark was **saturated**: across six runs, 19 questions passed every time,
16 failed every time, **only 2 verdicts ever changed**. Four rounds of work
were evaluated against an instrument with a dynamic range of two questions, and
it called a working intervention dead.

562 pooled, blind adjudications fixed it — seeds needed to resolve an effect
went **16 → 7**, and the intervention that had read as "not significant"
(+1.75pp, p=0.156) resolved at **+9.8pp, p=0.017** on the *same runs*.

Judgment cost is therefore real but **front-loaded and small** (562 items,
one afternoon) — and skipping it was more expensive than paying it.

> ⚠️ We have paid this for **recall only**. Doing the same for precision is
> unstarted, and §1 says that is where the product is losing.

---

## 5. What transfers

**The thesis holds.** Structured retrieval over an extracted graph beat lexical
retrieval by 60 points of witness recall and 8× precision on the cases where
wording and mechanics diverge — and it produces per-result provenance, which no
text method can. That is a real, replicated result, not a hope.

A team applying this elsewhere should expect:

**Prerequisites for it to be worth doing**
1. A machine-readable formal encoding of the domain (card scripts ↔ code ASTs,
   IaC, medical coding, legal citation graphs, CAD assemblies).
2. Questions whose answers are structural but whose *vocabulary* is not.
3. Demonstrable text failure on the discriminating cases — run the flat-RAG
   ablation **first**; ours took a day and would have killed the project
   cheaply if it had gone the other way.

**Costs you will pay, in the order they will hurt**
1. **Evaluation ground truth**, before any optimisation. Sparse goldens do not
   merely under-measure, they actively mislead. Pool from system disagreement
   and judge blind.
2. **A concept→structure layer.** Mining gets a real fraction (+9.8pp measured)
   and not all of it.
3. **Your source's abstraction boundary**, inherited whole. Find out early what
   fraction of your encoding is opaque macros — ours is 15% of nodes and 41% of
   documents. This is the number that sets your ceiling, and it is cheap to
   compute on day one.

**What will dominate your metrics regardless:** model capability. Haiku→Opus
was +7.5 questions; the best prompt-side intervention was +2.7. Budget for the
better model before budgeting for cleverness.

---

## 6. Open, in priority order

1. **Precision ground truth.** Same pooling machinery, pointed at returned
   cards rather than missed ones. Blocks any honest claim about product quality.
2. **Mine keyword expansions from reminder text.** 76% coverage available free;
   targets the 25% of the residual nothing else can reach.
3. **Remove the four hand-written `DSL_SPEC` conventions** and re-measure. Three
   documented failures trace to them; the instrument can now resolve it.
4. **Semantic re-ranking over structural results** — not a second retriever
   (measured: 1/20) but an ordering over what the graph already returned.
   Aimed at precision; preserves provenance.
5. Cross-kind families (`mode: Continuous` ↔ `api: PumpAll`), which a live user
   question hit within minutes of the server starting.
