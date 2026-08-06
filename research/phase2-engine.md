# Phase 2 — Headless adjudication engines: verification of the reconnaissance

> **Post-review decision (2026-08-06):** XMage only. The Forge cross-check described below was
> investigated and works, but is cut from scope — Forge stays a data source (ontology), and
> the product claims "engine-simulated with rules cited" rather than dual-engine verification.
> This document remains the research record as investigated. Current plan: `plan/`.

**Go.** The preliminary conclusion in the brief was right in direction — XMage is the better
adjudication engine — but *understated* in two ways: (1) XMage's in-process JUnit harness is
even better-shaped for us than the server "test mode" the README advertises, and (2) Forge is
**not** limited to deck-vs-deck simulation; it has its own arbitrary-board-state test API,
which makes the cross-check engine much cheaper than expected. None of the three Phase 2 kill
criteria fire.

All findings below were verified by building and executing code in this session.

## 1. XMage — verified empirically

Setup path (reproduced end-to-end here):

```bash
git clone --depth 1 https://github.com/magefree/mage.git      # 294 MB working tree
cd mage && mvn -pl Mage.Tests -am -DskipTests install -T 1C   # JDK 21 targeting Java 8; ~25 min on 4 cores, one-time
mvn -pl Mage.Tests test -Dtest=LayerTests                     # run any scenario suite
```

- Engine version at test: `mage-1.4.60`, master @ 2026-08-06. Card pool: **32,047 card classes**
  in `Mage.Sets` (README's "31,000+" claim: confirmed).
- **No server, no GUI, no X11 involved.** `CardTestPlayerBase.execute()` constructs `GameImpl`
  directly in-process and runs it on a game thread. The advertised server "test mode"
  (`MageServerImpl.testMode`, gating cheat commands) exists but is the *wrong* entry point for
  us — the JUnit-layer API is a pure library path. `Mage` core's AWT imports are Color/geometry
  only; tests ran headless in this container.

### The scenario API (`CardTestPlayerAPIImpl`, ~2,600 lines)

Everything §4 of the brief asked for exists as a first-class method:

| Need | API |
|---|---|
| Place cards in any zone | `addCard(Zone.BATTLEFIELD/HAND/GRAVEYARD/LIBRARY/EXILE/COMMAND, player, name, count, tapped)` |
| Life / counters / state | `setLife`, counters helpers, `setChoice`, aliases for specific card instances |
| Drive actions | `castSpell(turn, step, player, name)`, `activateAbility`, `attack`, `block` |
| Force every decision | `setChoice`, `setModeChoice`, `addTarget`, `setChoiceAmount` |
| Control the clock | `setStopAt(turn, step)`, `setStopOnTurn`, `waitStackResolved` |
| Read resulting state | `getPermanent(...)` → power/toughness/types/counters; `assertLife`, `assertPermanentCount`, `assertGraveyardCount`, `assertExileCount`, `assertTapped`, `checkStackObject`, full game log |

### Determinism — verified in source, exercised in runs

`setStrictChooseMode(true)` + scripted choices means **no AI involvement at all**
(`TestPlayer.canChooseByComputer()` returns false in strict mode). Any decision the scenario
script did not pre-answer fails the run with "Found wrong choice command" rather than letting
an AI improvise. Repeated runs of the layer tests produced identical results. Residual
nondeterminism (shuffles) is irrelevant when scenarios stack known libraries via `addCard(LIBRARY,…)`.

### Failure detection — verified empirically (the non-negotiable)

Probe test written and executed this session
(`research/scripts/CardGuruFeasibilityTest.java`, dropped into `Mage.Tests`):

- **Unknown/unimplemented card:** `addCard(..., "Totally Nonexistent Card Name XYZ")` →
  `IllegalArgumentException: [TEST] Couldn't find a card: …` in 0.13s. Loud, immediate,
  pre-execution. Implementation status is also queryable up front via `CardRepository`.
- **Unscripted decision in strict mode:** loud `Assert.fail` (verified in `TestPlayer` source).
- **Engine exception ≠ wrong answer:** exceptions propagate out of `execute()`; a scenario
  either completes with readable state or throws.
- **Residual risk — a card implemented incorrectly** — cannot be detected from inside XMage by
  definition. Mitigations: XMage's own 2,017-file regression suite, cross-engine execution
  against Forge (below), and per-card rulings as an oracle for spot-checks.

### The showcase scenario, executed

Custom test (not from their suite): Humility + Opalescence on the same battlefield, Humility
with the earlier timestamp, strict mode, stop at combat:

```
Humility     P/T = 4/4, is creature: true
Opalescence  P/T = 0/0, is creature: false   (correct: it animates only *other* enchantments)
```

A definite, engine-executed answer to the brief's canonical nightmare question, in one JVM run.

### Latency — measured

| Cost | Measured |
|---|---|
| One-time full build | ~25 min (cold Maven cache, 4 cores) |
| JVM + card-DB init (first-ever run, builds H2 card DB) | ~34 s |
| JVM + card-DB init (warm DB) | ~7 s |
| **Marginal per scenario, warm JVM** | **20–150 ms** (7 layer tests: 0.02–0.15 s each) |

At ~100 ms/scenario, one warm JVM ≈ **500k+ scenarios/day/core**. Offline corpus generation
(Phase 2a) is compute-trivial. Online per-query adjudication fits interactive latency with a
resident JVM service (JSON-in/JSON-out wrapper around the same API; the test classes are
plain library code — nothing about them requires the JUnit *runner*, JUnit is just the default
harness. A thin wrapper module in `Mage.Tests`' classpath is the natural first cut.)

## 2. Forge — the brief's assumption was wrong, in our favor

The brief assumed Forge only offers deck-vs-deck AI matches (`sim -d`). That CLI exists, but
Forge *also* ships an arbitrary-board-state test API, structurally parallel to XMage's:

- `forge-gui-desktop/src/test/java/forge/ai/AITest` + `simulation/SimulationTest`:
  `addCard(name, player)`, `addCardToZone(name, p, ZoneType)`, `addTokens`,
  `devModeSet(PhaseType, player)` (jump to any phase), `playUntilStackClear`,
  `playUntilPhase`, `GameSimulator.simulateSpellAbility(sa)` → resulting `Game` snapshot.
- `GameSimulationTest` alone contains 73 board-state scenario tests; there is also a
  `gamesimulationtests/` package with `GameStateSpecification` builders and even
  `ComprehensiveRulesSection103/104` test classes.
- Not yet executed in this session (Forge's test classpath needs `FModel` resources
  initialized — an hour of setup, deferred); code inspection is unambiguous about the API's
  existence and shape.

Consequence: the **cross-check engine is cheap**. Same scenario spec, two independent
implementations, diff the outcomes; disagreement → flag for human/ruling review instead of
shipping either answer. This is the practical answer to "silently wrong card implementation."

Caveats: Forge's tests live in `forge-gui-desktop` (module wiring, not GUI dependence — they
run in CI headless); Forge is GPL-3.0 (fine as an isolated service; don't link it into
non-GPL code), XMage is MIT.

## 3. Corpus generation (2a) — shape of the generator

- Enumerate scenario templates from the Phase 1 ontology (trigger modes × effect APIs ×
  zones), instantiate with concrete cards mined from the ability graph (e.g. all 101
  combat-damage→token cards × removal/replacement interactions).
- Emit each scenario as a generated JUnit-style class or via a thin driver; record
  `(setup, actions, choices, final-state assertions, game log)`.
- **Seed corpus for free:** `Mage.Tests` itself is ~2,000 files of human-reviewed
  scenario→assertion pairs (including `LayerTests`, `HumilityTest`, replacement, copy,
  layers, SBA suites). Parsing these into structured records is a weekend job and yields
  thousands of verified interactions before we generate anything ourselves.

## 4. Kill criteria — none fire

| Criterion | Verdict |
|---|---|
| Arbitrary board states need a fork | **No.** First-class API in both engines, verified by execution in XMage. |
| Latency impractical for corpus generation | **No.** ~100 ms marginal; ~7 s warm-start amortized. |
| Can't detect unimplemented cards / errors | **No.** Loud pre-execution rejection + strict-mode choice failures, verified. Incorrect-implementation risk handled by cross-engine diff + rulings spot-checks, not by trusting one engine. |

## 5. Open items carried forward

1. Execute one Forge scenario end-to-end to confirm its harness runs outside their CI (only
   code-inspected here).
2. Wrap the XMage API in a JSON-scenario driver (no JUnit runner) and measure service latency
   under load; design the scenario-spec format to be engine-neutral so the same spec drives Forge.
3. Decide policy for choice-explosion scenarios (modal spells, ordering choices): enumerate
   all branches (bounded fan-out) vs. require the question to pin choices.
4. Alchemy/digital-only cards exist in neither engine's paper pool consistently; exclude from v1.
