# FRA synergy graph — generated report (`evaluate.py`, do not edit)

Cards: 280. Directed matches: 32608 ({'resource': 2029, 'state': 29877, 'cost': 702}).

## 1. Schemes

| scheme | undirected edges | Louvain modularity | seed stability (NMI, 20 seeds) | communities |
|---|---|---|---|---|
| uniform | 18821 | 0.134 | 0.972 | [109, 103, 68] |
| tight | 18821 | 0.148 | 0.728 | [108, 101, 71] |
| rarity | 18821 | 0.227 | 0.689 | [82, 79, 67, 52] |
| full | 18821 | 0.285 | 0.896 | [78, 59, 56, 37, 36, 14] |
| full_knn | 2366 | 0.505 | 0.918 | [61, 51, 40, 29, 28, 25, 17, 16, 13] |
| mutual_knn | 434 | 0.674 | 0.957 | [28, 26, 24, 21, 21, 18, 17, 15, 14, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |
| norm_knn | 2037 | 0.605 | 0.932 | [43, 41, 39, 38, 25, 25, 21, 20, 16, 12] |

Cross-scheme agreement (NMI): uniform~tight 0.717, uniform~rarity 0.488, uniform~full 0.317, uniform~full_knn 0.229, uniform~mutual_knn 0.218, uniform~norm_knn 0.237, tight~rarity 0.51, tight~full 0.38, tight~full_knn 0.278, tight~mutual_knn 0.229, tight~norm_knn 0.281, rarity~full 0.493, rarity~full_knn 0.387, rarity~mutual_knn 0.323, rarity~norm_knn 0.457, full~full_knn 0.682, full~mutual_knn 0.452, full~norm_knn 0.614, full_knn~mutual_knn 0.533, full_knn~norm_knn 0.756, mutual_knn~norm_knn 0.562

## 2a. Communities under `full_knn`

**C0** (61 cards, colours BRG) — primitives: reenter 59%, enter 17%, mana (resource) 8%, cast 7%, tograve 4%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Return to the Light Realms, Aerid Konstrari, Hungering Puppetbeast, Gallia, Tragic Host, Tenured Tethermage

**C1** (51 cards, colours UGB) — primitives: activate_loyalty 51%, enter 21%, counter+:LOYALTY 20%, cost_mod (cost) 3%, counter+:* 2%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Paradox, Way of the Mind Sculptor, Kiora of Salt and Sand, Jace, Reality Sculptor, Tam, the Possibility, Avatar of Burgeoning Echoes

**C2** (40 cards, colours RUG) — primitives: prepare 44%, cast 30%, cost_mod (cost) 14%, tograve 5%, enter 4%
  core: Codie, Ravenous Codex, Infinite Coursework, Geist of Saint Thalia, Variable Chaser, Pyre Rhymer, Pompous Battlemage, Theorix Metamage, Void Extrapolator

**C3** (29 cards, colours URB) — primitives: draw 74%, discard 18%, tograve 4%, enter 3%, mana (resource) 2%
  core: Tinybones, Pocket Nuisance, The Theorist, Jace Beleren, Lyra, Tolarian Archangel, Murmuring Volume, Hallway Heckler, Solitary Cell, Proft, Sinister Mastermind, Gideon's Memorial

**C4** (28 cards, colours WGB) — primitives: lifegain 94%, enter 2%, counter+:LOYALTY 2%, discard 1%, tograve 1%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Bloombrute, Lyra, Archangel of Dawn, Unflinching Hortimancer, Way of the Mentor, Enlightened Confidant

**C5** (25 cards, colours WRG) — primitives: counter+:P1P1 57%, cast_target_own 37%, cast 3%, enter 2%, mana (resource) 0%
  core: Vigorbloom Vanguard, Ruric Thar, Biomagus, Yoshimaru, Beloved Companion, Danitha, Sword of Hope, Gallia, the Merrymaker, Guiding Hydra, Predictive Preparations, Tam's Resistance

**C6** (17 cards, colours BGW) — primitives: die 96%, enter 2%, mana (resource) 1%, tograve 1%
  core: Edgar, Ancient Bloodlord, Eye of Jace, Loot, the Anomaly, Gardenize, Massacre Girl, Most Wanted, Darklight Phoenix, Bloodline Recollector, Budding Insurgent

**C7** (16 cards, colours UWR) — primitives: surveil 93%, tograve 3%, enter 2%, reenter 1%, mana (resource) 0%
  core: Prudent Fateseer, Proctor of Potential, Diviner of Victory, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Desperate Futurescribe

**C8** (13 cards, colours GRB) — primitives: enter 98%, mana (resource) 1%, tograve 0%
  core: Shipwreck Marsh, Koth, the Geomancer, Rockfall Vale, Overgrown Farmland, Haunted Ridge, Primal Witchstalker, Deserted Beach, Hexhaven Invigorator

## 2a2. Communities under `mutual_knn`

**C0** (28 cards, colours GBR) — primitives: enter 72%, mana (resource) 14%, tograve 6%, reenter 3%, attack 2%
  core: Hexhaven Invigorator, Shipwreck Marsh, Koth, the Geomancer, Rockfall Vale, Overgrown Farmland, Deserted Beach, Haunted Ridge, Primal Witchstalker

**C1** (26 cards, colours GBW) — primitives: counter+:P1P1 53%, reenter 29%, enter 11%, tograve 6%, mana (resource) 1%
  core: Yoshimaru, Beloved Companion, Guiding Hydra, Gallia, the Merrymaker, Liliana the Repentant, Vinelasher Adept, Generous Revival, Vigorbloom Vanguard, Rewrite Regrets

**C2** (24 cards, colours RUG) — primitives: prepare 53%, enter 21%, cast 19%, mana (resource) 7%, tograve 1%
  core: Codie, Ravenous Codex, Infinite Coursework, Heartwood Crafter, Woodwork Prodigy, Konstrari Improviser, Craterclaw Colossus, Pyre Rhymer, Pompous Battlemage

**C3** (21 cards, colours UGR) — primitives: activate_loyalty 44%, counter+:LOYALTY 24%, enter 15%, cost_mod (cost) 10%, counter+:* 3%
  core: Inspired Tethermage, Way of the Paradox, Tam, the Possibility, Kiora of Salt and Sand, Way of the Mind Sculptor, Jace, Reality Sculptor, Ajani Unrelenting, Way of the Mentor

**C4** (21 cards, colours RUB) — primitives: draw 55%, discard 25%, die 8%, tograve 6%, enter 3%
  core: Tinybones, Pocket Nuisance, Solitary Cell, Murmuring Volume, Sureshot Sower, Lyra, Tolarian Archangel, The Theorist, Jace Beleren, Hallway Heckler, Proft, Sinister Mastermind

**C5** (18 cards, colours GWB) — primitives: cast_target_own 82%, cost_mod (cost) 10%, cast 6%, enter 1%
  core: Ruric Thar, Biomagus, Danitha, Sword of Hope, Predictive Preparations, Tam's Resistance, Geist of Saint Thalia, Emergency Phytomedic, Blossom-Blessed Angel, Last Gasp

**C6** (17 cards, colours WGR) — primitives: lifegain 81%, discard 8%, enter 5%, draw 3%, mana (resource) 2%
  core: Liliana the Faultless, Titanbones, Towering Heart, Kwia Vigorbloom, Bloombrute, Ajani Resolute, Greenhouse Propagator, Germinate Recruits, Unflinching Hortimancer

**C7** (15 cards, colours UW) — primitives: surveil 93%, tograve 4%, enter 2%, reenter 1%, mana (resource) 0%
  core: Proctor of Potential, Surveillance Phantasm, Prudent Fateseer, Denzilore Fatehold, Diviner of Victory, Yuriko, Hope from the Shadows, Saheeli, Consul of Oversight, Proft, Consulting Detective

**C8** (14 cards, colours BGU) — primitives: die 95%, enter 4%, mana (resource) 1%, tograve 1%
  core: Edgar, Ancient Bloodlord, Loot, the Anomaly, Eye of Jace, Way of the Necromancer, Gardenize, Massacre Girl, Most Wanted, Aerid Konstrari, Apex Witchstalker

**C9** (1 cards, colours W) — primitives: 
  core: Campus Crier

**C10** (1 cards, colours W) — primitives: 
  core: Kindred Judgment

**C11** (1 cards, colours W) — primitives: 
  core: Loyal Tutor

**C12** (1 cards, colours W) — primitives: 
  core: Memory Trap

**C13** (1 cards, colours W) — primitives: 
  core: Refute Destiny

**C14** (1 cards, colours W) — primitives: 
  core: Repurposed Enforcer

**C15** (1 cards, colours W) — primitives: 
  core: Shatterwing Pegasus

**C16** (1 cards, colours W) — primitives: 
  core: Surgical Precision

**C17** (1 cards, colours U) — primitives: 
  core: Countersculpt

**C18** (1 cards, colours U) — primitives: 
  core: Cryotheory Adept

**C19** (1 cards, colours U) — primitives: 
  core: Divining Duelist

**C20** (1 cards, colours U) — primitives: 
  core: Icy Reception

**C21** (1 cards, colours U) — primitives: 
  core: Perfected Theory

**C22** (1 cards, colours U) — primitives: 
  core: Precise Redaction

**C23** (1 cards, colours U) — primitives: 
  core: Protege's Awakening

**C24** (1 cards, colours U) — primitives: 
  core: Sphinx's Approach

**C25** (1 cards, colours U) — primitives: 
  core: Unsummon

**C26** (1 cards, colours B) — primitives: 
  core: Cast Away Doubt

**C27** (1 cards, colours B) — primitives: 
  core: Extended Absence

**C28** (1 cards, colours B) — primitives: 
  core: Extrapolate the Impossible

**C29** (1 cards, colours B) — primitives: 
  core: Lich's Relic

**C30** (1 cards, colours B) — primitives: 
  core: Overwrite the Multiverse

**C31** (1 cards, colours B) — primitives: 
  core: Rampart Hunter

**C32** (1 cards, colours B) — primitives: 
  core: Rank Rat

**C33** (1 cards, colours B) — primitives: 
  core: Screeching Soulbreaker

**C34** (1 cards, colours B) — primitives: 
  core: Silence the Echo

**C35** (1 cards, colours B) — primitives: 
  core: Solve for Disappointment

**C36** (1 cards, colours B) — primitives: 
  core: Terminal Criticism

**C37** (1 cards, colours B) — primitives: 
  core: Theoretical Necromancer

**C38** (1 cards, colours B) — primitives: 
  core: Vraska's Final Mercy

**C39** (1 cards, colours R) — primitives: 
  core: Artifist Acumen

**C40** (1 cards, colours R) — primitives: 
  core: Curse-Marred Demon

**C41** (1 cards, colours R) — primitives: 
  core: Eardrum Rattler

**C42** (1 cards, colours R) — primitives: 
  core: Essence Burn

**C43** (1 cards, colours R) — primitives: 
  core: Face Yourself

**C44** (1 cards, colours R) — primitives: 
  core: Fulminous Forte

**C45** (1 cards, colours R) — primitives: 
  core: Heartstring Puller

**C46** (1 cards, colours R) — primitives: 
  core: Master of Barbs

**C47** (1 cards, colours R) — primitives: 
  core: No Admittance

**C48** (1 cards, colours R) — primitives: 
  core: Skilled Battlecarver

**C49** (1 cards, colours R) — primitives: 
  core: Stingcaster Mage

**C50** (1 cards, colours R) — primitives: 
  core: Violent Echoes

**C51** (1 cards, colours G) — primitives: 
  core: Bestial Incursion

**C52** (1 cards, colours G) — primitives: 
  core: Compel Brutality

**C53** (1 cards, colours G) — primitives: 
  core: Flourishing Grapple

**C54** (1 cards, colours G) — primitives: 
  core: Hunter's Axe

**C55** (1 cards, colours G) — primitives: 
  core: Puppet Crafting

**C56** (1 cards, colours G) — primitives: 
  core: Tarmogoyf

**C57** (1 cards, colours BW) — primitives: 
  core: Blessed Ghoul

**C58** (1 cards, colours RW) — primitives: 
  core: Charge the Sanctum

**C59** (1 cards, colours RU) — primitives: 
  core: Clash of Elements

**C60** (1 cards, colours GU) — primitives: 
  core: Entrust the Spark

**C61** (1 cards, colours UW) — primitives: 
  core: Fatehold Charm

**C62** (1 cards, colours RU) — primitives: 
  core: Frostbite Pyromental

**C63** (1 cards, colours BU) — primitives: 
  core: Paradox Shaper

**C64** (1 cards, colours GW) — primitives: 
  core: Solarium Sentry

**C65** (1 cards, colours BR) — primitives: 
  core: Stingerquill Charm

**C66** (1 cards, colours BR) — primitives: 
  core: Stingerquill Voxmancer

**C67** (1 cards, colours BR) — primitives: 
  core: Stinging Vitriol

**C68** (1 cards, colours BU) — primitives: 
  core: Theorix Charm

**C69** (1 cards, colours BW) — primitives: 
  core: Twisted Fates

**C70** (1 cards, colours BU) — primitives: 
  core: Uldaros Theorix

**C71** (1 cards, colours BW) — primitives: 
  core: Vindictive Triumph

**C72** (1 cards, colours ) — primitives: 
  core: Afterthought Sentry

**C73** (1 cards, colours ) — primitives: 
  core: Archive Arbiter

**C74** (1 cards, colours ) — primitives: 
  core: Medic's Kitesail

**C75** (1 cards, colours ) — primitives: 
  core: Dedicated Commons

**C76** (1 cards, colours ) — primitives: 
  core: Fatehold Annex

**C77** (1 cards, colours ) — primitives: 
  core: Formidable Commons

**C78** (1 cards, colours ) — primitives: 
  core: Innovative Commons

**C79** (1 cards, colours ) — primitives: 
  core: Konstrari Annex

**C80** (1 cards, colours ) — primitives: 
  core: Meticulous Commons

**C81** (1 cards, colours ) — primitives: 
  core: Stingerquill Annex

**C82** (1 cards, colours ) — primitives: 
  core: Theorist's Sanctum

**C83** (1 cards, colours ) — primitives: 
  core: Theorix Annex

**C84** (1 cards, colours ) — primitives: 
  core: Transformative Commons

**C85** (1 cards, colours ) — primitives: 
  core: Vigorbloom Annex

**C86** (1 cards, colours W) — primitives: 
  core: Rescue Girl, First Responder

**C87** (1 cards, colours W) — primitives: 
  core: Thalia, the Survivor

**C88** (1 cards, colours W) — primitives: 
  core: Tomik, Orzhov Lawmage

**C89** (1 cards, colours W) — primitives: 
  core: Yuriko, Blade of the Mighty

**C90** (1 cards, colours U) — primitives: 
  core: Fblthp, Impossibly Lost

**C91** (1 cards, colours U) — primitives: 
  core: Hapatra, the Desert Frost

**C92** (1 cards, colours U) — primitives: 
  core: Samut, Tyrant of Naktamun

**C93** (1 cards, colours U) — primitives: 
  core: Tetsuko Umezawa, Fugitive

**C94** (1 cards, colours U) — primitives: 
  core: Yargle, Goliath of Otaria

**C95** (1 cards, colours B) — primitives: 
  core: Danitha, Spear of Agony

**C96** (1 cards, colours B) — primitives: 
  core: Gideon the Oathless

**C97** (1 cards, colours B) — primitives: 
  core: Mabel, Bitter Recluse

**C98** (1 cards, colours B) — primitives: 
  core: Yargle, Glutton of Urborg

**C99** (1 cards, colours R) — primitives: 
  core: Arni, Renowned Champion

**C100** (1 cards, colours R) — primitives: 
  core: Jiang Yanggu, Alone

**C101** (1 cards, colours R) — primitives: 
  core: Marwyn, the Clearcutter

**C102** (1 cards, colours R) — primitives: 
  core: Samut, Hazoret's Champion

**C103** (1 cards, colours G) — primitives: 
  core: Jiang Yanggu, Never Alone

**C104** (1 cards, colours G) — primitives: 
  core: Ruric Thar, Magecrusher

## 2a3. Communities under `norm_knn`

**C0** (43 cards, colours BRU) — primitives: cast 35%, prepare 31%, cost_mod (cost) 17%, tograve 8%, die 7%
  core: Geist of Saint Thalia, Codie, Ravenous Codex, Infinite Coursework, Pyre Rhymer, Bloodline Recollector, Tomik, Izzet Sparkmage, Tetsuko Umezawa, Pursuer, Grim Repriser

**C1** (41 cards, colours UGR) — primitives: activate_loyalty 49%, enter 25%, counter+:LOYALTY 18%, cost_mod (cost) 4%, counter+:* 2%
  core: Inspired Tethermage, Kiora of Salt and Sand, Way of the Mind Sculptor, Way of the Paradox, Tam, the Possibility, Ajani Unrelenting, Avatar of Burgeoning Echoes, Way of the Cryomancer

**C2** (39 cards, colours RGW) — primitives: enter 51%, mana (resource) 27%, cast 15%, attack 6%, enter (cost) 1%
  core: Traxos, Scourge Eternal, Hungering Puppetbeast, Aerid Konstrari, Ingris Stingerquill, Craterclaw Colossus, Tenured Tethermage, Pia, Determined Rebuilder, Konstrari Improviser

**C3** (38 cards, colours URB) — primitives: draw 59%, discard 33%, tograve 3%, enter 3%, mana (resource) 1%
  core: Tinybones, Pocket Nuisance, Lyra, Tolarian Archangel, Titanbones, Towering Heart, Proft, Sinister Mastermind, Sureshot Sower, The Theorist, Jace Beleren, Murmuring Volume, Solitary Cell

**C4** (25 cards, colours WGB) — primitives: lifegain 95%, counter+:LOYALTY 2%, enter 2%, tograve 1%, mana (resource) 0%
  core: Lyra, Archangel of Dawn, Unflinching Hortimancer, Bloombrute, Kwia Vigorbloom, Germinate Recruits, Ajani Resolute, Way of the Mentor, Enlightened Confidant

**C5** (25 cards, colours WGB) — primitives: counter+:P1P1 51%, cast_target_own 43%, cast 3%, enter 2%, mana (resource) 0%
  core: Danitha, Sword of Hope, Ruric Thar, Biomagus, Yoshimaru, Beloved Companion, Guiding Hydra, Gallia, the Merrymaker, Vigorbloom Vanguard, Predictive Preparations, Last Gasp

**C6** (21 cards, colours BUR) — primitives: reenter 87%, tograve 9%, enter 5%
  core: Generous Revival, Rewrite Regrets, Liliana the Repentant, Gallia, Tragic Host, Return to the Light Realms, Rank Rat, Stingcaster Mage, Mabel, Bitter Recluse

**C7** (20 cards, colours GBR) — primitives: enter 96%, mana (resource) 3%, tograve 0%
  core: Deserted Beach, Shipwreck Marsh, Rockfall Vale, Overgrown Farmland, Haunted Ridge, Roiling Canopy, Hexhaven Invigorator, Verdant Kraken

**C8** (16 cards, colours UWR) — primitives: surveil 94%, tograve 3%, enter 2%, reenter 1%, mana (resource) 0%
  core: Diviner of Victory, Prudent Fateseer, Surveillance Phantasm, Saheeli, Consul of Oversight, Proft, Consulting Detective, Denzilore Fatehold, Proctor of Potential, Refute Destiny

**C9** (12 cards, colours BGU) — primitives: die 96%, enter 3%, tograve 1%, mana (resource) 0%
  core: Edgar, Ancient Bloodlord, Loot, the Anomaly, Massacre Girl, Most Wanted, Gardenize, Living Library, Way of the Necromancer, Eye of Jace, Budding Insurgent

## 2b. Communities under `full`

**C0** (78 cards, colours GRB) — primitives: enter 34%, reenter 29%, mana (resource) 13%, counter+:P1P1 9%, cast 7%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Yoshimaru, Beloved Companion, Tenured Tethermage, Return to the Light Realms, Vraska, the Cutting Glare, Gallia, Tragic Host

**C1** (59 cards, colours RUB) — primitives: cast 41%, prepare 16%, tograve 13%, cost_mod (cost) 10%, cast_target_own 9%
  core: Geist of Saint Thalia, Codie, Ravenous Codex, Infinite Coursework, Ruric Thar, Biomagus, Pyre Rhymer, Pompous Battlemage, Theorix Metamage, Void Extrapolator

**C2** (56 cards, colours UGW) — primitives: enter 54%, activate_loyalty 28%, counter+:LOYALTY 13%, cost_mod (cost) 2%, counter+:* 1%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Paradox, Way of the Mind Sculptor, Kiora of Salt and Sand, Jace, Reality Sculptor, Avatar of Burgeoning Echoes, Way of the Necromancer

**C3** (37 cards, colours WGB) — primitives: lifegain 78%, die 11%, enter 4%, tograve 2%, counter+:P1P1 2%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Enlightened Confidant, Way of the Mentor, Unflinching Hortimancer, Bloombrute, Lyra, Archangel of Dawn

**C4** (36 cards, colours URB) — primitives: draw 71%, discard 13%, tograve 8%, enter 4%, die 1%
  core: Tinybones, Pocket Nuisance, The Theorist, Jace Beleren, Lyra, Tolarian Archangel, Murmuring Volume, Hallway Heckler, Solitary Cell, Proft, Sinister Mastermind, Gideon's Memorial

**C5** (14 cards, colours UW) — primitives: surveil 93%, tograve 4%, enter 1%, reenter 1%, cast 0%
  core: Prudent Fateseer, Diviner of Victory, Proctor of Potential, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Yuriko, Hope from the Shadows

## 2c. Communities under `rarity`

**C0** (82 cards, colours UBW) — primitives: tograve 44%, cast 23%, surveil 14%, enter 5%, prepare 4%
  core: Proctor of Potential, Chandra, Chill of Compliance, Eye of Jace, Enlightened Confidant, Prudent Fateseer, Diviner of Victory, Yuriko, Hope from the Shadows, Codie, Ravenous Codex

**C1** (79 cards, colours GRW) — primitives: mana (resource) 39%, enter 29%, counter+:P1P1 10%, lifegain 7%, cast 7%
  core: Kwia Vigorbloom, Yoshimaru, Beloved Companion, Aerid Konstrari, Hungering Puppetbeast, Vigorbloom Vanguard, Tenured Tethermage, Edgar, Ancient Bloodlord, Ingris Stingerquill

**C2** (67 cards, colours UGW) — primitives: enter 53%, activate_loyalty 23%, counter+:LOYALTY 15%, counter+:* 3%, mana (resource) 2%
  core: Ajani Unrelenting, Inspired Tethermage, Way of the Paradox, Kiora of Salt and Sand, Way of the Mind Sculptor, Tam, the Possibility, Way of the Necromancer, Way of the Mentor

**C3** (52 cards, colours BUR) — primitives: tograve 35%, draw 29%, reenter 16%, discard 9%, enter 8%
  core: Murmuring Volume, Gideon's Memorial, Liliana the Repentant, Solitary Cell, Tinybones, Pocket Nuisance, Proft, Sinister Mastermind, Grim Repriser, Hallway Heckler

## 2x. Colour coherence (post-hoc; colour is not a state-edge input)

Colour enters the graph only through the resource-flow colour factor. In a draft set archetypes are colour pairs, so communities that align with colour identity are recovering real structure. **Added after the first results, not pre-registered.** NMI(community, colour identity) vs 200 label shuffles.

| scheme | NMI with colour | shuffled mean | max shuffled |
|---|---|---|---|
| uniform | 0.100 | 0.039 | 0.059 |
| tight | 0.092 | 0.039 | 0.070 |
| rarity | 0.132 | 0.055 | 0.074 |
| full | 0.188 | 0.077 | 0.111 |
| full_knn | 0.205 | 0.107 | 0.136 |
| mutual_knn | 0.402 | 0.355 | 0.382 |
| norm_knn | 0.224 | 0.117 | 0.154 |

## 2y. Draft-archetype agreement and hub damping (`SYNERGY-GRAPH.md` §12)

Gold cards: 57 (colours exactly one of the 10 pairs). Signpost agreement = pairs whose signpost shares a cluster with the plurality of the pair's gold cards. Hub slots = kept edges between a Prepare card and Codie / Infinite Coursework. Prepare spread = most Prepare cards in one cluster.

| scheme | signpost agreement /10 | gold NMI | hub slots | Prepare spread /21 | isolated | UB / BR / RG gold plurality |
|---|---|---|---|---|---|---|
| uniform | 8 | 0.344 | 42 | 15 | 0 | C1 7/7 / C1 6/7 / C0 7/7 |
| tight | 8 | 0.295 | 42 | 16 | 0 | C1 6/7 / C1 6/7 / C0 6/7 |
| rarity | 7 | 0.425 | 42 | 14 | 0 | C0 5/7 / C0 4/7 / C1 6/7 |
| full | 8 | 0.553 | 42 | 11 | 0 | C1 4/7 / C1 4/7 / C0 4/7 |
| full_knn | 5 | 0.499 | 42 | 12 | 0 | C2 3/7 / C2 4/7 / C2 3/7 |
| mutual_knn | 4 | 0.620 | 20 | 7 | 96 | C0 2/7 / C4 2/7 / C2 4/7 |
| norm_knn | 6 | 0.579 | 40 | 8 | 0 | C0 3/7 / C0 5/7 / C2 5/7 |

## 3. Validation (plan's three known-good checks)

### V1 surveil enablers ↔ graveyard-count payoffs

13 surveil emitters; 12 graveyard-size payoffs (Count$ValidGraveyard, Threshold, graveyard triggers).

| scheme | same-community rate | shuffled-label baseline | p (one-sided, 2000 perms) | direct edges S→P / pairs |
|---|---|---|---|---|
| uniform | 0.922 | 0.343 | 0.0005 | 154/154 |
| tight | 0.766 | 0.342 | 0.0005 | 154/154 |
| rarity | 0.688 | 0.255 | 0.0005 | 154/154 |
| full | 0.065 | 0.194 | 1.0000 | 154/154 |
| full_knn | 0.065 | 0.136 | 0.9950 | 154/154 |
| mutual_knn | 0.065 | 0.048 | 0.2549 | 154/154 |
| norm_knn | 0.065 | 0.111 | 0.9790 | 154/154 |

Payoffs: Cruel Calculations, Dark Matter Manipulator, Eye of Jace, Hapatra, the Desert Fang, Null Summoner, Proft, Sinister Mastermind, Recursive Recruitment, Tarmogoyf, Theorix Metamage, Void Extrapolator, Winter, Tormented Loner, Yuriko, Hope from the Shadows

### V2 loyalty adders → 'whenever you put loyalty counters on a planeswalker'

`Inspired Tethermage`: 43/44 loyalty emitters link to it by `counter+:LOYALTY`. Their rank among its 132 neighbours under `full`: median 22, best 1. Same community under full: 38/43.

Top-10 neighbours (full): Way of the Paradox 0.493; Way of the Mind Sculptor 0.481; Jace, Reality Sculptor 0.455; Ajani Unrelenting 0.407; Way of the Pyromancer 0.403; Jace's Machinations 0.400; Sanctum Lurker 0.395; Avatar of Burgeoning Echoes 0.395; Way of the Healer 0.395; Way of the Cryomancer 0.395

Pre-registration check 4 (Empower → PW card SubCounter fuel edges): **0** (must be 0).

### V3 Chandra, Torch of Defiance → top end / X spells (resource flow)

52 resource-flow consumers. Chandra's keywords: none. Consumers sharing a keyword: 0. Resource edges whose reason cites a keyword: 0 (pre-reg 2: must be 0).

| consumer | MV / cost | reason | w(full) |
|---|---|---|---|
| Kindred Judgment | 5 W W | ManaCost 5 W W (MV 7) | 0.096 |
| Craterclaw Colossus | 4 R R R | ManaCost 4 R R R (MV 7) | 0.096 |
| Face Yourself | 5 R R | ManaCost 5 R R (MV 7) | 0.096 |
| Verdant Kraken | 4 G G G | ManaCost 4 G G G (MV 7) | 0.096 |
| Craftwork Crusher | 3 R R G G | ManaCost 3 R R G G (MV 7) | 0.096 |
| Ruric Thar, Magecrusher | 5 G G | ManaCost 5 G G (MV 7) | 0.096 |
| Emrakul, the Exigent Doom | 10 | ManaCost 10 (MV 10) | 0.094 |
| Return to the Light Realms | 7 W W | ManaCost 7 W W (MV 9) | 0.094 |
| Omnipresence | 5 G G G | ManaCost 5 G G G (MV 8) | 0.094 |
| Ghalta the Immovable | 8 W | ManaCost 8 W (MV 9) | 0.094 |
| Ghalta the Unstoppable | 8 G | ManaCost 8 G (MV 9) | 0.094 |
| Ajani's Anguish | X R | SVar:X:Count$xPaid | 0.051 |

Among Chandra's 279 neighbours under `full`: best consumer of any kind ranks 1 (that one is linked by other edges too); 48 consumers have resource flow as their *strongest* link, the best of which ranks 12. Mana is a common primitive (24 emitting cards, 244 consuming cards), so rarity weighting ranks these edges low; they are present but not what the combined weight surfaces first.

Chandra top-10 neighbours overall (full): Tam, the Possibility 0.663; Ajani Unrelenting 0.312; Way of the Mentor 0.302; Way of the Necromancer 0.302; Inspired Tethermage 0.289; Way of the Mind Sculptor 0.264; Way of the Paradox 0.264; Kiora of Salt and Sand 0.248; Teyo, Lightshield Expert 0.156; Teyo, Diamondblade Mage 0.156

## 4. Held-out check: Forge's hand-authored DeckHas / DeckHints

Forge authors tag some cards `DeckHints:Ability$Graveyard` ("this card wants graveyard enablers") and others `DeckHas:Ability$Graveyard`. Neither is an input. For each hinted card, take its top-10 neighbours and ask what fraction carry the matching `DeckHas` (for `Type$X` hints: have type X). Baseline = the label's rate over all other cards. Wilson 95% intervals. Small n — these are sanity rows, not results.

| scheme | hinted (card,label) pairs | hits in top-10 | rate [95% CI] | baseline rate | lift |
|---|---|---|---|---|---|
| uniform | 43 | 89/430 | 0.207 [0.171, 0.248] | 0.037 | 5.58× |
| tight | 43 | 89/430 | 0.207 [0.171, 0.248] | 0.037 | 5.58× |
| rarity | 43 | 94/430 | 0.219 [0.182, 0.260] | 0.037 | 5.89× |
| full | 43 | 75/430 | 0.174 [0.141, 0.213] | 0.037 | 4.70× |
| full_knn | 43 | 75/430 | 0.174 [0.141, 0.213] | 0.037 | 4.70× |
| mutual_knn | 22 | 53/227 | 0.233 [0.183, 0.293] | 0.037 | 6.29× |
| norm_knn | 43 | 65/430 | 0.151 [0.120, 0.188] | 0.037 | 4.08× |

## 5. Sparse edges — scarce enablers and lonely emissions

Intrinsic emissions (being a creature, being cast) and resource edges are excluded here.

### 5a. Scarce enablers — listeners that ≤ 3 cards in the set can satisfy

Grouped by (primitive, the set of cards that can satisfy it). These are the cards a whole group of listeners depends on.

| primitive | the only enablers | # listener cards | listeners (first 6) |
|---|---|---|---|
| cost_mod | Geist of Saint Thalia | 92 | Academic Ascent, Ajani's Anguish, Artifist Acumen, Awaken the Inferno, Bestial Incursion, Blazing Crescendo |
| counter+:* | Tam, the Possibility | 1 | Gardenize |
| prepare | Codie, Ravenous Codex, Infinite Coursework | 21 | Bloodline Recollector, Blossom-Blessed Angel, Carnivorous Cultivator, Diviner of Victory, Emergency Phytomedic, Fatehold Chronologist |
| cost_mod | Geist of Saint Thalia, Tam, the Possibility | 8 | Ajani Resolute, Ajani Unrelenting, Chandra, Chill of Compliance, Chandra, Torch of Defiance, Garruk, Curse Breaker, Garruk, Veiled Butcher |
| counter+:LOYALTY | Tam, the Possibility, Teyo, Diamondblade Mage, Teyo, Lightshield Expert | 7 | Avatar of Burgeoning Echoes, Kiora of Salt and Sand, Way of the Cryomancer, Way of the Deathbringer, Way of the Healer, Way of the Warlord |
| counter+:* | Tam, the Possibility, Teyo, Diamondblade Mage, Teyo, Lightshield Expert | 7 | Avatar of Burgeoning Echoes, Kiora of Salt and Sand, Way of the Cryomancer, Way of the Deathbringer, Way of the Healer, Way of the Warlord |

### 5b. Lonely emissions — a card emitting something ≤ 3 other cards listen for

Grouped by (primitive, the listener set).

| primitive | listened for only by | # emitters | emitters (first 8) |
|---|---|---|---|
| counter+:LOYALTY | Inspired Tethermage | 41 | Academic Ascent, Ajani Resolute, Ajani Unrelenting, Arcane Amphisbaena, Avatar of Burgeoning Echoes, Campus Crier, Chandra, Chill of Compliance, Chandra, Torch of Defiance |
| discard | Tinybones, Pocket Nuisance, Titanbones, Towering Heart | 23 | Ajani Unrelenting, Apex Witchstalker, Arni, Humble Scribe, Awaken the Inferno, Curse-Marred Demon, Divining Duelist, Gideon's Memorial, Hallway Heckler |
| die | Bloodline Recollector, Darklight Phoenix | 18 | Ajani Unrelenting, Archive Arbiter, Fulminous Forte, Kindred Judgment, Lich's Relic, Mind Meanderer, Prophesied End, Silence the Echo |
| cast_target_own | Danitha, Sword of Hope, Ruric Thar, Biomagus | 10 | Academic Ascent, Blazing Crescendo, Blossom-Blessed Angel, Emergency Phytomedic, Last Gasp, Multiply by Zero, Predictive Preparations, Tam's Resistance |
| counter+:P1P1 | Gallia, the Merrymaker, Vigorbloom Vanguard, Yoshimaru, Beloved Companion | 14 | Chandra's Emberling, Danitha, Spear of Agony, Edgar, Ancient Bloodlord, Edgar, Moonlit Sovereign, Graft Surgeon, Guiding Hydra, Hungering Puppetbeast, Inspired Tethermage |
| counter+:P1P1 | Gallia, the Merrymaker, Guiding Hydra, Yoshimaru, Beloved Companion | 1 | Vigorbloom Vanguard |
| counter+:P1P1 | Gallia, the Merrymaker, Guiding Hydra, Vigorbloom Vanguard | 1 | Yoshimaru, Beloved Companion |
| counter+:P1P1 | Guiding Hydra, Vigorbloom Vanguard, Yoshimaru, Beloved Companion | 1 | Gallia, the Merrymaker |
| activate_loyalty | Kiora of Salt and Sand, Way of the Mind Sculptor, Way of the Paradox | 1 | Ajani Unrelenting |
| activate_loyalty | Ajani Unrelenting, Kiora of Salt and Sand, Way of the Mind Sculptor | 1 | Way of the Paradox |
| activate_loyalty | Ajani Unrelenting, Way of the Mind Sculptor, Way of the Paradox | 1 | Kiora of Salt and Sand |
| activate_loyalty | Ajani Unrelenting, Kiora of Salt and Sand, Way of the Paradox | 1 | Way of the Mind Sculptor |

(120 lonely emissions in 12 groups.)

## 6. Top pairs overall under `full` with no shared keyword (each card at most twice)

Hub-capped: Tam, the Possibility pairs with every planeswalker (cost reduction + proliferate) and would otherwise fill the list.

| pair | w(full) | why (top reasons) |
|---|---|---|
| Jace, Reality Sculptor ⟷ Tam, the Possibility | 0.716 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Jace, Reality Sculptor [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Jace, Reality Sculptor [A AB$Effect Cost$ -LOYALTY] (counter+:*, state) |
| Proctor of Potential ⟷ Prudent Fateseer | 0.702 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Proctor of Potential | 0.692 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Ajani Unrelenting ⟷ Way of the Necromancer | 0.669 | Way of the Necromancer [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Unrelenting [A AB$Discard Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Unrelenting [A AB$DamageAll Creature.YouCtrl+!token,Creature.YouDontCtrl] → Way of the Necromancer [T Mode$ChangesZone Battlefield->Graveyard Creature.YouCtrl] (die, state) |
| Chandra, Torch of Defiance ⟷ Tam, the Possibility | 0.663 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Chandra, Torch of Defiance [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Chandra, Torch of Defiance [A AB$DealDamage Cost$ -LOYALTY] (counter+:*, state) |
| Prudent Fateseer ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Liliana the Faultless ⟷ Titanbones, Towering Heart | 0.645 | Liliana the Faultless [A AB$Pump Cost$ Discard] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Liliana the Faultless [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Apex Witchstalker ⟷ Titanbones, Towering Heart | 0.596 | Apex Witchstalker [K:TypeCycling] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Apex Witchstalker [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Ruric Thar, Biomagus ⟷ Tam's Resistance | 0.561 | Tam's Resistance [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Tam's Resistance [cast Tam's Resistance] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Predictive Preparations ⟷ Ruric Thar, Biomagus | 0.561 | Predictive Preparations [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Predictive Preparations [cast Predictive Preparations] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Codie, Ravenous Codex ⟷ Heartwood Crafter | 0.542 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Heartwood Crafter [Prepare card: re-prepared by others] (prepare, state); Heartwood Crafter [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Ajani Resolute ⟷ Way of the Mentor | 0.541 | Way of the Mentor [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Resolute [A AB$GainLife Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Resolute [A AB$GainLife] → Way of the Mentor [T Mode$LifeGained] (lifegain, state) |
| Ajani Unrelenting ⟷ Kiora of Salt and Sand | 0.539 | Kiora of Salt and Sand [SVar:PWLeviathan AB$Token loyalty ability] → Ajani Unrelenting [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Ajani Unrelenting [A AB$PumpAll loyalty ability] → Kiora of Salt and Sand [SVar:X:Count$ThisTurnActivated_Activated.Loyalty+YouCtrl] (activate_loyalty, state) |
| Codie, Ravenous Codex ⟷ Woodwork Prodigy | 0.528 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Woodwork Prodigy [Prepare card: re-prepared by others] (prepare, state); Woodwork Prodigy [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Danitha, Sword of Hope ⟷ Vigorbloom Vanguard | 0.525 | Vigorbloom Vanguard [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Vigorbloom Vanguard [A SP$PutCounter needs a target] (enter, state) |
| Danitha, Sword of Hope ⟷ Emergency Phytomedic | 0.525 | Emergency Phytomedic [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Emergency Phytomedic [A SP$PutCounter needs a target] (enter, state) |
| Aerid Konstrari ⟷ Eye of Jace | 0.504 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Aerid Konstrari [T Mode$ChangesZone self dies] (die, state); Eye of Jace [Eye of Jace enters] → Aerid Konstrari [SVar:X:Count$Valid Artifact.YouCtrl] (enter, state) |
| Ajani Resolute ⟷ Way of the Paradox | 0.499 | Ajani Resolute [A AB$GainLife loyalty ability] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Way of the Paradox [SVar:TrigGainLife DB$GainLife] → Ajani Resolute [T Mode$LifeGained] (lifegain, state) |
| Inspired Tethermage ⟷ Way of the Paradox | 0.493 | Way of the Paradox [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state) |
| Apex Witchstalker ⟷ Eye of Jace | 0.485 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Apex Witchstalker [T Mode$ChangesZone self dies] (die, state); Apex Witchstalker [K:TypeCycling] → Eye of Jace [SVar:X:Count$ValidGraveyard Card.YouCtrl] (tograve, state) |
| Inspired Tethermage ⟷ Way of the Mind Sculptor | 0.481 | Way of the Mind Sculptor [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Mind Sculptor [T Mode$AbilityCast Activated.Loyalty+CountersRemovedToPayGE2You] (activate_loyalty, state) |
| Aerid Konstrari ⟷ Edgar, Ancient Bloodlord | 0.471 | Edgar, Ancient Bloodlord [A AB$PutCounter Cost$ Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] → Aerid Konstrari [T Mode$ChangesZone self dies] (die, state); Aerid Konstrari [SVar:TrigToken DB$Token rg_a_heartwood makes mana] → Edgar, Ancient Bloodlord [A AB$PutCounter mana sink Cost$ 2 Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] (mana, resource) |
| Gallia, the Merrymaker ⟷ Yoshimaru, Beloved Companion | 0.468 | Gallia, the Merrymaker [A AB$PutCounter P1P1] → Yoshimaru, Beloved Companion [R:AddCounter P1P1] (counter+:P1P1, state); Yoshimaru, Beloved Companion [A AB$PutCounter P1P1] → Gallia, the Merrymaker [S Mode$Continuous Affected$ Creature.Other+YouCtrl+counters_GE1_P1P1] (counter+:P1P1, state) |
| Edgar, Ancient Bloodlord ⟷ Simulacrum Shaper | 0.467 | Edgar, Ancient Bloodlord [A AB$PutCounter Cost$ Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] → Simulacrum Shaper [T Mode$ChangesZone self dies] (die, state); Simulacrum Shaper [SVar:TrigChange DB$ChangeZone ramp] → Edgar, Ancient Bloodlord [A AB$PutCounter mana sink Cost$ 2 Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] (mana, resource) |

