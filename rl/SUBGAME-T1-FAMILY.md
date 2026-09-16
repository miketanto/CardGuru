# T1 family — generate, solve, filter

`rl/SUBGAME-T1-BUILD.md` records one board. This file records the
search that was supposed to replace it, per the closing section of
`rl/SUBGAME-DESIGN.md`: *an instance is not a design, it is a search
result.* Engine pin `7554968c`, this container.

Status: **IN PROGRESS** — the numbers below are filled in as the run
completes. Nothing here is a capability claim; no network has been
scored on this family.

## What runs

`rl/xmage-src/SubgameFamily.java`, three modes:

| mode | what it does |
|---|---|
| `pool` | scans the card DB for **strict** vanillas and prints them |
| `gen` | draws boards, solves each exactly, labels each |
| `gate1` | re-solves the kept instances with more filler |
| `probe` | asks whether the optimal action is even expressible |

Driven by `rl/subgame_gen.sh` (sharded) and `rl/subgame_gates.sh`,
summarised by `rl/subgame_summary.sh`.

## The pool is engine-verified, and "no rules text" is not the test

`rl/artifacts/subgame/pool_vanilla_v1.tsv`, 17 bodies from 1/1 to 5/4,
drawn from M10–M15. The admission test is that **every ability on the
card is a `SpellAbility`** — the one that casts it — rather than that
its rule text is empty. `SUBGAME-T1-BUILD.md` records why: Hillcomber
Giant has an empty graph vector in `cards_v1` and mountainwalk in the
engine. A keyword smuggled into a "vanilla" family would make every
tier-1 result a measurement of something else.

## Uniqueness is over symmetry classes, not over masks

The solver's root options are bitmasks over the canonically ordered
attackers. Two copies of one vanilla body are interchangeable on a
fresh board, so "attack with lion #1" and "attack with lion #2" are two
masks denoting **one** decision. Counting masks would fail the
uniqueness gate on every board holding a duplicate, and would report a
coverage hole in gate 3 that is not there. Everything below is counted
over classes: the multiset of attacker names.

## Labels

Each solved board gets exactly one, from the solve alone:

| label | meaning |
|---|---|
| `HOLD` | A wins, and the empty attack is the **unique** winning class |
| `SWING` | A wins, and one specific attack is the **unique** winning class |
| `MULTI` | A wins, but more than one class does |
| `TRIVIAL` | every class wins — the opening action is not load-bearing |
| `DEAD` | A loses down every line |
| `CAPPED` | the replay cap was hit; no answer, and not counted as one |
| `NOTERM` | some replay ended with no winner — a design violation |

`HOLD` and `SWING` are the family. The rest are recorded, not hidden:
the yield is the honest cost of the method.

## Two calibration findings, each of which cost solves

**1. A uniform draw produces no usable boards.** The first batch of
eight, drawn from the bare parameter ranges, came back six `TRIVIAL`
and two `DEAD` — zero usable, at up to 90 s a solve. The reason is not
subtle: when one side is ahead on board *and* on life, the opening
attack cannot be what decides the game, because A has many later
decisions to recover in. A first decision is load-bearing only when it
is irrecoverable. Admission now requires both sides to be one swing
from death — `sum(B power) ≥ A life` and `sum(A power) ≥ B life` — and
neither condition mentions the solver.

**2. With every defender untapped, every admissible board is a hold.**
Attacking taps the attacker. On a board where both sides are one swing
from lethal and nothing is tapped, whoever swings first dies to the
crack-back — so `SWING` cannot occur, and the `never` baseline would
score 1.000 on the whole family by construction. B's bodies are
therefore tapped with probability 0.4 (B just attacked). This is part
of the generator, not a per-instance rescue.

## A screen that cost more than what it protected

A 60-playout screen was tried ahead of each solve, on the reasoning
that a board uniform-random play already decides has no discrimination
to measure. Measured: it rejected **one admitted board in nine** while
costing more per board than the solve it was protecting, because every
shard had to screen the whole stream before it knew whose board it was.
It is gone. Gate 2 is applied *after* the solve — which is also the
unbiased order, since the family is then not selected on the statistic
it reports.

## Pre-registered baselines

Four stats-only rules, fixed before the family was scored, so none can
be swapped in after seeing which one loses:

| baseline | rule |
|---|---|
| `allin` | attack with everything |
| `never` | attack with nobody |
| `bodycount` | all-in if A has more bodies than B has **untapped** ones |
| `safeattack` | attack with exactly the bodies whose toughness exceeds the best blocker's power |

**The family-level gate is that none of them reaches 1.000.** A family
a stats-only rule solves outright measures nothing about a network. A
per-instance "at least one baseline is wrong" filter is deliberately
*not* applied: it would select the family on the thing being measured.

## Results

_pending — the sharded run is still going._

## What this will not support

Stated before the numbers land, per the project's standing rules:

- **No capability claim.** No network is scored here. The family is an
  instrument; the arms that get measured on it are Step 2.
- **`randA` is not "how hard the game is".** It is uniform-random A
  against uniform-random B, not against the solver's best defence.
  Random-vs-optimal is strictly lower and is not measured yet, because
  seating the solver as an opponent is a per-decision solve.
- **Yield is not quality.** A high `TRIVIAL` fraction says the
  parameter range is loose, not that the surviving instances are weak.
- **Tier 1's adaptation axis is weak by construction.** There is no C
  variant because there is no mechanic to flip; swapping one vanilla
  body for another with the same stats tests name-invariance and
  nothing more. Real adaptation evidence starts at tier 2.

## Operational gotchas found here

- **Three JVMs opening the card DB at once lose a lock race.**
  `CardScanner.scan` opens H2; simultaneous opens give
  `Error opening database: "Lock file recently modified"` and the
  losing shard **dies outright while the others run on**. Nothing in
  stdout says so — it is only in the `.err` file, and the family
  quietly comes out a third short. Shards now start 25 s apart, and the
  `.err` files get read before any summary is believed.
- Solve cost is dominated by a minority of boards. Most solve in
  seconds; a few hit the replay cap. The cap is a budget, and a capped
  board is discarded rather than guessed at.
