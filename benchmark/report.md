# Mechanical-search benchmark report

Dataset: `dataset.jsonl.gz` (34519 faces, pin `670429bf`), index load 0.7s.


| query | hits | goldens |
|---|---|---|
| combat-damage-player-token | 101 | pass |
| impulse-exile | 268 | pass |
| sac-creature-cost-mana | 34 | pass |
| etb-drain-each-opponent | 24 | pass |
| dies-token | 167 | pass |
| cast-copy-trigger | 93 | pass |
| landfall-token | 32 | pass |
| token-doubling-replacement | 32 | pass |
| counter-add-replacement | 30 | pass |
| graveyard-activated | 209 | pass |
| lifegain-counter | 37 | pass |
| opponent-draw-punisher | 10 | pass |
| creature-cost-reduction | 56 | pass |
| extra-turn | 65 | pass |
| free-cast-static | 58 | pass |
| saga-tutor-battlefield | 8 | pass |
| discard-cost-activated | 383 | pass |
| fetch-land-battlefield | 290 | pass |
| attack-token | 161 | pass |
| die-exile-replacement | 81 | pass |
Baseline = best-effort oracle-text regex (stand-in for Scryfall `o:` search).

## combat-damage-player-token  ✅

*Combat-damage-to-a-player trigger whose effect chain creates a token*

- structural hits: **101** (2 ms)
- goldens: present 3/3, absent-respected 3/3
- sample: A-Prosperous Thief, Ancient Copper Dragon, Ancient Gold Dragon, Ant-Man, Elusive Avenger, Aya of Alexandria, Battle Angels of Tyr, Beamtown Beatstick, Bejeweled Warg
- baseline regex `deals combat damage to a player[^.]*,[^.]*create`: 79 hits — agree 64, structural-only 37, regex-only 15
  - regex misses (structural found): ['A-Prosperous Thief', 'Ancient Copper Dragon', 'Ancient Gold Dragon', 'Battle Angels of Tyr', 'Bejeweled Warg']
  - regex extras (structural rejected): ['Bloodforged Battle-Axe', 'Calix, Guided by Fate', 'Commanding Presence', 'Conclave Evangelist', 'Donatello, Gadget Master']

## impulse-exile  ✅

*One ability chain both exiles from the library and grants may-play*

- structural hits: **268** (6 ms)
- goldens: present 4/4, absent-respected 2/2
- sample: A-Ardent Dustspeaker, A-Nashi, Moon Sage's Scion, A-Visions of Phyrexia, Abbot of Keral Keep, Act on Impulse, Aerial Caravan, Alania's Pathmaker, Aminatou's Augury
- baseline regex `exile the top [^.]*librar[^.]*\.[^.]*may (play|cast)`: 238 hits — agree 190, structural-only 78, regex-only 48
  - regex misses (structural found): ["Aminatou's Augury", "Archaic's Agony", 'Black Cat, Cunning Thief', 'Blightwing Bandit', 'Bloodsoaked Insight']
  - regex extras (structural rejected): ['Anep, Vizier of Hazoret', 'Bard Class', 'Boomer Scrapper', 'Break Down', 'C.A.M.P.']

## sac-creature-cost-mana  ✅

*Activated ability: sacrificing a creature in the cost, mana in the effect*

- structural hits: **34** (60 ms)
- goldens: present 3/3, absent-respected 2/2
- sample: Ashnod's Altar, Basal Sliver, Basal Thrull, Blood Pet, Blood Vassal, Catalyst Elemental, Coal Golem, Composite Golem
- baseline regex `sacrifice [^.:]*creature[^.:]*: add`: 70 hits — agree 11, structural-only 23, regex-only 59
  - regex misses (structural found): ['Basal Sliver', 'Basal Thrull', 'Blood Pet', 'Blood Vassal', 'Catalyst Elemental']
  - regex extras (structural rejected): ['Abstruse Interference', 'Adverse Conditions', 'Awakening Zone', 'Basking Broodscale', 'Birthing Hulk']

## etb-drain-each-opponent  ✅

*ETB trigger draining each opponent (they lose life, you gain) in one chain*

- structural hits: **24** (3 ms)
- goldens: present 1/1, absent-respected 2/2
- sample: A-Cauldron Familiar, Arbiter of Woe, Arrogant Outlaw, Ayara, First of Locthwain, Cauldron Familiar, Corroding Dragonstorm, Dawnhand Eulogist, Diregraf Scavenger

## dies-token  ✅

*Self-dies trigger that creates token(s)*

- structural hits: **167** (12 ms)
- goldens: present 2/2, absent-respected 2/2
- sample: A-Hobbling Zombie, Adorned Crocodile, Agents of HYDRA, Ambitious Augmenter, Anax, Hardened in the Forge, Ancient Adamantoise, Ancient Stone Idol, Atsushi, the Blazing Sky
- baseline regex `when (this creature|[A-Z][^ ]*) dies[^.]*create`: 42 hits — agree 24, structural-only 143, regex-only 18
  - regex misses (structural found): ['A-Hobbling Zombie', 'Anax, Hardened in the Forge', 'Ancient Stone Idol', 'Atsushi, the Blazing Sky', 'Bant Sojourners']
  - regex extras (structural rejected): ['Chronozoa', 'Clavileño, First of the Blessed', "Debtors' Transport", 'Diabolical Salvation', 'Fake Your Own Death']

## cast-copy-trigger  ✅

*Trigger on casting a spell that copies the spell*

- structural hits: **93** (1 ms)
- goldens: present 2/2, absent-respected 2/2
- sample: A-Leyline of Resonance, A-Mentor's Guidance, Alania, Divergent Storm, Ancestral Communion, Archmage of Echoes, Aziza, Mage Tower Captain, Banish into Fable, Beamsplitter Mage

## landfall-token  ✅

*Landfall trigger (land you control enters) that creates a token*

- structural hits: **32** (8 ms)
- goldens: present 3/3, absent-respected 2/2
- sample: Akoum Stonewaker, Chocobo Racetrack, Curse of the Restless Dead, Dancing from Dark to Dawn, Dragonback Assault, Elfsworn Giant, Emeria Angel, Eusocial Engineering

## token-doubling-replacement  ✅

*Replacement effect modifying token creation*

- structural hits: **32** (1 ms)
- goldens: present 3/3, absent-respected 2/2
- sample: Academy Manufactor, Adrix and Nev, Twincasters, Anointed Procession, Bard, King of Dale, Bilbo, Fellow Conspirator, Bloodspatter Vampire, Case of the Pilfered Proof, Chatterfang, Squirrel General
- baseline regex `create (twice|two times|that many)[^.]*token`: 67 hits — agree 5, structural-only 27, regex-only 62
  - regex misses (structural found): ['Academy Manufactor', 'Adrix and Nev, Twincasters', 'Anointed Procession', 'Bard, King of Dale', 'Bilbo, Fellow Conspirator']
  - regex extras (structural rejected): ['Angelic Aberration', 'Ant-Man, Elusive Avenger', 'Arco-Flagellant', 'Basri Ket', 'Bottle-Cap Blast']

## counter-add-replacement  ✅

*Replacement effect modifying counters being put on permanents*

- structural hits: **30** (0 ms)
- goldens: present 3/3, absent-respected 1/1
- sample: Aether Refinery, Benevolent Hydra, Branching Evolution, Caradora, Heart of Alacria, Conclave Mentor, Corpsejack Menace, Doc Samson, Super Psychiatrist, Doubling Season

## graveyard-activated  ✅

*Activated ability usable only from the graveyard*

- structural hits: **209** (2 ms)
- goldens: present 2/2, absent-respected 2/2
- sample: A-Cauldron Familiar, A-Cobbled Lancer, A-Earthquake Dragon, A-Llanowar Greenwidow, A-Narfi, Betrayer King, Abzan Devotee, Adorned Crocodile, Advanced Stitchwing

## lifegain-counter  ✅

*Lifegain trigger that puts +1/+1 counters*

- structural hits: **37** (1 ms)
- goldens: present 3/3, absent-respected 1/1
- sample: A-Vampire Scrivener, Aerith Gainsborough, Ageless Entity, Ajani's Pridemate, Blood Researcher, Bloodbond Vampire, Bloodthirsty Aerialist, Celestial Unicorn
- baseline regex `whenever you gain life[^.]*\+1/\+1 counter`: 44 hits — agree 33, structural-only 4, regex-only 11
  - regex misses (structural found): ['Cradle of Vitality', 'Heroic Feast', 'Kavu Predator', 'Serene Steward']
  - regex extras (structural rejected): ['Ajani Resolute', 'Ajani, Strength of the Pride', 'Archangel of Thune', 'Blech, Loafing Pest', 'Citizen V, Helmut Zemo']

## opponent-draw-punisher  ✅

*Trigger on an opponent drawing that costs them life / deals damage*

- structural hits: **10** (2 ms)
- goldens: present 2/2, absent-respected 2/2
- sample: A-Orcish Bowmasters, Fate Unraveler, Kederekt Parasite, Nekusar, the Mindrazer, Ob Nixilis, the Hate-Twisted, Orcish Bowmasters, Razorkin Needlehead, Scrawling Crawler

## creature-cost-reduction  ✅

*Static ability reducing the cost of creature spells*

- structural hits: **56** (4 ms)
- goldens: present 2/2, absent-respected 1/1
- sample: Agatha of the Vile Cauldron, Animar, Soul of Elements, Artist's Talent, Biomancer's Familiar, Blood Funnel, Bontu's Monument, Centaur Omenreader, Conduit of Ruin

## extra-turn  ✅

*Any ability granting an extra turn*

- structural hits: **65** (0 ms)
- goldens: present 3/3, absent-respected 1/1
- sample: A-Alrund's Epiphany, Aetherflux Car, Alchemist's Gambit, All in Good Time, Alrund's Epiphany, Avatar Kuruk, Beacon of Tomorrows, Capture of Jingzhou
- baseline regex `extra turn`: 67 hits — agree 64, structural-only 1, regex-only 3
  - regex misses (structural found): ['Urza, Academy Headmaster']
  - regex extras (structural rejected): ["Gerrard's Hourglass Pendant", 'Stranglehold', 'Trouble in Pairs']

## free-cast-static  ✅

*Static allowing casting without paying mana costs*

- structural hits: **58** (1 ms)
- goldens: present 1/1, absent-respected 1/1
- sample: A-Fires of Invention, Aluren, Aminatou's Augury, Apex Observatory, Casey & Raph, Hotheads, Caves of Chaos Adventurer, Chandra, Flame's Catalyst, Codie, Vociferous Codex

## saga-tutor-battlefield  ✅

*Saga whose chapter chain fetches from library to battlefield*

- structural hits: **8** (2 ms)
- goldens: present 1/1, absent-respected 1/1
- sample: Binding the Old Gods, Fugitive of the Judoon, Summon: Fenrir, The Hunger Tide Rises, The Legend of Arena, The Weatherseed Treaty, There and Back Again, Urza's Saga

## discard-cost-activated  ✅

*Activated ability with discarding a card in the cost*

- structural hits: **383** (31 ms)
- goldens: present 2/2, absent-respected 2/2
- sample: A-Mishra, Excavation Prodigy, A-Soul of Windgrace, Action News Crew, Advanced Stitchwing, Aeromoeba, Alexi, Zephyr Mage, Altanak, the Thrice-Called, Amok

## fetch-land-battlefield  ✅

*Spell or ETB chain searching a land from library onto the battlefield*

- structural hits: **290** (17 ms)
- goldens: present 4/4, absent-respected 2/2
- sample: A-Navigation Orb, A-Scout the Wilderness, Aerial Surveyor, Alpine Guide, Arid Mesa, Assassin's Trophy, Atalan Jackal, Avatar of Growth

## attack-token  ✅

*Attack trigger that creates token(s)*

- structural hits: **161** (2 ms)
- goldens: present 2/2, absent-respected 2/2
- sample: A-Acererak the Archlich, A-Goldspan Dragon, A-Rulik Mons, Warren Chief, Aang and Katara, Acererak the Archlich, Aether Chaser, Aether Herder, Aether Inspector

## die-exile-replacement  ✅

*Replacement sending cards to exile instead of the graveyard*

- structural hits: **81** (2 ms)
- goldens: present 1/1, absent-respected 1/1
- sample: A-Brinebound Gift, A-Catlike Curiosity, A-Departed Soulkeeper, A-Dorothea's Retribution, A-Etching of Kumano, A-Gutter Shortcut, A-Lanterns' Lift, A-Spectral Binding

