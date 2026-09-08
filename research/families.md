# Disjunctive api/mode families: mined, wired in, measured

> **RESOLVED 2026-08-07.** At 7 seeds per arm on the pooled goldens the
> intervention is **+9.8pp golden recall, exact permutation p = 0.017**. The
> "not significant" verdict in §5 below was a property of the *benchmark*, not
> of the intervention — see §9 and `research/benchmark-density.md`. §5 is kept
> as written because the reasoning that got there was sound on the evidence
> available; it was the evidence that was too thin.

Follows `docs/handoff.md` §4b (the measured execution-feedback A/B) and
`research/execution-feedback.md`. Those established that the repair loop works
and that **the residual failures are vocabulary, not structure**. This note is
about one slice of that vocabulary wall — the slice where the compiler picks a
real api name that means the right thing and still answers a narrower question
than it was asked, because Forge spells the same concept several ways.

`shapes.py` mines the opposite direction: one name, several meanings, split by
params. Nothing yet mined **one meaning, several names**, and the ontology
cannot supply it — it is a flat frequency table in which `Destroy` and
`DestroyAll` are two unrelated tokens.

Everything below is derived from `data/dataset.jsonl.gz`. Nothing is
hand-authored, per the brief's "mine it, don't hand-author it".

## 1. What a family is, and the two signals that define it

`cardguru/families.py`, one command:

```bash
python -m cardguru families           # -> data/families.json, 88 families
python -m cardguru families --anchor destroy
```

A group must satisfy two signals that fail in opposite directions.

**Anchor (language).** Forge writes a player-facing sentence on most nodes. A
word anchors a facet when it is *characteristic* of it (on ≥30% of its nodes)
and *specific* to it (≥4× its rate among nodes of the same facet kind).

Three details in that sentence were each a measured correction:

- **Per token, not per node.** Measuring "does this node's description contain
  the word" makes verbose facets collect *the*, *your*, *this*, *that* — they
  have more chances to contain them. A unigram rate normalises length away and
  the function-word families disappear.
- **Conditioned on facet kind.** Against a global background, *whenever* is
  "specific" to 34 trigger modes at once. It is specific to the node kind, not
  to any facet. Against a kind-conditional background its lift is ≈1 and it is
  gone.
- **The word must occur in oracle text.** Forge descriptions carry template
  tokens — `CARDNAME`, `EFFECTSOURCE` — which are frequent, specific, and not
  words a question can contain. Oracle text is the player-facing rendering and
  has no such token, so requiring survival there keeps the anchor vocabulary to
  things a user can actually type.

**Substitutability (structure).** Sharing a word is not enough — the two halves
of a reveal chain share *reveal*. Members of a family are ALTERNATIVES, so they
should appear on the same card no more often than chance. The threshold is
chance itself: co-occurrence lift 1.0.

That last point matters against `execution-feedback.md` §2, which had to reject
the over-narrow signal because **no threshold separated good from bad**. Here
one does, and it is not a number anyone picked:

| | max co-occurrence lift |
|---|---|
| `Destroy` / `DestroyAll` | 0.7 |
| `DealDamage` / `DamageAll` | 1.4 |
| `Untap` / `UntapAll` | 0.0 |
| the combat-trigger group (complements) | **600** |
| the reveal chain (complements) | **40** |

Substitutes sit at chance; complements sit two orders of magnitude above it.
The shipped cut is 3.0, which is anywhere in the empty gap between them.

## 2. What the two signals buy, separately

Both are load-bearing, and each was verified by watching the other one fail.

**Distributional similarity alone merges antonyms.** The first version scored
facets by cosine over param profiles and graph neighbours. It ranked
`GainLife`↔`LoseLife` at 0.69, `PutCounter`↔`RemoveCounter` at 0.62,
`Taps`↔`Untaps` at 0.69, `ReduceCost`↔`RaiseCost` at 0.84 — every one an
antonym pair, because opposites have identical distributions. This is the
textbook failure and it is fatal here: a disjunction over an antonym pair is
wrong in a way that is invisible in the query text.

Under an anchor, opposites can only meet on a word they share. *gain* selects
one side, *lose* the other. They do still meet under *life*, and that is left
alone deliberately: a question that says only "life" is genuinely ambiguous
between the two, and the digest shows `life: GainLife, LoseLife` next to
`gain: GainLife`, so the ambiguity is visible rather than buried.

**Anchors alone admit function words and chains.** Before the co-occurrence
peel, *hand* grouped `Reveal` with `RevealHand` (the two ends of one ability)
and *whenever* grouped 23 unrelated trigger modes.

## 3. The independent check that needed no model

Before spending anything on an A/B: the 37 hand-vetted queries in
`benchmark/compiled_questions.json` contain **13 distinct api/mode
disjunctions a careful human wrote**. They were never used for mining, so
asking how many a mined family reproduces is a free, seed-free validity check.

**5/13 reproduced (Jaccard ≥ 0.5), 6 partial, 2 missed.**

Exact hits: `DealDamage|DamageAll`, `Destroy|DestroyAll`, `Untap|UntapAll`,
`Pump|PumpAll|Debuff`, `DealDamage|DamageAll|LoseLife`.

The two clean misses are the most useful output of this note, because they are
*the exact pattern the module exists for*:

| missed | why |
|---|---|
| `ChangeZone` / `ChangeZoneAll` | `ChangeZone` is the most overloaded api in the corpus (6,596 nodes). Its descriptions are so varied that **no word reaches 30% coverage**. There is no anchor to be had. |
| `Sacrifice` / `SacrificeAll` | **No word above 20% coverage either** — sacrifice effects are usually a cost or a sub-ability, and the sentence lives on the parent node. |

### The obvious fix for that, measured and rejected

Give a node with no sentence of its own the nearest ancestor's, following
chain edges. It does what it says: `Sacrifice|SacrificeAll` and
`PutCounter|PutCounterAll` both appear.

It also **destroys `DealDamage|DamageAll` and `Untap|UntapAll`**, by diluting
every effect node's word profile with its trigger's context. Net **4/13,
down from 5/13**. Not shipped. The families are mined from each node's own
sentence.

This is the second time this session's line of work has had a plausible
improvement fail on measurement (the first was the over-narrow signal), and
the pattern is the same: the mechanism was real, the side effect was larger.

## 4. A reproducibility defect found *between* the two A/B runs

The A/B was run twice, and the reason is worth more than either result.

After the first run scored, `cardguru families` was run again and reported a
**different number of families**: 88, then 91, then 89. Both `_peel` and
`_merge` iterate sets of `(kind, name)` tuples, whose order follows string
hashes and therefore changes per interpreter process. Under `PYTHONHASHSEED`
1 / 2 / 3 the same command mined 90 / 89 / 91 families.

That is disqualifying on its own — an artifact that differs from itself cannot
be diffed against a Forge bump — but the diagnosis found a worse bug behind it.
**A pair over the co-occurrence cut implicates both its members equally**, so
the greedy "drop the worst offender" step is a tie *by construction*, and the
tie-break was deciding which member left. In the `[untap]` group exactly one
pair is over the cut (`TapOrUntap`–`Untap` at 3.07, against a cut of 3.0), and
the arbitrary break dropped **`Untap` (480 nodes)** rather than
**`TapOrUntap` (50)** — discarding the member the family is named for.

Fixed by breaking the tie toward the rarer facet: the family is named for a
concept its high-volume members carry, and a rare api that co-occurs with a
common one is the rider. The digest is now byte-identical across hash seeds
(`test_mining_is_deterministic` runs the miner in three subprocesses).

**The first A/B measured an artifact that can no longer be regenerated**, so
its numbers are reported below only as a lesson, not as a result. 33 of its 50
digest lines survive into the shipped artifact.

## 5. The A/B, on the shipped artifact

Three seeds per arm, `--source agent` (in-session agents as the model turn, no
API spend), `--signals zero`, the production retry budget. The only difference
between arms is the `DISJUNCTIVE FAMILIES` block in the system prompt, switched
with `CARDGURU_FAMILIES=off`. Prompt cost: **+861 tokens, +10.4%**. The control
arm is shared between both runs — its prompt contains no families block and did
not change.

| arm | pass /37 | golden recall | absent respected | Jaccard vs reference |
|---|---|---|---|---|
| control (`off`) | 20.7 (20, 21, 21) | 74.5% | 94.7% | 0.660 |
| families (shipped) | 20.7 (21, 21, 20) | 76.3% | 94.7% | 0.673 |
| delta | **+0.0** | **+1.9pp** | **0.0** | +0.013 |

> The discarded first run, on the pre-fix artifact, scored 21.0 (21, 21, 21)
> and **77.6%** — a full +1.2pp more from a nondeterministic redraw of the same
> miner. That gap is the seed-and-artifact lottery the handoff warns about,
> landing on the intervention itself rather than on the model.

**The effect is not established.** Pass rate is flat, the paired sign test is
1 win / 1 loss (p=0.75), and the arm does not even emit more disjunctions:
**control 8/11/11 queries carry an api/mode `any`, families 9/10/12** — a
difference of 0.3 per run, which is nothing. Three seeds cannot resolve a
+1.9pp recall move.

### What *is* established

**It costs no precision.** Across all six runs of both arms:

- **absent-golden leaks are identical** — the same two questions
  (`landfall-payoffs`, `flash-permission-static`), three seeds each, both arms.
- **median result-set size 72 → 66.**

The standing worry about telling a compiler to disjoin is that it returns more
and means less. That did not happen in any seed.

**One question moved, robustly, for the stated reason.**

| question | control | families | |
|---|---|---|---|
| `move-counters-between-permanents` | 0 / 3 | **2 / 3** | in **all three** seeds, and in all three of the discarded run |

```
control    {"chain": {"from": {"api": "RemoveCounter"},
                      "to": {"api": {"any": ["PutCounter", "PutCounterAll"]}}}}
families   {"node": {"api": "MoveCounter"}}          <- mined [counter] line
```

That question failed in **all 13 runs** of the §4b A/B. The control arm still
reasons its way to a `RemoveCounter → PutCounter` chain; the families arm knows
`MoveCounter` exists because the mined `[counter]` line puts it next to the
`Counter` it was already thinking of. Six treatment seeds across two different
artifacts, no exceptions.

### The other movements are seed noise, and it is worth showing why

Net recall was +2.0 cards of 107: five questions up, two down. The two
"regressions" are **not caused by the families** —

| | control | families | |
|---|---|---|---|
| `enters-as-a-copy` | 4/4/4 | 4/4/**0** | lost in seed 3 only |
| `impulse-exile-then-cast` | 2/2/2 | **0**/2/2 | lost in seed 1 only |

— and in the seeds where both arms succeed, the two arms emit **byte-identical
queries**. Each lost seed is one agent writing a worse query, in an arm that
had no relevant family line. Symmetrically, `reanimate-on-a-trigger` gained in
one seed of three. At this sample size single-seed movements in both directions
are the background, which is exactly the handoff's point.

## 6. Honest limits

- **~1 in 5 of the 50 digest lines is junk.** Structural-English anchors
  survive at low volume — `this`, `one`, `more`, `that`. Ranking by
  volume × anchor-IDF demotes them below the truncation in most cases but does
  not eliminate them. None was implicated in a loss, and the absent-golden
  numbers say they cost nothing measurable, but they are spending prompt
  tokens to say nothing.
- **The two biggest apis have no family and cannot get one this way.**
  `ChangeZone` and `Sacrifice` are §3. A different signal is needed for them —
  name morphology (`X`/`XAll`) is the obvious candidate and is derivable from
  the vocabulary alone, but it was not tried here.
- **The aggregate effect is not significant and this note does not claim it
  is.** What three seeds support: precision flat, one question fixed for the
  stated reason in six of six treatment seeds, prompt cost known and small.
  What they do not support: any statement about the +1.9pp. Deciding this needs
  more seeds, and the cheapest way to get them is the live harness on Opus
  rather than agents — roughly $3.50 per arm-seed by §4b's measured rate.
- **Do not read the two A/B runs as five or six seeds per arm.** They used
  different family artifacts. Only the control is shared.
- **Agents are not the API.** `--source agent` runs an in-session agent per
  model turn, batched 8 questions to an agent for cost. Both arms were batched
  identically, so the contrast is fair, but the absolute numbers are an
  Opus-class result and should be compared to the handoff's Opus rows (21.0 /
  72.9%) rather than its Haiku ones. The control arm reproducing those almost
  exactly is the evidence that the substitution is sound.

## 7. Reproducing

```bash
python -m cardguru families                     # mine -> data/families.json
python -m cardguru families --anchor destroy    # inspect one family
python -m pytest tests/test_families.py -q      # incl. the determinism test

# A/B. Re-run each command until it stops printing pending task files; agents
# answer them in between. Arms MUST use separate --run-dir: the system prompt
# is written once per run dir.
python benchmark/eval_compile.py --source agent --signals zero \
    --run-dir benchmark/agent_runs/fam_s1 --json-out benchmark/agent_runs/fam_s1.json
CARDGURU_FAMILIES=off python benchmark/eval_compile.py --source agent \
    --signals zero --run-dir benchmark/agent_runs/off_s1 \
    --json-out benchmark/agent_runs/off_s1.json
python benchmark/ab_families.py benchmark/agent_runs/*_s*.json
```

Raw numbers: `research/data/eval_families_2026-08-07.json`.

The cheap check, if you only want to know whether a miner change was good, is
§3 — 13 human-written disjunctions, no model, no API key, one second.

---

## 9. Resolved: the powered A/B

§6 said the aggregate effect was not established and named the cost of settling
it. `research/benchmark-density.md` then showed the benchmark was the binding
constraint and put a number on the fix: **7 seeds per arm** on pooled goldens.
That test has now been run — 14 runs, 7 per arm, same prompts, same `--signals
zero`, same 16/16/8 batching as the original seeds.

### Result

| goldens | control | families | gap | exact permutation p |
|---|---|---|---|---|
| **pooled / dense (302 present)** | 66.13% | **75.97%** | **+9.84pp** | **0.017** ✅ |
| original (106 present) | 76.01% | 77.76% | +1.75pp | 0.156 ✗ |

**The families block works.** Golden recall +9.8pp, significant at 7 seeds.

The second row is the point of the whole detour: **the same 14 runs, scored on
the old goldens, are still not significant.** Extrapolating from the old sd
(pooled ≈2.0pp) that benchmark would have needed **~20 seeds per arm** to see
an effect the dense one resolves at 7. Four rounds of measurement called this
intervention dead because the instrument judged ~3 cards per question, and
those cards were the ones every system already found.

A t-test is not used. With 7+7 seeds all C(14,7)=3432 relabelings are
enumerable, so `benchmark/final_ab.py` computes the exact permutation p — no
normality assumption, which matters because the families arm is visibly skewed.

### The pass metric stays flat, and that is expected

+0.14 questions, p=1.00. With ~8 present goldens per question the
all-or-nothing verdict needs all of them, so it saturates. **On dense goldens
the headline is recall.** The pass count is retained only for continuity with
§4b.

### Pool bias: checked, not assumed

The dense goldens were adjudicated from a pool built out of six runs; the eight
added for this test did not contribute to it, so cards they find that nobody
judged are invisible. That only cancels if it lands on both arms equally:

| | judged fraction of returned cards |
|---|---|
| control | 4.7% |
| families | 4.7% |

**Arm difference 0.0pp.** The bias is real in absolute terms — 95% of returned
cards are unjudged, which is normal for pooled IR evaluation and is why recall
rather than precision is the headline — but it is symmetric, so the comparison
stands.

### What is still true from §6

- **The intervention is inconsistent.** Families seeds run 63.9 … 86.1
  (sd 8.17) against control's 59.3 … 69.2 (sd 3.32). It is a real mean
  improvement with a wide spread, not a uniform lift.
- **Only three questions move on the pass metric** (+1 `attack-trigger-makes-token`,
  +1 `dies-exile-instead`, −1 `token-doubling`). The gain is overwhelmingly
  partial recall inside questions that still fail overall — exactly the shape
  §5 predicted a disjunction would have.
- **`ChangeZone` and `Sacrifice` still have no family**, and description
  inheritance is still a measured loss.

### Recommendation

Turn the block on by default. It is +861 prompt tokens for +9.8pp recall at
p=0.017, with no measured precision cost in 14 runs.
