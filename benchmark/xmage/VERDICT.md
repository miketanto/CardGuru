# Verdict: is XMage viable as an RL environment?

**Yes — with a snapshot-pool architecture and heavy pass-pruning, both of
which the numbers directly justify. No kill criterion fired.** The spec's
10²–10³ steps/sec/core guess was correct: measured 647 decisions/sec/core.

## The four numbers

| Question | Answer |
|---|---|
| Decisions/sec/core | **647** (random policy, real 25-turn burn games, in-JVM, 4-core Xeon 2.8GHz) — 13× above the ~50 floor that would have killed tier-2 self-play |
| Snapshot vs setup | **copy 0.5 ms vs setup 10 ms (~20×); restore from a pooled snapshot 0.02 ms (~500×)** — snapshot pooling wins decisively |
| Pruning headroom | **78.5% of priority windows are forced passes; 94% have ≤1 playable.** Only ~6% of windows are genuine ≥2-way choices — ~30 real decisions per game |
| Coverage | **97.6% of a modern pool** implemented, 0 instantiation errors, loud failure on unknowns — above the 85% kill line with room |

## Projections at measured throughput

At this 4-core container's measured aggregate (2.36 games/sec, P=4,
Maven-wrapped workers — a lower bound):

| Workload | Wall clock |
|---|---|
| 10⁴ full games | **~1.2 hours** |
| 10⁵ full games | **~11.8 hours** |

Per-core planning number: ~0.6–1.0 games/sec/core (game length ~25
turns, ~500 decisions). A single 32-core box at the same per-core rate
runs 10⁵ games in **1.5–4 hours**; bare-JVM workers (no Maven parent)
should push toward the linear end. Memory budgets ~1 GB/worker —
RAM will not be the ceiling before cores are.

## What the policy actually pays for

The 647 decisions/sec are engine-priced, not policy-priced. Since 94% of
windows have ≤1 legal action, an RL agent that auto-passes forced
windows consults its network on only ~139 windows/sec/core of engine
time — i.e., **the environment can feed a policy ~10⁷ meaningful
decision points per day per 16-core machine.** Sample efficiency still
matters (this is no chess-engine 10⁶/sec), but it is not the
load-bearing crisis the low estimate implied.

## Architecture implications (from the measurements, not taste)

1. **Reset from snapshot pools, not scenario reconstruction** (B2):
   build each distinct scenario once (~10 ms), then copy/restore at
   0.02–0.5 ms. Curriculum resets become effectively free relative to
   stepping.
2. **Parallelize with one bare JVM per core, one game per JVM** (B4 +
   static-state audit): `MageTestPlayerBase` statics and AI caches make
   in-process parallelism unsafe; process isolation costs ~1 GB each and
   scales near-linearly when workers are bare JVMs.
3. **Auto-pass forced windows in the environment wrapper, not the
   policy** (B3 histogram): a 16× reduction in policy invocations for
   free, before any learned pruning.
4. **Watch trigger fan-out in scenario design** (B5): cost is ~flat in
   board size and linear in continuous effects, but ~1.7 ms per trigger
   *firing* and trending superlinear — trigger-storm boards (Soul
   Warden × token swarms) are the pathological case, not big boards or
   anthem stacks.

## Binding constraint

**Choice-resolution plumbing, not throughput.** The benchmark's random
policy delegates targets/modes/blocker choices to ComputerPlayer's cheap
heuristics; a real RL environment must surface those as policy decisions,
which multiplies the action-space engineering (every `choose*` callback
becomes an action head) — that work is the actual gate to tier-2
training, and it costs engineering time, not steps/sec. Second-order
constraints: per-worker RAM (~1 GB) sizes the fleet, and object UUIDs
are not seed-controlled, so reproducibility hashing must canonicalize
state (names/zones/life), never raw identity — determinism itself passed
100/100.

## Kill-criteria checklist (§8 of the spec)

- Decisions/sec/core below ~50 → **NOT fired** (647)
- State copy not meaningfully cheaper than setup → **NOT fired** (20×)
- Parallel scaling sublinear past 4 processes → **ambiguous on a 4-core
  box with Maven-wrapped workers; linear to 2, saturated at 4.** Re-run
  bare-JVM on ≥16 cores before hardware planning; nothing here suggests
  a memory wall (RSS flat, no paging).
- Uncontrollable nondeterminism → **NOT fired** (100/100 with seeded
  RandomUtil; UUID caveat is a hashing constraint, not gameplay
  nondeterminism)
- Coverage below ~85% modern → **NOT fired** (97.6%)
