# CardGuru — MTG rules-verified search & judge engine

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

Reproduce: `research/scripts/` (pure-Python parser + search prototype;
`CardGuruFeasibilityTest.java` drops into XMage's `Mage.Tests`). Pins: Forge `670429bf`,
XMage `1.4.60` @ master 2026-08-06.

## Phase 1 build — mechanical search (`cardguru/`)

Stdlib-only Python package: hardened Forge DSL parser (keyword nodes with Saga/Class edge
extraction), JSON query DSL with evidence-returning evaluation, postings index with candidate
pruning, CLI. See [docs/query-dsl.md](docs/query-dsl.md).

```bash
python -m cardguru build --cardsfolder <forge>/forge-gui/res/cardsfolder \
    --canonical <index.json> --pin <forge-commit>
python -m cardguru search queries/q1_combat_damage_token.json --explain
python -m pytest tests/          # unit + integration goldens
python benchmark/run.py          # 20-query golden benchmark -> benchmark/report.md
```

The benchmark (`benchmark/benchmark.json`) covers trigger→effect chains, cost structure,
replacement effects, statics, and zone logic, each with hand-labeled expected-present/absent
cards, and compares eight of them against best-effort oracle-text regexes (the Scryfall `o:`
stand-in). Current run: 20/20 goldens pass; see `benchmark/report.md`.
