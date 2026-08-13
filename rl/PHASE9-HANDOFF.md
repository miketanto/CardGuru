# Phase 9 handoff — engine throughput, what exists and how to run it

For the next session picking up engine performance. The results and the
reasoning are in `rl/PHASE9-PERF.md`; this file is the operational part:
what to rebuild, what the flags mean, and what is still open.

## State

Branch `claude/cardguru-engine-perf-sl17fn`, commit `d24e8c0`, branched
from `claude/cardguru-phase-5-kickoff-2usq4s` (where
`rl/ENGINE-PERF-KICKOFF.md`, the original mandate, lives). Nothing was
pushed to any other branch. No pull request was opened.

Measured on a 4-core container, 100-episode workloads, both benchmark
workloads run twice per configuration:

| workload | before | after | speedup |
|---|---|---|---|
| (a) scripted, `agent=search` vs heuristic | 0.49 games/sec | 2.72 (range 2.17-2.97) | **5.5x** |
| (b) policy, `agent=rl` vs heuristic | 0.48 games/sec | 1.28 at conc4, 1.44 at conc6 | **2.7-3.0x** |

Equivalence gate (workload (a) win_rate within .03 of a .6500 baseline)
passed on every configuration: all rows landed .65-.67.

## Rebuilding the environment from scratch

The container is ephemeral; `/home/user/mage` will not exist. In order:

1. **Clone XMage.** Full clone — a shallow fetch by SHA is refused by
   the remote for this repo.
   ```bash
   git clone https://github.com/magefree/mage.git /home/user/mage
   cd /home/user/mage && git checkout 7554968c
   ```
2. **Apply the engine patches** (bounded `getAttackablePlayers`, opt-in
   per-thread `RandomUtil`, opt-in `getPlayable` memo):
   ```bash
   cd /home/user/mage && git apply /home/user/CardGuru/rl/engine-patches/phase9-engine.patch
   ```
3. **Overlay the mirrored sources and decks:**
   ```bash
   mkdir -p Mage.Tests/src/test/java/org/mage/test/benchmark/rl
   cp /home/user/CardGuru/benchmark/xmage/src/*.java Mage.Tests/src/test/java/org/mage/test/benchmark/
   cp /home/user/CardGuru/rl/xmage-src/*.java       Mage.Tests/src/test/java/org/mage/test/benchmark/rl/
   cp /home/user/CardGuru/rl/*.dck /home/user/CardGuru/benchmark/xmage/*.dck \
      /home/user/CardGuru/rl/m3_decks/*.dck Mage.Tests/
   ```
4. **Build with `install`, not `test-compile`.** `surefire:test` resolves
   the sibling modules from the local repo, and the jboss mirror answers
   403 through the proxy, so a reactor-only build fails at run time:
   ```bash
   mvn -q -pl Mage.Tests -am install -DskipTests -Dfile.encoding=UTF-8   # ~10 min
   ```
   After editing only `rl/xmage-src/`, `mvn -q -pl Mage.Tests test-compile`
   is enough. After editing an engine file under `Mage/`, you must
   `mvn -q -pl Mage install -DskipTests` first.
5. **Python:** `pip install torch` (PyPI works; pytorch.org is blocked).
   `bash rl/restore_artifacts.sh` restores the checkpoints — workload (b)
   uses `/tmp/rl_c6_attn_s0/net.pt` with `--arch attn --cdim 91` and
   `-Drl.cardFeatures=/home/user/CardGuru/rl/e2_features.tsv`.

Gotcha: `Mage.Tests` targets **Java release 8**. `PrintStream(…, Charset)`,
`ByteArrayOutputStream.toString(Charset)` and friends will not compile.

## Running

```bash
# one server per session; drop playableCache for lanes with no search seat
bash rl/driver_server.sh start 7910 \
    "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on"

# a job == the -D list mvn took
python3 rl/driver_client.py --port 7910 -Drl.episodes=100 -Drl.agent=search ... \
    -Drl.concurrency=4

# benchmarks (appends a BENCH| row to /tmp/rl_p9/bench_log.txt)
bash rl/perf_bench.sh a mytag persist -Drl.concurrency=4
bash rl/perf_bench.sh b mytag persist -Drl.concurrency=4   # RL_BENCH_SRV_THREADS=4

bash rl/driver_server.sh stop 7910
```

In a league runner, replace the whole `mvn -q -pl Mage.Tests
surefire:test -Dtest='RLEpisodeDriver' … ` invocation with
`RL_PERSIST=1 RL_CONC=4 bash rl/run_driver.sh …` keeping the same `-D`
flags. With `RL_PERSIST` unset that script execs the original mvn
command, so converting a runner does not change its default behavior.
**No runner has been converted** — that was deliberate, so the main
session's lanes keep working untouched.

## The flags, and when each is wrong

| flag | default | notes |
|---|---|---|
| `-Drl.concurrency=N` | 1 | N = core count. Regresses above it (4 cores: 4.1x at N=4, 3.4x at N=6). **Training lanes only** — eval/Elo must stay sequential. Rejected at runtime with `rl.opponent=rl`. |
| `-Dmage.randomPerThread=true` | false | Required for `rl.concurrency>1` (the runner fails fast without it). Off = the original single shared `Random`, bit-for-bit. |
| `-Dmage.playableCache=on\|verify\|off` | off | Only pays where a seat calls `getPlayable` twice per window, i.e. search/teacher seats. **0 hits in 207k calls on a pure rl-vs-heuristic lane.** `verify` recomputes and throws on disagreement. |
| `-XX:+UseParallelGC` | G1 | Pause time 5.5s -> 3.5s per 2x100 episodes. Weakest of the wins; run-to-run variance is the same order. |
| `-Drl.deckCache=true` | false | Implemented, never benchmarked — deck loading is <1% of the profile. |
| `--threads N` (policy_server) | 1 | Needed for a concurrent lane with `agent=rl`. Per-connection trajectory buffers; episodes still enter the PPO batch whole and in order, but **which episode lands first is scheduler-dependent, so training runs stop being bit-reproducible from seed**. |

The persistent server **pins** `rl.cardFeatures`, `rl.phi`,
`rl.noYields` and `rl.debug` on its first job and refuses later jobs that
change them (they land in `static final`s downstream). One server per
encoder configuration — a workload-(a) server cannot run a workload-(b)
job.

## What the profile says (so you don't re-derive it)

JFR, 50-episode conc4 scripted run, `rl/perf/scripted.{svg,top.txt,collapsed.gz}`,
regenerate with `python3 rl/jfr_flame.py <recording.jfr> rl/perf/<name>`.
Note `jfr print` needs `--stack-depth 512`; its default truncates every
stack to 5 frames and silently ruins any inclusive-time analysis.

- `PlayerImpl.getPlayable` **82%** of game-thread time; the full state
  copy *inside* it (`createSimulationForPlayableCalc`) is 72%;
  `getManaAvailable`/`ManaOptions` 42%.
- `createSimulationForAI` — the D1 search sims — **2.8%**. The kickoff's
  expectation that `Game.copy()` in the sim tree was a main cost is
  wrong at D1 breadth 8.
- 27.7% was the D1 seat recomputing `getPlayable` on an unchanged state
  (searchBest, then the delegated `HeuristicPlayer.priority`). That is
  what the memo recovers.
- Policy IPC, deck loading and the state encoder are each <1%.

## Open items, roughly in value order

1. **Concurrency for `rl.opponent=rl`** — currently rejected, because
   both policy seats share one `oppPolicy` connection. Per-thread
   opponent connections would let the self-play league lanes (C5/C6/P7,
   the ones that actually consume the training budget) use conc4. This
   is the single biggest remaining win.
2. **The `getPlayable` state copy itself** (72% of engine time). The memo
   only removes duplicate calls; making the copy cheaper, or avoiding it
   when the caller already holds a simulation, is untouched territory.
   Anything here needs `mage.playableCache=verify`-grade evidence.
3. **Re-verify the memo on new card pools.** The fingerprint is
   conservative but hand-written, and everything here was the BenchDimir
   mirror. Run a lane with `-Dmage.playableCache=verify` once on any new
   pool; it throws on the first disagreement.
4. `rl.deckCache` has never been measured.

## Rules inherited from the kickoff, still in force

- **Do not modify `HeuristicPlayer`/`SearchPlayer`/`SearchPlayerIP`
  decision logic.** D0/D1/D1ip are frozen instruments; Phase 4/5
  calibration depends on them. Phase 9 touched no player file.
- Any change that can affect execution order runs the equivalence gate:
  workload (a), 100 episodes, seed 960000, win_rate within .03 of .6500.
  Note the summary is not bit-identical across JVMs even at fixed seed
  (turns_per_ep and node counts drift), so identical wins/losses plus
  win_rate within jitter is the strongest available form.
- Sequential eval mode stays available and reproducible — Elo depends
  on it.
- Mirror any Java change back into `rl/xmage-src/` (and
  `benchmark/xmage/src/` if a player file is ever touched), and
  re-export engine diffs with
  `cd /home/user/mage && git diff <files> > rl/engine-patches/phase9-engine.patch`.

## One bug worth knowing about

`TokenRepository.init()` in the engine is an unsynchronized lazy
initializer: it publishes `allTokens` before building its indexes, so a
second game thread entering that window streams a half-built index and
throws `ConcurrentModificationException` out of
`GameImpl.initGameDefaultHelperEmblems`. It hit ~1 concurrent job in 15.
`RLDriverServer` and `EpisodeRunner.runConcurrent` now force the init to
completion before any worker starts. If you add another concurrent entry
point, do the same. Expect more of these: the engine's repositories are
full of lazy initializers written for a single-threaded test harness.
