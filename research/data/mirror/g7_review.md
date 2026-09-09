# Decision review — g7.jsonl

Result: **pilot won** in 27 turns. 108 real decisions out of 397 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Undercity Sewers, Kaito, Bane of Nightmares, Cut Down, Sheoldred, the Apocalypse, Deep-Cavern Bat, Faerie Mastermind, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: MULLIGAN**
- Pilot's reasoning: "Only one land (Undercity Sewers) in the opening 7, despite strong spells (Sheoldred, Kaito, removal). A one-land hand is too big a risk of getting stuck; need a functional mana base."

## Turn 1 — null [target]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Menu: [0] Restless Reef; [1] Swamp; [2] Island; [3] Deep-Cavern Bat; [4] Go for the Throat; [5] Floodpits Drowner; [6] Island
- **Chose: target Island**
- Pilot's reasoning: "Keeping 6: bottoming one Island since 4 lands among 7 cards is land-heavy. Remaining 3 lands (Island, Restless Reef, Swamp) cover both U and B for Go for the Throat, Deep-Cavern Bat, and Floodpits Drowner."

## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "3 lands covering both colors plus removal, a disruptive flyer, and a flash tempo creature is a solid, keepable 6-card hand."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **65** (Play Island: us 20 vs 20)
    - `Play Restless Reef` scored **95** (Play Restless Reef: us 20 vs 20)
    - `Play Swamp` scored **65** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Turn 1 nothing costs 1 mana in hand, so the right sequencing is to play the tapped land (Restless Reef) now while it costs nothing, saving untapped Island/Swamp for later turns when we need live mana."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **90** (Play Island: us 20 vs 20)
    - `Play Swamp` scored **92** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Either basic enables casting Deep-Cavern Bat this turn via Restless Reef's flexible mana; slightly prefer Swamp since my hand is black-heavy (2x Bat, Go for the Throat) while keeping Island in reserve for Floodpits Drowner later. Passing wastes a land drop and this turn's tempo."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **92** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **35** (Cast Floodpits Drowner: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **92** (Cast Deep-Cavern Bat: us 20 vs 20)
- Pilot's reasoning: "Deep-Cavern Bat gives huge value now (hand info + exile their best card + lifelink flyer), while Floodpits Drowner's tap-down ETB is wasted with no enemy creature to target — better to flash it in later when it can actually stun something. Passing wastes tempo turn 2."

## Turn 3 — Precombat Main [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 2 lands (0 untapped)
- Pilot hand: Island, Go for the Throat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Menu: [0] Kaito, Bane of Nightmares; [1] Deep-Cavern Bat; [2] Floodpits Drowner; [3] Floodpits Drowner; [4] Kaito, Bane of Nightmares
- **Chose: target Kaito, Bane of Nightmares**
- Pilot's reasoning: "Their hand has two copies of Kaito, Bane of Nightmares, by far the most powerful and hardest-to-remove card here (hexproof 3/4 ninja on their turn). Exiling one strips their best draw, even though they'll still have a second copy."

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Island, Go for the Throat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **82** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Their Floodpits Drowner is just a summoning-sick 2/1 now (its tap ability already used on my Bat) — not worth Go for the Throat. Flashing in my own Floodpits Drowner to tap+stun theirs clears the way for my Bat to attack unblocked and gives me a vigilant blocker; passing to reassess after draw is al"

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Pilot hand: Island, Go for the Throat, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **90** (Play Island: us 20 vs 20)
- Pilot's reasoning: "Nothing to attack with this turn (Bat is stunned/tapped, Drowner is summoning sick) and no other play available, so just take the land drop to keep developing mana for future turns — no reason to skip it."

## Turn 7 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped) | 3 lands (3 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **20** (Cast Go for the Throat: us 20 vs 20)
- Pilot's reasoning: "Their board is just two vanilla 2/1 Floodpits Drowners - not worth spending premium removal on. Better to hold Go for the Throat for a real threat like Sheoldred, Preacher of the Schism, or Kaito."

## Turn 7 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped) | 3 lands (3 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat, Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **20** (Cast Go for the Throat: us 20 vs 20)
- Pilot's reasoning: "Same read as before - their board is only two vanilla 2/1 Floodpits Drowners, not worth Go for the Throat. Better to wait for a real threat."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped) | 3 lands (3 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat, Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **65** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **65** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Play Swamp` scored **None** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Playing Swamp first is free value with no downside and unlocks more mana for later plays this turn; casting a Deep-Cavern Bat for more disruption/lifelink is also good but slightly less urgent than securing the land drop. Go for the Throat is still wasted on their vanilla 2/1s."

## Turn 7 — Precombat Main [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped) | 3 lands (3 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat, Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] Cast Deep-Cavern Bat; [3] Cast Deep-Cavern Bat; [4] Play Swamp; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.
- **Chose: Play Swamp**
- Pilot's reasoning: "Play the land drop first (free, no downside) before committing mana to a spell this turn."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped) | 4 lands (4 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **20** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **78** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **78** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 20 vs 20)
- Pilot's reasoning: "Casting a second Deep-Cavern Bat gives more hand disruption, lifelink pressure, and a future attacker at minimal risk. Animating Restless Reef into a 4/4 taps out all mana and risks losing a land permanently to a trade or removal, for no real gain against their small board. Go for the Throat is stil"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped) | 4 lands (2 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **20** (Cast Go for the Throat: us 20 vs 20)
- Pilot's reasoning: "Still nothing worth Go for the Throat - both their creatures are vanilla 2/1s. Hold it for a real threat like Sheoldred/Preacher/Kaito, and keep the last Deep-Cavern Bat in hand for future value."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 4 lands (2 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **20** (Cast Go for the Throat: us 20 vs 20)
- Pilot's reasoning: "Same read as before - their two Floodpits Drowners are still just vanilla 2/1s, not worth premium removal."

## Turn 7 — Precombat Main [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 4 lands (2 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Menu: [0] Go for the Throat; [1] Deep-Cavern Bat; [2] Kaito, Bane of Nightmares
- **Chose: target Kaito, Bane of Nightmares**
- Pilot's reasoning: "Exile Kaito, Bane of Nightmares - a hexproof 3/4 ninja on their turn that generates emblems and stuns our creatures, far more dangerous than their own Go for the Throat or a vanilla Bat."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 4 lands (2 untapped)
- Pilot hand: Go for the Throat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **75** (Cast Deep-Cavern Bat: us 20 vs 20)
- Pilot's reasoning: "Deploying the second Deep-Cavern Bat now gives more hand disruption and another lifelink flyer while their board is just two vanilla 2/1s - low risk to tap out. Go for the Throat is still not worth using on their small creatures."

## Turn 7 — Precombat Main [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick), Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Pilot hand: Go for the Throat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Menu: [0] Go for the Throat; [1] Deep-Cavern Bat
- **Chose: target Go for the Throat**
- Pilot's reasoning: "Exile their Go for the Throat - removing their only interaction/removal spell protects my board of Bats and Drowner from being answered, since their Deep-Cavern Bat is comparatively low-impact."

## Turn 7 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick), Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Pilot hand: Go for the Throat
- MAD board: Floodpits Drowner 2/1 (tapped), Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **20** (unblocked: us 20 vs 20)
    - `attack-all` scored **90** (unblocked: us 21 vs 19)
- Pilot's reasoning: "My non-sick Deep-Cavern Bat is a 1/1 flyer with lifelink and they have no flying blockers; attacking is free damage and life gain with no risk since it's unblockable by their ground creatures."

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **21** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick), Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Pilot hand: empty
- MAD board: Floodpits Drowner 2/1, Floodpits Drowner 2/1, Deep-Cavern Bat 1/1 (sick) | 4 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **30** (after combat: us 17 vs 19)
    - `Deep-Cavern Bat>Floodpits Drowner` scored **65** (after combat: us 20 vs 19)
    - `Deep-Cavern Bat>Floodpits Drowner` scored **65** (after combat: us 20 vs 19)
    - `Deep-Cavern Bat>Floodpits Drowner` scored **65** (after combat: us 20 vs 19)
    - `Deep-Cavern Bat>Floodpits Drowner` scored **65** (after combat: us 20 vs 19)
    - `Deep-Cavern Bat>Floodpits Drowner, Deep-Cavern Bat>Floodpits Drowner` scored **96** (after combat: us 23 vs 19)
    - `Deep-Cavern Bat>Floodpits Drowner, Deep-Cavern Bat>Floodpits Drowner` scored **35** (after combat: us 21 vs 19)
- Pilot's reasoning: "Double-blocking each Floodpits Drowner with a Deep-Cavern Bat trades two summoning-sick 1/1s (which can't attack this turn anyway) for both of their 2/1 attackers, gains 2 life from lifelink, and takes zero combat damage - a clearly excellent trade that wipes their board down to just their own sick "

## Turn 9 — Upkeep [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 | 4 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 23 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **40** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 23 vs 19)
- Pilot's reasoning: "Animating Restless Reef now (upkeep) taps all mana before I've even drawn for turn - better to wait until precombat main after seeing what I draw, in case it's something worth casting instead of, or in addition to, attacking with the land."

## Turn 9 — Draw [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 23 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 23 vs 19)
- Pilot's reasoning: "Drew Preacher of the Schism - a strong 2/4 deathtouch value creature I want to cast this main phase. Animating Restless Reef now would tap all 4 mana and prevent casting Preacher; better to hold mana and deploy the real permanent."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 23 vs 19)
    - `Cast Preacher of the Schism` scored **90** (Cast Preacher of the Schism: us 23 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 23 vs 19)
- Pilot's reasoning: "Casting Preacher of the Schism deploys a 2/4 deathtouch value engine (draws cards / makes tokens while attacking) - much better long-term value than temporarily animating Restless Reef, and still leaves 1 mana up."

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 23 vs 19)
    - `attack-all` scored **78** (1 block(s), response 1: us 24 vs 20; unblocked: us 24 vs 18)
- Pilot's reasoning: "Attacking with the Bat is safe: worst case is a 1-for-1 trade of flying 1/1s with mutual lifelink (net neutral), best case is unblocked lifelink damage. Preacher stays home as a blocker regardless since it's summoning sick."

## Turn 11 — Upkeep [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 23 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **25** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 23 vs 19)
- Pilot's reasoning: "Nothing to gain from animating Restless Reef now at upkeep before the draw step; better to wait and decide in main phase whether to animate it as an additional attacker alongside Preacher and Bat."

## Turn 11 — Draw [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Cut Down
- MAD board: Deep-Cavern Bat 1/1 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything): us 23 vs 19)
    - `Cast Cut Down` scored **88** (Cast Cut Down: us 23 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **25** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 23 vs 19)
- Pilot's reasoning: "Cut Down can only ever kill something ≤5 total power/toughness, and their Deep-Cavern Bat is exactly the kind of target it's built for - killing it now clears their only blocker/potential attacker before I swing with Bat and Preacher (which will trigger card draw and a lifelink token since I have th"

## Turn 11 — Draw [target]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 | 5 lands (1 untapped)
- Menu: [0] Deep-Cavern Bat 1/1 (A); [1] Deep-Cavern Bat 1/1 (B)
- **Chose: target Deep-Cavern Bat 1/1 (B)**
- Pilot's reasoning: "Destroy their Deep-Cavern Bat, clearing their only blocker before I attack with my Bat and Preacher of the Schism."

## Turn 11 — Draw [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **10** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "Opponent has zero creatures on board right now (their Bat is dead, Kaito isn't a creature on my turn) - nothing to target with Go for the Throat, so hold it for their next threat."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **10** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "No creatures on their board to target with Go for the Throat; hold it for their next threat."

## Turn 11 — Begin Combat [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **10** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "Still nothing to target; hold Go for the Throat."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **15** (unblocked: us 23 vs 0)
    - `attack-all` scored **100** (unblocked: us 24 vs 0)
    - `hold[Deep-Cavern Bat]` scored **40** (unblocked: us 23 vs 0)
    - `hold[Preacher of the Schism]` scored **40** (unblocked: us 24 vs 0)
- Pilot's reasoning: "Opponent has no blockers - attacking with both Deep-Cavern Bat and Preacher of the Schism for full unblocked damage (3 total) reduces them to 0 life, ending the game right now."

## Turn 11 — Declare Attackers [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 22 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 22 vs 19)
- Pilot's reasoning: "Opponent still has no creatures on board; hold Go for the Throat for their next threat."

## Turn 11 — Declare Attackers [leaf_eval/priority]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Darkslick Shores
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 22 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 22 vs 19)
- Pilot's reasoning: "No creatures on opponent's board; hold Go for the Throat for a real target."

## Turn 11 — Declare Blockers [leaf_eval/priority]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Darkslick Shores
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 22 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 22 vs 19)
- Pilot's reasoning: "No creatures to target on opponent's side; hold Go for the Throat."

## Turn 11 — Combat Damage [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Darkslick Shores
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "No creatures to target on opponent's side; hold Go for the Throat."

## Turn 11 — End Combat [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Darkslick Shores
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "No creatures to target; hold Go for the Throat for their next threat."

## Turn 11 — Postcombat Main [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Darkslick Shores
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 23 vs 19)
    - `Play Darkslick Shores` scored **85** (Play Darkslick Shores: us 23 vs 19)
- Pilot's reasoning: "Playing Darkslick Shores costs nothing and develops mana for future turns; still no creature to target with Go for the Throat so hold it."

## Turn 11 — Postcombat Main [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "Land already played; no creature on board to target with Go for the Throat. Hold it."

## Turn 11 — End Turn [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **15** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "No creatures to target with Go for the Throat; hold it."

## Turn 12 — Upkeep [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: Kaito, Bane of Nightmares 4/5 | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **5** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "Kaito is a 4/5 hexproof ninja during their turn (loyalty counters + emblem), so Go for the Throat cannot target it right now regardless. Hold removal for a window when it's vulnerable or for a different threat."

## Turn 12 — Draw [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: Kaito, Bane of Nightmares 4/5 | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **5** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "Kaito remains hexproof during their turn; nothing else to target. Hold Go for the Throat."

## Turn 12 — Precombat Main [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: Kaito, Bane of Nightmares 4/5 | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **5** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "Kaito remains hexproof on their turn (now 5/6 after another +1); nothing to target."

## Turn 12 — Precombat Main [leaf_eval/priority]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: Kaito, Bane of Nightmares 5/6, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 23 vs 19)
    - `Cast Go for the Throat` scored **85** (Cast Go for the Throat: us 23 vs 19)
- Pilot's reasoning: "Enduring Curiosity is a real target now (4/3, legal for Go for the Throat) - it would otherwise be a persistent blocker that trades favorably against my Preacher of the Schism (4 power kills my 4-toughness Preacher while my 2 power doesn't kill it) and generates ongoing card draw. Removing the creat"

## Turn 12 — Precombat Main [target]
- Life: pilot **23** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (3 untapped)
- Pilot hand: empty
- MAD board: Kaito, Bane of Nightmares 5/6, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Menu: [0] Preacher of the Schism 2/4 (A); [1] Deep-Cavern Bat 1/1 (A); [2] Enduring Curiosity 4/3 (B)
- **Chose: target Enduring Curiosity 4/3 (B)**
- Pilot's reasoning: "Destroy their Enduring Curiosity - it's a 4/3 that would trade favorably against my Preacher of the Schism and blocks well going forward."

## Turn 13 — Upkeep [leaf_eval/priority]
- Life: pilot **18** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: empty
- MAD board: no creatures | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 18 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 19)
- Pilot's reasoning: "It's still my upkeep before the draw step; passing now costs nothing since the opponent only has 1 untapped Swamp (no real interaction available) and I retain the option to animate Restless Reef in my main phase after I see my draw, with the same alpha-strike available (opponent has zero blockers: K"

## Turn 13 — Draw [leaf_eval/priority]
- Life: pilot **18** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: Undercity Sewers
- MAD board: no creatures | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 18 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 19)
- Pilot's reasoning: "Still just my draw step with a land (Undercity Sewers) in hand — no reason to commit mana to animating Restless Reef yet. I'll play my land and decide on animating Reef once in the main phase, with the same alpha-strike still available since the opponent has no blockers."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: Undercity Sewers
- MAD board: no creatures | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 18 vs 19)
    - `Play Undercity Sewers` scored **85** (Play Undercity Sewers: us 18 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **60** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 19)
- Pilot's reasoning: "Playing Undercity Sewers first is free value (extra land, surveil 1) and doesn't cost me anything since it enters tapped anyway — I can still animate Restless Reef afterward with a separate priority action before combat. No reason to skip the land drop."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: no creatures | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 18 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **90** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 19)
- Pilot's reasoning: "Opponent has zero blockers this turn (Kaito isn't a creature on my turn; Enduring Curiosity is a non-creature enchantment), so animating Restless Reef adds a free 4/4 deathtouch attacker with no risk — I have no cards in hand to protect and nothing better to spend mana on."

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **18** vs MAD **19**
- Pilot board: Restless Reef 4/4, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 5 lands (0 untapped)
- Pilot hand: empty
- MAD board: no creatures | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 18 vs 0)
    - `attack-all` scored **95** (unblocked: us 19 vs 0)
    - `hold[Restless Reef]` scored **60** (unblocked: us 19 vs 0)
    - `hold[Deep-Cavern Bat]` scored **55** (unblocked: us 18 vs 0)
    - `hold[Preacher of the Schism]` scored **60** (unblocked: us 19 vs 0)
- Pilot's reasoning: "Opponent has no blockers this turn (Kaito isn't a creature on my turn, Enduring Curiosity is inert), so attacking with everything is free value: Deep-Cavern Bat's lifelink nets extra life, Preacher of the Schism triggers its token/draw abilities, and Restless Reef mills them 4 — no reason to hold an"

## Turn 13 — Declare Attackers [target]
- Life: pilot **18** vs MAD **19**
- Pilot board: Restless Reef 4/4 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (tapped) | 5 lands (0 untapped)
- Pilot hand: empty
- MAD board: no creatures | 7 lands (2 untapped)
- Menu: [0] player A (life 18); [1] player B (life 19)
- **Chose: target player B (life 19)**
- Pilot's reasoning: "Mill the opponent, not myself — milling them toward decking out or losing key cards is pure upside with no downside to me."

## Turn 15 — Upkeep [leaf_eval/priority]
- Life: pilot **19** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: empty
- MAD board: Preacher of the Schism 2/4 (sick), Faerie Mastermind 2/1 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 19 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 19)
- Pilot's reasoning: "Still upkeep — no reason to commit mana to animating Restless Reef yet, especially now that the opponent has real blockers (their own Preacher 2/4 and Faerie Mastermind 2/1). I'll decide on attacks/animation once I see the situation in my main phase."

## Turn 15 — Draw [leaf_eval/priority]
- Life: pilot **19** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Preacher of the Schism 2/4 (sick), Faerie Mastermind 2/1 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 19 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 19)
- Pilot's reasoning: "Drew a second Preacher of the Schism; still just the draw step. No reason to commit mana to animating Restless Reef yet — I'll decide in the main phase after considering how to cast the new Preacher and plan attacks against their two blockers."

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Preacher of the Schism 2/4 (sick), Faerie Mastermind 2/1 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 19 vs 19)
    - `Cast Preacher of the Schism` scored **90** (Cast Preacher of the Schism: us 19 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 19)
- Pilot's reasoning: "Casting the second Preacher of the Schism is pure upside — a deathtouch blocker/future attacker for 2B, leaving 3 mana untapped, no downside since opponent only has 1 untapped mana (can't meaningfully interact)."

## Turn 15 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **19** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4, Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: empty
- MAD board: Preacher of the Schism 2/4 (sick), Faerie Mastermind 2/1 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **45** (unblocked: us 19 vs 19)
    - `attack-all` scored **55** (1 block(s), response 1: us 20 vs 18; 2 block(s), response 4: us 20 vs 19; unblocked: us 20 vs 16)
    - `hold[Deep-Cavern Bat]` scored **None** (1 block(s), response 1: us 19 vs 19; unblocked: us 19 vs 17; 1 block(s), response 2: us 19 vs 19)
    - `hold[Preacher of the Schism]` scored **None** (unblocked: us 20 vs 18; 1 block(s), response 1: us 20 vs 19)
- Pilot's reasoning: "Attacking with both Preacher of the Schism and Deep-Cavern Bat guarantees Preacher's attack triggers (token creation + card draw, since life is tied) regardless of blocks, and even in the worst case (both attackers traded away) it clears their entire board including the annoying Faerie Mastermind ca"

## Turn 16 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4, Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: empty
- MAD board: Preacher of the Schism 2/4 (tapped), Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (8 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **55** (after combat: us 16 vs 18)
    - `Preacher of the Schism>Preacher of the Schism` scored **85** (after combat: us 18 vs 18)
    - `Preacher of the Schism>Preacher of the Schism` scored **85** (after combat: us 18 vs 18)
    - `Preacher of the Schism>Preacher of the Schism, Preacher of the Schism>Preacher of the Schism` scored **30** (after combat: us 18 vs 18)
- Pilot's reasoning: "Faerie Mastermind is flying and unblockable this turn (my Bat is tapped), so its 2 damage is unavoidable regardless. Single-blocking their Preacher of the Schism with one of mine trades evenly (both deathtouch, mutual kill) and removes their creature while preventing 2 more damage — clearly better t"

## Turn 16 — Postcombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 18 vs 18)
    - `Cast Go for the Throat` scored **45** (Cast Go for the Throat: us 18 vs 18)
- Pilot's reasoning: "Go for the Throat is best saved for a bigger threat (Sheoldred, Enduring Curiosity, Kaito, etc.) rather than spent on a tapped 2/1 Faerie Mastermind that poses no immediate threat — Mastermind's card-draw trigger is already a sunk cost this turn and it's not attacking or blocking anything of mine ri"

## Turn 16 — Postcombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 18 vs 18)
    - `Cast Go for the Throat` scored **45** (Cast Go for the Throat: us 18 vs 18)
- Pilot's reasoning: "Still holding Go for the Throat for a bigger threat; Faerie Mastermind remains tapped and non-threatening right now. My Deep-Cavern Bat died to their Cut Down, but that doesn't change the calculus on saving removal for a real target (Sheoldred, Enduring Curiosity, Kaito, etc.)."

## Turn 16 — End Turn [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: Go for the Throat
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 18 vs 18)
    - `Cast Go for the Throat` scored **45** (Cast Go for the Throat: us 18 vs 18)
- Pilot's reasoning: "Still end of their turn; nothing new has changed the calculus — holding Go for the Throat for a bigger threat remains correct since Faerie Mastermind is tapped and non-threatening."

## Turn 17 — Upkeep [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Go for the Throat
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 18 vs 18)
    - `Cast Go for the Throat` scored **45** (Cast Go for the Throat: us 18 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 18)
- Pilot's reasoning: "Still my upkeep — no reason to commit to animating Reef or spending Go for the Throat yet. I'll decide attacks in my main phase, noting Faerie Mastermind is still tapped from their attack and can't block this turn."

## Turn 17 — Draw [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Go for the Throat, Enduring Curiosity
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 18 vs 18)
    - `Cast Go for the Throat` scored **40** (Cast Go for the Throat: us 18 vs 18)
    - `Cast Enduring Curiosity` scored **55** (Cast Enduring Curiosity: us 18 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **50** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 18)
- Pilot's reasoning: "Still just the draw step — no reason to lock in Enduring Curiosity, Go for the Throat, or Reef's animation yet. I have 6 mana available and want to sequence carefully in the main phase (e.g., Enduring Curiosity + Go for the Throat together fit in 6 mana, or hold Curiosity's flash for a surprise bloc"

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Go for the Throat, Enduring Curiosity
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 18 vs 18)
    - `Cast Go for the Throat` scored **88** (Cast Go for the Throat: us 18 vs 18)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 18 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 18)
- Pilot's reasoning: "With 6 mana available, the best sequence is Go for the Throat now on Faerie Mastermind (removing their only real threat and stopping the card-draw trigger for good) — that still leaves 4 mana to animate Restless Reef afterward for a big attack (Reef 4/4 + Preacher 2/4 into just a summoning-sick 1/1 "

## Turn 17 — Precombat Main [target]
- Life: pilot **18** vs MAD **18**
- Pilot board: Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Menu: [0] Vampire Token 1/1 (B); [1] Preacher of the Schism 2/4 (A); [2] Faerie Mastermind 2/1 (B)
- **Chose: target Faerie Mastermind 2/1 (B)**
- Pilot's reasoning: "Faerie Mastermind is their real threat — a flash flying evasive creature with an ongoing card-advantage engine; the Vampire Token is harmless and my own Preacher isn't a legal target I'd want anyway."

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Preacher of the Schism 2/4 | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything): us 18 vs 18)
    - `Cast Enduring Curiosity` scored **55** (Cast Enduring Curiosity: us 18 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **88** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 18 vs 18)
- Pilot's reasoning: "Animating Restless Reef converts my remaining mana into immediate damage — attacking with a 4/4 deathtouch Reef plus my Preacher into their lone summoning-sick 1/1 Vampire Token forces either a bad chump block or 6 unblocked damage. Enduring Curiosity can wait; it's better used later (flash blocker "

## Turn 17 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **18** vs MAD **18**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 | 5 lands (0 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 18 vs 18)
    - `attack-all` scored **92** (unblocked: us 18 vs 16; 1 block(s), response 1: us 18 vs 19)
- Pilot's reasoning: "Attacking with both Reef and Preacher forces a bad choice for them: either take 6 damage or chump-block one attacker with their only creature (a summoning-sick 1/1). Even worst case, my board stays intact and I lose no creatures."

## Turn 17 — Postcombat Main [leaf_eval/priority]
- Life: pilot **17** vs MAD **16**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 5 lands (0 untapped)
- Pilot hand: Enduring Curiosity, Darkslick Shores
- MAD board: Vampire Token 1/1 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 17 vs 16)
    - `Play Darkslick Shores` scored **85** (Play Darkslick Shores: us 17 vs 16)
- Pilot's reasoning: "Playing Darkslick Shores is free value — an extra land for future turns with zero downside, since I have no more mana to use this turn anyway."

## Turn 19 — Upkeep [leaf_eval/priority]
- Life: pilot **16** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 | 7 lands (7 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 10 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 16 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 16 vs 17)
- Pilot's reasoning: "Still my upkeep — no reason to commit mana to animating Restless Reef yet. I'll assess my main phase options once I draw, noting Kaito is on their board as a planeswalker (not a creature during my turn) and they now have a Deep-Cavern Bat blocker."

## Turn 19 — Draw [leaf_eval/priority]
- Life: pilot **16** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 | 7 lands (7 untapped)
- Pilot hand: Floodpits Drowner
- MAD board: Vampire Token 1/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 10 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 16 vs 17)
    - `Cast Floodpits Drowner` scored **55** (Cast Floodpits Drowner: us 16 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **60** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 16 vs 17)
- Pilot's reasoning: "Drew Floodpits Drowner — still just the draw step, so no need to commit to animating Reef yet. Casting Floodpits Drowner in the main phase to tap+stun their Deep-Cavern Bat (their only blocker) before attacking would clear the way for a bigger hit."

## Turn 19 — Precombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 | 7 lands (7 untapped)
- Pilot hand: Floodpits Drowner
- MAD board: Vampire Token 1/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 10 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 16 vs 17)
    - `Cast Floodpits Drowner` scored **88** (Cast Floodpits Drowner: us 16 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 16 vs 17)
- Pilot's reasoning: "Casting Floodpits Drowner now taps and stuns their only blocker (Deep-Cavern Bat), clearing the way for a full attack, while adding a vigilant body to my board. This only costs 2 mana, leaving 5 more to animate Restless Reef afterward for a huge swing."

## Turn 19 — Precombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 | 7 lands (5 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 10 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything): us 16 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **88** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 16 vs 17)
- Pilot's reasoning: "Animate Restless Reef with the remaining mana for a big combined attack with Preacher of the Schism — even if Deep-Cavern Bat can still block one attacker, deathtouch trades favorably and Reef still gets through for heavy damage."

## Turn 19 — Precombat Main [target]
- Life: pilot **16** vs MAD **17**
- Pilot board: Restless Reef 4/4, Preacher of the Schism 2/4, Floodpits Drowner 2/1 (sick) | 6 lands (0 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 10 lands (3 untapped)
- Menu: [0] Deep-Cavern Bat 1/1 (B); [1] Vampire Token 1/1 (B)
- **Chose: target Deep-Cavern Bat 1/1 (B)**
- Pilot's reasoning: "Stun and tap their Deep-Cavern Bat — their only untapped blocker — clearing the way for my attack; their Vampire Token is already tapped and irrelevant."

## Turn 19 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **16** vs MAD **17**
- Pilot board: Restless Reef 4/4, Preacher of the Schism 2/4, Floodpits Drowner 2/1 (sick) | 6 lands (0 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 10 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **40** (unblocked: us 16 vs 17)
    - `attack-all` scored **95** (unblocked: us 16 vs 11)
    - `hold[Restless Reef]` scored **55** (unblocked: us 16 vs 15)
    - `hold[Preacher of the Schism]` scored **60** (unblocked: us 16 vs 13)
- Pilot's reasoning: "Opponent has zero available blockers (Vampire Token and Deep-Cavern Bat both tapped), so attacking with everything guarantees 6 unblocked damage with no risk to my board."

## Turn 19 — Declare Attackers [target]
- Life: pilot **16** vs MAD **17**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1 (sick) | 6 lands (0 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 10 lands (3 untapped)
- Menu: [0] player A (life 16); [1] player B (life 17)
- **Chose: target player B (life 17)**
- Pilot's reasoning: "Mill the opponent, not myself — pure upside toward decking them out or stripping key cards."

## Turn 20 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **16** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1 (sick), Vampire Token 1/1 (sick) | 7 lands (0 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1, Kaito, Bane of Nightmares 7/8 (tapped), Deep-Cavern Bat 1/1 (tapped) | 10 lands (9 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **30** (after combat: us 9 vs 11)
    - `Floodpits Drowner>Kaito, Bane of Nightmares` scored **55** (after combat: us 16 vs 11)
    - `Vampire Token>Kaito, Bane of Nightmares` scored **88** (after combat: us 17 vs 11)
    - `Floodpits Drowner>Kaito, Bane of Nightmares, Vampire Token>Kaito, Bane of Nightmares` scored **45** (after combat: us 17 vs 11)
- Pilot's reasoning: "Blocking with the Vampire Token alone absorbs Kaito's full 7 damage while its lifelink triggers on the block damage dealt, netting +1 life (17 total) — better than the Floodpits Drowner block (no lifegain) and far better than taking 7 unblocked. Double-blocking wastes both chump blockers for no extr"

## Turn 21 — Upkeep [leaf_eval/priority]
- Life: pilot **17** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 7 lands (7 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped) | 11 lands (9 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 17 vs 11)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 17 vs 11)
- Pilot's reasoning: "Still my upkeep — no reason to commit mana to animating Restless Reef yet. I'm well ahead on life (17 vs 11) and will plan attacks once I see my draw and the board state in the main phase."

## Turn 21 — Draw [leaf_eval/priority]
- Life: pilot **17** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 7 lands (7 untapped)
- Pilot hand: Swamp
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped) | 11 lands (9 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 17 vs 11)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 17 vs 11)
- Pilot's reasoning: "Drew a land (Swamp); still just the draw step. No reason to commit to animating Reef yet."

## Turn 21 — Precombat Main [leaf_eval/priority]
- Life: pilot **17** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 7 lands (7 untapped)
- Pilot hand: Swamp
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped) | 11 lands (9 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 17 vs 11)
    - `Play Swamp` scored **80** (Play Swamp: us 17 vs 11)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 17 vs 11)
- Pilot's reasoning: "Playing the Swamp is free value with no downside, and I can still animate Restless Reef afterward with plenty of mana left. No reason to skip the land drop."

## Turn 21 — Precombat Main [leaf_eval/priority]
- Life: pilot **17** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 8 lands (8 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped) | 11 lands (9 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 17 vs 11)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **88** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 17 vs 11)
- Pilot's reasoning: "Animating Restless Reef adds a 4/4 deathtouch attacker for a big alpha strike — opponent has only a 1/1 Vampire Token able to block among Reef, Preacher of the Schism, and Floodpits Drowner (8 total power). No downside since I have no cards to protect."

## Turn 21 — Precombat Main [leaf_eval/priority]
- Life: pilot **17** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 8 lands (4 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped) | 11 lands (9 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 17 vs 11)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **88** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 17 vs 11)
- Pilot's reasoning: "Animate Restless Reef now to add a 4/4 deathtouch attacker for the alpha strike; opponent only has a 1/1 Vampire Token able to block among three attackers."

## Turn 21 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **17** vs MAD **11**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 7 lands (0 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped) | 11 lands (9 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **40** (unblocked: us 17 vs 11)
    - `attack-all` scored **55** (1 block(s), response 2: us 17 vs 10; 1 block(s), response 1: us 17 vs 10; unblocked: us 17 vs 7)
    - `hold[Preacher of the Schism]` scored **None** (1 block(s), response 1: us 17 vs 12; unblocked: us 17 vs 9)
    - `hold[Floodpits Drowner]` scored **None** (1 block(s), response 1: us 17 vs 12; unblocked: us 17 vs 9)
- Pilot's reasoning: "Attacking with everything maximizes damage regardless of which one they chump-block with their lone Vampire Token — worst case still deals significant damage and trades favorably, while the unblocked case brings them to 7 life. No reason to hold anything back with no cards to protect."

## Turn 22 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **16** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1 | 8 lands (0 untapped)
- Pilot hand: Enduring Curiosity, Floodpits Drowner
- MAD board: Vampire Token 1/1, Kaito, Bane of Nightmares 8/9 (tapped), Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 11 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **25** (after combat: us 7 vs 10)
    - `Floodpits Drowner>Kaito, Bane of Nightmares` scored **90** (after combat: us 15 vs 10)
- Pilot's reasoning: "Blocking Kaito with Floodpits Drowner absorbs a massive 8 damage at the cost of a 2/1 body I can replay from hand (I hold a second Floodpits Drowner) — vastly better than taking 8 unblocked and dropping to 7 life."

## Turn 23 — Upkeep [leaf_eval/priority]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (8 untapped)
- Pilot hand: Enduring Curiosity, Floodpits Drowner
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 13 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 15 vs 10)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 15 vs 10)
    - `Cast Floodpits Drowner` scored **55** (Cast Floodpits Drowner: us 15 vs 10)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 15 vs 10)
- Pilot's reasoning: "Still my upkeep — no reason to commit mana or cards yet. I'm ahead on life (15 vs 10) with a strong board; I'll decide the best sequencing (casting Enduring Curiosity, Floodpits Drowner, and/or animating Reef) once I see my draw in the main phase."

## Turn 23 — Draw [leaf_eval/priority]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (8 untapped)
- Pilot hand: Enduring Curiosity, Floodpits Drowner, Go for the Throat
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 13 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 15 vs 10)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 15 vs 10)
    - `Cast Floodpits Drowner` scored **50** (Cast Floodpits Drowner: us 15 vs 10)
    - `Cast Go for the Throat` scored **45** (Cast Go for the Throat: us 15 vs 10)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **50** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 15 vs 10)
- Pilot's reasoning: "Drew Go for the Throat — still just the draw step. With 8 total mana I can likely cast Enduring Curiosity, Floodpits Drowner, and Go for the Throat all in one turn (8 mana exactly), so no need to commit yet."

## Turn 23 — Precombat Main [leaf_eval/priority]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (8 untapped)
- Pilot hand: Enduring Curiosity, Floodpits Drowner, Go for the Throat
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 13 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 15 vs 10)
    - `Cast Enduring Curiosity` scored **55** (Cast Enduring Curiosity: us 15 vs 10)
    - `Cast Floodpits Drowner` scored **60** (Cast Floodpits Drowner: us 15 vs 10)
    - `Cast Go for the Throat` scored **82** (Cast Go for the Throat: us 15 vs 10)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **45** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 15 vs 10)
- Pilot's reasoning: "Casting Go for the Throat on Faerie Mastermind removes their most dangerous remaining threat (an evasive flash blocker with an ongoing card-advantage engine) while I still have 6 mana left to also cast Floodpits Drowner and Enduring Curiosity this turn."

## Turn 23 — Precombat Main [target]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (8 untapped)
- Pilot hand: Enduring Curiosity, Floodpits Drowner
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 13 lands (5 untapped)
- Menu: [0] Faerie Mastermind 2/1 (B); [1] Deep-Cavern Bat 1/1 (B); [2] Spyglass Siren 1/1 (B); [3] Vampire Token 1/1 (B); [4] Preacher of the Schism 2/4 (A)
- **Chose: target Faerie Mastermind 2/1 (B)**
- Pilot's reasoning: "Faerie Mastermind is the most valuable removal target — an evasive flash flyer that also grants them card advantage every time I draw a second card in a turn."

## Turn 23 — Precombat Main [leaf_eval/priority]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (6 untapped)
- Pilot hand: Enduring Curiosity, Floodpits Drowner
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 13 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 15 vs 10)
    - `Cast Enduring Curiosity` scored **55** (Cast Enduring Curiosity: us 15 vs 10)
    - `Cast Floodpits Drowner` scored **82** (Cast Floodpits Drowner: us 15 vs 10)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **45** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 15 vs 10)
- Pilot's reasoning: "Casting Floodpits Drowner now lets me stun their remaining flyer (Spyglass Siren) before combat, clearing the way for my attack, while leaving exactly 4 mana to still cast Enduring Curiosity afterward."

## Turn 23 — Precombat Main [leaf_eval/priority]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 13 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 15 vs 10)
    - `Cast Enduring Curiosity` scored **88** (Cast Enduring Curiosity: us 15 vs 10)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **55** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 15 vs 10)
- Pilot's reasoning: "Cast Enduring Curiosity now with the remaining 4 mana — it adds a 4/3 body and sets up a card-draw engine for future combat damage, with no downside since I have no other use for this mana."

## Turn 23 — Precombat Main [target]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3 (sick), Floodpits Drowner 2/1 (sick) | 8 lands (0 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (sick), Spyglass Siren 1/1 (sick) | 13 lands (5 untapped)
- Menu: [0] Faerie Mastermind 2/1 (B); [1] Deep-Cavern Bat 1/1 (B); [2] Spyglass Siren 1/1 (B); [3] Vampire Token 1/1 (B)
- **Chose: target Spyglass Siren 1/1 (B)**
- Pilot's reasoning: "Stun Spyglass Siren, their only remaining flying blocker, to clear the way for my attack — the Vampire Token is harmless and Deep-Cavern Bat is already tapped."

## Turn 23 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **15** vs MAD **10**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3 (sick), Floodpits Drowner 2/1 (sick) | 8 lands (0 untapped)
- Pilot hand: empty
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 13 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **20** (unblocked: us 15 vs 10)
    - `attack-all` scored **55** (1 block(s), response 1: us 15 vs 11; unblocked: us 15 vs 8)
- Pilot's reasoning: "Preacher is my only untapped, non-summoning-sick attacker and I have zero cards to protect, so attacking is free upside. If they block with the Vampire Token, deathtouch kills it and Preacher survives (only +1 life to them via lifelink) — a clean trade in my favor. If unblocked, I deal 2 and draw a "

## Turn 24 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **14** vs MAD **8**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (sick), Floodpits Drowner 2/1 (sick) | 8 lands (0 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Cut Down
- MAD board: Vampire Token 1/1, Kaito, Bane of Nightmares 9/10 (tapped), Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 13 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **14** (after combat: us 4 vs 9)
    - `Enduring Curiosity>Kaito, Bane of Nightmares` scored **88** (after combat: us 13 vs 9)
    - `Floodpits Drowner>Kaito, Bane of Nightmares` scored **58** (after combat: us 13 vs 9)
    - `Enduring Curiosity>Kaito, Bane of Nightmares, Floodpits Drowner>Kaito, Bane of Nightmares` scored **48** (after combat: us 13 vs 9)
- Pilot's reasoning: "Both flying attackers (Deep-Cavern Bat, Spyglass Siren) are unblockable by our grounded creatures, so the only real decision is whether/how to block the 9/10 Kaito. Enduring Curiosity dying to Kaito costs almost nothing since its death trigger returns it to the battlefield as an enchantment, keeping"

## Turn 25 — Upkeep [leaf_eval/priority]
- Life: pilot **13** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 9 lands (9 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Cut Down
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 14 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **82** (pass (hold everything): us 13 vs 9)
    - `Cast Cut Down` scored **55** (Cast Cut Down: us 13 vs 9)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **48** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 13 vs 9)
- Pilot's reasoning: "It's only upkeep with no trigger or opposing action to respond to, so there's no benefit to committing Cut Down or spending 4 mana animating Restless Reef before I've even seen my draw for the turn. Passing here costs nothing (same mana available in precombat main) and keeps full flexibility to sequ"

## Turn 25 — Draw [leaf_eval/priority]
- Life: pilot **13** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 9 lands (9 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Cut Down, Floodpits Drowner
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 14 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 13 vs 9)
    - `Cast Cut Down` scored **55** (Cast Cut Down: us 13 vs 9)
    - `Cast Floodpits Drowner` scored **50** (Cast Floodpits Drowner: us 13 vs 9)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **45** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 13 vs 9)
- Pilot's reasoning: "Still no reason to act before main phase — this is just the draw step with an empty stack, and all three plays (Cut Down, Floodpits Drowner, animate Reef) are equally available in the main phase where I can also make my land drop and sequence everything together (kill a flyer, decide whether to hold"

## Turn 25 — Precombat Main [leaf_eval/priority]
- Life: pilot **13** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 9 lands (9 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Cut Down, Floodpits Drowner
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 14 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **8** (pass (hold everything): us 13 vs 9)
    - `Cast Kaito, Bane of Nightmares` scored **38** (Cast Kaito, Bane of Nightmares: us 13 vs 9)
    - `Cast Cut Down` scored **72** (Cast Cut Down: us 13 vs 9)
    - `Cast Floodpits Drowner` scored **85** (Cast Floodpits Drowner: us 13 vs 9)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **90** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 13 vs 9)
- Pilot's reasoning: "Opponent's only untapped blocker is the Vampire Token (Deep-Cavern Bat and Spyglass Siren are both tapped from attacking last turn and can't block); if I tap/stun that Vampire Token with Floodpits Drowner's ETB and animate Restless Reef into a 4/4, I can swing with Preacher (2) + Floodpits Drowner ("

## Turn 25 — Precombat Main [leaf_eval/priority]
- Life: pilot **13** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 9 lands (5 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Cut Down, Floodpits Drowner
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 14 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **10** (pass (hold everything): us 13 vs 9)
    - `Cast Cut Down` scored **70** (Cast Cut Down: us 13 vs 9)
    - `Cast Floodpits Drowner` scored **88** (Cast Floodpits Drowner: us 13 vs 9)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 13 vs 9)
- Pilot's reasoning: "Restless Reef is already animated as a 4/4 for this turn (re-activating again would just waste 4 more mana for no additional effect, since the ability doesn't stack). With 4 mana left, casting Floodpits Drowner to tap+stun their only untapped blocker (Vampire Token) is the critical remaining play — "

## Turn 25 — Precombat Main [leaf_eval/priority]
- Life: pilot **13** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 9 lands (3 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Cut Down
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 14 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 13 vs 9)
    - `Cast Cut Down` scored **85** (Cast Cut Down: us 13 vs 9)
- Pilot's reasoning: "With only 2 mana left and Kaito costing 4 (too expensive to deploy this turn anyway, better held for next turn), the only productive use of remaining mana is Cut Down, which permanently removes a flyer (Deep-Cavern Bat or Spyglass Siren) and stops future unblockable chip damage. There's no reason to"

## Turn 25 — Precombat Main [target]
- Life: pilot **13** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 9 lands (3 untapped)
- Pilot hand: Kaito, Bane of Nightmares
- MAD board: Vampire Token 1/1, Deep-Cavern Bat 1/1 (tapped), Spyglass Siren 1/1 (tapped) | 14 lands (13 untapped)
- Menu: [0] Deep-Cavern Bat 1/1 (B); [1] Spyglass Siren 1/1 (B); [2] Vampire Token 1/1 (B); [3] Floodpits Drowner 2/1 (A)
- **Chose: target Vampire Token 1/1 (B)**
- Pilot's reasoning: "Vampire Token is their only untapped potential blocker this combat — Deep-Cavern Bat and Spyglass Siren are already tapped and can't block regardless. If I don't remove it, a rational opponent blocks my biggest attacker (the 4/4 deathtouch Restless Reef) with the token, trading it away via deathtouc"

## Turn 25 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **13** vs MAD **9**
- Pilot board: Restless Reef 4/4, Preacher of the Schism 2/4, Floodpits Drowner 2/1, Floodpits Drowner 2/1 (sick) | 8 lands (1 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped) | 14 lands (11 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **8** (unblocked: us 13 vs 9)
    - `attack-all` scored **97** (unblocked: us 13 vs 1)
    - `hold[Restless Reef]` scored **45** (unblocked: us 13 vs 5)
    - `hold[Preacher of the Schism]` scored **55** (unblocked: us 13 vs 3)
    - `hold[Floodpits Drowner]` scored **35** (unblocked: us 13 vs 3)
- Pilot's reasoning: "Opponent has zero cards in hand, so there's no trick risk to a full alpha strike — attacking with everything (Restless Reef, Preacher, and the non-sick Floodpits Drowner) deals a fully unblocked 8, dropping them to 1 life with virtually no downside. Floodpits Drowner has vigilance, so attacking with"

## Turn 25 — Declare Attackers [target]
- Life: pilot **13** vs MAD **9**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1, Floodpits Drowner 2/1 (sick) | 8 lands (1 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped) | 14 lands (11 untapped)
- Menu: [0] player A (life 13); [1] player B (life 9)
- **Chose: target player B (life 9)**
- Pilot's reasoning: "Mill the opponent (player B), not myself. They're already tapped out with an empty hand and about to be at 1 life — milling them further reduces their draw step's chances of finding an answer and adds deck-out as a secondary win condition. Milling myself would only risk feeding my own graveyard for "

## Turn 25 — Postcombat Main [leaf_eval/priority]
- Life: pilot **12** vs MAD **1**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1, Floodpits Drowner 2/1 (sick) | 8 lands (1 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Darkslick Shores, Restless Reef, Darkslick Shores, Anoint with Affliction
- MAD board: Spyglass Siren 1/1 (tapped) | 14 lands (11 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 12 vs 1)
    - `Play Darkslick Shores` scored **82** (Play Darkslick Shores: us 12 vs 1)
    - `Play Restless Reef` scored **78** (Play Restless Reef: us 12 vs 1)
    - `Play Darkslick Shores` scored **82** (Play Darkslick Shores: us 12 vs 1)
- Pilot's reasoning: "It's free value to make a land drop now — mana is already tapped out this turn so it costs nothing, and banking an extra land ramps me toward casting both Kaito and Enduring Curiosity (8 mana total) as soon as next turn. All three land options are functionally similar (any of them enters tapped and "

## Turn 26 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **12** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1, Floodpits Drowner 2/1 (sick) | 10 lands (1 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction
- MAD board: Kaito, Bane of Nightmares 10/11 (tapped), Spyglass Siren 1/1 (tapped) | 14 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **5** (after combat: us 2 vs 1)
    - `Floodpits Drowner>Kaito, Bane of Nightmares` scored **92** (after combat: us 12 vs 1)
    - `Floodpits Drowner>Kaito, Bane of Nightmares` scored **92** (after combat: us 12 vs 1)
    - `Floodpits Drowner>Kaito, Bane of Nightmares, Floodpits Drowner>Kaito, Bane of Nightmares` scored **55** (after combat: us 12 vs 1)
- Pilot's reasoning: "Kaito is now a 10/11 unblocked would take me from 12 to 2 life, which is far too dangerous against an opponent still holding cards. A single Floodpits Drowner chump-blocking fully prevents all that damage since Kaito is the only attacker (Spyglass Siren is tapped). Double-blocking with both Floodpit"

## Turn 27 — Upkeep [leaf_eval/priority]
- Life: pilot **12** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 12 vs 1)
    - `Cast Enduring Curiosity` scored **40** (Cast Enduring Curiosity: us 12 vs 1)
    - `Cast Anoint with Affliction` scored **35** (Cast Anoint with Affliction: us 12 vs 1)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **35** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 1)
- Pilot's reasoning: "It's upkeep — nothing here is time-sensitive since opponent has zero cards in hand and no possible response. All I need to do is reach combat and attack: Preacher of the Schism or Floodpits Drowner alone already deals lethal damage since opponent is at 1 life with no untapped blockers (Spyglass Sire"

## Turn 27 — Draw [leaf_eval/priority]
- Life: pilot **12** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction, Sheoldred, the Apocalypse
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 12 vs 1)
    - `Cast Enduring Curiosity` scored **42** (Cast Enduring Curiosity: us 12 vs 1)
    - `Cast Anoint with Affliction` scored **35** (Cast Anoint with Affliction: us 12 vs 1)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **35** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 1)
- Pilot's reasoning: "Same reasoning as upkeep — opponent has zero cards and no untapped blockers, so any of my untapped attackers (Preacher or Floodpits Drowner) wins the game in combat this turn. There's no benefit to committing spells now versus in the main phase; passing preserves maximum flexibility with zero cost."

## Turn 27 — Precombat Main [leaf_eval/priority]
- Life: pilot **12** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction, Sheoldred, the Apocalypse
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **95** (pass (hold everything): us 12 vs 1)
    - `Cast Kaito, Bane of Nightmares` scored **55** (Cast Kaito, Bane of Nightmares: us 12 vs 1)
    - `Cast Enduring Curiosity` scored **55** (Cast Enduring Curiosity: us 12 vs 1)
    - `Play Restless Reef` scored **55** (Play Restless Reef: us 12 vs 1)
    - `Play Darkslick Shores` scored **55** (Play Darkslick Shores: us 12 vs 1)
    - `Cast Anoint with Affliction` scored **45** (Cast Anoint with Affliction: us 12 vs 1)
    - `Cast Sheoldred, the Apocalypse` scored **60** (Cast Sheoldred, the Apocalypse: us 12 vs 1)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **45** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 1)
- Pilot's reasoning: "Opponent has zero cards in hand and no untapped blockers (Spyglass Siren is tapped), so attacking with Preacher of the Schism or Floodpits Drowner in combat is unstoppable, guaranteed lethal — there's no removal, no counterspell, nothing they can do about it. Passing straight to combat wins the game"

## Turn 27 — Begin Combat [leaf_eval/priority]
- Life: pilot **12** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction, Sheoldred, the Apocalypse
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **95** (pass (hold everything): us 12 vs 1)
    - `Cast Enduring Curiosity` scored **55** (Cast Enduring Curiosity: us 12 vs 1)
    - `Cast Anoint with Affliction` scored **55** (Cast Anoint with Affliction: us 12 vs 1)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **60** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 1)
- Pilot's reasoning: "Same as before — opponent has zero cards and no untapped blockers, so attacking with Preacher or Floodpits Drowner is unstoppable lethal. Nothing gained by spending resources first; passing to combat wins immediately."

## Turn 27 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **12** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction, Sheoldred, the Apocalypse
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **5** (unblocked: us 12 vs 1)
    - `attack-all` scored **100** (unblocked: us 12 vs -3)
    - `hold[Preacher of the Schism]` scored **60** (unblocked: us 12 vs -1)
    - `hold[Floodpits Drowner]` scored **60** (unblocked: us 12 vs -1)
- Pilot's reasoning: "Opponent is at 1 life with no untapped blockers and zero cards in hand — attacking with either creature alone is already lethal, and attacking with both guarantees it beyond any doubt. There's no reason to hold anything back since there's no follow-up threat to play around; not attacking at all woul"

## Turn 27 — Declare Attackers [leaf_eval/priority]
- Life: pilot **12** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction, Sheoldred, the Apocalypse
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 11 vs 1)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 11 vs 1)
    - `Cast Anoint with Affliction` scored **45** (Cast Anoint with Affliction: us 11 vs 1)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **45** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 11 vs 1)
- Pilot's reasoning: "Attackers are already declared (Preacher's trigger already resolved, giving me a card and costing 1 life) and opponent still has zero blockers and zero cards — passing simply lets the turn continue to blockers and combat damage, which will be lethal. No further action is needed or beneficial before "

## Turn 27 — Declare Attackers [leaf_eval/priority]
- Life: pilot **11** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction, Sheoldred, the Apocalypse, Spyglass Siren
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 11 vs 1)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 11 vs 1)
    - `Cast Anoint with Affliction` scored **45** (Cast Anoint with Affliction: us 11 vs 1)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **45** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 11 vs 1)
- Pilot's reasoning: "Same situation, unchanged — opponent still has zero blockers and zero cards. Passing lets combat damage resolve for lethal."

## Turn 27 — Declare Blockers [leaf_eval/priority]
- Life: pilot **11** vs MAD **1**
- Pilot board: Preacher of the Schism 2/4 (tapped), Floodpits Drowner 2/1 | 10 lands (10 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Enduring Curiosity, Restless Reef, Darkslick Shores, Anoint with Affliction, Sheoldred, the Apocalypse, Spyglass Siren
- MAD board: Spyglass Siren 1/1 (tapped) | 15 lands (13 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **92** (pass (hold everything): us 11 vs 1)
    - `Ninjutsu {1}{U}{B} <i>({1}{U}{B} Return an unblocked attacker you control to hand: Put this card onto the battlefield from your hand tapped and attacking.)</i>` scored **40** (Ninjutsu {1}{U}{B} <i>({1}{U}{B} Return an unblocked attacker you control to hand: Put this card onto the battlefield from your hand tapped and attacking.)</i>: us 11 vs 1)
    - `Cast Enduring Curiosity` scored **40** (Cast Enduring Curiosity: us 11 vs 1)
    - `Cast Anoint with Affliction` scored **40** (Cast Anoint with Affliction: us 11 vs 1)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **40** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 11 vs 1)
- Pilot's reasoning: "Floodpits Drowner is already an unblocked attacker dealing 2 damage into a 1-life opponent — lethal is already assured. Ninjutsu'ing in Kaito would just swap a guaranteed-lethal attacker for another guaranteed-lethal attacker at the cost of mana and returning Floodpits Drowner to hand for no benefit"
