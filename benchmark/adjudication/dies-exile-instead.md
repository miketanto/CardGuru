# Adjudication: `dies-exile-instead`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> permanents that replace things going to the graveyard with exile

**What makes it tricky:** Grafdigger's Cage is a prohibition, not a replacement, and Bojuka Bog is a one-shot exile - the structural distinction between 'instead' and 'can't' and 'do it once' is invisible to keyword matching.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Rest in Peace, Leyline of the Void, Anafenza, the Foremost

**Cards already rejected**: Grafdigger's Cage, Bojuka Bog

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | Eelectrocute | Instant | Eelectrocute deals 2 damage to any target.\nYou may cast Eelectrocute from your graveyard as long as you've rolled a 6 this turn. If you cast Eelectrocute this way and it would be put into your graveyard, exile it instead. |
| 2 | Glimpse the Cosmos | Sorcery | Look at the top three cards of your library. Put one of them into your hand and the rest on the bottom of your library in any order.\nAs long as you control a Giant, you may cast Glimpse the Cosmos from your graveyard by paying {U} rather than paying its mana cost. If you cast Glimpse the Cosmos thi |
| 3 | Haakon, Stromgald Scourge Avatar | Vanguard | Hand +0, life -3\nPay 1 life: You may cast target creature card in your graveyard this turn.\nWhenever you cast a creature spell from your graveyard, it becomes a black Zombie Knight.\nIf a Zombie Knight would be put into your graveyard from the battlefield, exile it instead. |
| 4 | The Doctor's Tomb | Plane Trenzalore | If a creature would die, instead exile it and that creature's controller loses 2 life.\nWhenever chaos ensues, redistribute any number of players' life totals. (Each of those players gets one life total back.) |

## Answer format

Write JSON to `verdicts/dies-exile-instead.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
