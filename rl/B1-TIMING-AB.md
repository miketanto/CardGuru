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

## 3. Results — `B1Fast` arm (complete)

n=100 per probe; `D0` and `TWIN` pooled to n=200 (§1); Wilson 95%.

| trained | D0+TWIN pooled n=200 | D1 n=100 | instants cast | target choices | under/over |
|---|---|---|---|---|---|
| 0 | .000 [.000, .019] | .000 [.000, .037] | 1 | 1 | 0/0 |
| 512 | .430 [.363, .499] | .410 [.319, .508] | **0** | **0** | 0/96 |
| 1024 | **.595** [.526, .661] | .540 [.443, .634] | **0** | **0** | 5/77 |

512 → 1024 pooled: **+.165, z=3.30, p=0.0010.** D1: +.130, z=1.84,
p=0.066.

### 3a. It learned to .595 without ever casting its removal

**Across 300 eval games at ck_512 and 300 more at ck_1024, `instCasts`
and the entire `tgt*` block are absent from every probe file.**
`EpisodeRunner` emits the instant block only `if (instantCasts > 0)` and
the target block only `if (targetCreatureChoices > 0)`, so absent means
the count is genuinely zero — not that the instrument is missing. It
fires elsewhere in the same run: `flashThreats=0` prints, because that
counter is unconditional.

So the arm's whole gain — .000 → .430 → .595 — is combat play. Four
Cruel Cuts are being played as blanks.

The one exception is the untrained row, and it is worth keeping: at
`ck_0` the policy cast exactly **one** instant in 300 games, and
`instOppTurn=1` — that single cast was **at instant speed, on the
opponent's turn**. The count is in the D1 probe only; an earlier reading
of this arm checked the D0 probe alone and reported zero, which is why
`b1_report.py` sums all three probes and stars a key absent from every
one.

**Training did not make the agent cast its removal at the wrong time. It
made it stop casting it.** The handoff describes this rung as responding
to training by casting removal "8× LESS" (25 → 3 casts, n=25 probes). At
n=100 the endpoint is not 8× less, it is **zero**, and the starting
point is 1 rather than 25 — the n=25 figures are not reproduced by this
run and, being different weights from a lost checkpoint, are not
comparable to it either.

### 3b. `under_over` does not replicate the handoff's reading

`HANDOFF-STACK-TIMING.md` §2b cites `under_over = 7/24` on the old
B1Fast run as evidence that "this policy is *not* collapsed the same
way" as Dimir's `0/39` and `0/40`, "which makes the rung more
informative, not less". This run gives **0/96 at ck_512** — the same
one-directional collapse as Dimir, at a larger denominator — relaxing to
**5/77 at ck_1024**. The 7/24 came from n=25 probes. The claim built on
it should not be carried forward.

## 4. Results — `B1Narrow` arm (complete)

| trained | D0+TWIN pooled n=200 | D1 n=100 | removal casts (3 probes) | under/over |
|---|---|---|---|---|
| 0 | .000 [.000, .019] | .000 [.000, .037] | 0 | 0/0 |
| 512 | .020 [.008, .050] | .020 [.006, .070] | 41 | 0/9 |
| 1024 | **.585** [.516, .651] | .580 [.482, .672] | **86** | 0/96 |

Target-by-power census, `D0` probe:

| ck | chose p2 | legal p2 | any other power |
|---|---|---|---|
| 512 | 13 | 30 | 0 everywhere |
| 1024 | 27 | 70 | 0 everywhere |

Defeat is power ≤2 and only power-2 creatures were ever legal targets,
so the histogram has exactly the shape the restriction implies. The
policy takes the kill in **39%** of windows where one is legal (27/70),
against 43% at ck_512 — stable, and neither 0 nor 1.

### 4a. The ck_512 reading was withheld, and it was right to withhold it

At ck_512 this arm read **.020** against `B1Fast`'s `.430`, which taken
alone says the sorcery deck collapsed. It did not: **512 → 1024 is .020
→ .585, z=12.30.** The dense training curve said so at the time — the
*sampled* win rate was climbing .031 → .219 with steps/episode at 4724,
normal — while the *greedy* policy was degenerate
(`attackOpportunities` 87 in 100 games, games over at 15.5 turns).

That gap is a sampled-vs-argmax divergence on one checkpoint. **With
three battery points and no curve, the published claim would have been
"the sorcery arm collapsed", and it would have been wrong.** This is the
first result the two-line `--log` change (§2) has paid for.

## 5. Verdict — instant speed buys nothing here, and neither does the removal

At matched budget, matched seed, matched everything but the card type:

| ck_1024 | `B1Fast` (instant) | `B1Narrow` (sorcery) | test |
|---|---|---|---|
| D0+TWIN pooled n=200 | .595 [.526, .661] | .585 [.516, .651] | **z=−0.20, p=0.84** |
| D1 n=100 | .540 [.443, .634] | .580 [.482, .672] | z=0.57, p=0.57 |
| removal casts / 300 games | **0** | **86** | — |

**The answer to §2b is no.** The instant arm does not beat its own
sorcery twin — the two are indistinguishable, at n=200 per arm on the
pooled heuristic probe. This is the outcome §0 pre-registered, and it is
reported as the predicted result rather than as a failure.

**But the more useful finding is the pair of columns beside the win
rates, and it bounds what this rung can ever settle.** One arm cast its
removal 86 times and the other cast it zero times, and they finished at
the same win rate. So on this rung **the removal has no measurable
win-rate value even when it is used.** A deck slot worth nothing cannot
be made worth something by casting it earlier or later, which means:

> **`B1Fast` vs `B1Narrow` is not a powered test of timing.** It varies
> the timing of a card whose presence or absence the win rate cannot
> detect. `CURRICULUM-LADDER.md` §5 calls `B1Fast` "a free replication"
> of the white branch's `W3 → W4` timing experiment; on this evidence it
> is a replication of nothing, and the same objection applies to `W3 →
> W4` unless that pair's removal is shown to carry win-rate value.

Pre-registration clause 4 fired, in the direction it was written to
catch: `B1Fast`'s `instantCastsOppTurn` is zero, so no win-rate result
of this A/B could have been credited to timing. It did not have to be
invoked, because there is no win-rate gap to explain.

### 5a. The behaviour finding, which is the opposite of the premise

**The sorcery arm learned to cast its removal. The instant arm never
cast its once.** 0 casts in 600 eval games against 127 in 600.

`CURRICULUM-LADDER.md` §5 built this pair expecting instant speed to be
an *added capability* over its sorcery twin. Behaviourally it was a
handicap: the strictly more permissive card is the one the policy failed
to use at all.

A mechanism is available and it is `TIMING-GATE-RESULT.md`'s finding
turned around. Under a timing-blind candidate encoding:

- **Defeat's candidate row appears only in a main phase.** A sorcery is
  legal nowhere else, so legality has already filtered the context and
  the row is unambiguous — one vector, one kind of moment.
- **Cruel Cut's identical row appears in ~10 different step contexts**
  (own upkeep, draw, main, begin combat, opponent's turn...), most of
  them poor moments to cast. §2a measured exactly this: one distinct row
  across all four steps it was offered in.

So the instant's candidate is *ambiguous* in a way the sorcery's is not,
and the policy must recover the difference from the state token alone.
`TIMING-GATE-RESULT.md` §5 shows that path exists and is weak at init
(the step moves the cast-vs-hold margin about as much as one extra enemy
creature). **Timing-blindness may not merely fail to help an instant —
it may make an instant harder to learn than a sorcery.**

**This is a hypothesis with one seed per arm behind it, not a result.**
Two arms, two training trajectories, one seed each; the mechanism is
consistent with the evidence and is not established by it. What would
test it is in §6.

## 6. What this does not support, and what to run next

- **One seed per arm.** `POOLED-ANALYSIS.md` §6 found between-net
  comparisons at one seed provisional as a class. The null (p=0.84) is
  the more robust half of this; the behaviour asymmetry (0 vs 127 casts)
  is one trajectory each and could be trajectory noise.
- **The .02 row proves how thin a single battery point is.** Read alone
  it inverted the arm's entire story.
- **`B1Fast`'s zero casts have three possible causes** — never offered
  (mana), offered and declined (policy), or the priority site collapsed
  onto one index the way the attack site has (`under_over` 0/96 on both
  arms at 1024). The window census and the chosen-index dump separate
  them; that run is §7.
- **Nothing here bears on the encoder.** No arm varies it.

## 7. Reproduction

```bash
nohup bash rl/b1_timing_ab.sh > /tmp/b1_ab.log 2>&1 &   # ~3h, sequential
python3 rl/b1_report.py /tmp/rl_b1fast /tmp/rl_b1narrow
```

Artifacts: `rl/artifacts/v6/b1ab/`.
