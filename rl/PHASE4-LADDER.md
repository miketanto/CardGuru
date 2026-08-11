# Phase 4 M1-M2 — search opponent + ladder calibration

## The instrument

`SearchPlayer` (benchmark package): depth-limited perfect-information
minimax over `Game.createSimulationForAI()` copies, leaves scored by
the mad module's `GameStateEvaluator2` (life/board/hand materialism -
reused unchanged, it is an instrument). Candidate execution follows the
ComputerPlayer6 pattern: activate on sim, drain stack with resolve +
applyEffects + checkStateAndTriggered (guard 25).

Documented choices:
- **Perfect info** (sims copy true hidden state): a "cheating"
  yardstick - deterministic, cheap, strictly harder to fool per node
  than determinized search. K (determinizations) = 0 by design.
- Search fires only when >1 non-mana playable exists; all other
  windows (and ALL combat) inherit HeuristicPlayer (=D0) behavior.
- Targets/modes inside candidates resolved by ComputerPlayer
  heuristics on the sim.
- Deterministic: RandomUtil reseeded from (benchSeed, decision#)
  before AND after each search, so node count cannot perturb the
  main game's stream.
- Dial: plies x breadth. Driver: -Drl.agent/opponent=search,
  -Drl.{agent,search}Plies/Breadth.

## Calibration (BenchDimir mirror, fixed seed blocks)

| match | games | result | nodes/decision |
|---|---|---|---|
| D1 (1 ply x8) vs D0 | **500** | **.776 (CI [.74, .81])** | ~2.9 |
| D2 (2 ply x6) vs D0 | 100 | .77 | ~10 |
| Db (1 ply x3) vs D0 | 100 | .79 | ~2.5 |
| D2 vs D1 | 100 | .52 | 8.1 vs 2.9 |
| D3 (3 ply x5) vs D1 | 60 | .52 | 8.6 vs 3.0 |

Throughput: D1 games run at 0.74-0.76 games/sec (vs 0.84 pure
heuristic) - the search tax at 1 ply is ~12%.

## VERDICT: the ladder is NOT monotone above D1 — it has two rungs

D0 -> D1 is one giant step (+27 points, CI-solid). D2 and D3 are flat
against D1 (.52, .52), and even breadth-3 D1 already captures the full
gain. Interpretation: **with a materialistic static evaluator and
perfect information, one ply of lookahead extracts everything the
evaluator knows.** Deeper minimax re-asks the same evaluator the same
material question; it cannot see what the evaluator cannot score
(tempo, card quality, holding interaction). This is the spec's §9
"ladder isn't monotone" branch - not a bug (D1>D0 replicates at 500
games; sims are deterministic; execution verified), but an evaluator
ceiling, caught exactly where the calibration gate was designed to
catch it.

## Consequences for the rest of Phase 4 (per spec §9, recorded now)

1. **M4 becomes a two-point curve**: the A/B runs at D0 (already done,
   Phase 3) and D1 (calibrated here). The D1-D4 sweep as drawn cannot
   run - there is no D2+ that is actually deeper in strength.
2. A stronger ladder needs a stronger evaluator (learned or
   hand-tuned). That is a NEW instrument and must be versioned as
   such; it is not a mid-sweep tune. Candidate: use a trained value
   head as the leaf evaluator - but that couples the instrument to the
   thing being measured; defer to Track B where self-play checkpoints
   provide the graded opponents instead.
3. D1 is a better anchor than D0 for Track B regardless: 77.6% over
   the Phase 2/3 yardstick, still cheap (12% tax), deterministic.
4. M3 (novelty sweep) is unaffected - it never needed the ladder.
