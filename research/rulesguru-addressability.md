# RulesGuru benchmark addressability

**Question:** before building the NL→scenario path, what fraction of the frozen
held-out benchmark (1,483 judge questions, `eval/rulesguru/`) could the XMage
simulator even *attempt* — i.e. every card in the question is implemented?

**Method** (`eval/addressability.py`): reads ONLY per-question metadata (card
names, level, complexity, tags — never question/answer text; freeze hash
verified first). Card names are matched against XMage's implemented-card list
minus the `unfinished` exclusions, with multi-face names resolved through the
canonical index's face groups (`Insectile Aberration` → `Delver of Secrets`).

## Result: 97.0% of the benchmark is engine-addressable

| status | questions | share |
|---|---|---|
| engine_ready (all cards implemented) | 1,439 | **97.0%** |
| engine_partial (some cards missing) | 29 | 2.0% |
| engine_blocked (no card implemented) | 6 | 0.4% |
| no_cards (pure rules question) | 9 | 0.6% |

Ability-graph coverage (search/citations layer) is even higher: **99.2%** of
questions have every card in the Forge-derived graph.

By difficulty — addressability barely degrades with difficulty, which is the
important finding (the hard questions are hard because of *rules interactions*,
not exotic unimplemented cards):

| level | ready | of |
|---|---|---|
| 0 | 96% | 207 |
| 1 | 98% | 571 |
| 2 | 98% | 438 |
| 3 | 97% | 185 |
| Corner Case | 88% | 82 |

All 12 "Complicated"-complexity questions are engine-ready.

## What's actually missing

The top missing cards are a museum of things engines refuse to implement, not
a coverage gap: **Shahrazad** (subgames, ×7), **Ertai's Meddling** (×3),
**Illusionary Mask** (×2), and text-changing effects (Trait Doctoring,
Exchange of Words, Artificial Evolution, Spy Kit). Only 6 questions are fully
blocked (ids 468, 469, 475, 1344, 2554, 7204 — the Shahrazad cluster).

## Implication

The ceiling for engine-simulated answers on this benchmark is ~97%, so the
binding constraint is **not** card coverage — it's (1) compiling a question
into a faithful scenario and (2) mapping the engine outcome back to the asked
question. That's where eval effort should go. The honest-degradation path for
the remaining 3% is already designed: graph + CR-citation retrieval with a
Best-effort label (99.2% graph coverage).

Full per-question data: `research/data/rulesguru_addressability.json`.
