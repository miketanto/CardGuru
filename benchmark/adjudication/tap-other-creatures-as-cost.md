# Adjudication: `tap-other-creatures-as-cost`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> cards where you tap OTHER untapped creatures you control to pay for something

**What makes it tricky:** Crew N, Convoke, and spelled-out 'Tap an untapped creature you control' are the same structural cost wearing three different names; Cryptolith Rite grants a tap ability rather than using tapping as a cost.

**Author's notes:** Heart of Kiran also has a counter-removal alternative; still a crew card.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Springleaf Drum, Smuggler's Copter, Heart of Kiran

**Cards already rejected**: Cryptolith Rite

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | Angelic Favor | Instant | If you control a Plains, you may tap an untapped creature you control rather than pay this spell's mana cost.\nCast this spell only during combat.\nCreate a 4/4 white Angel creature token with flying. Exile it at the beginning of the next end step. |
| 2 | Aziza, Mage Tower Captain | Legendary Creature Djinn Sorcerer | Whenever you cast an instant or sorcery spell, you may tap three untapped creatures you control. If you do, copy that spell. You may choose new targets for the copy. |
| 3 | Burn at the Stake | Sorcery | As an additional cost to cast this spell, tap any number of untapped creatures you control.\nBurn at the Stake deals damage to any target equal to three times the number of creatures tapped this way. |
| 4 | Caparocti Sunborn | Legendary Creature Human Soldier | Whenever Caparocti Sunborn attacks, you may tap two untapped artifacts and/or creatures you control. If you do, discover 3. (Exile cards from the top of your library until you exile a nonland card with mana value 3 or less. Cast it without paying its mana cost or put it into your hand. Put the rest  |
| 5 | Explosive Singularity | Sorcery | As an additional cost to cast this spell, you may tap any number of untapped creatures you control. This spell costs {1} less to cast for each creature tapped this way.\nExplosive Singularity deals 10 damage to any target. |
| 6 | Fear of Exposure | Enchantment Creature Nightmare | As an additional cost to cast this spell, tap two untapped creatures and/or lands you control.\nTrample |
| 7 | Gaze of Justice | Sorcery | As an additional cost to cast this spell, tap three untapped white creatures you control.\nExile target creature.\nFlashback {5}{W} (You may cast this card from your graveyard for its flashback cost and any additional costs. Then exile it.) |
| 8 | Gravelgill Scoundrel | Creature Merfolk Rogue | Vigilance\nWhenever this creature attacks, you may tap another untapped creature you control. If you do, this creature can't be blocked this turn. |
| 9 | Guardian of the Great Door | Creature Angel | As an additional cost to cast this spell, tap four untapped artifacts, creatures, and/or lands you control.\nFlying |
| 10 | Hollow Warrior | Artifact Creature Golem Warrior | Hollow Warrior can't attack or block unless you tap an untapped creature you control not declared as an attacking or blocking creature this combat. (This cost is paid as attackers or blockers are declared.) |
| 11 | Kitt Kanto, Mayhem Diva | Legendary Creature Cat Bard Druid | When Kitt Kanto enters, create a 1/1 green and white Citizen creature token.\nAt the beginning of combat on each player's turn, you may tap two untapped creatures you control. When you do, target creature that player controls gets +2/+2 and gains trample until end of turn. Goad that creature. |
| 12 | Lashknife | Enchantment Aura | If you control a Plains, you may tap an untapped creature you control rather than pay this spell's mana cost.\nEnchant creature\nEnchanted creature has first strike. |
| 13 | Mossbridge Troll | Creature Troll | If Mossbridge Troll would be destroyed, regenerate it.\nTap any number of untapped creatures you control other than Mossbridge Troll with total power 10 or greater: Mossbridge Troll gets +20/+20 until end of turn. |
| 14 | Orim's Cure | Instant | If you control a Plains, you may tap an untapped creature you control rather than pay this spell's mana cost.\nPrevent the next 4 damage that would be dealt to any target this turn. |
| 15 | Raff, Weatherlight Stalwart | Legendary Creature Human Wizard | Whenever you cast an instant or sorcery spell, you may tap two untapped creatures you control. If you do, draw a card.\n{3}{W}{W}: Creatures you control get +1/+1 and gain vigilance until end of turn. |
| 16 | Ramosian Rally | Instant | If you control a Plains, you may tap an untapped creature you control rather than pay this spell's mana cost.\nCreatures you control get +1/+1 until end of turn. |
| 17 | Redcap Raiders | Creature Goblin Warrior | Whenever Redcap Raiders attacks, you may tap an untapped non-Human creature you control. If you do, Redcap Raiders gets +1/+1 and gains trample until end of turn. |
| 18 | Sephara, Sky's Blade | Legendary Creature Angel | You may pay {W} and tap four untapped creatures you control with flying rather than pay this spell's mana cost.\nFlying, lifelink\nOther creatures you control with flying have indestructible. (Damage and effects that say "destroy" don't destroy them.) |
| 19 | Shared Discovery | Sorcery | As an additional cost to cast this spell, tap four untapped creatures you control.\nDraw three cards. |
| 20 | Sivvi's Valor | Instant | If you control a Plains, you may tap an untapped creature you control rather than pay this spell's mana cost.\nAll damage that would be dealt to target creature this turn is dealt to you instead. |
| 21 | Swallow Whole | Sorcery | As an additional cost to cast this spell, tap an untapped creature you control.\nExile target tapped creature. Put a +1/+1 counter on the creature tapped to pay this spell's additional cost. |
| 22 | Thousand Moons Smithy | Legendary Artifact | When Thousand Moons Smithy enters, create a white Gnome Soldier artifact creature token with "This token's power and toughness are each equal to the number of artifacts and/or creatures you control."\nAt the beginning of your first main phase, you may tap five untapped artifacts and/or creatures you |
| 23 | Tidal Terror | Creature Octopus | Whenever Tidal Terror attacks, you may tap two other untapped creatures you control. If you do, Tidal Terror can't be blocked this turn.\nIslandcycling {2} ({2}, Discard this card: Search your library for an Island card, reveal it, put it into your hand, then shuffle.) |
| 24 | Warlord's Elite | Creature Human Soldier | As an additional cost to cast this spell, tap two untapped artifacts, creatures, and/or lands you control. |

## Answer format

Write JSON to `verdicts/tap-other-creatures-as-cost.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.
