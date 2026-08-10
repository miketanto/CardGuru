# Verdict — Phase 2: build the policy interface around yields

## The headline number

**Act-rate at k≥1: 6.9%–15.7% by archetype, ~10% typical** — measured
over 800 games (4 archetypes × 200) of a deterministic scripted
heuristic, stated as a floor on competent decision density. This is
squarely in the spec's "yields are worth another ~7×" regime and
nowhere near the ~40% that would have killed the abstraction.

## Consults per game, the three regimes

| Regime | Burn | Midrange | Control | Triggers |
|---|---|---|---|---|
| no gate | 216 | 322 | 880 | 502 |
| k=0 gate only | 112 | 204 | 806 | 325 |
| **gate + yields** | **63** | **71** | **244** | **131** |

Two facts the Phase 1 histogram could not show:
1. **The k=0 gate is weak exactly where it matters** — control mirrors
   almost always have a nominal playable (806 of 880 windows), so
   gating alone buys 9%. Yields cut the same games 3.3×.
2. **Yields also make the ENGINE 1.6–2.2× faster** (skipped windows
   never call `getPlayable`, the most expensive per-window operation),
   compounding with Phase 1's throughput numbers.

## Recommendation: yield-based policy interface

Build the v2 action space as: *act(action) | pass | yield(predicate)*,
with the wrapper auto-passing yielded windows. Grounds:

- 10% act-rate means a per-window policy burns ~90% of its consults —
  and its gradient signal — re-confirming passes. Median
  consecutive-pass runs are 10–18 windows long (p95 up to 40); each run
  is one yield.
- The predicate set {REACTIVE, MY_NEXT_MAIN} — two predicates! —
  already covers the heuristic exactly: equivalence replay is
  bit-identical for burn/midrange/triggers (50/50 each), and for
  control it matches the plain-vs-plain replay baseline (22/50 vs
  21/50) — i.e., yields add ZERO divergence beyond the engine's own
  instance instability (proven by control experiment, see
  RESULTS-PHASE2.md). The RL predicate set should add the spec's full
  list (UNTIL_PHASE(x), MANA_WOULD_EMPTY) as ACTIONS THE POLICY
  CHOOSES, not hardcoded rules.
- Dense auxiliary rewards remain useful but are no longer forced to
  carry the whole credit-assignment burden.

## Sub-action normalization (B7)

Callback sequences are short and tightly bounded: median 1–2, p95 ≤ 6,
max 6 across 800 games. **Per-action log-prob normalization is
sufficient**; no hierarchical decoder needed for this action space.
Watch two future classes that did not appear in these decks: X
announcements (integer head) and ordering choices (permutation head).

## Curriculum weights (B8)

Decision-density and throughput anti-correlate: control has 3.2× the
actions/game of burn at 0.4× the games/sec. To equalize DECISIONS SEEN
per archetype per wall-clock, sample inversely to
(games/sec × actions/game):

| Archetype | games/sec (yields) | actions/game | decisions/sec | weight (norm.) |
|---|---|---|---|---|
| Burn | 5.98 | 17.5 | 105 | 1.0 |
| Midrange | 7.70 | 25.1 | 193 | 0.5 |
| Control | 2.43 | 55.6 | 135 | 0.8 |
| Triggers | 3.72 | 28.6 | 106 | 1.0 |

(Weights ∝ 1/decisions-per-second, normalized to burn. The spread is
mild — ~2× — because low speed and high density partially cancel;
revisit when real decklists replace bench decks.)

## Caveats that must survive into v2 planning

1. **The heuristic is a floor.** It never holds mana with intent, never
   bluffs, casts tricks only at end steps. Real act-rates are higher;
   the yield conclusion is robust up to ~40%, so the margin is wide.
2. **Engine tie-breaking is not reproducible across game instances.**
   ComputerPlayer's internal choices follow UUID-set iteration order;
   the same seed can replay identically or not depending on hash
   layout. For RL this means: canonical action ordering must be
   imposed at the wrapper (we sort by name), and replay-based tests
   must tolerate benign drift or pin the choice layer. Deck order
   itself required canonicalization + per-player re-seeding inside
   shuffleLibrary (see RESULTS-PHASE2.md determinism findings).
3. **k-semantics**: `getPlayable` lists the pending land drop at
   illegal times; the environment wrapper must timing-filter the
   action set or the policy sees phantom actions (~1 per window, every
   window, all game).
4. **Control mirrors stall**: 18% of heuristic control games hit the
   turn-80 bound. Real RL self-play in control matchups needs either a
   turn budget in the reward or stall detection.

## What would still change the plan

- If a learned policy's act-rate at k≥1 rises above ~40% (it holds
  interaction far more than the heuristic), revisit — but 4× headroom
  from 10% makes this unlikely to flip the interface decision.
- If future archetypes (combo, X-spell decks) blow past 6-callback
  sub-action sequences, add the integer/permutation heads then.
