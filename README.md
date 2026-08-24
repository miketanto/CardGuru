# CardGuru — MTG rules-verified search & judge engine

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
- [research/oracle-grammar-m0.md](research/oracle-grammar-m0.md) — M0 probe for an
  oracle-text grammar as a second, Forge-independent derivation of the ability graph:
  90.2% ability-kind agreement over 34,156 faces, kill criterion did not fire
- [research/oracle-grammar-m1.md](research/oracle-grammar-m1.md) — M1: effect-verb
  grammar scored on a held-out half — 83.4% precision / 76.9% recall, dev→holdout gap
  0.56pp, 12 of 33 APIs at ≥90/90; the two weakest are the two phase 1 §6 called conflated
- [research/oracle-grammar-m2.md](research/oracle-grammar-m2.md) — **M2: the
  pre-committed kill criterion does not clear.** 3/5 adversarial questions pass on
  verbatim Forge-vocabulary queries (cost/target family, 76–87% agreement); the 2 that
  fail need unimplemented node classes. Grammar's status: labelled fallback, not replacement
- [research/oracle-grammar-triage.md](research/oracle-grammar-triage.md) — triage of all
  697 cross-derivation disagreements: 95.4% are grammar debt concentrated in six named
  bugs, only 3.3% Forge artifacts; burns a01–a05 as a clean measure (see the note there)
- [research/oracle-grammar-fixes.md](research/oracle-grammar-fixes.md) — all six bugs
  fixed; corpus-wide holdout agreement on sacrifice-cost atoms 52.4% → 78.3%, `{T}`-as-cost
  recall 91.0% → 99.9%; the Disdainful Stroke correctness gate is closed (fail-closed
  `ValidTgts`), and 14 of 15 apparent over-restrictions turn out to be Forge, not the grammar
- [research/oracle-grammar-m3.md](research/oracle-grammar-m3.md) — M3 adds trigger
  modes, replacement events and chain edges to a pre-stated frequency rule; criterion
  re-run on a mechanically generated, **renewable** adversarial slice (6/9 fresh vs
  Forge 9/9). Cost/target layer is at near-parity (96–99% recall); the mode layer is
  not — so the merge unit is the field, not the card
- [research/oracle-grammar-coverage-boundary.md](research/oracle-grammar-coverage-boundary.md) —
  the coverage rule measured at its edge: 6/9 in scope vs **1/8 one rank-band outside**,
  a cliff that shows the pre-stated rule is load-bearing; trigger modes 85.5/73.9 →
  92.9/80.1; `derivation` now stamped on both derivations
- [research/oracle-grammar-cycle4.md](research/oracle-grammar-cycle4.md) — best score
  yet (7/10, 82.8% mean recall) and the largest gain came from *deleting* duplicated
  logic: the emitter was re-deriving ability kind instead of calling M0's `classify()`
- [research/oracle-grammar-cycle5.md](research/oracle-grammar-cycle5.md) — audits every
  production against the text of the cards it should match: exactly one was authored from
  a mode's *name* (`AttackersDeclared`, 0%→83.5%); trigger modes now 93.7/81.4. The
  slices are relabelled as a regression suite — a verdict needs an untouched question source
- [research/scryfall-dependency-reassessed.md](research/scryfall-dependency-reassessed.md) —
  **correction:** the oracle grammar never needed Scryfall. It reads Forge's own `Oracle:`
  line, and Forge is a live GitHub feed (92 new card scripts in 18 days). Coverage was
  always the weak argument; fidelity vs. the implementation ontology is the real one
- [research/oracle-grammar-cycle6.md](research/oracle-grammar-cycle6.md) — two ordering
  bugs (the ability-word stripper was eating Saga chapter markers; the alt-cost
  short-circuit ran before `classify()`), static modes 71.5/81.9 → 76.2/80.8, plus a
  six-class taxonomy of what has actually gone wrong — two classes no aggregate score can see

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
