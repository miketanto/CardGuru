# Handoff — the board is encoded, the *timing* is not

You are picking up a project that has spent several phases improving how
the **board** is represented to the policy, and has just finished
demonstrating that this is no longer the binding constraint. The next
question is whether the agent can learn to act at the right *moment* —
stack interaction and instant-speed removal — and whether anything it
learns carries to a deck it has not seen.

Read this file, then `DIMIR-V6-2K-RESULT.md` (the run that motivates
it), then `CURRICULUM-LADDER.md` §5 (the black branch — the experiment
you need is already built), then `PHASE8-TRANSFER.md` §Verdict (so you
do not re-run a null result).

## 0. State of the world

- **v6 landed and is gated.** Entity tokens + typed relation edge bias,
  server and emission both shipped, §5b collision gate passed on real
  emission (1983 positions, 853 pairs, all distinct). See
  `ENCODER-V6-RESULT.md` and `ENCODER-V6-NETWORK.md`.
- **Training v6 on a real constructed deck (BenchDimir) to 2048
  episodes produced no measurable win-rate gain past 1024**: pooled
  n=200, .555 → .590 → .585, p=0.54 over the whole 1024 episodes.
- **The policy has collapsed onto one action per decision site.**
  Attack decisions: `under_over = 0/39` and `0/40` across two
  batteries — every suboptimal attack is an over-attack, none is an
  under-attack, at 96% of opportunities taken. Priority decisions: 83
  of 92 windows passed in a full traced game, 26 of them with 3+ real
  candidates.
- **Phase 8 already answered "does a better card encoder buy zero-shot
  transfer?" — no**, at two perturbation scales, with the negative
  control transferring as well as the treatment. Its verdict names the
  lever it thinks remains: *feature dimensions that capture conditions
  — what a counter can counter, what removal can hit.*

Those last two converge on the same place, which is why this handoff
exists.

## 1. What the last session settled, and the one number it got wrong

Settled:

- **The self-targeting pathology does not exist.** Split target windows
  by whether an enemy creature was legal, and the policy chooses the
  enemy **104/124 at ck_1024 and 132/132 and 107/107 at ck_1536 and
  ck_2048**. `V6-TARGETING-FINDING.md` is corrected in the file; the
  apparent pathology was entirely the denominator.
- **The gap is timing, not targeting.** ~90% of instants are cast on
  the agent's own turn (18/180, 23/193, 15/187), and flash-capable
  permanents are held for the opponent's turn **1 time in 1,027
  opportunities** across three checkpoints. The agent has an
  instant-speed deck and plays it at sorcery speed. Training did not
  move this.
- **The share of target windows with no enemy option rose with
  training**: 51% → 54% → 67%. It fires removal into emptier boards
  the longer it trains. (Upper bound — see the cost-leg caveat below.)

Got wrong, and you should assume the same class of error is still
lurking elsewhere:

- **Every probe before this run was 10 games.** Re-probing the *same*
  `ck_1024` weights at 100 games moved D0 .40 → .54 and D1 .20 → .29.
  The `.00/.20/.40` learning curve previously reported was noise around
  a higher level. `R0_EVAL_G` defaults to 100 for a reason; do not
  lower it.
- **`rung0_lane.sh BenchDimir BenchDimir`** puts the same deck in both
  slots, so the `TWIN` column is a second sample of `D0`, not a second
  matchup. Pool them; do not read them as agreement.

## 2. The task

Three questions, in the order they should be attacked, because the
first is cheap and can kill the other two.

### 2a. Can the policy *represent* a timing decision at all?

Before asking whether it learns timing, prove the features can express
it. The same removal spell, castable in your own main phase and
castable in the opponent's declare-attackers step, must produce
**distinct candidate vectors**. If they collide, no amount of training
can learn the difference and every downstream experiment is void.

This is the v6 §5b gate methodology applied to a new axis, and
`rl/entity_gate.py` is the template — it already loads a dump of real
emission, groups positions that a coarser encoder folded together, and
reports the closest surviving pair. Build the timing analogue: dump
candidate rows for the same card at different steps, group by card
identity, assert the within-card cross-step distance is non-zero and
report the minimum.

**Pre-registration, per the §6 ground rule: if the vectors collide,
that is the finding, and no training run is needed to establish it.**

### 2b. Does the ladder's timing twin separate?

`CURRICULUM-LADDER.md` §5 already built the controlled experiment and
only half of it has been run:

| deck | the four card slots become | type |
|---|---|---|
| `B1Narrow` | 4 Defeat — power ≤2 | **sorcery** |
| `B1Fast` | 4 Cruel Cut — power ≤2 | **instant** |

Same cost `{1}{B}`, same colour, same count, same restriction, same
slot. **Only the timing changes.** That is tighter than any A/B this
project has run on the encoder.

`B1Fast` has been run to 1086 episodes. `B1Narrow` has not been run at
all. What `B1Fast` shows, and it is not encouraging:

| trained | win rate (n=25) | instants cast / 25 games | on opp turn | in combat |
|---|---|---|---|---|
| 574 | .520 | 25 | 1 | 3 |
| 1086 | .680 | **3** | 0 | 1 |

Win rate went **up** while removal casts went **down** by 8×
(`attacks` went 124/137 → 184/204 over the same interval). On the deck
built to test timing, the trained policy's answer was to stop casting
the removal and attack more. Note `under_over = 7/24` here, unlike
Dimir's `0/40` — this policy is *not* collapsed the same way, which
makes the rung more informative, not less.

Caveat before you build on it: **n=25 games per probe.** Re-probe
`ck_1086` at 100 games before treating any of those levels as real.
That is the exact mistake §1 documents.

The comparison to run is `B1Narrow` at matched budget and matched
`R0_EVAL_G=100`. If the instant deck does not beat its own sorcery twin,
the agent is getting nothing from instant speed.

### 2c. Transfer — and what not to redo

`PHASE8-TRANSFER.md` tested whether a better *card encoder* buys
zero-shot transfer and found nothing at 200g, at 12-card and
full-archetype perturbation, with the negative control transferring as
well as the treatment. **Do not re-run that A/B.** Its own verdict says
the remaining levers are (i) features that capture conditions, or (ii)
enough capacity that card identity becomes load-bearing.

The transfer question worth asking now is narrower and follows from
§2a: if you add condition features (does this removal have a legal
enemy target right now; can it be cast at instant speed; is the
opponent's turn coming), does a policy trained on one removal deck
carry to another removal deck with different card names but the same
conditions? That is a transfer test of the *condition* axis, which
Phase 8 never had. Phase 8's deck variants and matrix runner
(`p8_decks.py`, `p8_matrix.sh`, `p8_eval.sh`) are reusable as-is.

## 3. Pre-register what cannot move

Following `ENCODER-V6-BUILD.md` §0, which is the model for this and
which caught a real anomaly last time:

- **A candidate-feature change cannot improve block-optimality on a
  vanilla-body deck.** `CombatMath` handles vanilla bodies only, and
  BLOCKOPT is computed against it. If BLOCKOPT moves when you add
  timing features, find the bug.
- **Adding condition features cannot improve win rate on a deck with no
  instants.** `B0Base` and `B1Narrow` are the controls. A gain there is
  a leak, not a result.
- **The §2a collision test cannot be passed by training.** It is a
  property of the emission. If it fails, no checkpoint fixes it.

## 4. Known caveats you inherit

- **Cost legs are counted as target decisions.** Requiting Hex takes
  *two* `target` consults for one cast — the kill and the additional
  cost — and the cost leg usually has one legal option. So
  `tgtNoOppAvail` is an **upper bound** on "cast removal into an empty
  board", and the split by leg is still not built. It is the cheapest
  unfinished diagnostic in the repo.
- **ATKOPT's reference is one combat deep** and cannot see that an
  attacker will not be home to block. It over-credits attacking. Read
  it beside the attack *rate*, never alone.
- **`CombatMath` SCOPE is vanilla bodies only** — no first strike,
  deathtouch, trample, flying, menace. Joint attack/block *candidates*
  are built from its outcomes, so a keyword deck corrupts the features,
  not merely the audit. Any new deck must respect this or say loudly
  that it does not.
- **BLOCKOPT's denominator is not all free choices.** The trace shows 5
  of 7 block windows in a real game were `k=1` — forced, no untapped
  creatures.

## 5. Gotchas, including two this session paid for

Everything in `HANDOFF-ENCODER-V6.md` §5 still holds (class-init
constants, `pkill` bracketing, eval-only attack audit, transcript
location). New:

- **The policy server grows ~5 MB/episode** — floor 3.8 → 5.1 GB over
  256 episodes. Not a reference leak (buffers are cleared); it fits
  allocator fragmentation from the ~550 MB transient stacks in
  `update()`. **It survives only because the lane restarts the server
  every 512 episodes** (measured 6107 MB → 655 MB across a battery).
  Raising `UPDATE_EPISODES` or lengthening a block needs this fixed.
- **Never edit `rung0_lane.sh` while a lane is running.** Bash reads a
  script incrementally as it executes; an edit mid-run can corrupt
  execution.
- **`Monitor` clamps to a 30-minute timeout** regardless of the
  `persistent` flag. Long runs need it re-armed; the timeout
  notification itself doubles as a session-activity keepalive, which
  matters because the container recycles on *session* inactivity, not
  process activity. `rl/dimir2k_alive.sh` is a working heartbeat.
- **No run in this project has a durable dense training curve.**
  `server.log` is truncated on every `start_server` and the lane never
  passes `policy_server.py`'s `log_path`. Wiring `--log` into the lane
  is two lines and would turn three battery points into a curve. Do it
  first; it is the highest value-per-line change available.

## 6. Ground rules

`HANDOFF-ATTACK-JOINT.md` §6 governs — Wilson not Wald, pool only
finished seeds, a regression is not "flat", state what a number cannot
support, confounds in the doc and not only in chat. Plus:

- **Pre-register what the change cannot do** (§3 above).
- **Never report a level from fewer than 100 games.** This session
  published a learning curve built from 10-game probes and had to
  retract it. A rate is not a result until its Wilson interval is
  narrower than the effect being claimed.
- **A behaviour counter beats a win rate.** The two real findings of
  the last session (`under_over = 0/40`, `1/1027` flash held) came from
  per-decision censuses, not from win rates, and neither would have
  been visible in a win rate at any sample size.

## 7. Files

| file | why |
|---|---|
| `rl/DIMIR-V6-2K-RESULT.md` | **the run that motivates this handoff**; §4 is the timing evidence |
| `rl/CURRICULUM-LADDER.md` | §5 the black branch; `B1Fast`/`B1Narrow` is your controlled timing pair, §3 rung 5 is the hidden-information rung |
| `rl/PHASE8-TRANSFER.md` | the transfer null — read the verdict before designing any transfer test |
| `rl/ENCODER-V6-RESULT.md` | v6 end to end; §5b the gate methodology you are copying for §2a |
| `rl/entity_gate.py` | the collision gate — the template for the timing-collision test |
| `rl/entattn_check.py` | 23 checks over net and wire, no engine, ~4 s; run it after any server change |
| `rl/xmage-src/RLPlayer.java` | `-Drl.trace` (one line per consult, 7 sites), `recordTargetChoice`, the instant-timing counters at ~line 600 |
| `rl/dimir_trace.sh` | one game, every decision, ready to point at any checkpoint |
| `rl/artifacts/v6/dimir_ck1024_trace_seed980005.txt` | what a full game of decisions looks like |
| `rl/rung0_lane.sh` | the lane; `R0_EVAL_G`, `R0_EVERY`, `R0_ENCODER_V`, `R0_OUT`, `R0_PORT` |

## 8. The prompt

> Read `rl/HANDOFF-STACK-TIMING.md`, then `rl/DIMIR-V6-2K-RESULT.md`,
> then `rl/CURRICULUM-LADDER.md` §5 and `rl/PHASE8-TRANSFER.md`
> §Verdict.
>
> The board encoding is done and is not the binding constraint. The
> agent plays an instant-speed deck at sorcery speed: ~90% of instants
> on its own turn, flash held for the opponent's turn once in 1,027
> opportunities, and on the ladder rung built to test timing it
> responded to training by casting its removal 8× *less*.
>
> Your task, in this order:
>
> 1. **Prove the features can express a timing decision.** Build the
>    §2a collision test on the model of `rl/entity_gate.py`: the same
>    card castable in your main phase and in the opponent's
>    declare-attackers step must produce distinct candidate vectors.
>    Report the minimum within-card cross-step distance. If they
>    collide, stop — that is the finding, and it voids everything
>    below until fixed.
> 2. **Run `B1Narrow` at matched budget** against the existing
>    `B1Fast`, both at `R0_EVAL_G=100`, and re-probe `B1Fast` ck_1086
>    at 100 games first because its current numbers are n=25. Same
>    cost, colour, count and restriction; only sorcery-vs-instant
>    differs. Does instant speed buy anything?
> 3. **Only then** design the transfer test, on the condition axis
>    Phase 8 named — not the card-encoder axis Phase 8 already found
>    null.
>
> Ground rules in §6. Pre-registration in §3 — say in advance which
> metrics your change cannot move, and treat an improvement on them as
> a bug to find rather than a result to write up. Never report a level
> from fewer than 100 games; the last session published a learning
> curve from 10-game probes and had to retract it.
>
> Branch: develop and push to `claude/v6-network`. Never push to
> `phase-5`. Do not touch `rung0_lane.sh` while a lane is running.
