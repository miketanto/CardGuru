# M3 — modes, events and chains, and a criterion that can be re-run

**Verdict: the criterion still does not clear — 6/9 on a fresh, disjoint slice
against Forge's 9/9. But the failure is now localised. The cost and target layer
is at near-parity (96–99% recall, 96–98% Jaccard); the mode layer is not. That
turns the recommendation from a card-level fallback into a field-level merge.**

## What M3 built

M2's emitter stopped at ability kinds, effect APIs, costs and target
restrictions — no `mode` field, no `R` nodes. M3 adds trigger modes, replacement
events with `Origin`/`Destination`, static modes, and chain edges.

Coverage was decided by a rule **written into the module docstring before any
production existed**: top 10 trigger modes, top 10 replacement events, top 15
static modes, by frequency rank — the same top-frequency-first order phase 1 §2
established. Nothing in or out because a question needed it. `Panharmonicon`
lands in scope at rank 14/81; `ReplaceToken` lands out at rank 95/191.

Holdout agreement (17,140 faces; developed on dev, dev→holdout gap ~0 as in
M0/M1):

| | precision | recall | exact set |
|---|---|---|---|
| trigger modes | 85.47 | 73.89 | 71.03% |
| static modes | 66.79 | 78.90 | 59.88% |
| replacement events | **96.46** | 81.66 | 75.60% |

Two emitter changes were needed. Api-less nodes are now emitted for *every*
ability line rather than only activated and triggered ones — static modes sat at
9.3% recall purely because S nodes were barely emitted. And `R:Moved` was
tightened to require the replacement construction rather than a bare "enters",
which took event precision from 61.0 to 96.3.

One production was tried and reverted: widening `CantBlockBy` to "can't be
blocked except by" cost 5 points of static-mode precision on dev. The docstring
records it so nobody re-tries it.

## The slice problem, and a structural fix

The triage burned a01–a05. A hand-authored replacement has a different problem:
written *after* the grammar, by someone who knows its weak spots.

So `eval/gen_adversarial_slice.py` generates slices by rule. Archetypes are
enumerated from the ontology by frequency; questions are template-filled;
**the witness is the highest BM25-ranked Forge match**; and — the part that makes
it adversarial without judgment — **the foil is the non-matching card whose
oracle text is closest to the witness's own text.** That produces
textually-similar/mechanically-different pairs mechanically. Doubling Season vs
Vorinclex, Monstrous Raider (doubles counters, not tokens) fell out of the
generator, not out of my head.

The generator also solves the burn problem structurally. A hand-written slice is
a one-shot resource and every fix-and-rescore cycle consumes one. A generated
slice is renewable: `SLICE_RANK_OFFSET` advances to the next band of frequency
ranks and yields a **disjoint** slice. v3 shares zero archetypes with v2. That
is what makes this criterion re-runnable at all.

## Results

Both slices were frozen and hashed before their first scoring run
(`research/data/adversarial_v2_freeze.txt`), per `plan/eval.md` §B rule 2.

| slice | oracle | forge | vacuous | mean recall of Forge hits |
|---|---|---|---|---|
| v2 (15 q, now spent) | 9/15 — **60.0%** | 15/15 | 2 | 71.6% |
| v3 (9 q, disjoint, post-fix) | 6/9 — **66.7%** | 9/9 | 2 | 63.0% |

v2's run surfaced two genuine code bugs, both fixed and validated corpus-wide
rather than on the slice:

- **Planeswalker loyalty costs never emitted a LOYALTY atom at all.**
  `LOYALTY_BRACKET_RE` is anchored on a trailing colon, but `cost_span()` splits
  on that colon before `cost_atoms()` is called — the pattern could never match.
  A dead code path, invisible until a question asked for it.
- **`R:Event$ Counter` is uncounterability** ("this spell can't be countered"),
  not a "would be countered" replacement. Recall 77.74 → 81.66.

## Where the failures actually are

Across both slices the pattern is the same, and it is not uniform weakness:

**Cost and target: 8 of 10 questions pass, and the passes are near-identical to
Forge.** v3's cost questions return 96.8–99.7% of Forge's hits at 96–98%
Jaccard. This is the layer M2 built and the triage fixed, and it now behaves like
a second derivation rather than an approximation.

**Modes: 2 of 5 pass.** The three v3 failures are precisely diagnosable:

| id | archetype | cause |
|---|---|---|
| b04 | `tapXType` cost atom | no production written — "tap two untapped creatures you control" as a cost is unimplemented |
| b06 | `Drawn` trigger mode | over-broad production: 721 hits vs Forge's 145, Jaccard 7.3% |
| b07 | `ChangesZoneAll` trigger mode | rank 11+ — **outside the stated top-10 rule**, so out of scope by design |

b07 is the coverage rule predicting its own limit, which is the point of stating
it in advance. b04 is missing vocabulary. Only b06 is a production that is
actively wrong.

## What this changes

The M2 verdict — hybrid, not replacement — stands, but it can now be stated more
usefully. The right unit of merge is **not the card, it is the field**:

- **Cost atoms and target restrictions**: merge-ready behind a `derivation` tag.
  Two independent derivations agreeing at 96–99% is a usable QA signal, and the
  fail-closed `ValidTgts` gate from the triage is already in place.
- **Modes and events**: Forge-only for now. 66–85% precision is not enough to
  feed a query layer that treats `mode` as an exact match, and the `Drawn`
  case shows how a single over-broad production poisons a whole archetype.

That is a better answer than "fallback for unscripted cards," and it is only
visible because the slice was regenerated rather than reused.

## Caveats

- **v3 is now spent too.** These results informed the diagnosis above; any fix
  aimed at b04/b06 must be scored on v4 (`SLICE_RANK_OFFSET=12`). The generator
  makes that cheap, but the discipline still applies.
- **The slices are small** (15 and 9 questions) and the questions are templated
  from Forge's internal vocabulary, so their wording is not natural language.
  They test cross-derivation fidelity on frequency-ranked archetypes, which is a
  weaker property than a01–a05's hand-crafted mechanics-vs-wording divergence. A
  genuinely natural-language adversarial set still wants RulesGuru or a human
  author who has not seen the grammar.
- **Pass/fail is harsh.** Several failures are witness misses on questions where
  bulk recall is high — v2's b06 missed its witness while returning 99.6% of
  Forge's hits. Mean recall of Forge hits is the softer and probably more
  informative number.
- The blocker is unchanged: `api.scryfall.com` is still 403 through the session
  proxy, so none of this yet parses a card Forge does not already cover.
