# FRA synergy graph — generated report (`evaluate.py`, do not edit)

Cards: 280. Directed matches: 32731 ({'resource': 2152, 'state': 29877, 'cost': 702}).

## 1. Schemes

| scheme | undirected edges | Louvain modularity | seed stability (NMI, 20 seeds) | communities |
|---|---|---|---|---|
| uniform | 18850 | 0.134 | 0.910 | [110, 101, 69] |
| tight | 18850 | 0.146 | 0.744 | [123, 87, 70] |
| rarity | 18850 | 0.225 | 0.660 | [84, 82, 67, 47] |
| full | 18850 | 0.278 | 0.844 | [85, 55, 53, 37, 36, 14] |
| full_knn | 2359 | 0.506 | 0.917 | [63, 51, 37, 30, 28, 25, 18, 16, 12] |

Cross-scheme agreement (NMI): uniform~tight 0.644, uniform~rarity 0.484, uniform~full 0.333, uniform~full_knn 0.211, tight~rarity 0.562, tight~full 0.399, tight~full_knn 0.265, rarity~full 0.497, rarity~full_knn 0.373, full~full_knn 0.668

## 2a. Communities under `full_knn`

**C0** (63 cards, colours RBG) — primitives: reenter 53%, enter 21%, mana (resource) 12%, cast 7%, tograve 4%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Hungering Puppetbeast, Aerid Konstrari, Vraska, the Cutting Glare, Tenured Tethermage, Return to the Light Realms

**C1** (51 cards, colours UGB) — primitives: activate_loyalty 51%, enter 21%, counter+:LOYALTY 20%, cost_mod (cost) 3%, counter+:* 2%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Paradox, Way of the Mind Sculptor, Kiora of Salt and Sand, Jace, Reality Sculptor, Tam, the Possibility, Avatar of Burgeoning Echoes

**C2** (37 cards, colours RUG) — primitives: prepare 46%, cast 28%, cost_mod (cost) 14%, mana (resource) 5%, tograve 5%
  core: Codie, Ravenous Codex, Infinite Coursework, Geist of Saint Thalia, Pyre Rhymer, Variable Chaser, Pompous Battlemage, Theorix Metamage, Void Extrapolator

**C3** (30 cards, colours URB) — primitives: draw 72%, discard 18%, mana (resource) 4%, tograve 4%, enter 2%
  core: Tinybones, Pocket Nuisance, Murmuring Volume, Lyra, Tolarian Archangel, The Theorist, Jace Beleren, Hallway Heckler, Solitary Cell, Proft, Sinister Mastermind, Gideon's Memorial

**C4** (28 cards, colours WGB) — primitives: lifegain 94%, enter 2%, counter+:LOYALTY 2%, discard 1%, tograve 1%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Bloombrute, Lyra, Archangel of Dawn, Unflinching Hortimancer, Way of the Mentor, Enlightened Confidant

**C5** (25 cards, colours WRG) — primitives: counter+:P1P1 57%, cast_target_own 37%, cast 3%, enter 2%, mana (resource) 1%
  core: Vigorbloom Vanguard, Ruric Thar, Biomagus, Yoshimaru, Beloved Companion, Danitha, Sword of Hope, Gallia, the Merrymaker, Guiding Hydra, Predictive Preparations, Tam's Resistance

**C6** (18 cards, colours BGW) — primitives: die 96%, enter 2%, mana (resource) 1%, tograve 1%
  core: Edgar, Ancient Bloodlord, Eye of Jace, Loot, the Anomaly, Gardenize, Massacre Girl, Most Wanted, Darklight Phoenix, Bloodline Recollector, Living Library

**C7** (16 cards, colours UWR) — primitives: surveil 93%, tograve 3%, enter 2%, reenter 1%, mana (resource) 0%
  core: Prudent Fateseer, Proctor of Potential, Diviner of Victory, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Desperate Futurescribe

**C8** (12 cards, colours GRB) — primitives: enter 98%, mana (resource) 2%, tograve 0%
  core: Koth, the Geomancer, Rockfall Vale, Overgrown Farmland, Shipwreck Marsh, Primal Witchstalker, Haunted Ridge, Deserted Beach, Hexhaven Invigorator

## 2b. Communities under `full`

**C0** (85 cards, colours RGB) — primitives: enter 32%, mana (resource) 26%, reenter 20%, counter+:P1P1 7%, cast 6%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Hungering Puppetbeast, Tenured Tethermage, Yoshimaru, Beloved Companion, Aerid Konstrari, Vraska, the Cutting Glare

**C1** (55 cards, colours UGW) — primitives: enter 53%, activate_loyalty 29%, counter+:LOYALTY 13%, cost_mod (cost) 2%, counter+:* 1%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Paradox, Way of the Mind Sculptor, Kiora of Salt and Sand, Jace, Reality Sculptor, Avatar of Burgeoning Echoes, Tam, the Possibility

**C2** (53 cards, colours RBU) — primitives: cast 40%, tograve 16%, prepare 14%, cost_mod (cost) 12%, cast_target_own 11%
  core: Geist of Saint Thalia, Codie, Ravenous Codex, Ruric Thar, Biomagus, Infinite Coursework, Pyre Rhymer, Pompous Battlemage, Danitha, Sword of Hope, Grim Repriser

**C3** (37 cards, colours WGB) — primitives: lifegain 78%, die 11%, enter 4%, tograve 2%, counter+:P1P1 2%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Enlightened Confidant, Way of the Mentor, Unflinching Hortimancer, Bloombrute, Lyra, Archangel of Dawn

**C4** (36 cards, colours URB) — primitives: draw 72%, discard 13%, tograve 6%, enter 4%, mana (resource) 3%
  core: Tinybones, Pocket Nuisance, The Theorist, Jace Beleren, Murmuring Volume, Lyra, Tolarian Archangel, Hallway Heckler, Solitary Cell, Gideon's Memorial, Proft, Sinister Mastermind

**C5** (14 cards, colours UW) — primitives: surveil 93%, tograve 4%, enter 1%, reenter 1%, mana (resource) 0%
  core: Prudent Fateseer, Diviner of Victory, Proctor of Potential, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Chandra, Chill of Compliance

## 2c. Communities under `rarity`

**C0** (84 cards, colours UBW) — primitives: tograve 45%, cast 23%, surveil 13%, enter 5%, prepare 4%
  core: Proctor of Potential, Chandra, Chill of Compliance, Eye of Jace, Grim Repriser, Prudent Fateseer, Enlightened Confidant, Diviner of Victory, Yuriko, Hope from the Shadows

**C1** (82 cards, colours GRW) — primitives: mana (resource) 37%, enter 30%, counter+:P1P1 10%, lifegain 8%, cast 7%
  core: Kwia Vigorbloom, Yoshimaru, Beloved Companion, Hungering Puppetbeast, Vigorbloom Vanguard, Aerid Konstrari, Tenured Tethermage, Edgar, Ancient Bloodlord, Traxos, Scourge Eternal

**C2** (67 cards, colours UGW) — primitives: enter 53%, activate_loyalty 23%, counter+:LOYALTY 15%, counter+:* 3%, mana (resource) 1%
  core: Ajani Unrelenting, Inspired Tethermage, Kiora of Salt and Sand, Way of the Paradox, Way of the Mind Sculptor, Tam, the Possibility, Way of the Necromancer, Way of the Mentor

**C3** (47 cards, colours BUR) — primitives: tograve 38%, draw 29%, reenter 11%, discard 11%, enter 8%
  core: Liliana the Repentant, Murmuring Volume, Tinybones, Pocket Nuisance, Titanbones, Towering Heart, Gideon's Memorial, Seasoned Cryomancer, Proft, Sinister Mastermind, Solitary Cell

## 2x. Colour coherence (post-hoc; colour is not a state-edge input)

Colour enters the graph only through the resource-flow colour factor. In a draft set archetypes are colour pairs, so communities that align with colour identity are recovering real structure. **Added after the first results, not pre-registered.** NMI(community, colour identity) vs 200 label shuffles.

| scheme | NMI with colour | shuffled mean | max shuffled |
|---|---|---|---|
| uniform | 0.100 | 0.039 | 0.061 |
| tight | 0.095 | 0.039 | 0.068 |
| rarity | 0.138 | 0.055 | 0.078 |
| full | 0.189 | 0.078 | 0.119 |
| full_knn | 0.202 | 0.108 | 0.135 |

## 3. Validation (plan's three known-good checks)

### V1 surveil enablers ↔ graveyard-count payoffs

13 surveil emitters; 12 graveyard-size payoffs (Count$ValidGraveyard, Threshold, graveyard triggers).

| scheme | same-community rate | shuffled-label baseline | p (one-sided, 2000 perms) | direct edges S→P / pairs |
|---|---|---|---|---|
| uniform | 0.922 | 0.341 | 0.0005 | 154/154 |
| tight | 0.766 | 0.349 | 0.0005 | 154/154 |
| rarity | 0.688 | 0.260 | 0.0005 | 154/154 |
| full | 0.065 | 0.200 | 1.0000 | 154/154 |
| full_knn | 0.065 | 0.136 | 0.9940 | 154/154 |

Payoffs: Cruel Calculations, Dark Matter Manipulator, Eye of Jace, Hapatra, the Desert Fang, Null Summoner, Proft, Sinister Mastermind, Recursive Recruitment, Tarmogoyf, Theorix Metamage, Void Extrapolator, Winter, Tormented Loner, Yuriko, Hope from the Shadows

### V2 loyalty adders → 'whenever you put loyalty counters on a planeswalker'

`Inspired Tethermage`: 43/44 loyalty emitters link to it by `counter+:LOYALTY`. Their rank among its 133 neighbours under `full`: median 22, best 1. Same community under full: 38/43.

Top-10 neighbours (full): Way of the Paradox 0.516; Way of the Mind Sculptor 0.481; Jace, Reality Sculptor 0.455; Way of the Pyromancer 0.416; Ajani Unrelenting 0.407; Jace's Machinations 0.400; Sanctum Lurker 0.395; Avatar of Burgeoning Echoes 0.395; Way of the Healer 0.395; Way of the Cryomancer 0.395

Pre-registration check 4 (Empower → PW card SubCounter fuel edges): **0** (must be 0).

### V3 Chandra, Torch of Defiance → top end / X spells (resource flow)

77 resource-flow consumers. Chandra's keywords: none. Consumers sharing a keyword: 0. Resource edges whose reason cites a keyword: 0 (pre-reg 2: must be 0).

| consumer | MV / cost | reason | w(full) |
|---|---|---|---|
| Ajani's Anguish | X R | SVar:X:Count$xPaid | 0.070 |
| Ajani's Anguish | X R | ManaCost X R (X spell) | 0.070 |
| Awaken the Inferno | 4 R | ManaCost 4 R (MV 5) | 0.070 |
| Draconic Visitor | 3 R R | ManaCost 3 R R (MV 5) | 0.070 |
| Identity Echo | 2 R | A AB$ChangeZone mana sink Cost$ 3 R | 0.070 |
| Tether Technician | 4 R | ManaCost 4 R (MV 5) | 0.070 |
| Archive Arbiter | 6 | ManaCost 6 (MV 6) | 0.070 |
| Codie, Ravenous Codex | 3 | A AB$AlterAttribute mana sink Cost$ W U B R G T | 0.070 |
| The Echoverse Fulcrum | 2 | A AB$DestroyAll mana sink Cost$ 5 T Exile<1/CARDNAME> | 0.070 |
| Hall of Echoes | no cost | A AB$Clone mana sink Cost$ 5 | 0.070 |
| Hexhaven Dueling Arena | no cost | A AB$AlterAttribute mana sink Cost$ 4 T | 0.070 |
| Room of Refuge | no cost | A AB$PutCounter mana sink Cost$ 5 T Sac<1/CARDNAME/this land> | 0.070 |

Among Chandra's 279 neighbours under `full`: best consumer of any kind ranks 1 (that one is linked by other edges too); 72 consumers have resource flow as their *strongest* link, the best of which ranks 12. Mana is a common primitive (25 emitters, 84 listeners), so rarity weighting ranks these edges low; they are present but not what the combined weight surfaces first.

Chandra top-10 neighbours overall (full): Tam, the Possibility 0.685; Ajani Unrelenting 0.333; Way of the Mind Sculptor 0.306; Way of the Mentor 0.302; Way of the Necromancer 0.302; Inspired Tethermage 0.300; Way of the Paradox 0.264; Kiora of Salt and Sand 0.248; Teyo, Lightshield Expert 0.156; Teyo, Diamondblade Mage 0.156

## 4. Held-out check: Forge's hand-authored DeckHas / DeckHints

Forge authors tag some cards `DeckHints:Ability$Graveyard` ("this card wants graveyard enablers") and others `DeckHas:Ability$Graveyard`. Neither is an input. For each hinted card, take its top-10 neighbours and ask what fraction carry the matching `DeckHas` (for `Type$X` hints: have type X). Baseline = the label's rate over all other cards. Wilson 95% intervals. Small n — these are sanity rows, not results.

| scheme | hinted (card,label) pairs | hits in top-10 | rate [95% CI] | baseline rate | lift |
|---|---|---|---|---|---|
| uniform | 43 | 87/430 | 0.202 [0.167, 0.243] | 0.037 | 5.45× |
| tight | 43 | 90/430 | 0.209 [0.174, 0.250] | 0.037 | 5.64× |
| rarity | 43 | 96/430 | 0.223 [0.186, 0.265] | 0.037 | 6.02× |
| full | 43 | 83/430 | 0.193 [0.159, 0.233] | 0.037 | 5.20× |
| full_knn | 43 | 82/430 | 0.191 [0.156, 0.231] | 0.037 | 5.14× |

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
| Chandra, Torch of Defiance ⟷ Tam, the Possibility | 0.685 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Chandra, Torch of Defiance [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Chandra, Torch of Defiance [A AB$DealDamage Cost$ -LOYALTY] (counter+:*, state) |
| Ajani Unrelenting ⟷ Way of the Necromancer | 0.669 | Way of the Necromancer [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Unrelenting [A AB$Discard Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Unrelenting [A AB$DamageAll Creature.YouCtrl+!token,Creature.YouDontCtrl] → Way of the Necromancer [T Mode$ChangesZone Battlefield->Graveyard Creature.YouCtrl] (die, state) |
| Prudent Fateseer ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Liliana the Faultless ⟷ Titanbones, Towering Heart | 0.645 | Liliana the Faultless [A AB$Pump Cost$ Discard] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Liliana the Faultless [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Apex Witchstalker ⟷ Titanbones, Towering Heart | 0.596 | Apex Witchstalker [K:TypeCycling] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Apex Witchstalker [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Codie, Ravenous Codex ⟷ Pyre Rhymer | 0.585 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Pyre Rhymer [Prepare card: re-prepared by others] (prepare, state); Pyre Rhymer [cast Molten Tide] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Codie, Ravenous Codex ⟷ Woodwork Prodigy | 0.583 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Woodwork Prodigy [Prepare card: re-prepared by others] (prepare, state); Woodwork Prodigy [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Ruric Thar, Biomagus ⟷ Tam's Resistance | 0.561 | Tam's Resistance [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Tam's Resistance [cast Tam's Resistance] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Predictive Preparations ⟷ Ruric Thar, Biomagus | 0.561 | Predictive Preparations [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Predictive Preparations [cast Predictive Preparations] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Ajani Resolute ⟷ Way of the Mentor | 0.541 | Way of the Mentor [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Resolute [A AB$GainLife Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Resolute [A AB$GainLife] → Way of the Mentor [T Mode$LifeGained] (lifegain, state) |
| Ajani Unrelenting ⟷ Kiora of Salt and Sand | 0.539 | Kiora of Salt and Sand [SVar:PWLeviathan AB$Token loyalty ability] → Ajani Unrelenting [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Ajani Unrelenting [A AB$PumpAll loyalty ability] → Kiora of Salt and Sand [SVar:X:Count$ThisTurnActivated_Activated.Loyalty+YouCtrl] (activate_loyalty, state) |
| Danitha, Sword of Hope ⟷ Vigorbloom Vanguard | 0.525 | Vigorbloom Vanguard [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Vigorbloom Vanguard [A SP$PutCounter needs a target] (enter, state) |
| Danitha, Sword of Hope ⟷ Emergency Phytomedic | 0.525 | Emergency Phytomedic [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Emergency Phytomedic [A SP$PutCounter needs a target] (enter, state) |
| Edgar, Ancient Bloodlord ⟷ Simulacrum Shaper | 0.522 | Edgar, Ancient Bloodlord [A AB$PutCounter Cost$ Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] → Simulacrum Shaper [T Mode$ChangesZone self dies] (die, state); Simulacrum Shaper [SVar:TrigChange DB$ChangeZone ramp] → Edgar, Ancient Bloodlord [A AB$PutCounter mana sink Cost$ 2 Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] (mana, resource) |
| Inspired Tethermage ⟷ Way of the Paradox | 0.516 | Way of the Paradox [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state) |
| Aerid Konstrari ⟷ Eye of Jace | 0.504 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Aerid Konstrari [T Mode$ChangesZone self dies] (die, state); Eye of Jace [Eye of Jace enters] → Aerid Konstrari [SVar:X:Count$Valid Artifact.YouCtrl] (enter, state) |
| Ajani Resolute ⟷ Way of the Paradox | 0.499 | Ajani Resolute [A AB$GainLife loyalty ability] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Way of the Paradox [SVar:TrigGainLife DB$GainLife] → Ajani Resolute [T Mode$LifeGained] (lifegain, state) |
| Aerid Konstrari ⟷ Edgar, Ancient Bloodlord | 0.495 | Edgar, Ancient Bloodlord [A AB$PutCounter Cost$ Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] → Aerid Konstrari [T Mode$ChangesZone self dies] (die, state); Aerid Konstrari [SVar:TrigToken DB$Token rg_a_heartwood makes mana] → Edgar, Ancient Bloodlord [A AB$PutCounter mana sink Cost$ 2 Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] (mana, resource) |
| Apex Witchstalker ⟷ Eye of Jace | 0.485 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Apex Witchstalker [T Mode$ChangesZone self dies] (die, state); Apex Witchstalker [K:TypeCycling] → Eye of Jace [SVar:X:Count$ValidGraveyard Card.YouCtrl] (tograve, state) |
| Inspired Tethermage ⟷ Way of the Mind Sculptor | 0.481 | Way of the Mind Sculptor [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Mind Sculptor [T Mode$AbilityCast Activated.Loyalty+CountersRemovedToPayGE2You] (activate_loyalty, state) |
| Gallia, the Merrymaker ⟷ Yoshimaru, Beloved Companion | 0.468 | Gallia, the Merrymaker [A AB$PutCounter P1P1] → Yoshimaru, Beloved Companion [R:AddCounter P1P1] (counter+:P1P1, state); Yoshimaru, Beloved Companion [A AB$PutCounter P1P1] → Gallia, the Merrymaker [S Mode$Continuous Affected$ Creature.Other+YouCtrl+counters_GE1_P1P1] (counter+:P1P1, state) |

