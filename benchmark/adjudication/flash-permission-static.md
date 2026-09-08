# Adjudication: `flash-permission-static`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> anything that lets me cast my spells at instant speed

**What makes it tricky:** 'As though they had flash' is the key phrase but the question never says flash; Quicken grants the same effect to one spell as a one-shot rather than as a continuous permission.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Vedalken Orrery, Leyline of Anticipation, Teferi, Mage of Zhalfir

**Cards already rejected**: Quicken

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | A-Teferi, Time Raveler | Legendary Planeswalker Teferi | Your opponents can't cast spells during your turn.\n[+1]: Until your next turn, you may cast sorcery spells as though they had flash.\n[-3]: Return up to one target artifact, creature, or enchantment to its owner's hand. Draw a card. |
| 2 | Alchemist's Refuge | Land | {T}: Add {C}.\n{G}{U}, {T}: You may cast spells this turn as though they had flash. |
| 3 | Arlinn, the Pack's Hope | Legendary Planeswalker Arlinn | Daybound (If a player casts no spells during their own turn, it becomes night next turn.)\n[+1]: Until your next turn, you may cast creature spells as though they had flash, and each creature you control enters with an additional +1/+1 counter on it.\n[-3]: Create two 2/2 green Wolf creature tokens. |
| 4 | Borne Upon a Wind | Instant | You may cast spells this turn as though they had flash.\nDraw a card. |
| 5 | Cherished Hatchling | Creature Dinosaur | When Cherished Hatchling dies, you may cast Dinosaur spells this turn as though they had flash, and whenever you cast a Dinosaur spell this turn, it gains "When this creature enters, you may have it fight another target creature." |
| 6 | Complete the Circuit | Instant | Convoke (Your creatures can help cast this spell. Each creature you tap while casting this spell pays for {1} or one mana of that creature's color.)\nYou may cast sorcery spells this turn as though they had flash.\nWhen you next cast an instant or sorcery spell this turn, copy that spell twice. You  |
| 7 | Emergence Zone | Land | {T}: Add {C}.\n{1}, {T}, Sacrifice Emergence Zone: You may cast spells this turn as though they had flash. |
| 8 | Progenitor's Icon | Artifact | As Progenitor's Icon enters, choose a creature type.\n{T}: Add one mana of any color.\n{T}: The next spell of the chosen type you cast this turn can be cast as though it had flash. |
| 9 | Ride the Avalanche | Instant | The next spell you cast this turn can be cast as though it had flash. When you cast your next spell this turn, put X +1/+1 counters on up to one target creature, where X is the mana value of that spell. |
| 10 | Savage Summoning | Instant | This spell can't be countered.\nThe next creature spell you cast this turn can be cast as though it had flash. That spell can't be countered. That creature enters with an additional +1/+1 counter on it. |
| 11 | Scout's Warning | Instant | The next creature card you play this turn can be played as though it had flash.\nDraw a card. |
| 12 | Teferi's Talent | Enchantment Aura | Enchant planeswalker\nEnchanted planeswalker has "[-12]: You get an emblem with 'You may activate loyalty abilities of planeswalkers you control on any player's turn any time you could cast an instant.'"\nWhenever you draw a card, put a loyalty counter on enchanted planeswalker. |
| 13 | Teferi, Temporal Archmage | Legendary Planeswalker Teferi | [+1]: Look at the top two cards of your library. Put one of them into your hand and the other on the bottom of your library.\n[-1]: Untap up to four target permanents.\n[-10]: You get an emblem with "You may activate loyalty abilities of planeswalkers you control on any player's turn any time you co |
| 14 | Teferi, Time Raveler | Legendary Planeswalker Teferi | Each opponent can cast spells only any time they could cast a sorcery.\n[+1]: Until your next turn, you may cast sorcery spells as though they had flash.\n[-3]: Return up to one target artifact, creature, or enchantment to its owner's hand. Draw a card. |
| 15 | Winding Canyons | Land | {T}: Add {C}.\n{2}, {T}: You may cast creature spells this turn as though they had flash. |

## Answer format

Write JSON to `verdicts/flash-permission-static.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
