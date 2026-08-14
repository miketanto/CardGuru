# Phase 12 — measuring against XMage's own AI, for the first time

## Why this had never been done

Every instrument this project has used is something the project wrote.
`HeuristicPlayer` (D0) **extends XMage's `ComputerPlayer`** — the basic
shipped AI — and `SearchPlayer` (D1) extends `HeuristicPlayer`. The
whole Elo ladder is anchored at D0 = 1000, a number assigned to a
player we built on top of the weakest of the four AIs XMage ships.

The other three (`ComputerPlayer6`, `ComputerPlayer7`,
`ComputerPlayerMCTS`) have never appeared in a measurement in ten
phases, despite both plugins already being on the `Mage.Tests`
classpath and XMage's own test framework already shipping wrappers for
them.

So "ck_6144 reached D1 parity at Elo 1101" was never a statement about
whether the agent beats the AI a person actually plays against.

## What CP7 is

Not a heuristic bot. `ComputerPlayer7` extends `ComputerPlayer6`, which
is **alpha-beta minimax over simulated games**:

| component | value |
|---|---|
| search | `addActions(node, depth, alpha, beta)` — alpha-beta |
| depth | `maxDepth = skill` (run at skill 6; D1 is **1 ply**) |
| node budget | 5,000 simulated nodes per decision |
| time budget | `skill * 3` = 18s per decision |
| parallelism | its own thread pool (`AI-SIM-MAD` threads) |
| evaluation | `GameStateEvaluator2` — hand-written linear scoring |

The evaluator is a weighted sum of life differential, permanent values
and hand size (`HAND_CARD_SCORE = 5`); a live log line reads
`5367 total Score (life:1600 permanents:3757 hand:10)`.

So CP7 is the same *architecture family* as D1 — fixed evaluator plus
search — scaled from 1 ply to depth 6 with a 5,000-node budget. We have
been benchmarking against a deliberately hobbled version of the thing
XMage ships and calling it "the search instrument".

## Results (50 games each, BenchDimir mirror, seed 950000, sequential)

| agent | vs D0 | vs D1 | **vs CP7** |
|---|---|---|---|
| ck_6144 (mirror champion, Elo 1101) | .67 | .48 | **.28** |
| p10_final (deck-diverse flagship, Elo 1047) | .58 | .44 | **.22** |

The D1 column is a same-session control and it reproduces history:
ck_6144's 500-game crown match measured .48, and the flagship's own
final checkpoint measured .48 at 100g. The harness is behaving; the CP7
column is measured on a validated setup.

±95% at 50 games is about ±.13, so both CP7 rows are comfortably below
.5, and the .28 vs .22 gap between the two agents is **not** resolvable.

## Three things this settles

**1. The Elo ladder was anchored too low, and is externally
uncalibrated.** D0 = 1000 was assigned to a player we wrote. CP7 sits
above the entire published scale (D0 1000 → ck_6144 1101). Every rating
in this project is internally consistent and externally meaningless.

**2. "Saturation at 6144 episodes" was saturation against weak
opposition.** `rl/POOLED-ANALYSIS.md` found five runs plateauing at
1.5k-6k episodes, always against a fixed population, and concluded the
opponent distribution was the binding constraint. This is that
conclusion confirmed from an independent direction: there was
substantial headroom above the entire training population the whole
time. The agents stopped improving because they ran out of opposition,
not because they ran out of room.

**3. Deck diversity bought nothing against a stronger opponent.**
Phase 10's case was that opponent-deck diversity buys robustness the
mirror cannot. Against the D0-piloted archetype matrix it did (beat
ck_6144 on redrush, tied on ramp). Against CP7 on the mirror it did
not: .22 vs .28, i.e. no better, inside the noise band. Whatever the
flagship learned, it does not transfer into beating a deeper search.

## MCTS is blocked by an upstream bug

`ComputerPlayerMCTS` cannot run in the test harness on this pin:

```java
public final static String THREAD_PREFIX_AI_SIMULATION_MCTS = "AI-SIM-MCTS";  // defined...

public static boolean isRunGameThread() {
    if (name.startsWith(THREAD_PREFIX_GAME))                    return true;
    else if (name.startsWith(THREAD_PREFIX_AI_SIMULATION_MAD))  return true;   // MAD allowed
    else if (name.equals("main"))                               return true;
    // ...MCTS never checked
```

The MCTS thread prefix is declared and then never added to the
allow-list, so MCTS throws `Wrong code usage: game related code must
run in GAME thread, but it used in AI-SIM-MCTS - 4` on its own worker
threads. CP7 works because its threads are named `AI-SIM-MAD`.

The fix is one line. It is also unusually safe to argue: no thread is
ever *named* `AI-SIM-MCTS` unless an MCTS player is in the game, so
adding the prefix is a strict no-op for every existing lane and every
frozen instrument. Not applied yet — the running battery owned the
driver JVM.

## What to do with CP7

**Keep it held out. Do not train against it.** The moment CP7 enters a
training pool we lose the only external, uncontaminated answer to "is
this agent actually good?" — we would be measuring training
performance. It is worth far more as a test set than as opposition.

The improvement mechanism has to come from somewhere that does not
depend on a fixed external opponent:

- an opponent that improves as the agent does (a real self-play
  fraction — `rl/PHASE11-KICKOFF.md`), and
- a policy-improvement operator that needs no opponent at all. CP7 is
  *fixed evaluator + search*. AlphaZero is *learned evaluator +
  search*. This project has a learned evaluator and **no search**, and
  Phase 4 already recorded the symptom from the other side: terminal
  reward PPO cannot beat 1-ply search. The search machinery is sitting
  in the same JAR.

## The number to carry forward

Not Elo 1101. **~.25 against XMage's shipped AI**, and the research
question is whether anything we build moves it past .50.

## Reproduction

```
# opponent kinds cp7 / mcts are wired in EpisodeRunner (a fake Match is
# built for them - CP7/MCTS read MatchPlayer, and a game with no Match
# NPEs in SimulatedPlayer2.<init>)
bash rl/p12_xmage_ai_bench.sh 50 10
```

Artifacts: `rl/artifacts/tmp/rl_p12_aibench/`.
