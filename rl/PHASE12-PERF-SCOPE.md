# Phase 12 — scoping the next engine speedup, measured not guessed

**Update: the recommended change was BUILT and TESTED. It is safe and it
is small. See §5 — and the reason it is small is the most useful thing
this phase found.**

Prompted by the Phase 10 result: 12288 training episodes + 7500 eval
games took **~15h on 4 cores** (~0.37 games/sec overall). A 5-seed
replication of that design is 75h, which is not a research loop. More
cores are not available, so the speedup has to come from the code.

Phase 9 got 5.5x on the scripted workload and 2.7x on the policy
workload, and left one gap: **its flame graph profiled
`agent=search vs heuristic`, while the workload we actually run 12288
times is `agent=rl`.** This document closes that gap and prices the
options.

## 1. The measurement

Two 50-episode conc4 runs through the persistent JVM, JFR
`settings=profile stackdepth=512`, BenchDimir mirror, seed 950000,
p10_final.pt on the agent seat. Rendered with `rl/jfr_flame.py`,
attributed with `rl/p12_profile_analyze.py` (new — Phase 9's tooling
reports hot frames, not callers).

Artifacts: `rl/perf/policy_vs_heuristic.{collapsed,top.txt,svg}`.

### Where the time goes (`rl` vs `heuristic`, 4991 samples)

| frame | inclusive |
|---|---|
| `PlayerImpl.getPlayable` (any overload) | **77.8%** |
| ` -> GameImpl.createSimulationForPlayableCalc` | **67.2%** |
| ` -> getManaAvailable` | 38.2% |
| `SocketPolicyClient` (IPC) | 2.0% |
| `StateEncoder` (feature build) | 0.2% |
| `createSimulationForAI` (search sims) | 0.0% |

Self time is allocation churn inside that copy: `ManaCostsImpl.<init>`
8.1%, `ManaOptions.<init>` 7.6%, `HashMap.putAll` 5.5%,
`CardUtil.deepCopyObject` 5.0%, `Effects.<init>` 4.9%,
`AbilitiesImpl.<init>` 3.9%, plus ~12% `ArrayList`/`HashMap` growth.

**Phase 9's finding transfers**: `getPlayable` dominates the policy
workload too (77.8% vs 82%). **IPC, the policy server and the state
encoder are confirmed irrelevant** — 2.2% combined. No effort there.

### Who calls it

| caller | share of total | share of getPlayable |
|---|---|---|
| `RLPlayer.priority` | 39.4% | 50.6% |
| `HeuristicPlayer.priority` | 38.3% | 49.3% |

Both seats, evenly. The depth-3 nesting in 92.8% of stacks is a
**delegation chain**, not recomputation:
`getPlayable(Game,boolean)` -> `getPlayable(Game,boolean,Zone,boolean)`
-> `getPlayableUncached(...)` -> `createSimulationForPlayableCalc()`.
One logical call, three frames.

### Why the Phase 9 memo cannot help here

| workload | getPlayable calls / 50 eps | memo hits |
|---|---|---|
| `rl` vs `heuristic` | 22,370 (447/ep) | **0** |
| `rl` vs `rl` | 44,663 (893/ep) | **0** |

Every call is on a *distinct* state — one per seat per priority window
— so a memo keyed on state fingerprint can never hit. Phase 9 measured
this (0 hits in 207,830 calls) and correctly scoped the memo to search
seats. Note an RL seat costs ~2x a heuristic seat in calls, so
**self-play chunks are the expensive ones**.

## 2. The finding that decides the scope

`RLPlayer.priority` calls `getPlayable(game, true)` unconditionally at
every priority window, then passes if the result is empty
(`rl/xmage-src/RLPlayer.java:264-272`). Instrumenting the counter that
was already there but never surfaced (`autoPassK0`):

    windows = 11,249   autoPassEmpty = 6,742   ->  59.9%

**Three fifths of the agent's priority windows pay a full game-state
copy to discover the seat has nothing to do.** The copy happens
*before* the answer is known, so that cost is unconditional.

## 3. Options, priced

Amdahl ceilings for this workload: removing `getPlayable` entirely is
4.5x; removing the state copy inside it is **3.05x**; halving the copy
is 1.5x.

| # | change | expected | effort | risk |
|---|---|---|---|---|
| **A** | **Cheap "can I act at all?" pre-check in `RLPlayer.priority`**, full path only when it passes | **1.7-1.9x** on rl-vs-rl, **1.3x** vs scripted seats | **1-2 days** | **low** — our code, not the engine |
| B | Same pre-check in `HeuristicPlayer.priority` | +1.3x on rl-vs-heuristic chunks | 1-2 days | **needs sign-off**: D0 is a frozen instrument |
| C | Mana-availability memo (coarser key than the playable memo) | unknown; 38.2% is under `getManaAvailable` | 1 week + measurement | medium, engine |
| D | Pool/reuse the simulation object instead of allocating | unknown; ~30% of self time is allocation | 2+ weeks | high, engine |

**A is the recommendation.** It is the only option that is large,
cheap, and outside the engine. Arithmetic: 60% of agent calls avoided x
the 67.2% of runtime that is the unconditional copy = ~40% of runtime
saved on rl-vs-rl -> **1.67x**, and up to 1.88x if the avoided calls
cost an average amount rather than a below-average one.

### What the pre-check must be

A *conservative necessary condition* — it may only skip when the full
call provably returns empty. Sketch: empty mana pool AND no untapped
permanent that could produce mana AND no zero-cost activated ability
AND (not a sorcery window OR no land in hand). If the condition fails,
run the real `getPlayable` exactly as today.

### The gate (non-negotiable, Phase 9's protocol)

1. **`verify` mode**: run the fast path *and* the full path, throw on
   any disagreement. Phase 9 used exactly this to turn its memo's
   equivalence claim from an assertion into a test (0 mismatches in
   123k calls).
2. **Equivalence gate**: workload (a) win rate within .03 of the .65
   baseline.
3. **Behavioural gate specific to this change**: agent `windows`,
   `consults` and `autoPassEmpty` counters must be identical, since a
   skipped window must produce the same pass as the full path would.

## 4. What this does NOT fix

Even at 1.9x, a 5-seed Phase 11 replication is ~40h rather than 75h.
Options A+B+C compounding would be ~3x (25h). Reaching a true 10x on 4
cores requires option D or an engine replacement, and an engine
replacement invalidates D0/D1/D1h, the Elo scale anchored to them, and
every result from phases 4-10. **The cheapest real 10x remains running
5 seeds concurrently in 5 containers** (5x experiment throughput, zero
code) combined with A (1.7x) — which is ~8.5x on the metric that
actually matters, wall-clock to a replicated result.


## 5. The redundant-copy experiment: built, tested, measured

Prompted by the question "can the pre-check miss something?" — it can
(Kaito's loyalty ability costs no mana, so "tapped out" does not imply
"nothing playable", and 4 Kaito are in BenchDimir), so option A was
dropped for the sound alternative: remove the second copy rather than
guess at emptiness.

`rl/engine-patches/phase12-mana-recopy.patch`, flag-guarded exactly
like Phase 9's memo:

    -Dmage.manaNoRecopy=off      (default) untouched
    -Dmage.manaNoRecopy=on       skip the redundant copy
    -Dmage.manaNoRecopy=verify   compute the playable list BOTH ways,
                                 each from its own fresh simulation,
                                 compare, count, return the ORIGINAL

### Is it safe? Yes, and this is measured, not argued

    RL|manaNoRecopy|mode=verify|checked=22825|mismatches=0

22,825 `getPlayable` calls over a 50-episode policy workload; the
no-copy path produced an identical playable list every single time.
The risk was real and specific — `getPlayableUncached` reads `game`
dozens of times after the mana call, so any mutation would be visible
— and it did not materialise.

### Does it work? Yes, exactly as designed

| profile share | off | on |
|---|---|---|
| copy reached via `getManaAvailable` | 35.4% | **0.0%** |
| `createSimulationForPlayableCalc` | 67.2% | 50.9% |
| `getManaAvailable` | 38.2% | 4.8% |
| `getPlayable` | 77.8% | 67.9% |

The renormalisation checks out: removing 35.4 units of 100 leaves
(67.2-35.4)/64.6 = 49.2% predicted vs 50.9% observed for the copy, and
2.8/64.6 = 4.3% vs 4.8% for mana. **~35% of game-thread work is gone.**

### So why is the wall-clock win small?

| configuration | off | on | speedup |
|---|---|---|---|
| sequential | 0.516 g/s (n=2) | 0.662 g/s (n=2) | **1.28x** |
| conc4 | 1.431 g/s (n=3) | 1.496 g/s (n=4) | **1.05x** |
| Amdahl ceiling from the profile | | | 1.55x |

**Game-thread work is no longer the wall-clock bottleneck at conc4.**
Sequential recovers most of the predicted win; conc4 recovers almost
none. Cutting engine work by a third barely moves a 4-worker run, which
means something else is now the constraint — the obvious suspect is
`policy_server.py`, where a SINGLE lock guards inference and the PPO
buffers for all four workers. Phase 9 dismissed that lock explicitly
("fine, because engine work dwarfs it"). Engine work no longer dwarfs
it.

### What this changes about the 10x plan

The profile's 82%/77.8% `getPlayable` share is real but **misleading as
a speedup budget**: at conc4 it is partly hidden behind contention.
Before spending 1-2 weeks on options C or D (mana memo, simulation
pooling), measure the policy server. If the lock is the conc4
bottleneck, batching inference across workers or sharding the lock is
likely cheaper AND larger than any further engine work — and it is
Python, not a 15-year-old rules engine.

Revised order:
1. **Measure the policy server's serialization** at conc4 (cheap).
2. Adopt `manaNoRecopy=on` regardless — it is verified safe, it is
   1.28x sequential (which is what every Elo probe, matrix cell and
   gate runs at), and eval was 27% of Phase 10's wall clock.
3. Only then decide between engine work (C/D) and server work.
