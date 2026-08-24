# Triage — the disagreements are the grammar's fault, not Forge's

**Verdict: 95.4% of 697 disagreements are grammar debt. 3.3% are Forge-modelling
or query-vocabulary artifacts. The debt is concentrated in six named bugs, not a
long tail.**

This reverses a hypothesis from M1. That note argued the oracle grammar's value
might lie in being a QA instrument — a second derivation whose disagreements
expose Forge's "implementation ontology, not rules ontology" problem. At current
maturity that is not what the disagreements are. The grammar is not yet good
enough to audit Forge; it is still auditing itself.

## Method

M2 left the residual untriaged, describing it only as "either a grammar gap or a
Forge scripting quirk." This classifies **the full population** — every card in
the symmetric difference of the two hit sets on a01/a04/a05, 697 cards — rather
than a sample. Causes are decided from the two graphs' own structure (which
node kinds exist, what the cost atom looks like, whether Forge's `ValidTgts`
carries a qualifier), never from a hand-written list of card names.

```bash
python3 research/scripts/m2_triage_disagreements.py data/dataset.jsonl.gz \
    oracle_graph.jsonl.gz research/data/m2_triage.json
```

## The six bugs

| # | bug | cards | question |
|---|---|---|---|
| 1 | missing effect production → no node emitted at all | **225** | a04 |
| 2 | cost atom: `another/other X` not parsed | **135** | a01 |
| 3 | cost atom: self-sacrifice by card name not detected | **102** | a01 |
| 4 | node ordering: APIs assigned in production-list order, so `Counter` is demoted to a sub-ability | **44** | a05 |
| 5 | post-nominal target restriction ignored (`counter target spell **with mana value 4 or greater**`) | **18** | a05 |
| 6 | `CARDNAME` over-detected on cards named after a type ("Goblin Chirurgeon" sacrificing "a Goblin") | **16** | a01 |

Bugs 2, 3 and 6 are all the same 20-line regex (`SAC_RE` in
`m2_graph_emit.py`) — 253 cards, one function. Bug 4 is genuinely one line: APIs
are appended in the order the `PRODUCTIONS` list declares them rather than the
order they appear in the text, so "Counter target spell. You gain 3 life."
makes `GainLife` the root and `Counter` a child, and the query's `apiKind: SP`
then misses it.

The remaining 23 artifacts split into: Forge storing an ability as an `SVar`
where the query wants `kind: A` (16, mostly modal spells nested under `Charm`),
and Forge using `NICKNAME` rather than `CARDNAME` in cost atoms for legendaries
(7) — a gap in the *compiled query's* vocabulary, where the oracle graph is
incidentally the more correct of the two.

## The finding that matters most

Bug 5 is small in count and large in consequence. The grammar reads

> Counter target spell **with mana value 4 or greater**

and emits `ValidTgts: Card` — unrestricted — where Forge correctly emits
`Card.cmcGE4`. That is Disdainful Stroke, and this project already knows that
card by name. `research/answer-frames-and-deck-fingerprints.md` records
`_counter_target_legal` in `cardguru/answers.py` evaluating `ValidTgts` as stack
restrictions — "type gates (Annul), cmc gates (Disdainful Stroke), color gates
(Flashfreeze)". That logic is load-bearing product behaviour, and it consumes
exactly the field this bug corrupts.

So the grammar does not merely mis-rank a search result here. Fed into the
answers path, it would assert that Disdainful Stroke can counter anything —
a confidently-wrong answer, which `plan/eval.md` §B names as the metric to drive
to ~0. **Any hybrid merge must not let oracle-derived `ValidTgts` reach
`answers.py` until bug 5 is fixed**, regardless of what else is decided.

## A methodological cost that has now been paid

These bugs were found by inspecting disagreements on a01, a04 and a05. That
means **those three questions are now burned as a clean measure.** Fixing the
bugs and re-reporting a01/a04/a05 would be scoring on an eval whose failures
were used to guide development — exactly what `plan/eval.md` §B rule 1 forbids,
and the same flaw the baseline was criticised for.

This was a deliberate trade: the triage is worth more than keeping five
questions pristine, because it converts "76–87% agreement, cause unknown" into
six actionable line items. But the consequence has to be honoured:

- Fixes should be validated against **M1's holdout half**, which is independent
  of the adversarial slice and already set up.
- Any future rerun of the M2 kill criterion needs a **fresh adversarial slice**.
  `plan/eval.md` §B rule 2 already anticipates this — "any later change is a new
  benchmark version."
- The a01/a04/a05 numbers in `research/oracle-grammar-m2.md` remain valid as a
  record of what was true before triage. They must not be re-quoted after fixes.

## Revised recommendation

The M2 verdict stands — hybrid, not replacement — but the reason for it has
sharpened. It is not that oracle text lacks the information; it is that the
emitter has six specific bugs, five of them small.

1. **Fix bugs 1–4 and 6.** Mostly one regex and one ordering line. Validate on
   M1's holdout.
2. **Fix bug 5 before anything touches `answers.py`.** This is a correctness
   gate, not an optimisation.
3. **Then, if a rerun is wanted, build a fresh adversarial slice.** Do not reuse
   a01–a05.
4. **Drop the "grammar as QA instrument" framing for now.** It may become true
   once the debt is paid — the 23 genuine artifacts are real, and two of them
   (NICKNAME, `Charm` nesting) are cases where the oracle reading is better —
   but 23 cards is not yet an audit signal, and claiming otherwise on this data
   would be overreach.

**Superseded:** earlier drafts of this note ended by calling blocked Scryfall
access the outstanding blocker. That was wrong — the grammar reads oracle text
from Forge's own `Oracle:` line and never needed Scryfall. See
[research/scryfall-dependency-reassessed.md](scryfall-dependency-reassessed.md).
