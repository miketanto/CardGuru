# Cycle 6 — two ordering bugs, and a taxonomy of what actually goes wrong

**Static modes went 71.45/81.94 → 76.21/80.83 on holdout, exact-set agreement
65.31% → 68.21%. Neither fix added a production. Both were the right logic
running in the wrong order.**

## Bug 1: the ability-word stripper was eating Saga chapters

`ABILITY_WORD_RE` removes CR 207.2c ability words and flavour names — "Landfall
— ", "Heavy Power Hammer — ". A Saga chapter marker is also short text before an
em-dash:

```
I — Exile target creature an opponent controls.
```

The stripper ran first, removed `I — `, and `CHAPTER_RE` then had nothing to
match. Every chapter line fell through to `S`/`Continuous`. Ajani Fells the
Godsire emitted three static abilities where Forge has one `K:Chapter` node.

This is not a new defect — it is the `K-1, S+3` mismatch shape M0 documented at
124 faces and attributed to Sagas. The attribution was right; the cause was an
ordering bug one line away, not a missing production.

Fixing it needed `ROMAN` tightened first: it was `(?:I{1,3}|IV|V?I{0,3})`, and
`V?I{0,3}` matches the **empty string**, so the pattern could not be used in the
negative lookahead the fix requires. With a real numeral alternation, the
stripper now declines to touch chapter markers.

## Bug 2: the alternative-cost short-circuit ran before classification

The emitter short-circuited any line matching `ALT_COST_RE` straight to
`S:Mode$ AlternativeCost`, *before* calling `classify()`. So it fired on
triggered abilities and keyword lines too — 182 false `AlternativeCost` nodes on
dev.

Moved to after classification and applied only to lines `classify()` already
called static. Same regex, same intent, correct position.

## Results

| holdout | before | after |
|---|---|---|
| static modes — precision | 71.45 | **76.21** |
| static modes — exact set | 65.31% | **68.21%** |
| replacement events — exact set | 77.58% | **78.11%** |
| trigger modes — exact set | 79.49% | **79.57%** |
| M0 ability-kind bag | 90.29% | **90.31%** |

The regression suite moved with it — mean recall of Forge hits:

| slice | before | after |
|---|---|---|
| v5 (10 q) | 82.8% | **85.1%** |
| v6 (4 q) | 80.9% | **91.0%** |

Pass counts held at 7/10 and 3/4. That is what a regression suite is for: the
pass/fail verdicts were already spent as a measurement, but the bulk-recall
numbers still detect movement.

## The defect taxonomy, after six cycles

Worth writing down, because each class needed a *different* kind of check to
find, and the aggregate metrics found none of them on their own:

| class | example | what found it |
|---|---|---|
| **Over-broad production** | `Drawn` firing 721× vs Forge's 145 | per-archetype Jaccard on a slice |
| **Missing vocabulary** | `tapXType`, `ExileFromGrave` cost atoms | a slice question returning zero |
| **Authored from the wrong artefact** | `AttackersDeclared` = "attackers are declared", a phrase no card contains | the production audit (cycle 5) |
| **Wrong assumption about Forge** | `SubCounter` means loyalty — it means *any* counter removal | following a partially-fixed number |
| **Ordering** | ability-word stripper eating chapter markers; alt-cost short-circuit before `classify()` | tracing one card end-to-end |
| **Duplicated logic** | emitter re-deriving ability kind instead of calling `classify()` | reading the code, not any metric |

The last two are the interesting ones. **Neither shows up in any aggregate
score** — they present as diffuse precision loss spread across a catch-all
bucket (`Continuous`), which looks like "the grammar is just imprecise here"
rather than "there is a bug". Both were only found by picking one card and
tracing what happened to it line by line.

The corollary: the metrics are good at telling you *whether* something is wrong
and bad at telling you *what*. Every real fix in the last three cycles came from
a targeted diagnostic — the audit, the triage, a single-card trace — not from
the numbers themselves.

## Status

| layer | precision | recall | exact set |
|---|---|---|---|
| `{T}` in activation cost | 99.75 | 99.85 | — |
| counter cost atoms | 96.70 | 89.60 | — |
| sacrifice cost atoms | 94.08 | 78.25 | 78.27% |
| trigger modes | 93.81 | 81.44 | 79.57% |
| replacement events | 89.82 | 80.39 | 78.11% |
| static modes | 76.21 | 80.83 | 68.21% |

Static modes remain the weakest layer, and `Continuous` remains the catch-all
that absorbs everything unclassified — 830 false positives on dev, 585 of them
on faces where Forge has no static ability at all. The remaining causes are
Forge modelling statics as keywords (landwalk-like abilities, conspiracy
deck-construction text) and replacement templating the `R` detector misses.

Verified: 92 tests pass, 20/20 benchmark goldens, M1 83.35/76.9 unchanged.
