# Phase 5 C0 — SearchPlayerIP: is perfect information load-bearing?

## Question

Phase 4's D1 (SearchPlayer 1-ply x breadth-8, GameStateEvaluator2 leaves)
is a PERFECT-INFORMATION instrument: sims copy true hidden state. Before
using D1 as an imitation teacher (C1) or a shaping source (C2a), C0 asks
whether an honest, imperfect-information version of the same search keeps
the D0->D1 step — i.e. whether the cheat is load-bearing.

## Instrument

`SearchPlayerIP` (benchmark package, mirrored): identical minimax
skeleton, evaluator, candidate ordering, and breadth cap to SearchPlayer;
the only change is that each candidate is scored as the MEAN over K
determinizations. A determinization is a sim copy whose hidden zones are
re-randomized before anything executes:

- opponent hand + library pooled and re-dealt (decks are known mirrors,
  so "decklist minus observed" == shuffle hidden cards among hidden
  slots) — the MCTSNode.randomizePlayers pattern;
- own library order shuffled too (an honest player knows its own hand
  but not its library order; candidate sims that draw would otherwise
  read the true order). This goes slightly beyond the handoff's
  "opponent hidden zones" spec, in the honest direction, at zero cost.

Determinism: RandomUtil reseeded per (benchSeed, decision#, k); after
each search the stream is re-keyed exactly as SearchPlayer does, so a
SearchPlayerIP seat perturbs the main game identically to a SearchPlayer
seat. Dial: plies x breadth x K. Driver: `rl.agent/opponent=searchip`,
`rl.agentDetK`/`rl.detK` (default 4). Runner: `rl/c0_calib.sh`.

## Environment note (fresh container)

The XMage checkout was rebuilt from scratch this session (pin 7554968c +
bounded getAttackablePlayers patch + mirrored sources). Validation:
D1 vs D0 replicates at .71 over 100g (Phase 4: .776 over 500g,
CI [.74, .81]) and nodes/decision is 2.9, an exact match. Two latent
harness fixes landed with the rebuild: the driver now runs
CardScanner.scan() itself (MageTestPlayerBase never scans — a fresh
checkout had an empty card DB), and RLPlayer.actionLog was restored
after mirror drift.

## Calibration (BenchDimir mirror, stopTurn 80, PHASE4-LADDER protocol)

| match | games | seed block | result | nodes/decision |
|---|---|---|---|---|
| D1ip (1x8, K=4) vs D0 | **500** | 960000 | **.728 (CI [.69, .77])** | 11.6 (= 4 x 2.9) |
| D1ip vs D1 (head-to-head) | **500** | 960000 | **.482 (CI [.44, .53])** | 11.6 vs 2.9 |
| D2ip (2x6, K=4) vs D0 | 100 | 950000 | .70 | 39.5 |
| D2ip vs D1 | 100 | 950000 | .52 | 30.5 vs 3.0 |

Zero stalls in all four. Throughput: D1ip-vs-D0 games run at 0.49
games/sec vs 0.66 for D1-vs-D0 on this container — the K=4
determinization tax is ~25% of game wall-clock.

## Findings

1. **Perfect information is NOT load-bearing at 1 ply.** D1ip keeps
   +22.8 of D1's +27.6 points over D0, and the direct head-to-head is
   statistically even (.482, CI spans .50). Mechanistically this makes
   sense: at 1 ply the search never simulates opponent action, and
   GameStateEvaluator2 scores hand SIZE not contents, so hidden state
   only enters through library-order reads during candidate execution
   (draw/mill triggers). Empirically that leak is worth ~0.
2. **Honesty doesn't collapse at depth either — the evaluator ceiling
   binds first.** D2ip vs D1 is .52, the same flatness Phase 4 found
   for perfect-info D2 vs D1 (.52). Depth 2 is where determinization
   actually bites (opponent replies are simulated from a re-dealt
   hand), and it neither gains nor loses: the materialistic evaluator
   remains the ceiling regardless of information regime.
3. **The two-rung ladder survives the honesty change.** D0 -> D1ip is
   the same giant step, and the D1-level plateau is unchanged. Any
   Phase 5 use of "search opponent" may treat D1 and D1ip as
   interchangeable in strength.

## BRANCH TAKEN: proceed to C1 (imitation from D1)

C0's gate was: an honest search player must retain the D0->D1 step,
otherwise imitation/shaping targets built from D1 would be laundering
hidden information into the student. It passed. Consequences for C1:

- **Use plain D1 as the imitation teacher.** Its decisions are
  ~equivalent to the honest player's (head-to-head .482 over 500g) and
  it is 4x cheaper per decision (2.9 vs 11.6 nodes) and deterministic.
  C0 is the license for this shortcut; if C1's student ever needs
  re-auditing, D1ip logging is a drop-in swap.
- The RL agent's state encoding sees exactly what an honest player
  sees, so imitation targets from D1 are now defensible.
