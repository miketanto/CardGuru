# Decision review — g1.jsonl

Result: **pilot lost** in 19 turns. 30 real decisions out of 303 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "3 lands (2 untapped-capable colors covering both U and B) plus Sheoldred, two Preachers, and a Drowner is a strong curve with both colors available - clear keep."

## Turn 1 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Darkslick Shores` scored **52** (play Darkslick Shores | s0: they do nothing: us 20 vs 20; play Darkslick Shores | s1: they do nothing: us 20 vs 20; play Darkslick Shores | s2: they do nothing: us 20 vs 20)
    - `play Island` scored **50** (play Island | s0: they do nothing: us 20 vs 20; play Island | s1: they do nothing: us 20 vs 20; play Island | s2: they do nothing: us 20 vs 20)
    - `play Swamp` scored **50** (play Swamp | s0: they do nothing: us 20 vs 20; play Swamp | s1: they do nothing: us 20 vs 20)
- Pilot's reasoning: "All lines are turn-1 land drops with no board impact yet; Darkslick Shores entering untapped gives both colors and slightly more flexibility going forward, so those leaves score marginally above parity."

## Turn 3 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Swamp, hold Drowner up` scored **52** (play Swamp, hold Drowner up | s0: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Swamp, hold Drowner up | s0: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; play Swamp, hold Drowner up | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Swamp, hold Drowner up | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `play Swamp, cast Drowner on Siren now` scored **45** (play Swamp, cast Drowner on Siren now | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; play Swamp, cast Drowner on Siren now | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; play Swamp, cast Drowner on Siren now | s2: they cast Cast Go for the Throat | I do nothing: us 20 vs 20)
    - `play Island, hold Drowner up` scored **52** (play Island, hold Drowner up | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Island, hold Drowner up | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; play Island, hold Drowner up | s1: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Island, hold Drowner up | s1: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Holding Drowner up keeps optionality and lets me react to whatever they commit (still fine even if they just untap freely); casting it on the 1/1 Siren now is slightly worse since it risks eating removal or getting outvalued by a Deep-Cavern Bat/second Drowner with nothing left in hand to respond."

## Turn 5 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop + attack with Drowner` scored **42** (develop + attack with Drowner | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; develop + attack with Drowner | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; develop + attack with Drowner | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `develop + hold Drowner back` scored **50** (develop + hold Drowner back | s0: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; develop + hold Drowner back | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; develop + hold Drowner back | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Attacking with Drowner reliably trades it for their Faerie Mastermind (good) but risks a two-for-one if they also have Go for the Throat up, while holding Drowner back keeps both my creatures on board as blockers into their development, which is safer and still fine on card count."

## Turn 5 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **54** (unblocked: us 20 vs 20)
    - `attack-all` scored **55** (1 block(s), response 1: us 20 vs 20; unblocked: us 20 vs 18)
- Pilot's reasoning: "Attacking with vigilant Drowner either trades evenly with their Faerie Mastermind (denying their card-draw engine, acceptable trade) or gets in 2 free damage if unblocked, while not attacking just leaves an identical static board with no progress."

## Turn 7 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Island, Swamp
- MAD board: Spyglass Siren 1/1 (tapped) | 4 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Swamp, slam Sheoldred` scored **72** (play Swamp, slam Sheoldred | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 20 vs 18)
    - `play Island, cast Preacher, hold Sheoldred` scored **54** (play Island, cast Preacher, hold Sheoldred | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; play Island, cast Preacher, hold Sheoldred | s1: they cast Cast Cut Down | I do nothing: us 20 vs 20; play Island, cast Preacher, hold Sheoldred | s2: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Sheoldred resolving as an immediate 4/5 deathtouch blocker that already started draining their life on their own draw step is a huge swing, clearly outclassing the safer Preacher line whose leaves sit near parity even in the better cases."

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 (sick) | 4 lands (0 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **68** (after combat: us 19 vs 18)
- Pilot's reasoning: "I'm at 19 vs their 18, but I have Sheoldred, the Apocalypse (4/5 deathtouch) dominating the board against their 1/1 Siren and summoning-sick Preacher, plus the ongoing life-drain from Sheoldred's triggers each draw step."

## Turn 9 — Precombat Main [leaf_eval/plan]
- Life: pilot **21** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Island, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop Bat + Preacher, hold Sheoldred back` scored **55** (develop Bat + Preacher, hold Sheoldred back | s0: they cast Cast Spyglass Siren | I do nothing: us 21 vs 16; develop Bat + Preacher, hold Sheoldred back | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 21 vs 16; develop Bat + Preacher, hold Sheoldred back | s2: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 16)
    - `cast Enduring Curiosity, hold Sheoldred back` scored **56** (cast Enduring Curiosity, hold Sheoldred back | s0: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 16; cast Enduring Curiosity, hold Sheoldred back | s1: they cast Cast Faerie Mastermind | I do nothing: us 21 vs 16)
- Pilot's reasoning: "I'm well ahead at 21 vs 16 life with Sheoldred draining them every draw step; developing Bat+Preacher gives more bodies and hand info while Enduring Curiosity gives a bigger card-draw engine, both keep me clearly ahead even if they land their own bomb or stun Sheoldred."

## Turn 9 — Precombat Main [choose]
- Life: pilot **21** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] Anoint with Affliction; [1] Sheoldred, the Apocalypse; [2] Cut Down; [3] Enduring Curiosity
- **Chose: target Anoint with Affliction**
- Pilot's reasoning: "Anoint with Affliction is likely unconditional removal that can kill my Sheoldred (Cut Down's power+toughness cap can't touch a 4/5, and their own Sheoldred takes another turn to matter), so exiling it directly protects my best threat right now."

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **21** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **62** (unblocked: us 21 vs 18)
    - `attack-all` scored **35** (1 block(s), response 1: us 21 vs 18; unblocked: us 21 vs 14)
- Pilot's reasoning: "Attacking risks a bad trade since their Preacher also has deathtouch (any block kills Sheoldred for their weaker 2/4), and a rational opponent takes that trade; not attacking keeps my board intact and still ahead on life and card quality."

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **21** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **62** (after combat | after blocks they cast Cast Floodpits Drowner: us 18 vs 16)
    - `Sheoldred, the Apocalypse>Preacher of the Schism` scored **40** (after combat | after blocks they cast Cast Floodpits Drowner: us 20 vs 16)
- Pilot's reasoning: "Taking 3 damage (21→18) while keeping Sheoldred is far better than trading it away for their 2/4 Preacher via mutual deathtouch - I'm already way ahead on life and card quality, so preserving my best engine piece matters far more than 2-3 life."

## Turn 11 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 5 lands (5 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack Sheoldred, then cast Preacher postcombat` scored **60** (attack Sheoldred, then cast Preacher postcombat | NOT available: cast Preacher of the Schism | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 15; attack Sheoldred, then cast Preacher postcombat | NOT available: cast Preacher of the Schism | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 15; attack Sheoldred, then cast Preacher postcombat | NOT available: cast Preacher of the Schism | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 20 vs 15)
    - `attack Sheoldred, then cast Enduring Curiosity postcombat` scored **55** (attack Sheoldred, then cast Enduring Curiosity postcombat | NOT available: cast Enduring Curiosity | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 20 vs 15; attack Sheoldred, then cast Enduring Curiosity postcombat | NOT available: cast Enduring Curiosity | s1: they cast Cast Cut Down | I do nothing: us 20 vs 15)
- Pilot's reasoning: "Attacking connected for solid damage (opponent down to 15) while my board of Sheoldred + Enduring Curiosity dominates their small creatures in every branch; the only slightly worse case is them landing their own Sheoldred to start a symmetric drain race."

## Turn 11 — Precombat Main [priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 6 lands (6 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 4 lands (3 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Enduring Curiosity; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {B}.; [6] {T}: Add {U}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.
- **Chose: Cast Preacher of the Schism**
- Pilot's reasoning: "Combat resolved (Sheoldred attacked); now in postcombat main I cast Preacher of the Schism per the chosen plan to add another deathtouch body to the board."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **55** (unblocked: us 20 vs 16)
    - `attack-all` scored **62** (1 block(s), response 1: us 20 vs 17; unblocked: us 20 vs 12)
- Pilot's reasoning: "Attacking with Sheoldred is safe since their Preacher is tapped and can't block; even the chump-block case still kills their Vampire Token for a trivial 1 life lifelink gain, while unblocked deals a huge 4 damage to bring them to 12."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **62** (after combat: us 17 vs 15)
    - `Preacher of the Schism>Preacher of the Schism` scored **56** (after combat: us 19 vs 15)
- Pilot's reasoning: "I have a big life cushion (20) and want to keep both deathtouch bodies on my side now that they have their own Sheoldred coming online; trading my Preacher for theirs saves only 2 life but weakens my future board against their growing threats."

## Turn 13 — Precombat Main [leaf_eval/plan]
- Life: pilot **17** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `Bat for info, then attack, then Enduring Curiosity` scored **54** (Bat for info, then attack, then Enduring Curiosity | NOT available: cast Enduring Curiosity | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 17 vs 16; Bat for info, then attack, then Enduring Curiosity | NOT available: cast Enduring Curiosity | s1: they cast Cast Faerie Mastermind | I do nothing: us 17 vs 16; Bat for info, then attack, then Enduring Curiosity | NOT available: cast Enduring Curiosity | s2: they cast Cast Floodpits Drowner | I do nothing: us 17 vs 16)
    - `attack first, develop postcombat` scored **54** (attack first, develop postcombat | NOT available: cast Enduring Curiosity | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 17 vs 16; attack first, develop postcombat | NOT available: cast Enduring Curiosity | s1: they cast Cast Floodpits Drowner | I do nothing: us 17 vs 16; attack first, develop postcombat | NOT available: cast Enduring Curiosity | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 17 vs 16)
    - `no attack, just develop` scored **66** (no attack, just develop | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 17 vs 15; no attack, just develop | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 17 vs 15; no attack, just develop | s2: they cast Cast Preacher of the Schism | I do nothing: us 17 vs 15)
- Pilot's reasoning: "Attacking trades my Sheoldred for theirs while dealing zero net damage (their Vampire Token chump-blocks Preacher for lifelink), a fair but unremarkable outcome; holding back and developing Bat + Enduring Curiosity keeps my full four-creature board (11 power) intact against their smaller board, sett"

## Turn 13 — Precombat Main [choose]
- Life: pilot **17** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4, Enduring Curiosity 4/3 (sick), Deep-Cavern Bat 1/1 (sick) | 6 lands (0 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Menu: [0] Anoint with Affliction; [1] Cut Down; [2] Enduring Curiosity
- **Chose: target Anoint with Affliction**
- Pilot's reasoning: "Anoint with Affliction is likely unconditional removal that threatens Sheoldred or Preacher, while Cut Down's power+toughness cap can't touch either of them and their Enduring Curiosity is just a value creature, not urgent to deny."

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **17** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4, Enduring Curiosity 4/3 (sick), Deep-Cavern Bat 1/1 (sick) | 6 lands (0 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **65** (unblocked: us 17 vs 15)
    - `attack-all` scored **66** (2 block(s), response 5: us 17 vs 16; 1 block(s), response 1: us 17 vs 13; 1 block(s), response 3: us 17 vs 14)
    - `hold[Sheoldred, the Apocalypse]` scored **63** (1 block(s), response 2: us 17 vs 16; unblocked: us 17 vs 13; 1 block(s), response 1: us 17 vs 15)
    - `hold[Preacher of the Schism]` scored **66** (1 block(s), response 1: us 17 vs 15; 1 block(s), response 2: us 17 vs 16; unblocked: us 17 vs 11)
- Pilot's reasoning: "All-out attack or holding either creature back both lead to favorable outcomes since both my attackers have deathtouch and trade up into anything that blocks; holding Sheoldred back while attacking with Preacher has the best upside (either free damage, a free Vampire Token kill, or a fair Sheoldred-"

## Turn 14 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **16** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (sick) | 6 lands (0 untapped)
- Pilot hand: Go for the Throat, Island
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped), Vampire Token 1/1 (sick) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **50** (after combat: us 9 vs 14)
    - `Enduring Curiosity>Preacher of the Schism` scored **57** (after combat | after blocks they cast Cast Cut Down: us 11 vs 14)
    - `Enduring Curiosity>Sheoldred, the Apocalypse` scored **53** (after combat | after blocks they cast Cast Faerie Mastermind: us 13 vs 14)
- Pilot's reasoning: "No block risks dropping to 9 life against their growing board; blocking their Sheoldred with Enduring Curiosity only chump-saves life without permanently removing a threat, while blocking their Preacher trades for a permanent kill of their recurring deathtouch attacker (and Enduring Curiosity return"

## Turn 15 — Precombat Main [leaf_eval/plan]
- Life: pilot **11** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 7 lands (7 untapped)
- Pilot hand: Go for the Throat, Island, Preacher of the Schism
- MAD board: Spyglass Siren 1/1 (tapped), Sheoldred, the Apocalypse 4/5 (tapped), Vampire Token 1/1 (sick) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `Go for the Throat their Sheoldred, develop, attack all` scored **70** (Go for the Throat their Sheoldred, develop, attack all | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 13 vs 11; Go for the Throat their Sheoldred, develop, attack all | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 13 vs 11; Go for the Throat their Sheoldred, develop, attack all | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 13 vs 11)
    - `no removal, just attack and develop` scored **62** (no removal, just attack and develop | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 13 vs 11; no removal, just attack and develop | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 13 vs 11; no removal, just attack and develop | s2: they cast Cast Cut Down | I do nothing: us 13 vs 11)
- Pilot's reasoning: "Their Sheoldred was already tapped from attacking so it couldn't block either way, but Go for the Throat permanently removes it before it can untap and threaten me again next turn (attacking or draining me on draws), which the no-removal line leaves fully intact."

## Turn 15 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **11** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 8 lands (6 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (sick) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **58** (unblocked: us 11 vs 14)
    - `attack-all` scored **65** (1 block(s), response 1: us 11 vs 13; 1 block(s), response 2: us 11 vs 11; unblocked: us 11 vs 8)
    - `hold[Sheoldred, the Apocalypse]` scored **60** (1 block(s), response 1: us 11 vs 15; unblocked: us 11 vs 12)
    - `hold[Preacher of the Schism]` scored **60** (1 block(s), response 1: us 11 vs 15; unblocked: us 11 vs 10)
- Pilot's reasoning: "With their Sheoldred dead and only a 1/1 Siren and 1/1 Vampire Token left, attacking with both my deathtouch creatures carries very little risk - worst case removes their only real blocker for minor damage, best case is a huge 6-point swing; not attacking wastes the opportunity while I have almost n"

## Turn 15 — Postcombat Main [priority]
- Life: pilot **13** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 8 lands (6 untapped)
- Pilot hand: Preacher of the Schism, Spyglass Siren
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (4 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Spyglass Siren; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {B}.; [6] {T}: Add {U}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.
- **Chose: Cast Preacher of the Schism**
- Pilot's reasoning: "Postcombat main with mana available; cast Preacher of the Schism to keep developing my board after this turn's attack."

## Turn 16 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **13** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick), Preacher of the Schism 2/4 (sick) | 8 lands (3 untapped)
- Pilot hand: Spyglass Siren
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **65** (after combat | after blocks they cast Cast Cut Down: us 12 vs 11)
- Pilot's reasoning: "Their Spyglass Siren has flying so none of my ground creatures could have blocked it anyway; ending at 12 life with two deathtouch Preachers against their lone Siren is still a strong position for me."

## Turn 17 — Precombat Main [leaf_eval/plan]
- Life: pilot **12** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4 | 8 lands (8 untapped)
- Pilot hand: Spyglass Siren, Island
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop then attack all` scored **80** (develop then attack all | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 13 vs 6; develop then attack all | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 13 vs 6; develop then attack all | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Floodpits Drowner: us 13 vs 6; develop then attack all | s1: they cast Cast Preacher of the Schism | I do nothing: us 13 vs 6; develop then attack all | s2: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 13 vs 6; develop then attack all | s2: they cast Cast Floodpits Drowner | I do nothing: us 13 vs 6)
    - `attack all then develop` scored **78** (attack all then develop | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 13 vs 6; attack all then develop | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 13 vs 6; attack all then develop | s2: they cast Cast Go for the Throat | on the stack I cast Cast Floodpits Drowner: us 13 vs 6; attack all then develop | s2: they cast Cast Go for the Throat | after it resolves I cast Cast Floodpits Drowner: us 13 vs 6; attack all then develop | s2: they cast Cast Go for the Throat | I do nothing: us 13 vs 6)
- Pilot's reasoning: "Opponent is down to 6 life with almost no board while I have overwhelming board presence at 13 life - this is a near-winning position regardless of their one response; losing a Preacher to Go for the Throat barely dents my advantage since I still threaten lethal next turn."

## Turn 17 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **12** vs MAD **11**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4, Spyglass Siren 1/1 (sick) | 10 lands (9 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **55** (unblocked: us 12 vs 11)
    - `attack-all` scored **85** (unblocked: us 13 vs 6)
    - `hold[Preacher of the Schism]` scored **72** (unblocked: us 13 vs 8)
    - `hold[Vampire Token]` scored **78** (unblocked: us 12 vs 7)
    - `hold[Preacher of the Schism]` scored **72** (unblocked: us 13 vs 8)
- Pilot's reasoning: "Opponent has zero blockers (Siren tapped) so attacking with everything deals full unblocked damage, dropping them to 6 life with no risk to my board; holding anything back only reduces damage for no defensive benefit since they can't attack back meaningfully."

## Turn 17 — Postcombat Main [priority]
- Life: pilot **11** vs MAD **6**
- Pilot board: Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Spyglass Siren 1/1 (sick) | 10 lands (9 untapped)
- Pilot hand: Restless Reef, Floodpits Drowner, Swamp, Anoint with Affliction, Darkslick Shores
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] Cast Anoint with Affliction; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {B}.; [6] {T}: Add {U}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.; [10] {T}: Add {U}.; [11] {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.
- **Chose: PASS**
- Pilot's reasoning: "Opponent only has a tapped 1/1 Siren; no reason to spend Anoint with Affliction or Floodpits Drowner now when I can hold them up as instant-speed answers to whatever they play on their turn."

## Turn 18 — Precombat Main [priority]
- Life: pilot **11** vs MAD **6**
- Pilot board: Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Spyglass Siren 1/1 (sick) | 10 lands (9 untapped)
- Pilot hand: Restless Reef, Floodpits Drowner, Swamp, Anoint with Affliction, Darkslick Shores
- MAD board: Spyglass Siren 1/1 | 5 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] Cast Anoint with Affliction; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {B}.; [6] {T}: Add {U}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.; [10] {T}: Add {U}.
- **Chose: PASS**
- Pilot's reasoning: "Sheoldred is only on the stack, not yet a permanent, so Floodpits Drowner's ETB couldn't target it yet, and Anoint with Affliction can't hit a mana value 4 creature anyway; better to let it resolve and then stun it with Floodpits Drowner afterward."

## Turn 19 — Precombat Main [leaf_eval/plan]
- Life: pilot **9** vs MAD **6**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4, Spyglass Siren 1/1 | 10 lands (10 untapped)
- Pilot hand: Restless Reef, Floodpits Drowner, Swamp, Anoint with Affliction, Darkslick Shores, Undercity Sewers
- MAD board: Spyglass Siren 1/1, Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `stun their Sheoldred, attack all` scored **50** (stun their Sheoldred, attack all | s0: they cast Cast Anoint with Affliction | I do nothing: us 6 vs 6; stun their Sheoldred, attack all | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 6 vs 6; stun their Sheoldred, attack all | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 6 vs 6)
    - `no removal, just attack all` scored **72** (no removal, just attack all | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Anoint with Affliction: us 10 vs 4; no removal, just attack all | s0: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Anoint with Affliction: us 10 vs 4; no removal, just attack all | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 10 vs 4; no removal, just attack all | s1: they do nothing: us 10 vs 4; no removal, just attack all | s2: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Anoint with Affliction: us 10 vs 4; no removal, just attack all | s2: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Anoint with Affliction: us 10 vs 4; no removal, just attack all | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 10 vs 4)
- Pilot's reasoning: "Stunning their Sheoldred with Floodpits Drowner keeps it alive (just tapped) so its life-drain passive still punishes every card I draw from Preacher/Enduring Curiosity triggers all combat, resulting in a costly wash at 6-6; leaving it able to block instead lets it likely trade away into a deathtouc"

## Turn 19 — Precombat Main [priority]
- Life: pilot **9** vs MAD **6**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4, Spyglass Siren 1/1 | 10 lands (10 untapped)
- Pilot hand: Restless Reef, Floodpits Drowner, Swamp, Anoint with Affliction, Darkslick Shores, Undercity Sewers
- MAD board: Spyglass Siren 1/1, Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (2 untapped)
- Menu: [0] pass priority; [1] Play Restless Reef; [2] Cast Floodpits Drowner; [3] Play Swamp; [4] Cast Anoint with Affliction; [5] Play Darkslick Shores; [6] Play Undercity Sewers; [7] {T}: Add {U}.; [8] {T}: Add {B}.; [9] {T}: Add {B}.; [10] {T}: Add {U}.; [11] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Per the evaluated plan, skip using Floodpits Drowner on their Sheoldred - keeping it able to block means it likely trades away into a deathtouch attacker, removing its life-drain passive; proceed straight to combat."

## Turn 19 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **9** vs MAD **6**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4, Spyglass Siren 1/1 | 10 lands (10 untapped)
- Pilot hand: Restless Reef, Floodpits Drowner, Swamp, Anoint with Affliction, Darkslick Shores, Undercity Sewers
- MAD board: Spyglass Siren 1/1, Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **55** (unblocked: us 9 vs 6)
    - `attack-all` scored **85** (2 block(s), response 8: us 10 vs 4; 1 block(s), response 6: us 10 vs 1; 1 block(s), response 5: us 10 vs 2)
    - `hold[Preacher of the Schism]` scored **78** (2 block(s), response 6: us 10 vs 5; 1 block(s), response 4: us 10 vs 3; 1 block(s), response 5: us 10 vs 4)
    - `hold[Vampire Token]` scored **72** (2 block(s), response 6: us 9 vs 5; 1 block(s), response 4: us 9 vs 3; 1 block(s), response 5: us 9 vs 3)
    - `hold[Preacher of the Schism]` scored **78** (2 block(s), response 6: us 10 vs 5; 1 block(s), response 5: us 10 vs 3; 1 block(s), response 4: us 10 vs 4)
    - `hold[Spyglass Siren]` scored **78** (1 block(s), response 5: us 10 vs 2; 2 block(s), response 7: us 10 vs 5; 1 block(s), response 4: us 10 vs 3)
- Pilot's reasoning: "Attacking with everything drives opponent down to 1-4 life while I climb to 9-10, clearly the best outcome; holding any single attacker back leaves opponent noticeably higher (3-5 life) for no defensive benefit since they have almost no offense of their own."
