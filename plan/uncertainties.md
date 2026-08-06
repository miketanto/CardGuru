# Ranked uncertainties (most worrying first)

Honest residual uncertainty after the feasibility session. Items verified this session are
excluded — this is what could still hurt.

1. **NL → scenario compilation accuracy (Phase 2b).** The one genuine research problem, and it
   was *not* de-risked this session — only its target vocabulary (ontology) and substrate
   (engine API) were. Nobody has demonstrated reliable compilation of free-form rules
   questions into executable board states. Mitigation is sequencing (it's last) and the
   structured-input fallback; but if the product vision is judged on NL adjudication, this is
   where it lives or dies.

2. **Correct-but-different: engine implementations that are wrong in the same way.**
   Cross-engine diff catches independent bugs; it cannot catch shared misreadings of the rules
   (both engines are community reimplementations, and XMage/Forge devs read each other's
   trackers). The 90%+ agreement number is unmeasured — the 2a agreement rate is the single
   most informative number the project doesn't have yet. Rulings-based spot-checks are the
   only independent oracle, and they're English text.

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
   the "verified" coverage rate.

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

8. **Forge harness runtime.** Its board-state API is code-verified but was not executed here
   (FModel/resource init). Small risk it's fiddly (classpath resources, localization files);
   contained to one day in roadmap 2a.3. If it truly can't run standalone, the cross-check
   engine loses its cheapness and item 2 above gets worse.

9. **Fan Content Policy edges for a public dataset.** Serving verified scenario records that
   embed oracle text and CR excerpts is presumably fine non-commercially with attribution;
   *redistributing* Forge script text verbatim in a public dataset is murkier (GPL text +
   WotC-derived expression). Needs a real read before any data release; internal use is safe.
