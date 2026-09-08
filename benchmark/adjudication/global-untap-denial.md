# Adjudication: `global-untap-denial`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> cards that stop permanents from untapping during untap steps

**What makes it tricky:** These modify the untap step itself (a rule-replacement/continuous effect) rather than tapping anything; Icy Manipulator taps permanents and matches on the shared vocabulary.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Winter Orb, Static Orb, Stasis

**Cards already rejected**: Icy Manipulator

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | Edge of Malacol | Plane Belenon | If a creature you control would untap during your untap step, put two +1/+1 counters on it instead.\nWhenever chaos ensues, untap each creature you control. |
| 2 | Freyalise's Winds | Enchantment | Whenever a permanent becomes tapped, put a wind counter on it.\nIf a permanent with a wind counter on it would untap during its controller's untap step, remove all wind counters from it instead. |

## Answer format

Write JSON to `verdicts/global-untap-denial.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
