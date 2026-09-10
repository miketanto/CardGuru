# Decision review — g1.jsonl

Result: **pilot won** in 15 turns. 30 real decisions out of 227 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Three lands (two colors covered) plus a strong curve: Floodpits Drowner on 2, Preacher on 3, Sheoldred on 4 - excellent keep."

## Turn 1 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Darkslick Shores` scored **51** (play Darkslick Shores | s0: they do nothing: us 20 vs 20; play Darkslick Shores | s1: they do nothing: us 20 vs 20; play Darkslick Shores | s2: they do nothing: us 20 vs 20)
    - `play Island` scored **50** (play Island | s0: they do nothing: us 20 vs 20; play Island | s1: they do nothing: us 20 vs 20; play Island | s2: they do nothing: us 20 vs 20)
    - `play Swamp` scored **50** (play Swamp | s0: they do nothing: us 20 vs 20; play Swamp | s1: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Turn-1 land drops are all near-identical parity positions; Darkslick Shores is marginally best since it provides both colors untapped and preserves basics for flexibility later."

## Turn 3 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play land, flash Drowner on Siren now` scored **48** (play land, flash Drowner on Siren now | s0: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; play land, flash Drowner on Siren now | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `play land, hold Drowner for a better flash target` scored **47** (play land, hold Drowner for a better flash target | s0: they cast Cast Go for the Throat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play land, hold Drowner for a better flash target | s0: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; play land, hold Drowner for a better flash target | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; play land, hold Drowner for a better flash target | s1: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; play land, hold Drowner for a better flash target | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Casting Drowner now on the 1/1 Siren is fine tempo but low-impact; holding it preserves the option to answer a bigger threat (Deep-Cavern Bat) or even see the opponent waste removal, generally as good or better across the sampled opponent lines."

## Turn 4 — Precombat Main [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 3 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.
- **Chose: PASS**
- Pilot's reasoning: "Faerie Mastermind is still on the stack and isn't a legal target yet; passing lets it resolve so I can decide with full information whether it's worth stunning versus saving Drowner for a bigger threat."

## Turn 5 — Precombat Main [leaf_eval/plan]
- Life: pilot **19** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop Preacher, hold Drowner for later flash` scored **35** (develop Preacher, hold Drowner for later flash | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; develop Preacher, hold Drowner for later flash | s1: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
    - `stun Faerie Mastermind now, hold Preacher` scored **40** (stun Faerie Mastermind now, hold Preacher | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; stun Faerie Mastermind now, hold Preacher | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; stun Faerie Mastermind now, hold Preacher | s2: they cast Cast Cut Down | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Losing Preacher to removal before it does anything is worse than losing Drowner after it already banked its tap+stun value; Drowner as a removal-bait target keeps my stronger card safe in hand for a better window."

## Turn 7 — Precombat Main [leaf_eval/plan]
- Life: pilot **16** vs MAD **20**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `deploy Sheoldred, the Apocalypse` scored **55** (deploy Sheoldred, the Apocalypse | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 16; deploy Sheoldred, the Apocalypse | s1: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 18)
    - `redeploy Preacher of the Schism` scored **35** (redeploy Preacher of the Schism | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20; redeploy Preacher of the Schism | s1: they cast Cast Enduring Curiosity | I do nothing: us 16 vs 20; redeploy Preacher of the Schism | s2: they cast Cast Floodpits Drowner | I do nothing: us 16 vs 20)
    - `stun a flier with Drowner, hold rest` scored **38** (stun a flier with Drowner, hold rest | s0: they cast Cast Anoint with Affliction | I do nothing: us 16 vs 20; stun a flier with Drowner, hold rest | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20; stun a flier with Drowner, hold rest | s2: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 20)
- Pilot's reasoning: "Sheoldred is the standout: it swings the life race immediately via the draw triggers and is a huge deathtouch body their small fliers can't profitably engage, whereas Preacher or Drowner leave me thin on board or exposed to a tempo-losing removal/stun on my only creature."

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **16** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 (sick) | 4 lands (0 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **42** (after combat: us 13 vs 18)
- Pilot's reasoning: "No other block options existed (Sheoldred can't block fliers); I'm now behind on life (13 vs 18) but Sheoldred is a dominant deathtouch body that threatens a fast clock and its draw-trigger engine can still swing the race back."

## Turn 9 — Precombat Main [leaf_eval/plan]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no attack, full development (Bat + Preacher)` scored **48** (no attack, full development (Bat + Preacher) | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 14; no attack, full development (Bat + Preacher) | s1: they cast Cast Anoint with Affliction | I do nothing: us 15 vs 16; no attack, full development (Bat + Preacher) | s2: they cast Cast Go for the Throat | I do nothing: us 15 vs 16)
    - `attack with Sheoldred, still develop` scored **35** (attack with Sheoldred, still develop | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 18; attack with Sheoldred, still develop | s1: they cast Cast Floodpits Drowner | I do nothing: us 15 vs 18; attack with Sheoldred, still develop | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 15 vs 18)
- Pilot's reasoning: "Holding Sheoldred back to develop a full three-creature board is clearly stronger across all opponent responses; attacking risks trading my premium engine for their Preacher and still leaves me exposed to follow-up disruption on the creatures that remain."

## Turn 9 — Precombat Main [priority]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Let Deep-Cavern Bat resolve to get its ETB (flying/lifelink body plus hand disruption); I still have 3 mana up to follow with Preacher of the Schism as planned."

## Turn 9 — Precombat Main [priority]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Let Deep-Cavern Bat's trigger resolve so I can see their hand and choose the best card to exile."

## Turn 9 — Precombat Main [choose]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] Cut Down; [1] Sheoldred, the Apocalypse; [2] Anoint with Affliction; [3] Enduring Curiosity
- **Chose: target Anoint with Affliction**
- Pilot's reasoning: "Anoint with Affliction is an unconditional removal spell that can kill my already-resolved Sheoldred (Cut Down can't touch it due to power/toughness restrictions), and protecting my main engine/threat is worth more than denying their as-yet-uncastable second Sheoldred."

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **64** (unblocked: us 15 vs 18)
    - `attack-all` scored **40** (1 block(s), response 1: us 15 vs 18; unblocked: us 15 vs 14)
- Pilot's reasoning: "With their known removal (Anoint) now exiled and Cut Down unable to target Sheoldred, holding it back keeps my best asset completely safe as a blocker/engine; attacking risks a deathtouch trade with their Preacher that loses my superior card even though an unblocked swing would be great."

## Turn 9 — Postcombat Main [priority]
- Life: pilot **15** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Floodpits Drowner; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: Cast Preacher of the Schism**
- Pilot's reasoning: "Complete the planned development: cast Preacher of the Schism with my remaining 3 mana for another deathtouch blocker/body."

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **15** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Pilot hand: Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **25** (after combat | after blocks they cast Cast Go for the Throat: us 10 vs 13)
    - `Sheoldred, the Apocalypse>Preacher of the Schism` scored **50** (after combat: us 12 vs 13)
    - `Preacher of the Schism>Preacher of the Schism` scored **65** (after combat: us 12 vs 13)
- Pilot's reasoning: "Blocking with my Preacher (not Sheoldred) trades evenly with their Preacher while keeping Sheoldred fully intact as my premier blocker/engine; not blocking risks eating 5 damage and losing Sheoldred to follow-up removal, and blocking with Sheoldred needlessly trades away my best card."

## Turn 11 — Precombat Main [leaf_eval/plan]
- Life: pilot **14** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 5 lands (5 untapped)
- Pilot hand: Floodpits Drowner, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `full development + attack unblocked Sheoldred` scored **82** (full development + attack unblocked Sheoldred | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 5; full development + attack unblocked Sheoldred | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 7; full development + attack unblocked Sheoldred | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 16 vs 5)
    - `attack only, hold both spells up` scored **78** (attack only, hold both spells up | s0: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Floodpits Drowner: us 16 vs 7; attack only, hold both spells up | s0: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Floodpits Drowner: us 18 vs 3; attack only, hold both spells up | s0: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 18 vs 3; attack only, hold both spells up | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 3; attack only, hold both spells up | s1: they cast Cast Enduring Curiosity | on the stack I cast Cast Floodpits Drowner: us 16 vs 7; attack only, hold both spells up | s1: they cast Cast Enduring Curiosity | after it resolves I cast Cast Floodpits Drowner: us 16 vs 5; attack only, hold both spells up | s1: they cast Cast Enduring Curiosity | I do nothing: us 16 vs 5)
    - `cast Curiosity, hold Drowner, attack` scored **90** (cast Curiosity, hold Drowner, attack | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 3)
- Pilot's reasoning: "Every line leaves me massively ahead (opponent life crashing to single digits from their own draw triggers plus Sheoldred's unblocked hit), with holding mana up giving slightly more flexibility to answer their plays instantly rather than tapping out."

## Turn 11 — Precombat Main [priority]
- Life: pilot **14** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 6 lands (2 untapped)
- Pilot hand: Floodpits Drowner
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (4 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Let Enduring Curiosity resolve; I still have 2 mana up to flash Floodpits Drowner in reactively during their turn if needed."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **14** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 (sick) | 6 lands (2 untapped)
- Pilot hand: Floodpits Drowner
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **60** (unblocked: us 14 vs 13)
    - `attack-all` scored **72** (unblocked: us 14 vs 9)
- Pilot's reasoning: "Attacking is completely free right now since both their creatures are tapped and cannot block; swinging for 4 unblocked damage while keeping Drowner mana up is strictly better than not attacking."

## Turn 11 — Postcombat Main [priority]
- Life: pilot **16** vs MAD **7**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Enduring Curiosity 4/3 (sick) | 6 lands (2 untapped)
- Pilot hand: Floodpits Drowner, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (4 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] Cast Deep-Cavern Bat; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {B}.
- **Chose: Cast Deep-Cavern Bat**
- Pilot's reasoning: "Deep-Cavern Bat has no flash, so it must be cast now at sorcery speed or not at all this turn; it adds a flying/lifelink blocker and lets me strip another card from their hand while they're at 7 life. Floodpits Drowner keeps its flash flexibility for later regardless."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **16** vs MAD **5**
- Pilot board: Enduring Curiosity 4/3 (sick) | 6 lands (0 untapped)
- Pilot hand: Floodpits Drowner
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **72** (after combat | after blocks they cast Cast Go for the Throat: us 13 vs 5)
- Pilot's reasoning: "No blocks available against their fliers regardless; even after losing Enduring Curiosity to follow-up removal, I'm at 13 life versus their 5 with only two small tapped fliers on their side - I'm heavily favored to close this out soon."

## Turn 13 — Precombat Main [leaf_eval/plan]
- Life: pilot **13** vs MAD **5**
- Pilot board: Enduring Curiosity 4/3 | 6 lands (6 untapped)
- Pilot hand: Floodpits Drowner, Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack, then deploy Drowner` scored **90** (attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | on the stack I cast Cast Go for the Throat: us 13 vs 1; attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | after it resolves I cast Cast Go for the Throat: us 13 vs 1; attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 13 vs 1; attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 13 vs 1; attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 13 vs 1; attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 13 vs 1; attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 13 vs 1; attack, then deploy Drowner | NOT available: cast Floodpits Drowner | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 13 vs 1)
    - `attack, hold both spells up` scored **90** (attack, hold both spells up | s0: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 13 vs 1; attack, hold both spells up | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 13 vs 1; attack, hold both spells up | s1: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 13 vs 1; attack, hold both spells up | s1: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 13 vs 1; attack, hold both spells up | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 13 vs 1)
- Pilot's reasoning: "Opponent is now at 1 life in every line with only small non-lethal blockers on their fliers; I hold Go for the Throat and multiple bodies, making next turn's kill essentially guaranteed barring a board wipe they don't have."

## Turn 13 — Precombat Main [priority]
- Life: pilot **13** vs MAD **5**
- Pilot board: Enduring Curiosity 4/3 | 6 lands (6 untapped)
- Pilot hand: Floodpits Drowner, Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (3 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] Cast Go for the Throat; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Nothing to do precombat; move to combat and attack with Enduring Curiosity into their tapped, blockerless board."

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **13** vs MAD **5**
- Pilot board: Enduring Curiosity 4/3 | 6 lands (6 untapped)
- Pilot hand: Floodpits Drowner, Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **65** (unblocked: us 13 vs 5)
    - `attack-all` scored **92** (unblocked: us 13 vs 1)
- Pilot's reasoning: "Attacking is free damage since both their creatures are tapped and can't block, putting them at 1 life and drawing me a card; not attacking wastes a completely safe lethal-adjacent swing."

## Turn 13 — Postcombat Main [priority]
- Life: pilot **13** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3 (tapped) | 6 lands (4 untapped)
- Pilot hand: Go for the Throat, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (3 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Let Floodpits Drowner resolve to complete my planned development; opponent is at 1 life with no way to block it either."

## Turn 13 — Postcombat Main [target]
- Life: pilot **13** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3 (tapped), Floodpits Drowner 2/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Go for the Throat, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (3 untapped)
- Menu: [0] Faerie Mastermind 2/1 (B); [1] Spyglass Siren 1/1 (B)
- **Chose: target Faerie Mastermind 2/1 (B)**
- Pilot's reasoning: "Stunning Faerie Mastermind (their better creature, with a card-advantage ability) delays it an extra turn and denies them a blocker/attacker while they're at 1 life and I move to close out the game."

## Turn 13 — Postcombat Main [priority]
- Life: pilot **13** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3 (tapped), Floodpits Drowner 2/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Go for the Throat, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (3 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] Play Island; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {B}.
- **Chose: Play Island**
- Pilot's reasoning: "Play my land for the turn; hold Go for the Throat with remaining mana to answer any blocker or threat on their turn."

## Turn 14 — Precombat Main [priority]
- Life: pilot **13** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3 (tapped), Floodpits Drowner 2/1 (sick) | 7 lands (5 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Go for the Throat; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.; [7] {T}: Add {U}.
- **Chose: PASS**
- Pilot's reasoning: "Sheoldred isn't a legal target yet while on the stack; pass to let it resolve, then kill it with Go for the Throat before it can block or gain them life off a future draw."

## Turn 14 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **13** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3 (tapped), Floodpits Drowner 2/1 (sick) | 7 lands (5 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **78** (after combat: us 12 vs 1)
- Pilot's reasoning: "No blockers available against their flying Siren regardless; I still hold Go for the Throat to remove their newly-resolved Sheoldred, and they remain at 1 life with no way to stabilize enough - I'm heavily favored."

## Turn 15 — Precombat Main [leaf_eval/plan]
- Life: pilot **10** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3, Floodpits Drowner 2/1 | 7 lands (7 untapped)
- Pilot hand: Go for the Throat, Preacher of the Schism
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `kill Sheoldred first, then attack all for guaranteed lethal` scored **100** (kill Sheoldred first, then attack all for guaranteed lethal | s0: they do nothing: us 10 vs -5; kill Sheoldred first, then attack all for guaranteed lethal | s1: they do nothing: us 10 vs -5)
    - `attack all without removal (they only have one blocker)` scored **None** ()
- Pilot's reasoning: "Opponent's life total goes to -5 in both sampled lines - this line is simply lethal and wins the game outright."

## Turn 15 — Precombat Main [priority]
- Life: pilot **10** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3, Floodpits Drowner 2/1 | 7 lands (5 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 6 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.; [7] {T}: Add {U}.
- **Chose: PASS**
- Pilot's reasoning: "Sheoldred is already destroyed and they have no untapped blockers; move to combat and attack for lethal with Enduring Curiosity and Floodpits Drowner."

## Turn 15 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **10** vs MAD **1**
- Pilot board: Enduring Curiosity 4/3, Floodpits Drowner 2/1 | 7 lands (5 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **70** (unblocked: us 10 vs 1)
    - `attack-all` scored **100** (unblocked: us 10 vs -5)
    - `hold[Enduring Curiosity]` scored **100** (unblocked: us 10 vs -1)
    - `hold[Floodpits Drowner]` scored **100** (unblocked: us 10 vs -3)
- Pilot's reasoning: "Attacking with any creature is lethal since opponent is at 1 life with no blockers or mana; attack-all secures the win outright, so not attacking is the only clearly worse option."
