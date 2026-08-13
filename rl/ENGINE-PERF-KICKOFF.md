# Engine-performance kickoff — raise XMage episode throughput for RL training

You are a sibling session of the CardGuru MTG-RL project. Your job is
ONLY engine throughput: make episodes-per-hour go up without changing
game behavior. Work on branch `claude/cardguru-engine-perf` (create it
from the head of `claude/cardguru-phase-5-kickoff-2usq4s`); commit and
push there after every milestone. Do NOT push to the phase-5 branch.

Read `rl/RESEARCH-REPORT.md` for context and `rl/PHASE5-C0.md` for the
engine setup recipe.

## Environment setup

1. Clone XMage pin `7554968c` into /home/user/mage, overlay
   `rl/xmage-src/` (Mage.Tests driver+players) and
   `benchmark/xmage/src/` mirrors, `mvn -pl Mage.Tests test-compile`
   with -Dfile.encoding=UTF-8.
2. torch from PyPI (pytorch.org is proxy-blocked); `bash
   rl/restore_artifacts.sh` for checkpoints if you need policy-server
   opponents (scripted-vs-scripted needs no Python at all).
3. Baseline smoke before touching anything (see Benchmark protocol).

## Current cost structure (measured this project)

- Throughput today: ~0.12-0.7 games/sec depending on matchup; a
  64-episode training chunk takes ~6-8 min of games PLUS 1-2 min of
  fixed overhead.
- Fixed overhead per chunk: fresh Maven+surefire JVM boot, then
  `CardScanner.scan()` + `DataCollectorServices.init` in @BeforeClass
  (see rl/xmage-src/RLEpisodeDriver.java).
- In-game hotspots (known for XMage generally, confirmed here):
  `getPlayable` (the Gurmag Angler delve OOM came from its
  graveyard-subset explosion - see PHASE5-M3.md) and `Game.copy()`
  deep-copies inside `createSimulationForAI` during SearchPlayer
  consults. `rl.consultBudget` (default 20000, league uses 4000) caps
  sim nodes.
- The NDJSON-over-TCP policy consult is NOT the bottleneck (~ms per
  consult vs engine work).

## Optimization candidates, in expected-value order

1. **Persistent driver process.** Replace per-chunk mvn surefire runs
   with a long-lived JVM: a plain Java main (classpath from
   `mvn -pl Mage.Tests dependency:build-classpath`, or exec:java) that
   scans cards ONCE, then accepts episode-batch jobs over a local
   socket or stdin (deck, seeds, agent/opponent config, episode count)
   and streams back the RL| summaries. The league runners then talk to
   it instead of invoking mvn. Keep the old path working - runners
   take a flag.
2. **Concurrent games in one JVM.** The XMage server runs many games
   in parallel in production; the test harness plays one at a time.
   Run N episodes concurrently (thread-per-game, distinct Game
   instances). Verify no shared-static crosstalk in OUR classes first:
   RLPlayer/TeacherLogPlayer/HeuristicPlayer/SearchPlayer statics,
   RandomUtil seeding (per-game seeding is keyed off benchSeed - check
   it is not process-global), and the singleton policy-socket client
   (one connection per game or a mutexed channel; the policy server
   handles one connection at a time today - coordinate or multiplex).
   Determinism caveat: concurrent games may interleave RandomUtil if
   it IS global - if so, either per-game Random instances or accept
   documented non-determinism for training lanes only (eval lanes must
   stay sequential+deterministic).
3. **JVM tuning.** Measure GC time (-Xlog:gc). Try -XX:+UseParallelGC
   vs G1, larger young gen; JIT warmup means later episodes are faster
   - a persistent JVM (item 1) compounds this.
4. **Hotspot micro-fixes.** Profile first (async-profiler or JFR on a
   50-episode run; flame graph to rl/perf/). Only then consider
   caching in getPlayable/copy paths. Anything touching engine
   semantics needs the equivalence gate below - be conservative;
   upstream XMage correctness is subtle.

## Benchmark protocol (the contract)

- Metric: wall-clock for a fixed workload, reported as games/sec and
  total minutes. Two workloads:
  (a) scripted: `-Drl.agent=search -Drl.opponent=heuristic`, 100
      episodes, seed 960000, BenchDimir.dck, consultBudget 4000;
  (b) policy: agent=rl via policy server (any attn ckpt), opponent=
      heuristic, 100 episodes, seed 950000.
- Run each 2x before AND after every change on the same container;
  report both runs (cross-run variance matters).
- **Equivalence gate**: workload (a)'s summary line (wins/losses/
  draws/turns) must reproduce the baseline within cross-JVM jitter
  (identical is expected for a pure-overhead change like persistent
  JVM; small diffs are documented for anything touching execution
  order - see PHASE5-C0.md determinism notes). Any change that shifts
  win_rate by >.03 on 100g is rejected as behavior-altering.
- Sequential eval mode must remain available and bit-stable: Elo
  ratings depend on it.

## Operational rules

- mvn: `-Dtest='RLEpisodeDriver'` simple class names,
  `-DargLine="-Dfile.encoding=UTF-8 -Xmx4500m"`,
  -DfailIfNoTests=false. Foreground commands <=590s; long runs =
  harness-tracked background tasks, never detached daemons.
- pgrep/pkill patterns bracket a letter: `policy_serve[r]`.
- Do not modify HeuristicPlayer/SearchPlayer decision logic (D0/D1
  are frozen instruments); driver/harness/threading changes only.

## Deliverables

`rl/PHASE9-PERF.md`: before/after benchmark table per change,
flame-graph summary of where time goes, the persistent-driver design,
and a recommendation with measured speedup for the league runners.
Mirror any Java changes into `rl/xmage-src/` (and
`benchmark/xmage/src/` if player files are touched) exactly like the
main session does. Keep every change opt-in behind flags so the main
session's runners keep working unmodified until it adopts them.
