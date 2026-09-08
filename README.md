# CardGuru — MTG rules-verified search & judge engine

**Picking up mid-stream? Read [docs/handoff.md](docs/handoff.md)** — current state,
defects found, architecture assessment, and the argued next step. It points at
[nl-to-dsl-research-brief.md](nl-to-dsl-research-brief.md) (prior art on semantic
parsing / text-to-SQL) and `research/agent-compiler-round2.md` (the repair loop,
already measured at 18/20 → 19/20). Read those before changing the compiler.
Graph-layer questions are formalized separately in
[graph-upgrades-research-brief.md](graph-upgrades-research-brief.md).

**New machine? Start here: [docs/getting-started.md](docs/getting-started.md)** —
clone-to-working-search in four steps (the dataset is rebuilt locally, not shipped).

Feasibility investigation, 2026-08-06. **Both core premises verified with running code; no
kill criteria fired.**

| Question | Verdict | Evidence |
|---|---|---|
| Is Forge's cardsfolder a usable ontology? | **Yes** — 34,519 faces, 98.9% scripted, closed Zipfian vocabulary, graphs traversable; 3 mechanical-search queries Scryfall can't express run in seconds | [research/phase1-cardscripts.md](research/phase1-cardscripts.md) |
| Can an engine adjudicate arbitrary board states headlessly? | **Yes** — XMage executed a custom Humility+Opalescence scenario in-process; ~100 ms/scenario; loud failure on unknown cards | [research/phase2-engine.md](research/phase2-engine.md) |

**Engine decision:** XMage is the sole adjudication engine (best headless story, MIT license).
Forge is a data source only — its card scripts are the ontology; its game engine is out of
scope. Product posture: answers are *engine-simulated, shown step by step, with CR rules
cited* — not certified correct. Accuracy is measured by spot-checking simulated outcomes
against official rulings.

Plans built on those findings:

- [plan/architecture.md](plan/architecture.md) — system shape, router critique, graph-vs-flat
  ablation designed in, versioning policy, licenses
- [plan/eval.md](plan/eval.md) — benchmark design, anti-gaming rules, frozen held-out set,
  confidently-wrong as the gating metric
- [plan/roadmap.md](plan/roadmap.md) — phases, riskiest-first ordering, explicit kill criteria
- [plan/uncertainties.md](plan/uncertainties.md) — ranked list of what's still unknown
- [research/generalized-discovery.md](research/generalized-discovery.md) — autonomous
  concept-gap mining, ablation importance, induction pipeline results
- [research/answer-frames-and-deck-fingerprints.md](research/answer-frames-and-deck-fingerprints.md) —
  taxonomic vs ontological gaps (the Annul/Disdainful lesson), lifecycle edge-cut framing,
  timing cost profiles, and the per-deck fingerprint-graph proposal

Reproduce: `research/scripts/` (pure-Python parser + search prototype;
`CardGuruFeasibilityTest.java` drops into XMage's `Mage.Tests`). Pins: Forge `670429bf`,
XMage `1.4.60` @ master 2026-08-06.

## Phase 1 build — mechanical search (`cardguru/`)

Stdlib-only Python package: hardened Forge DSL parser (keyword nodes with Saga/Class edge
extraction), JSON query DSL with evidence-returning evaluation, postings index with candidate
pruning, CLI. See [docs/query-dsl.md](docs/query-dsl.md).

**Scryfall card store** (`cardguru/cardstore.py`, SQLite, stdlib): the attribute tier, kept as
a separate artifact from the graph dataset so `forge_commit` and `oracle_data_date` stay
independent axes of the version tuple. Join rate **99.83%** (34,461 / 34,519 faces at pin
`670429bf`); the 58 misses are labeled, not aliased — 17 Alchemy `A-` rebalances are
*mechanically distinct cards* and must never inherit the paper card's oracle text.

```bash
python -m cardguru build --cardsfolder <forge>/forge-gui/res/cardsfolder \
    --pin <forge-commit>
python -m cardguru cardstore --download   # Scryfall attribute tier -> data/cards.sqlite
python -m cardguru join                   # Forge->Scryfall match report (99.83%)
python -m cardguru search queries/q1_combat_damage_token.json --explain
python -m cardguru serve                  # web UI at http://127.0.0.1:8000
python -m pytest tests/          # unit + integration goldens
python benchmark/run.py          # 20-query golden benchmark -> benchmark/report.md

# NL -> DSL compiler (requires ANTHROPIC_API_KEY; uses claude-opus-5)
python -m cardguru ask "sagas whose chapters tutor a card onto the battlefield" --explain
python -m cardguru ask "cards that let you play lands from your graveyard" --compile-only
```

The `ask` command compiles a natural-language question into the query DSL with Claude,
validates every exact api/mode/keyword/param token against the mined ontology
(`cardguru/validate.py` — out-of-vocabulary queries are rejected and errors fed back for
bounded retries), then runs the validated query. The validator and retry loop are fully
tested offline; only the LLM call itself needs credentials.

## Phase 2a — adjudication driver + corpus seed

Engine-neutral scenario JSON ([docs/scenario-spec.md](docs/scenario-spec.md)) executed by
`driver/CardGuruScenarioRunner.java` inside an XMage checkout, batched one JVM per run,
strict-choose mode always on; errors (unimplemented cards, unscripted choices) are
first-class outcomes, never silent. Demo scenarios in `scenarios/` (Humility+Opalescence:
332 ms marginal).

```bash
export CARDGURU_MAGE_REPO=~/mage        # clone + `mvn -pl Mage.Tests -am -DskipTests install`
python -m cardguru adjudicate scenarios/*.json

python corpus/parse_mage_tests.py  "$CARDGURU_MAGE_REPO"   # 6,021 scenario records from Mage.Tests
python corpus/extract_unfinished.py "$CARDGURU_MAGE_REPO"  # per-set unfinished-card lists
```

The benchmark (`benchmark/benchmark.json`) covers trigger→effect chains, cost structure,
replacement effects, statics, and zone logic, each with hand-labeled expected-present/absent
cards, and compares eight of them against best-effort oracle-text regexes (the Scryfall `o:`
stand-in). Current run: 20/20 goldens pass; see `benchmark/report.md`.
