# Roadmap — phased, riskiest-first, with kill criteria

Feasibility session (2026-08-06) already retired the two biggest risks: the ontology extraction
works (Phase 1 proven with running code) and the adjudication engine works (XMage executed
arbitrary scenarios headlessly at ~100 ms each). What remains is mostly engineering plus one
genuine research problem (NL → scenario compilation), which is deliberately scheduled last.

## Phase 1 — Mechanical search MVP (≈ 2–4 weeks of focused work)

Riskiest-first inside the phase:
1. **Harden the parser** (edge cases: `AlternateMode` variants, `SPECIALIZE`, meld, Class/Saga
   chapters as structured levels rather than raw params). Property test: every face
   round-trips; zero silent drops. *(Prototype exists.)*
2. **Name canonicalization + Scryfall join** on real bulk data (needs network allowlist:
   api.scryfall.com or data.scryfall.io). Alias table for the ~1–2% mismatches; attach
   legalities, rulings, printings, images-by-reference.
3. **Query DSL + index** (postings over node/edge predicates; see architecture §1.2). Port the
   three prototype queries; write the ~50-query benchmark with hand-verified answers (eval.md §C).
4. **NL → query-DSL compiler** (LLM, ontology-validated output, reject-and-retry loop).
   This is the first LLM component and it is *checkable*: compiled queries either validate
   against the ontology or don't.
5. Minimal web UI: Scryfall-syntax box + mechanical-query results with "why it matched"
   (the matching subgraph, rendered as text).

**Kill criteria (Phase 1):** none remaining — the sink-the-premise scenario (DSL too sparse /
too Count$-dependent) was tested and did not fire. Residual quality bar: if the 50-query
benchmark can't reach ~0.9 precision with the DSL approach, the NL compiler ships later;
DSL-only search is still a product.

## Phase 2a — Verified corpus (≈ 2–3 weeks, parallelizable with Phase 1 after week 1)

1. **Engine-neutral scenario spec** (JSON) + resident XMage driver service. *(API verified;
   wrapper is plumbing.)*
2. **Parse `Mage.Tests` into corpus records** — ~2k files of human-reviewed scenarios for free.
3. **Forge driver** behind the same spec (their `AITest`/`GameSimulationTest` harness;
   code-verified, one day to prove at runtime — do this first within 2a as it's the only
   unexecuted claim left).
4. **Ontology-driven scenario generator**, starting from Phase 1 graph queries (e.g. every
   damage-trigger card × every replacement-of-damage card). Budget is a non-issue at 100 ms;
   the real work is choosing templates that produce *interesting* interactions.
5. **Cross-engine diff pipeline**; disagreements queue for human triage. Store agreement rate —
   it is the empirical bound on single-engine trust and decides how much the product may say
   "verified" without the second engine.

**Kill criteria (2a):** all three from the brief were tested and did not fire. New one:
if XMage-vs-Forge disagreement exceeds ~5% on generated scenarios and triage shows both sides
wrong in nontrivial shares, "verified" claims require per-area human curation — scope of
"verified" shrinks to curated areas (visible-uncertainty product posture, not project death).

## Phase 3 — CR mapping + retrieval (≈ 3–4 weeks)

1. CR parser (numbered hierarchy + cross-references + glossary). Format-stability check across
   the last ~6 CR releases before committing to the parser design.
2. Ontology→CR mapping table, top-frequency-first (top ~50 APIs + 30 trigger modes + keyword
   list, which maps nearly 1:1 to CR 702). Everything unmapped is *labeled* unmapped.
3. Retrieval corpus assembly: CR chunks, rulings, verified scenarios (from 2a), all
 version-stamped.
4. **Run the graph-vs-flat ablation (eval.md §D). Pre-committed decision rule; cut the graph
   expansion if it doesn't earn ≥5 points on the adversarial slice.**

**Kill criterion (Phase 3):** the ablation itself. Losing it kills the graph *retrieval* layer,
not the project — search (Phase 1) and verified adjudication (2a) don't depend on it.

## Phase 2b — NL → scenario compilation (the research problem; only now)

Sequenced after 1, 2a, 3 because it consumes all of them: the ontology as target vocabulary,
the corpus as few-shot/training data, CR mapping for explanation.
1. Hand-write scenario specs for ~100 real questions (RulesGuru/rulings) = compiler eval set.
2. LLM compiler: question → scenario spec, validated (cards exist & implemented, choices pinned,
   zones legal). Invalid → visible fallback to retrieval-only answer. Compilation accuracy is
   its own gate (eval.md §E) *before* any adjudication accuracy is claimed.
3. Choice-explosion policy: enumerate bounded branches (≤ ~16) and present branch outcomes;
   otherwise ask the user to pin the choice interactively.

**Kill criterion (2b):** if compilation accuracy on the held-out 100 stalls below ~80% after
serious iteration, ship adjudication as a *structured* input feature (user picks cards/board
via UI — the spec format is the feature) plus best-effort NL, and revisit as models improve.

## Phase 4 — Product routing + answer composition (≈ 2 weeks)

Router-with-fallback per architecture §2; answer composer citing CR + rulings + engine record;
confidently-wrong rate gates launch (eval.md §C). Held-out benchmark scored once, at the end.

## Standing engineering rules

- Pin: Forge `670429bf`, XMage `1.4.60`/master-2026-08-06, CR version, data snapshot date;
  stamp the tuple on every artifact (architecture §4).
- Every "verified" user-visible answer must trace to a stored engine execution record.
- Re-run the corpus on every engine version bump; diff before adopting.
- Network allowlist needed for production data: api.scryfall.com / data.scryfall.io,
  mtgjson.com, rulesguru.org, magic.wizards.com (all blocked in this sandbox; GitHub mirrors
  used as stand-ins this session).
