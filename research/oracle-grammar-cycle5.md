# Cycle 5 — auditing productions against card text, not mode names

**One production in the whole table was authored from a Forge mode's *name*
rather than from any card's wording. Finding it required a new kind of check;
repairing it and four others like it moved holdout trigger-mode agreement to
93.72/81.44.**

## The audit

Cycle 4 found `AttackersDeclared` written as `attackers are declared` — a phrase
no card contains. 127 cards, zero matches, and no aggregate measure caught it
because recall averaged it away across the other nine modes.

`research/scripts/m3_production_audit.py` checks the whole table the same way,
mechanically: for each mode, take the dev-half faces Forge assigns it, and ask
whether the production matches. For the misses, surface the most distinctive
phrases so the repair can be written **from the cards**.

The result was reassuring and specific — of everything in scope, exactly one
production was dead:

| mode | cards | before | after | what the cards actually say |
|---|---|---|---|---|
| `AttackersDeclared` | 127 | **0.0%** | **83.5%** | "whenever you attack", not "attackers are declared" |
| `Drawn` | 74 | 44.6% | **97.3%** | "draw **your second card each turn**" |
| `CantBeCast` | 47 | 10.6% | **76.6%** | active voice — "your opponents can't cast spells" |
| `CantBeActivated` | 17 | 23.5% | **76.5%** | "activated abilities of … can't be activated" |
| `CantBlockBy` | 198 | 32.8% | 52.0% | "can't be blocked **except** by", "can block only" |

Everything else the audit flagged as "no production" — `TurnFaceUp`,
`Sacrificed`, `Taps`, `BecomesTarget` and twenty more — is below the top-10 rank
cut and therefore out of scope by M3's stated rule, not a defect.

`CantBlockBy` is worth a note: "except by" / "can block only" were tried in cycle
3 and *hurt* precision, so they were removed with a comment saying so. Re-tried
after the emitter started taking its kind from M0's classifier, they now help.
The comment has been corrected rather than deleted — the earlier result was real,
it just no longer holds.

## A wrong assumption, found by following a number

v6's `SubCounter` question returned 334 of Forge's 654. The loyalty fix from
cycle 3 had taken that from 0, so it looked like partial success. It was not:
the remaining misses are not planeswalkers at all.

> `{1}, Remove a fade counter from it:` … `Remove three charge counters from this Vehicle:`

Forge's `SubCounter` cost covers **any** counter-removal cost, not just loyalty —
`SubCounter<1/P1P1>`, `SubCounter<1/CHARGE>`, `SubCounter<3/LOYALTY>`. The cycle-3
fix was correct and the assumption behind it ("SubCounter means loyalty") was
wrong. Adding the general form:

| counter-cost atoms (holdout) | precision | recall |
|---|---|---|
| `AddCounter` / `SubCounter` | **96.7%** | **89.6%** |

## Holdout after this cycle

| | precision | recall | exact set |
|---|---|---|---|
| trigger modes | **93.72** | **81.44** | **79.49%** |
| static modes | 71.45 | 81.94 | 65.31% |
| replacement events | 89.13 | 80.39 | 77.58% |
| sacrifice cost atoms | 94.18 | 78.25 | 78.27% |
| `{T}` in activation cost | 99.75 | 99.75 | — |
| counter cost atoms | 96.70 | 89.60 | — |

Trigger modes across the last three cycles: 85.47/73.89 → 92.87/80.10 →
**93.72/81.44**, exact set 71.03% → 78.07% → **79.49%**.

## The slices have changed role, and should be relabelled

Two things have happened to the generated-slice mechanism:

1. **In-scope archetypes are spent.** Every archetype in the head of the
   frequency distribution has now appeared in v2, v3, v5 or v6, and their
   failures have informed fixes.
2. **Yield collapses on the remaining axis.** Witness-rank offsets produce 10,
   14, 10, 8, 4 and 7 questions at offsets 0–5. v6 yielded four questions — too
   few to carry a verdict.

So the honest position: **the corpus-wide holdout measures are the trustworthy
number now, and the slices have become a small regression suite.** That is a
useful role — v6 scored 3/4 with mean recall 80.9%, and `AttackersDeclared` went
from 0 hits to 208 of Forge's 233, which is exactly the regression signal you
want — but it is not the role a kill criterion needs.

A criterion that can carry a verdict again needs a source of questions this work
has not touched: RulesGuru (held out by `plan/eval.md` §B rule 1 and still
unread), or a human author who has not seen the grammar.

## Status

Unchanged in shape, better in every number:

- **Cost and target**: strongest layer. Sacrifice atoms 94.18/78.25, tap
  99.75/99.75, counter atoms 96.70/89.60.
- **Trigger modes**: now genuinely good — 93.72/81.44.
- **Static modes**: still weakest at 71.45/81.94; `Continuous` remains the
  catch-all absorbing unclassified lines.
- **Replacement events**: 89.13/80.39.

Verified: 92 tests pass, M0 90.29%, M1 83.35/76.9.

**Superseded:** earlier drafts of this note ended by calling blocked Scryfall
access the outstanding blocker. That was wrong — the grammar reads oracle text
from Forge's own `Oracle:` line and never needed Scryfall. See
[research/scryfall-dependency-reassessed.md](scryfall-dependency-reassessed.md).
