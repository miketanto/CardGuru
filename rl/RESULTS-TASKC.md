# Task C results — E0 (name-hash) vs E2 (graph features) on held-out cards

Same stack as Tasks B/D (PPO, terminal reward, IPC V1, HeuristicPlayer
v2 opponent). Arms differ ONLY in the candidate identity block:
E0 = 16-bucket name hash (cdim 38); E2 = 68-dim mechanical readout of
the CardGuru Forge ability graph + unknown flag (cdim 91). 3 seeds/arm.
Training pool: BenchBurn/BenchControl/BenchMidrange/BenchDimir mirrors,
interleaved per episode. Holdout decks: graph-selected functional
analogs (rl/holdout_pick.py), zero card overlap with the pool,
including two textually identical swaps (Remove Soul = Essence
Scatter, Counsel of the Soratami = Divination).

## Protocol amendments (both applied to BOTH arms, decided on
## in-distribution evidence before any holdout data existed)

1. Budget 2048 -> 1344 episodes: both arms flat (~0.50 pool) across
   three consecutive checkpoints (768/1024/1280) in seed 0.
2. Zero-shot = 200 games/seed/deck (600 pooled per arm-deck), split in
   100-game slices; eval seed block 970000+.

## Training curves (pool eval, 100 games)

Both arms learn the pool at the same rate after E2's slower start
(E2 seed 0 was at 0.04 at 256 eps vs E0's 0.28 - within a fixed pool,
graph features COLLAPSE functionally-similar cards that the hash keeps
distinct, so E2 must lean on base features longer). By 768: parity.
Final pool plateau both arms, all seeds: 0.37-0.53.

## In-distribution, per deck (100 games/seed, 300 pooled)

| deck | E0 | E2 |
|---|---|---|
| burn | .640 | .767 |
| control | .080 | .057 |
| midrange | .413 | .397 |
| dimir | .623 | .677 |

Per-seed spread is large (E0 burn: .76/.41/.75). Neither arm learned
the control mirror under pooled training - capacity went to the decks
that win faster. Arms matched overall.

## THE MEASUREMENT — zero-shot on held-out cards (600 games/arm/deck)

| holdout deck | E0 | E2 | E0 by seed | E2 by seed |
|---|---|---|---|---|
| burn | .608 | .677 | .67 / .70 / .455 | .675 / .58 / .775 |
| midrange | .435 | .455 | .46 / .395 / .45 | .465 / .44 / .46 |
| control | .292 | .238 | .205 / .455 / .215 | .235 / .245 / .235 |
| control STALLS | **15.5%** | **7.0%** | 34/27/32 per 200 | 0/22/20 per 200 |

**Spec decision rule: NOT MET.** E2 does not beat E0 by a CI-excluded
margin on >=2 of 3 holdout decks once seed-level variance is priced in
(game-level z on burn is ~2.4, but seed SDs of .10-.14 swamp it at
n=3 seeds; control's direction even favors E0, driven entirely by one
outlier seed).

## Few-shot recovery (128 fine-tune episodes on HoldoutControl,
## then 100-game eval @970000; baseline = zs slice on same block)

| arm | s0 | s1 | s2 |
|---|---|---|---|
| E0 | .16 -> .38 | .44 -> .30 | .24 -> .25 |
| E2 | .235 -> .28 | .29 -> .29 | .21 -> .29 |

No recovery-speed advantage either way; 128 episodes moves both arms
to a similar ~0.25-0.38 band (and can REGRESS a lucky zero-shot seed,
e.g. E0 s1).

## Robust secondary findings

1. **Base features do the transferring.** Zero-shot burn barely
   degrades from in-dist for either arm: mana value + stats + type
   are enough to play an archetype against analogs. Card identity -
   hashed or graphed - is not where transfer lives at this task depth.
2. **E2 is far more consistent when identity goes unfamiliar.**
   Holdout-control win rate across seeds: E2 .235/.245/.235
   (SD < .01) vs E0 .205/.455/.215 (SD .14). The graph gives every
   seed the same handle on unseen cards; the hash makes transfer a
   lottery over bucket collisions.
3. **E2 halves the freeze rate.** E0 pass-loops to the turn-80 stall
   bound in 15.5% of holdout-control games; E2 7%. Hash identity on
   unseen cards yields low value estimates everywhere -> passing
   dominates; graph features keep actions comparable.
4. Fixed-pool learning is mildly HARDER for E2 early (feature
   collapse among similar cards) - visible as the 0.04-at-256 start.

## Caveats

- 3 seeds; the consistency finding (2) is the one that most needs
  more seeds to harden.
- One eval-tag accounting wrinkle: e0 s0 trained-count label drifted
  by one 64-ep chunk mid-run (killed untracked chunk); checkpoint
  episode counters (authoritative) were re-synced and final budgets
  matched at 1344/1344. train.csv files in rl/taskc_curves/ are the
  ground truth.
- HeuristicPlayer v2 opponent throughout; stall = reward 0 and counted.
- Raw curves: rl/taskc_curves/*.txt / *_train.csv.
