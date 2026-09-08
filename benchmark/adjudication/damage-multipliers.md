# Adjudication: `damage-multipliers`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> anything that makes damage hit for double or triple

**What makes it tricky:** Multipliers ('deals double that damage instead') and flat adders (Torbran's +2) are the same idea to a player but structurally distinct replacement effects, and symmetric vs one-sided matters too.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Furnace of Rath, Dictate of the Twin Gods, Fiery Emancipation

**Cards already rejected**: Torbran, Thane of Red Fell

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | Absorbing Man and Titania | Legendary Creature Human Villain | Double all damage that creature sources you control would deal. |
| 2 | Angel of Suffering | Creature Nightmare Angel | Flying\nIf damage would be dealt to you, prevent that damage and mill twice that many cards. |
| 3 | City on Fire | Enchantment | Convoke (Your creatures can help cast this spell. Each creature you tap while casting this spell pays for {1} or one mana of that creature's color.)\nIf a source you control would deal damage to a permanent or player, it deals triple that damage instead. |
| 4 | Collective Inferno | Enchantment | Convoke (Your creatures can help cast this spell. Each creature you tap while casting this spell pays for {1} or one mana of that creature's color.)\nAs this enchantment enters, choose a creature type.\nDouble all damage that sources you control of the chosen type would deal. |
| 5 | Mjölnir, Hammer of Thor | Legendary Artifact Equipment | When Mjölnir enters, it deals 4 damage to up to one target creature.\nDouble all damage equipped creature would deal.\nEquip worthy {1} (A creature is worthy if it's a legendary non-Villain that's red and/or white.)\n{2}{R}, Discard this card: It deals 2 damage to each creature. |
| 6 | Raphael, the Muscle | Legendary Creature Mutant Ninja Turtle | Double all damage that creatures you control with counters on them would deal.\nWhen Raphael enters, create a Mutagen token.\nPartner—Character select (You can have two commanders if both have this ability.) |
| 7 | Sawhorn Nemesis | Creature Dinosaur | As Sawhorn Nemesis enters, choose a player.\nIf a source would deal damage to the chosen player or a permanent they control, it deals double the damage instead. |
| 8 | Wolverine, Best There Is | Legendary Creature Mutant Berserker Hero | Unrivaled Lethality — Double all damage Wolverine would deal.\nAt the beginning of each end step, if Wolverine dealt damage to another creature this turn, put a +1/+1 counter on him.\n{1}{G}: Regenerate Wolverine. (The next time he would be destroyed this turn, instead tap him, remove him from comba |

## Answer format

Write JSON to `verdicts/damage-multipliers.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
