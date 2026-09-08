# Live-match feasibility: can XMage's test harness host a real interactive game?

P5's remaining step is the *interactive bridge* — a genuine 1v1 game where our
agent (playerA) makes each decision from outside the JVM while playerB is
XMage's built-in AI. This is the first thing in the project that is NOT a
variation of the scenario adjudicator (which runs a predetermined script and
stops). This doc records what the XMage source actually supports, so we build
on fact rather than hope.

All line references are against the checkout at `~/Documents/mage`
(`181b465f`), Java 24 / Maven 3.9.

## Verdict: FEASIBLE, with one honest simplification for the MVP

Both halves of the requirement are directly supported by the existing test
framework — no fork of the engine, no driving `GameController` by hand, no
custom low-level `Player` needed:

1. **playerB = real built-in AI (the "MAD" ComputerPlayer):** a `TestPlayer`
   flipped to `setAIPlayer(true)` delegates *every* decision to its wrapped
   `computerPlayer`, which is a `TestComputerPlayer extends ComputerPlayer`
   (`Mage.Player.AI/.../ComputerPlayer.java`) — i.e. the standard XMage AI,
   the same class the server seats for a `COMPUTER_MAD` human-vs-AI table.
2. **playerA = externally driven, interactively:** a `TestPlayer` subclass can
   override the decision callbacks and, inside each, *block* on a spool
   round-trip (write request file, poll for response file) exactly the way the
   scenario server already blocks waiting for `in/*.json`. The game runs
   synchronously on a single thread, so blocking a callback simply parks the
   game until the external policy answers.

The simplification (see "MVP scope" below): the MVP externalizes the
*top-level* decisions — mulligan, which play to make at priority, which
creatures attack, which creatures block — and lets the wrapped AI resolve
*fiddly sub-choices* (individual spell targets, mana payment, X values) for
now. That is enough for a real, complete aggro game driven from Python, and it
isolates the one remaining piece of work for full LLM control (see "biggest
remaining blocker").

## Why it works — the four load-bearing facts

### 1. The whole game runs synchronously on one thread inside `execute()`

`CardTestPlayerAPIImpl.execute()` (line 244) ends in
`currentGame.start(activePlayer.getId())` (line 324). `GameImpl` then runs its
own play loop — `while (!hasEnded())` (`GameImpl.java:1564`) — to completion on
the *calling* thread. Every time a player must decide, the engine calls that
player's callback (`priority`, `selectAttackers`, `chooseTarget`, …)
synchronously and uses the return value. Nothing is event-queued or
async for a test game.

Consequence: if playerA's `priority(game)` override writes a request file and
then sleeps in a poll loop until a response file appears, it just parks the
single game thread. When Python writes the response, the callback returns and
the game proceeds. This is the identical mechanic the scenario server already
relies on (`serve()` in the driver blocks the JVM polling the spool), only now
the block happens *inside a decision callback* instead of between scenarios.

`ThreadUtils.ensureRunInGameThread()` (`Mage/.../ThreadUtils.java:91`) accepts
the thread named `"main"` as a valid game thread (line 111) — which is the
thread Surefire runs the test on, and is why the existing adjudicator works at
all. Blocking it is fine; no other engine thread needs it.

### 2. `TestPlayer` is a thin router over a real `ComputerPlayer`

`TestPlayer` holds `private final ComputerPlayer computerPlayer` (line 114),
"the real player", and exposes it via `getComputerPlayer()` (line 4704). Its
`priority(game)` (line 607):

- if `AIPlayer` → `changeAIControl(game, true)` then `tryToPlayPriority` →
  `computerPlayer.priority(game)` (lines 609, 1214) — i.e. **full AI play**;
- otherwise it walks the scripted `actions` for the current turn/step, and if
  none match, `tryToPlayPriority` → `computerPlayer.pass(game)` (line 1217) —
  i.e. **pass** (a plain unscripted `TestPlayer` just passes every priority).

`selectAttackers`/`selectBlockers` (lines 1923, 2004) have the same shape:
process scripted `attack:`/`block:` commands, else, *if AI-controlled*, defer
to `computerPlayer.selectAttackers/selectBlockers`. The concrete engine calls
they use are the exact ones our interactive player will reuse:

- `computerPlayer.declareAttacker(attackerId, defenderId, game, false)` (1981)
- `computerPlayer.declareBlocker(defenderId, blockerId, attackerId, game)` (2029)
- enumerate plays: `computerPlayer.getPlayable(game, true, Zone.ALL, false)`
  (646) → `List<ActivatedAbility>`
- apply a chosen play: `computerPlayer.activateAbility(ability.copy(), game)`
  (653) returning `true` when it consumed priority.

So an interactive `TestPlayer` subclass never re-implements rules — it *routes*
to the same `computerPlayer` primitives the harness itself uses, choosing
*which* primitive from an externally supplied decision.

### 3. `setAIPlayer(true)` turns a `TestPlayer` into the built-in AI opponent

`setAIPlayer(boolean)` is public (line 4578). With it set, playerB needs zero
scripted actions and plays a full game via `ComputerPlayer`. We seat playerB
this way and never script it. (The default `RB Aggro.dck` loaded by
`CardTestPlayerBase` is a legal 60-card deck, adequate for plumbing; a
hardcoded mono-red list can replace it later.)

### 4. The game can be told to run to its natural end

The stop mechanism is just `gameOptions.stopOnTurn` / `stopAtStep`
(`execute()` lines 318-319), checked in `GameImpl.checkStopOnTurnOption()`
(1234). Set the stop turn arbitrarily high (e.g. 100) via `setStopAt(100,
PhaseStep.UNTAP)` and the `while (!hasEnded())` loop instead exits on a real
win/loss. `currentGame.getWinner()` then names the winner — the driver already
maps it to `"A"`/`"B"` in `addWinner()`.

## MVP scope (what the interactive driver externalizes)

Externalized to Python (one spool request + blocking wait each):

| Decision | Callback overridden | Engine primitive applied |
|---|---|---|
| Mulligan | `chooseMulligan(game)` | return the boolean |
| Priority play | `priority(game)` | `getPlayable` menu → `activateAbility`, or `pass` |
| Attackers | `selectAttackers(game, id)` | `declareAttacker` per chosen creature |
| Blockers | `selectBlockers(src, game, id)` | `declareBlocker` per chosen pair |

Delegated to the wrapped AI for the MVP (overridden to call
`getComputerPlayer().<method>`): spell/ability *target* selection
(`chooseTarget`, `choose`), mana payment (`playMana`), `announceX`,
`chooseUse`. These fire *during* an `activateAbility` the external policy
already chose, so the high-level line is still the agent's; only the
sub-resolution is the AI's.

## Biggest remaining blocker for a *full* LLM-driven match

**Externalizing the in-cast sub-choices (targets / mana / X).** They are
callbacks reached *re-entrantly* from inside `activateAbility`, so the request
protocol must support a nested "the play you picked now needs a target"
exchange rather than one flat decision per priority. It is mechanically the
same spool round-trip — the work is (a) rendering the legal target/mode set
into the request and (b) letting a single logical "line" span several
request/response hops. Until that lands, targeted spells are the AI's choice,
which is fine for a mono-red aggro plumbing deck (mostly creatures + face
burn) but not for a control agent. This is the one piece to build next, and it
does not change any of the four facts above.

## Rejected alternatives (and why the chosen path wins)

- **Drive `GameController` directly:** `GameController` is the *server*
  orchestration layer (network sessions, timeouts, chat). It expects
  `GameSession`/socket callbacks; standing one up headless is far more
  scaffolding than subclassing `TestPlayer`, for no added capability — the
  test harness already gives us a synchronous, seatable 1v1 game.
- **Write a fresh low-level `Player`:** `PlayerImpl` has ~200 abstract-ish
  callbacks; `ComputerPlayer` implements them all sanely. Subclassing
  `TestPlayer` (which wraps `ComputerPlayer`) lets us override only the handful
  we want external and inherit correct behavior for the rest.
