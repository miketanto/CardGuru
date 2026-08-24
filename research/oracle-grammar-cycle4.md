# Cycle 4 — reuse beats re-derivation, and the best score yet

**7/10 on v5, mean recall of Forge hits 82.8% — the best of four in-scope
slices. The largest single gain came from deleting duplicated logic, not from
adding productions.**

| slice | in scope? | passed | mean recall of Forge hits |
|---|---|---|---|
| v2 | yes | 9/15 — 60.0% | 71.6% |
| v3 | yes | 6/9 — 66.7% | 63.0% |
| v4 | **no** (ranks 13–18) | 1/8 — 12.5% | 21.3% |
| **v5** | yes | **7/10 — 70.0%** | **82.8%** |

## The main finding: the emitter was re-deriving what M0 already knew

`m2_graph_emit.py` decided ability kind with its own `if TRIGGER_RE … elif
activated … elif is_spell … else S` chain. M0's `classify()` — measured at 90.2%
bag agreement — already made that decision, and made it better: it knows Saga
chapters are `K:Chapter`, that "enters with N counters" is folded into an
implementation keyword and should emit **no node at all**, and how replacement
templating reads.

Every one of those cases was falling through the emitter's `else` branch into
`S`, which is where most of `Continuous`'s 1,162 false positives came from.
Ajani Fells the Godsire emitted three static abilities where Forge has one
`K:Chapter` node.

Replacing the duplicated chain with a call to `classify()`:

| holdout | before | after |
|---|---|---|
| trigger modes — exact set | 71.03% | **78.07%** |
| static modes — exact set | 60.17% | **63.79%** |
| replacement events — exact set | 75.60% | **77.58%** |

No new productions were written for any of that. It is the single largest
quality gain of the four cycles, and it came from removing code.

One nuance the change surfaced: M0 and M3 detect replacements by *different
evidence* — M0 by templating ("would … instead"), M3 by the event vocabulary.
Using M0 alone dropped replacement recall from 84.7% to 65.5%, because M0's R
recall is ~70%. The fix is to use both: M0 decides kind, and a line M0 called
static but M3 can name an event for is promoted to `R`. Neither detector alone
is as good as the union.

Also fixed this cycle: keyword lines now split on `;` as well as `,`, so
"Defender; reach" is two keywords rather than an unrecognised static. M0 ticked
90.20 → 90.29.

## Generator hardening

Two real defects, both surfaced by v4:

**Junk archetypes.** v4's b03 was "cards with an activated ability whose cost
includes **or**" — the archetype enumerator whitespace-split raw cost strings,
and `Sac<1/Artifact;Creature/artifact or creature>` contains prose. Stripping
`<…>` payloads before tokenising fixes it. This never surfaced in the head of the
distribution; only the tail exposed it.

**No in-scope axis of variation.** Advancing `SLICE_RANK_OFFSET` walks out of the
coverage rule's scope (that is what v4 measured). `SLICE_WITNESS_OFFSET` now
selects the *N*th-ranked witness and foil instead of the top one, so the same
archetypes yield different exemplars. v5 uses it: zero witness overlap with v2,
and the generator produced genuinely confusable pairs by rule — Ruby Collector
vs Emerald Collector, Keeper of the Flame vs Keeper of the Dead, Ant-Man, Colony
Commander vs Ant-Man, Elusive Avenger.

**v5 is therefore partially independent, not fully.** Its archetypes are v2's;
only the exemplars are fresh. It tests whether the fixes generalise to different
cards within a known archetype, which is weaker than a fully disjoint slice and
should not be read as one. The head of the frequency distribution is now spent
as a clean measure in every axis available.

## What still fails

| id | archetype | cause |
|---|---|---|
| b05 | `DamageDone` trigger | 98.2% recall but the witness missed; over-emits (1,172 vs 866), Jaccard 71.5% |
| b06 | `AttackersDeclared` trigger | 0 hits — the production is `attackers are declared`, which is not how any card is worded |
| b07 | `ReduceCost` static | 64.3% recall — cost-reduction phrasings beyond "costs {N} less to cast" |

b06 is the instructive one. It is in scope by the coverage rule, has 233 cards,
and the production matches **nothing** — written from the mode's *name* rather
than from any card's text. That is a distinct failure class from the ones the
earlier cycles found: not an over-broad production, not missing vocabulary, but a
production authored against the wrong artefact. Worth checking the others in the
same list for the same defect.

## Status

- **Cost and target**: unchanged and strong — v5's cost questions returned
  99.2% and 99.8% of Forge's hits at ~98% Jaccard.
- **Trigger modes**: much improved (92.87/80.10, exact 78.07) but still
  over-emitting on `DamageDone`.
- **Static modes**: the weakest layer at 69.80/79.71, exact 63.79.
- **Replacement events**: 89.13/80.39, exact 77.58.

The verdict is unchanged — field-level merge, cost/target ready, modes
Forge-only — but the trend across four cycles is upward and the remaining
failures are individually named.

Verified: 92 tests pass, M0 90.29%, M1 83.35/76.9 unchanged, M2 params
94.18/78.25 sac and 99.75/99.75 tap.

Blocker unchanged: `api.scryfall.com` still 403 through the session proxy.
