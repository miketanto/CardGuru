# Decision review — g4.jsonl

Result: **pilot lost** in 16 turns. 27 real decisions out of 199 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Undercity Sewers, Kaito, Bane of Nightmares, Cut Down, Sheoldred, the Apocalypse, Deep-Cavern Bat, Faerie Mastermind, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: MULLIGAN**
- Pilot's reasoning: "Only one land in seven cards means mana screw. Sheoldred, Kaito, and most spells are uncastable until turns 3+. Need 2-3 lands to curve out."

## Turn 1 — null [target]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Menu: [0] Island; [1] Restless Reef; [2] Swamp; [3] Go for the Throat; [4] Island; [5] Floodpits Drowner; [6] Deep-Cavern Bat
- **Chose: target Island**
- Pilot's reasoning: "Island is redundant—I have another Island and Restless Reef for blue mana. Keep Go for the Throat (removal), both creatures (cheap evasion + disruption), and the dual land."

## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Solid 6-card hand with proper mana fixing (Island, Swamp, Restless Reef), two cheap creatures with relevant abilities (bat discard, drowner tempo), and Go for the Throat for interaction. Mulligan to 5 would be worse."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **18** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **70** (Play Island: us 20 vs 20)
    - `Play Restless Reef` scored **43** (Play Restless Reef: us 20 vs 20)
    - `Play Swamp` scored **70** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Pass (18) misses a land drop, disaster in a mirror. Island (70) and Swamp (70) are equivalent—both set up cheap creatures next turn; slight preference for Swamp enables Deep-Cavern Bat's hand disruption early. Restless Reef (43) enters tapped, wastes Turn 1 mana efficiency. Play any basic land."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 20 vs 20)
    - `Play Restless Reef` scored **65** (Play Restless Reef: us 20 vs 20)
    - `Play Swamp` scored **80** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Swamp gives immediate {U}{B} on turn 3 to cast creatures, gaining tempo. Restless Reef enters tapped, delaying mana access until turn 4 despite having creature upside. Pass wastes development—opponent is already at parity but deploying faster. Play Swamp now."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Restless Reef, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **70** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **78** (Cast Floodpits Drowner: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **70** (Cast Deep-Cavern Bat: us 20 vs 20)
- Pilot's reasoning: "Passing wastes tempo when ahead on board development. Deep-Cavern Bat (leaves 1-3) gets hand information and disruption but 1/1 body is weak. Floodpits Drowner (leaf 2) is superior: 2/1 with vigilance and flash pressure, plus the tap effect handles future threats better. Drowner is the efficient tem"

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Restless Reef, Go for the Throat, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **85** (Cast Go for the Throat: us 20 vs 20)
- Pilot's reasoning: "Opponent's Floodpits Drowner is summoning sick but will untap next turn and attack for 2. Go for the Throat removes their only threat immediately, leaving them with zero board presence while my Drowner untaps. Trading one spell for board control and tempo is correct. Passing lets them establish pres"

## Turn 5 — Upkeep [target]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Restless Reef, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Menu: [0] Floodpits Drowner 2/1 (B); [1] Floodpits Drowner 2/1 (A)
- **Chose: target Floodpits Drowner 2/1 (B)**
- Pilot's reasoning: "Target opponent's Floodpits Drowner (index 0). Destroying their only creature removes their threat and gives me board control with my Drowner."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (tapped) | 2 lands (0 untapped)
- Pilot hand: Restless Reef, Deep-Cavern Bat, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 20 vs 20)
    - `Play Restless Reef` scored **75** (Play Restless Reef: us 20 vs 20)
- Pilot's reasoning: "Playing Restless Reef develops my mana base. Though it enters tapped, by Turn 6 all three lands untap, giving me {U}{B}{U/B} for creature threats and activated abilities. Passing wastes the land drop—I should maximize mana production early to establish board presence when opponent stabilizes. Play t"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (tapped) | 3 lands (3 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat, Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything): us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **68** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **68** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **68** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Play Swamp` scored **32** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Casting Deep-Cavern Bat (leaves 1-3) is clearly superior. The bat is evasive (flying), gains life, exiles a card from opponent's hand, and applies pressure while they can't attack with their summoning-sick Drowner. Passing (leaf 0) is passive in a race—I'd let them develop answers while I hold creat"

## Turn 7 — Precombat Main [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Menu: [0] Kaito, Bane of Nightmares; [1] Deep-Cavern Bat; [2] Go for the Throat; [3] Kaito, Bane of Nightmares
- **Chose: target Kaito, Bane of Nightmares**
- Pilot's reasoning: "Kaito, Bane of Nightmares is the highest-impact card in their hand. The {2}{U}{B} planeswalker generates significant value if cast, so exiling it denies them their strongest threat, even if only temporarily while the bat is in play. Go for the Throat is tempting as removal denial, but Kaito is the s"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **56** (pass (hold everything): us 20 vs 20)
    - `Play Swamp` scored **45** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Passing (leaf 0) is better. I have 2 bats in hand and should be deploying threats, not playing lands. Leaf 0 keeps my land drop available for future turns while maintaining board presence. Leaf 1 (playing Swamp) wastes my main phase on mana when I should be applying pressure with creatures. I alread"

## Turn 7 — Postcombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **56** (pass (hold everything): us 20 vs 20)
    - `Play Swamp` scored **45** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Same analysis as decision 33: passing (leaf 0) is superior. I can't cast more creatures with the available mana {U} or {B}, so playing Swamp (leaf 1) just uses my land drop on ramp without advancing my board. Passing keeps the land drop option for later while maintaining current board presence. Temp"

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat, Swamp
- MAD board: Floodpits Drowner 2/1, Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **30** (after combat: us 18 vs 20)
    - `Deep-Cavern Bat>Floodpits Drowner` scored **80** (after combat: us 21 vs 20)
- Pilot's reasoning: "Blocking with Deep-Cavern Bat is significantly better. While we lose our creature and its hand disruption, we: (1) eliminate Floodpits Drowner, a 2/1 threat with vigilance that would attack repeatedly untapped, (2) gain 1 life from lifelink (21 vs 18), improving our life total, and (3) still have an"

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **20**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Deep-Cavern Bat, Swamp, Preacher of the Schism
- MAD board: Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 21 vs 20)
    - `Cast Deep-Cavern Bat` scored **70** (Cast Deep-Cavern Bat: us 21 vs 20)
    - `Play Swamp` scored **45** (Play Swamp: us 21 vs 20)
    - `Cast Preacher of the Schism` scored **78** (Cast Preacher of the Schism: us 21 vs 20)
- Pilot's reasoning: "Preacher of the Schism (option 3) is strongest: a 2/4 with deathtouch creates a strong clock and draws cards when we're at life parity. While tapping out is risky, in a mirror match we need to deploy threats efficiently to pressure the opponent before they stabilize. Deep-Cavern Bat (option 1, score"

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Pilot hand: Deep-Cavern Bat, Swamp
- MAD board: Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 21 vs 20)
    - `Play Swamp` scored **90** (Play Swamp: us 21 vs 20)
- Pilot's reasoning: "Playing the Swamp is clearly correct. I have one land play per turn and no downside to using it—the Swamp expands my mana base from 3 to 4 lands, giving me an untapped land for future turns. All my current lands are tapped after casting Preacher, so I have no mana to spend this turn anyway. Playing "

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **21** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Deep-Cavern Bat 1/1 (tapped), Kaito, Bane of Nightmares 4/5 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **32** (after combat: us 20 vs 21)
- Pilot's reasoning: "Taking 1 damage unblocked (21→20 life) while opponent gains 1 life (20→21) represents a -2 life swing and leaves their Deep-Cavern Bat alive to pressure me next turn. Blocking with Preacher of the Schism would be superior: Preacher (2/4) kills Bat (1/1) while taking 1 damage and surviving. However, "

## Turn 11 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **21**
- Pilot board: Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Deep-Cavern Bat 1/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything): us 20 vs 21)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **68** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 20 vs 21)
- Pilot's reasoning: "Passing (Option 1) leaves me with only Preacher of the Schism (2/4) against opponent's Deep-Cavern Bat and Kaito, maintaining board disadvantage while I have mana available—a missed opportunity to develop threats. Activating Restless Reef's ability (Option 2) immediately generates a 4/4 deathtouch c"

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **21**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 | 3 lands (0 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down
- MAD board: Deep-Cavern Bat 1/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **60** (unblocked: us 20 vs 0)
    - `attack-all` scored **90** (unblocked: us 20 vs 0)
- Pilot's reasoning: "Both options show opponent at 0 life, suggesting both lead to victory, but they differ in execution. Attack-none (Option 0) is passive and keeps creatures untapped for defense, but fails to develop immediate threats or leverage the kill potential. Attack-all (Option 1) is strongly favored because: ("

## Turn 13 — Upkeep [leaf_eval/priority]
- Life: pilot **14** vs MAD **22**
- Pilot board: Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (sick) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything): us 14 vs 22)
    - `Cast Cut Down` scored **50** (Cast Cut Down: us 14 vs 22)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **72** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 22)
- Pilot's reasoning: "At 14 life facing flying threats (Deep-Cavern Bat 1/1, Enduring Curiosity 4/3), I must address the board rather than remain passive. Option 1 (Pass) at 35: Keeps mana untapped but does nothing to address Enduring Curiosity and Deep-Cavern Bat—passive play when I'm low on life is dangerous. Option 2 "

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **14** vs MAD **22**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 | 3 lands (0 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down, Darkslick Shores
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (sick) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **47** (pass (hold everything): us 14 vs 22)
    - `Play Darkslick Shores` scored **53** (Play Darkslick Shores: us 14 vs 22)
- Pilot's reasoning: "At 14 life, both options maintain the same defensive posture with Restless Reef 4/4 ready to block or attack. Option 1 (Pass) at 47: Fails to play an available land drop; in Magic, playing lands that don't create immediate disadvantage is nearly always correct, and passing leaves resources unused. O"

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **14** vs MAD **22**
- Pilot board: Restless Reef 4/4 (tapped), Preacher of the Schism 2/4 | 4 lands (0 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (sick) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **55** (unblocked: us 14 vs 0)
    - `attack-all` scored **92** (unblocked: us 14 vs 0)
- Pilot's reasoning: "Both options lead to opponent at 0 life (game-ending state), but they differ significantly in method. Attack-none (Option 0) at 55: Passive approach that keeps Preacher untapped for defense but fails to develop immediate threats or leverage Restless Reef's milling ability. At 14 life, a passive stra"

## Turn 15 — Upkeep [leaf_eval/priority]
- Life: pilot **3** vs MAD **23**
- Pilot board: no creatures | 5 lands (5 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Preacher of the Schism 2/4 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **8** (pass (hold everything): us 3 vs 23)
    - `Cast Cut Down` scored **15** (Cast Cut Down: us 3 vs 23)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **35** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 3 vs 23)
- Pilot's reasoning: "At 3 life facing opponent's Deep-Cavern Bat (1/1 T), Enduring Curiosity (4/3 T), Kaito (tapped), and Preacher of the Schism (2/4 untapped, summoning sick), every option is dire—I'm in a race against a superior board position. Option 1 (Pass) at 8: Passive approach guarantees I face untapped flying t"

## Turn 15 — Upkeep [leaf_eval/priority]
- Life: pilot **3** vs MAD **23**
- Pilot board: no creatures | 5 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Preacher of the Schism 2/4 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 3 vs 23)
    - `Cast Cut Down` scored **25** (Cast Cut Down: us 3 vs 23)
- Pilot's reasoning: "At 3 life, the untapped Restless Reef 4/4 is my only defense against opponent's flying threats. Option 1 (Pass) at 40: Maintains the untapped 4/4 blocker essential for survival—opponent's Enduring Curiosity (4/3) will attack next turn and the 4/4 can block it and survive (taking 3 damage but not dyi"

## Turn 15 — Upkeep [leaf_eval/priority]
- Life: pilot **3** vs MAD **23**
- Pilot board: Restless Reef 4/4 | 4 lands (0 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Preacher of the Schism 2/4 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything): us 3 vs 23)
    - `Cast Cut Down` scored **24** (Cast Cut Down: us 3 vs 23)
- Pilot's reasoning: "At 3 life with Restless Reef already as an untapped 4/4 creature, the decision mirrors the critical need for defense. Option 1 (Pass) at 42: Maintains untapped 4/4 blocker—when opponent attacks with Enduring Curiosity (4/3 tapped, will untap next turn), the 4/4 can block it and survive (takes 3 dama"

## Turn 15 — Draw [leaf_eval/priority]
- Life: pilot **3** vs MAD **23**
- Pilot board: Restless Reef 4/4 | 4 lands (0 untapped)
- Pilot hand: Deep-Cavern Bat, Cut Down, Undercity Sewers
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Preacher of the Schism 2/4 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 3 vs 23)
    - `Cast Cut Down` scored **85** (Cast Cut Down: us 3 vs 23)
- Pilot's reasoning: "Option 2 (pass to combat) is stronger: Restless Reef has vigilance, so attacking doesn't tap it—I deal 4 damage to opponent (19 life) while maintaining my untapped blocker for Enduring Curiosity. This is critical at 3 life; I need to apply pressure while keeping defense intact. Option 1 (play Underc"

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **3** vs MAD **23**
- Pilot board: Restless Reef 4/4 (tapped) | 4 lands (0 untapped)
- Pilot hand: Deep-Cavern Bat, Undercity Sewers, Deep-Cavern Bat
- MAD board: Enduring Curiosity 4/3 (tapped), Preacher of the Schism 2/4 (sick) | 7 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything): us 3 vs 23)
    - `Play Undercity Sewers` scored **50** (Play Undercity Sewers: us 3 vs 23)
- Pilot's reasoning: "Option 1 (Play Undercity Sewers) edges out Option 0 despite both paths leading to critical pressure. At 3 life with Restless Reef tapped (cannot block Enduring Curiosity's 4/3 flying next turn), the position is likely lost. However, playing the land: (1) develops mana base for future turns despite e"
