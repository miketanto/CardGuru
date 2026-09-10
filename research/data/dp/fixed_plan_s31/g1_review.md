# Decision review — g1.jsonl

Result: **pilot lost** in 12 turns. 21 real decisions out of 171 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Swamp, Undercity Sewers, Undercity Sewers, Undercity Sewers, Preacher of the Schism, Deep-Cavern Bat, Faerie Mastermind
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "4 lands (1 Swamp + 3 Undercity Sewers, both colors covered) with a clean curve of Deep-Cavern Bat/Faerie Mastermind at 2 and Preacher of the Schism at 3 - an easy keep."

## Turn 1 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Swamp, Undercity Sewers, Undercity Sewers, Undercity Sewers, Preacher of the Schism, Deep-Cavern Bat, Faerie Mastermind
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `tapped land first` scored **52** (tapped land first | s0: they do nothing: us 20 vs 20; tapped land first | s1: they do nothing: us 20 vs 20)
    - `swamp first` scored **50** (swamp first | s0: they do nothing: us 20 vs 20; swamp first | s1: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Turn 1 with no plays either way; playing the tapped Undercity Sewers now (with its surveil) is marginally better sequencing than a Swamp since Swamps stay flexible for later untapped turns, but the difference is tiny at parity."

## Turn 3 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Swamp, Undercity Sewers, Undercity Sewers, Preacher of the Schism, Deep-Cavern Bat, Faerie Mastermind, Island
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `cast Bat now for info` scored **52** (cast Bat now for info | s0: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; cast Bat now for info | s1: they do nothing: us 20 vs 20)
    - `hold up flash Mastermind` scored **45** (hold up flash Mastermind | s0: they do nothing: us 20 vs 20; hold up flash Mastermind | s1: they cast Cast Spyglass Siren | on the stack I cast Cast Faerie Mastermind: us 20 vs 20; hold up flash Mastermind | s1: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; hold up flash Mastermind | s2: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Faerie Mastermind: us 20 vs 20; hold up flash Mastermind | s2: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Faerie Mastermind: us 20 vs 20; hold up flash Mastermind | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
- Pilot's reasoning: "All lines are near parity this early (life untouched, small creatures); casting Bat now for board presence/info scores slightly better when they don't respond, while passing into their Spyglass Siren or Bat unanswered (leaves 4/7) is the worst since we cede the board and sometimes lose Preacher to e"

## Turn 3 — Precombat Main [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Undercity Sewers, Undercity Sewers, Preacher of the Schism, Deep-Cavern Bat, Faerie Mastermind, Island
- MAD board: no creatures | 1 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Deep-Cavern Bat; [2] Cast Faerie Mastermind; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {B}.
- **Chose: Cast Deep-Cavern Bat**
- Pilot's reasoning: "Leaf-eval showed casting Bat now has a better worst-case (52) than holding up mana for Mastermind (worst-case 45 when they land Spyglass Siren unanswered); get the flying lifelinker down now for board presence and hand info."

## Turn 3 — Precombat Main [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 2 lands (0 untapped)
- Pilot hand: Undercity Sewers, Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Island
- MAD board: no creatures | 1 lands (1 untapped)
- Menu: [0] Floodpits Drowner; [1] Preacher of the Schism; [2] Preacher of the Schism; [3] Enduring Curiosity; [4] Kaito, Bane of Nightmares
- **Chose: target Kaito, Bane of Nightmares**
- Pilot's reasoning: "Kaito, Bane of Nightmares is a legendary planeswalker - by far the highest-impact, hardest-to-answer card in their hand compared to two more Preachers, an Enduring Curiosity, or a Floodpits Drowner, so exile it now while I can."

## Turn 5 — Upkeep [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Undercity Sewers, Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Island
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Nothing on the stack and no reason to flash in Mastermind during my own upkeep; better to wait for main phase to sequence land + Preacher, or hold Mastermind for their turn."

## Turn 5 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Undercity Sewers, Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Island, Preacher of the Schism
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Island, cast Preacher` scored **38** (play Island, cast Preacher | s0: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; play Island, cast Preacher | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; play Island, cast Preacher | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
    - `play Island, hold up Mastermind flash` scored **42** (play Island, hold up Mastermind flash | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Faerie Mastermind: us 20 vs 20; play Island, hold up Mastermind flash | s0: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Faerie Mastermind: us 20 vs 20; play Island, hold up Mastermind flash | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; play Island, hold up Mastermind flash | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Faerie Mastermind: us 20 vs 20; play Island, hold up Mastermind flash | s1: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Faerie Mastermind: us 20 vs 20; play Island, hold up Mastermind flash | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Casting Preacher now gives a strong deathtouch wall/threat and is fine against most of their responses, only bad if they have Go for the Throat ready (leaf1); holding up Mastermind flash is solid when I flash it in response to their Bat, but doing nothing lets their Bat resolve and often exile my se"

## Turn 6 — Precombat Main [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 3 lands (3 untapped)
- Pilot hand: Undercity Sewers, Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Preacher of the Schism
- MAD board: Floodpits Drowner 2/1 | 3 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.
- **Chose: PASS**
- Pilot's reasoning: "Their Preacher of the Schism is just a creature spell with no reason to respond to on the stack - Faerie Mastermind doesn't interact with it, so I'll let it resolve and decide my response to the resulting board after."

## Turn 7 — Precombat Main [leaf_eval/plan]
- Life: pilot **18** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 | 3 lands (3 untapped)
- Pilot hand: Undercity Sewers, Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Kaito, Bane of Nightmares
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack Bat, Ninjutsu into Kaito` scored **38** (attack Bat, Ninjutsu into Kaito | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 19; attack Bat, Ninjutsu into Kaito | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 19; attack Bat, Ninjutsu into Kaito | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 19)
    - `cast Preacher, no attack` scored **40** (cast Preacher, no attack | s0: they do nothing: us 18 vs 20; cast Preacher, no attack | s1: they cast Cast Enduring Curiosity | I do nothing: us 18 vs 20; cast Preacher, no attack | s2: they cast Cast Preacher of the Schism | I do nothing: us 18 vs 20)
    - `cast Preacher, attack Bat anyway` scored **35** (cast Preacher, attack Bat anyway | s0: they cast Cast Go for the Throat | I do nothing: us 19 vs 19; cast Preacher, attack Bat anyway | s1: they cast Cast Faerie Mastermind | I do nothing: us 19 vs 19; cast Preacher, attack Bat anyway | s2: they cast Cast Enduring Curiosity | I do nothing: us 19 vs 19)
- Pilot's reasoning: "Casting Preacher now and holding Bat back as a blocker (candidate 2) has the safest floor since it avoids exposing a second creature to their Go for the Throat; the Ninjutsu/attack lines have good upside but their removal or a second Preacher on their side drags the worst case down."

## Turn 7 — Precombat Main [priority]
- Life: pilot **18** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 | 4 lands (3 untapped)
- Pilot hand: Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Kaito, Bane of Nightmares
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.
- **Chose: PASS**
- Pilot's reasoning: "Surveil trigger from Undercity Sewers on the stack, nothing to respond to - pass to let it resolve, then proceed to cast Preacher of the Schism this main phase."

## Turn 7 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **18** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 | 4 lands (3 untapped)
- Pilot hand: Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Kaito, Bane of Nightmares
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 18 vs 20)
    - `attack-all` scored **62** (unblocked: us 19 vs 19)
- Pilot's reasoning: "Opponent is fully tapped out (0 mana) so attacking with Bat is completely free - no risk of instant-speed removal - and sets up the Ninjutsu into Kaito for extra damage plus a lifelink tick; not attacking wastes a safe opportunity."

## Turn 7 — Postcombat Main [priority]
- Life: pilot **18** vs MAD **17**
- Pilot board: Kaito, Bane of Nightmares 3/4 (tapped) | 4 lands (0 untapped)
- Pilot hand: Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Menu: [0] pass priority; [1] +1: You get an emblem with "Ninjas you control get +1/+1."; [2] 0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.; [3] -2: Tap target creature. Put two stun counters on it.
- **Chose: 0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.**
- Pilot's reasoning: "Kaito's 0 ability surveils 2 and draws a card since the opponent lost life this turn (3 damage from the Ninjutsu attack) - free card advantage and selection at zero mana cost, better than the marginal +1 emblem with only one Ninja or spending loyalty on -2 when there's no urgent threat to tap."

## Turn 9 — Precombat Main [leaf_eval/plan]
- Life: pilot **18** vs MAD **17**
- Pilot board: no creatures | 4 lands (4 untapped)
- Pilot hand: Undercity Sewers, Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Deep-Cavern Bat, Cut Down, Enduring Curiosity
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `Bat + Mastermind (two bodies + info)` scored **30** (Bat + Mastermind (two bodies + info) | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 18 vs 17; Bat + Mastermind (two bodies + info) | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 18 vs 17)
    - `Preacher, hold up Cut Down` scored **22** (Preacher, hold up Cut Down | s0: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Cut Down: us 18 vs 17; Preacher, hold up Cut Down | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 18 vs 17; Preacher, hold up Cut Down | s1: they cast Cast Enduring Curiosity | on the stack I cast Cast Cut Down: us 18 vs 17; Preacher, hold up Cut Down | s1: they cast Cast Enduring Curiosity | I do nothing: us 18 vs 17)
    - `Enduring Curiosity (resilient threat)` scored **25** (Enduring Curiosity (resilient threat) | s0: they cast Cast Floodpits Drowner | I do nothing: us 18 vs 17; Enduring Curiosity (resilient threat) | s1: they cast Cast Preacher of the Schism | I do nothing: us 18 vs 17; Enduring Curiosity (resilient threat) | s2: they cast Cast Go for the Throat | I do nothing: us 18 vs 17)
- Pilot's reasoning: "Opponent has strong follow-ups across the board (Sheoldred, a second Preacher, Enduring Curiosity, extra threats) that keep outnumbering whatever I develop; the Bat+Mastermind line has the safest floor since it develops two bodies without over-committing, while holding up Cut Down for just one remov"

## Turn 9 — Precombat Main [priority]
- Life: pilot **18** vs MAD **17**
- Pilot board: no creatures | 5 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Deep-Cavern Bat, Cut Down, Enduring Curiosity
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (tapped) | 5 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] Cast Cut Down; [3] Cast Enduring Curiosity; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.; [7] {T}: Add {U}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Surveil trigger from Undercity Sewers on the stack - nothing to respond to, pass to let it resolve then proceed with casting Deep-Cavern Bat and Faerie Mastermind this main phase."

## Turn 9 — Precombat Main [priority]
- Life: pilot **18** vs MAD **17**
- Pilot board: no creatures | 5 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Deep-Cavern Bat, Cut Down, Enduring Curiosity
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (tapped) | 5 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Faerie Mastermind; [3] Cast Preacher of the Schism; [4] Cast Deep-Cavern Bat; [5] Cast Cut Down; [6] Cast Enduring Curiosity; [7] {T}: Add {U}.; [8] {T}: Add {B}.; [9] {T}: Add {B}.; [10] {T}: Add {U}.; [11] {T}: Add {U}.
- **Chose: Cast Deep-Cavern Bat**
- Pilot's reasoning: "Proceeding with the Bat + Mastermind plan - cast Deep-Cavern Bat first to peek their hand and exile their best card, then Faerie Mastermind with remaining mana."

## Turn 9 — Precombat Main [choose]
- Life: pilot **18** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 5 lands (2 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Cut Down, Enduring Curiosity
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (tapped) | 5 lands (1 untapped)
- Menu: [0] Preacher of the Schism; [1] Preacher of the Schism; [2] Enduring Curiosity
- **Chose: target Enduring Curiosity**
- Pilot's reasoning: "Enduring Curiosity is a resilient 4/3 flash threat that draws cards on combat damage and returns from death as an enchantment - much harder to permanently answer than another Preacher of the Schism, which I can already trade with using my own Preachers or Cut Down."

## Turn 10 — Precombat Main [priority]
- Life: pilot **18** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 5 lands (2 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Cut Down, Enduring Curiosity
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4, Kaito, Bane of Nightmares 4/5 | 4 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] Cast Cut Down; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Their Preacher of the Schism spell is on the stack - nothing I can do interacts with it (Cut Down needs a permanent, not a spell), so let it resolve and decide blocks/Cut Down with full board information afterward."

## Turn 10 — Precombat Main [priority]
- Life: pilot **18** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 5 lands (2 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Cut Down, Enduring Curiosity
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4, Kaito, Bane of Nightmares 4/5, Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] Cast Cut Down; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Nothing to gain by responding to the Floodpits Drowner spell itself; better to let it resolve (its ETB will just tap my only current creature, the Bat) and then decide whether to flash in Faerie Mastermind as a fresh untapped blocker afterward."

## Turn 11 — Precombat Main [leaf_eval/plan]
- Life: pilot **10** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 5 lands (5 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Cut Down, Enduring Curiosity, Cut Down
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (tapped), Preacher of the Schism 2/4 (sick), Floodpits Drowner 2/1 (sick), Vampire Token 1/1 (sick) | 6 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `Double Cut Down + Preacher` scored **44** (Double Cut Down + Preacher | s0: they cast Cast Floodpits Drowner | I do nothing: us 10 vs 17; Double Cut Down + Preacher | s1: they cast 0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn. | I do nothing: us 10 vs 17; Double Cut Down + Preacher | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 10 vs 17)
    - `Enduring Curiosity + single Cut Down` scored **38** (Enduring Curiosity + single Cut Down | s0: they cast 0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn. | I do nothing: us 10 vs 17; Enduring Curiosity + single Cut Down | s1: they cast Cast Go for the Throat | I do nothing: us 10 vs 17; Enduring Curiosity + single Cut Down | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 10 vs 17)
    - `Single Cut Down + Preacher, hold second Cut Down` scored **24** (Single Cut Down + Preacher, hold second Cut Down | s0: they cast Cast Enduring Curiosity | on the stack I cast Cast Cut Down: us 10 vs 17; Single Cut Down + Preacher, hold second Cut Down | s0: they cast Cast Enduring Curiosity | I do nothing: us 10 vs 17; Single Cut Down + Preacher, hold second Cut Down | s1: they cast 0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn. | on the stack I cast Cast Cut Down: us 10 vs 17; Single Cut Down + Preacher, hold second Cut Down | s1: they cast 0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn. | I do nothing: us 10 vs 17; Single Cut Down + Preacher, hold second Cut Down | s2: they cast 0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn. | I do nothing: us 10 vs 17)
- Pilot's reasoning: "At 10 life facing a wide board, using both Cut Downs now to kill both Floodpits Drowners while landing a Preacher is the safest floor - it removes the most immediate attacking power regardless of what they do next. Holding the second Cut Down risks them resolving an unanswered Enduring Curiosity (le"

## Turn 11 — Precombat Main [priority]
- Life: pilot **10** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Enduring Curiosity
- MAD board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (tapped), Preacher of the Schism 2/4 (sick), Floodpits Drowner 2/1 (sick), Vampire Token 1/1 (sick) | 6 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Both Cut Downs are already on the stack targeting the Floodpits Drowners - nothing to add, just let them resolve."

## Turn 12 — Precombat Main [priority]
- Life: pilot **10** vs MAD **17**
- Pilot board: no creatures | 5 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Faerie Mastermind, Preacher of the Schism, Enduring Curiosity
- MAD board: Preacher of the Schism 2/4, Kaito, Bane of Nightmares 4/5, Preacher of the Schism 2/4, Floodpits Drowner 2/1, Vampire Token 1/1 | 5 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Faerie Mastermind; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Their Enduring Curiosity spell doesn't affect my plan (it's summoning sick, can't attack this turn regardless) and I have nothing to gain by responding to it - I'll flash in Faerie Mastermind before combat via my standing plan instead."
