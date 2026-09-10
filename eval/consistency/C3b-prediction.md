# Arm D pre-registration — param values + the `true` rule

**Written and committed before the run.** The C3 ablation's weakness was that I named
its target stratum (`H02`) only after seeing which arm won. R5 is only enforceable if the
prediction is on record first, so this is.

## What changed

Two things, shipped together because they address one mechanism:

1. **`research/data/param_values.json`** — mined value space for the 123 parameters whose
   top-12 values cover ≥55% of their uses. `Defined` (16,748 uses, 279 distinct, top-12
   covers 81%) now shows `Player.Opponent` and `Opponent` explicitly; `Destination` (16
   values, 100%); `Origin` (40 values, 99%); `Event` (34, 97%). Emitted as a `PARAM VALUES`
   block.
2. **Two `DSL_SPEC` rules** — constrain param *values* rather than asserting the key
   exists with `true`, and prefer an exact value from the mined list over a substring
   guess.

Prompt grows 29,023 → 43,952 chars (~11k tokens), behind the existing ephemeral cache.

## Mechanism being tested

Full vocabulary told the compiler *which parameter names exist*. It still had to guess
what they contain, and fell back on `{"ValidPlayers": true}` — "this key is present with
any value" — which matched every mass-damage ability touching players, so "damage to each
opponent" returned Anger of the Gods (3 damage to each *creature*). Hand-tightening that
one query to constrain the value took the result from 358 cards to 250, kept all three
witnesses, and dropped both foils.

## Predictions, in order of confidence

1. **`foil rate` falls.** This is the primary claim: value-anchoring is a *precision*
   intervention. v2 was 0.110 across the full set. I expect **≤0.05**. If foil rate does
   not fall, the intervention did not do the one thing it was designed to do.
2. **`H03` (scope/quantifier — I08, I11, I37) improves on PC.** This is the R5 target
   stratum, named now. v2 `H03` mean PC is the comparison point. I expect a gain, smaller
   than C3's +0.143 on `H02` because only three rows and two of them already score well.
3. **Headline PC moves little, and may fall slightly.** Value-anchoring makes queries
   *narrower*. v2's PC gain came partly from broader queries overlapping more — the
   pattern I flagged as unbanked. Tightening should trade a little PC for precision. **A
   small PC drop with a large foil drop is a pass, not a failure**, and I am saying so
   before seeing the number rather than after.
4. **`I20`'s hook leak closes.** The facet-selectivity annotation shipped with v2 but was
   never measured. v2 had `hook: reanimator` (1,227 faces) on all five rungs against a
   precise 82-face question, foil rate 1.00. With the count now shown in the prompt I
   expect the compiler to drop the facet branch. This is a separate change riding along;
   it gets credited separately.

## What would make me revert

- Foil rate flat or up **and** PC down → the block is noise, costing 15k chars for nothing.
- `agreement@witness` falls below v2's 0.963 → tightening has gone too far and is now
  excluding correct answers, which matters more than either headline metric.

## Protocol

Identical to v2: 40 intents × 5 rungs, sample 0, one rung per agent so no compiler
instance sees two paraphrases of one intent, batches frozen on disk before launch.
Compared against v2 at the same k, same set, same harness — only the prompt differs.
