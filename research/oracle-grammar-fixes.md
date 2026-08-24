# Fixes — the six bugs, and what validating them honestly costs

**All six triaged bugs are fixed. On a corpus-wide holdout measure, sacrifice
cost-atom agreement went 52.4% → 78.3% and `{T}`-as-cost recall 91.0% → 99.9%.
The one number that went *down* went down on purpose.**

## What was fixed

The six bugs from `research/oracle-grammar-triage.md`, plus two more found while
validating:

| # | bug | cards | fix |
|---|---|---|---|
| 1 | missing effect production → no node emitted at all | 225 | emit an api-less node when a line is a recognisable ability but no production names its effect — the ability (and its cost) exists regardless |
| 2 | cost atom: `another/other X` not parsed | 135 | replaced the one over-clever `SAC_RE` with a noun-phrase parse: count → `another/other` → type list |
| 3 | cost atom: self-sacrifice by card name | 102 | exact match against the card name and its pre-comma nickname, plus `this <type>` / `it` |
| 4 | node ordering: `Counter` demoted to sub-ability | 44 | order APIs by match position in the *text*, not by `PRODUCTIONS` list order |
| 5 | post-nominal target restriction ignored | 18 | parse the span after "spell" and **fail closed** (below) |
| 6 | `CARDNAME` over-detected on type-named cards | 16 | use Magic's capitalisation convention — lowercase = card type, capitalised = subtype — instead of `card_name.startswith(...)` |
| 7 | sub-nodes inherited the Counter node's target params | — | scope `counter_targets` to the `Counter` node itself |
| 8 | selector formatting: `Foods`/`Islands`, `.Other` vs `+Other` | — | singularise bare subtypes; conjoin qualifiers with `+` as Forge does |

Bugs 2, 3, 6 and 8 were all one function. Bug 4 was one line — APIs were
appended in `PRODUCTIONS`-declaration order, so "Counter target spell. You gain
3 life." rooted the ability at `GainLife`.

## Validating this honestly

The triage burned a01/a04/a05 as a clean measure: the bugs were found by
inspecting those questions' disagreements, so rerunning them is debugging, not
scoring. `research/scripts/m2_param_agreement.py` therefore measures the same
fields over the **whole corpus** — every face, split dev/holdout by M1's stable
card-name hash — and reports the holdout half.

Holdout, 17,140 faces:

| measure | before | after |
|---|---|---|
| sacrifice cost atoms — precision / recall | 98.07 / 52.04 | 94.08 / **78.25** |
| sacrifice cost atoms — exact set agreement per face | 52.37% | **78.27%** |
| `{T}` in activation cost — precision / recall | 99.73 / 91.01 | 99.75 / **99.85** |
| Counter `ValidTgts` — exact set agreement | 76.47% | **73.30%** |
| Counter "is unrestricted" flag — precision / recall | 93.66 / 98.52 | **99.17** / 88.89 |

This is still not an independent confirmation of the M2 kill criterion, and
cannot be — it scores fields whose bugs were found via the burned slice. It
answers a narrower question: *do the fixes generalise beyond the ~700 cards that
motivated them?* On a holdout half of the full corpus, they do.

For the record, the diagnostic rerun on the burned slice: **697 → 96
disagreements**, a01's forge-only misses 330 → 25, a04's 256 → 4. That number is
debugging output. It is not a score and must not be quoted as one.

## The number that went down, and why that is correct

Counter `ValidTgts` exact agreement fell 76.47% → 73.30%. That is the fail-closed
rule working as designed. Bug 5's fix marks any *unrecognised* post-nominal
restriction as `.restricted` rather than leaving the target as a bare `Card`,
because a false "unrestricted" is the Disdainful Stroke failure — `answers.py`
reads `ValidTgts` as a stack restriction, so it would produce a
confidently-wrong answer rather than a mis-ranked one.

The trade shows up exactly where it should: **false "unrestricted" claims fell
from 9 to 1**, at the cost of 15 cards now marked restricted that Forge calls
unrestricted. Over-restriction causes under-retrieval; under-restriction causes
confidently-wrong answers. `plan/eval.md` §B is unambiguous about which to
prefer.

## An unexpected result: the grammar is sometimes right and Forge is wrong

Inspecting those 15 "over-restrictions" turned up something the triage did not
predict. Most of them are not errors:

```
Dispersal Shield   Counter target spell if its mana value is less than or equal
                   to the highest mana value among permanents you control.
Ertai's Trickery   Counter target spell if it was kicked.
Hindering Light    Counter target spell that targets you or a permanent you control.
Jaded Response     Counter target spell if it shares a color with a creature you control.
```

Forge emits `ValidTgts: Card` — unrestricted — for every one, because it
implements the condition elsewhere in its data model rather than in the target
selector. **None of these can counter any kind of spell.** On a05's actual
question — "counterspells that can counter any kind of spell" — the oracle
grammar is the more correct of the two derivations.

This is the first solid instance of M1's "implementation ontology, not rules
ontology" thesis appearing as a case where the grammar *wins*. The triage
concluded the grammar was not yet good enough to audit Forge, and at 95.4%
grammar debt that was right. Post-fix, the balance has shifted: of 96 remaining
disagreements, 32 are Forge/query artifacts and only 23 are grammar debt. The QA
framing is not yet earned, but it is no longer refuted.

Only one of the 15 was a genuine false positive — Fuel for the Cause ("Counter
target spell, then proliferate"), where a trailing continuation clause was read
as a restriction. Fixed in bug 8's pass.

## Status

Unchanged where it matters: **hybrid, not replacement.** The M2 verdict stands
because nothing has re-tested it, and nothing can until there is a fresh
adversarial slice. What has changed is that the grammar's parameter layer is now
worth merging behind a `derivation` tag, and the correctness gate on bug 5 is
closed — oracle-derived `ValidTgts` no longer asserts that Disdainful Stroke
counters anything.

Next, in order:

1. **A fresh adversarial slice** (`plan/eval.md` §B rule 2 — "any later change is
   a new benchmark version"), then rerun M2's criterion honestly.
2. **`derivation: "script"` on the Forge path** in `cardguru/dataset.py`, so both
   derivations are distinguishable in one dataset.
3. **M3** — `R` nodes with `Event$`, static modes, real chain edges — still the
   work that would let a02/a03 pass at all.

The blocker is unchanged: `api.scryfall.com` is still 403 through the session
proxy, so the grammar has nothing to parse that Forge does not already cover.
Everything above is preparation.
