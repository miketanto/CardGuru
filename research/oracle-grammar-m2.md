# M2 — the pre-committed kill criterion, and it does not clear

**Verdict: 3 of 5 adversarial questions pass. The pre-committed criterion was
"hold near 5/5 witness recall"; it did not hold. Per the rule as written, the
oracle grammar is a labelled fallback for unscripted cards, not a replacement
for the Forge-derived graph.**

That is the decision. The rest of this document is why, and what would change it.

## The test

`research/graph-vs-flat-ablation.md` pre-committed the adversarial slice as the
measure that decides whether the ability-graph layer earns its complexity. M2
reuses it to decide something else: whether an *oracle-derived* graph is a
genuine second derivation of the same structure.

The strictness matters. The queries are the ones the agent compiled for the
original ablation (`research/data/ablation_adversarial.json`), used **verbatim**
— written in Forge's param vocabulary (`Sac<1/Creature>`, `Cost` regex `(^|\s)T($|\s)`,
`ValidTgts$ Card`). Nothing was rewritten to suit the grammar. So M2's emitter
has to produce Forge's own vocabulary from English:

```
Viscera Seer        forge  A AB Scry       Cost: Sac<1/Creature>
                    oracle A AB Scry       Cost: Sac<1/Creature>
Prodigal Sorcerer   forge  A AB DealDamage Cost: T
                    oracle A AB DealDamage Cost: T
Counterspell        forge  A SP Counter    TargetType: Spell  ValidTgts: Card
                    oracle A SP Counter    TargetType: Spell  ValidTgts: Card
Essence Scatter     forge  A SP Counter    TargetType: Spell  ValidTgts: Creature
                    oracle A SP Counter    TargetType: Spell  ValidTgts: Creature
```

If the grammar had to be met halfway by hand-tuned queries, the comparison would
measure the query author rather than the grammar.

```bash
python3 research/scripts/m2_graph_emit.py data/dataset.jsonl.gz oracle_graph.jsonl.gz
python3 research/scripts/m2_adversarial_rerun.py data/dataset.jsonl.gz \
    oracle_graph.jsonl.gz research/data/m2_adversarial_rerun.json
```

## Results

| id | question turns on | forge | oracle | witness | foil | recall of Forge hits | Jaccard |
|---|---|---|---|---|---|---|---|
| a01 | sacrifice as **cost** vs effect | 1,380 hits | 1,074 | ✅ | ✅ | 76.1% | 74.8% |
| a02 | trigger-doubling **static mode** | 2 | **0** | ❌ | ✅\* | 0.0% | 0.0% |
| a03 | token-doubling **replacement chain** | 8 | **0** | ❌ | ✅\* | 0.0% | 0.0% |
| a04 | `{T}` as **cost** vs "tap" as effect | 1,956 | 1,708 | ✅ | ✅ | 86.9% | 86.6% |
| a05 | unrestricted **ValidTgts** | 189 | 176 | ✅ | ✅ | 75.7% | 64.4% |

\* a02 and a03 "reject the foil" only because they return nothing at all — the
same vacuous rejection the original ablation called out in the flat arm ("its
foil rejection is vacuous — it rejects the foils because it retrieves almost
nothing relevant at all"). It is not a pass.

**The three that pass, pass properly.** a01, a04 and a05 are the cost-and-target
family — precisely the distinctions the original ablation showed BM25
*structurally cannot make*. The grammar makes them from English, using Forge's
vocabulary, and recovers 76–87% of the Forge-derived answer set. On the question
the ablation cared most about, the oracle graph behaves like the Forge graph.

## Why a02 and a03 return zero

Not because the text lacks the information. Because **the emitter does not
produce the node classes those queries address**:

- a02 needs `S:Mode$ Panharmonicon` — a *static mode*. The M2 emitter writes no
  `mode` field on any node.
- a03 needs `R:Event$ CreateToken` chained via `ReplaceWith` to an api
  `ReplaceToken` node — a *replacement event plus a chain edge*. The emitter
  produces no `R` nodes and only trivial `SubAbility` chains.

So the honest reading is narrower than "the grammar failed": two whole node
classes are unimplemented, and the two questions that depend on them returned
nothing. M0 already showed replacement abilities are classifiable from text at
70.0% recall, so the information is demonstrably there; it is the emitter that
stops at kinds, APIs, costs and targets.

**What I deliberately did not do:** write a production that recognises "triggers
an additional time" → `Mode$ Panharmonicon`, or "twice that many tokens" →
`ReplaceToken`. Two targeted regexes would have turned 3/5 into 5/5 in about ten
minutes. That is tuning on the eval, which `plan/eval.md` §B rule 1 exists to
forbid — the baseline's named flaw was that "it was scored on an eval its authors
curated while building the system." A 5/5 bought that way would be worth less
than an honest 3/5.

## What this means for the plan

The pre-committed rule was explicit about both branches, and the failing branch
is the one that fired:

> Hold near 5/5 witness recall and it's a genuine second source; fall short and
> it's a labelled fallback for unscripted cards only.

So, unchanged from the M1 recommendation but now measured rather than predicted:

1. **Hybrid, not replacement.** Forge graph where a card is scripted;
   oracle-grammar graph where it is not. This was always the expected landing;
   M2 is the evidence for it rather than the hope.
2. **Tag derivation on every record.** The M2 emitter already writes
   `derivation: "oracle-grammar"` on each face. The Forge path should write
   `derivation: "script"`, and disagreement between the two becomes a QA queue.
3. **The 76–87% cross-derivation agreement on a01/a04/a05 is the useful number**
   for that QA idea. It is high enough that disagreements are worth triaging and
   low enough that there will be plenty to triage — on a01 the two derivations
   disagree about roughly a quarter of a 1,380-card answer set, and every one of
   those is either a grammar gap or a Forge scripting quirk.

## What would change the verdict

A scoped M3 — emit `R` nodes with `Event$` params, static `mode` values, and
real chain edges — followed by a **rerun of this same script with the same
verbatim queries**. That is a general capability, not a per-question fix, so it
does not violate §B rule 1. If a02 and a03 then pass without their productions
having been written against them, the criterion clears honestly and the
"genuine second source" branch opens.

Until that happens, the grammar's status is fallback.

## Caveats

- Five questions is a small slice. It was pre-committed and it is the slice the
  project already bet on, which is why it was reused — but 3/5 vs 5/5 is a
  two-question difference and should not be over-read.
- Recall-of-Forge-hits treats the Forge graph as truth. Where they disagree, the
  oracle reading is sometimes the more correct one (M1 §"Forge's structural
  choices"), so this metric understates the grammar on an unknown fraction.
- a05's Jaccard (64.4%) is notably below its recall (75.7%), meaning the oracle
  graph also returns counterspells Forge's graph does not. Those were not
  inspected and may be grammar false positives or Forge scripting gaps.

