# Adjudication: `etb-creature-pings-opponents`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> permanents that ping each opponent whenever another creature enters under my control

**What makes it tricky:** The trigger condition (creature ETB) and the effect (damage to opponents) are two separate clauses that plain text search cannot bind together; Goblin Bombardment deals the same damage but off a sacrifice cost, not an ETB trigger.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Impact Tremors, Purphoros, God of the Forge, Warstorm Surge

**Cards already rejected**: Goblin Bombardment

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | Aether Flash | Enchantment | Whenever a creature enters, Aether Flash deals 2 damage to it. |
| 2 | Ayara, First of Locthwain | Legendary Creature Elf Noble | Whenever Ayara, First of Locthwain or another black creature you control enters, each opponent loses 1 life and you gain 1 life.\n{T}, Sacrifice another black creature: Draw a card. |
| 3 | Corpse Knight | Creature Zombie Knight | Whenever another creature you control enters, each opponent loses 1 life. |
| 4 | Flame-Kin War Scout | Creature Elemental Scout | When another creature enters, sacrifice Flame-Kin War Scout. If you do, Flame-Kin War Scout deals 4 damage to that creature. |
| 5 | Flametongue Kavu Avatar | Vanguard | Hand +0, life -6\nWhenever a nontoken creature you control enters, that creature deals X damage to target creature, where X is a number chosen at random from 0 to 4. |
| 6 | Flayer of the Hatebound | Creature Devil | Undying (When this creature dies, if it had no +1/+1 counters on it, return it to the battlefield under its owner's control with a +1/+1 counter on it.)\nWhenever Flayer of the Hatebound or another creature enters from your graveyard, that creature deals damage equal to its power to any target. |
| 7 | Halana, Kessig Ranger | Legendary Creature Human Archer Ranger | Reach\nWhenever another creature you control enters, you may pay {2}. When you do, that creature deals damage equal to its power to target creature.\nPartner (You can have two commanders if both have partner.) |
| 8 | Immersturm | Plane Valla | Whenever a creature enters, that creature's controller may have it deal damage equal to its power to any target of their choice.\nWhenever chaos ensues, exile target creature, then return it to the battlefield under its owner's control. |
| 9 | Marauding Raptor | Creature Dinosaur | Creature spells you cast cost {1} less to cast.\nWhenever another creature you control enters, Marauding Raptor deals 2 damage to it. If a Dinosaur is dealt damage this way, Marauding Raptor gets +2/+0 until end of turn. |
| 10 | Mogg Bombers | Creature Goblin | When another creature enters, sacrifice Mogg Bombers and it deals 3 damage to target player or planeswalker. |
| 11 | Pandemonium | Enchantment | Whenever a creature enters, that creature's controller may have it deal damage equal to its power to any target of their choice. |
| 12 | Rampaging Ferocidon | Creature Dinosaur | Menace\nPlayers can't gain life.\nWhenever another creature enters, Rampaging Ferocidon deals 1 damage to that creature's controller. |
| 13 | Wispdrinker Vampire | Creature Vampire Rogue | Flying\nWhenever another creature you control with power 2 or less enters, each opponent loses 1 life and you gain 1 life.\n{5}{W}{B}: Creatures you control with power 2 or less gain deathtouch and lifelink until end of turn. |

## Answer format

Write JSON to `verdicts/etb-creature-pings-opponents.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
