# Decision review — g1.jsonl

Result: **pilot lost** in 14 turns. 19 real decisions out of 198 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Strong 7: three lands (Darkslick, Island, Swamp) covering both colors, plus a great curve of Floodpits Drowner into two Preacher of the Schism into Sheoldred. Easily keepable."

## Turn 1 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Darkslick Shores` scored **50** (play Darkslick Shores | s0: they do nothing: us 20 vs 20; play Darkslick Shores | s1: they do nothing: us 20 vs 20)
    - `play Swamp` scored **50** (play Swamp | s0: they do nothing: us 20 vs 20; play Swamp | s1: they do nothing: us 20 vs 20; play Swamp | s2: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Turn 1 land drop with no board development either way is symmetric parity; playing Darkslick Shores gives dual-color flexibility (both U and B available) which is marginally better than a basic Swamp, but the difference is negligible at this stage."

## Turn 3 — Precombat Main [leaf_eval/plan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `flash in Drowner now to stun Siren` scored **45** (flash in Drowner now to stun Siren | s0: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; flash in Drowner now to stun Siren | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; flash in Drowner now to stun Siren | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
    - `hold Drowner, just land drop` scored **45** (hold Drowner, just land drop | s0: they cast Cast Spyglass Siren | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; hold Drowner, just land drop | s0: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; hold Drowner, just land drop | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; hold Drowner, just land drop | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; hold Drowner, just land drop | s2: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; hold Drowner, just land drop | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
- Pilot's reasoning: "All leaves are near-parity, low-impact turn-2 development; casting Drowner now gives an immediate body but taps us out before we see their play, while holding it preserves flexibility to match their strongest threat, so holding scores marginally better in the best cases and about the same in the wor"

## Turn 3 — Precombat Main [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Holding Floodpits Drowner at flash for a better ambush later scored equal or better than casting it now on a 1/1 Siren; pass to keep options open and mana available for their turn."

## Turn 3 — Postcombat Main [priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Floodpits Drowner; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Postcombat main with no better use of mana this turn; still holding Floodpits Drowner for a reactive flash play on opponent's turn."

## Turn 5 — Precombat Main [leaf_eval/plan]
- Life: pilot **19** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop Preacher of the Schism` scored **45** (develop Preacher of the Schism | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; develop Preacher of the Schism | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; develop Preacher of the Schism | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
    - `hold up Drowner instead, just land` scored **40** (hold up Drowner instead, just land | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Floodpits Drowner: us 19 vs 20; hold up Drowner instead, just land | s0: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Floodpits Drowner: us 19 vs 20; hold up Drowner instead, just land | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20; hold up Drowner instead, just land | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Floodpits Drowner: us 19 vs 20; hold up Drowner instead, just land | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Developing Preacher of the Schism gives a deathtouch 2/4 that matches up well against their small creatures regardless of their follow-up, while holding back leaves my board empty against their growing 2-3 creature board even with mana up; the worst case for both is losing tempo to removal or a disc"

## Turn 7 — Precombat Main [leaf_eval/plan]
- Life: pilot **16** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `play Swamp (double black for Sheoldred)` scored **25** (play Swamp (double black for Sheoldred) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 16 vs 20; play Swamp (double black for Sheoldred) | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 20; play Swamp (double black for Sheoldred) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20)
    - `play Island (blue for Enduring Curiosity)` scored **30** (play Island (blue for Enduring Curiosity) | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 16 vs 20; play Island (blue for Enduring Curiosity) | s1: they cast Cast Cut Down | I do nothing: us 16 vs 20; play Island (blue for Enduring Curiosity) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 16 vs 20)
- Pilot's reasoning: "Both land choices leave me unable to develop this turn while they add more threats (Deep-Cavern Bat, their own Sheoldred, or Kaito) or kill my only creature with Cut Down — I'm behind on board and mana-starved either way, with their own Sheoldred being the scariest outcome."

## Turn 9 — Precombat Main [leaf_eval/plan]
- Life: pilot **13** vs MAD **19**
- Pilot board: no creatures | 4 lands (4 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `develop Preacher + Deep-Cavern Bat (info + disruption)` scored **35** (develop Preacher + Deep-Cavern Bat (info + disruption) | s0: they cast Cast Preacher of the Schism | I do nothing: us 13 vs 19; develop Preacher + Deep-Cavern Bat (info + disruption) | s1: they cast Cast Go for the Throat | I do nothing: us 13 vs 19; develop Preacher + Deep-Cavern Bat (info + disruption) | s2: they cast Cast Preacher of the Schism | I do nothing: us 13 vs 19)
    - `cast Sheoldred now` scored **60** (cast Sheoldred now | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 15; cast Sheoldred now | s1: they cast Cast Preacher of the Schism | I do nothing: us 13 vs 17)
- Pilot's reasoning: "Sheoldred is a much bigger board and life-total swing — a 4/5 deathtouch immediately dominates combat and punishes any card draw (like Faerie Mastermind's ability) far harder than two small bodies that still leave me outnumbered and vulnerable to a single Go for the Throat 2-for-1."

## Turn 11 — Precombat Main [leaf_eval/plan]
- Life: pilot **6** vs MAD **20**
- Pilot board: no creatures | 5 lands (5 untapped)
- Pilot hand: Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `Preacher + Deep-Cavern Bat (flying blocker + info)` scored **10** (Preacher + Deep-Cavern Bat (flying blocker + info) | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 6 vs 22; Preacher + Deep-Cavern Bat (flying blocker + info) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 4 vs 24)
    - `Double Preacher (two deathtouch ground blockers)` scored **12** (Double Preacher (two deathtouch ground blockers) | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 6 vs 22; Double Preacher (two deathtouch ground blockers) | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 4 vs 24)
- Pilot's reasoning: "This position is nearly lost either way — I'm at 4-6 life against a snowballing board (Sheoldred draining/gaining life every draw, plus Kaito or more card draw) — but two deathtouch Preachers give me two credible trades against their ground threats (Sheoldred, their Preacher, or Kaito) versus only o"

## Turn 11 — Precombat Main [priority]
- Life: pilot **6** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 (sick) | 6 lands (3 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Preacher of the Schism; [2] Cast Deep-Cavern Bat; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: Cast Preacher of the Schism**
- Pilot's reasoning: "First Preacher resolved; now cast the second Preacher of the Schism to get two deathtouch blockers online against their ground threats before their attack."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **6** vs MAD **23**
- Pilot board: Preacher of the Schism 2/4 (sick) | 6 lands (0 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **0** (after combat | after blocks they cast Cast Cut Down: us -2 vs 23)
    - `Preacher of the Schism>Preacher of the Schism` scored **0** (after combat | after blocks they cast Cast Go for the Throat: us -1 vs 23)
    - `Preacher of the Schism>Sheoldred, the Apocalypse` scored **30** (after combat | after blocks they cast Cast Go for the Throat: us 1 vs 23)
- Pilot's reasoning: "Blocking anything except Sheoldred leaves me dead this combat (life goes to -1 or -2); only blocking Sheoldred with my deathtouch Preacher survives (down to 1 life) and also kills Sheoldred, removing their draw-drain engine, so that's the only viable line even though I'm still in a desperate spot af"

## Turn 13 — Upkeep [priority]
- Life: pilot **1** vs MAD **23**
- Pilot board: no creatures | 6 lands (6 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 6 lands (4 untapped)
- Menu: [0] pass priority; [1] Cast Enduring Curiosity; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {U}.; [8] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "It's my upkeep before the draw step; Sheoldred is dead so drawing is safe now, and there's no reason to cast Enduring Curiosity early instead of in my main phase, so I pass."

## Turn 13 — Precombat Main [leaf_eval/plan]
- Life: pilot **1** vs MAD **23**
- Pilot board: no creatures | 6 lands (6 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 6 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `Enduring Curiosity + Deep-Cavern Bat` scored **55** (Enduring Curiosity + Deep-Cavern Bat | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 1 vs 23; Enduring Curiosity + Deep-Cavern Bat | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 1 vs 23)
    - `Double Deep-Cavern Bat (flexible flying blockers + double disruption)` scored **78** (Double Deep-Cavern Bat (flexible flying blockers + double disruption) | s0: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 1 vs 23; Double Deep-Cavern Bat (flexible flying blockers + double disruption) | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 1 vs 23; Double Deep-Cavern Bat (flexible flying blockers + double disruption) | s1: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 1 vs 23; Double Deep-Cavern Bat (flexible flying blockers + double disruption) | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 1 vs 23; Double Deep-Cavern Bat (flexible flying blockers + double disruption) | s2: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 1 vs 23; Double Deep-Cavern Bat (flexible flying blockers + double disruption) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 1 vs 23)
- Pilot's reasoning: "Drawing Go for the Throat is huge — the Double Bat line leaves 2 mana open to cast it (either now or reactively during their attack) killing their Preacher of the Schism, after which both lifelink flying Bats can wall and trade with the two remaining small fliers for zero net life loss; the Curiosit"

## Turn 13 — Precombat Main [priority]
- Life: pilot **1** vs MAD **23**
- Pilot board: no creatures | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 6 lands (4 untapped)
- Menu: [0] pass priority; [1] Cast Enduring Curiosity; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Let the first Deep-Cavern Bat resolve; I'll cast the second one next to keep Go for the Throat open at instant speed."

## Turn 13 — Precombat Main [choose]
- Life: pilot **1** vs MAD **23**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 6 lands (4 untapped)
- Menu: [0] Anoint with Affliction; [1] Enduring Curiosity; [2] Cut Down; [3] Sheoldred, the Apocalypse
- **Chose: target Sheoldred, the Apocalypse**
- Pilot's reasoning: "Sheoldred back on their board would make my own draw step lethal at my current 1 life (lose 2 automatically), an instant death sentence I can't play around — far worse than Cut Down or Anoint, which I can still survive this combat against given my Go for the Throat and lifelink blockers."

## Turn 13 — Precombat Main [priority]
- Life: pilot **1** vs MAD **23**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 6 lands (3 untapped)
- Menu: [0] pass priority; [1] Cast Enduring Curiosity; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {B}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Cut Down is targeting my Deep-Cavern Bat and I have no way to save it, so I pass and let it resolve, then continue with casting the second Deep-Cavern Bat."

## Turn 13 — Precombat Main [priority]
- Life: pilot **1** vs MAD **23**
- Pilot board: no creatures | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 6 lands (3 untapped)
- Menu: [0] pass priority; [1] Cast Enduring Curiosity; [2] Cast Deep-Cavern Bat; [3] {T}: Add {U}.; [4] {T}: Add {B}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.; [7] {T}: Add {B}.
- **Chose: Cast Deep-Cavern Bat**
- Pilot's reasoning: "With only 4 mana and unable to cast both spells (6 total needed), Deep-Cavern Bat gives a flexible flying lifelink blocker plus another look at their hand to exile a second dangerous card, better than Enduring Curiosity which can only block their ground Preacher and leaves both fliers completely una"

## Turn 13 — Precombat Main [choose]
- Life: pilot **1** vs MAD **23**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 6 lands (2 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 6 lands (3 untapped)
- Menu: [0] Anoint with Affliction; [1] Enduring Curiosity; [2] Sheoldred, the Apocalypse
- **Chose: target Sheoldred, the Apocalypse**
- Pilot's reasoning: "Exile Sheoldred again — at 1 life, if they resolve it, my own next draw step is auto-lethal, which is far worse than Anoint with Affliction (a single removal spell) or their own Enduring Curiosity."

## Turn 14 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **1** vs MAD **22**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 6 lands (2 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 7 lands (6 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **0** (after combat | after blocks they cast {3}{U}: Each player draws a card.: us -4 vs 22)
    - `Deep-Cavern Bat>Preacher of the Schism` scored **0** (after combat | after blocks they cast {3}{U}: Each player draws a card.: us -1 vs 22)
    - `Deep-Cavern Bat>Faerie Mastermind` scored **0** (after combat | after blocks they cast {3}{U}: Each player draws a card.: us -1 vs 22)
    - `Deep-Cavern Bat>Spyglass Siren` scored **0** (after combat | after blocks they cast {3}{U}: Each player draws a card.: us -2 vs 22)
- Pilot's reasoning: "Every block assignment results in negative life (-1 to -4) — I'm taking lethal damage this combat no matter what I do, since I only have one 1/1 blocker against 5 total attacking power at 1 life."
