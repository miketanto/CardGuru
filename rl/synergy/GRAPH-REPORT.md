# FRA synergy graph — generated report (`evaluate.py`, do not edit)

Cards: 280. Directed matches: 32305 ({'resource': 2069, 'state': 29534, 'cost': 702}).

## 1. Schemes

| scheme | undirected edges | Louvain modularity | seed stability (NMI, 20 seeds) | communities |
|---|---|---|---|---|
| uniform | 18596 | 0.135 | 0.872 | [110, 102, 68] |
| tight | 18596 | 0.145 | 0.699 | [124, 86, 70] |
| rarity | 18596 | 0.228 | 0.660 | [81, 80, 67, 52] |
| full | 18596 | 0.279 | 0.856 | [84, 55, 54, 37, 36, 14] |
| full_knn | 2355 | 0.507 | 0.909 | [65, 50, 41, 30, 28, 25, 16, 14, 11] |

Cross-scheme agreement (NMI): uniform~tight 0.644, uniform~rarity 0.456, uniform~full 0.316, uniform~full_knn 0.217, tight~rarity 0.499, tight~full 0.385, tight~full_knn 0.272, rarity~full 0.515, rarity~full_knn 0.418, full~full_knn 0.682

## 2a. Communities under `full_knn`

**C0** (65 cards, colours RBG) — primitives: reenter 52%, enter 21%, mana (resource) 12%, cast 7%, tograve 4%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Hungering Puppetbeast, Vraska, the Cutting Glare, Aerid Konstrari, Gallia, Tragic Host, Tenured Tethermage

**C1** (50 cards, colours UGR) — primitives: activate_loyalty 55%, enter 20%, counter+:LOYALTY 18%, cost_mod (cost) 4%, counter+:* 2%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Mind Sculptor, Way of the Paradox, Kiora of Salt and Sand, Jace, Reality Sculptor, Tam, the Possibility, Avatar of Burgeoning Echoes

**C2** (41 cards, colours RUB) — primitives: prepare 44%, cast 27%, cost_mod (cost) 15%, mana (resource) 5%, tograve 4%
  core: Codie, Ravenous Codex, Infinite Coursework, Geist of Saint Thalia, Pyre Rhymer, Variable Chaser, Pompous Battlemage, Bloodline Recollector, Void Extrapolator

**C3** (30 cards, colours URB) — primitives: draw 71%, discard 18%, mana (resource) 4%, tograve 4%, enter 2%
  core: Tinybones, Pocket Nuisance, Murmuring Volume, Lyra, Tolarian Archangel, The Theorist, Jace Beleren, Hallway Heckler, Solitary Cell, Proft, Sinister Mastermind, Gideon's Memorial

**C4** (28 cards, colours WGB) — primitives: lifegain 94%, enter 2%, counter+:LOYALTY 2%, discard 1%, tograve 1%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Bloombrute, Lyra, Archangel of Dawn, Unflinching Hortimancer, Way of the Mentor, Enlightened Confidant

**C5** (25 cards, colours WRG) — primitives: counter+:P1P1 57%, cast_target_own 37%, cast 3%, enter 2%, mana (resource) 1%
  core: Vigorbloom Vanguard, Ruric Thar, Biomagus, Yoshimaru, Beloved Companion, Danitha, Sword of Hope, Gallia, the Merrymaker, Guiding Hydra, Predictive Preparations, Tam's Resistance

**C6** (16 cards, colours UWR) — primitives: surveil 93%, tograve 3%, enter 2%, reenter 1%, mana (resource) 0%
  core: Prudent Fateseer, Proctor of Potential, Diviner of Victory, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Desperate Futurescribe

**C7** (14 cards, colours BGW) — primitives: die 95%, enter 3%, mana (resource) 1%, tograve 1%
  core: Edgar, Ancient Bloodlord, Eye of Jace, Loot, the Anomaly, Way of the Necromancer, Gardenize, Massacre Girl, Most Wanted, Budding Insurgent, Theorist's Proxy

**C8** (11 cards, colours GBR) — primitives: enter 99%, tograve 0%, mana (resource) 0%
  core: Overgrown Farmland, Shipwreck Marsh, Rockfall Vale, Haunted Ridge, Primal Witchstalker, Deserted Beach, Koth, the Geomancer, Hexhaven Invigorator

## 2b. Communities under `full`

**C0** (84 cards, colours RGB) — primitives: enter 32%, mana (resource) 25%, reenter 21%, counter+:P1P1 8%, cast 6%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Hungering Puppetbeast, Tenured Tethermage, Yoshimaru, Beloved Companion, Aerid Konstrari, Vraska, the Cutting Glare

**C1** (55 cards, colours UGW) — primitives: enter 53%, activate_loyalty 29%, counter+:LOYALTY 13%, cost_mod (cost) 2%, counter+:* 1%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Mind Sculptor, Way of the Paradox, Kiora of Salt and Sand, Jace, Reality Sculptor, Avatar of Burgeoning Echoes, Tam, the Possibility

**C2** (54 cards, colours RBU) — primitives: cast 43%, prepare 14%, tograve 13%, cost_mod (cost) 12%, cast_target_own 11%
  core: Geist of Saint Thalia, Codie, Ravenous Codex, Ruric Thar, Biomagus, Infinite Coursework, Pyre Rhymer, Pompous Battlemage, Grim Repriser, Danitha, Sword of Hope

**C3** (37 cards, colours WGB) — primitives: lifegain 78%, die 11%, enter 4%, tograve 2%, counter+:P1P1 2%
  core: Titanbones, Towering Heart, Ajani Resolute, Kwia Vigorbloom, Enlightened Confidant, Way of the Mentor, Unflinching Hortimancer, Bloombrute, Lyra, Archangel of Dawn

**C4** (36 cards, colours URB) — primitives: draw 72%, discard 13%, tograve 6%, enter 4%, mana (resource) 3%
  core: Tinybones, Pocket Nuisance, The Theorist, Jace Beleren, Murmuring Volume, Lyra, Tolarian Archangel, Hallway Heckler, Solitary Cell, Gideon's Memorial, Proft, Sinister Mastermind

**C5** (14 cards, colours UW) — primitives: surveil 93%, tograve 4%, enter 1%, reenter 1%, mana (resource) 0%
  core: Prudent Fateseer, Diviner of Victory, Proctor of Potential, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Chandra, Chill of Compliance

## 2c. Communities under `rarity`

**C0** (81 cards, colours GRW) — primitives: mana (resource) 39%, enter 29%, counter+:P1P1 9%, cast 7%, lifegain 6%
  core: Kwia Vigorbloom, Hungering Puppetbeast, Yoshimaru, Beloved Companion, Aerid Konstrari, Tenured Tethermage, Vigorbloom Vanguard, Edgar, Ancient Bloodlord, Traxos, Scourge Eternal

**C1** (80 cards, colours UWB) — primitives: tograve 44%, cast 21%, surveil 14%, enter 6%, prepare 5%
  core: Proctor of Potential, Chandra, Chill of Compliance, Enlightened Confidant, Eye of Jace, Prudent Fateseer, Diviner of Victory, Codie, Ravenous Codex, Yuriko, Hope from the Shadows

**C2** (67 cards, colours UGW) — primitives: enter 53%, activate_loyalty 23%, counter+:LOYALTY 15%, counter+:* 3%, cost_mod (cost) 1%
  core: Ajani Unrelenting, Inspired Tethermage, Kiora of Salt and Sand, Way of the Paradox, Way of the Mind Sculptor, Tam, the Possibility, Way of the Necromancer, Way of the Mentor

**C3** (52 cards, colours BRU) — primitives: tograve 35%, draw 29%, reenter 15%, discard 10%, enter 8%
  core: Murmuring Volume, Liliana the Repentant, Gideon's Memorial, Tinybones, Pocket Nuisance, Solitary Cell, Proft, Sinister Mastermind, Grim Repriser, Hallway Heckler

## 2x. Colour coherence (post-hoc; colour is not a state-edge input)

Colour enters the graph only through the resource-flow colour factor. In a draft set archetypes are colour pairs, so communities that align with colour identity are recovering real structure. **Added after the first results, not pre-registered.** NMI(community, colour identity) vs 200 label shuffles.

| scheme | NMI with colour | shuffled mean | max shuffled |
|---|---|---|---|
| uniform | 0.097 | 0.039 | 0.072 |
| tight | 0.094 | 0.039 | 0.070 |
| rarity | 0.119 | 0.054 | 0.076 |
| full | 0.192 | 0.077 | 0.111 |
| full_knn | 0.196 | 0.108 | 0.136 |

## 3. Validation (plan's three known-good checks)

### V1 surveil enablers ↔ graveyard-count payoffs

13 surveil emitters; 12 graveyard-size payoffs (Count$ValidGraveyard, Threshold, graveyard triggers).

| scheme | same-community rate | shuffled-label baseline | p (one-sided, 2000 perms) | direct edges S→P / pairs |
|---|---|---|---|---|
| uniform | 0.922 | 0.344 | 0.0005 | 154/154 |
| tight | 0.766 | 0.353 | 0.0005 | 154/154 |
| rarity | 0.688 | 0.254 | 0.0005 | 154/154 |
| full | 0.065 | 0.199 | 1.0000 | 154/154 |
| full_knn | 0.065 | 0.142 | 0.9950 | 154/154 |

Payoffs: Cruel Calculations, Dark Matter Manipulator, Eye of Jace, Hapatra, the Desert Fang, Null Summoner, Proft, Sinister Mastermind, Recursive Recruitment, Tarmogoyf, Theorix Metamage, Void Extrapolator, Winter, Tormented Loner, Yuriko, Hope from the Shadows

### V2 loyalty adders → 'whenever you put loyalty counters on a planeswalker'

`Inspired Tethermage`: 43/44 loyalty emitters link to it by `counter+:LOYALTY`. Their rank among its 133 neighbours under `full`: median 22, best 1. Same community under full: 38/43.

Top-10 neighbours (full): Way of the Mind Sculptor 0.481; Way of the Paradox 0.481; Jace, Reality Sculptor 0.456; Way of the Pyromancer 0.417; Ajani Unrelenting 0.407; Sanctum Lurker 0.395; Avatar of Burgeoning Echoes 0.395; Way of the Healer 0.395; Way of the Cryomancer 0.395; Way of the Deathbringer 0.395

Pre-registration check 4 (Empower → PW card SubCounter fuel edges): **0** (must be 0).

### V3 Chandra, Torch of Defiance → top end / X spells (resource flow)

77 resource-flow consumers. Chandra's keywords: none. Consumers sharing a keyword: 0. Resource edges whose reason cites a keyword: 0 (pre-reg 2: must be 0).

| consumer | MV / cost | reason | w(full) |
|---|---|---|---|
| Ajani's Anguish | X R | SVar:X:Count$xPaid | 0.071 |
| Ajani's Anguish | X R | ManaCost X R (X spell) | 0.071 |
| Awaken the Inferno | 4 R | ManaCost 4 R (MV 5) | 0.071 |
| Draconic Visitor | 3 R R | ManaCost 3 R R (MV 5) | 0.071 |
| Identity Echo | 2 R | A AB$ChangeZone mana sink Cost$ 3 R | 0.071 |
| Tether Technician | 4 R | ManaCost 4 R (MV 5) | 0.071 |
| Archive Arbiter | 6 | ManaCost 6 (MV 6) | 0.071 |
| Codie, Ravenous Codex | 3 | A AB$AlterAttribute mana sink Cost$ W U B R G T | 0.071 |
| The Echoverse Fulcrum | 2 | A AB$DestroyAll mana sink Cost$ 5 T Exile<1/CARDNAME> | 0.071 |
| Hall of Echoes | no cost | A AB$Clone mana sink Cost$ 5 | 0.071 |
| Hexhaven Dueling Arena | no cost | A AB$AlterAttribute mana sink Cost$ 4 T | 0.071 |
| Room of Refuge | no cost | A AB$PutCounter mana sink Cost$ 5 T Sac<1/CARDNAME/this land> | 0.071 |

Among Chandra's 279 neighbours under `full`: best consumer of any kind ranks 1 (that one is linked by other edges too); 72 consumers have resource flow as their *strongest* link, the best of which ranks 12. Mana is a common primitive (25 emitters, 84 listeners), so rarity weighting ranks these edges low; they are present but not what the combined weight surfaces first.

Chandra top-10 neighbours overall (full): Tam, the Possibility 0.687; Ajani Unrelenting 0.335; Way of the Mind Sculptor 0.307; Way of the Mentor 0.302; Way of the Necromancer 0.302; Inspired Tethermage 0.301; Way of the Paradox 0.264; Kiora of Salt and Sand 0.249; Teyo, Lightshield Expert 0.156; Teyo, Diamondblade Mage 0.156

## 4. Held-out check: Forge's hand-authored DeckHas / DeckHints

Forge authors tag some cards `DeckHints:Ability$Graveyard` ("this card wants graveyard enablers") and others `DeckHas:Ability$Graveyard`. Neither is an input. For each hinted card, take its top-10 neighbours and ask what fraction carry the matching `DeckHas` (for `Type$X` hints: have type X). Baseline = the label's rate over all other cards. Wilson 95% intervals. Small n — these are sanity rows, not results.

| scheme | hinted (card,label) pairs | hits in top-10 | rate [95% CI] | baseline rate | lift |
|---|---|---|---|---|---|
| uniform | 43 | 86/430 | 0.200 [0.165, 0.240] | 0.037 | 5.39× |
| tight | 43 | 89/430 | 0.207 [0.171, 0.248] | 0.037 | 5.58× |
| rarity | 43 | 99/430 | 0.230 [0.193, 0.272] | 0.037 | 6.21× |
| full | 43 | 80/430 | 0.186 [0.152, 0.226] | 0.037 | 5.02× |
| full_knn | 43 | 81/430 | 0.188 [0.154, 0.228] | 0.037 | 5.08× |

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
| Jace, Reality Sculptor ⟷ Tam, the Possibility | 0.717 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Jace, Reality Sculptor [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Jace, Reality Sculptor [A AB$Effect Cost$ -LOYALTY] (counter+:*, state) |
| Proctor of Potential ⟷ Prudent Fateseer | 0.702 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Proctor of Potential | 0.692 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Chandra, Torch of Defiance ⟷ Tam, the Possibility | 0.687 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Chandra, Torch of Defiance [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Chandra, Torch of Defiance [A AB$DealDamage Cost$ -LOYALTY] (counter+:*, state) |
| Ajani Unrelenting ⟷ Way of the Necromancer | 0.669 | Way of the Necromancer [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Unrelenting [A AB$Discard Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Unrelenting [A AB$DamageAll Creature.YouCtrl+!token,Creature.YouDontCtrl] → Way of the Necromancer [T Mode$ChangesZone Battlefield->Graveyard Creature.YouCtrl] (die, state) |
| Prudent Fateseer ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Liliana the Faultless ⟷ Titanbones, Towering Heart | 0.645 | Liliana the Faultless [A AB$Pump Cost$ Discard] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Liliana the Faultless [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Apex Witchstalker ⟷ Titanbones, Towering Heart | 0.596 | Apex Witchstalker [K:TypeCycling] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Apex Witchstalker [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Codie, Ravenous Codex ⟷ Pyre Rhymer | 0.586 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Pyre Rhymer [Prepare card: re-prepared by others] (prepare, state); Pyre Rhymer [cast Molten Tide] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Codie, Ravenous Codex ⟷ Woodwork Prodigy | 0.584 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Woodwork Prodigy [Prepare card: re-prepared by others] (prepare, state); Woodwork Prodigy [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Ruric Thar, Biomagus ⟷ Tam's Resistance | 0.561 | Tam's Resistance [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Tam's Resistance [cast Tam's Resistance] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Predictive Preparations ⟷ Ruric Thar, Biomagus | 0.561 | Predictive Preparations [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Predictive Preparations [cast Predictive Preparations] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Ajani Resolute ⟷ Way of the Mentor | 0.541 | Way of the Mentor [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Resolute [A AB$GainLife Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Resolute [A AB$GainLife] → Way of the Mentor [T Mode$LifeGained] (lifegain, state) |
| Ajani Unrelenting ⟷ Kiora of Salt and Sand | 0.539 | Kiora of Salt and Sand [SVar:PWLeviathan AB$Token loyalty ability] → Ajani Unrelenting [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Ajani Unrelenting [A AB$PumpAll loyalty ability] → Kiora of Salt and Sand [SVar:X:Count$ThisTurnActivated_Activated.Loyalty+YouCtrl] (activate_loyalty, state) |
| Danitha, Sword of Hope ⟷ Vigorbloom Vanguard | 0.525 | Vigorbloom Vanguard [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Vigorbloom Vanguard [A SP$PutCounter needs a target] (enter, state) |
| Danitha, Sword of Hope ⟷ Tam's Resistance | 0.525 | Tam's Resistance [A SP$PutCounter targets Creature] → Danitha, Sword of Hope [T Mode$SpellCast Equipment,Spell.IsTargeting Valid Creature.YouCtrl] (cast_target_own, state); Danitha, Sword of Hope [Danitha, Sword of Hope enters] → Tam's Resistance [A SP$PutCounter needs a target] (enter, state) |
| Edgar, Ancient Bloodlord ⟷ Simulacrum Shaper | 0.524 | Edgar, Ancient Bloodlord [A AB$PutCounter Cost$ Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] → Simulacrum Shaper [T Mode$ChangesZone self dies] (die, state); Simulacrum Shaper [SVar:TrigChange DB$ChangeZone ramp] → Edgar, Ancient Bloodlord [A AB$PutCounter mana sink Cost$ 2 Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] (mana, resource) |
| Aerid Konstrari ⟷ Eye of Jace | 0.504 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Aerid Konstrari [T Mode$ChangesZone self dies] (die, state); Eye of Jace [Eye of Jace enters] → Aerid Konstrari [SVar:X:Count$Valid Artifact.YouCtrl] (enter, state) |
| Ajani Resolute ⟷ Way of the Paradox | 0.499 | Ajani Resolute [A AB$GainLife loyalty ability] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state); Way of the Paradox [SVar:TrigGainLife DB$GainLife] → Ajani Resolute [T Mode$LifeGained] (lifegain, state) |
| Aerid Konstrari ⟷ Edgar, Ancient Bloodlord | 0.495 | Edgar, Ancient Bloodlord [A AB$PutCounter Cost$ Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] → Aerid Konstrari [T Mode$ChangesZone self dies] (die, state); Aerid Konstrari [SVar:TrigToken DB$Token rg_a_heartwood makes mana] → Edgar, Ancient Bloodlord [A AB$PutCounter mana sink Cost$ 2 Sac<1/Creature.Other;Planeswalker.Other/another creature or planeswalker>] (mana, resource) |
| Apex Witchstalker ⟷ Eye of Jace | 0.485 | Eye of Jace [SVar:DBSac DB$Sacrifice] → Apex Witchstalker [T Mode$ChangesZone self dies] (die, state); Apex Witchstalker [K:TypeCycling] → Eye of Jace [SVar:X:Count$ValidGraveyard Card.YouCtrl] (tograve, state) |
| Inspired Tethermage ⟷ Way of the Paradox | 0.481 | Way of the Paradox [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Paradox [T Mode$AbilityCast Activated.LoyaltyYou] (activate_loyalty, state) |
| Inspired Tethermage ⟷ Way of the Mind Sculptor | 0.481 | Way of the Mind Sculptor [SVar:DBEmpower DB$Empower Empower Jace] → Inspired Tethermage [T Mode$CounterAddedOnce Planeswalker] (counter+:LOYALTY, state); Inspired Tethermage [A AB$Empower Empower Jace token has loyalty abilities] → Way of the Mind Sculptor [T Mode$AbilityCast Activated.Loyalty+CountersRemovedToPayGE2You] (activate_loyalty, state) |
| Gallia, the Merrymaker ⟷ Yoshimaru, Beloved Companion | 0.468 | Gallia, the Merrymaker [A AB$PutCounter P1P1] → Yoshimaru, Beloved Companion [R:AddCounter P1P1] (counter+:P1P1, state); Yoshimaru, Beloved Companion [A AB$PutCounter P1P1] → Gallia, the Merrymaker [S:Continuous Affected$ Creature.Other+YouCtrl+counters_GE1_P1P1] (counter+:P1P1, state) |

