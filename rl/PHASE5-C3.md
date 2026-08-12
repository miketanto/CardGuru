# Phase 5 C3 — DAgger: is covariate shift the binding constraint?

## Question

C1/C2a left a specific hypothesis: the student matches the teacher
offline (97%) but not online because it gets no labels on the states
IT visits. C3 tests it two ways, both built on the searchBest/
choosePolicyActionStatic refactor (the full D1 policy callable from
any seat).

## Rounds

1. **Noise-injected DAgger** (rl.daggerEps): teacher plays, but with
   prob .25 takes a uniform-random action at decisive windows; labels
   are always the teacher's pick. 600 eps -> 115,798 examples
   (deviation RNG isolated from RandomUtil after measuring 40%
   first-draw-after-sequential-seed bias; teacher still .458 vs D1
   while playing 25% random at decisive points).
2. **True DAgger** (RLPlayer.shadowOut): the STUDENT plays its own
   games vs D1 while a shadow teacher labels every consulted priority
   window. 600 eps -> 39,021 labels. The smoke data measured the
   covariate gap directly: **35% of labels on student-visited states
   are act-labels vs ~8% on teacher trajectories** - the student
   really does wander into act-here states it was never taught.

Each round retrained the same E0 net on the aggregate (up to 2,200
episodes / ~425k examples).

## Results (500g @960000, 4-deck pool)

| system | vs D1v3 | vs D0v3 | stalls vs D1 |
|---|---|---|---|
| BC (v3 baseline) | .396 | .428 | 8.6% |
| + noise-DAgger | .398 | .412 | 6.8% |
| + true DAgger | **.396** | .456 | 8.4% |
| BC + PPO (C2a, best) | **.442** | .442-.476 | 10-13% |
| teacher (refs) | ~.504 mirror | .614 Dimir | 0 |

(An earlier .054/.082 "collapse" was an artifact - a path bug left the
checkpoint unwritten and the evals served a random-init net; voided.)

## Findings

1. **Covariate shift is NOT the binding constraint.** Exactly-on-policy
   teacher labels moved the D1 win rate by 0.000. The hypothesis had
   the right mechanism (the 35%-vs-8% gap is real) but the wrong
   bottleneck.
2. **The student underfits its own state distribution.** Validation on
   shadow-heavy episodes: 90.2% (71.7% non-pass) vs 96.8% on teacher
   trajectories. Given labels for its own states, the E0 net cannot fit
   them - a representation/capacity floor, not a data floor. More
   DAgger rounds would sharpen this number, not the win rate.
3. **Direct objective optimization remains the best use of interaction:**
   C2a's plain PPO (.442) beats every imitation variant. Signal beats
   supervision once supervision saturates.
4. Where the remaining teacher gap plausibly lives, in order: (a) the
   ~10% of priority decisions the net cannot represent with 38-dim E0
   candidates; (b) combat/target windows (never shadow-labeled); (c)
   decision-importance weighting (accuracy is not uniformly
   distributed over decisiveness).

## BRANCH TAKEN: C-track CONCLUDED at its measured ceiling

The imitation family (BC, +noise-DAgger, +true-DAgger) saturates at
~.40 vs D1; imitation+RL tops at ~.44; the teacher itself is ~.50 in
the mirror. Between here and "beats D1" stand capacity/encoding and
combat - not more demonstrations and not more shaping. Continuing to
C4/C5-style variations of the same family would spend games against a
proven ceiling. The evidence-backed next levers, if the goal remains
beating D1: a wider candidate encoder + bigger net trained with
RL-from-BC (capacity), shadow labels for combat (coverage), or
self-play league (Track B as re-anchored by PHASE4-VERDICT). Phase 5's
remaining planned milestone is M3 (novelty sweep) - independent of
this ceiling and still the cheapest open experiment.
