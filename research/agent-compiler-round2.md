# Agent-as-compiler, round 2: 20 search + 8 scenarios + flat-baseline ablation

Round 2 scales the no-API-key evaluation pattern (see `research/agent-compiler-poc.md`)
and adds the graph-vs-flat comparison. Questions: `eval/nl_questions_dev.json`
(witness-verified, disjoint from every prior set; RulesGuru remains unread).

## NL → query DSL: 20/20 valid, 18/20 → 19/20 witness-correct

First pass jumped from round 1's 5/8 to **18/20** — the two DSL_SPEC idiom lines added
after round 1 (the `*All` variants, `ReplaceCounter`) were both used correctly this time
(d20 compiled the DamageAll branch unprompted). The failures:

- **d13** (mass bounce): used `ValidCards` where zone-changes use `ChangeType`. Two
  zero-result retries (automatic signal only) reached the correct query — final: 44 hits
  including Evacuation. → 19/20.
- **d12** (Fog): no automatic signal (22 hits, witness missing). Diagnosis: Forge gives
  fog effects their own dedicated `Fog` api; the agent guessed `PreventDamage`/oracle
  fallback. Another one-line spec fix for round 3.

## NL → scenario: 8/8 valid, 6/8 engine-clean first pass, 8/8 after fixes

All 8 compiled scenarios passed validation untouched; XMage executed them at 28–439ms.
Clean first pass: Pridemate lifegain-counter, Guttersnipe+Shock stacking (16 life),
Doubling Season × Krenko's Command (4 Goblins), Doom Blade vs indestructible Colossus
(survives), unblocked vigilance attacker (untapped, 4 damage), Wrath killing the
caster's own creatures. The two failures are the interesting part:

1. **S7 (Mind Rot)**: driver rejected the scripted discard choices. Root cause chain:
   XMage scripts multi-card selections as one `^`-joined target — but a forced discard
   with no real choice (2 cards, discard 2) must not be scripted at all. Both facts are
   now in `docs/scenario-spec.md`; final version runs clean with zero choice actions.
2. **S2 (Last Gasp)**: the agent predicted the 2/2 survives at -1/1 — internally correct
   rules reasoning, but *the question I authored fed it wrong card text* ("-3/-1"; the
   card is -3/-3). The engine killed the Bears; XMage source, Forge script, and the
   canonical oracle text all agree on -3/-3. **The engine arbitrated a false premise in
   the question itself** — exactly the failure mode ("plausible reasoning from a wrong
   card fact") that pure-LLM judges cannot detect in their own answers.

All 8 corrected scenarios are shipped under `scenarios/nl_compiled/` and run clean.

## Ablation: graph search vs LLM recall (flat baseline)

A memory-only agent (no tools) answered the same 20 questions with up to 8 card names.
Results (`research/data/ablation_baseline.json`):

| metric | flat (LLM recall) | graph search |
|---|---|---|
| witness recall | 20/20 | 19/20 |
| cards returned | 109 | **1,123** |
| verifiability | none (names only) | every hit carries its matched subgraph |
| hallucinated names | 0/109 (all exist) | n/a |

Reading it honestly, both directions:

- The baseline is **good at what fame measures**: every witness card was in its lists,
  and none of its 109 names were hallucinated. For "name a few famous examples of X",
  LLM recall works.
- But its coverage is **~10%** of the mechanically-true set (109 vs 1,123), it skews to
  format staples, it cannot prove any claim, and it goes to zero for cards outside its
  training distribution (new sets — the day-one moat). 21/109 of its names weren't
  graph-confirmed; spot-checking shows a mix of genuine graph-query imperfections
  (modal/overload variants like Vandalblast) and baseline near-misses (sorcery-speed or
  broader effects than asked).
- The product conclusion is composition, not competition: **LLM proposes phrasing,
  graph retrieves exhaustively, engine verifies** — each layer catches the layer above.

## Cumulative compiler scorecard (dev sets, both rounds)

- DSL validity: 28/28 first-pass (the ontology gate has never been hit by a dev query)
- Witness accuracy: 23/28 first-pass, 26/28 after automatic-signal retries; both
  residual misses are one-line vocabulary-idiom documentation gaps, not model failures
- Scenario validity: 10/10 first-pass; engine-clean: 8/10 first-pass, 10/10 after fixes,
  with one true rules-arbitration case (S2) caught by the engine

Phase 2b's kill criterion (~80% compilation accuracy) continues to look safe on
questions of this shape; the held-out RulesGuru run stays locked until the compiler
spec is frozen.
