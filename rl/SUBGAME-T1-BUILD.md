# T1 subgame harness — build log and first result

Rung 1 (`T1.HOLD`), this container, engine pin `7554968c`. Design is
`rl/SUBGAME-DESIGN.md`; this file records what was built and what it
returned.

## What exists now

- `rl/xmage-src/LinePlayer.java` — a seat whose combat choices come from
  a fixed LINE of integer indices, canonical (name-sorted) option order,
  priority always passes. Records the option count at the first decision
  past the end of its line (the "frontier"), which is the hook the
  solver will enumerate from.
- `rl/xmage-src/SubgameRunner.java` — builds a constructed board through
  the engine's own `GameImpl.cheat()` and plays it to a real terminal
  state. `describe` mode prints engine-verified P/T and abilities.

**Board construction needs no test framework.** `GameImpl.cheat()` is
Mage core, not `Mage.Tests`, so a subgame is built the same way
`EpisodeRunner` builds a game: `new TwoPlayerDuel(...)`, `addPlayer`,
then `cheat` for zones and `cheat(playerId, {OUTSIDE: "life:N"})` for
life. Two details that are load-bearing:

1. `addPlayer` fills the library from the deck, and `cheat` puts its
   cards **on top** of that. So the stub deck's library is cleared
   before the cheat — otherwise the "small library is the clock"
   property silently does not hold.
2. `GameOptions.testMode = true` means no opening hand is drawn, so the
   hand is exactly what the spec says. (`EpisodeRunner` sets it `false`
   on purpose, to get real opening hands — the opposite need.)

## Enumeration is by REPLAY, not by state copy

The solver will run the game from the start with a line prefix; when a
decision arrives past the end of the prefix, the seat records how many
options it had and plays the canonical do-nothing. Each extension is a
fresh replay. Subgames are a few turns long, so this needs no
`game.copy()`, no transposition table, and no assumptions about what
XMage's copy constructor preserves. It also makes the solve cost a
number we already measure in games/sec.

## Cards, engine-verified (no stat guessed)

| card | engine says |
|---|---|
| Silvercoat Lion | 2/2, mv 2, abilities NONE |
| Trokin High Guard | 3/3, mv 4, abilities NONE |
| Hillcomber Giant | 3/3, **mountainwalk** |

**Gotcha worth keeping:** filtering `rl/artifacts/cards_v1` for an
empty graph vector is *not* a vanilla test — Hillcomber Giant passes it
and has mountainwalk. Every card in a family gets `describe`d before it
is used.

## First result — `T1.HOLD` behaves as designed

Board: A 3 life, two Silvercoat Lions, library 7 · B 4 life, one Trokin
High Guard, library 4 · A on the play.

| line | result |
|---|---|
| A holds, double-blocks, then attacks | **A wins** on turn 5, A at 3, B at 0 |
| A attacks with both | **A loses** on turn 2, A at 0, B at 2 |

Both match the hand-derivation in `SUBGAME-DESIGN.md` exactly, including
B's life at 2 in the losing line. The sample instance is real: holding
back wins, attacking with everything dies to the crack-back, and the
win comes through a double block.

**What this does NOT show.** It verifies two lines, not that holding is
*optimal* — that is the solver's job, and until it runs, `T1.HOLD` is a
position whose two interesting lines behave as predicted, nothing more.
It also says nothing about any policy: no network was involved.

Also confirmed incidentally: cheated creatures are not summoning-sick,
so turn-1 attacks are available (the losing line attacked on turn 1).

## Next

The exact solver: enumerate both seats' lines by replay, back up
win/loss, and report the optimal action set per instance plus the solve
cost in replays. That is what turns this from a scripted check into
ground truth.
