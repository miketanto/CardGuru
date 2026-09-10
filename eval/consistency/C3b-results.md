# Arm D results — the precision fix worked, and it tripped its own revert rule

Scored against `C3b-prediction.md`, which was committed before the run. 200
compilations, 40 intents × 5 rungs, sample 0, same harness and same set as v2 — only
the prompt differs.

## Predictions, scored

| # | prediction | v2 | v3 | Δ | verdict |
|---|---|---|---|---|---|
| 1 | **foil rate ≤ 0.05** (primary) | 0.110 | **0.014** | −0.096 | **PASS** |
| 2 | **`H03` improves** (R5 target, named in advance) | 0.620 | **0.659** | +0.039 | **PASS** |
| 3 | PC moves little, may fall | 0.716 | 0.674 | −0.042 | PASS |
| — | PC_correct | 0.771 | 0.744 | −0.027 | — |
| ⚠ | **REVERT IF agreement@witness < 0.963** | 0.963 | **0.912** | −0.051 | **FIRED** |

Also: `invalid` rate **0.000** — the harness's new decline/failure split confirms the
5% "failures" were entirely I33/I34 correctly refusing out-of-scope questions.

All three positive predictions landed, including the R5 target named before the run
rather than after. **And the revert condition fired.** Both are true; the second decides.

## Precision did exactly what it was designed to do

Every foil leak flagged in v2 closed or shrank:

| intent | hazard | v2 | v3 |
|---|---|---|---|
| I07 | H00 | 1.00 | **0.00** |
| I20 | H04 | 1.00 | **0.00** |
| I25 | H08 | 0.60 | 0.20 |
| I31 | H10 | 0.20 | **0.00** |
| I40 | H02 | 0.20 | **0.00** |

I20 is the one that matters: it was the regression the *previous* round introduced, where
`hook: reanimator` (1,227 faces) rode along on a precise 82-face question and returned
Raise Dead every time. It is now clean.

## Why it still has to be reverted

Five intents lost witnesses. The worst is decisive:

**I37 — "cards that make each player draw an additional card", witness Howling Mine.**
agreement 0.80 → **0.00**, while PC *rose* to 0.948. Perfectly consistent and completely
wrong — the exact pathology R2 exists to catch.

Howling Mine's script is `Phase` → `Draw` with **`Defined$ TriggeredPlayer`**. The
"each player" lives in the *trigger* (it fires on every player's draw step), not in the
Draw node. My value list taught the compiler to pin exact `Defined` values — and
`Defined`'s most frequent values are `Self`, `You`, `Remembered`, `Targeted`,
`TriggeredPlayer`, which are **contextual**: they resolve at runtime and carry no scope
information at all. Anchoring on them is not tightening, it is matching the wrong thing.

That is a defect in the intervention, not noise, and it explains all five losses:
I02/I20 (H04 zone), I07, I22 (H06 timing), I37 (H03 scope) are all cases where the
structure carries the meaning and the value does not.

## What shipped

**Reverted:** the `PARAM VALUES` block is now behind `param_values=False`. Default
prompt 43,952 → 29,951 chars.

**Kept**, because neither can produce a witness miss on its own:
- The `true` rule — "constrain the value, don't just assert the key exists." This is the
  caution that drove the precision win.
- A new **contextual-value caution** written from the I37 diagnosis: scope often lives in
  the trigger; `Self`/`You`/`Remembered`/`Targeted`/`TriggeredPlayer` say nothing about
  how many players are affected; pin values only for genuinely absolute ones like
  `Player.Opponent`.

**Kept as data:** `research/data/param_values.json` and its miner. The values are right;
what is missing is a contextual-vs-absolute annotation on them.

## Arm E, specified

Re-enable the block with each value tagged `absolute` or `contextual`, and list only the
absolute ones for scope-bearing parameters. Same protocol, same set.

Pre-registered now, before any run:
- **foil rate stays ≤ 0.05** — the win must survive, not be traded back.
- **agreement@witness returns to ≥ 0.963** — this is the whole point of the correction.
- `H03` holds its +0.039 or better.
- Revert again if agreement stays below 0.963, and treat value-advertising as a dead end
  rather than iterating a third time.

## Honest note on attribution

Arm D bundled two changes — the value block and the `true` rule — so I cannot attribute
the foil win or the agreement loss between them from this run alone. I reverted the block
and kept the rule on a mechanistic argument (a caution cannot cause a miss; an exact
anchor can), not on measurement. Arm E should carry the rule alone in its baseline so the
attribution stops being an argument and becomes a number.
