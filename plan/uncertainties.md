# Ranked uncertainties (most worrying first)

Honest residual uncertainty after the feasibility session. Items verified this session are
excluded — this is what could still hurt.

1. **NL → scenario compilation accuracy (Phase 2b).** The one genuine research problem, and it
   was *not* de-risked this session — only its target vocabulary (ontology) and substrate
   (engine API) were. Nobody has demonstrated reliable compilation of free-form rules
   questions into executable board states. Mitigation is sequencing (it's last) and the
   structured-input fallback; but if the product vision is judged on NL adjudication, this is
   where it lives or dies.

2. **XMage's error rate is unmeasured.** By decision, XMage is the sole engine and the product
   posture is "simulated and shown, with rules cited" rather than "certified correct" —
   accepted trade-off. The residual unknown is *how often* XMage's implementation deviates
   from official rulings, per rules area; that number (from the 2a rulings spot-check) is the
   most informative one the project doesn't have yet, because it becomes the accuracy caveat
   shown next to simulated answers. Mitigations: XMage's own 2k-test regression suite, mature
   codebase, and the option to add Forge back as a cross-check later (the scenario spec stays
   engine-agnostic).

3. **Semantic drift between Forge scripts and actual card behavior in *search* results.**
   Phase 1 queries returned structurally-correct hits, but precision/recall was eyeballed on
   ~10 known cards per query, not measured against hand-labeled answer sets. The 50-query
   benchmark (roadmap §Phase 1.3) is designed to close this; until then "≥99% coverage,
   high precision" is an impression, not a number. Related known wart: `DB$ ChangeZone`
   conflates mechanically distinct effects, so some queries will need param-level refinement
   to avoid false positives.

4. **Choice explosion in adjudication.** Many real questions ("what happens when X meets Y")
   hide player decisions (ordering triggers, modes, replacement-effect order). Strict mode
   *forces* us to pin them — correct, but the UX and the corpus generator both need a
   principled policy for enumerating vs. asking. Unbounded branch fan-out could quietly gut
   the simulated-answer coverage rate.

5. **Scryfall/MTGJSON access from production infra.** Blocked in this sandbox (worked around
   via a GitHub-vendored mirror of unknown freshness). Not a real risk for production (public
   APIs, allowlist request), but the legality-weighted coverage number and rulings corpus are
   unverified until real bulk data is in hand.

6. **Ontology/engine drift over time.** Both repos moved same-day during this session; the DSL
   gains keywords with every set. The parser will rot without a pinned-bump-diff routine
   (roadmap standing rules). Cost is recurring maintenance, not a cliff — but it's forever,
   and it's the classic way projects like this die quietly.

7. **RulesGuru/judge-exam licensing and access for the held-out eval.** The API exists; terms
   for bulk use and redistribution are unverified. If unavailable, the held-out set falls back
   to official rulings + Stack Exchange, which are noisier and less difficulty-stratified.

8. ~~Forge harness runtime.~~ Retired by the single-engine decision: Forge's game engine is
   out of scope (data source only). Recorded for the record: its board-state API is
   code-verified but was never executed, so if a cross-check engine is ever revived, budget a
   day to prove its harness runs standalone.

9. **Fan Content Policy edges for a public dataset.** Serving simulated scenario records that
   embed oracle text and CR excerpts is presumably fine non-commercially with attribution;
   *redistributing* Forge script text verbatim in a public dataset is murkier (GPL text +
   WotC-derived expression). Needs a real read before any data release; internal use is safe.
