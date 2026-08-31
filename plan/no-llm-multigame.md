# CardGuru without an LLM backend — and as a multi-game search API

Design note answering two coupled questions:

1. What does CardGuru look like with **no LLM at serving time** — just graph + semantic?
2. Can that shape become a **per-game search-helper API** (MTG, Riftbound, One Piece, …),
   each game carrying its own graph and its own embedding space?

Short answers: (1) it looks like almost exactly what already exists — the LLM is 3.6% of the
package and sits on one command; (2) yes for the *engine*, but the cost per game is entirely
"where does the ability graph come from," and it must be paid game by game against a
pre-committed ablation, not assumed.

## 1. How much LLM is actually in here today

Measured, not estimated:

| layer | modules | lines | LLM? |
|---|---|---|---|
| NL compiler | `nl_compiler.py` | 201 | **yes — the only one** |
| Graph engine | `querydsl`, `index`, `dataset`, `validate`, `induction`, `gaps` | 883 | no |
| Data adapter | `forge_parser` | 236 | no |
| Adjudication | `adjudicate` + JVM driver | 98 | no |
| Game knowledge | `recommend`, `answers`, `deck`, `fingerprint`, `intuition`, `goldfish`, `threats`, `cite` | 3,459 | no |
| CLI | `cli` | 661 | one subcommand (`ask`) |

**5,343 of 5,544 lines never call a model.** Every product surface that exists — `search`,
`answers`, `deck`, `fingerprint`, `threats`, `windows`, `gaps`, `recommend`, `adjudicate` — is
deterministic Python over the ability graph. Deleting `nl_compiler.py` costs exactly one thing:
free-form natural language in the front door.

So "no LLM backend" is not a rewrite. It is a question about **what replaces the NL front
door**, and nothing else.

## 2. Three replacements for the NL front door

### (a) Don't replace it — ship the DSL as the API

For a *search-helper API for developers*, natural language is not the product. Scryfall's moat
is a query syntax, not a chatbot. The DSL is already better than a syntax: closed-vocabulary,
validated (`validate.py` rejects out-of-ontology tokens before execution), and
evidence-returning (`index.explain` renders the matched subgraph). An API consumer wants
determinism, latency and zero per-call vendor cost — all three of which the LLM path removes.

This is the cheapest option and probably the correct default for the API positioning.

### (b) Semantic ontology binding — embeddings instead of a compiler

The compiler's real job is **lexical grounding**: mapping "sacrifice a creature to add mana"
onto `api: Mana` + `Cost` regex `Sac<1/Creature`. The target vocabulary is closed and small:

```
191 effect APIs · 137 trigger modes · 138 static modes · 34 replacement events
252 keywords · 1,206 param keys · 207 count functions
```

Embed each token with a short human gloss, embed the query, take nearest neighbours. That is
pre-LLM semantic parsing over a closed vocabulary, and it works here precisely because the
vocabulary is closed and Zipfian (phase 1's finding).

What embeddings **cannot** give you is *structure* — `chain` vs `node` vs `all/any` — or idiom
knowledge ("ETB = `ChangesZone` + `ValidCard: Card.Self` + `Destination: Battlefield`"). That
needs a **template bank**: parameterized query patterns with canonical phrasings and typed
slots. Retrieval picks the template; embedding + string match fills the slots.

The bank is already half-written and not currently recognized as one:

| existing source | count |
|---|---|
| `recommend.HOOKS` detectors + complement queries | 29 hooks / 31 complement blocks |
| `answers.ANSWER_QUERIES` | 9 |
| `benchmark/benchmark.json` | 20 |
| `queries/*.json` | 3 |
| eval dev set + adversarial slice | 25 |

~85 hand-authored, hand-labeled queries with NL descriptions attached. That is a seed corpus
for template retrieval, and it grows for free every time a hook or answer class is added.

**Honest accuracy expectation:** templates cover the head of a Zipfian question distribution
and fail on arbitrary composition, which is exactly what the LLM was good at. Mitigation is
already in the product design — `plan/product.md` wants the compiled query *shown to the user
before running* ("the compiled query is a feature"). A template match with a visible, editable
query and a confidence label degrades honestly; a wrong LLM compile does not.

### (c) Structural embeddings — where "semantic" actually earns its place

The differentiated move is not embedding card *text*. It is embedding card *structure*.

`rl/e2_extract.py:face_vector` already produces a 62-dimension pure-graph feature vector
(answer classes, effect APIs, keywords, trigger shapes, target classes, type flags) with — its
own docstring — "no text embeddings, no learned components." Promote that to a first-class card
embedding (feature vector + bag-of-subgraphs, or node2vec/GNN over the ability graph) and query
modes open up that text retrieval structurally cannot serve:

- **Functional more-like-this.** "Cards that play like Anointed Procession." The ablation
  already proved the point negatively: Procession's oracle text never contains "double" (it
  says "twice that many"), so BM25 ranks it 21st, below mana doublers. Structure ranks it first.
- **Search by example** — hand the API a card ID instead of a query string. No parser, no NL, no
  vocabulary problem. For an API product this is the single highest value-per-line endpoint.
- **Cross-game analogy** (see §4) — nearest neighbours *across* corpora in a game-neutral
  structural space.

### What semantic embeddings will *not* fix

Worth stating plainly because it is the most likely design error here: swapping BM25 for dense
text embeddings does **not** recover what the graph provides. `research/graph-vs-flat-ablation.md`
measured flat text at 2/5 witness recall on the adversarial slice, and every one of its failures
is structural rather than lexical:

- cost-vs-effect sacrifice — the same words on both sides of the colon;
- `{T}` as a cost vs "tap" as an effect — the cost is a symbol, not a word;
- "counter target spell" being a *substring* of "counter target creature spell" — lexical
  retrieval cannot express "and nothing more";
- token doubling phrased as "twice that many".

Dense embeddings move the text-friendly dev number a little and the adversarial number roughly
not at all. **Semantic is a recall tier; the graph is the precision tier.** They compose; they
do not substitute.

## 3. The resulting architecture

```
                  ┌ attribute filters ──► card store (SQL)                 ┐
 query ─► router ─┼ text tier ──────────► BM25 + dense embedding (recall)  ├─► graph
 (or card id,     ├ template match ─────► parameterized DSL query          │   evaluator
  or DSL direct)  └ card-as-query ──────► structural kNN over graph vectors ┘   (exact,
                                                                                evidence)
                                    ─► ranked results + machine-readable WHY
```

Router is a scored fan-out, not a classifier: run the cheap tiers in parallel, union with
provenance labels, rank. `plan/architecture.md` §2 already argues misroutes between attribute
and mechanical are low-stakes and millisecond-cheap — that argument holds *better* without an
LLM, because there is no per-call cost to running all tiers every time.

Properties: deterministic, cacheable, offline-capable, no API key, no vendor bill, sub-second,
and every result still ships the matched subgraph as proof.

**What is genuinely lost, stated honestly:**

1. Arbitrary compositional NL. Templates cover the head; the tail degrades to text search.
2. NL scenario compilation for the Judge surface. Board states become a structured builder UI.
   (The adjudicator itself never used a model.)
3. Answer *narration*. `plan/architecture.md` §1.7 assigns the LLM the job of narrating an
   engine result. Without one, WHY strings are templated from evidence — which `index.explain`
   and the hook WHY strings already do.

None of the three is load-bearing for a search API. All three are load-bearing for a consumer
chatbot. That is the real fork in the road.

## 4. Multi-game

### The honest core

CardGuru's power is not the graph algorithms. It is **Forge**: 34,519 faces, 98.9% scripted, a
hand-authored machine-executable card DSL accreted by volunteers over two decades. The Python
in this repo is a few thousand lines that would port in days. The Forge equivalent for Riftbound
and One Piece **does not exist**. The entire multi-game question reduces to: *where does each
game's ability graph come from?*

### Three source tiers

**Tier 1 — a scripted engine exists.** MTG (Forge). Pokémon has a real analog in TCG ONE's
card-implementation repo. Parse and go; this is the proven path.

**Tier 2 — structured card data plus heavily templated text.** One Piece and Riftbound both have
open card APIs (OPTCGAPI ~4,347 cards / 51 sets; apitcg covering both; Riftcodex, RiftScribe and
Scrydex for Riftbound). These give text, not structure — but the text is far more templated than
MTG's. One Piece prints its *trigger taxonomy on the card face* as bracket tags: `[On Play]`,
`[When Attacking]`, `[Activate: Main]`, `[On K.O.]`, `[Trigger]`, `[Blocker]`, `[Rush]`,
`[End of Your Turn]`. That is a machine-readable trigger label already — the `T`/`A`/`S`/`R`/`K`
node kinds fall straight out of the brackets with essentially no NLP. Only the effect side needs
a grammar, and the effect vocabulary of a 4,300-card game is a fraction of MTG's over 34,519.

A hand-built PEG/regex grammar is tractable at that scale, and unlike MTG it can plausibly reach
high coverage. **Coverage must be measured before betting** — the same discipline phase 1 used
when it measured 98.9% scripted before committing to Forge.

**Tier 3 — nothing structured.** Then extraction is genuinely a language problem, and the right
tool is a model — **at build time, once per card, offline, human-reviewable, frozen and diffed
per set release.** This is the distinction worth holding onto: *"no LLM backend" constrains the
serving path, not the ingest pipeline.* A one-time batch extraction over 4,000 cards produces a
static artifact; the API that serves it stays deterministic, free and offline. If the "no LLM at
all" constraint is about cost, latency and determinism, tier 3 satisfies it. If it is about
having no model dependency anywhere, tier 3 is out and only tiers 1–2 are eligible.

### What has to become per-game

The record format is the strongest asset here: `{kind, api, apiKind, mode, params, edges}` is
already game-neutral. The vocabulary inside it is not.

| component | today | multi-game shape |
|---|---|---|
| `forge_parser.py` | Forge DSL | `adapters/<game>/parser.py` → same record |
| `research/data/ontology.json` | mined from Forge | per-game mined ontology, same miner |
| `validate.py` | generic, but `KINDS`/`API_KINDS` hardcoded | move those constants into the ontology file |
| `querydsl`, `index`, `dataset`, `induction`, `gaps` | already generic | unchanged — this is the platform |
| zone/timing model | MTG zones inline | zones as data (One Piece: Life/DON!!/Trash/Cost Area; Riftbound: Battlefields/Runes) |
| `recommend`, `answers`, `deck`, `fingerprint`, `threats`, `intuition`, `goldfish` | 3,345 lines of MTG knowledge | per-game plugin; a few hundred lines each |
| `adjudicate` + XMage | MTG only | **cut from the multi-game product** |

That last row is a real scope cut and should be stated up front: there is no XMage for One Piece
or Riftbound. The multi-game product is **search + structure + recommendation**. Rules
adjudication stays an MTG-only premium tier.

Shared platform across games: record format, postings index, DSL evaluator, ontology
miner + validator, evidence/explain, structural vectors and kNN, decklist analysis skeleton, and
the eval harness — with `eval/flat_baseline.py` run as a mandatory control for every new game.

### The commercial caveat

The moat per game is proportional to **how much structure text search misses**. MTG is the
extreme case: thirty years of accreted mechanical complexity where Scryfall's `o:` regex
genuinely fails. One Piece is a much simpler game — short card text, few effect types, ~4,300
cards. A competent text search may already answer 90% of what its players ask, which makes the
graph's *marginal* value lower there even though the graph is easier to build.

So the go/no-go per game is not "can we build the graph" but "does the graph beat text." The
repo already owns the right instrument and the right pre-commitment.

### Kill criterion (per game, pre-committed)

Reusing `plan/eval.md` §D verbatim, applied per game:

> Build a 5–10 question adversarial slice for the game (each question carrying a witness that
> must be found and a textually-similar, mechanically-wrong foil that must not be). Run BM25
> over that game's card text as the control. **If graph retrieval does not beat flat text by
> ≥5 points of witness recall on that slice, do not build the graph tier for that game** — ship
> the text tier plus structural kNN and move on.

MTG cleared this by +60 points. No other game gets a free pass on MTG's result.

## 5. Staging

1. **Cut the serving-path LLM dependency.** Add `search-by-example` (structural kNN over
   promoted `face_vector`) and a template-retrieval front door over the ~85 existing labeled
   queries. Keep `ask` as an optional extra, not a dependency.
2. **Prove game-neutrality with a second game before generalizing the framework.** Pick the
   tier-2 candidate with the best-measured text templating. Write its adapter against the
   existing record format and run the ablation *before* porting any knowledge layer.
3. **Only if step 2 clears the kill criterion**, extract the plugin boundary — adapters,
   per-game ontology, zones-as-data, knowledge-layer plugin API.
4. **The cross-game structural embedding is a research bet, not a given.** "Find One Piece's
   Counterspell" is a genuinely novel API that nobody ships, and it depends on a game-neutral
   node taxonomy being real rather than aspirational. Probe it on two games before pricing it.
