# Phase 4 M4 — the depth A/B (D0 vs D1 rows)

Protocol identical to Task C (same pool, holdout decks, eval blocks,
1280-episode budget with the three-flat-checkpoints rule) except the
opponent: D0 = HeuristicPlayer v2 (Phase 3 data), D1 = SearchPlayer
1-ply (the calibrated .776 rung). **3 seeds/arm at D1** (user-directed
cut from the spec's 5; D0 row is Task C's 3 seeds). Consults as
primary unit: D1 training games average ~90-100 agent consults/ep;
1280 episodes is roughly 120k consults per run.

## Training vs D1

Both arms converge BELOW parity against D1: pool evals plateau at
.34-.42 (E0) and .26-.38 (E2) by 1024-1280 episodes, vs cruising past
.50 against D0. Terminal-reward PPO at this budget cannot beat the
1-ply searcher - the depth instrument works as intended.

## Zero-shot holdout, pooled over 3 seeds (600 games/arm/deck)

| deck | metric | E0 @D0 | E2 @D0 | E0 @D1 | E2 @D1 |
|---|---|---|---|---|---|
| burn | win | .608 | .677 | .608 | .617 |
| midrange | win | .435 | .455 | .365 | .363 |
| control | win | .292 | .238 | .220 | .288 |
| control | **freeze** | **15.5%** | **7.0%** | **22.8%** | **17.2%** |

Per-seed freeze on holdout control at D1:
E0 = 33% / 15.5% / 20%; E2 = 11% / 14.5% / 26%.

## Findings

1. **Depth raises freeze rates for BOTH arms** (E0 15.5->22.8%, E2
   7->17.2%). The searcher grinds value instead of mercy-killing a
   passive opponent, so lock-ups run to the turn bound more often.
2. **The pooled freeze gap persists at depth (E0 +5.6 points) but the
   per-seed picture no longer supports the clean Task C story.** At
   D0, E2's advantage was seed-invariant (0/22/20 stalls vs 34/27/32).
   At D1 the seeds disagree: one seed shows a huge E2 advantage
   (11% vs 33%), one shows none, one REVERSES (26% vs 20%). The
   "graph = liveness" claim survives on the pooled average only.
3. **Win-rate parity holds at depth** on burn and midrange
   (differences <=1 point pooled). Holdout control flips to a nominal
   E2 advantage (.288 vs .220) - but control numbers carry the freeze
   confound and seed noise in both arms; not a CI-defensible gap at
   n=3.
4. The prediction ledger (spec 3c): "freeze gap persists or widens at
   every depth" - pooled: CONFIRMED (persists, does not close);
   per-seed: WEAKENED. "Win-rate gap opens around D2-D3" - untestable
   as specified (the ladder has no D2+; see PHASE4-LADDER.md).

## Caveats

- 3 seeds/arm at D1, not 5: directional evidence, not a variance
  claim. This is exactly the sample size the spec warned about.
- D0 and D1 rows share decks/blocks but D0 numbers come from Task C
  runs trained vs D0; each row's agents trained vs their own row's
  opponent (the spec's design - depth changes both teacher and
  examiner).
- One e2 s2 eval was accidentally run at 1152 episodes and discarded
  (curve line labeled trained=1152); the 1280 battery is authoritative.
- Raw data: rl/p4_curves/.
