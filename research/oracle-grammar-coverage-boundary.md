# The coverage rule's boundary, measured — and a correction

**In scope, the grammar scores 6/9. One rank-band outside it, 1/8. The coverage
rule stated in M3 is doing real work, not decorating the result.**

This also corrects something I claimed in `research/oracle-grammar-m3.md`: that
the generated slice "solves the burn problem structurally". It solves it only
*within the coverage rule's scope*. Advancing the rank offset far enough stops
measuring the grammar and starts measuring the rule's boundary.

## This cycle's fixes

Three changes, all general, all validated on M1's holdout rather than on a slice:

**1. Trigger modes are decided by the event clause.** The `Drawn` production was
firing 721 times against Forge's 145 because it matched the whole ability line —
so "Whenever Ragavan deals combat damage to a player, **draw a card**" voted
`Drawn` instead of `DamageDone`. A triggered ability's mode is determined by its
*event*, which ends at the first comma. Matching there instead:

| trigger modes (holdout) | before | after |
|---|---|---|
| precision | 85.47 | **92.87** |
| recall | 73.89 | **80.10** |

**2. `tapXType` cost atoms.** "Tap two untapped creatures you control" now emits
`tapXType<2/Creature>`, matching Forge. This was v3's b04 failure.

**3. `derivation: "script"` on the Forge path** (`cardguru/dataset.py`), with a
test. The oracle emitter already stamped `oracle-grammar`; without the matching
tag the two derivations are indistinguishable once merged, and the field-level
merge policy has nothing to branch on. This is the first change this line of work
has made to product code rather than to `research/scripts/`.

## The boundary probe

v4 was generated at `SLICE_RANK_OFFSET=12` — ranks 13–18 of each vocabulary.
Zero archetype overlap with v2 or v3.

| slice | rank band | in M3's coverage rule? | result |
|---|---|---|---|
| v3 | 7–12 | mostly yes | 6/9 — 66.7% |
| v4 | 13–18 | **mostly no** | 1/8 — 12.5% |

v4's failures are not surprises. They are what the rule said would happen:

| id | archetype | rank | in scope? |
|---|---|---|---|
| b04 | `BecomesTarget` trigger mode | 13 | no — rule covers top 10 |
| b05 | `Sacrificed` trigger mode | 14 | no |
| b06 | `Taps` trigger mode | 15 | no |
| b07 | `LifeGained` trigger mode | 16 | no |
| b01 | `ExileFromGrave` cost atom | — | no production written |
| b08 | `OptionalCost` static mode | 13 | in scope, 20% recall — a real weakness |

Only b02 (`PayLife`, 98.1% recall) passes, and only b08 is an in-scope failure.
Four of the eight are trigger modes the rule explicitly declines to cover.

**This is the strongest evidence so far that the coverage rule is load-bearing.**
A rule stated in advance that then predicts, correctly, which questions will fail
is doing something a post-hoc rationalisation cannot. The 6/9 → 1/8 cliff at the
rule's edge is the shape you want to see.

## The correction

`research/oracle-grammar-m3.md` says the generator "solves the burn problem
structurally" because advancing `SLICE_RANK_OFFSET` yields a disjoint slice.
That is true but incomplete, and the incompleteness matters:

- **Disjointness and in-scope-ness trade off.** Each advance moves further into
  the frequency tail. By offset 12 the slice is mostly testing vocabulary the
  grammar never claimed. It is still a valid measurement — of the boundary — but
  it is no longer the same measurement as v2 and v3.
- **The tail produces junk archetypes.** v4's b03 is "cards with an activated
  ability whose cost includes **or**", an artifact of splitting cost atoms on
  `<`. In the head of the distribution this never surfaced; in the tail it does.
  The generator needs an archetype sanity filter before it is used much deeper.

So the honest statement is narrower: **the slice is renewable within the coverage
rule's scope.** Beyond that scope, a fresh in-scope measurement needs a different
axis of variation — different witness/foil exemplars drawn from the *same*
archetypes — which the generator does not yet support.

## Status

Unchanged in substance, sharper in detail:

- **Cost and target**: merge-ready behind the `derivation` tag, which now exists
  on both sides. v4's in-scope cost question returned 98.1% of Forge's hits.
- **Modes and events**: Forge-only. Trigger modes improved materially this cycle
  (92.87/80.10) but static modes sit at 66.79/78.90 and `OptionalCost` at 20%
  recall inside the coverage rule.
- **Outside the top-10/15 rule**: no claim, and now a measured one — 12.5%.

Verified: 92 tests pass (one new), 20/20 benchmark goldens, M0 90.2%, M1
83.35/76.9, M2 params unchanged.

The blocker has not moved: `api.scryfall.com` is still 403 through the session
proxy.
