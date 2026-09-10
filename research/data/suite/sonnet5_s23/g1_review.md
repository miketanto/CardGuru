# Decision review — g1.jsonl

Result: **pilot lost** in 12 turns. 16 real decisions out of 141 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Strong keepable hand: 3 lands (2 untapped colors covered) plus a great curve of Sheoldred, two Preacher of the Schism, and Floodpits Drowner. All castable with these colors and good threats."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they do nothing: us 20 vs 20; pass (hold everything) | s1: they do nothing: us 20 vs 20; pass (hold everything) | s2: they do nothing: us 20 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they do nothing: us 20 vs 20; Play Darkslick Shores | s1: they do nothing: us 20 vs 20; Play Darkslick Shores | s2: they do nothing: us 20 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they do nothing: us 20 vs 20; Play Island | s1: they do nothing: us 20 vs 20; Play Island | s2: they do nothing: us 20 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they do nothing: us 20 vs 20; Play Swamp | s1: they do nothing: us 20 vs 20; Play Swamp | s2: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Playing Darkslick Shores now while I control 0 other lands guarantees it enters untapped, banking the dual land's flexibility; Island/Swamp are fine but waste the free untapped dual-land window since Darkslick only enters untapped with two or fewer other lands."

## Turn 1 — Postcombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they do nothing: us 20 vs 20; pass (hold everything) | s1: they do nothing: us 20 vs 20; pass (hold everything) | s2: they do nothing: us 20 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they do nothing: us 20 vs 20; Play Darkslick Shores | s1: they do nothing: us 20 vs 20; Play Darkslick Shores | s2: they do nothing: us 20 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they do nothing: us 20 vs 20; Play Island | s1: they do nothing: us 20 vs 20; Play Island | s2: they do nothing: us 20 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they do nothing: us 20 vs 20; Play Swamp | s1: they do nothing: us 20 vs 20; Play Swamp | s2: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Still haven't played a land this turn; playing Darkslick Shores now locks in the untapped dual while I control 0 other lands."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; Play Darkslick Shores | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Darkslick Shores | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; Play Island | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Island | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; Play Swamp | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Swamp | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Still no land in play — need to fix mana now. Darkslick Shores enters untapped while I control two or fewer other lands (true here), and gives me both colors for upcoming Preacher/Sheoldred casts, so it's the best land to play first."

## Turn 3 — Postcombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Darkslick Shores | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Darkslick Shores | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Island | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; Play Island | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Play Swamp | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Swamp | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Still no land in play this turn; play Darkslick Shores now while it enters untapped (2 or fewer other lands) to fix mana and keep both colors open."

## Turn 3 — Cleanup [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Menu: [0] Preacher of the Schism; [1] Floodpits Drowner; [2] Darkslick Shores; [3] Island; [4] Preacher of the Schism; [5] Sheoldred, the Apocalypse; [6] Swamp; [7] Enduring Curiosity
- **Chose: target Preacher of the Schism**
- Pilot's reasoning: "Discarding to hand size with 0 lands in play — must keep all 3 lands plus my unique threats (Sheoldred, Floodpits Drowner, Enduring Curiosity). The two Preacher of the Schism copies are redundant, so cut one and keep the other."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20; pass (hold everything) | s1: they cast Cast Anoint with Affliction | I do nothing: us 19 vs 20; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Play Darkslick Shores | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; Play Darkslick Shores | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 20; Play Island | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; Play Island | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast Cast Anoint with Affliction | I do nothing: us 19 vs 20; Play Swamp | s1: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Play Swamp | s2: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; Play Island | s1: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Play Island | s2: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Still 0 lands in play at turn 5 — this is urgent. Play Darkslick Shores now while it can still enter untapped (0 other lands) to finally get mana online and keep both colors available for Preacher/Sheoldred."

## Turn 5 — Postcombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; pass (hold everything) | s2: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Play Darkslick Shores | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; Play Darkslick Shores | s2: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; Play Island | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; Play Island | s2: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Play Swamp | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; Play Swamp | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Play Island | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20; Play Island | s2: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Same postcombat main, still no land in play — keep pushing to play Darkslick Shores untapped while I control 0 other lands, to finally get mana online."

## Turn 5 — Cleanup [choose]
- Life: pilot **19** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Menu: [0] Floodpits Drowner; [1] Darkslick Shores; [2] Island; [3] Preacher of the Schism; [4] Sheoldred, the Apocalypse; [5] Swamp; [6] Enduring Curiosity; [7] Island
- **Chose: target Island**
- Pilot's reasoning: "Still 0 lands in play — keep all unique spells (Sheoldred, Preacher, Floodpits Drowner, Enduring Curiosity) and enough land diversity. I have two Islands; discarding one keeps Darkslick Shores + Swamp + Island for both colors while trimming the redundant copy."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 16 vs 20; pass (hold everything) | s1: they cast Cast Anoint with Affliction | I do nothing: us 16 vs 20; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 16 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they cast Cast Anoint with Affliction | I do nothing: us 16 vs 20; Play Darkslick Shores | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 20; Play Darkslick Shores | s2: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20; Play Island | s1: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20; Play Island | s2: they cast Cast Faerie Mastermind | I do nothing: us 16 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast Cast Anoint with Affliction | I do nothing: us 16 vs 20; Play Swamp | s1: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast Cast Cut Down | I do nothing: us 16 vs 20; Play Swamp | s1: they cast Cast Cut Down | I do nothing: us 16 vs 20; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20)
- Pilot's reasoning: "Still stuck with 0 lands in play at turn 7 while taking damage each turn — must keep trying to land. Darkslick Shores still enters untapped (0 other lands) and gives flexible mana for both Preacher and Sheoldred."

## Turn 7 — Postcombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 20; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20; pass (hold everything) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20; Play Darkslick Shores | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20; Play Darkslick Shores | s2: they cast Cast Enduring Curiosity | I do nothing: us 16 vs 20)
    - `Play Island` scored **None** (Play Island | s0: they cast Cast Anoint with Affliction | I do nothing: us 16 vs 20; Play Island | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20; Play Island | s2: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 16 vs 20; Play Swamp | s1: they cast Cast Anoint with Affliction | I do nothing: us 16 vs 20; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20)
    - `Play Swamp` scored **None** (Play Swamp | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20; Play Swamp | s1: they cast Cast Go for the Throat | I do nothing: us 16 vs 20; Play Swamp | s2: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20)
- Pilot's reasoning: "Postcombat main, still no land in play. Keep pushing Darkslick Shores — enters untapped while I control 0 other lands, gives both colors I need."

## Turn 7 — Cleanup [choose]
- Life: pilot **16** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] Swamp; [1] Floodpits Drowner; [2] Darkslick Shores; [3] Island; [4] Preacher of the Schism; [5] Sheoldred, the Apocalypse; [6] Swamp; [7] Enduring Curiosity
- **Chose: target Swamp**
- Pilot's reasoning: "I realized my prior leaf_eval scores were malformed (one per candidate instead of one per leaf), which likely caused the engine to never actually play my land. Fixing that now. For this discard: I have 4 lands (2 Swamp, Island, Darkslick Shores) and 4 unique spells — trim the redundant second Swamp "

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **11** vs MAD **19**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **8** (pass (hold everything) | s0: they cast Cast Enduring Curiosity | I do nothing: us 11 vs 19; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 11 vs 19; pass (hold everything) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 11 vs 19)
    - `Play Darkslick Shores` scored **32** (Play Darkslick Shores | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Enduring Curiosity | I do nothing: us 11 vs 19; Play Darkslick Shores | they respond on the stack: Cast Anoint with Affliction | s1: they cast Cast Go for the Throat | I do nothing: us 11 vs 19; Play Darkslick Shores | they respond on the stack: Cast Go for the Throat | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 11 vs 19)
    - `Play Island` scored **20** (Play Island | they respond on the stack: Cast Cut Down | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 11 vs 19; Play Island | they respond on the stack: Cast Floodpits Drowner | s1: they cast Cast Preacher of the Schism | I do nothing: us 11 vs 19; Play Island | they respond on the stack: Cast Anoint with Affliction | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 11 vs 19)
    - `Play Swamp` scored **28** (Play Swamp | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 11 vs 19; Play Swamp | they respond on the stack: Cast Floodpits Drowner | s1: they cast Cast Go for the Throat | I do nothing: us 11 vs 19; Play Swamp | they respond on the stack: Cast Floodpits Drowner | after it resolves they cast: Cast Cut Down | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 11 vs 19)
- Pilot's reasoning: "Fixed scoring format: one score per leaf. Critical to finally land a permanent — turn 9, still 0 lands, life 11, opponent has a growing board. Darkslick Shores is the most flexible (both colors) and its worst-case leaf still beats every pass leaf, so it should win as the chosen action."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **4** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **8** (pass (hold everything) | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 4 vs 22; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22)
    - `Play Island` scored **15** (Play Island | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Island | s0: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; Play Island | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; Play Island | s1: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Island | s1: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Floodpits Drowner: us 2 vs 24; Play Island | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 2 vs 24; Play Island | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Island | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; Play Island | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22)
    - `Play Swamp` scored **30** (Play Swamp | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s0: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; Play Swamp | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22)
    - `Play Swamp` scored **15** (Play Swamp | s0: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s0: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Floodpits Drowner: us 2 vs 24; Play Swamp | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 2 vs 24; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Floodpits Drowner: us 2 vs 24; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 2 vs 24)
- Pilot's reasoning: "At 4 life, must play a land (economy) and strongly prefer flashing in Floodpits Drowner to get a blocker + stun one of their attackers before their crackback. Leaves where I hold Floodpits Drowner in hand and pass leave me with zero blockers against a lethal-capable board; leaves where their card-dr"

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **4** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 4 vs 22; pass (hold everything) | s2: they cast Cast Enduring Curiosity | on the stack I cast Cast Floodpits Drowner: us 4 vs 22; pass (hold everything) | s2: they cast Cast Enduring Curiosity | after it resolves I cast Cast Floodpits Drowner: us 4 vs 22; pass (hold everything) | s2: they cast Cast Enduring Curiosity | I do nothing: us 4 vs 22)
    - `Cast Floodpits Drowner` scored **40** (Cast Floodpits Drowner | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; Cast Floodpits Drowner | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 2 vs 24; Cast Floodpits Drowner | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 2 vs 24)
    - `Cast Deep-Cavern Bat` scored **28** (Cast Deep-Cavern Bat | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 2 vs 24; Cast Deep-Cavern Bat | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 4 vs 22; Cast Deep-Cavern Bat | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 2 vs 24)
- Pilot's reasoning: "Casting Floodpits Drowner now (before their turn) taps and stuns their biggest threat — Sheoldred stays tapped through their untap step and can't attack turn 12 — while Floodpits Drowner itself remains untapped as a blocker for something else. That neutralizes my single biggest lethal threat proacti"

## Turn 11 — Precombat Main [target]
- Life: pilot **4** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Menu: [0] Spyglass Siren 1/1 (B); [1] Faerie Mastermind 2/1 (B); [2] Preacher of the Schism 2/4 (B); [3] Sheoldred, the Apocalypse 4/5 (B)
- **Chose: target Sheoldred, the Apocalypse 4/5 (B)**
- Pilot's reasoning: "Target Sheoldred, the Apocalypse — it's their biggest threat (4/5 deathtouch) and the stun counter keeps it tapped through their next untap step, taking it out of their attack entirely at 4 life where any unblocked big hit kills me."
