# FRA synergy graph — generated report (`evaluate.py`, do not edit)

Cards: 280. Directed matches: 32373 ({'resource': 2093, 'state': 29578, 'cost': 702}).

## 1. Schemes

| scheme | undirected edges | Louvain modularity | seed stability (NMI, 20 seeds) | communities |
|---|---|---|---|---|
| uniform | 18602 | 0.134 | 0.882 | [108, 101, 71] |
| tight | 18602 | 0.145 | 0.671 | [86, 81, 68, 45] |
| rarity | 18602 | 0.223 | 0.618 | [87, 79, 66, 48] |
| full | 18602 | 0.280 | 0.888 | [76, 61, 56, 37, 36, 14] |

Cross-scheme agreement (NMI): uniform~tight 0.543, uniform~rarity 0.466, uniform~full 0.31, tight~rarity 0.439, tight~full 0.331, rarity~full 0.475

## 2a. Communities under `full`

**C0** (76 cards, colours GRB) — primitives: enter 30%, reenter 24%, mana (resource) 17%, counter+:P1P1 14%, cast 6%
  core: Liliana the Repentant, Rewrite Regrets, Generous Revival, Yoshimaru, Beloved Companion, Tenured Tethermage, Hungering Puppetbeast, Vraska, the Cutting Glare, Vigorbloom Vanguard

**C1** (61 cards, colours RBU) — primitives: cast 41%, prepare 15%, tograve 13%, cost_mod (cost) 10%, cast_target_own 9%
  core: Codie, Ravenous Codex, Geist of Saint Thalia, Infinite Coursework, Ruric Thar, Biomagus, Pyre Rhymer, Pompous Battlemage, Grim Repriser, Void Extrapolator

**C2** (56 cards, colours UGR) — primitives: enter 53%, activate_loyalty 29%, counter+:LOYALTY 13%, cost_mod (cost) 2%, counter+:* 1%
  core: Inspired Tethermage, Ajani Unrelenting, Way of the Mind Sculptor, Way of the Paradox, Kiora of Salt and Sand, Jace, Reality Sculptor, Avatar of Burgeoning Echoes, Way of the Necromancer

**C3** (37 cards, colours URB) — primitives: draw 71%, discard 13%, tograve 7%, enter 4%, mana (resource) 3%
  core: Tinybones, Pocket Nuisance, Murmuring Volume, The Theorist, Jace Beleren, Lyra, Tolarian Archangel, Hallway Heckler, Solitary Cell, Gideon's Memorial, Proft, Sinister Mastermind

**C4** (36 cards, colours WGB) — primitives: lifegain 79%, die 12%, enter 3%, tograve 2%, mana (resource) 1%
  core: Ajani Resolute, Titanbones, Towering Heart, Kwia Vigorbloom, Enlightened Confidant, Way of the Mentor, Bloombrute, Lyra, Archangel of Dawn, Unflinching Hortimancer

**C5** (14 cards, colours UW) — primitives: surveil 94%, tograve 3%, enter 1%, reenter 1%, mana (resource) 0%
  core: Prudent Fateseer, Diviner of Victory, Proctor of Potential, Surveillance Phantasm, Denzilore Fatehold, Saheeli, Consul of Oversight, Proft, Consulting Detective, Chandra, Chill of Compliance

## 2b. Communities under `rarity`

**C0** (87 cards, colours GRW) — primitives: mana (resource) 37%, enter 29%, counter+:P1P1 11%, cast 9%, lifegain 6%
  core: Yoshimaru, Beloved Companion, Kwia Vigorbloom, Vigorbloom Vanguard, Hungering Puppetbeast, Aerid Konstrari, Tenured Tethermage, Guiding Hydra, Edgar, Ancient Bloodlord

**C1** (79 cards, colours UBW) — primitives: tograve 47%, cast 18%, surveil 15%, enter 5%, prepare 4%
  core: Proctor of Potential, Chandra, Chill of Compliance, Eye of Jace, Grim Repriser, Enlightened Confidant, Prudent Fateseer, Diviner of Victory, Yuriko, Hope from the Shadows

**C2** (66 cards, colours UGW) — primitives: enter 53%, activate_loyalty 23%, counter+:LOYALTY 15%, counter+:* 3%, cost_mod (cost) 1%
  core: Ajani Unrelenting, Inspired Tethermage, Kiora of Salt and Sand, Way of the Paradox, Way of the Mind Sculptor, Tam, the Possibility, Way of the Necromancer, Way of the Mentor

**C3** (48 cards, colours BRU) — primitives: tograve 36%, draw 30%, reenter 13%, discard 11%, enter 7%
  core: Murmuring Volume, Liliana the Repentant, Tinybones, Pocket Nuisance, Gideon's Memorial, Titanbones, Towering Heart, Solitary Cell, Proft, Sinister Mastermind, Hallway Heckler

## 3. Validation (plan's three known-good checks)

### V1 surveil enablers ↔ graveyard-count payoffs

13 surveil emitters; 12 graveyard-size payoffs (Count$ValidGraveyard, Threshold, graveyard triggers).

| scheme | same-community rate | shuffled-label baseline | p (one-sided, 2000 perms) | direct edges S→P / pairs |
|---|---|---|---|---|
| uniform | 0.922 | 0.342 | 0.0005 | 154/154 |
| tight | 0.766 | 0.261 | 0.0005 | 154/154 |
| rarity | 0.688 | 0.259 | 0.0005 | 154/154 |
| full | 0.065 | 0.195 | 1.0000 | 154/154 |

Payoffs: Cruel Calculations, Dark Matter Manipulator, Eye of Jace, Hapatra, the Desert Fang, Null Summoner, Proft, Sinister Mastermind, Recursive Recruitment, Tarmogoyf, Theorix Metamage, Void Extrapolator, Winter, Tormented Loner, Yuriko, Hope from the Shadows

### V2 loyalty adders → 'whenever you put loyalty counters on a planeswalker'

`Inspired Tethermage`: 43/44 loyalty emitters link to it by `counter+:LOYALTY`. Their rank among its 133 neighbours under `full`: median 22, best 1. Same community under full: 38/43.

Top-10 neighbours (full): Way of the Mind Sculptor 0.481; Way of the Paradox 0.481; Jace, Reality Sculptor 0.456; Way of the Pyromancer 0.416; Ajani Unrelenting 0.407; Sanctum Lurker 0.395; Avatar of Burgeoning Echoes 0.395; Way of the Healer 0.395; Way of the Cryomancer 0.395; Way of the Deathbringer 0.395

Pre-registration check 4 (Empower → PW card SubCounter fuel edges): **0** (must be 0).

### V3 Chandra, Torch of Defiance → top end / X spells (resource flow)

78 resource-flow consumers. Chandra's keywords: none. Consumers sharing a keyword: 0. Resource edges whose reason cites a keyword: 0 (pre-reg 2: must be 0).

| consumer | MV / cost | reason | w(full) |
|---|---|---|---|
| Pyre Rhymer | 1 R R | SVar:IslandTrigger Mode$TapsForMana Mountain | 0.102 |
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

Chandra top-10 neighbours overall (full): Tam, the Possibility 0.686; Ajani Unrelenting 0.334; Way of the Mind Sculptor 0.307; Way of the Mentor 0.302; Way of the Necromancer 0.302; Inspired Tethermage 0.300; Way of the Paradox 0.264; Kiora of Salt and Sand 0.249; Teyo, Lightshield Expert 0.154; Teyo, Diamondblade Mage 0.154

## 4. Held-out check: Forge's hand-authored DeckHas / DeckHints

Forge authors tag some cards `DeckHints:Ability$Graveyard` ("this card wants graveyard enablers") and others `DeckHas:Ability$Graveyard`. Neither is an input. For each hinted card, take its top-10 neighbours and ask what fraction carry the matching `DeckHas` (for `Type$X` hints: have type X). Baseline = the label's rate over all other cards. Wilson 95% intervals. Small n — these are sanity rows, not results.

| scheme | hinted (card,label) pairs | hits in top-10 | rate [95% CI] | baseline rate | lift |
|---|---|---|---|---|---|
| uniform | 43 | 87/430 | 0.202 [0.167, 0.243] | 0.037 | 5.45× |
| tight | 43 | 91/430 | 0.212 [0.176, 0.253] | 0.037 | 5.71× |
| rarity | 43 | 98/430 | 0.228 [0.191, 0.270] | 0.037 | 6.14× |
| full | 43 | 79/430 | 0.184 [0.150, 0.223] | 0.037 | 4.95× |

## 5. Sparse edges — lonely pairings

Matches where the listener is satisfied by ≤ 3 cards in the set **and** the emission satisfies ≤ 3 listeners, excluding intrinsic emissions (being a creature, being cast). Sorted by `full` weight.

| emitter | listener | primitive | why | m_listen / m_emit | w(full) |
|---|---|---|---|---|---|
| Twisted Fates | Ferocity of the Hunt | die (state) | A SP$Destroy Permanent.nonLand → T Mode$ChangesZone Battlefield->Graveyard Card.AttachedBy | 3 / 3 | 0.194 |
| Archive Arbiter | Ferocity of the Hunt | die (state) | SVar:DBDestroy DB$Destroy Permanent.nonCreature+nonLand → T Mode$ChangesZone Battlefield->Graveyard Card.AttachedBy | 3 / 3 | 0.194 |
| Vraska, the Cutting Glare | Ferocity of the Hunt | die (state) | SVar:TrigDestroy DB$Destroy Permanent.OppCtrl → T Mode$ChangesZone Battlefield->Graveyard Card.AttachedBy | 3 / 3 | 0.194 |

(3 lonely ordered pairs in total.)

## 6. Top pairs overall under `full` with no shared keyword

| pair | w(full) | why (top reasons) |
|---|---|---|
| Jace, Reality Sculptor ⟷ Tam, the Possibility | 0.717 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Jace, Reality Sculptor [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Jace, Reality Sculptor [A AB$Effect Cost$ -LOYALTY] (counter+:*, state) |
| Proctor of Potential ⟷ Prudent Fateseer | 0.702 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Proctor of Potential | 0.692 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Chandra, Torch of Defiance ⟷ Tam, the Possibility | 0.686 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Chandra, Torch of Defiance [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Chandra, Torch of Defiance [A AB$DealDamage Cost$ -LOYALTY] (counter+:*, state) |
| Chandra, Chill of Compliance ⟷ Tam, the Possibility | 0.686 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Chandra, Chill of Compliance [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Chandra, Chill of Compliance [A AB$Tap Cost$ -LOYALTY] (counter+:*, state) |
| Ajani Unrelenting ⟷ Way of the Necromancer | 0.669 | Way of the Necromancer [SVar:TrigPutCounterAll DB$PutCounterAll LOYALTY] → Ajani Unrelenting [A AB$Discard Cost$ -LOYALTY] (counter+:LOYALTY, state); Ajani Unrelenting [A AB$DamageAll Creature.YouCtrl+!token,Creature.YouDontCtrl] → Way of the Necromancer [T Mode$ChangesZone Battlefield->Graveyard Creature.YouCtrl] (die, state) |
| Prudent Fateseer ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Prudent Fateseer [T Mode$Surveil] (surveil, state); Prudent Fateseer [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Diviner of Victory ⟷ Surveillance Phantasm | 0.659 | Surveillance Phantasm [A AB$Surveil] → Diviner of Victory [T Mode$Surveil] (surveil, state); Diviner of Victory [SVar:DBSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Garruk, Curse Breaker ⟷ Tam, the Possibility | 0.647 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Garruk, Curse Breaker [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Garruk, Curse Breaker [A AB$Token Cost$ -LOYALTY] (counter+:*, state) |
| Liliana the Faultless ⟷ Titanbones, Towering Heart | 0.645 | Liliana the Faultless [A AB$Pump Cost$ Discard] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Liliana the Faultless [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Garruk, Veiled Butcher ⟷ Tam, the Possibility | 0.644 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Garruk, Veiled Butcher [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Garruk, Veiled Butcher [A AB$Sacrifice Cost$ -LOYALTY] (counter+:*, state) |
| Ajani Unrelenting ⟷ Tam, the Possibility | 0.644 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Ajani Unrelenting [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Ajani Unrelenting [A AB$Discard Cost$ -LOYALTY] (counter+:*, state) |
| Tam, the Possibility ⟷ The Theorist, Jace Beleren | 0.641 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → The Theorist, Jace Beleren [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → The Theorist, Jace Beleren [A AB$ChangeZone Cost$ -LOYALTY] (counter+:*, state) |
| Ajani Resolute ⟷ Tam, the Possibility | 0.636 | Tam, the Possibility [S:ReduceCost ValidCard$ Planeswalker Amount$ 1] → Ajani Resolute [matches ValidCard$] (cost_mod, cost); Tam, the Possibility [A AB$Proliferate] → Ajani Resolute [A AB$GainLife Cost$ -LOYALTY] (counter+:*, state) |
| Proctor of Potential ⟷ Surveillance Phantasm | 0.618 | Proctor of Potential [SVar:TrigSurveil DB$Surveil] → Surveillance Phantasm [SVar:Y:Count$YouSurveilThisTurn] (surveil, state); Surveillance Phantasm [A AB$Surveil] → Proctor of Potential [SVar:Y:Count$YouSurveilThisTurn] (surveil, state) |
| Apex Witchstalker ⟷ Titanbones, Towering Heart | 0.596 | Apex Witchstalker [K:TypeCycling] → Titanbones, Towering Heart [T Mode$Discarded] (discard, state); Apex Witchstalker [SVar:TrigGainLife DB$GainLife] → Titanbones, Towering Heart [T Mode$LifeGained] (lifegain, state) |
| Codie, Ravenous Codex ⟷ Pyre Rhymer | 0.586 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Pyre Rhymer [Prepare card: re-prepared by others] (prepare, state); Pyre Rhymer [cast Molten Tide] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Codie, Ravenous Codex ⟷ Woodwork Prodigy | 0.583 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Woodwork Prodigy [Prepare card: re-prepared by others] (prepare, state); Woodwork Prodigy [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Codie, Ravenous Codex ⟷ Konstrari Improviser | 0.583 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Konstrari Improviser [Prepare card: re-prepared by others] (prepare, state); Konstrari Improviser [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Codie, Ravenous Codex ⟷ Heartwood Crafter | 0.583 | Codie, Ravenous Codex [A AB$AlterAttribute prepares Valid Creature.YouCtrl] → Heartwood Crafter [Prepare card: re-prepared by others] (prepare, state); Heartwood Crafter [cast Soul Tether] → Codie, Ravenous Codex [T Mode$SpellCast Card.prepared] (cast, state) |
| Ruric Thar, Biomagus ⟷ Tam's Resistance | 0.561 | Tam's Resistance [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Tam's Resistance [cast Tam's Resistance] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Predictive Preparations ⟷ Ruric Thar, Biomagus | 0.561 | Predictive Preparations [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Predictive Preparations [cast Predictive Preparations] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Ruric Thar, Biomagus ⟷ Vigorbloom Vanguard | 0.561 | Vigorbloom Vanguard [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Vigorbloom Vanguard [cast Seed Suture] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Emergency Phytomedic ⟷ Ruric Thar, Biomagus | 0.561 | Emergency Phytomedic [A SP$PutCounter targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Emergency Phytomedic [cast Seed Suture] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |
| Ruric Thar, Biomagus ⟷ Tethermage's Advantage | 0.555 | Tethermage's Advantage [A SP$Pump targets Creature] → Ruric Thar, Biomagus [T Mode$BecomesTarget] (cast_target_own, state); Tethermage's Advantage [cast Tethermage's Advantage] → Ruric Thar, Biomagus [K:Prowess] (cast, state) |

