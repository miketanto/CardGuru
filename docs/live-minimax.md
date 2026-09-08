# Live minimax: a real simulation-backed attack search inside a running game

This is the culminating piece of the Stackwise agent: at the declare-attackers
decision of a **live** XMage game, the driver builds a genuine depth-~1.5
minimax tree by **rolling out candidate attacks on disposable copies of the real
game** and backing up the value the opponent's best block leaves us. It is the
PokeChamp shape (our move = max, opponent response = min, value at the leaf),
scoped to the one decision where it matters most in aggro.

Every claim below is grounded in engine code that was read and run; file/line
references are against the checkout at `~/Documents/mage` (Java 24, Maven 3.9).

## The rollout primitive: `Game.createSimulationForAI()`

`GameImpl.createSimulationForAI()` (`Mage/.../game/GameImpl.java:269`) is:

```java
public Game createSimulationForAI() {
    Game res = this.copy();
    ((GameImpl) res).simulation = true;
    ((GameImpl) res).aiGame = true;
    return res;
}
```

i.e. a **full deep copy** of the entire game (battlefield, stack, players,
combat, zones — `copy()` preserves every permanent's UUID) flagged
`simulation=true`. This is exactly the primitive XMage's own MAD AI uses to
think: `SimulatedPlayer2`, `ComputerPlayer6`, and `CombatUtil` all call it
(`grep -rn createSimulationForAI`). Because permanent IDs are stable across the
copy, we can name the same attacker/blocker on the copy that we see on the real
game — which is what `CombatUtil.willItSurviveSimulation`
(`.../ai/util/CombatUtil.java:280`) does, and the recipe our leaf resolution
mirrors.

We never mutate the real game while searching; each candidate gets its own
copy, which is discarded.

## The tree we build

At `InteractiveTestPlayer.selectAttackers` (driver
`CardGuruScenarioRunner.java`), with `-Dcardguru.minimax=attacks`:

```
                 selectAttackers (REAL game)
                          |
        ┌───────── MAX over attack sets ──────────┐      (our move)
        │           (a handful, not 2^n)          │
   attack-none   attack-all   hold[X]   hold[Y] ...
        │                                          │
        │  createSimulationForAI(); declare the    │      (engine rollout
        │  exact set on the COPY; resolve.         │       on a copy)
        ▼                                          ▼
   ┌─── MIN over opponent block responses ───┐            (opponent reply)
   │  no-block, each legal 1-1 block, greedy  │
   │  full block — resolved on a copy each    │
   └──────────────────────────────────────────┘
        │
        ▼
   LEAF: GameStateEvaluator2.evaluate(us, copy).getTotalScore()
         (+ our own life/board terms emitted for the trace)
```

- **MAX layer — candidate attack sets** (`candidateAttackSets`): `attack-none`,
  `attack-all`, and `hold-one-creature-back` for each available attacker,
  deduplicated. A deliberate handful (n+2 before dedup), so this is a real tree
  rather than an exhaustive `2^n` enumeration — matching the brief's "start
  simple" instruction.
- **engine step** (`evaluateAttackSet`): `createSimulationForAI()`, then
  `sim.getPlayer(us).declareAttacker(atkId, defenderId, sim, false)` for each
  chosen attacker (the same `declareAttacker` primitive the harness uses on the
  real game), then `checkStateAndTriggered()` + drain the stack.
- **MIN layer — opponent blocks** (`enumerateBlockResponses`): on the
  post-attack copy we enumerate a bounded set of block responses — no-block,
  every legal single 1-1 block (`blocker.canBlock(attacker)`), and one greedy
  "block the biggest threat with each blocker" full assignment — capped at
  `MAX_BLOCK_RESPONSES = 16`. Each response is applied on **its own** copy
  (`afterAttack.copy()`) via `defender.declareBlocker(...)`, combat is resolved
  (below), and we take the response that **minimises our leaf value**. Because
  `GameStateEvaluator2`'s score is player-minus-opponent, minimising our score
  is identical to maximising the defender's — exactly what the built-in MAD
  block heuristic optimises. So this min-layer is a faithful stand-in for "the
  opponent picks its best block". (See the deviation note below on why we
  compute it by value-minimisation rather than by calling ComputerPlayer6.)
- **combat resolution on the copy** (`applyBlocksAndResolveCombat` +
  `simulateStep`): mirrors `CombatUtil.willItSurviveSimulation` /
  `CombatUtil.simulateStep` exactly — fire `DECLARED_BLOCKERS`,
  `checkStateAndTriggered`, drain the stack, then step
  `CombatDamageStep(true)` (first strike), `CombatDamageStep(false)` (normal
  damage), `EndOfCombatStep`, draining the stack after each. `simulateStep` is
  `private` in `CombatUtil`, so it is replicated verbatim in the driver
  (set the step, `beginStep`, drain stack, `endStep`).
- **LEAF** (`GameStateEvaluator2.evaluate`, `.../ai/score/GameStateEvaluator2.java:27`):
  the engine's own AI leaf evaluator, scored from our seat. We also emit our own
  life/board terms (`a_life`, `b_life`, `a_board`, `b_board`) in the trace, in
  the spirit of `cardguru/value.py`, so the Python side can score the same
  leaves with its linear value if desired.

We back up **max-over-min** and apply the argmax attack set to the REAL game
with `declareAttacker`.

## How blocks are obtained on the copy — and the one honest deviation

The brief's ideal was: on the copy, "let the OPPONENT (the built-in AI on the
copy) choose blocks". Two engine facts forced a precise, smaller-footprint
implementation, documented here rather than papered over:

1. **The seated opponent's block AI is a no-op stub.** The interactive harness
   seats playerB as a `TestPlayer` wrapping a `TestComputerPlayer`, which
   `extends ComputerPlayer` (the base AI in `Mage.Player.AI`). Base
   `ComputerPlayer.selectAttackers`/`selectBlockers`
   (`.../ai/ComputerPlayer.java:910,915`) are literally `// do nothing, parent
   class must implement it`. The real combat AI lives only in
   `ComputerPlayer6` (the MAD plugin), which overrides them
   (`ComputerPlayer6.java:1157,1163`) and delegates block choice to
   `CombatUtil.blockWithGoodTrade2`.
2. **The MAD plugin is not on the test classpath.** `Mage.Tests/pom.xml`
   depends on `mage-player-ai` but **not** `mage-player-ai-mad`, so
   `CombatUtil`/`ComputerPlayer6` cannot be called from the driver without
   editing the engine's build — and the driver is deployed as a single `.java`
   file copied into the checkout (`cardguru/adjudicate.py:ensure_driver`), so a
   pom edit would not travel with it and would break reproducibility.

**Deviation:** instead of invoking `ComputerPlayer6`'s block wrapper, the driver
computes the opponent's best block itself by **minimising the engine's own
`GameStateEvaluator2` over enumerated block responses, each resolved on a game
copy**. This uses the very evaluation function the MAD block heuristic
optimises, so the min-layer is a genuine engine-grounded opponent response — it
just skips the MAD wrapper's heuristic short-cuts (and its multi-blocker
subtleties). This is the "smallest working alternative" the brief explicitly
permits, and it keeps the driver a single self-contained file on the existing
classpath.

A second consequence is worth stating plainly: because playerB's live combat
callbacks are the base stubs, **the live opponent never actually blocks or
attacks in the real game** — it only plays lands/spells at priority. So the
minimax search's min-layer is real (it weighs blocks the opponent *could* make),
but the *live* game does not exercise the opponent's blocking. See
"Limitations".

## Exposure (design A — in-driver search)

The brief offered two designs; this ships design **A**: the
`InteractiveTestPlayer`, at `selectAttackers`, runs the search itself and plays
the argmax. The external Python policy is **not** consulted for attacks (it
still answers mulligan/priority/blockers over the spool). The "agent" for
attacks *is* the search. Enabled with `-Dcardguru.minimax=attacks`; without it
the attackers decision round-trips to Python exactly as before, so the existing
`dumb`/`pass`/`belief` policies are unchanged.

Per-decision proof-of-work is appended to `spool/minimax.jsonl` (one JSON object
per attack decision: turn, `candidate_sets`, per-candidate value +
block-response count, and the chosen set with its leaf terms). Python reads it
after the game (`MatchClient.read_trace`) and folds a summary into the match
result.

## Running it

```
python3 -m cardguru play --games 2 --policy dumb --minimax \
    --mage-repo ~/Documents/mage
```

`--minimax` launches the driver with `-Dcardguru.minimax=attacks` and uses the
`dumb` policy for the non-attack decisions the search does not own.

## Limitations (honest scope)

- **Only attacks, only depth ~1.5.** No priority/spell search, no look-ahead past
  the opponent's block. That is the intended PokeChamp-shaped scope.
- **The live opponent does not block or attack.** The seated `TestComputerPlayer`
  has no-op combat callbacks (see deviation above); it is the base AI, not
  COMPUTER_MAD. Win/loss is therefore **integration evidence, not an agent
  strength result** — and the deck is a tiny hardcoded mono-red aggro list
  (`writeInteractiveDeck`) chosen so combat happens at all.
- **The min-layer approximates the MAD block AI** by value-minimisation over a
  bounded, mostly 1-1 block enumeration; it does not reproduce MAD's
  multi-blocker/trigger handling.
- **Combat resolution reuses the 2012-era `simulateStep` recipe** from
  `CombatUtil`; exotic combat replacement effects may resolve imperfectly on the
  copy. Fine for a vanilla-creature aggro deck.

## The single biggest limitation

The min-layer is a real engine rollout, but the **live** opponent it plays
against cannot block (base-AI stub combat), so the search's cleverness is never
truly pressure-tested in the games it wins. Making the live opponent block —
either by putting `mage-player-ai-mad` on the test classpath and seating a
`ComputerPlayer6`, or by driving the same value-minimising block chooser from
playerB's `selectBlockers` — is the one change that would turn this from "a
verified real search" into "a search demonstrably beating a blocking opponent".
