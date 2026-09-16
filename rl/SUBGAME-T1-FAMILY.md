# T1 family — generate, solve, filter

`rl/SUBGAME-T1-BUILD.md` records one board. This file records the
search that was supposed to replace it, per the closing section of
`rl/SUBGAME-DESIGN.md`: *an instance is not a design, it is a search
result.* Engine pin `7554968c`, this container.

Status: generation **COMPLETE** (28 instances); gates 1 and 3 running.
Nothing here is a capability claim; no network has been
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

Seed 11, three shards, replay cap 8,000. All three wrote **identical**
admission footers — `drawn=658 rejStats=448 admitted=210 rate=0.319` —
which is the check that they walked the same draw stream, so the union
of shards is exactly the single-JVM run.

### Yield

| label | n | |
|---|---|---|
| `TRIVIAL` | 92 | opening action not load-bearing |
| `CAPPED` | 36 | no answer inside the replay cap |
| `MULTI` | 31 | A wins, but several classes do |
| `DEAD` | 23 | A loses down every line |
| `SWING` | 19 | **family** |
| `HOLD` | 9 | **family** |

**28 instances have a unique optimal opening class.** That is 13.3% of
admitted boards (Wilson 95% 0.094–0.186) and 4.3% of boards drawn
(0.030–0.061). The yield is reported rather than tuned away: it is what
the method costs.

`TRIVIAL` at 44% of admitted is the single biggest cost, and it is the
same thing the first calibration finding was about — the admission test
buys sharpness on *life totals* but nothing on whether A has slack to
recover in.

### Solve cost

Mean 41.3 s, max 217.3 s, mean 2,449 replays. **36 of 210 boards bought
no answer at all.** This is the number that should set how wide a tier-2
board is allowed to be, and it is why the solver now carries a
wall-clock budget as well as a replay cap.

### Gate 2 — discrimination: PASSES

Uniform-random play (both seats) over the family: mean **0.539**, min
0.315, max 0.725, n=28 instances × 200 playouts. Nowhere near ceiling,
on any instance.

### The baselines — no stats-only rule solves the family

| baseline | correct | Wilson 95% |
|---|---|---|
| `safeattack` | 21/28 = **0.750** | 0.566–0.873 |
| `bodycount` | 19/28 = 0.679 | 0.493–0.821 |
| `allin` | 14/28 = 0.500 | 0.326–0.674 |
| `never` | 9/28 = 0.321 | 0.179–0.507 |

The family-level gate passes: none is at ceiling. The load-bearing
consequence is the bar it sets — **a network on this family is measured
against 0.750, not against 0.25 or 0.5.** A checkpoint scoring 0.6 here
is worse than a rule that reads two numbers off the cards.

### The family is too small for the claim it is meant to support

Stated plainly because it is the result that most constrains what
happens next. At n=28 the baseline intervals are ±0.15 and they
**overlap each other**: `safeattack` 0.566–0.873 and `bodycount`
0.493–0.821 cannot be told apart by this family, let alone a network
separated from either. The project's standing rule — never report a
level from fewer than 100 games; a rate is not a result until its
interval is narrower than the effect claimed — applies here with
instances in place of games.

So 28 instances is enough to prove the *pipeline* works and to set the
bar; it is not enough to score an arm on. Reaching ~200 instances needs
roughly 1,500 admitted boards at the observed 13.3% yield, which at
41.3 s a solve over three shards is about **six hours** of wall clock.
That is a real and affordable number, and it is the honest price of
Step 2 rather than a reason to quote a level off 28.

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
