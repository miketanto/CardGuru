# Session handoff — 2026-08-07

State of the search product after a working session, the defects found, and the
argued plan for what comes next. Written to be read cold.

**Branch:** `claude/mtg-rules-search-feasibility-05siv8` (no `main`). Nothing
committed this session — everything below is uncommitted working-tree state.

---

## 1. Where things stand

`python -m pytest tests/` → **222 passing** (was 177). `python benchmark/run.py`
→ 20/20 goldens. Both green.

### Built this session

| module | what it is |
|---|---|
| `cardguru/cardstore.py` | Scryfall attribute tier, SQLite, stdlib. 38,623 cards. |
| `cardguru/join.py` | Forge↔Scryfall join + match report. **99.83%** (34,461/34,519). |
| `cardguru/server.py` | Stdlib HTTP server + `cardguru/static/index.html`. `serve --verbose`. |
| `cardguru/diagnose.py` | Explains empty AND over-narrow results. |
| `cardguru/shapes.py` | Mines param-shape clusters from the dataset. |
| `cardguru/families.py` | Mines disjunctive api/mode families. See §4c. |
| `cardguru/similar.py` | Card-anchored search ("cards like X"). |

New CLI: `cardstore`, `join`, `serve`, `shapes`, `similar`.

### Environment (already set up on this machine)

```bash
~/forge-src                     # Forge at pin 670429bf
data/dataset.jsonl.gz           # 34,519 faces
data/cards.sqlite               # Scryfall, snapshot 2026-08-07
data/shapes.json                # mined param shapes (regenerate: cardguru shapes)
export CARDGURU_TOKENSCRIPTS=~/forge-src/forge-gui/res/tokenscripts
```

`data/` is gitignored — all of it rebuilds from `docs/getting-started.md`.

### LLM configuration

Default model is **`claude-haiku-4-5`** (cheapest), overridable via
`CARDGURU_MODEL` or `--model`. Measured: **$0.0020/call** with prompt caching
engaged, ~$0.004 without. Successful compiles are cached to
`data/compile_cache/` keyed on (model, question, system prompt), so a repeat
question costs nothing.

**Haiku vs Opus was measured, and the sticker price misleads.** Opus 5 is 5×
the list price but only ~1.2–3× the real cost, because the prompt now exceeds
Haiku's 4,096-token cache floor only *just*, while Opus caches from 512. Opus
also produced materially better queries (3 cards vs 0 on one probe). Use Haiku
for clicking around, Opus for anything you'd judge quality on.

> ⚠️ **The API key used this session was pasted in a chat transcript. Treat it
> as compromised and rotate it.** It was never written to a file in this repo.

---

## 2. Defects found and fixed

Seven questions from the owner produced seven distinct defects. In **every
case the graph already contained the right answer and the DSL could express
it** — the failure was always getting from the question to the query.

| # | question | root cause | fix |
|---|---|---|---|
| 1 | white/blue ≤3 counter | colour filtered on `types`, which never holds a colour (it's in `manaCost`) | prompt convention + `diagnose` |
| 2 | ...disruption recall | `Counter` only; missed `Airbend`, exile-off-stack, `RaiseCost` | `disrupts_spells` hook |
| 3 | creatures stop casting | wrapped a standalone static in a `chain from T` | prompt convention |
| 4 | ...(same) | `Caster: Opponent` dropped symmetric cards (Meddling Mage, Sanctum Prelate) | prompt convention |
| 5 | can't cast at instant speed | `CantBeCast` is 8 meanings split by params; guessed `SorcerySpeed` (doesn't exist) | `shapes.py` mining |
| 6 | cards like Reprieve | nothing ever *looked at the card*; kept `Destination: Hand`, dropped `Origin: Stack` → 1,170 | `similar.py` |
| 7 | lands pay life to fetch | filtered `ChangeType` on `"Land"`; fetchlands say `Plains,Island` | `near_misses` |

Plus two defects in my own fixes, both caught by tests:

- **`disrupts_spells` had invented complements.** Nothing "pays off" holding
  counterspells. The fake synergy injected 13 edges into the deck-fingerprint
  graph and made a 2-card package outrank the Dimir deck's real game plan.
  Complements are now empty, with a comment saying why.
- **Signature ranking was backwards.** Ranked nodes by param count, so the
  generic ETB trigger (3 params, 4,471 cards) beat `api: Counter` (0 params,
  514) and "like Spellstutter Sprite" returned 4,470. Now ranks by
  **selectivity**, band-limited (10 … 10% of corpus) with greedy validation —
  pure selectivity overshoots the other way and picks rare riders like
  `Attributes: Plotted`.

### Two bugs worth remembering

- **Debug logs didn't appear.** stdout is block-buffered when redirected;
  `tail -f` showed nothing. Every log line now flushes explicitly.
- **A typo silently answered a different question.** "aven interruptor" (card
  is *Interrupt**er***) failed exact lookup, fell through to the NL compiler,
  and returned 756 unrelated cards with no indication anything went wrong.
  Names now resolve fuzzily and **report the correction**.

---

## 3. Architecture assessment

### Rules mapping: an index, not a graph

`research/data/cr_mapping.json` is real — 3,317 CR rules, effective
2026-08-07. Coverage weighted by node volume: keywords 89%, trigger_modes 92%,
replacement_events 96%, apis 84%.

**`static_modes`: no table at all, 0 of 138.** `CantBeCast`, `RaiseCost`,
`Continuous` are all unmapped — and static modes are exactly where the
prohibition/tax questions failed.

More importantly it is a **flat token → rule lookup**. There is no rules
hierarchy, no dependency between layers (613) and replacement effects (614),
no link from a trigger to the state-based action that caused it. It supports
*citation*, not *reasoning*.

### Structural limits that are real

The blind benchmark found three of these independently before the owner did:

1. **Single-card scope.** `evaluate()` takes one `CardGraph`; no joins, no
   pair enumeration → combos unreachable.
2. **No rules-layer causation.** A creature dying to a state-based action and
   to a sacrifice produce an identical `ChangesZone` trigger. *This is the one
   a real rules graph would fix.*
3. **Values are opaque strings.** Furnace of Rath and Torbran are node-for-node
   identical; "double" vs "+2" lives inside `ReplaceCount$DamageAmount/Twice`.
   The `value` field is now matchable, but there is no arithmetic.
4. **No attribute tier in the evaluator.** `cards.sqlite` has `cmc` and
   `colors`; the query evaluator cannot see them, so "≤3 mana" is a regex
   approximation.

### Is semantic search the answer?

Partly, and not where you'd point it first. Measured: across the 8 benchmark
queries with a text baseline, **313 cards were found only by structure** and
**216 text matches were correctly rejected** by structure. Text embeddings
cannot recover Bejeweled Warg's 3-hop chain, because the text never says it.

Embeddings would have helped on the *vocabulary/concept* failures (#2, #6, #7)
and not on the *precision* failures (#1, #3, #5).

> **Superseded by §3b.** I originally recommended embedding the ontology to
> retrieve a relevant vocabulary slice. The research brief argues against doing
> that first: our vocabulary fits in context, and retrieval adds a failure mode
> we don't have. Where embeddings *are* clearly indicated is mining the alias
> layer (§3b) — mapping player slang onto DSL patterns.

The final answer and the evidence chip must keep coming from the graph. An
embedding can rank; it cannot say *why*.

---

## 3b. READ THE RESEARCH BRIEF FIRST

`nl-to-dsl-research-brief.md` (repo root) already surveys this exact problem —
semantic parsing / text-to-SQL — with verified citations. Plus two prior
evaluations nobody should redo: `research/agent-compiler-poc.md` and
`research/agent-compiler-round2.md`.

**The prior work already validated the repair loop.** Round 2: 20/20 queries
valid, **18/20 witness-correct first pass, 19/20 after retry** — using nothing
but the automatic zero-result signal, no goldens leaked. Execution feedback is
not speculative here; it is measured and simply never wired into production.

Round 2's remaining failures are the same treadmill this session fell into:
d13 used `ValidCards` where zone-changes use `ChangeType`; d12 missed Forge's
dedicated `Fog` api. Both were fixed by adding a line to `DSL_SPEC` — and the
doc's own next step was "another one-line spec fix for round 3." That is the
hand-patching loop, already diagnosed a round earlier than this session.

### Where the brief corrects the plan below

- **Do NOT build ontology retrieval / schema linking first.** §3 cites *The
  Death of Schema Linking?* — modern models identify relevant schema in the
  presence of irrelevant data, and their no-retriever pipeline ranked first on
  BIRD at 71.83%. Our vocabulary is a few hundred primitives and the prompt is
  ~8.3k tokens; it fits. A retriever adds a failure mode we don't have
  (dropping the one primitive that mattered). Measure full-vocab-in-context
  first. My earlier "embed the ontology" advice was wrong on ordering.
- **The largest expected gain is an alias layer, which was not in my plan.**
  §7: players say *tutor, wrath, blink, sac outlet, removal, ramp, stax* —
  none are Forge primitives. BIRD's knowledge-evidence swing is **20pp**,
  larger than any architectural gain in the brief. The brief says **mine it,
  don't hand-author it** (EDHREC tags, Scryfall community tags, MTG Wiki
  slang). This session hand-authored exactly one such alias (`disrupts_spells`)
  after the owner found the gap — the brief predicted that wall and the method.
- **Synthetic corpus via inverted Overnight**, also not in my plan. §5: card
  script → canonical NL → LLM paraphrase → (NL, DSL) pairs, correct by
  construction. SynthCypher got +40% this way and had to *invent* its programs;
  **we already have ~30,000 real ones**. Verify by execution — unverified
  generation gave only 50% executable Cypher.
- **Write the BNF.** §4: grammar *prompting* delivers most of the gain even
  without enforced decoding. We have no BNF.
- **Don't expect 90%.** §6: leading BIRD systems ~82% vs ~93% human; on the
  harder BEAVER benchmark, agentic methods with GPT-5.2 reach 10.8%. Design to
  degrade visibly.

### Our seven failures, in the brief's taxonomy (§8)

| our failure | brief's diagnosis |
|---|---|
| colour in `types`; `Caster` on symmetric cards | over-constrained primitive selection → relaxation-and-retry |
| **disruption ≠ Counter; Plains≠"Land"** | **vocabulary mismatch → alias layer (the predicted wall)** |
| static wrapped in a chain | compositional generalisation → decomposition |
| `CantBeCast` param shapes | wrong primitives chosen → more few-shot pairs |
| "like Reprieve"; Spellstutter ranking | not in the taxonomy — card-anchored search is our own addition |

Two of seven are the vocabulary wall the brief flags as the biggest single win.

### One open question the brief raises that we have de facto answered

§11 asks whether the search DSL needs to be the Forge DSL "or should we design
a separate query language over the extracted graph." We already did: `querydsl`
is a separate language over the extracted graph, and Forge syntax is ingestion
only. Worth recording as settled.

---

## 4. The bottleneck, and the plan

**The graph is not the bottleneck. Unaided query formulation is.**

The retry loop in `nl_compiler.compile_question` only ever sees `validate()`
errors — syntax and vocabulary. **It never executes the query.** Five of the
seven failures were detectable from the result count alone:

| question | first compile | signal |
|---|---|---|
| white/blue ≤3 counter | 0 | zero |
| creatures stop casting | 10 | suspiciously few |
| lands pay life to fetch | 2 | suspiciously few |
| like Reprieve | 1,170 | suspiciously many |
| like Spellstutter | 4,470 | suspiciously many |

This is text-to-SQL / semantic parsing. Ranked by expected value here:

1. **Execution-guided generation** — execute candidates, feed results back.
   Our version is stronger than the generic one: our queries are
   **conjunctions of independently executable predicates**, and every failure
   except #6 was *one bad conjunct inside an `all`*. `diagnose` and
   `near_misses` already compute exactly the right feedback; they just run
   after the answer instead of before.
2. **Exemplar retrieval** — 37 solved question→query pairs already sit in
   `benchmark/compiled_questions.json`, used for nothing but a UI sidebar.
   Retrieve k-nearest as few-shot.
3. **Schema linking** — retrieve the relevant ontology slice. Usually the
   largest single gain on wide schemas, and ours is wide.
4. **Sample-and-rerank** — sample N, execute, pick by golden agreement. At
   $0.002/call, N=5 costs a cent. Also fixes the observed non-determinism
   (same question, different query, different run).
5. **Decomposition** — compile clause-by-clause.

Skip grammar-constrained decoding: the validator already rejects invalid
tokens, and none of the failures were invalid tokens. They were valid queries
that meant the wrong thing.

### Recommended order (revised against the brief)

0. **Eval harness first.** ✅ **Done** — `benchmark/eval_compile.py`, see §4b.
1. **Wire the repair loop into production.** ✅ **Built**, live A/B not yet run
   (needs `ANTHROPIC_API_KEY`). See §4b.
2. **Mined alias layer** — the largest expected gain, and the class two of the
   owner's seven questions fell into.
3. **BNF + grammar prompting** (cheap half of §4; skip enforced decoding until
   the error taxonomy shows syntax errors — ours currently shows none).
4. **Synthetic corpus** via inverted Overnight, execution-verified.
5. **Only then** consider retrieval/schema linking, and only if measurement
   says full-vocab-in-context is the limit.

Cross-card joins and rules causation are genuine research — last, and they are
formalized in **`graph-upgrades-research-brief.md`** (repo root): six research
questions on the graph layer, each with our measured evidence, candidate fields
to search, and a decision criterion. That brief is explicitly *after* this one —
formulation is the binding constraint today.

---

## 4b. Built since: the eval harness and the repair loop

### The harness — `benchmark/eval_compile.py`

One command: compile all 40 questions from scratch, execute each compiled
query, score the result set against `expect_present`/`expect_absent`, print a
number. Graded on **execution**, not query text.

```bash
python benchmark/eval_compile.py --source reference    # no API key needed
python benchmark/eval_compile.py --signals off         # live, validate-only
python benchmark/eval_compile.py --signals zero        # live, + execution feedback
python benchmark/eval_compile.py --source agent        # in-session agents, no API spend
```

**`--source agent` runs the harness without spending API credit**, the way
`agent-compiler-poc.md` and round 2 were run — but as a first-class mode rather
than by hand. It replaces *only the model turn*: same system prompt, same
validator gate, same execution feedback, same retry budget, so the score is
directly comparable to a `--source live` run. Implementation is
`cardguru/agent_bridge.py`, and the design point worth knowing is that it does
**not** reimplement the loop — everything except the model turn is
deterministic, so each round replays the prior turns for free through the real
`compile_question` and stops where the next model turn is owed. There is no
second copy of the loop to drift.

Run the same command repeatedly: each invocation folds in whatever answers
exist, advances every question as far as it can, and writes a task file per
turn still owed. Verified end-to-end on a 3-question slice — agents answered,
the answers folded in, and the run scored (8/10 goldens, Jaccard 0.78 vs the
vetted queries).

Note the constraint the task files impose and that any operator must enforce:
the agent gets the system prompt and the conversation, and must not search the
corpus or read the goldens. An agent with tools is a different system and its
score is not comparable to the numbers below.

**Scorable set is 37, not 40.** The three questions with no goldens on either
side are exactly the three the reference file marks `unexpressible`
(`triggers-off-state-based-actions`, `triggers-on-opponent-voluntary-choice`,
`infinite-combo-enablers`). Counting them as failures would put a permanent
7.5% floor under the error rate; they are excluded and *named* in the headline
rather than dropped silently. A test asserts the two sets stay identical.

**The ceiling is 36/37 (97.3%), and the 37th is unreachable.**
`removal-that-never-says-destroy` requires Pongify, whose Forge node is
`SP$ Destroy` and whose oracle text opens "Destroy target creature" — it cannot
satisfy "without ever saying destroy". Verified against the dataset, and the
reference file's own `judgment_calls` flags it. **The golden is wrong**, and per
the brief's §6 warning about BIRD, a bad golden is worth fixing before it moves
a ranking. Left alone pending the owner's call on the replacement.

`--signals` is part of the compile cache key, so the arms of an A/B never serve
each other's cached compiles.

### The repair loop — `cardguru/repair.py`

`compile_question` now takes a `checker`; `ExecutionChecker` runs each validated
candidate and feeds the result back as the next user turn, exactly like a
validation error. Wired into `ask`, `serve` and the harness, default `zero`.
Two guards stop the loop arguing with itself: an advisory fires at most once per
compile, and re-emitting the identical query counts as standing by it.

**What was measured, and what it cost me** — full write-up in
`research/execution-feedback.md`:

| signal | complains about known-good queries | calls for 37 questions |
|---|---|---|
| zero-hit → per-clause diagnosis | **0 / 37** | 37 |
| over-narrow (relaxation ≥2×) | **24 / 37** | 61 |
| dead predicate (matches no real value) | **0 / 37** | 37 |

The middle row is the correction to §4's plan above. `near_misses` does compute
the right *explanation* — it does not carry a decision boundary. Known-good
queries reach unlock ratios of 267×, 206× and 123×; the real `ChangeType`
defect (#7) sits at **61×**, below all three. No threshold separates them,
because a correct precise predicate is supposed to do most of the filtering.
So the ranking stays as human-facing diagnosis and triggers nothing. Only the
judgement-free half of it — a predicate matching none of the values its
parameter actually takes — is acted on, under `--signals full`.

### The live A/B, measured

Three seeds per arm on Haiku, two valid seeds on Opus (the third died when the
API key ran out of credit, and is discarded — it is not a model result).
Reference ceiling on the same 37 scorable questions is 36 / 99.1%.

| model / arm | pass (of 37) | golden recall | zero-hit queries |
|---|---|---|---|
| Haiku, `off` | 11.3 (9, 14, 11) | 43.3% | 12.3 |
| Haiku, `zero` | **14.0** (13, 15, 14) | **56.1%** | 4.3 |
| Haiku, `full` | 14.7 (16, 14, 14) | 55.1% | 3.0 |
| Opus, `off` | 19.5 (19, 20) | 68.7% | 3.0 |
| Opus, `zero` | **21.0** (21, 21) | **72.9%** | **0.0** |

**Execution feedback works.** `zero` beats `off` in every seed on both models:
+2.7 questions / +12.8pp recall on Haiku, +1.5 / +4.2pp on Opus, with zero-hit
queries down 65% (Haiku) and to zero (Opus). Paired over 111 Haiku
question×seed pairs: 13 wins, 5 losses (sign test one-sided p=0.048).

**`full` is not better than `zero`.** Paired 9–7, mean recall 1pp *worse*. The
dead-predicate check costs nothing in false positives but does not earn a
default-on. Left available, default `zero`.

**Model choice dominates the intervention.** Haiku→Opus is +7.5 questions;
the repair loop is +1.5 to +2.7. Anything judged on quality should be on Opus,
and the ~6× per-call cost ($3.51 for ~200 Opus calls) is the price of it.

> ⚠️ **Read the seed spreads before quoting any single number.** The `off` arm
> scored 9, 14 and 11 on three identical runs — a spread *larger* than the
> effect being measured. A one-seed comparison of this harness is worthless.
> This was learned the expensive way twice in one session: the first Haiku A/B
> reported +4 of which about half was luck, and the `full` arm was called a win
> on two seeds before the third erased it. **Golden recall is the more stable
> metric** — it is over 107 cards rather than 37 all-or-nothing verdicts, and
> it moved in the same direction in every seed.

### Two defects this run surfaced

- **The validator accepts value predicates the evaluator rejects.** A compiled
  query used `{"not": {...}}` where a value predicate goes; `validate()`
  returns `[]` and `match_value` raises `QueryError`. The harness now scores
  that as a compile failure instead of losing the run, but the fix is a shape
  check in `validate.py` — **not made**, because it would change both arms
  after the numbers above were collected. Note the `zero` arm survived it
  unaided: the checker caught the exception, fed it back, and the model
  repaired it (`compiled ok` 39/40 → 40/40).
- **The residual failures are vocabulary, not structure.** Every query still at
  zero after repair is a guessed *parameter value* the data never uses —
  `Cost` regex `"Tap<"`, `AddAbility` containing `"doesn't untap"`,
  `params.Destination` where the param is `DestinationZone`. The zero signal
  detects these and cannot fix them: the diagnose tree says which clause is
  empty, not what that parameter contains. This is the brief's §7 wall,
  confirmed on our own data, and it is the argument for doing the alias/value
  layer next.

---

## 4c. Mined disjunctive families — built and measured

The §4b conclusion was "the residual failures are vocabulary, not structure".
One slice of that is now mined rather than guessed: **one concept, several api
names**. `{"api": "Destroy"}` silently drops 364 `DestroyAll` nodes, and the
ontology cannot say otherwise — it is a flat frequency table.

`cardguru/families.py` derives 88 families from the dataset (`cardguru
families` → `data/families.json`), digests the top 50 into the system prompt
(**+861 tokens, +10.4%**), and is switched off with `CARDGURU_FAMILIES=off`.
A family needs two signals that fail in opposite directions: a shared
player-facing **anchor word** from Forge's own descriptions (which keeps
antonyms apart — pure distributional similarity ranked `GainLife`↔`LoseLife`
at 0.69) and **co-occurrence at or below chance** (which keeps out the two ends
of a chain). The second has the decision boundary `near_misses` turned out not
to have: substitutes measure 0–1.4×, complements 40–600×.

Three seeds per arm, `--source agent`, `--signals zero`:

| arm | pass (of 37) | golden recall | absent respected | median hits |
|---|---|---|---|---|
| control (`off`) | 20.7 (20, 21, 21) | 74.5% | 94.7% | 72 |
| families | 20.7 (21, 21, 20) | 76.3% | 94.7% | 66 |

> ✅ **SUPERSEDED — see the resolved result below.** At 3 seeds on the sparse
> goldens this read as "not established". It was the benchmark, not the
> intervention.

**At 3 seeds the aggregate effect was NOT established:** pass rate flat, paired
sign test 1 win / 1 loss (p=0.75), and the treatment arm did not even emit more
disjunctions (control 8/11/11 queries carry an api/mode `any`; families 9/10/12).

### Resolved at 7 seeds per arm on the pooled goldens

| goldens | control | families | gap | exact permutation p |
|---|---|---|---|---|
| **pooled / dense (302 present)** | 66.1% | **76.0%** | **+9.8pp** | **0.017** ✅ |
| original (106 present) | 76.0% | 77.8% | +1.75pp | 0.156 ✗ |

**The families block works: +9.8pp golden recall.** Turn it on by default —
+861 prompt tokens, no measured precision cost across 14 runs.

The second row is why §4d exists: **the same 14 runs on the old goldens are
still not significant**, and that benchmark would have needed ~20 seeds per arm
to see it. Pool bias was checked rather than assumed — judged fraction of
returned cards is 4.7% in *both* arms, difference 0.0pp.

Caveats that survive: the pass metric stays flat (+0.14, p=1.00) because with
~8 goldens per question an all-or-nothing verdict saturates — **on dense
goldens the headline is recall**; and the intervention is *inconsistent*
(families seeds span 63.9–86.1, sd 8.17, against control's 3.32). Full detail
in `research/families.md` §9; exact permutation test in
`benchmark/final_ab.py`.

Two things it *does* establish:

- **No precision cost, in any seed.** Absent-golden leaks are byte-identical
  between arms across all six runs, and result sets got slightly *smaller*.
  The standing worry about telling a compiler to disjoin did not materialise.
- **`move-counters-between-permanents` is fixed**, 0/3 → 2/3 golden cards in
  **six of six** treatment seeds across two artifacts, via the mined
  `[counter]` line putting `MoveCounter` next to `Counter`. It had failed in
  **all 13 runs** of the §4b A/B. The other movements are single-seed and go
  both ways; in the two apparent regressions the arms emit *identical* queries,
  so they are the agent, not the families.

> ⚠️ **The A/B was run twice and the first run is discarded.** `cardguru
> families` was not deterministic — `_peel` and `_merge` iterate sets of facet
> tuples, so the same command mined 88 / 89 / 90 / 91 families across runs. The
> tie it was breaking arbitrarily is structural (a pair over the cut implicates
> both members), and it was dropping `Untap` (480 nodes) rather than
> `TapOrUntap` (50) from the `[untap]` family. Fixed, with a determinism test.
> The discarded run scored 21.0 and 77.6% — **+1.2pp better from a
> nondeterministic redraw of the same miner**, which is the size of the lottery
> now landing on the intervention as well as the model.

Two things measured and rejected rather than shipped, both in
`research/families.md`:

- **Description inheritance** (give a sub-ability its parent's sentence) fixes
  the two clean misses — `ChangeZone`/`ChangeZoneAll` and
  `Sacrifice`/`SacrificeAll`, whose nodes carry no sentence of their own — and
  **wrecks `DealDamage|DamageAll` and `Untap|UntapAll`** by diluting every
  effect node with its trigger's context. Net 4/13 vs 5/13 on the seed-free
  check. Not shipped.
- Ranking families by raw volume, rather than volume × anchor IDF, promotes
  structural-English anchors (*this*, *one*, *more*) into the digest.

The seed-free check worth knowing: the 37 vetted queries contain **13
api/mode disjunctions a human wrote**, and a mined family reproduces **5**
(6 partial, 2 missed). It needs no model and no API key, so it is the cheap
regression test for the miner — far cheaper than another A/B.

**The open question is whether to keep the block on by default.** It is
+861 tokens for one demonstrated fix and no measured harm. Resolving it needs
more seeds than agents can cheaply supply; the live harness on Opus is ~$3.50
per arm-seed by §4b's rate.

---

## 4d. The benchmark was the bottleneck — and the ceiling was an artifact

**Read `research/benchmark-density.md` before trusting any number in §4b or
§4c.** Full write-up there; the load-bearing facts:

- **The eval set was saturated, not noisy.** Across six runs, 19 questions
  passed every time, 16 failed every time, and **only 2 verdicts ever changed**.
  More seeds could not have helped: 35 of 37 questions were frozen.
- **The Pongify golden was wrong** and is fixed (moved to `expect_absent`).
  The original ceiling went 36/37 → **37/37**.
- **Goldens are now pooled and blind-adjudicated.** 6 runs + the reference were
  pooled TREC-style; the 5,203-card contested band was capped at 30/question
  and **562 cards judged against the question wording**, with assessors shown
  no query, no system identity and no vote count. `expect_present` **106 →
  302**; 74 cards came back `unclear` and are excluded from scoring.
- **The instrument is 2.3× cheaper.** Seeds per arm needed to call the families
  effect: **16 → 7**. Variance went *up* (my 1/√n prediction was wrong); signal
  went up faster.

> ⚠️ **The reference queries are not a ceiling.** Scored against the pooled,
> blind goldens they get **15/37 (40.5%), recall 69.2%** — their 100% was
> earned on 106 cards they were co-designed with. **The families arm already
> beats them (73.2% recall).** Stop quoting 36/37 or 37/37 as an upper bound.

This also re-reads §4c. On the contested band the families gap is **+12.2pp**
(58.8% → 71.1%) against **+1.9pp** on the old consensus-core goldens, and on
`attack-trigger-makes-token` the arms measure control **0.0/20** vs families
**13.3/20** — a question the old benchmark scored 0/6 for *both* arms because
none of its three goldens was a `CopyPermanent` card. The reference query there
says `{"api": "Token"}` and misses Flamerush Rider, Ghired and Furnace-Blessed
Conqueror, which is exactly the failure the mined `[create] Token,
CopyPermanent, Amass` line describes.

**The dense set is not the default**, so every §4b/§4c number stays
reproducible. Pass `--questions benchmark/candidate_questions.dense.json`.

Known limit: pool bias. These goldens are valid for systems that contributed to
the pool; re-pool before trusting them on a materially different system.

---

## 4e. Read this if you are deciding whether the approach transfers

`research/kg-search-assessment.md` is the scientific accounting: what is
winning, what is losing, every intervention with its verdict, and where the
ceiling is. Three facts from it that change decisions:

- **The compiler beats expert hand-authoring.** On blind pooled goldens the
  best config scores 76.0% recall against the hand-vetted reference queries'
  69.2%. Stop treating the reference as an upper bound.
- **The ceiling is the source encoding, not labelling.** 100% of Forge's 18,199
  keyword nodes are paramless — 15% of all nodes, 41.4% of cards, 252 distinct
  keywords. Crew/Delve/Escape carry their entire meaning in the word, so the
  graph is blind to them and no mining of the graph recovers it. That is 25% of
  the residual. **But 76% of those keywords have their definition sitting in
  oracle reminder text**, so the fix is mineable, not authored. Untested, and
  the highest-value untried lever.
- **We have only ever measured recall.** `expect_absent` averages four cards per
  question and pool coverage is 4.7%. Where precision is visible it is 9-16%,
  and result sets run to a mean of 297. Precision ground truth is item 1 on the
  open list.

---

## 5. Open decisions the owner has not made

- **Prompt patches vs mined shapes.** Four hand-written conventions still sit
  in `nl_compiler.DSL_SPEC` alongside the mined `shapes.json` digest. Removing
  them is a *measurement*, not an edit — A/B the seven questions with them out.
  Prediction: the colour and don't-pin-`kind` rules become redundant; the
  static-vs-chain and symmetric-effects rules survive (they are about query
  shape and interpretation, which shape-mining doesn't touch).
- **Should `similar` match card type?** Aven Interrupter returns an
  Enchantment and an Artifact that do the same thing. Right for
  "like Lightning Bolt", wrong for "like Aven Interrupter".
- **`shapes.json` is not wired into `cardguru build`.** Separate command, can
  go stale. It stamps `forge_pin` so a mismatch is *detectable*; nothing checks.
  **`families.json` has the same gap**, same stamp, same nothing checking it.
- **Keep the families digest at 50 lines?** About 1 in 5 surviving lines is a
  structural-English anchor that says nothing (*this*, *one*, *more*). None was
  implicated in a loss and precision was flat, so the cost is prompt tokens
  rather than accuracy — but a tighter cut is a measurement, not an edit.
- **`ChangeZone` and `Sacrifice` still have no family** and cannot get one from
  description text (§4c). Name morphology (`X`/`XAll`) would reach them and is
  derivable from the vocabulary alone. Untried.
- **Research pass?** Whether clause-isolation query repair is novel or
  well-trodden, and whether cardmystic-style projects have solved
  concept→structure in a borrowable way.

---

## 6. Running it

```bash
export CARDGURU_TOKENSCRIPTS=~/forge-src/forge-gui/res/tokenscripts
export ANTHROPIC_API_KEY=...            # rotate first

python -m cardguru serve --verbose      # http://127.0.0.1:8000
python -m cardguru similar "Reprieve"
python -m cardguru shapes --facet CantBeCast
python -m cardguru families             # mined disjunctive api/mode families
python -m cardguru families --anchor destroy
python -m cardguru join                 # Forge<->Scryfall match report
python -m pytest tests/ -q              # 222
python benchmark/run.py                 # 20/20
python benchmark/eval_compile.py --source reference   # 36/37, no API key
python benchmark/eval_compile.py --signals zero       # live NL->DSL accuracy
python benchmark/eval_compile.py --source agent       # agents as the model turn, no API spend
```

`serve --verbose` logs every query, the compiled DSL, the zero-hit diagnosis,
and near-misses on a suspiciously narrow result.
