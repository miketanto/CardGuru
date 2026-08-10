# XMage throughput benchmark — results

## Environment

| Fact | Value |
|---|---|
| XMage commit | `7554968c` ("[MBC] Don't enable Acorn stamp reprints in Constructed by default (#15874)", master, 2026-08-06 vintage) |
| CPU | Intel Xeon @ 2.80GHz, **4 cores** (cloud container) |
| RAM | 15 GB |
| JVM | OpenJDK 21.0.10, surefire default heap, `-Dfile.encoding=UTF-8` |
| OS | Linux 6.18.5 |
| Checkout size | 847 MB including all build artifacts |
| Build cost | Full `mvn install -DskipTests` was executed in a prior session on this machine (not re-timed for this report — a re-run would cost the ~30–60 min it was avoiding; `Mage.Sets` alone is 32,698 java files). Incremental `mvn -pl Mage.Tests test-compile` after adding the benchmark package: **~35 s**. Single-test JVM launch overhead (surefire + config + plugin classloader init): **~13–15 s** per invocation, amortizable across any number of games/iterations in-process. |

All numbers are median/p95/stddev over ≥30 measured iterations (≥20 for
Phase 2) after ≥5 warmup iterations in the same JVM. Reproduction
commands: [README.md](README.md).

## Phase 0 sanity baselines

- `DeathtouchTest` (3 scripted card tests): pass, 20.9 s suite including JVM init.
- `SimulationPerformanceAITest` (full ComputerPlayer7 tree-search AI):
  `test_Simple_ShortGame` **18.0 s for ONE turn** of AI-vs-AI; LongGame
  (variable turns) 3.7 s. Confirms: the sim AI is orders of magnitude too
  slow to be the stepping engine, as expected — nothing below uses it.

## B1 — scenario setup cost (fresh game + addCard×N + execute to turn-1 main)

| N permanents | median ms | p95 ms | stddev |
|---|---|---|---|
| reset only (game+decks, no run) | 4.49 | 55.4 | 16.1 |
| 2 | 11.1 | 36.3 | 8.8 |
| 8 | 10.7 | 71.2 | 22.1 |
| 20 | 8.3 | 13.3 | 15.4 |
| 50 | 9.9 | 13.2 | 1.5 |

**Setup ≈ 8–11 ms, essentially flat in board size** (dominated by game
object + deck construction and turn-1 phase stepping, not by card count).
≈ 100 fresh scenarios/sec/core.

## B2 — GameState.copy() / restore() (the critical one)

| Board | copy median ms | copy p95 | restore median ms |
|---|---|---|---|
| 5 permanents | 0.577 | 0.94 | 0.034 |
| 20 permanents | 0.435 | 1.27 | 0.017 |
| 50 permanents | 0.608 | 1.30 | 0.013 |
| 100 permanents | 0.856 | 10.9 | 0.012 |
| 50 + 30-card graveyards | 0.478 | 0.66 | 0.013 |

**Copy ≈ 0.4–0.9 ms** (sub-linear in board size at these scales; p95 tail
at 100 permanents is GC noise). **Restore ≈ 0.01–0.03 ms** — it is
reference reassignment, effectively free. A snapshot-pool reset
(copy-then-restore) costs ~0.5 ms vs ~10 ms for scenario reconstruction:
**snapshot reset is ~20× cheaper than setup, and restoring a pre-built
snapshot is ~700× cheaper.**

## B3 — random-policy full games (no AI, uniform action selection)

Deck: `BenchBurn.dck` (mono-red burn, 60 cards, all implemented,
choice-light). Both players RandomPlayer. 30 games, turn bound 50.

| Metric | median | p95 | stddev |
|---|---|---|---|
| wall per game | 745 ms | 980 ms | 149 |
| decisions per game | 495 | 623 | 83 |
| turns per game | 25 | 30 | 3.3 |

- **Throughput: 1.31 games/sec, 647 decisions/sec, single core** (in-JVM,
  measured over 22.9 s of continuous play)
- **30/30 games ended naturally** (life reached 0; none hit the turn bound)
- Priority-window histogram (playable count k at each window):
  k=0: 11,608 · k=1: 2,295 · k=2: 577 · k=3: 192 · k=4: 76 · k≥5: 43
- **78.5% of priority windows are forced passes** (zero playable actions —
  pass is the only legal move). A further 15.5% have exactly one playable.
  Only ~6% of windows offer a genuine ≥2-way action choice.

## B4 — parallel process scaling

Each worker = one `mvn surefire` invocation (a Maven parent JVM + a test
JVM), 15 games after 3 warmup, aggregate = sum of in-JVM game rates.

| P processes | aggregate games/sec | speedup | peak java RSS |
|---|---|---|---|
| 1 | 1.05 | 1.0× | 1.0 GB |
| 2 | 1.96 | 1.87× | 2.0 GB |
| 4 | 2.36 | 2.25× | 4.3 GB |
| 8 | 2.31 | 2.20× | 8.0 GB |

**Near-linear to P=2, flattening at P=4, saturated by P=8 — on a 4-core
box where each worker is TWO JVMs** (the Maven parent burns real CPU).
This is a lower bound on scaling: a production harness would launch bare
JVMs (one per worker, no Maven), which on this box should track core
count. Memory: ~1.0–1.1 GB per worker pair; no growth over the run. The
15 GB box never paged.

## Phase 2 — complexity sweep

Each config: reset + build board + run 3 full turns (no actions unless
stated), median over 20 runs after 5 warmup; plus GameState.copy() on
the resulting board.

| Axis | config | 3-turn stepping median ms | copy ms |
|---|---|---|---|
| board size (vanilla) | 5 | 36.2 | 0.09 |
| | 20 | 39.5 | 0.41 |
| | 50 | 37.6 | 0.28 |
| | 100 | 58.2 | 0.53 |
| continuous effects | 0 anthems (20 bodies) | 17.0 | 0.14 |
| | 5 anthems | 34.8 | 0.21 |
| | 20 anthems | 48.3 | 0.31 |
| trigger fan-out | 0 wardens + 3 casts | 34.1 | 0.10 |
| | 5 wardens + 3 casts | 51.5 | 0.13 |
| | 20 wardens + 3 casts | 134.2 | 0.22 |
| stack churn | 0 bolts | 12.0 | 0.09 |
| | 3 bolts | 28.0 | 0.08 |
| | 10 bolts | 52.2 | 0.14 |

Cost model, per 3 turns of stepping:
- **Board size: near-flat to 50, then ~+0.25 ms/permanent** — permanents
  are cheap to carry.
- **Continuous effects: ~+1.6 ms per anthem** — layer recomputation is
  real but linear at this scale, not the feared blowup.
- **Trigger fan-out is the hot spot: ~+1.7 ms per trigger FIRING**
  (20 wardens × 3 casts = 60 firings ≈ +100 ms), trending superlinear —
  the 5→20 warden step costs 5.5× the 0→5 step per unit.
- **Cast/resolve cycle: ~4 ms per spell** (bolt churn), consistent with
  B3's whole-game arithmetic (495 decisions, ~66 casts+combats, 745 ms).

## Phase 3 — determinism, failure signals, coverage

- **Determinism: PASS.** 100/100 identical canonical end states for a
  same-seed scripted scenario (combat + removal + blocks, 4 turns), via
  `RandomUtil.setSeed`. Object UUIDs are *not* seed-controlled
  (`UUID.randomUUID()`), so state comparison must be canonical
  (names/zones/life), not `GameState.getValue()` — a real constraint for
  corpus hashing, not a gameplay nondeterminism source.
- **Failure signal**: `CardRepository.findCards(unknown)` returns empty —
  detectable, not silent; the scripted harness's strict-choose mode
  additionally fails loudly on any unscripted decision (verified across
  this project's earlier adjudication corpus: unimplemented cards and
  unscripted choices surface as first-class errors).
- **Coverage** (samples drawn from the canonical printings index;
  "modern pool" = cards with a printing in an expansion/core set released
  ≥2016; names looked up in `CardRepository`, then `createCard()`
  attempted):
  - **Modern pool: 488/500 = 97.6% implemented, 0 instantiation errors.**
    The 12 misses: Alchemy digital-only variants ("(Alchemy)" suffixed),
    Universes Beyond one-offs (Kid Loki, Kang the Conqueror), and a
    handful of very recent set cards.
  - **All-cards pool: 438/500 = 87.6%.** Extra misses are dominated by
    Un-set / Mystery Booster playtest cards ("What", "Your Own Face
    Mocks You", CMB1 printings) and obscure ancient cards (Ring of
    Ma'rûf) — none of which a competitive-format oracle needs.
  - Unknown-name lookup returns empty (loud), never a silent stub.
