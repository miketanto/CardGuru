# Adjudication: `cast-from-top-of-library`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> stuff that lets me play cards off the top of my library

**What makes it tricky:** A permission-granting static effect, not a draw or a tutor; Sensei's Divining Top manipulates the top of your library but grants no casting permission, and impulse-draw effects exile first so they are a different structure.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Future Sight, Oracle of Mul Daya, Bolas's Citadel, Vizier of the Menagerie

**Cards already rejected**: Sensei's Divining Top

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | A-Fires of Invention | Enchantment | You can cast spells only during your turn and you can cast no more than two spells each turn.\nYou may cast spells with mana value less than or equal to the number of lands you control without paying their mana costs. |
| 2 | Aluren | Enchantment | Any player may cast creature spells with mana value 3 or less without paying their mana costs and as though they had flash. |
| 3 | Apex Observatory | Artifact | Apex Observatory enters tapped. As it enters, choose a card type shared among two exiled cards used to craft it.\n{T}: The next spell you cast this turn of the chosen type can be cast without paying its mana cost. |
| 4 | As Foretold | Enchantment | At the beginning of your upkeep, put a time counter on As Foretold.\nOnce each turn, you may pay {0} rather than pay the mana cost for a spell you cast with mana value X or less, where X is the number of time counters on As Foretold. |
| 5 | Conspiracy Unraveler | Creature Sphinx Detective | Flying\nYou may collect evidence 10 rather than pay the mana cost for spells that you cast. (To collect evidence 10, exile cards with total mana value 10 or greater from your graveyard.) |
| 6 | Demon of Fate's Design | Enchantment Creature Demon | Flying, trample\nOnce during each of your turns, you may cast an enchantment spell by paying life equal to its mana value rather than paying its mana cost.\n{2}{B}, Sacrifice another enchantment: Demon of Fate's Design gets +X/+0 until end of turn, where X is the sacrificed enchantment's mana value. |
| 7 | Dracogenesis | Enchantment | You may cast Dragon spells without paying their mana costs. |
| 8 | Fires of Invention | Enchantment | You can cast spells only during your turn and you can cast no more than two spells each turn.\nYou may cast spells with mana value less than or equal to the number of lands you control without paying their mana costs. |
| 9 | Flames of Moradin | Sorcery | Destroy up to three target artifacts. Conjure a duplicate of each nontoken artifact destroyed this way into your hand. The duplicates perpetually gain "You may pay {R} rather than pay this spell's mana cost" and "at the beginning of your end step, sacrifice this artifact." |
| 10 | Grenzo, Crooked Jailer | Legendary Creature Goblin Rogue | When Grenzo enters and at the beginning of your upkeep, heist target opponent's library.\nOnce each turn, you may pay {0} rather than pay the mana cost for a spell you cast that you don't own with mana value 3 or less. |
| 11 | Mine Security | Creature Kavu Soldier | Trample\nWhen this creature enters, conjure a card named Flametongue Kavu into the top eight cards of your library at random. It perpetually gains "You may pay {0} rather than pay this spell's mana cost." |
| 12 | Nissa, Worldsoul Speaker | Legendary Creature Elf Druid | Landfall — Whenever a land you control enters, you get {E}{E} (two energy counters).\nYou may pay eight {E} rather than pay the mana cost for permanent spells you cast. |
| 13 | Primal Prayers | Enchantment | When Primal Prayers enters, you get {E}{E} (two energy counters).\nYou may cast creature spells with mana value 3 or less by paying {E} rather than paying their mana costs. If you cast a spell this way, you may cast it as though it had flash. |
| 14 | Sanguine Soothsayer | Creature Bat Cleric | Flying, lifelink\nWhenever Sanguine Soothsayer attacks, conjure a card named Sanguine Bond into the top fifteen cards of your library at random. It perpetually gains "You may pay {0} rather than pay this spell's mana cost" and "When this permanent enters, draw a card." |
| 15 | Sarkhan, Wanderer to Shiv | Legendary Planeswalker Sarkhan | [+1]: Dragon cards in your hand perpetually gain "This spell costs {1} less to cast," and "You may pay {X} rather than pay this spell's mana cost, where X is its mana value."\n[+1]: Conjure a Shivan Dragon card into your hand.\n[-2]: Sarkhan, Wanderer to Shiv deals 3 damage to target creature. |
| 16 | Veko, Death's Doorkeeper | Legendary Creature Spirit Cleric | Extort\n{T}, Sacrifice a non-Spirit creature: Return target creature card from your graveyard to your hand. It perpetually becomes a Spirit, has base power and toughness 1/1, and gains "You may pay {W/B} rather than pay this spell's mana cost." Activate only as a sorcery. |
| 17 | Windriddle Palaces | Plane Belenon | Players play with the top card of their libraries revealed.\nYou may play lands and cast spells from the top of any player's library.\nWhenever chaos ensues, each player mills a card. |
| 18 | World War Hulk | Enchantment Saga | (As this Saga enters and after your draw step, add a lore counter. Sacrifice after III.)\nI — The next red or green creature spell you cast this turn can be cast without paying its mana cost.\nII — Put three +1/+1 counters on target creature you control.\nIII — Choose target creature you control. Un |

## Answer format

Write JSON to `verdicts/cast-from-top-of-library.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
