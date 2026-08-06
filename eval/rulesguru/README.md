# RulesGuru corpus — HELD-OUT evaluation set

1,483 judge-written rules questions pulled from rulesguru.org (2026-08-06), with
per-question cited CR rules, included cards, difficulty levels, and tags. See
`stats.json` for the distribution (top tags: triggered abilities, zone changes,
replacement effects; 764 unique rules cited; 2,539 unique cards).

## Discipline (do not break this)

This corpus is the **frozen benchmark** for the adjudicator (plan/eval.md). Rules:

- **Never** read question/answer content while developing the engine, the scenario
  generator, the compiler prompts, or the answer/recommendation logic. Development
  tunes on the Forge-derived corpus and XMage's own tests only.
- Aggregate metadata (tag counts, rule-citation frequencies in `stats.json`) may be
  used to prioritize which mechanics to support — that is coverage planning, not
  tuning on answers.
- Evaluation runs read questions, produce answers, and score against
  `answerSimple`/`citedRules` — results are reported, never iterated on per-question.
- Integrity: `sha256sum -c FROZEN.sha256` must pass before any eval run. If the file
  changes, the benchmark is void.

## Files

- `rulesguru_full.json` — the questions (fields: questionSimple, answerSimple,
  answerSimpleCited, citedRules, includedCards, level, complexity, tags, url, id)
- `rules_index.json` / `cards_index.json` / `edges.csv` — question↔rule↔card joins
- `stats.json` — corpus-level distributions
- `FROZEN.sha256` — freeze hash for the question file
