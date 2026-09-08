# Adjudication: `untap-on-other-players-turns`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> what lets me untap my stuff on other people's turns so I can use tap abilities more than once a round?

**What makes it tricky:** The stated goal (reuse tap abilities) is downstream of the actual text (untap permanents during another player's untap step or end step), so the search has to reason about why an effect is wanted, not just what it says.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Seedborn Muse, Wilderness Reclamation

**Cards already rejected**: Unwind

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | Assault Suit | Artifact Equipment | Equipped creature gets +2/+2, has haste, can't attack you or planeswalkers you control, and can't be sacrificed.\nAt the beginning of each opponent's upkeep, you may have that player gain control of equipped creature until end of turn. If you do, untap it.\nEquip {3} |
| 2 | White Plume Adventurer | Creature Orc Cleric | When White Plume Adventurer enters battlefield, you take the initiative.\nAt the beginning of each opponent's upkeep, untap a creature you control. If you've completed a dungeon, untap all creatures you control instead. |

## Answer format

Write JSON to `verdicts/untap-on-other-players-turns.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
