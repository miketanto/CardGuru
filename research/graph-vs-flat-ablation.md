# Graph vs flat-RAG ablation (plan/eval.md §D) — executed, graph retained

**The pre-committed question:** does graph retrieval beat flat text retrieval by ≥5
points on an adversarial slice (questions where mechanics and oracle wording diverge)?
If not, the graph retrieval layer gets cut. **Verdict: graph wins by +60 points of
witness recall on the adversarial slice. The layer stays.**

## Setup

- **Flat arm** (`eval/flat_baseline.py`): BM25 over oracle text + type line for every
  card in the dataset, with symbol expansion ({T}→"tap"), stopwording, plural stemming.
  This is what a text-RAG system retrieves over. Scored on its top-30.
- **Graph arm**: the agent-compiled DSL queries (same no-API-key compiler pattern as
  rounds 1–2), executed over the ability-graph index.
- **Question sets**: the 20-question dev set (text-friendly mix) plus a 5-question
  adversarial slice (`eval/nl_questions_adversarial.json`), each adversarial question
  carrying a witness (must find) and a textually-similar-but-mechanically-wrong foil
  (must not find). RulesGuru remains unread.

## Results

**Dev set (text-friendly):** flat witness@30 = 15/20; graph = 19/20. Flat retrieval is
genuinely serviceable when the question's words appear in oracle text — consistent with
the architecture's decision to keep a Scryfall-style text tier in the router.

**Adversarial slice (the deciding measure):**

| metric | graph | flat (BM25@30) |
|---|---|---|
| witness recall | **5/5** | 2/5 |
| foil rejected | 5/5 | 5/5* |
| mean precision@10 vs ground truth | **0.82** | 0.10 |

\* Flat's foil rejection is vacuous — it rejects the foils because it retrieves almost
nothing relevant at all (its top-30 for "sacrifice as a cost" is a soup of
sacrifice-adjacent cards in which neither witness nor foil ranks).

Where and why flat fails:
- **a01 cost-vs-effect sacrifice**: "sacrifice a creature" appears verbatim in both
  Viscera Seer (cost) and Fleshbag Marauder (effect); BM25 cannot see which side of the
  colon the phrase sits on. Graph: `Cost` param regex — exact.
- **a04 tap costs**: the cost is the symbol {T}, not the word "tap"; even with symbol
  expansion, tap-as-cost vs tap-as-effect (Twiddle) is invisible to text. Graph: `T` in
  the Cost param.
- **a05 unrestricted counterspells**: "counter target spell" is a substring of "counter
  target creature spell" — lexical retrieval structurally cannot express "and nothing
  more". Graph: exact `ValidTgts` match.
- **a03 token doubling**: Anointed Procession's text never says "double" (it says
  "twice that many"); flat ranks it 21st, below mana-doublers that do say "double".
  Graph: `R:CreateToken → ReplaceToken` chain — 8 hits, all correct.
- **a02 trigger-doubling** is the one flat got right (Teysa's oracle text happens to
  contain nearly the question's exact words) — and even there its precision@10 was 0.2
  vs the graph's exact 2-card answer.

Scoring notes, for honesty: the graph's 0.10 precision on a01 against my ground-truth
set is a truth-definition artifact, not retrieval error — the agent's query also counted
self-sacrifice costs (`Sac<1/CARDNAME>` on creatures), a defensible reading of the
question that my narrower truth regex excluded. And a05 needed one automatic
zero-result retry: the Forge idiom for unrestricted counterspells (`TargetType$ Spell`
+ `ValidTgts$ Card`) was a vocabulary-documentation gap — the third such idiom found by
this eval method, each now a one-line spec fix.

## Decision

Per the pre-committed rule (≥5 points on the adversarial slice): **+60 points of
witness recall, 8× precision@10 — the graph retrieval layer earns its complexity and
stays.** The complete picture across both ablations run this session:

- vs **LLM parametric memory**: graph gives ~10× coverage and proofs; memory gives
  famous exemplars only.
- vs **flat text-RAG**: parity on text-friendly questions, decisive graph win the
  moment cost/effect, replacement/trigger, target-restriction, or cross-card structure
  is what the question is actually about.

Compose all three: text tier for attribute queries, graph tier for mechanics, engine
for verification.
