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

A second, larger consequence surfaced when the games actually ran: base
`ComputerPlayer.priority` is itself a stub —

```java
public boolean priority(Game game) {
    // minimum implementation for do nothing
    pass(game);
    return false;
}
```

(`.../ai/ComputerPlayer.java:388`). The real *playing* AI (cast a spell, play a
land, attack, block) lives **entirely** in `ComputerPlayer6`, which overrides
`priority` with its simulation loop. So the seated `TestComputerPlayer`
opponent, `setAIPlayer(true)` or not, **passes every priority and declares no
attackers and no blockers** — across a full 39-turn game it kept **zero
permanents** (verified in the trace: `b_board=0` every decision, `b_life`
ticking down only from our chip damage). The live opponent is effectively a
do-nothing player. The minimax search's min-layer is therefore *correct code*
that ran on every decision, but because the live opponent never develops
blockers, it almost always finds only the no-block response. See "Limitations"
— this is the single biggest one.

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

## Verified end to end (2026-09-08)

Built and run, not reasoned about. `mvn -pl Mage.Tests test-compile` is clean
(the driver + `InteractiveTestPlayer$AttackEval` compile). Two full games
played to a natural winner:

```
$ python3 -m cardguru play --games 2 --policy dumb --minimax
-- dumb+minimax policy vs COMPUTER_MAD: 2W / 0L / 0E over 2 game(s)
  game1: winner=A turns=31 attack_decisions=11 total_candidate_sets=41
  game2: winner=A turns=27 attack_decisions=11 total_candidate_sets=36
```

A single decision's full record (the search's proof-of-work, from
`spool/minimax.jsonl`), showing the max-layer choosing `attack-all` over
`attack-none` because the rollout leaf leaves the opponent one life lower:

```json
{ "turn": 5, "available_attackers": 1, "candidate_sets": 2,
  "chosen": "attack-all", "chosen_value": 1487.0, "chosen_block_responses": 1,
  "chosen_leaf": {"engine_score": 1487.0, "a_life": 20, "a_board": 2,
                  "b_life": 19, "b_board": 0},
  "candidates": [
    {"label": "attack-none", "value": 1417.0, "block_responses": 1,
     "leaf": {"a_life": 20, "b_life": 20, "a_board": 2, "b_board": 0}},
    {"label": "attack-all",  "value": 1487.0, "block_responses": 1,
     "leaf": {"a_life": 20, "b_life": 19, "a_board": 2, "b_board": 0}} ] }
```

`block_responses: 1` because the opponent had no blockers (`b_board: 0`) — see
the limitation below on why the live opponent never develops a board.

## Limitations (honest scope)

- **Only attacks, only depth ~1.5.** No priority/spell search, no look-ahead past
  the opponent's block. That is the intended PokeChamp-shaped scope.
- **The live opponent does nothing.** The seated `TestComputerPlayer` is the
  base AI, whose `priority`/`selectAttackers`/`selectBlockers` are all
  do-nothing stubs (the playing AI is `ComputerPlayer6`/MAD only). It plays no
  lands or spells, and never attacks or blocks. Win/loss is therefore **pure
  integration evidence, not an agent strength result** — playerA wins by
  unopposed chip damage. The deck is a tiny hardcoded mono-red aggro list
  (`writeInteractiveDeck`) chosen so playerA at least has creatures to attack
  and search over.
- **The min-layer approximates the MAD block AI** by value-minimisation over a
  bounded, mostly 1-1 block enumeration; it does not reproduce MAD's
  multi-blocker/trigger handling.
- **Combat resolution reuses the 2012-era `simulateStep` recipe** from
  `CombatUtil`; exotic combat replacement effects may resolve imperfectly on the
  copy. Fine for a vanilla-creature aggro deck.

## The single biggest limitation

The min-layer is a real engine rollout, but the **live** opponent it plays
against does nothing at all — base `ComputerPlayer` passes every priority and
has stub combat, so it never develops a board, never attacks, and never blocks.
The search runs correctly on every turn, but with an empty opposing board it
almost always sees only the no-block response, so its max-over-min collapses to
"attack for the most damage" and is never truly pressure-tested in the games it
wins. The one change that would make this a search *demonstrably beating a real
opponent* is to seat `ComputerPlayer6` (the MAD AI) as playerB — which means
putting `mage-player-ai-mad` on the `Mage.Tests` classpath (a pom edit the
single-file driver deployment currently avoids) and seating it in place of the
base `TestComputerPlayer`. Everything upstream of that — the copy-based rollout,
the tree, the leaf evaluation — is already real.
