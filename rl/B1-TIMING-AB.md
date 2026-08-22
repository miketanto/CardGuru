# B1Narrow vs B1Fast — does instant speed buy anything?

`CURRICULUM-LADDER.md` §5's timing pair, run as an A/B.
`HANDOFF-STACK-TIMING.md` §2b asks for `B1Narrow` at matched budget
against `B1Fast`, both at `R0_EVAL_G=100`.

| deck | the four card slots | type |
|---|---|---|
| `B1Narrow` | 4 Defeat `[DTK:97]` — destroy target creature power ≤2 | **sorcery** |
| `B1Fast` | 4 Cruel Cut `[ANB:47]` — destroy target creature power ≤2 | **instant** |

Verified, not assumed — `diff` of the two deck files is three lines:
the Defeat line, the Cruel Cut line, and `NAME:`. Same cost `{1}{B}`,
same colour, same count, same restriction, same slot, same 56 other
cards. **Only the timing changes.**

## 0. Pre-registration — written before either lane started

Per `HANDOFF-STACK-TIMING.md` §3 and the standing rule in `CLAUDE.md`:
state in advance what this change *cannot* move, and treat a move there
as a bug to find rather than a result to write up.

1. **The §2a collision cannot be changed by this run.** It is a property
   of `StateEncoder.forCard`, which no checkpoint touches.
   `TIMING-GATE-RESULT.md` §3.
2. **The two arms cannot differ at `ck_0`.** Both lanes take the same
   `--seed`, so `p10_init_net.py` produces **byte-identical initial
   weights**, and the untrained battery is argmax on those weights. A
   `ck_0` win-rate gap beyond its Wilson interval is a deck-strength
   confound, not timing, and must be subtracted from every later
   comparison rather than explained.
3. **`B1Narrow` cannot gain from instant-speed play.** It has no
   instants. Its `instantCastsOppTurn` must stay at 0. A nonzero value
   is a counter bug.
4. **The load-bearing one.** `B1Fast` can only convert instant speed
   into a win rate *through opponent-turn casts*. So: **if `B1Fast`
   beats `B1Narrow` while its `instantCastsOppTurn` stays at or near
   zero, that is not a timing result** — the decks are otherwise
   identical, so the gap would have to come from somewhere this
   experiment did not intend, and the job is to find it, not to report
   it. The behaviour counter gates the win rate, not the other way
   round.

Stated equally plainly: the outcome this design expects, given
`TIMING-GATE-RESULT.md` §4, is **no separation**, because the agent
reaches an opponent declare-attackers window with anything castable
about once in a hundred windows. A null here is the predicted result and
will be reported as one, not as a failed experiment.

## 1. What had to change from the handoff's plan

**§2b's "re-probe `B1Fast` ck_1086 at 100 games first" cannot be done.**
Those weights do not exist: `artifacts/v6/black/` holds the *probe logs*
from that run but no `.pt`, and there is no B1 checkpoint anywhere in
the repo. `/tmp/rl_b1_v6/` died with its container.

So the n=25 numbers the handoff warns about are not upgradeable in
place — the arm has to be retrained. Since it is being retrained anyway,
both arms are run **from scratch, same seed, same budget**, which is a
tighter comparison than re-probing one old checkpoint against one new
lane would have been. The published n=25 rows are superseded rather than
corrected; they are not comparable to anything below (different run,
different weights).

**Budget: 1024, not 1086.** 1086 is not a multiple of the 64-episode
chunk or the 512-episode battery cadence; 1024 gives batteries at 0,
512, 1024 on both arms at the same points.

**`TWIN` is the base deck in both arms.** No `B1NarrowTwin.dck` exists,
and giving one arm a twin and not the other would unmatch them. Passing
`BASE` in both slots makes `TWIN` a second sample of `D0` — exactly the
case `DIMIR-V6-2K-RESULT.md` §0 documents — so **`D0` and `TWIN` are
pooled to n=200 and never read as agreement.** This costs the transfer
probe, which is not the question here.

## 2. Configuration

```bash
R0_ENCODER_V=6 R0_EVAL_G=100 R0_EVERY=512 R0_CP7_G=0 R0_CONC=2 \
  R0_OUT=/tmp/rl_b1fast   R0_PORT=7971 bash rl/rung0_lane.sh B1Fast   B1Fast   1024 0
  R0_OUT=/tmp/rl_b1narrow R0_PORT=7972 bash rl/rung0_lane.sh B1Narrow B1Narrow 1024 0
```

Identical but for the deck. `R0_CP7_G=0` skips the alpha-beta holdout
symmetrically — the handoff records 50 games of it as decorative, and an
A/B that skips it on both arms loses nothing it could have settled.

Also landed in this run, per `HANDOFF-STACK-TIMING.md` §5: the lane now
passes `--log $OUT/train.csv` to `policy_server.py`. `server.log` is
truncated by its own redirect on every restart, which is why no run in
this project has a dense training curve; `--log` appends, so these are
the first two runs with one.

## 3. Results

*(pending — filled in from the batteries, n=100 per probe, D0+TWIN
pooled to n=200, Wilson 95%)*
