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

---

## RL seat smoke — two harness findings, no capability number

Seat A swapped from `LinePlayer` to `RLPlayer` (v7 seat, joint attack
and block candidates via `JointCands`), driven by the in-process
`RandomPolicyClient`. No network: torch is not installed in this
container, so the policy server cannot run here yet.

### Finding 1 — who goes first was not pinned, and the POLICY was deciding it

The first RL run's action log showed seat A being **attacked on turn 1**
in a subgame whose whole premise is "A to act". Cause:
`GameImpl.init` resolves the starting player by asking the choosing
player's `choose()` callback (GameImpl.java:1318-1340). `LinePlayer`
inherits `ComputerPlayer.choose` and answers deterministically;
`RLPlayer` overrides `choose` and **delegates to the policy** — so a
random policy was silently picking which side was on the play. Twenty
"episodes of T1.HOLD" were a mixture of two different subgames.

Fixed by pinning `game.setStartingPlayerId(first.getId())` before
`start`. The two scripted lines re-verify unchanged afterwards (A wins
turn 5 / B wins turn 2), so the fix did not move the instance.

This is a general hazard for the whole design: **any engine question
routed through the policy's generic callbacks is a decision the subgame
did not intend to ask.** Later rungs with modes, X values and targets
will have more of them.

### Finding 2 — a fixed line cannot be an opponent

With the starting player pinned, the random policy went **100/100**
against seat B. That is not a capability result, it is the opponent
being inert: B's line is a list of indices consumed in decision order,
and *which decision comes first depends on what A does*. A attacked on
turn 1, so B's single scripted index was eaten by the resulting BLOCK
decision, leaving B's attack decision past the end of its line and
defaulted to "no attack" — forever. B then sat still and lost to its own
deck-out clock.

So a line is a replay artefact, not a strategy. **The opponent seat has
to be a function of state** — the solver's best defence, or at minimum a
rule-based defender. Recorded here because it was the argued-about
question ("why a solver?") and it is now a measured answer rather than a
prediction.

### Throughput, measured

**38.5 episodes/sec** for T1.HOLD with the random policy (100 episodes,
one JVM, warm). Full BenchBurn games on this box smoke at 1.465
games/sec, so a subgame is roughly 26x cheaper. That makes replay-based
exact solving clearly affordable: a few hundred replays per instance is
seconds, not minutes.

### What these runs do NOT support

No statement about the network (none ran), and none about T1.HOLD's
difficulty: the 1.000 is against an inert opponent and must never be
quoted as a win rate. The only real numbers here are the throughput and
the two bugs.

---

## The solver runs, and `T1.HOLD` is exactly solved

`rl/xmage-src/SubgameSolver.java`. Replay-based minimax over the real
game: run from the start with a prefix of choices, and when a decision
arrives past the end of it, branch on its options with a fresh replay
each. Values are binary ("does A win"), so alpha-beta degenerates into a
short-circuit — an A node stops at the first winning child, a B node at
the first losing one — which is what keeps an exhaustive solve cheap.
Both seats now consume ONE shared script in global decision order, the
fix demanded by finding 2: whose decision comes next depends on what was
chosen before, so per-seat lines cannot express a strategy.

### Result

```
SOLVE|T1.HOLD|value=1|rootSeat=A|rootKind=atk|rootOptions=4
      |optimalRoot=[0]|unique=true|replays=611|noWinner=0|capHit=false
      |solveSecs=2.8
```

- **value = 1**: with best play on both sides, A wins.
- **optimalRoot = [0], unique = true**: option 0 is "attack with
  nobody". **Holding is the only first action that wins**, against a
  defence that is now optimal rather than scripted. The hand-derivation
  in `SUBGAME-DESIGN.md` is confirmed by exact solve, and the uniqueness
  gate passes.
- **noWinner = 0**: every replay terminated on its own. The
  small-library clock does what the design claims.
- **611 replays, 2.8 s.** Exact ground truth for a combat position costs
  seconds on this box.

### Gate 1 (horizon insensitivity) — PASSES

Same instance with more filler in both libraries:

| filler delta | value | optimal root | replays | solve |
|---|---|---|---|---|
| +0 | 1 | [0] | 611 | 2.5 s |
| +2 | 1 | [0] | 1,802 | 6.9 s |
| +4 | 1 | [0] | 4,049 | 17.1 s |

The answer does not move, so `T1.HOLD` is measuring combat and not the
deck-out clock. The cost of the gate is worth noting for later rungs:
**replays roughly triple per two extra cards**, because filler extends
the game and every extra turn adds decisions. Libraries should be as
short as the concept allows.

### Discrimination, at the root only

One of four root options wins, so a policy choosing its first action
uniformly scores 0.25 there. That is a root-level statistic, not the
family's discrimination — the full gate needs the solver seated as the
opponent, which is the next build.

### What this still does not support

Nothing about the network. And the solver's own two limits stand as
written in its header: the seats choose only attacks and blocks
(priority always passes, so no rung with castable cards can use it
unchanged — that is T3 onward), and the block option space is a superset
in which distinct indices can denote the same legal assignment.

---

## The probe: a policy at a solved position

`rl/xmage-src/SubgameProbe.java`. Rather than seating the solver as an
opponent and playing games, the probe asks the cheaper and more
diagnostic question: **at a position whose optimal action is known, what
does the policy choose, and could it have chosen right?**

Everything is compared in SOLVER space — an attack is the set of
attacking creature ids, mapped to a bitmask over canonically ordered
available attackers. Mapping by id, not by list position, is required:
`RLPlayer` sorts its candidates by name only and `LinePlayer` by name
then id, so comparing positions would silently compare different
creatures.

### Result on `T1.HOLD`

| policy | expressible | optimal | choices seen |
|---|---|---|---|
| uniform random, 200 samples | 200/200 | **89/200 = 0.445** (Wilson 95% 0.373-0.510) | {0, 3} |
| v7 network, untrained, argmax | 1/1 | **0/1** | {3} |

- **Gate 3 (expressibility) PASSES here.** The optimal action, mask 0
  ("attack with nobody"), is in the candidate list every time. On this
  position the §15/C coverage hole does not bite, and that is now
  verified per position rather than estimated from teacher counters.
- **The candidate list is {0, 3}, not all four subsets.** The Pareto
  filter and outcome dedup remove both single-attacker sets. So the
  action space the policy chooses from has 2 options where the solver
  has 4 — which means **the random baseline on this position is ~0.5,
  not 0.25**. The filter blamed for the coverage hole is also what makes
  a coin-flip score 0.445 here, and any "beats random" bar has to be set
  against the filtered space.
- **The untrained network picked mask 3** — attack with both, the line
  the solver proves loses. One deterministic argmax decision from a
  fresh random initialisation: it demonstrates the socket path works end
  to end and **nothing whatsoever about capability**. A trained
  checkpoint is what makes this row mean anything.

### A methodology bug caught by disagreement, not by review

The first probe run reported the uniform random policy playing
**optimally 200/200**, which is impossible for a coin flip. Cause: the
probe built a fresh `RandomPolicyClient(7000 + i)` per sample, and at
encoder v5+ there is exactly ONE consult per combat, so only the FIRST
`nextInt` of each seed was ever used — and `java.util.Random` returns
the same first value for long runs of consecutive seeds. At v2 the
per-creature attack path made two consults per combat, which hid the
correlation behind a second draw.

Fixed by sharing one client across the battery; the rate fell to the
0.445 above. Recorded because the wrong version was a *clean-looking*
number that would have made every later "the agent beats random" claim
meaningless.

### Wiring notes for the next session

- The v7 arch needs `-Drl.cardFeatures=rl/e2_features.tsv` or the
  handshake fails with `cdim 41 != 94`; `CAND_DIM` is a class-init
  constant derived from that file.
- A failed handshake **kills the policy server**, so it must be
  restarted between attempts.
- Start the server with output redirected to a file, not through a pipe:
  it binds within ~4 s, but piping its stdout made it look hung.
