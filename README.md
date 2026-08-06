# CardGuru — MTG rules-verified search & judge engine

Feasibility investigation, 2026-08-06. **Both core premises verified with running code; no
kill criteria fired.**

| Question | Verdict | Evidence |
|---|---|---|
| Is Forge's cardsfolder a usable ontology? | **Yes** — 34,519 faces, 98.9% scripted, closed Zipfian vocabulary, graphs traversable; 3 mechanical-search queries Scryfall can't express run in seconds | [research/phase1-cardscripts.md](research/phase1-cardscripts.md) |
| Can an engine adjudicate arbitrary board states headlessly? | **Yes** — XMage executed a custom Humility+Opalescence scenario in-process; ~100 ms/scenario; loud failure on unknown cards; Forge has a parallel API (bonus: brief's deck-vs-deck-only assumption was wrong) | [research/phase2-engine.md](research/phase2-engine.md) |

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
