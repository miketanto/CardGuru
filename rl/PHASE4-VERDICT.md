# PHASE 4 VERDICT

## What was asked

Does opponent depth open the E0-vs-E2 gap that Task C found closed?
And is self-play (Track B) worth its cost?

## What happened, milestone by milestone

- **M0 (throughput):** the "4x gap" dissolved under measurement -
  rollout-only socket throughput is 1.00x pure engine on the same
  deck; IPC is 2% of wall-clock; training overhead 22%; 2-lane scaling
  1.87x. IPC V2 skipped: Amdahl-bounded to ~10-15% while the engine
  is 87% of cost. (PHASE4-THROUGHPUT.md)
- **M1-M2 (ladder):** SearchPlayer (perfect-info 1-3-ply minimax,
  GameStateEvaluator2 leaves) calibrated: D1 beats D0 at .776
  (500g CI). But D2/D3 are FLAT vs D1 (.52) - with a materialistic
  static evaluator, one ply extracts everything the evaluator knows.
  **The ladder has two rungs, not five.** The planned depth SWEEP
  cannot exist without a better evaluator, which would be a new
  instrument. (PHASE4-LADDER.md)
- **M4 (depth A/B, D0+D1, 3 seeds/arm):** training vs D1 converges
  below parity for both arms (the instrument bites). Zero-shot:
  win-rate parity on burn/midrange at both depths; pooled freeze gap
  persists at depth (E0 22.8% vs E2 17.2% on holdout control) but the
  per-seed consistency that made the Task C liveness finding
  compelling did NOT replicate - seeds now disagree, one even
  reverses. (PHASE4-DEPTH-AB.md)
- **M3 (novelty sweep): not run** - lanes were consumed by M4;
  it remains the cheapest open experiment.

## The honest synthesis

1. **The graph still hasn't bought win rate anywhere** - not at D0,
   not at D1, not zero-shot, not few-shot. Four independent
   measurements now agree. The fixed-deck/analog-transfer regime is
   simply not where card identity binds.
2. **The liveness (freeze) advantage is real on average but noisy per
   seed at depth.** It is a product argument (rotating formats,
   never-lock-up), not a strength argument, and it needs the M3
   novelty sweep and/or 5+ seeds to be a defensible claim.
3. **Depth as an instrument works but saturates immediately** - the
   deepest lesson of Phase 4. Strength above D1 requires evaluator
   quality, not node count. Any future ladder should dial the
   EVALUATOR (material-only -> +tempo -> +card-quality), not plies.
4. **Terminal-reward PPO at ~120k consults cannot beat even 1-ply
   search.** The RL agent's ceiling is currently set by its training
   signal, not its encoder. That reframes Track B: self-play's job
   would be to supply graded opponents and denser learning signal,
   and its success criterion "beats D4" should read "beats D1".

## Recommendation on Track B (the hard-stop decision)

**Do not start self-play yet.** Two cheaper experiments dominate it:
1. **M3 novelty sweep** (freeze rate vs training-pool size, both
   arms) - directly hardens or kills the one live differentiator, no
   new infrastructure.
2. **Evaluator ladder v2** (one search opponent, three evaluator
   tiers) - restores a monotone instrument for pennies, and gives
   Track B its anchors if it ever runs.
Self-play only becomes the right spend if (a) the liveness finding
survives M3 at scale, or (b) beating D1 becomes the goal in itself -
and then league design should follow the spec's Track B as written.

## Cost ledger (Phase 4)

~9,000 games: ladder calibration ~1,100, M4 training ~7,700 episodes
across 6 runs + 6 eval batteries + pool evals. Wall-clock ~7h on
4 cores. Two harness incidents (cold-torch server timeout; one
premature eval), both caught by guards, zero corrupted results.
