# v2 re-baseline — the shipped prompt, all 40 intents

Discharges R4 for both changes shipped after C0 (full parameter vocabulary from the C3
ablation; `hook`/`role` operators added to the validator and advertised). 200
compilations, all 40 intents × 5 rungs, sample 0.

## Like-for-like

Comparing the 40-intent run against the 10-intent baseline would be meaningless — a
different set, likely a different difficulty. Restricted to the **same 10 intents, same
k=1**, so the only variable is the prompt:

| run | PC | PC_correct | agreement@wit | foil |
|---|---|---|---|---|
| C0 baseline | 0.474 | 0.488 | 0.900 | 0.000 |
| **v2 shipped** | **0.745** | **0.713** | **1.000** | 0.025 |
| | **+0.271** | **+0.225** | **+0.100** | +0.025 |

**PC +27 points, and agreement@witness is now perfect** on those ten. This is far more
than the C3 ablation alone predicted (+0.119 at k=2), so the two changes compound rather
than overlap — full vocabulary and the facet operators fix different things.

Full 40-intent set, for the record and **not** comparable to the above: PC 0.716,
PC_correct 0.771, agreement@witness 0.963, 36 headline intents.

## H11 passes outright — the first stratum to do so

I33 ("best commander for a budget deck") and I34 ("cards banned in Modern") returned
`query: null` on **5/5 rungs each**, and nothing else nulled anywhere in the 200
compilations. Consistent, correct refusal on out-of-scope questions.

**Metric bug this exposed:** the harness counts those as `compile_fail`, giving a 5%
failure rate that is entirely correct behaviour. True failure rate is **0/190**. The
harness needs to distinguish "declined an out-of-scope question" from "failed to
compile" before that number is quoted anywhere.

## The foil metric caught a regression I introduced

Foil rate rose 0.000 → 0.025 like-for-like, and reached 0.11 across the full set. Two
intents leaked on every rung. They have opposite causes and both matter:

**I20 — a real bug, and my own fix caused it.** Every rung compiled
`{"any": [{"hook": "reanimator"}, {node: graveyard→battlefield}]}`. The node branch is
exactly right. The hook branch is not:

| query | faces | includes Raise Dead (graveyard→**hand**) |
|---|---|---|
| precise node predicate | 82 | no |
| `hook: reanimator` | **1,227** | **yes** |

The hook is **15× broader** than the question, and it drags in artifact/enchantment
recursion, monarch enchantments and graveyard-to-hand effects. The hooks were built as
*deck-archetype* facets — "does this commander support a reanimator build?" — where that
breadth is correct. They were never search predicates. By advertising them to the
compiler under names that sound precise, I handed it a tool that looks surgical and is
not.

*Fix shipped:* `build_system_prompt` now annotates every facet with its measured face
count (`reanimator (1227)`) and states plainly that facets are broad archetype labels,
to be used only for archetype-level questions. Counts are mined by
`eval/consistency/build_facet_selectivity.py` into `research/data/facet_selectivity.json`
— one pass over the pool, since one scan per facet times out.

**I07 — my authoring error, not a compiler fault.** Foil was Windfall, which discards
then draws; the intent is "one ability that draws and makes you discard." Windfall
genuinely satisfies it, so a 1.00 foil rate was correct behaviour scored as failure.
Foil changed to Divination, which draws with no discard half.

The remaining leaks are smaller and look like genuine precision misses worth watching:
I25 (0.60 — `Lord of Extinction` counts *all* graveyards, an H03 scope trap riding on an
H08 intent), I24, I31, I40 (0.20 each).

## Reading

The headline gain is real and large, but three things temper it:

1. **k=1.** No `SC` from this run, and single-sample PC carries roughly ±0.035 of noise
   by the C0 spread. The +0.271 clears that comfortably; the +0.025 foil delta does not.
2. **Precision moved the wrong way while consistency moved the right way.** PC and
   agreement@witness both improved while the foil rate rose. That is the pattern you get
   from *broader* queries — more agreement because there is more overlap, more foils
   because there is less discrimination. Facet annotation is the corrective; it needs its
   own measurement before the gain is banked.
3. **The 40-intent PC of 0.716 is not a baseline** for anything yet. The set is not
   frozen, and 30 of its ladders were authored after the numbers above were produced.

## Next

- Re-run with the facet annotation in place; confirm the I20 leak closes without giving
  back the PC gain.
- Fix the `compile_fail` / intentional-refusal conflation in the harness.
- Add k=2 for an `SC` figure on the full set, then freeze v1 under R6.
