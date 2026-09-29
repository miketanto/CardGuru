# FRA synergy graph — generated report (`evaluate.py`, do not edit)

Cards: 280. Directed matches: 30854 ({'resource': 2029, 'state': 28123, 'cost': 702}).

## 1. Schemes

| scheme | undirected edges | Louvain modularity | seed stability (NMI, 20 seeds) | communities |
|---|---|---|---|---|
| uniform | 17955 | 0.133 | 0.893 | [97, 68, 63, 52] |
| tight | 17955 | 0.146 | 0.726 | [91, 62, 61, 47, 19] |
| rarity | 17955 | 0.245 | 0.790 | [81, 81, 66, 52] |
| full | 17955 | 0.284 | 0.839 | [74, 55, 51, 44, 28, 15, 13] |
| full_knn | 2363 | 0.488 | 0.855 | [48, 48, 46, 38, 30, 27, 26, 17] |
| mutual_knn | 437 | 0.663 | 0.968 | [33, 25, 24, 21, 20, 15, 15, 13, 9, 7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |
| norm_knn | 2007 | 0.591 | 0.940 | [59, 37, 37, 30, 24, 23, 22, 20, 17, 11] |

Cross-scheme agreement (NMI): uniform~tight 0.644, uniform~rarity 0.587, uniform~full 0.353, uniform~full_knn 0.243, uniform~mutual_knn 0.289, uniform~norm_knn 0.305, tight~rarity 0.511, tight~full 0.43, tight~full_knn 0.293, tight~mutual_knn 0.318, tight~norm_knn 0.375, rarity~full 0.432, rarity~full_knn 0.299, rarity~mutual_knn 0.305, rarity~norm_knn 0.416, full~full_knn 0.631, full~mutual_knn 0.428, full~norm_knn 0.619, full_knn~mutual_knn 0.518, full_knn~norm_knn 0.682, mutual_knn~norm_knn 0.523

## 2a. Communities under `full_knn`

**C0** (48 cards, colours RBG) — primitives: damage_opp 68%, enter 18%, mana (resource) 6%, attack 4%, cast 3%
  core: Massacre Girl, Most Wanted, Master of Barbs, Whiplash Wordsmith, Grim Repriser, Command the Stage, Ingris Stingerquill, Koth, the Geomancer, Chandra, Torch of Defiance

**C1** (48 cards, colours WRU) — primitives: counter+:P1P1 41%, cast_target_own 27%, cost_mod (cost) 15%, cast 13%, enter 3%
  core: Vigorbloom Vanguard, Geist of Saint Thalia, Ruric Thar, Biomagus, Yoshimaru, Beloved Companion, Danitha, Sword of Hope, Gallia, the Merrymaker, Guiding Hydra, Predictive Preparations

**C2** (46 cards, colours UGW) — primitives: activate_loyalty 52%, enter 24%, counter+:LOYALTY 17%, cost_mod (cost) 3%, counter+:* 2%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Paradox, Way of the Mind Sculptor, Kiora of Salt and Sand, Jace, Reality Sculptor, Avatar of Burgeoning Echoes, Way of the Pyromancer

**C3** (38 cards, colours BGR) — primitives: reenter 67%, enter 19%, tograve 6%, cast 6%, mana (resource) 3%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Return to the Light Realms, Aerid Konstrari, Hungering Puppetbeast, Tenured Tethermage, Craterclaw Colossus

**C4** (30 cards, colours URB) — primitives: draw 69%, discard 21%, tograve 6%, enter 2%, mana (resource) 1%
  core: Tinybones, Pocket Nuisance, The Theorist, Jace Beleren, Lyra, Tolarian Archangel, Murmuring Volume, Proft, Sinister Mastermind, Hallway Heckler, Solitary Cell, Gideon's Memorial

**C5** (27 cards, colours UWR) — primitives: surveil 64%, prepare 24%, tograve 5%, cast 4%, enter 2%
  core: Codie, Ravenous Codex, Prudent Fateseer, Diviner of Victory, Proctor of Potential, Infinite Coursework, Surveillance Phantasm, Semester Foreseer, Fatehold Chronologist

**C6** (26 cards, colours WGB) — primitives: lifegain 94%, enter 2%, counter+:LOYALTY 2%, discard 1%, tograve 1%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Bloombrute, Lyra, Archangel of Dawn, Unflinching Hortimancer, Way of the Mentor, Enlightened Confidant

**C7** (17 cards, colours BGW) — primitives: die 95%, enter 3%, tograve 1%, mana (resource) 1%
  core: Edgar, Ancient Bloodlord, Eye of Jace, Loot, the Anomaly, Way of the Necromancer, Gardenize, Darklight Phoenix, Bloodline Recollector, Budding Insurgent

## 2a2. Communities under `mutual_knn`

**C0** (33 cards, colours GWB) — primitives: counter+:P1P1 41%, reenter 15%, discard 13%, die 8%, draw 8%
  core: Yoshimaru, Beloved Companion, Guiding Hydra, Gallia, the Merrymaker, Tinybones, Pocket Nuisance, Generous Revival, Vinelasher Adept, Yoshimaru, Scrappy Stray, Rewrite Regrets

**C1** (25 cards, colours UGR) — primitives: activate_loyalty 46%, counter+:LOYALTY 16%, enter 13%, draw 11%, cost_mod (cost) 9%
  core: Inspired Tethermage, Way of the Mind Sculptor, Tam, the Possibility, Way of the Paradox, Kiora of Salt and Sand, Ajani Unrelenting, Jace, Reality Sculptor, The Theorist, Jace Beleren

**C2** (24 cards, colours RGU) — primitives: prepare 48%, enter 22%, cast 19%, mana (resource) 8%, reenter 3%
  core: Codie, Ravenous Codex, Infinite Coursework, Heartwood Crafter, Woodwork Prodigy, Konstrari Improviser, Craterclaw Colossus, Pompous Battlemage, Variable Chaser

**C3** (21 cards, colours RBG) — primitives: damage_opp 81%, enter 8%, mana (resource) 6%, attack 2%, cast 2%
  core: Whiplash Wordsmith, Massacre Girl, Most Wanted, Master of Barbs, Ingris Stingerquill, Grim Repriser, Command the Stage, Chandra, Torch of Defiance, Clash of Elements

**C4** (20 cards, colours GWR) — primitives: cast_target_own 82%, cost_mod (cost) 10%, cast 6%, enter 2%
  core: Ruric Thar, Biomagus, Danitha, Sword of Hope, Predictive Preparations, Tam's Resistance, Geist of Saint Thalia, Emergency Phytomedic, Blossom-Blessed Angel, Last Gasp

**C5** (15 cards, colours UW) — primitives: surveil 92%, tograve 5%, enter 2%, reenter 1%, mana (resource) 0%
  core: Proctor of Potential, Surveillance Phantasm, Prudent Fateseer, Diviner of Victory, Denzilore Fatehold, Yuriko, Hope from the Shadows, Saheeli, Consul of Oversight, Chandra, Chill of Compliance

**C6** (15 cards, colours WGB) — primitives: lifegain 80%, counter+:LOYALTY 7%, enter 7%, discard 4%, draw 1%
  core: Liliana the Faultless, Ajani Resolute, Kwia Vigorbloom, Bloombrute, Titanbones, Towering Heart, Way of the Mentor, Greenhouse Propagator, Unflinching Hortimancer

**C7** (13 cards, colours GBU) — primitives: die 94%, enter 4%, tograve 1%, mana (resource) 1%
  core: Edgar, Ancient Bloodlord, Loot, the Anomaly, Eye of Jace, Way of the Necromancer, Gardenize, Apex Witchstalker, Aerid Konstrari, Sphinx of False Conclusions

**C8** (9 cards, colours BUG) — primitives: reenter 48%, tograve 36%, enter 17%
  core: Liliana the Repentant, Dark Matter Manipulator, Carnivorous Cultivator, Keeper of the Quiet Hour, Mindseeker Oculus, Arcane Amphisbaena, Void Extrapolator, Theorix Metamage

**C9** (7 cards, colours G) — primitives: enter 95%, mana (resource) 5%
  core: Hexhaven Invigorator, Haunted Ridge, Overgrown Farmland, Deserted Beach, Rockfall Vale, Shipwreck Marsh, Fblthp, Knows the Way

**C10** (1 cards, colours W) — primitives: 
  core: Campus Crier

**C11** (1 cards, colours W) — primitives: 
  core: Kindred Judgment

**C12** (1 cards, colours W) — primitives: 
  core: Loyal Tutor

**C13** (1 cards, colours W) — primitives: 
  core: Memory Trap

**C14** (1 cards, colours W) — primitives: 
  core: Refute Destiny

**C15** (1 cards, colours W) — primitives: 
  core: Repurposed Enforcer

**C16** (1 cards, colours W) — primitives: 
  core: Shatterwing Pegasus

**C17** (1 cards, colours W) — primitives: 
  core: Surgical Precision

**C18** (1 cards, colours U) — primitives: 
  core: Countersculpt

**C19** (1 cards, colours U) — primitives: 
  core: Cryotheory Adept

**C20** (1 cards, colours U) — primitives: 
  core: Divining Duelist

**C21** (1 cards, colours U) — primitives: 
  core: Icy Reception

**C22** (1 cards, colours U) — primitives: 
  core: Perfected Theory

**C23** (1 cards, colours U) — primitives: 
  core: Precise Redaction

**C24** (1 cards, colours U) — primitives: 
  core: Protege's Awakening

**C25** (1 cards, colours U) — primitives: 
  core: Sphinx's Approach

**C26** (1 cards, colours U) — primitives: 
  core: Unsummon

**C27** (1 cards, colours B) — primitives: 
  core: Cast Away Doubt

**C28** (1 cards, colours B) — primitives: 
  core: Extended Absence

**C29** (1 cards, colours B) — primitives: 
  core: Extrapolate the Impossible

**C30** (1 cards, colours B) — primitives: 
  core: Lich's Relic

**C31** (1 cards, colours B) — primitives: 
  core: Overwrite the Multiverse

**C32** (1 cards, colours B) — primitives: 
  core: Rampart Hunter

**C33** (1 cards, colours B) — primitives: 
  core: Rank Rat

**C34** (1 cards, colours B) — primitives: 
  core: Screeching Soulbreaker

**C35** (1 cards, colours B) — primitives: 
  core: Silence the Echo

**C36** (1 cards, colours B) — primitives: 
  core: Solve for Disappointment

**C37** (1 cards, colours B) — primitives: 
  core: Terminal Criticism

**C38** (1 cards, colours B) — primitives: 
  core: Theoretical Necromancer

**C39** (1 cards, colours B) — primitives: 
  core: Vraska's Final Mercy

**C40** (1 cards, colours R) — primitives: 
  core: Artifist Acumen

**C41** (1 cards, colours R) — primitives: 
  core: Curse-Marred Demon

**C42** (1 cards, colours R) — primitives: 
  core: Eardrum Rattler

**C43** (1 cards, colours R) — primitives: 
  core: Essence Burn

**C44** (1 cards, colours R) — primitives: 
  core: Face Yourself

**C45** (1 cards, colours R) — primitives: 
  core: Fulminous Forte

**C46** (1 cards, colours R) — primitives: 
  core: Heartstring Puller

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
  core: Restore with Empathy

**C57** (1 cards, colours G) — primitives: 
  core: Something Worth Saving

**C58** (1 cards, colours G) — primitives: 
  core: Tarmogoyf

**C59** (1 cards, colours BW) — primitives: 
  core: Blessed Ghoul

**C60** (1 cards, colours RW) — primitives: 
  core: Charge the Sanctum

**C61** (1 cards, colours GU) — primitives: 
  core: Entrust the Spark

**C62** (1 cards, colours UW) — primitives: 
  core: Fatehold Charm

**C63** (1 cards, colours RU) — primitives: 
  core: Frostbite Pyromental

**C64** (1 cards, colours BU) — primitives: 
  core: Null Summoner

**C65** (1 cards, colours BU) — primitives: 
  core: Paradox Shaper

**C66** (1 cards, colours BU) — primitives: 
  core: Recursive Recruitment

**C67** (1 cards, colours GW) — primitives: 
  core: Solarium Sentry

**C68** (1 cards, colours BR) — primitives: 
  core: Stingerquill Charm

**C69** (1 cards, colours BU) — primitives: 
  core: Theorix Charm

**C70** (1 cards, colours BW) — primitives: 
  core: Twisted Fates

**C71** (1 cards, colours BU) — primitives: 
  core: Uldaros Theorix

**C72** (1 cards, colours BW) — primitives: 
  core: Vindictive Triumph

**C73** (1 cards, colours ) — primitives: 
  core: Afterthought Sentry

**C74** (1 cards, colours ) — primitives: 
  core: Archive Arbiter

**C75** (1 cards, colours ) — primitives: 
  core: Medic's Kitesail

**C76** (1 cards, colours ) — primitives: 
  core: Dedicated Commons

**C77** (1 cards, colours ) — primitives: 
  core: Fatehold Annex

**C78** (1 cards, colours ) — primitives: 
  core: Formidable Commons

**C79** (1 cards, colours ) — primitives: 
  core: Hexhaven Dueling Arena

**C80** (1 cards, colours ) — primitives: 
  core: Innovative Commons

**C81** (1 cards, colours ) — primitives: 
  core: Konstrari Annex

**C82** (1 cards, colours ) — primitives: 
  core: Meticulous Commons

**C83** (1 cards, colours ) — primitives: 
  core: Room of Refuge

**C84** (1 cards, colours ) — primitives: 
  core: Stingerquill Annex

**C85** (1 cards, colours ) — primitives: 
  core: Theorist's Sanctum

**C86** (1 cards, colours ) — primitives: 
  core: Theorix Annex

**C87** (1 cards, colours ) — primitives: 
  core: Transformative Commons

**C88** (1 cards, colours ) — primitives: 
  core: Vigorbloom Annex

**C89** (1 cards, colours W) — primitives: 
  core: Rescue Girl, First Responder

**C90** (1 cards, colours W) — primitives: 
  core: Thalia, the Survivor

**C91** (1 cards, colours W) — primitives: 
  core: Tomik, Orzhov Lawmage

**C92** (1 cards, colours W) — primitives: 
  core: Yuriko, Blade of the Mighty

**C93** (1 cards, colours U) — primitives: 
  core: Fblthp, Impossibly Lost

**C94** (1 cards, colours U) — primitives: 
  core: Hapatra, the Desert Frost

**C95** (1 cards, colours U) — primitives: 
  core: Samut, Tyrant of Naktamun

**C96** (1 cards, colours U) — primitives: 
  core: Tetsuko Umezawa, Fugitive

**C97** (1 cards, colours U) — primitives: 
  core: Yargle, Goliath of Otaria

**C98** (1 cards, colours B) — primitives: 
  core: Danitha, Spear of Agony

**C99** (1 cards, colours B) — primitives: 
  core: Gideon the Oathless

**C100** (1 cards, colours B) — primitives: 
  core: Mabel, Bitter Recluse

**C101** (1 cards, colours B) — primitives: 
  core: Yargle, Glutton of Urborg

**C102** (1 cards, colours R) — primitives: 
  core: Arni, Renowned Champion

**C103** (1 cards, colours R) — primitives: 
  core: Jiang Yanggu, Alone

**C104** (1 cards, colours R) — primitives: 
  core: Marwyn, the Clearcutter

**C105** (1 cards, colours R) — primitives: 
  core: Samut, Hazoret's Champion

**C106** (1 cards, colours G) — primitives: 
  core: Ruric Thar, Magecrusher

**C107** (1 cards, colours BG) — primitives: 
  core: Hapatra, the Desert Fang

## 2a3. Communities under `norm_knn`

**C0** (59 cards, colours GUB) — primitives: enter 41%, activate_loyalty 37%, counter+:LOYALTY 15%, cost_mod (cost) 3%, counter+:* 2%
  core: Inspired Tethermage, Kiora of Salt and Sand, Shipwreck Marsh, Deserted Beach, Overgrown Farmland, Rockfall Vale, Haunted Ridge, Way of the Mind Sculptor

**C1** (37 cards, colours RGW) — primitives: enter 53%, mana (resource) 26%, cast 14%, attack 5%, enter (cost) 2%
  core: Traxos, Scourge Eternal, Hungering Puppetbeast, Aerid Konstrari, Craterclaw Colossus, Konstrari Improviser, Woodwork Prodigy, Tenured Tethermage, Pia, Determined Rebuilder

**C2** (37 cards, colours URG) — primitives: draw 51%, discard 37%, tograve 8%, enter 3%, mana (resource) 1%
  core: Tinybones, Pocket Nuisance, Titanbones, Towering Heart, Lyra, Tolarian Archangel, Proft, Sinister Mastermind, Sureshot Sower, Solitary Cell, Pia, Aether Ascetic, The Theorist, Jace Beleren

**C3** (30 cards, colours RUB) — primitives: cast 52%, cost_mod (cost) 31%, die 15%, enter 1%, enter (cost) 0%
  core: Geist of Saint Thalia, Silence the Echo, Tomik, Izzet Sparkmage, Fulminous Forte, Tetsuko Umezawa, Pursuer, Traxos, Academy Guardian, Chandra's Emberling, Cryotheory Adept

**C4** (24 cards, colours WGR) — primitives: counter+:P1P1 50%, cast_target_own 44%, cast 3%, enter 2%, mana (resource) 0%
  core: Danitha, Sword of Hope, Ruric Thar, Biomagus, Yoshimaru, Beloved Companion, Guiding Hydra, Vigorbloom Vanguard, Gallia, the Merrymaker, Predictive Preparations, Last Gasp

**C5** (23 cards, colours WGB) — primitives: lifegain 95%, counter+:LOYALTY 3%, enter 1%, tograve 1%, mana (resource) 0%
  core: Lyra, Archangel of Dawn, Unflinching Hortimancer, Bloombrute, Kwia Vigorbloom, Germinate Recruits, Ajani Resolute, Way of the Mentor, Solarium Sentry

**C6** (22 cards, colours UWB) — primitives: surveil 75%, prepare 14%, tograve 6%, cast 2%, enter 1%
  core: Diviner of Victory, Prudent Fateseer, Surveillance Phantasm, Saheeli, Consul of Oversight, Proft, Consulting Detective, Denzilore Fatehold, Proctor of Potential, Fatehold Chronologist

**C7** (20 cards, colours BUR) — primitives: reenter 86%, tograve 8%, enter 5%
  core: Generous Revival, Rewrite Regrets, Liliana the Repentant, Gallia, Tragic Host, Return to the Light Realms, Rank Rat, Stingcaster Mage, Mabel, Bitter Recluse

**C8** (17 cards, colours RBU) — primitives: damage_opp 95%, cast 2%, enter 2%, reenter 2%, mana (resource) 0%
  core: Master of Barbs, Whiplash Wordsmith, Massacre Girl, Most Wanted, Command the Stage, Grim Repriser, Stinging Vitriol, Clash of Elements, Stingerquill Voxmancer

**C9** (11 cards, colours BGU) — primitives: die 95%, enter 3%, tograve 2%, mana (resource) 0%
  core: Edgar, Ancient Bloodlord, Loot, the Anomaly, Gardenize, Way of the Necromancer, Graft Surgeon, Eye of Jace, Living Library, Sphinx of False Conclusions

## 2b. Communities under `full`

**C0** (74 cards, colours GRB) — primitives: enter 37%, reenter 26%, mana (resource) 17%, die 9%, cast 7%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Aerid Konstrari, Tenured Tethermage, Edgar, Ancient Bloodlord, Simulacrum Shaper, Hungering Puppetbeast

**C1** (55 cards, colours UGB) — primitives: enter 53%, activate_loyalty 29%, counter+:LOYALTY 13%, cost_mod (cost) 2%, counter+:* 1%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Paradox, Way of the Mind Sculptor, Kiora of Salt and Sand, Jace, Reality Sculptor, Avatar of Burgeoning Echoes, Way of the Necromancer

**C2** (51 cards, colours UBR) — primitives: draw 45%, tograve 25%, prepare 9%, discard 9%, enter 5%
  core: Tinybones, Pocket Nuisance, Hallway Heckler, Murmuring Volume, The Theorist, Jace Beleren, Proft, Sinister Mastermind, Solitary Cell, Lyra, Tolarian Archangel, Codie, Ravenous Codex

**C3** (44 cards, colours RWG) — primitives: cast 31%, counter+:P1P1 29%, cast_target_own 19%, cost_mod (cost) 13%, enter 5%
  core: Geist of Saint Thalia, Ruric Thar, Biomagus, Vigorbloom Vanguard, Yoshimaru, Beloved Companion, Danitha, Sword of Hope, Gallia, the Merrymaker, Guiding Hydra, Predictive Preparations

**C4** (28 cards, colours WGB) — primitives: lifegain 94%, enter 2%, counter+:LOYALTY 2%, tograve 1%, discard 1%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Enlightened Confidant, Way of the Mentor, Bloombrute, Lyra, Archangel of Dawn, Unflinching Hortimancer

**C5** (15 cards, colours UW) — primitives: surveil 91%, tograve 6%, enter 2%, reenter 1%, cast 0%
  core: Proctor of Potential, Prudent Fateseer, Diviner of Victory, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Yuriko, Hope from the Shadows

**C6** (13 cards, colours RBU) — primitives: damage_opp 91%, enter 3%, cast 2%, attack 2%, mana (resource) 1%
  core: Massacre Girl, Most Wanted, Whiplash Wordsmith, Master of Barbs, Grim Repriser, Command the Stage, Ingris Stingerquill, Koth, the Geomancer, Stingerquill Voxmancer

## 2c. Communities under `rarity`

**C0** (81 cards, colours GWR) — primitives: mana (resource) 37%, enter 31%, counter+:P1P1 10%, cast 8%, lifegain 7%
  core: Yoshimaru, Beloved Companion, Kwia Vigorbloom, Aerid Konstrari, Hungering Puppetbeast, Vigorbloom Vanguard, Tenured Tethermage, Edgar, Ancient Bloodlord, Traxos, Scourge Eternal

**C1** (81 cards, colours UBW) — primitives: tograve 59%, draw 11%, surveil 9%, enter 7%, reenter 7%
  core: Proctor of Potential, Chandra, Chill of Compliance, Liliana the Repentant, Proft, Sinister Mastermind, Gideon's Memorial, Enlightened Confidant, Eye of Jace, Seasoned Cryomancer

**C2** (66 cards, colours UGW) — primitives: enter 53%, activate_loyalty 23%, counter+:LOYALTY 15%, counter+:* 3%, mana (resource) 2%
  core: Ajani Unrelenting, Inspired Tethermage, Way of the Paradox, Kiora of Salt and Sand, Way of the Mind Sculptor, Tam, the Possibility, Way of the Necromancer, Way of the Mentor

**C3** (52 cards, colours RBU) — primitives: cast 44%, damage_opp 24%, die 9%, cost_mod (cost) 8%, cast_target_own 6%
  core: Grim Repriser, Geist of Saint Thalia, Whiplash Wordsmith, Command the Stage, Ruric Thar, Biomagus, Massacre Girl, Most Wanted, Bloodline Recollector, Pyre Rhymer

## 2x. Colour coherence (post-hoc; colour is not a state-edge input)

Colour enters the graph only through the resource-flow colour factor. In a draft set archetypes are colour pairs, so communities that align with colour identity are recovering real structure. **Added after the first results, not pre-registered.** NMI(community, colour identity) vs 200 label shuffles.

| scheme | NMI with colour | shuffled mean | max shuffled |
|---|---|---|---|
| uniform | 0.126 | 0.054 | 0.080 |
| tight | 0.147 | 0.067 | 0.089 |
| rarity | 0.157 | 0.054 | 0.074 |
| full | 0.211 | 0.089 | 0.113 |
| full_knn | 0.190 | 0.099 | 0.127 |
| mutual_knn | 0.411 | 0.362 | 0.391 |
| norm_knn | 0.232 | 0.117 | 0.149 |

## 2y. Draft-archetype agreement and hub damping (`SYNERGY-GRAPH.md` §12)

Gold cards: 57 (colours exactly one of the 10 pairs). Signpost agreement = pairs whose signpost shares a cluster with the plurality of the pair's gold cards. Hub slots = kept edges between a Prepare card and Codie / Infinite Coursework. Prepare spread = most Prepare cards in one cluster.

| scheme | signpost agreement /10 | gold NMI | hub slots | Prepare spread /21 | isolated | UB / BR / RG gold plurality |
|---|---|---|---|---|---|---|
| uniform | 6 | 0.405 | 42 | 9 | 0 | C2 7/7 / C3 4/7 / C0 7/7 |
| tight | 7 | 0.449 | 42 | 9 | 0 | C1 6/7 / C3 4/7 / C0 7/7 |
| rarity | 9 | 0.513 | 42 | 10 | 0 | C1 7/7 / C3 5/7 / C0 7/7 |
| full | 7 | 0.635 | 42 | 10 | 0 | C2 6/7 / C6 6/7 / C0 5/7 |
| full_knn | 6 | 0.556 | 42 | 13 | 0 | C5 3/7 / C0 6/7 / C5 3/7 |
| mutual_knn | 4 | 0.671 | 20 | 6 | 98 | C8 2/7 / C3 6/7 / C2 4/7 |
| norm_knn | 5 | 0.597 | 40 | 8 | 0 | C6 3/7 / C8 5/7 / C1 5/7 |

## 3. Validation (plan's three known-good checks)

### V1 surveil enablers ↔ graveyard-count payoffs

13 surveil emitters; 12 graveyard-size payoffs (Count$ValidGraveyard, Threshold, graveyard triggers).

| scheme | same-community rate | shuffled-label baseline | p (one-sided, 2000 perms) | direct edges S→P / pairs |
|---|---|---|---|---|
| uniform | 0.922 | 0.262 | 0.0005 | 154/154 |
| tight | 0.922 | 0.230 | 0.0005 | 154/154 |
| rarity | 0.922 | 0.253 | 0.0005 | 154/154 |
| full | 0.130 | 0.178 | 0.9190 | 154/154 |
| full_knn | 0.253 | 0.134 | 0.0020 | 154/154 |
| mutual_knn | 0.065 | 0.048 | 0.2604 | 154/154 |
| norm_knn | 0.279 | 0.118 | 0.0015 | 154/154 |

Payoffs: Cruel Calculations, Dark Matter Manipulator, Eye of Jace, Hapatra, the Desert Fang, Null Summoner, Proft, Sinister Mastermind, Recursive Recruitment, Tarmogoyf, Theorix Metamage, Void Extrapolator, Winter, Tormented Loner, Yuriko, Hope from the Shadows

### V2 loyalty adders → 'whenever you put loyalty counters on a planeswalker'

`Inspired Tethermage`: 43/44 loyalty emitters link to it by `counter+:LOYALTY`. Their rank among its 132 neighbours under `full`: median 22, best 1. Same community under full: 37/43.

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

Among Chandra's 279 neighbours under `full`: best consumer of any kind ranks 1 (that one is linked by other edges too); 48 consumers have resource flow as their *strongest* link, the best of which ranks 17. Mana is a common primitive (24 emitting cards, 244 consuming cards), so rarity weighting ranks these edges low; they are present but not what the combined weight surfaces first.

Chandra top-10 neighbours overall (full): Tam, the Possibility 0.663; Massacre Girl, Most Wanted 0.342; Master of Barbs 0.336; Ajani Unrelenting 0.312; Grim Repriser 0.308; Way of the Mentor 0.302; Way of the Necromancer 0.302; Inspired Tethermage 0.289; Whiplash Wordsmith 0.276; Command the Stage 0.272

## 4. Held-out check: Forge's hand-authored DeckHas / DeckHints

Forge authors tag some cards `DeckHints:Ability$Graveyard` ("this card wants graveyard enablers") and others `DeckHas:Ability$Graveyard`. Neither is an input. For each hinted card, take its top-10 neighbours and ask what fraction carry the matching `DeckHas` (for `Type$X` hints: have type X). Baseline = the label's rate over all other cards. Wilson 95% intervals. Small n — these are sanity rows, not results.

| scheme | hinted (card,label) pairs | hits in top-10 | rate [95% CI] | baseline rate | lift |
|---|---|---|---|---|---|
| uniform | 43 | 91/430 | 0.212 [0.176, 0.253] | 0.037 | 5.71× |
| tight | 43 | 89/430 | 0.207 [0.171, 0.248] | 0.037 | 5.58× |
| rarity | 43 | 97/430 | 0.226 [0.189, 0.267] | 0.037 | 6.08× |
| full | 43 | 77/430 | 0.179 [0.146, 0.218] | 0.037 | 4.83× |
| full_knn | 43 | 77/430 | 0.179 [0.146, 0.218] | 0.037 | 4.83× |
| mutual_knn | 22 | 52/221 | 0.235 [0.184, 0.295] | 0.037 | 6.34× |
| norm_knn | 43 | 64/430 | 0.149 [0.118, 0.186] | 0.037 | 4.01× |

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
| Proctor of Potential ⟷ Prudent Fateseer | 0.720 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Jace, Reality Sculptor ⟷ Tam, the Possibility | 0.716 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Jace, Reality Sculptor [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Jace, Reality Sculptor [A AB$Effect Cost$ -LOYALTY] (counter+:*, state) |
| Eye of Jace ⟷ Massacre Girl, Most Wanted | 0.714 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Massacre Girl, Most Wanted [T Mode$ChangesZone Battlefield->Graveyard Creature.Other+YouCtrl,Planeswalker.Other+YouCtrl] (die, state); Eye of Jace [SVar:DBDealDamage DB$DealDamage -> Player.Opponent] → Massacre Girl, Most Wanted [T Mode$DamageDone ValidTarget$ Opponent noncombat] (damage_opp, state) |
| Diviner of Victory ⟷ Proctor of Potential | 0.710 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Ajani Unrelenting ⟷ Way of the Necromancer | 0.669 | Way of the Necromancer [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Unrelenting [A AB$Discard Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Unrelenting [A AB$DamageAll Creature.YouCtrl+!token,Creature.YouDontCtrl] → Way of the Necromancer [T Mode$ChangesZone Battlefield->Graveyard Creature.YouCtrl] (die, state) |
| Chandra, Torch of Defiance ⟷ Tam, the Possibility | 0.663 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Chandra, Torch of Defiance [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Chandra, Torch of Defiance [A AB$DealDamage Cost$ -LOYALTY] (counter+:*, state) |
| Prudent Fateseer ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Liliana the Faultless ⟷ Titanbones, Towering Heart | 0.645 | Liliana the Faultless [A AB$Pump Cost$ Discard] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Liliana the Faultless [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Massacre Girl, Most Wanted ⟷ Whiplash Wordsmith | 0.636 | Whiplash Wordsmith [A SP$DealDamage -> Opponent] → Massacre Girl, Most Wanted [T Mode$DamageDone ValidTarget$ Opponent noncombat] (damage_opp, state); Massacre Girl, Most Wanted [SVar:TrigDamage DB$DealDamage -> Opponent] → Whiplash Wordsmith [SVar:X wasDealtNonCombatDamage] (damage_opp, state) |
| Apex Witchstalker ⟷ Titanbones, Towering Heart | 0.596 | Apex Witchstalker [K:TypeCycling] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Apex Witchstalker [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Ruric Thar, Biomagus ⟷ Tam's Resistance | 0.561 | Tam's Resistance [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Tam's Resistance [cast Tam's Resistance] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Predictive Preparations ⟷ Ruric Thar, Biomagus | 0.561 | Predictive Preparations [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Predictive Preparations [cast Predictive Preparations] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Codie, Ravenous Codex ⟷ Heartwood Crafter | 0.542 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Heartwood Crafter [Prepare card: re-prepared by others] (prepare, state); Heartwood Crafter [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Ajani Resolute ⟷ Way of the Mentor | 0.541 | Way of the Mentor [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Resolute [A AB$GainLife Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Resolute [A AB$GainLife] → Way of the Mentor [T Mode$LifeGained] (lifegain, state) |
| Ajani Unrelenting ⟷ Kiora of Salt and Sand | 0.539 | Kiora of Salt and Sand [SVar:PWLeviathan AB$Token loyalty ability] → Ajani Unrelenting [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Ajani Unrelenting [A AB$PumpAll loyalty ability] → Kiora of Salt and Sand [SVar:X:Count$ThisTurnActivated_Activated.Loyalty+YouCtrl] (activate_loyalty, state) |
| Apex Witchstalker ⟷ Eye of Jace | 0.536 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Apex Witchstalker [T Mode$ChangesZone self dies] (die, state); Apex Witchstalker [K:TypeCycling] → Eye of Jace [SVar:X:Count$ValidGraveyard Card.YouCtrl] (tograve, state) |
| Codie, Ravenous Codex ⟷ Woodwork Prodigy | 0.528 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Woodwork Prodigy [Prepare card: re-prepared by others] (prepare, state); Woodwork Prodigy [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Danitha, Sword of Hope ⟷ Vigorbloom Vanguard | 0.525 | Vigorbloom Vanguard [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Vigorbloom Vanguard [A SP$PutCounter needs a target] (enter, state) |
| Danitha, Sword of Hope ⟷ Emergency Phytomedic | 0.525 | Emergency Phytomedic [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Emergency Phytomedic [A SP$PutCounter needs a target] (enter, state) |
| Ajani Resolute ⟷ Way of the Paradox | 0.499 | Ajani Resolute [A AB$GainLife loyalty ability] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Way of the Paradox [SVar:TrigGainLife DB$GainLife] → Ajani Resolute [T Mode$LifeGained] (lifegain, state) |
| Inspired Tethermage ⟷ Way of the Paradox | 0.493 | Way of the Paradox [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state) |
| Inspired Tethermage ⟷ Way of the Mind Sculptor | 0.481 | Way of the Mind Sculptor [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Mind Sculptor [T Mode$AbilityCast Activated.Loyalty+CountersRemovedToPayGE2You] (activate_loyalty, state) |
| Aerid Konstrari ⟷ Edgar, Ancient Bloodlord | 0.471 | Edgar, Ancient Bloodlord [A AB$PutCounter Cost$ Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] → Aerid Konstrari [T Mode$ChangesZone self dies] (die, state); Aerid Konstrari [SVar:TrigToken DB$Token rg_a_heartwood makes mana] → Edgar, Ancient Bloodlord [A AB$PutCounter mana sink Cost$ 2 Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] (mana, resource) |
| Gallia, the Merrymaker ⟷ Yoshimaru, Beloved Companion | 0.468 | Gallia, the Merrymaker [A AB$PutCounter P1P1] → Yoshimaru, Beloved Companion [R:AddCounter P1P1] (counter+:P1P1, state); Yoshimaru, Beloved Companion [A AB$PutCounter P1P1] → Gallia, the Merrymaker [S Mode$Continuous Affected$ Creature.Other+YouCtrl+counters_GE1_P1P1] (counter+:P1P1, state) |

