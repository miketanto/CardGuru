# C0 findings — instrumentation pass

Phase C0 of `plan/nl-dsl-consistency.md`. Environment rebuilt from scratch this run:
Forge `7ba1a393`, **34,611 faces** (research pin was `670429bf`/34,519 — +92 faces of drift),
ontology `research/data/ontology.json` (191 APIs, 137 trigger modes, 1,206 param keys).

Status: harness built and validated; intent set corrected against the real index; **the
scoring run itself is blocked on an LLM compile stage** (see §6).

---

## 1. Bug — the validator rejects two operators the evaluator implements

`cardguru/querydsl.py` evaluates nine operators. `cardguru/validate.py` accepts seven:

```
querydsl.evaluate  : all any card chain hook keyword node not role
validate.QUERY_OPS : all any card chain     keyword node not
```

`hook` and `role` are missing from the gate. Any compiled query using them is rejected with
`unknown operator 'role'` — confirmed by running one:

```
I18 reference query {"role": "card_draw:engine"}  ->  INVALID: $: unknown operator 'role'
```

`DSL_SPEC` in `nl_compiler.py` also never advertises them, so the two are consistent with
each other — the NL path was simply never told the semantic-facet layer exists. But
`docs/query-dsl.md` and the `querydsl` docstring both document `hook` and `role` as part of
the DSL.

**Net effect: the entire semantic-facet layer — 48 hooks, 4 roles — is unreachable from the
`ask` path.** Hand-written queries can use it; compiled ones cannot.

This matters beyond a missing feature. `S9` (closed-label operators) was designed as the
plan's **control stratum**: NL→facet is classification over a small closed label set, so it
should be the most consistent row in the set, and if it *isn't*, the problem is upstream in
question understanding rather than in DSL expressiveness. That control cannot be measured
until this is fixed. **I18 and I19 are marked unscoreable in the intent set.**

Fix is small (add the two operators to `QUERY_OPS`, validate their arguments against
`recommend.HOOKS` / `deck.ROLES`, advertise them in `DSL_SPEC`). Not applied here — C0 is a
measurement phase, and changing the compiler's vocabulary before the baseline exists would
violate R4.

---

## 2. The H02 thesis, quantified: the two encodings are near-disjoint

The `H02` hazard ("one concept, two Forge encodings") was argued from four known failures.
Measured directly, on the flagship q1 family — *"cards that deal damage to each opponent"*:

| encoding | faces |
|---|---|
| `DamageAll` + `ValidPlayers ~ Opponent` | 60 |
| `DealDamage` + `Defined ~ Opponent` | 200 |
| intersection | **1** |
| union | 259 |
| **Jaccard** | **0.0039** |

Both queries validate. Both are defensible readings of the same English sentence. They share
**one face out of 259**.

This is stronger than the original diagnosis in `research/agent-compiler-poc.md`, which
called the compiled q1 query "defensible (14 real matches of the targeted variant)". An
idiom-alternation coin-flip does not *degrade* the result set — it **replaces it wholesale**.
Note also that both intended witnesses (Sizzle, Fiery Confluence) live in the `DealDamage`
set, not the `DamageAll` set the spec line points at.

**Consequence for the plan:** this is the strongest available evidence for C3 (mined idiom
lexicon), and it sharpens §7 gap 13 of the outline — `H02` carrying three rows is too thin
for a stratum with this much dynamic range.

---

## 3. I40 is a *three*-encoding alternation, not two

Probing the damage-prevention family the drift probe sits in:

| encoding | faces |
|---|---|
| api `PreventDamage` | 115 |
| api `Fog` | 34 |
| `ReplacementEffects` SVar chain (`~Prevent`) | 162 |
| api `PreventDamageAll` | 0 |

~311 faces across three disjoint encodings; **any single-encoding compilation caps at ~52%
of the concept.**

This also caught an authoring error: the drafted witness, Circle of Protection: Red, does
**not** use the `PreventDamage` api at all — it is `ChooseSource` → `Effect` carrying a
`RPreventNextFromSource` replacement SVar. The reference query missed its own witness.

Corrected in the intent set: witnesses now deliberately **span two encodings** —
Conservator (`PreventDamage` / `Defined$ You`) and Circle of Protection: Red (SVar
replacement) — so a single-encoding compilation cannot score full marks. Foil changed to
Test of Faith (creature-only prevention), which must not be returned for "dealt to you".

---

## 4. My result-set size predictions were systematically low

Reference queries written and executed for 8 intents. **5 of 8 D-tags were wrong, all in
the same direction — under-estimates:**

| intent | declared | observed | hits |
|---|---|---|---|
| I04 | D2 | D2 ✓ | 187 |
| I08 | D1 | **D2** | 299 |
| I10 | D1 | **D2** | 40 |
| I11 | D2 | D2 ✓ | 259 |
| I12 | D1 | **D2** | 36 |
| I22 | D2 | **D3** | 2,364 |
| I36 | D1 | D1 ✓ | 0 (as designed — false premise) |
| I40 | D1 | **D2** | 115 |

Corrected in the intent set, with observed hit counts and the pin recorded. This matters
because D-regime is what makes a Jaccard number interpretable (outline §2, axis D) — a
mis-tagged regime silently mis-reads every score in it. It also means the set is thinner at
`D1` than designed, and `D3` picked up a row it wasn't supposed to have.

I36 returning exactly 0 is the one prediction that landed: "sorceries with flash" is
correctly empty.

---

## 5. Harness built and validated

`eval/consistency.py`, stdlib-only. The LLM stage is pluggable (`ApiBackend`,
`RecordedBackend` replaying a JSONL, `StubBackend`), so who performs compilation is not the
harness's concern — this is what makes the repo's established agent-as-compiler route
scoreable, and what let the harness be validated with no credentials.

Smoke test, on a synthetic recorded log where three rungs of I11 pick the `DamageAll`
encoding and two pick `DealDamage` (both valid — the exact H02 failure mode):

```
PC             0.402
PC_correct     1.0     <- R2: read with agreement below
agreement@wit  0.467
SC             0.867
foil rate      0.0
```

Read that `PC_correct` / `agreement@witness` pair carefully, because it is the whole reason
R2 exists: **`PC_correct` = 1.0 says "perfectly consistent"; `agreement@witness` = 0.467 says
"and wrong more than half the time."** Only the rungs that picked the witness-bearing
encoding are in the `PC_correct` subgroup, so it measures a consistent-but-minority reading
and scores it perfect. Reported alone it would be actively misleading. The guard is
load-bearing, not decorative.

`SC` (0.867) > `PC` (0.402) also reproduces the *shape* of the recorded prediction —
sampling variance below paraphrase variance — though on synthetic data, so it is a
harness check, not evidence about the compiler.

---

## 6. Blocked: the compile stage

`ANTHROPIC_API_KEY` is unset and the `anthropic` package is not installed in this
environment, so the 600-compilation scoring run cannot execute. Everything upstream of it is
done.

Two ways forward, both supported by the harness as built:

1. **API** — set `ANTHROPIC_API_KEY`, `pip install anthropic`, run with `--backend api`.
   Cost is 600 calls against a cached system prefix, single-digit dollars.
2. **Agent-as-compiler** — the route this repo already used for both prior compiler rounds
   (`research/agent-compiler-poc.md`): run the LLM stage in-session against the identical
   contract, log to JSONL, score with `--backend recorded`. No credentials.

## 7. State of the intent set

- All **52** referenced witness/foil cards resolve against the built index (0 unresolved).
  This was the stated freeze blocker and it is cleared.
- 5 D-tags corrected, 1 witness/foil pair corrected, 2 intents marked unscoreable.
- 10 of 40 intents carry full five-rung ladders; the other 30 are still one-liners.
- **Still not frozen.** Freezing before the remaining 30 ladders are authored would trigger
  a v2 re-hash under R6 as soon as they land.
