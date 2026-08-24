# M1 — can oracle text recover the Forge effect-API vocabulary?

**Verdict: 83.4% precision / 76.9% recall on a held-out half, with a
dev→holdout gap of 0.56 points.** Twelve APIs are already at ≥90/90. The
grammar generalises; the remaining error is concentrated and named. Proceed to
M2, which is where the real risk lives.

## Method, and one correction to M0

M0 (`research/oracle-grammar-m0.md`) developed its productions against the same
34,156 faces it scored. That number was therefore optimistic by an unknown
margin. M1 fixes the methodology: faces are split into **dev** and **holdout**
halves by a stable hash of the card name, every production was written while
looking only at dev, and the headline number is the holdout.

- **Predictor input:** oracle text + type line.
- **Ground truth:** the set of `api` values over *all* nodes of a face — ability
  roots and SVar sub-abilities alike — minus the control-flow APIs in
  `NON_TEXTUAL`.
- **Unit:** one face, scored as set precision/recall over APIs.

Sets, not multisets: M1 asks whether the grammar can *name* the effects, not yet
how many times each fires. Counting belongs to M2.

**Excluded as non-textual** (14 APIs): `Cleanup`, `Charm`, `Effect`,
`DelayedTrigger`, `ImmediateTrigger`, `RepeatEach`, `Repeat`, `Branch`,
`GenericChoice`, `StoreSVar`, `NoteCounters`, `InternalHaunt`, `Pull`,
`DebugTargets`. These are engine control flow and bookkeeping with no verb of
their own in oracle text — `Cleanup` (2,979 instances) and `Charm` (784) never
once appear as a face's only API. Scoring against them would measure the wrong
thing. This exclusion is itself a finding: **5% of all API instances in the
corpus are engine scaffolding rather than card semantics.**

```bash
python3 research/scripts/m1_effect_verbs.py data/dataset.jsonl.gz \
    research/data/m1_effect_verbs.json            # holdout (default)
python3 research/scripts/m1_effect_verbs.py data/dataset.jsonl.gz --split dev
```

## Results

| split | faces | exact API-set match | micro precision | micro recall |
|---|---|---|---|---|
| dev | 17,180 | 65.15% | 83.79% | 77.52% |
| **holdout** | **16,976** | **64.59%** | **83.35%** | **76.90%** |
| gap | | 0.56 pp | 0.44 pp | 0.62 pp |

**The 0.56-point generalisation gap is the most important number here.** Three
rounds of production-writing against dev (exact 54.6% → 58.9% → 65.2%) bought
almost exactly as much on data never looked at. The productions are capturing
real templating regularity, not memorising cards. That is the property a grammar
needs and the one a corpus-tuned heuristic usually lacks.

Holdout, APIs with support ≥ 100:

| api | support | recall | precision |
|---|---|---|---|
| ChangeZone | 2,791 | 87.3 | 81.9 |
| Pump | 2,206 | 72.7 | 74.5 |
| Draw | 1,781 | **99.6** | **97.4** |
| Token | 1,651 | **99.5** | 91.4 |
| PutCounter | 1,553 | 84.5 | 89.6 |
| DealDamage | 1,284 | **99.9** | 76.3 |
| Mana | 1,088 | **95.8** | **95.8** |
| GainLife | 821 | **99.6** | **95.1** |
| Tap | 741 | **91.9** | **97.7** |
| Destroy | 724 | 94.3 | 79.9 |
| LoseLife | 555 | **99.6** | **99.1** |
| Discard | 546 | 91.8 | 80.8 |
| PumpAll | 523 | 74.0 | 89.2 |
| Animate | 463 | 35.9 | 76.1 |
| Dig | 452 | 93.8 | 76.5 |
| Sacrifice | 397 | 71.3 | 49.7 |
| ChangeZoneAll | 301 | 40.9 | 93.9 |
| Mill | 278 | **96.8** | **99.6** |
| Counter | 253 | **92.1** | **99.6** |
| Untap | 236 | 63.1 | 70.3 |
| Scry | 212 | **99.1** | **100.0** |
| ChooseCard | 190 | 5.8 | 19.6 |
| DamageAll | 190 | 86.3 | 55.8 |
| CopyPermanent | 181 | 47.0 | 51.2 |
| DestroyAll | 180 | 82.2 | 98.7 |
| GainControl | 166 | 0.0 | — |
| SetState | 162 | 79.6 | 95.6 |
| PutCounterAll | 148 | 0.0 | — |
| Play | 148 | 63.5 | 32.1 |
| Regenerate | 134 | **100.0** | **98.5** |
| CopySpellAbility | 127 | 0.0 | — |
| Attach | 123 | **99.2** | **96.8** |
| Surveil | 111 | **100.0** | **99.1** |

**12 of 33 APIs are at ≥90 recall *and* ≥90 precision.** Three more
(`GainControl`, `PutCounterAll`, `CopySpellAbility`, 441 instances between them)
score zero for the simple reason that **no production was written for them** —
they are gaps in a 60-production lexicon, not failures of the approach.

## What the error actually is

Two findings worth separating from ordinary grammar debt.

**1. Forge's structural choices, not the text, drive the two worst APIs.**
`Pump` and `ChangeZone` — the two largest, together 21% of instances — are
precisely the two APIs `research/phase1-cardscripts.md` §6 named as conflated:
"`DB$ ChangeZone` conflates destroy-and-reanimate, bounce, tuck, exile; `Pump`
covers both P/T changes and ability grants." Their scores (74.5 and 81.9
precision) are the lowest of any high-support API, and the reason is that one
API answers to many unrelated English constructions.

The sharpest instance found while iterating: a P/T change is a `Pump` node only
when it is *one-shot*. "Creatures you control get +1/+1" — a continuous boost —
is an `S:Mode$ Continuous` static carrying `AddPower$`/`AddToughness$` params
and **no api at all**. Same English verb, same semantics to a player, different
side of Forge's data model. Requiring a duration on the pump productions moved
dev precision from 55.6% to 83.8% in a single change. The grammar was not
wrong about the text; it was wrong about Forge.

**2. The cost/effect split is implemented and works.** Effect verbs are matched
only against the *effect* span of a line, never the cost span — everything left
of an activated ability's colon and a triggered ability's event clause is
stripped first. This is the a01 distinction from
`research/graph-vs-flat-ablation.md` that BM25 structurally cannot make.
`Sacrifice` at 71.3/49.7 is the honest read on how well it currently works:
better than lexical retrieval, not yet good enough, and the residual is
mis-detected cost boundaries rather than a missing concept.

## What M1 does not show

- **It does not clear M2.** M1 asks whether the grammar can *name* effects.
  M2 asks whether it can recover the parameters that decide search results:
  cost-vs-effect at the *node* level, `ValidTgts` restrictions, and chain
  edges. a05 ("counter target spell **and nothing more**") is a `ValidTgts`
  question and nothing in M1 touches it.
- **Set-level scoring hides counting errors.** A face with two `Draw` nodes and
  one predicted scores as a hit.
- **Adjudication is still untouched.** A parsed new card is searchable, not
  playable.
- **The pre-committed M2 kill criterion stands unchanged:** rerun
  `research/graph-vs-flat-ablation.md`'s adversarial slice against the
  oracle-derived graph. Hold near 5/5 witness recall and the grammar is a
  genuine second derivation; fall short and it is a labelled fallback for
  unscripted cards only.

## Recommendation

Proceed to M2, and treat it as the real decision point. M1's job was to find out
whether effect templating is regular enough to be worth grammar effort; a
0.56-point generalisation gap says yes. But M1 measured the easy half of the
question, and the two APIs that scored worst are the two that carry the most
weight in mechanical search.

Cheap work available first, if wanted: the three zero-scoring APIs need one
production each, and `ChooseCard` / `CopyPermanent` / `Untap` are ordinary
lexicon debt. None of it changes the M2 verdict, so it should not precede M2.

