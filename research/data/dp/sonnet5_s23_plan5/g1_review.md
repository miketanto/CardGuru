# Decision review — g1.jsonl

Result: **pilot lost** in 22 turns. 39 real decisions out of 341 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "3 lands (2 colors covered) with a clean curve: Drowner T2, Preacher T3, second Preacher, Sheoldred T4 - excellent keep."

## Turn 1 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Darkslick Shores` scored **50** (play Darkslick Shores | s0: they do nothing: us 20 vs 20; play Darkslick Shores | s1: they do nothing: us 20 vs 20; play Darkslick Shores | s2: they do nothing: us 20 vs 20)
    - `play Swamp` scored **50** (play Swamp | s0: they do nothing: us 20 vs 20; play Swamp | s1: they do nothing: us 20 vs 20; play Swamp | s2: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Turn 1 with no board impact either way, all leaves are pure parity; Darkslick Shores is marginally better sequencing (guarantees untapped now) but doesn't change this turn's position."

## Turn 3 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Island, hold Drowner for flash` scored **54** (play Island, hold Drowner for flash | s0: they cast Cast Spyglass Siren | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Island, hold Drowner for flash | s0: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; play Island, hold Drowner for flash | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Island, hold Drowner for flash | s1: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; play Island, hold Drowner for flash | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; play Island, hold Drowner for flash | s2: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Island, hold Drowner for flash | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
    - `play Island, flash Drowner now on Siren` scored **50** (play Island, flash Drowner now on Siren | s0: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; play Island, flash Drowner now on Siren | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; play Island, flash Drowner now on Siren | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
    - `play Swamp, hold Drowner for flash` scored **50** (play Swamp, hold Drowner for flash | s0: they cast Cast Anoint with Affliction | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Swamp, hold Drowner for flash | s0: they cast Cast Anoint with Affliction | I do nothing: us 20 vs 20; play Swamp, hold Drowner for flash | s1: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Swamp, hold Drowner for flash | s1: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; play Swamp, hold Drowner for flash | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play Swamp, hold Drowner for flash | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
- Pilot's reasoning: "All leaves are even 20-20 parity boards on turn 3; holding Drowner's flash keeps flexibility and punishes real threats or bad removal (leaf 11 blanks their Anoint), while spending it immediately on the 1/1 Siren (leaves 7-9) is the weakest use since it's a low-value target."

## Turn 4 — Precombat Main [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 3 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Let Faerie Mastermind resolve first since Drowner can't target a spell on the stack; I'll reassess whether to flash Drowner on it once it's actually on the battlefield."

## Turn 5 — Precombat Main [leaf_eval/plan]
- Life: pilot **19** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop - cast Preacher of the Schism` scored **35** (develop - cast Preacher of the Schism | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20; develop - cast Preacher of the Schism | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
    - `flash Drowner on Faerie Mastermind` scored **46** (flash Drowner on Faerie Mastermind | s0: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; flash Drowner on Faerie Mastermind | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; flash Drowner on Faerie Mastermind | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20)
    - `hold everything, just play land` scored **44** (hold everything, just play land | s0: they cast Cast Cut Down | on the stack I cast Cast Floodpits Drowner: us 19 vs 20; hold everything, just play land | s0: they cast Cast Cut Down | I do nothing: us 19 vs 20; hold everything, just play land | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Floodpits Drowner: us 19 vs 20; hold everything, just play land | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; hold everything, just play land | s2: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 19 vs 20; hold everything, just play land | s2: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Casting Preacher (deathtouch 2/4) is the strongest board development against their small creatures unless they have removal ready (leaf1 drops sharply); holding mana for reactive Drowner plays is safer but doesn't advance my board against their growing 3-creature swarm."

## Turn 5 — Precombat Main [priority]
- Life: pilot **19** vs MAD **20**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Preacher of the Schism; [3] Cast Floodpits Drowner; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.; [7] {T}: Add {U}.
- **Chose: Cast Preacher of the Schism**
- Pilot's reasoning: "Committing to Preacher of the Schism scored highest across sampled opponent responses; deathtouch 2/4 is a strong blocker against their small creatures and starts building my board."

## Turn 7 — Precombat Main [leaf_eval/plan]
- Life: pilot **16** vs MAD **20**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Swamp, cast Sheoldred` scored **50** (play Swamp, cast Sheoldred | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 16; play Swamp, cast Sheoldred | s1: they cast Cast Enduring Curiosity | I do nothing: us 16 vs 18; play Swamp, cast Sheoldred | s2: they cast Cast Floodpits Drowner | I do nothing: us 16 vs 18)
    - `play Swamp, cast Preacher (rebuild)` scored **50** (play Swamp, cast Preacher (rebuild) | s0: they cast Cast Anoint with Affliction | I do nothing: us 16 vs 20; play Swamp, cast Preacher (rebuild) | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20; play Swamp, cast Preacher (rebuild) | s2: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20)
    - `play Island, hold up Drowner` scored **44** (play Island, hold up Drowner | s0: they cast Cast Enduring Curiosity | on the stack I cast Cast Floodpits Drowner: us 16 vs 20; play Island, hold up Drowner | s0: they cast Cast Enduring Curiosity | on the stack I cast Cast Enduring Curiosity: us 16 vs 20; play Island, hold up Drowner | s0: they cast Cast Enduring Curiosity | I do nothing: us 16 vs 20; play Island, hold up Drowner | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Floodpits Drowner: us 16 vs 20; play Island, hold up Drowner | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Enduring Curiosity: us 16 vs 20; play Island, hold up Drowner | s1: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Floodpits Drowner: us 16 vs 20; play Island, hold up Drowner | s1: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Enduring Curiosity: us 16 vs 20; play Island, hold up Drowner | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 16 vs 20; play Island, hold up Drowner | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Floodpits Drowner: us 16 vs 20; play Island, hold up Drowner | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Enduring Curiosity: us 16 vs 20; play Island, hold up Drowner | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 16 vs 20)
- Pilot's reasoning: "Sheoldred is the standout play - in the sampled lines it sticks and immediately swings life (me 18 vs them 16-18) while being an unkillable-in-combat 4/5 deathtouch wall; even the worst sampled case (tapped by their Drowner) just delays it a turn. Preacher rebuild is solid but lower ceiling, and hol"

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **16** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 (sick) | 4 lands (0 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **55** (after combat: us 13 vs 18)
- Pilot's reasoning: "Forced to take 3 from their unblockable fliers (no flying/reach blocker), dropping to 13 life, but Sheoldred stays untapped and active as a dominant deathtouch blocker/life-swing engine going forward - manageable but life total is getting concerning."

## Turn 9 — Precombat Main [leaf_eval/plan]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop full - Bat + Preacher, attack Sheoldred` scored **40** (develop full - Bat + Preacher, attack Sheoldred | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 18; develop full - Bat + Preacher, attack Sheoldred | s1: they cast Cast Preacher of the Schism | I do nothing: us 15 vs 18; develop full - Bat + Preacher, attack Sheoldred | s2: they cast Cast Enduring Curiosity | I do nothing: us 15 vs 18)
    - `Bat now, hold Drowner mana` scored **33** (Bat now, hold Drowner mana | s0: they cast Cast Go for the Throat | I do nothing: us 15 vs 18; Bat now, hold Drowner mana | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 18; Bat now, hold Drowner mana | s2: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 15 vs 18)
    - `hold everything, just attack` scored **50** (hold everything, just attack | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 18; hold everything, just attack | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 15 vs 18)
- Pilot's reasoning: "Sheoldred appears to trade away in combat across these sampled lines (attacking into their untapped Preacher is risky), so the differentiator is board development after: full deployment (Bat+Preacher) gives the most bodies but taps out into their follow-up threats, while holding mana lets me flash i"

## Turn 9 — Precombat Main [priority]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 5 lands (5 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Floodpits Drowner; [3] Cast Enduring Curiosity; [4] Cast Deep-Cavern Bat; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.; [10] {T}: Add {U}.
- **Chose: Cast Deep-Cavern Bat**
- Pilot's reasoning: "Deep-Cavern Bat gives a flying lifelink blocker for their evasive fliers plus hand disruption (exile their best card), while leaving 4 mana open after for a reactive Drowner or Enduring Curiosity."

## Turn 9 — Precombat Main [choose]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] Cut Down; [1] Enduring Curiosity; [2] Sheoldred, the Apocalypse; [3] Anoint with Affliction
- **Chose: target Anoint with Affliction**
- Pilot's reasoning: "Anoint with Affliction is unconditional creature removal that could kill my Sheoldred outright, while Cut Down can't touch it (total P+T of 9 is above its threshold) - protecting my best threat is the priority over denying their own Sheoldred or Curiosity."

## Turn 9 — Precombat Main [priority]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Floodpits Drowner; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: Cast Preacher of the Schism**
- Pilot's reasoning: "I already exiled their Anoint with Affliction, and their remaining known hand (Cut Down, Enduring Curiosity, Sheoldred) can't touch my Sheoldred - safe to keep developing with a second Preacher before combat."

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Pilot hand: Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **62** (unblocked: us 15 vs 18)
    - `attack-all` scored **40** (1 block(s), response 1: us 15 vs 18; unblocked: us 15 vs 14)
- Pilot's reasoning: "Their Preacher of the Schism also has deathtouch, so if they block Sheoldred with it, it's a mutual-kill trade - losing my life-drain engine for a replaceable 2/4 is a bad trade even though my remaining board (Bat+Preacher) stays even with theirs. Not attacking keeps my full board and Sheoldred's on"

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **15** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Pilot hand: Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **52** (after combat | after blocks they cast Cast Cut Down: us 11 vs 13)
    - `Sheoldred, the Apocalypse>Preacher of the Schism` scored **40** (after combat: us 12 vs 13)
    - `Preacher of the Schism>Preacher of the Schism` scored **60** (after combat | after blocks they cast Cast Floodpits Drowner: us 12 vs 13)
- Pilot's reasoning: "Preserving Sheoldred (my ongoing life-drain engine and best deathtouch blocker) is worth more than my second Preacher, so trading Preacher-for-Preacher while keeping Sheoldred (even tapped by their Drowner) is the best outcome; losing Sheoldred in the mutual-deathtouch trade is the worst since it's "

## Turn 11 — Precombat Main [leaf_eval/plan]
- Life: pilot **14** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 5 lands (5 untapped)
- Pilot hand: Floodpits Drowner, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack + full develop (Curiosity+Drowner)` scored **78** (attack + full develop (Curiosity+Drowner) | NOT available: cast Enduring Curiosity | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 5; attack + full develop (Curiosity+Drowner) | NOT available: cast Enduring Curiosity | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 16 vs 5; attack + full develop (Curiosity+Drowner) | NOT available: cast Enduring Curiosity | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 3)
    - `attack + hold everything reactive` scored **65** (attack + hold everything reactive | s0: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Floodpits Drowner: us 16 vs 7; attack + hold everything reactive | s0: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Floodpits Drowner: us 18 vs 3; attack + hold everything reactive | s0: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 18 vs 3; attack + hold everything reactive | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 3; attack + hold everything reactive | s1: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Floodpits Drowner: us 14 vs 9; attack + hold everything reactive | s1: they cast Cast Sheoldred, the Apocalypse | after it resolves I cast Cast Floodpits Drowner: us 16 vs 7; attack + hold everything reactive | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 7)
    - `attack + Drowner only, hold Curiosity` scored **76** (attack + Drowner only, hold Curiosity | s0: they cast Cast Enduring Curiosity | I do nothing: us 16 vs 5; attack + Drowner only, hold Curiosity | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 16 vs 5)
- Pilot's reasoning: "Sheoldred's draw-trigger life drain combined with their own Faerie Mastermind ability (which makes them draw extra cards) is swinging life hugely in my favor in almost every sampled line (opp down to 3-9, me up to 16-18); the only weaker outcomes are where they land their own Sheoldred, which is sti"

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **14** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 6 lands (6 untapped)
- Pilot hand: Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **58** (unblocked: us 14 vs 13)
    - `attack-all` scored **78** (unblocked: us 14 vs 9)
- Pilot's reasoning: "Their board is entirely tapped (Siren and Mastermind can't block), so attacking with Sheoldred is a completely free 4 damage (13->9) with zero risk; not attacking just wastes a turn of pressure while I still have 6 mana up to develop or react either way."

## Turn 11 — Postcombat Main [target]
- Life: pilot **14** vs MAD **9**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Floodpits Drowner 2/1 (sick) | 6 lands (0 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (4 untapped)
- Menu: [0] Faerie Mastermind 2/1 (B); [1] Spyglass Siren 1/1 (B)
- **Chose: target Faerie Mastermind 2/1 (B)**
- Pilot's reasoning: "Both are already tapped, so the stun counter decides which stays locked down an extra turn - Faerie Mastermind is the bigger threat (2 power flier plus card-draw utility) compared to the 1/1 Siren."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **14** vs MAD **7**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Enduring Curiosity 4/3 (sick) | 6 lands (0 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **62** (after combat: us 13 vs 7)
- Pilot's reasoning: "Forced to take 1 from their unblocked flying Siren (no flyer/reach blocker available), but I'm still well ahead on life (13 vs 7) with my own Sheoldred ready to keep attacking; their newly cast Sheoldred is a real threat but doesn't erase my life lead and tempo."

## Turn 13 — Precombat Main [leaf_eval/plan]
- Life: pilot **13** vs MAD **7**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 | 6 lands (6 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `cast Bat, attack all` scored **74** (cast Bat, attack all | s0: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 13 vs 3; cast Bat, attack all | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 13 vs 3; cast Bat, attack all | s1: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 13 vs 3; cast Bat, attack all | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 13 vs 3; cast Bat, attack all | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 13 vs 3; cast Bat, attack all | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 13 vs 3; cast Bat, attack all | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 13 vs 3)
    - `attack all, hold Bat back` scored **78** (attack all, hold Bat back | s1: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 13 vs 3; attack all, hold Bat back | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 13 vs 3)
- Pilot's reasoning: "Every sampled line ends with them at 3 life and me still at 13 with Sheoldred and Enduring Curiosity intact - a dominant, likely lethal-next-turn position regardless of whether I cast Bat pre- or post-combat; the only softer spots are where they land Kaito or their own Sheoldred as extra blockers, w"

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **13** vs MAD **7**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 | 6 lands (6 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **55** (unblocked: us 13 vs 7)
    - `attack-all` scored **82** (1 block(s), response 2: us 13 vs 3; 1 block(s), response 1: us 13 vs 3; unblocked: us 13 vs -1)
    - `hold[Sheoldred, the Apocalypse]` scored **45** (1 block(s), response 1: us 13 vs 7; unblocked: us 13 vs 3)
    - `hold[Enduring Curiosity]` scored **40** (1 block(s), response 1: us 13 vs 7; unblocked: us 13 vs 3)
- Pilot's reasoning: "Attacking with both creatures forces a bad choice: if they block either attacker with their Sheoldred it's a mutual deathtouch trade while the other still connects for 4 (opp to 3), and if they don't block it's lethal outright; holding one attacker back risks a bad trade for zero damage in the worst"

## Turn 13 — Postcombat Main [priority]
- Life: pilot **13** vs MAD **3**
- Pilot board: Enduring Curiosity 4/3 (tapped) | 6 lands (4 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Let Deep-Cavern Bat resolve to get its ETB trigger (see their hand, exile a threat); no reason to spend Go for the Throat now with no target worth killing at instant speed during my own main phase."

## Turn 13 — Postcombat Main [choose]
- Life: pilot **13** vs MAD **3**
- Pilot board: Enduring Curiosity 4/3 (tapped), Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Menu: [0] Enduring Curiosity; [1] Sheoldred, the Apocalypse; [2] Go for the Throat; [3] Anoint with Affliction
- **Chose: target Sheoldred, the Apocalypse**
- Pilot's reasoning: "Their Sheoldred would both block/kill any of my attackers with deathtouch and gain them 2 life per draw while draining me - the single biggest swing against my plan to close this out at 3 life, more dangerous than either removal spell."

## Turn 14 — Precombat Main [priority]
- Life: pilot **13** vs MAD **3**
- Pilot board: Enduring Curiosity 4/3 (tapped), Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 | 4 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Nothing I can do to stop their removal - I have no counterspell or protection; just let it resolve and reassess next turn."

## Turn 14 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **13** vs MAD **3**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 7 lands (5 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **68** (after combat: us 11 vs 3)
    - `Deep-Cavern Bat>Faerie Mastermind` scored **52** (after combat: us 14 vs 3)
- Pilot's reasoning: "My hand is down to just Go for the Throat, so Deep-Cavern Bat is my only remaining clock against their 3 life; trading it away for Faerie Mastermind leaves me with zero board presence and no way to actually close out the game beyond topdecks, while taking 2 and keeping Bat preserves a real path to f"

## Turn 15 — Precombat Main [leaf_eval/plan]
- Life: pilot **11** vs MAD **3**
- Pilot board: Deep-Cavern Bat 1/1 | 7 lands (7 untapped)
- Pilot hand: Go for the Throat, Island
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack Bat, hold removal` scored **55** (attack Bat, hold removal | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 12 vs 3; attack Bat, hold removal | s1: they cast Cast Enduring Curiosity | I do nothing: us 12 vs 3; attack Bat, hold removal | s2: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 12 vs 3)
    - `Go for the Throat on Siren, then attack unblocked` scored **56** (Go for the Throat on Siren, then attack unblocked | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 12 vs 3; Go for the Throat on Siren, then attack unblocked | s2: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 12 vs 3)
- Pilot's reasoning: "My Bat trades away and I'm hellbent (0 cards) in all samples, but I'm still at 12 life vs their 3 - a massive life buffer even as they stabilize with a Sheoldred or Curiosity; whether I spent Go for the Throat on the Siren or held it doesn't change much since it appears spent either way by the time "

## Turn 15 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **11** vs MAD **3**
- Pilot board: Deep-Cavern Bat 1/1 | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **58** (unblocked: us 11 vs 3)
    - `attack-all` scored **55** (1 block(s), response 1: us 12 vs 3; unblocked: us 12 vs 2)
- Pilot's reasoning: "Attacking risks trading Bat for their Siren (fine value, keeps them at 3, I gain 1 life) but the upside of getting through unblocked drops them to 2 life which is huge this close to lethal; not attacking is safe but makes zero progress."

## Turn 16 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **11** vs MAD **3**
- Pilot board: Deep-Cavern Bat 1/1 | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped), Enduring Curiosity 4/3 (sick) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **60** (after combat: us 9 vs 3)
    - `Deep-Cavern Bat>Faerie Mastermind` scored **65** (after combat: us 12 vs 3)
- Pilot's reasoning: "Blocking trades my Bat for their Faerie Mastermind (denying their card-draw engine) and nets me a lifelink point (11->12), which is strictly better than taking 2 unblocked given they've now got their own Enduring Curiosity developing - removing a piece of their board matters more than keeping a 1/1 "

## Turn 17 — Precombat Main [leaf_eval/plan]
- Life: pilot **12** vs MAD **3**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat, Preacher of the Schism
- MAD board: Spyglass Siren 1/1, Enduring Curiosity 4/3 (sick) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `cast Preacher, hold removal` scored **53** (cast Preacher, hold removal | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | on the stack I cast Cast Go for the Throat: us 12 vs 3; cast Preacher, hold removal | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | after it resolves I cast Cast Go for the Throat: us 12 vs 3; cast Preacher, hold removal | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 12 vs 3; cast Preacher, hold removal | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 12 vs 3; cast Preacher, hold removal | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 12 vs 3; cast Preacher, hold removal | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | on the stack I cast Cast Go for the Throat: us 12 vs 3; cast Preacher, hold removal | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | after it resolves I cast Cast Go for the Throat: us 12 vs 3; cast Preacher, hold removal | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 12 vs 3)
    - `cast Preacher + kill their Curiosity` scored **55** (cast Preacher + kill their Curiosity | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 12 vs 3; cast Preacher + kill their Curiosity | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 12 vs 3)
- Pilot's reasoning: "All lines keep me at a commanding 12-3 life lead while I develop Preacher and hold or spend removal reactively; their developing threats (Restless Reef animated, Kaito, their own Curiosity) are concerning long-term but not urgent given how far ahead I am on life."

## Turn 18 — Precombat Main [priority]
- Life: pilot **12** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 (sick) | 8 lands (5 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1, Enduring Curiosity 4/3 | 6 lands (2 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Go for the Throat can't target a spell on the stack - need to let Sheoldred resolve first, then kill it once it's an actual permanent."

## Turn 18 — Precombat Main [priority]
- Life: pilot **12** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 (sick) | 8 lands (5 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1, Enduring Curiosity 4/3, Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.
- **Chose: Cast Go for the Throat**
- Pilot's reasoning: "Their Sheoldred is now a resolved permanent and the single biggest threat on the board - killing it now removes the life-drain engine before it can swing the race back in their favor."

## Turn 18 — Precombat Main [target]
- Life: pilot **12** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 (sick) | 8 lands (5 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1, Enduring Curiosity 4/3, Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (0 untapped)
- Menu: [0] Enduring Curiosity 4/3 (B); [1] Sheoldred, the Apocalypse 4/5 (B); [2] Preacher of the Schism 2/4 (A); [3] Spyglass Siren 1/1 (B)
- **Chose: target Sheoldred, the Apocalypse 4/5 (B)**
- Pilot's reasoning: "Sheoldred is the biggest threat - its draw-trigger life swings could stabilize them and drain me, far more dangerous than their Curiosity or Siren."

## Turn 18 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **12** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 (sick) | 8 lands (3 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **65** (after combat: us 7 vs 3)
    - `Preacher of the Schism>Enduring Curiosity` scored **55** (after combat: us 11 vs 3)
- Pilot's reasoning: "Taking 5 unblocked (12->7) is comfortably affordable given my life lead, and keeping Preacher of the Schism alive preserves my only attacker to close out the game against their 3 life next turn; trading it away for their Curiosity (which just returns as a non-creature enchantment anyway) sets my clo"

## Turn 19 — Precombat Main [leaf_eval/plan]
- Life: pilot **7** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (8 untapped)
- Pilot hand: Spyglass Siren
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `cast Siren, attack Preacher` scored **63** (cast Siren, attack Preacher | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 6 vs 3; cast Siren, attack Preacher | s1: they cast Cast Enduring Curiosity | I do nothing: us 6 vs 3; cast Siren, attack Preacher | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 6 vs 3)
    - `attack Preacher only, hold Siren` scored **65** (attack Preacher only, hold Siren | s1: they cast Cast Enduring Curiosity | I do nothing: us 6 vs 3)
- Pilot's reasoning: "Preacher's attack killed their Faerie Mastermind blocker via deathtouch and survived, plus its own trigger (I have most life) drew me a card at the cost of 1 life; I'm still commanding at 6 vs 3 life regardless of what they develop in response (Kaito, another Curiosity, or animating Restless Reef)."

## Turn 19 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **7** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 | 8 lands (8 untapped)
- Pilot hand: Spyglass Siren
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **58** (unblocked: us 7 vs 3)
    - `attack-all` scored **62** (1 block(s), response 1: us 6 vs 3; unblocked: us 6 vs 1)
- Pilot's reasoning: "Attacking is strictly good here: if blocked, deathtouch kills their Faerie Mastermind while Preacher survives (I just draw a card and lose 1 from my own trigger since I have most life); if unblocked they drop to 1 life, nearly lethal. Not attacking wastes a turn of pressure against their critically "

## Turn 19 — Postcombat Main [priority]
- Life: pilot **6** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 (tapped) | 9 lands (8 untapped)
- Pilot hand: Island
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped) | 7 lands (0 untapped)
- Menu: [0] pass priority; [1] Play Island; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.
- **Chose: {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.**
- Pilot's reasoning: "Free value from the Map Token - explores with Preacher of the Schism, either filtering my draw or growing my best threat with a +1/+1 counter, at minimal mana cost."

## Turn 19 — Postcombat Main [priority]
- Life: pilot **6** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 (tapped) | 8 lands (6 untapped)
- Pilot hand: Island, Restless Reef
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped) | 7 lands (0 untapped)
- Menu: [0] pass priority; [1] Play Island; [2] Play Restless Reef; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.
- **Chose: Play Island**
- Pilot's reasoning: "Playing Island keeps a land untapped this turn for flexibility; Restless Reef always enters tapped so there's no rush to play it now."

## Turn 21 — Precombat Main [leaf_eval/plan]
- Life: pilot **1** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4 | 9 lands (9 untapped)
- Pilot hand: Restless Reef, Floodpits Drowner
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Enduring Curiosity 4/3 (sick) | 8 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `defensive - stun a Curiosity, hold Preacher back` scored **46** (defensive - stun a Curiosity, hold Preacher back | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 1 vs 3; defensive - stun a Curiosity, hold Preacher back | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 1 vs 3; defensive - stun a Curiosity, hold Preacher back | s1: they cast Cast Enduring Curiosity | on the stack I cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 1 vs 3; defensive - stun a Curiosity, hold Preacher back | s1: they cast Cast Enduring Curiosity | I do nothing: us 1 vs 3; defensive - stun a Curiosity, hold Preacher back | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | on the stack I cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 1 vs 3; defensive - stun a Curiosity, hold Preacher back | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | after it resolves I cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 1 vs 3; defensive - stun a Curiosity, hold Preacher back | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 1 vs 3)
    - `aggressive - attack Preacher, stun a Curiosity` scored **38** (aggressive - attack Preacher, stun a Curiosity | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 1 vs 1; aggressive - attack Preacher, stun a Curiosity | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 1 vs 1; aggressive - attack Preacher, stun a Curiosity | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 1 vs 1)
- Pilot's reasoning: "At 1 life, survival is paramount: the defensive line keeps Preacher (2/4 deathtouch) and Drowner both untapped as blockers, while the aggressive line taps Preacher away (my best blocker) for a whole turn and leaves only a 2/1 and a 1/1 token to block against their growing board (Kaito, extra Curiosi"

## Turn 21 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **1** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 (sick) | 9 lands (7 untapped)
- Pilot hand: Restless Reef
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Enduring Curiosity 4/3 (sick) | 8 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **55** (unblocked: us 1 vs 3)
    - `attack-all` scored **55** (1 block(s), response 1: us 1 vs 3; unblocked: us 1 vs 1)
- Pilot's reasoning: "Attacking with Preacher is safe here: if blocked it trades for their only available blocker while creating a Vampire lifelink token (leaving me with the same 2 blockers, just different composition), and if unblocked it drops them to 1 life - a huge swing. Not attacking is equally safe defensively bu"

## Turn 22 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **1** vs MAD **3**
- Pilot board: Preacher of the Schism 2/4, Floodpits Drowner 2/1 (sick) | 9 lands (7 untapped)
- Pilot hand: Restless Reef
- MAD board: Spyglass Siren 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Enduring Curiosity 4/3 (tapped), Deep-Cavern Bat 1/1 (sick) | 9 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **0** (after combat | after blocks they cast Cast Floodpits Drowner: us -4 vs 3)
    - `Preacher of the Schism>Enduring Curiosity` scored **0** (after combat | after blocks they cast Cast Cut Down: us 0 vs 3)
    - `Floodpits Drowner>Enduring Curiosity` scored **0** (after combat: us 0 vs 3)
    - `Preacher of the Schism>Enduring Curiosity, Floodpits Drowner>Enduring Curiosity` scored **0** (after combat | after blocks they cast Cast Floodpits Drowner: us 0 vs 3)
- Pilot's reasoning: "Neither Preacher of the Schism nor Floodpits Drowner have flying or reach, so Spyglass Siren's 1 damage is unblockable and lethal at 1 life regardless of how I assign blocks on the ground - every line here is a loss."
