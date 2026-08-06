# Agent-as-compiler proof of concept (no API key needed)

The two LLM-gated pipelines — NL→query-DSL (Phase 1) and NL→scenario (Phase 2b)
— were exercised using in-session agents as the LLM stage, with the exact same
contracts the API-based compiler uses: the production system prompt (built by
`nl_compiler.build_system_prompt` from the mined ontology), the ontology
validator as the gate, and bounded retry on feedback. No API credentials, no
extra cost beyond the session.

Questions are a fresh dev set (`eval/nl_questions_poc.json`) — disjoint from
the 20-query dev benchmark and from the held-out RulesGuru corpus, which
remains unread.

## NL → query DSL: 8/8 valid, 5/8 → 6/8 witness-correct

First pass: **all 8 compiled queries validated against the ontology on the
first attempt** (the production gate would have accepted every one), and 5/8
found their witness card. The retry round used only the automatic zero-result
signal — "this query returned 0 hits" — with no golden leaked, mirroring a
feedback mode the product can implement:

| q | question (abbrev.) | first pass | after retry |
|---|---|---|---|
| q1 | ETB damage to each opponent | valid, 14 hits, witness miss | — |
| q2 | double +1/+1 counters | valid, 0 hits | 53 hits, witness miss |
| q3 | land sacs itself to draw | **witness OK** (35 hits) | |
| q4 | counter on lifegain | **witness OK** (35 hits) | |
| q5 | counter unless pays | **witness OK** (79 hits) | |
| q6 | opponent discards → lose life | **witness OK** (3 hits) | |
| q7 | mill on draw | valid, 0 hits | **witness OK** (5 hits) |
| q8 | planeswalker reanimates | **witness OK** (14 hits) | |

The q7 retry is the striking one: the loosened query's five hits are exactly
the mill-on-draw family a Magic player would name (Sphinx's Tutelage, Jace's
Erasure, Psychic Corrosion, Teferi's Tutelage, Master's Councillors). Also
honest: q7's original wording was *my* error (it described "mill the drawing
player"; Tutelage mills an opponent when you draw) — the agent compiled my
wording faithfully, and the retry found the right family anyway.

The two remaining misses are **spec-documentation gaps, not model failures**:
- q1: Forge scripts "damage to each opponent" as `DamageAll`/`ValidPlayers`,
  while the spec text only advertised `DealDamage`. The compiled query was
  defensible (14 real matches of the targeted variant).
- q2: counter-doubling chains to `ReplaceCounter` (mirroring the documented
  `ReplaceToken`), but `MultiplyCounter` exists in the vocabulary as a rarer
  API and the agent picked it — validation rightly passed, results were wrong.

Both idioms are now documented in `DSL_SPEC` (this POC set is a dev set;
tuning on it is what it's for). Expected effect: q1/q2-class questions compile
correctly without retry.

## NL → scenario: 2/2 compiled, 2/2 engine-VERIFIED, zero fixes

A second agent read `docs/scenario-spec.md` plus one example scenario and
compiled two rules questions into scenario JSON:

1. *"My opponent controls Grizzly Bears, I Bolt it — what happens?"*
2. *"I control Doubling Season and cast Attended Knight — how many Soldiers?"*

Both passed `validate_scenario` untouched, and both **executed in XMage with
all 5 expectation checks passing** (434ms / 178ms): the Bears die to A's
graveyard, and exactly 2 Soldier Tokens enter. The agent independently got the
strict-choose details right — the separate `target` action, `wait_stack`
before checking, stopping at BEGIN_COMBAT. Shipped as
`scenarios/nl_compiled/`.

## What this proves, and what it doesn't

Proves: the *architecture* works end-to-end with a real LLM in the loop — the
ontology-closed vocabulary + validator gate + retry-on-signal produces
runnable, engine-verifiable output, and the scenario spec is learnable from
its documentation alone. The Phase 2b kill criterion ("compilation accuracy
stalls below ~80%") looks unlikely to fire on questions of this shape.

Doesn't prove: performance on *hard* judge questions (layers, replacement
ordering, corner cases) — that's what the held-out RulesGuru run is for, and
it stays untouched until the compiler is frozen. Sample size is 8+2; the POC
measures pipeline viability, not accuracy claims.

Cost note: ~87k subagent tokens total for both pipelines including retries.
