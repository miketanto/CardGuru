# Architecture (proposed after feasibility verification)

Everything here assumes the findings in `research/phase1-cardscripts.md` and
`research/phase2-engine.md`. Boring technology everywhere except the engine boundary, per the
brief.

**Decision (post-feasibility): single-engine adjudication on XMage.** Forge remains a *data*
source only (the card-script ontology); its game engine is not integrated. Rationale: XMage
has the better headless story (MIT license, in-process API, ~100 ms/scenario, loud failure
modes), and the product promise is calibrated accordingly — not "provably correct," but
"actually simulated, shown step by step, with the relevant rules cited." That is already
beyond anything shipping today. Accuracy is monitored by spot-checking engine outcomes against
official rulings (see eval.md), not by a second engine.

## 1. System shape

```
                        ┌────────────────────────────────────────────┐
 user query ──► Router ─┤ 1 attribute  → Card store (Scryfall data)  │
                        │ 2 mechanical → Ability-graph index (Forge) │
                        │ 3 interaction→ Adjudication service        │
                        └────────────────────────────────────────────┘
 Adjudication service:
   NL question ─► scenario compiler (LLM, targets Phase-1 ontology)
              ─► scenario spec (JSON, versioned)
              ─► XMage driver ─► executed: outcome + game log + CR citations
                              ─► rejected/errored: visible-uncertainty answer (retrieval-only)
```

### Components, in build order

1. **Card store.** Postgres (or SQLite to start). Scryfall bulk data as the canonical card
   table; Forge name→canonical alias table (from the Phase 1 join, ~1–2% need aliases).
   Scryfall-compatible attribute query syntax parsed to SQL. Explicit non-goal: improving on
   Scryfall here.
2. **Ability-graph index.** The Phase 1 parser output, persisted. Recommendation: **don't
   reach for a graph database yet.** Median graph is 3 nodes; the entire pool is 35k tiny
   graphs. Store graphs as JSONB rows + inverted postings on (node-api, trigger-mode,
   static-mode, param-key, cost-atoms, edge-type); run subgraph predicates in the application
   layer exactly like the prototype (whole-pool scan in Python is already seconds; indexed it's
   milliseconds). A graph DB is justified only if cross-card traversals (combo search) become a
   product feature.
3. **Query language for mechanical search.** Start with a small JSON/DSL of node/edge
   predicates (what `mechanical_search.py` hard-codes), then an LLM front end that compiles NL
   → that DSL. The mined ontology *is* the compiler's target vocabulary and its validator —
   reject any compiled query using tokens outside the ontology.
4. **Adjudication service.** Thin JVM wrapper over XMage's `CardTestPlayerAPIImpl` exposed as
   JSON-scenario-in / structured-outcome-out (resident process, ~100 ms/scenario measured).
   Strict mode always on; every choice must be in the spec. Outcome record: final
   zones/life/P-T/stack + step-by-step game log + engine version. The game log is a product
   feature, not just a debug artifact — "show the simulation" is the differentiator.
5. **Simulated-scenario corpus store.** Append-only records `(scenario spec, engine outcome,
   CR tags, rulings-check status where available, generator provenance, version tuple)`.
   Seeded by parsing `Mage.Tests` (~2k human-reviewed scenarios), grown by ontology-driven
   generation.
6. **Rules layer (Phase 3).** CR parsed into numbered nodes (the numbering is a pre-authored
   hierarchy; CR text confirmed available — e.g. vendored `MagicCompRules.txt` (956 KB) in
   taw/magic-search-engine, and WotC publishes updates). Mapping table
   `ontology token → CR rule ids`, built top-frequency-first (top ~50 APIs + ~30 trigger modes
   cover the overwhelming majority of instances; long tail explicitly marked unmapped).
7. **Answer composer.** For interaction queries: verified outcome + retrieved CR rules/rulings
   → explanation with citations. The engine result is load-bearing; the LLM only narrates it.

## 2. The router (critiqued, as ordered)

- **Decision mechanism:** don't build a bespoke classifier. One LLM call with three tools
  (attribute-search, mechanical-search, adjudicate) and structured output; the interesting
  design is *fallback*, not routing accuracy.
- **Misroute containment:**
  - Attribute vs mechanical is low-stakes: run both when confidence is low; union the results
    with provenance labels. Cost is milliseconds.
  - Interaction misrouted to search returns cards instead of an answer — visible, annoying,
    recoverable ("did you want X vs Y adjudicated?" affordance).
  - The dangerous misroute is *adjudication attempted and wrong*. Containment is the
    simulated/uncertain split, not the router: if scenario compilation fails validation or the
    engine rejects/errors, the answer is explicitly downgraded to "best-effort, not simulated"
    (retrieval-only, uncertainty shown). Simulated answers are labeled as engine-simulated —
    never as rules-authoritative — and always ship with the game log and CR citations so the
    user can check the reasoning. The confidently-wrong rate is the metric that gates shipping
    (see eval.md).
- Every response carries its tier label and version tuple, so a misroute is at least always
  diagnosable from the response itself.

## 3. Graph-vs-flat-RAG ablation (designed in, per the brief's skepticism)

Detailed protocol in `plan/eval.md` §D. Architectural consequence here: the rules layer is
built as **data (mapping tables + corpus), not as load-bearing plumbing**, so that if the
ablation says flat retrieval matches graph-expansion retrieval, we delete the expansion step
without unwinding the schema. The ability graph itself is exempt from this ablation — it is
already proven by mechanical search (Phase 1) and stands regardless.

## 4. Versioning (flagged now, per §7 of the brief)

Correctness claims are only meaningful relative to a version tuple:

```
(oracle_data_date, cr_version, banlist_date, forge_commit, xmage_commit, ontology_rev)
```

- Stamp the tuple on: every parsed card graph, every corpus record, every benchmark row,
  every user-facing simulated answer.
- **Bitemporal storage is deferred, not designed in.** v1 policy: single "current" snapshot,
  full tuple stamped everywhere, immutable archived corpus per tuple. That preserves the
  ability to go bitemporal later (all history is retained) without paying the schema cost now.
  Revisit when there's a concrete product need for "answer as of Standard 2025."
- Update cadence reality check (measured this session): Forge cardsfolder and XMage master
  both moved same-day; CR updates ~5×/year; Scryfall daily. Pin everything, refresh
  deliberately, re-run the regression corpus on every engine bump and diff outcomes — that
  diff is also a free engine-bug detector (and, cute side effect, a rules-change detector).

## 5. Licensing constraints (checked)

- **XMage: MIT.** Unrestricted use, may link.
- **Forge: GPL-3.0.** Only its card scripts are used, as data we parse — its engine is not
  integrated (single-engine decision above), so no linking question arises. The parser and
  extracted ontology-as-facts are our own work product (mined statistics, not copied
  expression) — but get a real opinion before any public data release that embeds script text
  verbatim.
- **WotC Fan Content Policy:** non-commercial, no paywalled rules content, attribute properly.
  Oracle text and CR are WotC IP used under the policy; card *images* are the riskiest asset —
  use Scryfall image URIs per their guidelines rather than rehosting.
