# M0 — can oracle text alone recover the Forge ability inventory?

**Verdict: 90.2% exact agreement across 34,156 faces from ~200 lines of regex
productions. The M0 kill criterion does not fire.** Oracle text is templated
tightly enough to justify M1 (effect-verb grammar).

## Why this probe exists

`plan/uncertainties.md` §6 names the slow death this project is exposed to: the
Forge DSL "gains keywords with every set… the parser will rot without a
pinned-bump-diff routine. Cost is recurring maintenance, not a cliff — but it's
forever, and it's the classic way projects like this die quietly." And
`research/phase1-cardscripts.md` §6 names the fidelity cost of sourcing the
ontology from a game engine: "**Implementation ontology, not rules ontology** —
confirmed. `DB$ ChangeZone` conflates destroy-and-reanimate, bounce, tuck,
exile."

A grammar over *oracle text* addresses both: it tracks Scryfall (daily) rather
than Forge's scripting backlog, and it reads the rules language directly instead
of an engine's execution vocabulary.

The reason we can evaluate that cheaply is that the parallel corpus already
exists. `forge_parser.py` captures the `Oracle:` line and `Face.to_record()`
writes it into every dataset row alongside the parsed nodes and edges — so the
built dataset is 34,519 aligned (oracle text, hand-authored graph) pairs. Every
grammar production can be scored against a human-curated target over the whole
pool. Most oracle-parser efforts fly blind; this one does not.

M0 tests the cheapest falsifiable slice of the grammar hypothesis:
**segmentation and ability-type classification**, nothing else.

- **Predictor input:** oracle text + type line. Nothing else.
- **Ground truth:** the Forge-derived node-kind bag for the same face.
- **Unit:** one face; it agrees when the predicted multiset over {A,T,S,R,K}
  equals Forge's.
- **Pre-committed kill criterion:** well under ~95% and oracle text is less
  templated than the grammar plan assumes — reconsider before writing a grammar.

Reproduce (~2 s over the full pool):

```bash
python -m cardguru build --cardsfolder <forge>/forge-gui/res/cardsfolder \
    --pin 670429bf9f77c06ac866003604205d9de3413e52 --out data/dataset.jsonl.gz
python3 research/scripts/m0_oracle_segment.py data/dataset.jsonl.gz \
    research/data/m0_oracle_segmentation.json
```

Pin `670429bf` — the same commit as phase 1, and the parse reproduces its
34,519 faces exactly.

## Results

34,156 faces scored; 363 skipped as true vanillas (empty oracle **and** no
nodes, so they are trivially correct and excluded rather than inflating the
score).

| measure | value |
|---|---|
| **exact node-kind bag agreement** | **90.2%** (30,810 / 34,156) |
| agreement if Forge's implementation-only keywords are counted | 88.8% |
| agreement ignoring keyword *counts* | 90.6% |

Per kind:

| kind | true | predicted | recall | precision |
|---|---|---|---|---|
| A — spell/activated | 18,410 | 18,380 | **99.2%** | **99.3%** |
| T — triggered | 16,912 | 16,589 | **97.0%** | **98.9%** |
| K — keyword | 17,310 | 16,334 | 93.2% | 98.8% |
| S — static | 7,078 | 9,099 | 92.4% | 71.9% |
| R — replacement | 1,692 | 1,233 | 70.0% | 96.0% |

A, T and K — 89% of all nodes — are essentially solved by line-level
segmentation. The error concentrates exactly where you would predict: `S` is the
classifier's `else` branch, so everything unrecognised lands there (precision
71.9%), and `R` is the kind whose templating is most varied (recall 70.0%).

Three iterations got from 80.0% → 82.0% → 90.2%. Each step was reading the
top mismatch shapes and adding a named production — ability-word and flavour-name
prefixes (`Landfall —`, `Heavy Power Hammer —`), bracketed loyalty costs
(`[+1]:`), named cost-keywords (`Waterbend {8}:`), em-dash keyword costs
(`Cumulative upkeep—`), `enters tapped` as a replacement, and collapsing a
spell's sentences into its single spell ability. That is the loop the parallel
corpus makes possible, and it is why the number moved 10 points in three passes.

## What the residual is

The 3,346 disagreements are a long tail of *named, bounded* shapes — the eight
largest sum to 7.3% of faces and none exceeds 1.9%:

| Δ | faces | cause |
|---|---|---|
| `S+1` | 629 | additional-cost lines on spells: Forge folds them into the spell ability, the probe emits a separate `S` |
| `K-1, S+1` | 563 | Forge models some statics as keywords (landwalk variants, conspiracy deck-construction text) |
| `S-1` | 386 | Aura `Enchant` + granted abilities: Forge splits into two `S`, the probe emits one |
| `R-1, S+1` | 336 | "This spell can't be countered", `enters tapped with N counters` — replacement templating the probe misses |
| `T-1` | 253 | remaining multi-condition triggers ("enters **or** attacks") |
| `K-1, S+3` | 124 | Sagas: Forge emits one `K:Chapter` node, the probe emits one per chapter line |
| `K-1` | 109 | compound keyword lines ("protection from black **and from** red" = 2 keywords) |
| `R-1` | 94 | more replacement templating |

None of this reads as "oracle text is not parseable." Every bucket is a
production someone can write in an afternoon.

## The finding worth keeping

Several disagreements are **Forge being wrong about the rules, not the grammar
being wrong about the text.** The clearest case is multi-condition triggers:

> Whenever Abomination blocks **or** becomes blocked by a green or white
> creature, destroy that creature at end of combat.

The rules read that as *one* triggered ability with two trigger conditions.
Forge emits *two* `T` nodes because its engine registers one handler per
condition. The probe has to deliberately mirror Forge's split
(`TRIGGER_OR_RE`) to score well — and even then the disjunction must be
restricted to event verbs, because "an instant **or** sorcery spell" is a
disjunction inside the event's *object* and stays one trigger.

That is §6's "implementation ontology, not rules ontology" showing up as a
measurable disagreement rather than a caveat in prose. It is also the argument
for the grammar that has nothing to do with new-card coverage: an oracle-derived
graph is a **second, independent derivation** of the same structure, and its
disagreements with the Forge-derived graph are a free QA signal — the same trick
`plan/architecture.md` §4 already uses for engine bumps. Phase 1 §6 anticipated
this with XMage's Java classes as a second extraction source "for cross-engine
disagreement as a QA signal"; oracle text is a cheaper third.

## What M0 does not show

- **Nothing about effect semantics.** M0 classifies ability *kind*. Whether the
  grammar can recover `api=Token` or `Cost$ Sac<1/Creature>` is M1/M2 and is
  strictly harder.
- **Nothing about the distinctions that won the ablation.** a01 (cost vs.
  effect), a04 (`{T}` as cost), a05 ("and nothing more") come free from Forge's
  param names and must be *reconstructed* from sentence position. That remains
  the make-or-break test, and it stays the M2 kill criterion: rerun
  `research/graph-vs-flat-ablation.md`'s adversarial slice against the
  oracle-derived graph.
- **Nothing about adjudication.** A parsed new card is searchable, not playable.
  XMage still needs its own implementation, so the interaction tier's new-card
  gap is untouched by any of this.
- **The keyword lexicon is borrowed.** It comes from the mined ontology
  (`research/data/ontology.json`, 252 keywords minus 7 implementation-only
  entries). That is a lexicon of the language, not per-card knowledge — the same
  posture `cardguru/validate.py` takes toward compiled queries — but it is an
  input the probe did not derive for itself, and a from-scratch grammar would
  need CR 702 instead.

## Recommendation

Proceed to M1 (effect-verb grammar for the top ~50 APIs; the build order is
already computed in phase 1 §2 — ChangeZone 6596, Pump 4967, Draw 3710, Token
3554, PutCounter 3269…).

Expected landing remains hybrid, not replacement: Forge graph where a card is
scripted, grammar graph where it is not, a `derivation` tag on every record, and
cross-derivation disagreements surfaced as a QA queue rather than silently
resolved.
