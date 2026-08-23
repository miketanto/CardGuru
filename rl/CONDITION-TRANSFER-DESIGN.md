# Transfer on the CONDITION axis — design

`HANDOFF-STACK-TIMING.md` §2c: design the transfer test on the axis
`PHASE8-TRANSFER.md` named, **not** the card-encoder axis it already
found null. This is that design. Nothing here has been run.

## 0. What is off the table, and why

`PHASE8-TRANSFER.md`'s verdict is explicit: *"Do graph features buy
measurable zero-shot transfer? No — not detectably at 200g resolution,
at either perturbation scale tested"*, with the negative control
transferring as well as the treatment. **That A/B is not re-run.**

Its own diagnosis names the reason, and the reason is the design of this
one:

> E2 similarity is coarse on exactly the axis that matters — the Force
> Spike incident showed two d=0 cards moving a scripted mirror by 11
> points because **conditionality breadth isn't a feature dimension**.

And the structural point that makes Phase 8's null almost inevitable in
hindsight: **Phase 8 swapped cards for feature-matched equivalents, so
the conditions were held constant across the swap.** A policy that
navigates by conditions and a policy that navigates by names both
transfer perfectly when the conditions do not move. Phase 8 could not
have separated them.

**So the condition axis requires decks whose conditions differ**, not
decks whose names differ. That is the whole design change.

## 1. The axis

A removal spell's *condition* is what it can legally hit right now.
`CURRICULUM-LADDER.md` §5 already built a ladder that varies exactly
that, at fixed cost, colour, count and slot:

| deck | the four slots | legal targets |
|---|---|---|
| `B1Narrow` | 4 Defeat — power ≤2 | near-forced |
| `B2Mid` | 4 Reave Soul — power ≤3 | a real but small choice |
| `B3Open` | 4 Fell — destroy target creature | full threat assessment |
| `B4Card` | 4 Mind Knives — random discard | **no board effect, no target** |

and `B0Base`'s power census (16 creatures at power 2, 8 at 3, 4 at 4, 8
at 5) is built so those thresholds bite: at B1 the best target is often
not legal at all; at B3 it always is.

**The question.** Train on one rung. Test zero-shot on the others. A
policy whose candidates carry *conditions* should carry across, because
"this spell has 3 legal enemy targets, the best of which is a 5/3" is
the same sentence on every rung. A policy whose candidates carry only
`manaValue / P / T / isInstant / isSorcery / name-hash` — which is
exactly what `StateEncoder.forCard` emits today — has nothing to carry
but a name it has never seen.

## 2. The features

Computed **at emission time, per cast candidate, against the current
board** — that is what makes them conditions rather than card facts.

| slot | channel | why |
|---|---|---|
| 12 | 1 if ≥1 legal **enemy** target exists now | the flat "can this do anything" bit |
| 13 | legal enemy targets / 6 | breadth — the Force Spike axis by name |
| 14 | max power among **legal** enemy targets / 6 | how good is the best thing I can hit |
| 15 | max power among **all** enemy creatures / 6 | how good is the best thing on the board |
| 16 | 1 if this cast is happening **at instant speed** (castable now and this is not a sorcery window) | the §2a hole, closed |
| 17 | untapped mana remaining **after** this cast / 6 | what casting costs me in held-up options |

Slots 12–17 are free for a cast candidate. They are written by
`forTargetPermanent` (12–16) and `forBlock` (17–24), and **a T_TARGET or
T_BLOCK candidate never shares a candidate list with a cast candidate** —
the priority consult builds `[PASS] + casts` only. This is the same slot
reuse `forAssignment` and `forAttackSet` already document, and it means
**`CAND_DIM` does not change, so existing v6 checkpoints still load.**
Same caveat as v4's, and it must be stated the same way: the *meaning*
of a T_SPELL candidate changes, so a checkpoint trained before this and
driven through it is out of distribution and its numbers carry no claim.

**Slots 14 and 15 are the pair that does the work.** Either alone is a
board fact; the *gap* between them is the condition — "the best threat
out there is a 5/3 and the best thing I can legally hit is a 2/2" is
precisely what distinguishes B1 from B3, and it is what a policy would
have to re-learn from names today.

## 3. Why these, and what §2a changed about the list

`HANDOFF-STACK-TIMING.md` §2c proposed three: *does this removal have a
legal enemy target right now; can it be cast at instant speed; is the
opponent's turn coming.* Two changes, both from this session's
measurements:

- **"Can it be cast at instant speed" is dropped — it already exists.**
  `forCard` sets `c[10] = isInstant`. `TIMING-GATE-RESULT.md` §3 shows
  what is actually missing: not whether the card *is* an instant, but
  whether *this cast* is happening at instant speed. Slot 16 is that,
  and it is the per-candidate fix for the §2a collision — today a timing
  preference can only be a state-conditioned rescoring of a step-blind
  candidate, so "hold this one, cast that one" is not expressible. With
  slot 16 it is.
- **"Is the opponent's turn coming" is dropped as a candidate feature.**
  It is a property of the position, not of the candidate, and the v6
  globals already carry it (`g[1]` active-player, `g[2..7]` the step
  one-hot with a dedicated `DECLARE_ATTACKERS` bucket). Adding it to
  every candidate would be a constant column.
- **Slot 17 is added, and it is not in the handoff's list.**
  `TIMING-GATE-RESULT.md` §4 found the agent holding a legal instant in
  116 of 451 opponent declare-attackers windows and able to cast in 1 of
  them: it is tapped out. Whatever else is true, a policy cannot learn
  to hold removal for the opponent's turn while nothing tells it that
  casting now spends the mana that would have paid for it. Slot 17 is
  the cheapest expression of that, and it is a **timing** feature, not a
  transfer one — see §6.

## 4. The matrix

Two arms, identical but for the candidate emission:

- **`cond`** — treatment, slots 12–17 live.
- **`v6`** — control, `forCard` as it is today.

Train each on **`B1Narrow`** (sorcery, narrowest condition, and the
control the pre-registration in `B1-TIMING-AB.md` §0 uses), then
evaluate **zero-shot**, no fine-tuning:

| test deck | what it perturbs | prediction |
|---|---|---|
| `B1Narrow` | nothing (in-distribution anchor) | both arms equal |
| `B2Mid` | condition widens (≤2 → ≤3) | `cond` ≥ `v6` |
| `B3Open` | condition opens fully | `cond` > `v6`, the largest gap |
| `B1Fast` | condition identical, **timing** differs | isolates slot 16 |
| `B4Card` | **no target, no board effect** | the null control — see §5 |

`P8SwapInteraction` / `p8_matrix.sh` / `p8_eval.sh` are reusable as-is
for the runner; only the deck list and the arm flag change.

## 5. Pre-registration

Per `HANDOFF-STACK-TIMING.md` §3, in advance, and an improvement on any
of these is a bug to find rather than a result to write up.

1. **Condition features cannot improve win rate on `B4Card`.** Mind
   Knives has no board effect and no target, so slots 12–15 are
   identically zero on every one of its four cards and slot 16 is zero
   (it is a sorcery). `B4Card` is the negative control this design
   needs and Phase 8's redirected-e0 control was criticised for not
   being. A gain there is a leak.
2. **Condition features cannot improve win rate on a deck with no
   instants, *through slot 16*.** `B1Narrow` and `B0Base` have none, so
   slot 16 is a constant-zero column on both. Any B1Narrow gain must be
   attributable to slots 12–15 or it is unexplained.
3. **A candidate-feature change cannot improve BLOCKOPT on a
   vanilla-body deck.** `CombatMath` handles vanilla bodies only and
   BLOCKOPT is computed against it. Standing rule from
   `ENCODER-V6-BUILD.md` §0; it caught a real anomaly once.
4. **This cannot change the §2a collision for slots 0–11.** Those are
   card facts. Slot 16 is the only channel that makes a cast candidate
   step-dependent, and `timing_gate.py` should be re-run after the
   change with the expectation that **LEVEL A now separates** — that is
   the acceptance test for the emission, and it needs no training run.

## 6. What this design cannot settle, stated now

- **It confounds two changes.** Slots 12–15 are a *transfer* lever;
  slots 16–17 are a *timing* lever. Run together, a gap on `B2Mid`
  cannot be attributed to either. **They should be run as separate
  arms** (`cond-target` = 12–15, `cond-timing` = 16–17, `cond-both`) or
  the result will be uninterpretable. This is the single most likely way
  for this experiment to produce a number nobody can use.
- **Zero-shot at 200g could not see a small effect.** Phase 8's ±.07 CI
  at 200 games is the resolution floor, and it is wider than most
  effects this project has measured. A null here means "not bigger than
  ~.07", not "zero".
- **One seed proves nothing.** `POOLED-ANALYSIS.md` §6 found
  between-net comparisons at one seed to be provisional as a class. The
  within-net measurement — the distribution of chosen targets by power,
  which `CURRICULUM-LADDER.md` §5 identifies as the strong instrument
  here — replicates where win rates do not, and it needs **no second
  training run**. It should be the primary readout and the win rate the
  secondary.
- **Correction — the instrumentation gap this section originally
  claimed does not exist.** `CURRICULUM-LADDER.md` §5 records
  target-by-power as unbuilt ("the action log records the spell but not
  the target it was pointed at"), and an earlier revision of this doc
  repeated it. It has since been built: `EpisodeRunner` emits
  `tgtChose_p0..p6` beside `tgtLegal_p0..p6` — two parallel histograms,
  so the read is "chose p5 this often, could have chosen p5 this often",
  which is the right shape and better than what §5 asked for. **The
  primary readout is available today and needs no new code.**
  `CURRICULUM-LADDER.md` §5 should be corrected in place.

  One property of it matters for reading any B-branch result: the whole
  `tgt*` block is emitted only `if (targetCreatureChoices > 0)`, so on a
  policy that never casts its removal the counters are **absent from the
  probe file rather than zero**. Absent means zero; it does not mean the
  instrument is broken.
- **It says nothing about capacity**, which is the other lever Phase 8's
  verdict named.

## 7. Order of work

1. Close the target-by-power instrumentation gap (§6) — it is small, it
   is the primary readout, and `CURRICULUM-LADDER.md` has called it the
   cheapest unfinished diagnostic in the repo for two phases.
2. Emit slots 12–15, re-run `timing_gate.py` as the emission acceptance
   test, then the `cond-target` transfer matrix.
3. Emit slots 16–17 separately, re-run the gate expecting **LEVEL A to
   separate**, then the timing arm against `B1Fast`.
4. Only then, if either arm moved, `cond-both`.
