# XMage throughput benchmark harness

Measures whether XMage is fast enough to serve as an RL environment.
Results: [RESULTS.md](RESULTS.md). Recommendation: [VERDICT.md](VERDICT.md).

## Layout

- `src/` — benchmark sources; copy into an XMage checkout at
  `Mage.Tests/src/test/java/org/mage/test/benchmark/`
- `BenchBurn.dck` — 60-card mono-red deck of implemented, choice-light
  cards; copy into `Mage.Tests/`. (The stock test deck `RB Aggro.dck`
  is 71 Mountains — scripted tests never cast from library, so random
  policies play nothing but lands with it. This cost us a debugging
  round; do not benchmark with the stock decks.)
- `b4_scaling.sh` — process-level parallel scaling driver

## Setup from a clean checkout

```bash
git clone https://github.com/magefree/mage.git ~/mage
cd ~/mage && git checkout <PIN>          # see RESULTS.md for the pin
mvn -q -DskipTests install               # full build; see RESULTS.md for cost
cp <this dir>/src/*.java ~/mage/Mage.Tests/src/test/java/org/mage/test/benchmark/
cp <this dir>/BenchBurn.dck ~/mage/Mage.Tests/
cd ~/mage && mvn -q -pl Mage.Tests test-compile
```

## Running

All commands run from the XMage checkout root. Surefire captures test
stdout into `Mage.Tests/target/surefire-reports/TEST-*.xml`; every
benchmark emits grep-able `BENCH|...` lines.

```bash
# B1 scenario setup cost (sweep 2/8/20/50 permanents)
mvn -q -pl Mage.Tests surefire:test -Dtest=B1SetupBenchmark -DfailIfNoTests=false

# B2 GameState.copy()/restore() (sweep 5/20/50/100 permanents, +graveyard)
mvn -q -pl Mage.Tests surefire:test -Dtest=B2StateCopyBenchmark -DfailIfNoTests=false

# B3 random-policy full games (tunables: bench.games/warmup/stopTurn/seed/out/debug)
mvn -q -pl Mage.Tests surefire:test -Dtest=B3RandomPolicyBenchmark \
    -DfailIfNoTests=false -Dbench.games=30 -Dbench.warmup=5

# B4 process scaling (P = 1,2,4,8; writes B4|... summary lines)
GAMES=15 bash b4_scaling.sh

# Phase 2 complexity sweep (board size / anthems / trigger fan-out / stack churn)
mvn -q -pl Mage.Tests surefire:test -Dtest=B5ComplexityBenchmark -DfailIfNoTests=false

# Phase 3 determinism (100x same-seed scripted scenario)
mvn -q -pl Mage.Tests surefire:test -Dtest=B6DeterminismTest -DfailIfNoTests=false

# Phase 3 coverage (reads /tmp/bench_samples/sample_{modern,all}.txt,
# one card name per line; see RESULTS.md for how samples were drawn)
mvn -q -pl Mage.Tests surefire:test -Dtest=B7CoverageTest -DfailIfNoTests=false
```

Collect results:

```bash
grep -h "BENCH|" Mage.Tests/target/surefire-reports/TEST-org.mage.test.benchmark.*.xml
```

## Design notes and honest caveats

- **Warmup**: every benchmark discards >=5 iterations before measuring;
  distributions are median/p95/stddev over >=30 (>=20 for B5), never a
  single run.
- **RandomPlayer** extends `ComputerPlayer` (NOT ComputerPlayer7): action
  selection at priority is uniform over {playables, pass}; combat is
  p=0.5 random attack/block declarations; targets/modes inside a chosen
  action resolve via ComputerPlayer's cheap heuristics (loops, no
  simulation). So B3 measures engine stepping cost, not policy cost —
  but "uniform random" is approximate below the action-selection level.
- **Thread gate**: `ThreadUtils.ensureRunInGameThread()` whitelists the
  `main` thread, so surefire runs pass without renaming. Any custom
  executor threads must be named `GAME...`.
- **Static state**: `MageTestPlayerBase` holds static players/config; the
  AI holds static caches. Parallelism is process-level only (B4), one
  game at a time per JVM.
- **Stack depth** (Phase 2) is approximated by sequential bolt churn —
  building a deep stack needs response scripting the harness only
  supports awkwardly; a true depth sweep would need a custom
  split-second-style scenario or a fork.
- **JUnit coupling**: `execute()` uses `Assert` for control flow; the
  benchmarks catch nothing — a failed scenario fails the test loudly,
  which is what we want.
