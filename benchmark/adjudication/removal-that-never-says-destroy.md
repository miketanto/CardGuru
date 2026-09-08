# Adjudication: `removal-that-never-says-destroy`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> removal spells that get rid of a creature without ever saying destroy or exile

**What makes it tricky:** This is a negative constraint over semantic function - the system has to know that bounce, tuck, sacrifice-edicts and -X/-X all achieve removal, then exclude the two most common words for it.

**Author's notes:** Flagged suspect: 'gets rid of' is a functional category, not a structural one. I expect the system either can't express the negation or can't express the functional grouping. Informative either way. [2026-08-07] Pongify moved expect_present -> expect_absent: its Forge node is SP$ Destroy and its oracle text opens 'Destroy target creature', so it cannot satisfy 'without ever saying destroy'. Flagged in compiled_questions.json judgment_calls since the harness was built; the golden was simply wrong.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Diabolic Edict

**Cards already rejected**: Doom Blade, Pongify, Swords to Plowshares

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | A Premonition of Your Demise | Scheme | When you set this scheme in motion, reveal the top two cards of your library and put them into your hand. When you reveal one or more nonland cards this way, this scheme deals damage equal to their total mana value to any target. |
| 2 | Apprentice Sorcerer | Creature Human Wizard Sorcerer | {T}: Apprentice Sorcerer deals 1 damage to any target. Activate only during your turn, before attackers are declared. |
| 3 | Batterskull | Artifact Equipment | Living weapon (When this Equipment enters, create a 0/0 black Phyrexian Germ creature token, then attach this to it.)\nEquipped creature gets +4/+4 and has vigilance and lifelink.\n{3}: Return Batterskull to its owner's hand.\nEquip {5} |
| 4 | Brawl | Instant | Until end of turn, all creatures gain "{T}: This creature deals damage equal to its power to target creature." |
| 5 | Chandra's Defeat | Instant | Chandra's Defeat deals 5 damage to target red creature or red planeswalker. If that permanent is a Chandra planeswalker, you may discard a card. If you do, draw a card. |
| 6 | Consuming Tide | Sorcery | Each player chooses a nonland permanent they control. Return all nonland permanents not chosen this way to their owners' hands. Then you draw a card for each opponent who has more cards in their hand than you. |
| 7 | Dead Before Sunrise | Instant | Until end of turn, outlaw creatures you control get +1/+0 and gain "{T}: This creature deals damage equal to its power to target creature." (Assassins, Mercenaries, Pirates, Rogues, and Warlocks are outlaws.) |
| 8 | Dormant Volcano | Land | Dormant Volcano enters tapped.\nWhen Dormant Volcano enters, sacrifice it unless you return an untapped Mountain you control to its owner's hand.\n{T}: Add {C}{R}. |
| 9 | Energy Flux | Enchantment | All artifacts have "At the beginning of your upkeep, sacrifice this artifact unless you pay {2}." |
| 10 | Fiery Impulse | Instant | Fiery Impulse deals 2 damage to target creature.\nSpell mastery — If there are two or more instant and/or sorcery cards in your graveyard, Fiery Impulse deals 3 damage instead. |
| 11 | Forked Bolt | Sorcery | Forked Bolt deals 2 damage divided as you choose among one or two targets. |
| 12 | Goblin Fireleaper | Creature Goblin Warrior | {1}{R}: Goblin Fireleaper gets +1/+0 until end of turn.\nWhen Goblin Fireleaper dies, it deals damage equal to its power to target creature an opponent controls. |
| 13 | Heavy Ballista | Creature Human Soldier | {T}: Heavy Ballista deals 2 damage to target attacking or blocking creature. |
| 14 | Inferno Fist | Enchantment Aura | Enchant creature you control\nEnchanted creature gets +2/+0.\n{R}, Sacrifice Inferno Fist: Inferno Fist deals 2 damage to any target. |
| 15 | Kazuul's Fury | Instant | As an additional cost to cast this spell, sacrifice a creature.\nKazuul's Fury deals damage equal to the sacrificed creature's power to any target. |
| 16 | Lich's Mirror | Artifact | If you would lose the game, instead shuffle your hand, your graveyard, and all permanents you own into your library, then draw seven cards and your life total becomes 20. |
| 17 | Mana Vortex | Enchantment | When you cast this spell, counter it unless you sacrifice a land.\nAt the beginning of each player's upkeep, that player sacrifices a land.\nWhen there are no lands on the battlefield, sacrifice Mana Vortex. |
| 18 | Mordant Dragon | Creature Dragon | Flying\n{1}{R}: Mordant Dragon gets +1/+0 until end of turn.\nWhenever Mordant Dragon deals combat damage to a player, you may have it deal that much damage to target creature that player controls. |
| 19 | Ominous Cemetery | Land | {T}: Add {C}.\n{5}, {T}, Exile Ominous Cemetery: Target creature's owner shuffles it into their library. |
| 20 | Pigment Storm | Sorcery | Pigment Storm deals 5 damage to target creature. Excess damage is dealt to that creature's controller instead. |
| 21 | Quarry Colossus | Creature Giant | When Quarry Colossus enters, put target creature into its owner's library just beneath the top X cards of that library, where X is the number of Plains you control. |
| 22 | Retrieval Agent | Creature Human Soldier | {2}: Retrieval Agent gets +1/-1 until end of turn. |
| 23 | Savage Twister | Sorcery | Savage Twister deals X damage to each creature. |
| 24 | Shrapnel Blast | Instant | As an additional cost to cast this spell, sacrifice an artifact.\nShrapnel Blast deals 5 damage to any target. |
| 25 | Soul Shatter | Instant | Each opponent sacrifices a creature or planeswalker with the highest mana value among creatures and planeswalkers they control. |
| 26 | Stormbind | Enchantment | {2}, Discard a card at random: Stormbind deals 2 damage to any target. |
| 27 | Temporal Adept | Creature Human Wizard | {U}{U}{U}, {T}: Return target permanent to its owner's hand. |
| 28 | Timothar, Baron of Bats | Legendary Creature Vampire Noble | Ward—Discard a card.\nWhenever another nontoken Vampire you control dies, you may pay {1} and exile it. If you do, create a 1/1 black Bat creature token with flying. It gains "When this creature deals combat damage to a player, sacrifice it and return the exiled card to the battlefield tapped." |
| 29 | Urborg Emissary | Creature Human Wizard | Kicker {1}{U} (You may pay an additional {1}{U} as you cast this spell.)\nWhen Urborg Emissary enters, if it was kicked, return target permanent to its owner's hand. |
| 30 | Warzone Duplicator | Artifact Creature Construct | Prototype {3}{U} — 3/3\nWhen Warzone Duplicator enters, return target creature an opponent controls with power less than Warzone Duplicator's power to its owner's hand. If that creature wasn't a token, conjure a duplicate of it into your hand. It perpetually gains "You may spend mana as though it we |

## Answer format

Write JSON to `verdicts/removal-that-never-says-destroy.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
