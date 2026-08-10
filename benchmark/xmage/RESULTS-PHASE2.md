# Phase 2 results — decision density and the yield abstraction

Hardware/pin: same as Phase 1 (`7554968c`, 4-core Xeon 2.8GHz, 15 GB,
JDK 21). ≥200 games per config (mirror matches), 5 warmup games per
JVM, turn bound 80. Sources: `src/HeuristicPlayer.java`,
`src/P2Stats.java`, `src/P2DecisionDensityBenchmark.java`; driver
`p2_sweep.sh`; decks `Bench{Burn,Midrange,Control,Triggers}.dck`.

## The instrument (what we measured)

`HeuristicPlayer` — deterministic, search-free, deliberately simple:

- **Sorcery speed** (own main, empty stack): land first, then the
  highest-MV affordable creature, then the highest-MV affordable
  sorcery, else pass. Ties broken by card name.
- **Instant speed**: counter an opponent's stack object if a known
  counterspell is playable (Counterspell/Cancel/Essence Scatter/Mana
  Leak); at the opponent's end step, cast the highest-MV playable
  instant; else pass.
- **Combat**: attack unless some untapped defender both kills the
  attacker and survives; block when the blocker kills and survives, or
  chump anything when unblocked damage is lethal.
- Targets/modes/costs inside a chosen action resolve via
  ComputerPlayer's cheap heuristics; every such callback is counted (B7).
- Mulligans are skipped (always keep 7): the instrument measures play
  density, not mulligan luck.

**Stated caveat:** this is a FLOOR on decision density. A strong human
represents more interaction (holds up mana with intent, plays
combat tricks in combat, bluffs). Act-rates below are lower bounds.

## Yield predicates (B6)

Emitted by the policy when it passes on an empty stack:
- `REACTIVE` (holds an instant in hand): wake on stack non-empty, OR
  opponent's END_TURN step, OR any DECLARE_BLOCKERS step, OR own main
  phase.
- `MY_NEXT_MAIN` (no instants in hand): wake at own main phase.
Any action or combat callback clears the yield. Windows skipped by an
active yield are auto-passed without consulting the policy.

`YIELD_UNTIL_MANA_WOULD_EMPTY` (CR 500.4) was NOT implemented: the
heuristic never floats mana, so the predicate would never bind — noted
as future work rather than approximated silently.

### Equivalence (correctness gate) — PASS, after catching two real bugs

Replaying the same seeds per-window vs with-yields produces **identical
action logs and identical canonical final states: 50/50 games (aggro),
50/50 games (control)**.

The gate caught two genuine yield bugs during development — exactly the
silent-agent-can't-play-instants class the spec warned about:
1. `YIELD_UNTIL_MY_NEXT_TURN` set during one's own upkeep slept through
   that same turn's main phase (fix: semantics changed to "wake at my
   next MAIN PHASE").
2. A reactive yield could sleep through the holder's own main phase
   (fix: own-main wake added to REACTIVE).

### Determinism findings (affects any replay/corpus infrastructure)

Two engine-level facts surfaced while making replays bit-identical:
- **Deck order is not a pure function of the seed.** Libraries shuffle
  from the single global RandomUtil stream in player-map iteration
  order, AND the pre-shuffle library order comes from UUID-keyed sets —
  both vary per game instance. The harness fixes this by canonicalizing
  (sort by name) and re-seeding per (seed, player, shuffle-index) inside
  `shuffleLibrary`. Any future RL reset path must do the same or
  equivalent.
- **List-order tie-breaks are not reproducible.** `getPlayable()` order
  follows hand-set UUID iteration; a policy that picks "first best"
  diverges across instances. The instrument tie-breaks by card name; a
  real policy must consume a canonically ORDERED action set.

<!-- P2_TABLES -->
