# Decision review — g3.jsonl

Result: **pilot lost** in 19 turns. 58 real decisions out of 251 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Kaito, Bane of Nightmares, Cut Down, Cut Down, Preacher of the Schism, Faerie Mastermind, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: MULLIGAN**
- Pilot's reasoning: "Only 1 land (Island) in 7 cards with 6 expensive spells (Kaito at {2}{U}{B}, Preacher at {2}{B}, two Cut Downs, and two Flash creatures). No black mana sources visible. High mana screw risk; unlikely to cast Preacher, Kaito, or Cut Down early. Better odds with a 6-card hand."

## Turn 1 — null [target]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Swamp, Swamp, Anoint with Affliction, Go for the Throat, Cut Down, Spyglass Siren
- MAD board: no creatures | 0 lands (0 untapped)
- Menu: [0] Darkslick Shores; [1] Spyglass Siren; [2] Swamp; [3] Anoint with Affliction; [4] Go for the Throat; [5] Cut Down; [6] Swamp
- **Chose: target Anoint with Affliction**
- Pilot's reasoning: "Anoint with Affliction is the most conditional removal (requires MV ≤3), while Cut Down and Go for the Throat are more universally applicable. In a 6-card hand, I need the most efficient plays. Bottoming this allows me to keep 2 Swamps + Darkslick Shores for mana consistency, Spyglass Siren (1-drop "

## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Swamp, Swamp, Go for the Throat, Cut Down, Spyglass Siren
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Solid 6-card hand with 3 lands (correct ratio for 6 cards), mana is clean (2 Swamps + Darkslick Shores covers U/B), 1-drop creature that generates value (Map token), and 2 efficient removal spells. Clear turn 1 play and reasonable progression. Worth keeping."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Swamp, Swamp, Go for the Throat, Cut Down, Spyglass Siren
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 20 vs 20)
    - `Play Darkslick Shores` scored **56** (Play Darkslick Shores: us 20 vs 20)
    - `Play Swamp` scored **53** (Play Swamp: us 20 vs 20)
    - `Play Swamp` scored **53** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Candidate 0 (pass) is bad - not playing a land on turn 1 falls behind. Candidates 1-3 all play a land, gaining a mana advantage. Darkslick Shores (candidate 1) scores highest at 56 because it's a dual land providing flexibility for both U (Spyglass Siren) and B (removal). Swamp (candidates 2 & 3) sc"

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Swamp, Swamp, Go for the Throat, Cut Down, Spyglass Siren
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything): us 20 vs 20)
    - `Cast Spyglass Siren` scored **56** (Cast Spyglass Siren: us 20 vs 20)
- Pilot's reasoning: "Candidate 1 (Cast Spyglass Siren) is superior on turn 1. The opponent has no threats or lands yet, so casting the 1/1 flyer safely develops my board and generates value via Map token. I'll play Swamps on future turns to rebuild mana. Candidate 0 (pass) falls behind on the board for no benefit - hold"

## Turn 3 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Swamp, Go for the Throat, Cut Down
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **53** (pass (hold everything): us 20 vs 20)
    - `Cast Cut Down` scored **48** (Cast Cut Down: us 20 vs 20)
- Pilot's reasoning: "Candidate 0 (pass) maintains my board advantage: Spyglass Siren generates value via Map Token, and I keep 1 untapped land. The opponent has no visible threats yet, so holding up options is sound. Candidate 1 (Cast Cut Down) results in 'no creatures' on my board despite starting with Spyglass Siren, "

## Turn 3 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Swamp, Go for the Throat, Cut Down, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **59** (pass (hold everything): us 20 vs 20)
    - `Cast Cut Down` scored **38** (Cast Cut Down: us 20 vs 20)
- Pilot's reasoning: "I just drew Deep-Cavern Bat, a strong 2/1 flyer with flying, lifelink, and hand disruption ({1}{B} cost). Candidate 0 (pass) preserves my {U}{B} mana to cast Deep-Cavern Bat in my main phase, which is a better play than wasting resources on removal when the opponent has no visible creatures. Candida"

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Swamp, Go for the Throat, Cut Down, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 20 vs 20)
    - `Play Swamp` scored **60** (Play Swamp: us 20 vs 20)
    - `Play Swamp` scored **60** (Play Swamp: us 20 vs 20)
    - `Cast Cut Down` scored **38** (Cast Cut Down: us 20 vs 20)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **52** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 20)
- Pilot's reasoning: "Candidates 1-2 (Play Swamp) score highest at 60. Playing a land develops my mana base to 2 untapped lands, enabling Deep-Cavern Bat ({1}{B}) next turn while keeping flexibility this turn. Candidate 0 (pass) scores 48—no development. Candidate 4 (Map Token: sacrifice for +1/+1 pump) scores 52—pumps S"

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1 | 3 lands (3 untapped)
- Pilot hand: Swamp, Go for the Throat, Cut Down, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Cut Down` scored **35** (Cast Cut Down: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **70** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **55** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 20)
- Pilot's reasoning: "Candidate 3 (Cast Deep-Cavern Bat) scores highest at 70. Deep-Cavern Bat ({1}{B}) is excellent on turn 3: flying + lifelink + hand disruption. Two creatures (Spyglass Siren + Deep-Cavern Bat) create a strong clock while revealing opponent's hand (critical when they hold 7 cards). Candidate 4 (Map To"

## Turn 3 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1, Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Swamp, Go for the Throat, Cut Down
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **48** (unblocked: us 20 vs 20)
    - `attack-all` scored **57** (unblocked: us 20 vs 19)
- Pilot's reasoning: "Candidate 1 (attack with Spyglass Siren) scores 57. Dealing 1 damage progresses the clock on turn 3 of a mirror match. Deep-Cavern Bat can still block despite summoning sickness, so I retain defense against the opponent's turn-4 plays. Spyglass Siren untaps next turn to attack/block again. Candidate"

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 | 3 lands (3 untapped)
- Pilot hand: Swamp, Go for the Throat, Cut Down
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 20 vs 19)
    - `Cast Go for the Throat` scored **56** (Cast Go for the Throat: us 20 vs 19)
    - `Cast Cut Down` scored **62** (Cast Cut Down: us 20 vs 19)
- Pilot's reasoning: "Candidate 2 (Cast Cut Down) scores highest at 62. Floodpits Drowner (2/1) is a real threat that can attack next turn; removing it efficiently at {B} is the right play. Cut Down leaves me with {U} untapped for future interaction, unlike Go for the Throat which uses all mana. I preserve Deep-Cavern Ba"

## Turn 5 — Upkeep [target]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 | 3 lands (3 untapped)
- Pilot hand: Swamp, Go for the Throat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Menu: [0] Spyglass Siren 1/1 (A); [1] Floodpits Drowner 2/1 (B); [2] Deep-Cavern Bat 1/1 (A)
- **Chose: target Floodpits Drowner 2/1 (B)**
- Pilot's reasoning: "Target Floodpits Drowner (index 1). It's the opponent's only creature and a real threat that can attack on turn 6. Destroying it with Cut Down is the efficient play to protect my board. Targeting my own creatures (indices 0 or 2) would be counterproductive and lose value."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 | 3 lands (2 untapped)
- Pilot hand: Swamp, Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 20 vs 19)
    - `Play Swamp` scored **65** (Play Swamp: us 20 vs 19)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **40** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 19)
- Pilot's reasoning: "Candidate 1 (Play Swamp) scores highest at 65. Playing a land develops my mana base to 3 sources with 2 untapped, getting me closer to casting Kaito, Bane of Nightmares ({2}{U}{B}) on turn 6. Candidate 0 (pass) scores 50—defensive but doesn't advance my plan. Candidate 2 (Map Token) scores 40—sacrif"

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **52** (pass (hold everything): us 20 vs 19)
    - `Cast Go for the Throat` scored **38** (Cast Go for the Throat: us 20 vs 19)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **48** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 19)
- Pilot's reasoning: "Candidate 0 (pass) scores highest at 52. I have 4 mana available ({U}{B}{B}{B}) but no visible opponent threats to remove. Passing keeps both creatures (Spyglass Siren + Deep-Cavern Bat) and preserves flexibility with 2 untapped lands for next turn. Candidate 1 (Go for the Throat) scores 38—casting "

## Turn 5 — Begin Combat [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything): us 20 vs 19)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 20 vs 19)
- Pilot's reasoning: "Candidate 0 (pass) scores 55. We're in begin combat phase; the opponent has no visible creatures on the board. Passing allows me to move to declare attackers and attack with my creatures. Candidate 1 (Cast Go for the Throat) scores 30—casting removal with no valid target is wasteful, and Deep-Cavern"

## Turn 5 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **41** (unblocked: us 20 vs 19)
    - `attack-all` scored **63** (unblocked: us 21 vs 18)
- Pilot's reasoning: "The opponent has no creatures on the battlefield, making this a free attack. Deep-Cavern Bat's damage is unblockable, advancing my clock by 1 while simultaneously gaining 1 life due to Spyglass Siren's drain ability. This nets me to 21 life while reducing the opponent to 18 life. After combat, I'll "

## Turn 5 — Declare Attackers [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **73** (pass (hold everything): us 20 vs 19)
    - `Cast Go for the Throat` scored **26** (Cast Go for the Throat: us 20 vs 19)
- Pilot's reasoning: "Leaf 0 (pass): Preserves mana for Kaito (costs {2}{U}{B}) while opponent remains board-empty. Both our creatures are tapped and unable to attack/block anyway, so holding position against a non-threatening opponent is sound strategy. Leaf 1 (Cast Go for the Throat): Go for the Throat requires an oppo"

## Turn 5 — Declare Blockers [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **73** (pass (hold everything): us 20 vs 19)
    - `Cast Go for the Throat` scored **26** (Cast Go for the Throat: us 20 vs 19)
- Pilot's reasoning: "Identical evaluation to the Declare Attackers priority window. Leaf 0 (pass): No opponent creatures exist to block, and passing preserves mana {U}{B}{B}{B} for future plays like Kaito. Board position remains stable. Leaf 1 (Cast Go for the Throat): Still no legal target—opponent controls zero creatu"

## Turn 5 — Combat Damage [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **73** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **26** (Cast Go for the Throat: us 21 vs 18)
- Pilot's reasoning: "Combat Damage phase evaluation follows the same pattern as prior priority windows. Leaf 0 (pass): My life is now 21 (from Spyglass Siren's drain), opponent at 18 (from unblocked Deep-Cavern Bat attack). Passing preserves position and mana for Kaito while opponent remains board-empty with no threats."

## Turn 5 — End Combat [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **73** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **26** (Cast Go for the Throat: us 21 vs 18)
- Pilot's reasoning: "End Combat priority window with identical evaluation. Leaf 0 (pass): Positions cleanly for transition to Main Phase 2, where I can cast Kaito (costs {2}{U}{B}) with available mana {U}{B}{B}{B}. Opponent remains board-empty at 18 life with no threats. Leaf 1 (Cast Go for the Throat): No legal target—"

## Turn 5 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **16** (Cast Go for the Throat: us 21 vs 18)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **44** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 18)
- Pilot's reasoning: "Leaf 0 (pass): Preserves all resources including the Map Token's future mana production and keeps {U}{B}{B}{B} available for critical plays next turn. Opponent at 18 life with empty board poses no immediate threat. Leaf 1 (Cast Go for the Throat): No legal target exists—opponent has zero creatures. "

## Turn 5 — End Turn [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **12** (Cast Go for the Throat: us 21 vs 18)
- Pilot's reasoning: "End Turn phase evaluation. Leaf 0 (pass): Correct play—ends turn 5 cleanly, preserving resources and transitioning to opponent's turn 6. I've dealt 1 damage (now 18 life), gained 1 life (now 21), and positioned for turn 6 with Kaito in hand and {U}{B}{B}{B} mana still available. Opponent board remai"

## Turn 6 — Upkeep [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **5** (Cast Go for the Throat: us 21 vs 18)
- Pilot's reasoning: "Opponent's turn 6 Upkeep phase evaluation. Leaf 0 (pass): Correct play—Upkeep is the opponent's priority window. I have no triggered abilities to respond to, and passing allows their turn to proceed normally. My creatures remain ready, and I preserve mana for my upcoming turn. Leaf 1 (Cast Go for th"

## Turn 6 — Draw [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **5** (Cast Go for the Throat: us 21 vs 18)
- Pilot's reasoning: "Opponent's turn 6 Draw phase. Opponent has drawn their card (hand now 6). Leaf 0 (pass): Correct play—allows opponent's main phase to proceed. No priority action needed. Leaf 1 (Cast Go for the Throat): Illegal—sorceries cannot be cast during opponent's turn, only during my own main phases. Addition"

## Turn 6 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: no creatures | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **62** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **24** (Cast Go for the Throat: us 21 vs 18)
- Pilot's reasoning: "Opponent's Precombat Main phase on turn 6. OPPONENT HAS CAST DEEP-CAVERN BAT (new threat on board). Leaf 0 (pass): Opponent now has a 1/1 Deep-Cavern Bat creature and both lands are tapped (spent mana casting it). This is a threat that can attack me, but opponent's board development is limited—their"

## Turn 6 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Go for the Throat, Kaito, Bane of Nightmares
- MAD board: Deep-Cavern Bat 1/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 21 vs 18)
    - `Cast Go for the Throat` scored **78** (Cast Go for the Throat: us 21 vs 18)
- Pilot's reasoning: "Opponent's Precombat Main phase, still turn 6. Opponent has Deep-Cavern Bat (summoning sick—cannot attack this turn but can block). Leaf 0 (pass): Opponent keeps their creature; it cannot attack but can block future attacks. My board remains intact (both creatures, 2 untapped lands). Opponent's land"

## Turn 6 — Precombat Main [target]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (3 untapped)
- Pilot hand: Kaito, Bane of Nightmares
- MAD board: Deep-Cavern Bat 1/1 (sick) | 2 lands (0 untapped)
- Menu: [0] Spyglass Siren 1/1 (A); [1] Deep-Cavern Bat 1/1 (A); [2] Deep-Cavern Bat 1/1 (B)
- **Chose: target Deep-Cavern Bat 1/1 (B)**
- Pilot's reasoning: "Target opponent's Deep-Cavern Bat (index 2). Go for the Throat destroys target nonartifact creature. The opponent's Deep-Cavern Bat is the only valid target that benefits my position—it removes their emerging threat while preserving both my creatures (Spyglass Siren and Deep-Cavern Bat). Targeting m"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1, Deep-Cavern Bat 1/1 | 4 lands (4 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Island
- MAD board: no creatures | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 21 vs 18)
    - `Play Island` scored **58** (Play Island: us 21 vs 18)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **38** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 18)
- Pilot's reasoning: "My turn 7 Precombat Main. I have significant mana available ({U}{B}{B}{B}{B}{B}) and Kaito in hand. Leaf 0 (pass): Preserves all resources and keeps options open. Opponent is at 18 life with empty board—no immediate threats. Holding Kaito for maximum impact. Score reflects strong position without co"

## Turn 7 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1, Deep-Cavern Bat 1/1 | 4 lands (4 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Island
- MAD board: no creatures | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 21 vs 18)
    - `attack-all` scored **75** (unblocked: us 22 vs 16)
    - `hold[Spyglass Siren]` scored **60** (unblocked: us 22 vs 17)
    - `hold[Deep-Cavern Bat]` scored **55** (unblocked: us 21 vs 17)
- Pilot's reasoning: "Declare Attackers on turn 7. Opponent at 18 life with empty board and all lands tapped. Leaf 0 (attack-none): Keeps creatures untapped for defense, but against empty board this is overly passive. Doesn't advance clock. Score reflects missed tempo. Leaf 1 (attack-all): Deals 2 damage (opponent to 16)"

## Turn 7 — Declare Blockers [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (4 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Island
- MAD board: no creatures | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 21 vs 18)
    - `Ninjutsu {1}{U}{B} <i>({1}{U}{B} Return an unblocked attacker you control to hand: Put this card onto the battlefield from your hand tapped and attacking.)</i>` scored **72** (Ninjutsu {1}{U}{B} <i>({1}{U}{B} Return an unblocked attacker you control to hand: Put this card onto the battlefield from your hand tapped and attacking.)</i>: us 21 vs 18)
- Pilot's reasoning: "Declare Blockers phase. Opponent has empty board with no creatures to block my attacking creatures (Spyglass Siren and Deep-Cavern Bat both attacking unblocked). Leaf 0 (pass): Maintains current position—both creatures attacking, Kaito remains in hand for casting after combat ends. Lands stay untapp"

## Turn 7 — Declare Blockers [choose]
- Life: pilot **21** vs MAD **18**
- Pilot board: Spyglass Siren 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 4 lands (1 untapped)
- Pilot hand: Kaito, Bane of Nightmares, Island
- MAD board: no creatures | 3 lands (0 untapped)
- Menu: [0] Spyglass Siren 1/1 (A); [1] Deep-Cavern Bat 1/1 (A)
- **Chose: target Deep-Cavern Bat 1/1 (A)**
- Pilot's reasoning: "Return Deep-Cavern Bat to hand to enable the Ninjutsu creature to enter attacking. Both my unblocked attackers are identical 1/1s with no board presence, so the choice is symmetrical. Deep-Cavern Bat has already dealt its damage by attacking unblocked; bouncing it to hand preserves it for replay whi"

## Turn 7 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Spyglass Siren 1/1 (tapped), Kaito, Bane of Nightmares 3/4 (tapped) | 4 lands (1 untapped)
- Pilot hand: Island, Deep-Cavern Bat
- MAD board: no creatures | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything): us 21 vs 14)
    - `Play Island` scored **58** (Play Island: us 21 vs 14)
    - `+1: You get an emblem with "Ninjas you control get +1/+1."` scored **62** (+1: You get an emblem with "Ninjas you control get +1/+1.": us 21 vs 14)
    - `0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.` scored **70** (0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.: us 21 vs 14)
    - `-2: Tap target creature. Put two stun counters on it.` scored **30** (-2: Tap target creature. Put two stun counters on it.: us 21 vs 14)
- Pilot's reasoning: "Leaf 3 (0 ability: Surveil 2 + Draw 1) is strongest—pure card advantage in a control deck at a critical mid-game juncture. Leaf 2 (+1 emblem: +1/+1 to Ninjas) is next, building permanent value if Spyglass Siren is a Ninja. Leaf 1 (play Island) gives utility mana but is incremental. Leaf 0 (pass) hol"

## Turn 7 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Spyglass Siren 1/1 (tapped), Kaito, Bane of Nightmares 3/4 (tapped) | 4 lands (1 untapped)
- Pilot hand: Island, Deep-Cavern Bat, Swamp
- MAD board: no creatures | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 21 vs 14)
    - `Play Island` scored **62** (Play Island: us 21 vs 14)
    - `Play Swamp` scored **65** (Play Swamp: us 21 vs 14)
- Pilot's reasoning: "Playing a land (Leaf 1-2) is superior to passing because it breaks the all-tapped-lands bottleneck and provides untapped mana for next turn, critical for an untapped response threat. Swamp (Leaf 2) edges Island (Leaf 1) slightly: the deck is 8 Swamps / 6 Islands, so black mana is slightly more neede"

## Turn 7 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Spyglass Siren 1/1 (tapped), Kaito, Bane of Nightmares 3/4 (tapped) | 5 lands (2 untapped)
- Pilot hand: Island, Deep-Cavern Bat
- MAD board: no creatures | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 21 vs 14)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **40** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 14)
- Pilot's reasoning: "Passing (Leaf 0) preserves mana efficiency and the Map Token explore engine. Activating the token (Leaf 1) costs 1 mana + tap + sacrifice, converting your only untapped resource into a one-time +1/+1 counter on Kaito (3/4→4/5), leaving you with 0 untapped mana going into opponent's turn 8. In a cont"

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4 | 5 lands (5 untapped)
- Pilot hand: Island, Deep-Cavern Bat, Kaito, Bane of Nightmares
- MAD board: Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 21 vs 14)
    - `Play Island` scored **42** (Play Island: us 21 vs 14)
    - `Cast Deep-Cavern Bat` scored **68** (Cast Deep-Cavern Bat: us 21 vs 14)
    - `Cast Kaito, Bane of Nightmares` scored **72** (Cast Kaito, Bane of Nightmares: us 21 vs 14)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **48** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 14)
    - `+1: You get an emblem with "Ninjas you control get +1/+1."` scored **58** (+1: You get an emblem with "Ninjas you control get +1/+1.": us 21 vs 14)
    - `0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.` scored **55** (0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.: us 21 vs 14)
    - `-2: Tap target creature. Put two stun counters on it.` scored **62** (-2: Tap target creature. Put two stun counters on it.: us 21 vs 14)
- Pilot's reasoning: "Leaf 3 (second Kaito, 72): Most powerful—two Kaitos represent overwhelming threats and redundant sources of removal/value. Floodpits Drowner summoning sickness expires next turn regardless; develop threats now while opponent's board is limited. Leaf 2 (Deep-Cavern Bat, 68): Adds blocker but less agg"

## Turn 9 — Precombat Main [choose]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4, Kaito, Bane of Nightmares 3/4 (sick) | 5 lands (1 untapped)
- Pilot hand: Island, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Menu: [0] Kaito, Bane of Nightmares 3/4 (A); [1] Kaito, Bane of Nightmares 3/4 (A)
- **Chose: target Kaito, Bane of Nightmares 3/4 (A)**
- Pilot's reasoning: "Keep the first Kaito (index 0), which is not summoning sick and can attack next turn. Sacrifice the newly cast Kaito (index 1), which is summoning sick and cannot attack this turn anyway. The older Kaito has more utility: it can attack, use abilities, and represent a persistent threat. Losing the su"

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4 (sick) | 5 lands (1 untapped)
- Pilot hand: Island, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 21 vs 14)
    - `Play Island` scored **65** (Play Island: us 21 vs 14)
    - `+1: You get an emblem with "Ninjas you control get +1/+1."` scored **55** (+1: You get an emblem with "Ninjas you control get +1/+1.": us 21 vs 14)
    - `0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.` scored **48** (0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.: us 21 vs 14)
    - `-2: Tap target creature. Put two stun counters on it.` scored **65** (-2: Tap target creature. Put two stun counters on it.: us 21 vs 14)
- Pilot's reasoning: "Leaf 1 (Play Island, 65) and Leaf 4 (Kaito -2 tap, 65) are equivalent strong plays. Island ramps mana for future turns—after untap next turn, you'll have multiple untapped Swamps + Island to cast Deep-Cavern Bat and maintain Kaito's abilities. Kaito -2 (Leaf 4) taps their Floodpits Drowner and puts "

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4 (sick) | 6 lands (2 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 21 vs 14)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **52** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 14)
    - `+1: You get an emblem with "Ninjas you control get +1/+1."` scored **65** (+1: You get an emblem with "Ninjas you control get +1/+1.": us 21 vs 14)
    - `0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.` scored **58** (0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.: us 21 vs 14)
    - `-2: Tap target creature. Put two stun counters on it.` scored **70** (-2: Tap target creature. Put two stun counters on it.: us 21 vs 14)
- Pilot's reasoning: "Leaf 4 (Kaito -2 tap, 70): Strongest play—taps Floodpits Drowner with stun counters, preventing their untap and attack next turn. This is critical tempo since the Drowner is their only threat and you have limited defense. Leaf 2 (Kaito +1, 65): Solid value—emblem is permanent, Kaito becomes 4/5, and"

## Turn 9 — Precombat Main [target]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4 (sick) | 6 lands (2 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Menu: [0] Kaito, Bane of Nightmares 3/4 (A); [1] Floodpits Drowner 2/1 (B)
- **Chose: target Floodpits Drowner 2/1 (B)**
- Pilot's reasoning: "Tap the opponent's Floodpits Drowner to prevent it from attacking next turn via stun counters. This provides critical defensive tempo—the Drowner is their only remaining threat, and neutralizing it buys time for our board development while we maintain a 7-life advantage (21 vs 14)."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4 (sick) | 6 lands (2 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 21 vs 14)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **55** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 14)
- Pilot's reasoning: "Leaf 0 (pass) maintains board flexibility and preserves the Map Token for potential future value. At turn 9 with a 7-life advantage (21 vs 14), we're in a strong position. Kaito will attack as a 3/4 next turn, which is sufficient. Leaf 1 (sacrifice Map Token for explore) uses a permanent resource fo"

## Turn 9 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4 (sick) | 6 lands (2 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 21 vs 14)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **55** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 14)
- Pilot's reasoning: "Leaf 0 (pass) maintains board stability and preserves the Map Token for future flexibility. We're already ahead 21-14 life with Kaito as a functional 3/4 threat. Casting Deep-Cavern Bat is impossible this turn (costs {1}{B}, we have only {U} available). Leaf 1 (sacrifice for explore) trades a perman"

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 3/4 | 6 lands (6 untapped)
- Pilot hand: Deep-Cavern Bat, Preacher of the Schism
- MAD board: Floodpits Drowner 2/1 (tapped) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything): us 21 vs 14)
    - `Cast Deep-Cavern Bat` scored **48** (Cast Deep-Cavern Bat: us 21 vs 14)
    - `Cast Preacher of the Schism` scored **62** (Cast Preacher of the Schism: us 21 vs 14)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **76** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 21 vs 14)
    - `+1: You get an emblem with "Ninjas you control get +1/+1."` scored **51** (+1: You get an emblem with "Ninjas you control get +1/+1.": us 21 vs 14)
    - `0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.` scored **44** (0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.: us 21 vs 14)
    - `-2: Tap target creature. Put two stun counters on it.` scored **38** (-2: Tap target creature. Put two stun counters on it.: us 21 vs 14)
- Pilot's reasoning: "Leaf 3 (Map Token explore) is optimal: efficiently upgrades Kaito to 4/5 for {1} mana, matching opponent's threat while preserving 4 untapped lands and hand resources. Leaf 2 (Preacher) is secondary defensive option at 62. Passive plays score lower as they don't address opponent's Kaito untapping ne"

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 4/5 | 5 lands (3 untapped)
- Pilot hand: Deep-Cavern Bat, Preacher of the Schism
- MAD board: Floodpits Drowner 2/1 (tapped) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything): us 21 vs 14)
    - `Cast Deep-Cavern Bat` scored **48** (Cast Deep-Cavern Bat: us 21 vs 14)
    - `Cast Preacher of the Schism` scored **70** (Cast Preacher of the Schism: us 21 vs 14)
    - `+1: You get an emblem with "Ninjas you control get +1/+1."` scored **80** (+1: You get an emblem with "Ninjas you control get +1/+1.": us 21 vs 14)
    - `0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.` scored **38** (0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.: us 21 vs 14)
    - `-2: Tap target creature. Put two stun counters on it.` scored **33** (-2: Tap target creature. Put two stun counters on it.: us 21 vs 14)
- Pilot's reasoning: "Leaf 3 (+1 emblem) is optimal: costs no mana, upgrades Kaito to 5/6 (dominant threat), creates persistent emblem for future Ninjas, preserves 3 untapped lands for flexibility. Leaf 2 (Preacher) is strong secondary option at 70 (solid 2/4 blocker), but +1 preserves resources while growing threats. Le"

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 5/6 | 5 lands (3 untapped)
- Pilot hand: Deep-Cavern Bat, Preacher of the Schism
- MAD board: Floodpits Drowner 2/1 (tapped) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 21 vs 14)
    - `Cast Deep-Cavern Bat` scored **44** (Cast Deep-Cavern Bat: us 21 vs 14)
    - `Cast Preacher of the Schism` scored **82** (Cast Preacher of the Schism: us 21 vs 14)
- Pilot's reasoning: "Leaf 2 (Cast Preacher of the Schism) is optimal at 82: Creates a strong 2/4 creature that blocks opponent's threats effectively, uses all available mana efficiently, and adds significant board presence alongside Kaito 5/6. Leaf 0 (Pass) at 48 is passive—preserves mana but wastes opportunity in favor"

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **21** vs MAD **14**
- Pilot board: Kaito, Bane of Nightmares 5/6, Preacher of the Schism 2/4 (sick) | 5 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **40** (unblocked: us 21 vs 14)
    - `attack-all` scored **82** (unblocked: us 21 vs 9)
- Pilot's reasoning: "Leaf 1 (attack with Kaito) is decisively better at 82: Kaito 5/6 attacking deals 5 damage unblocked (14 → 9), putting opponent within lethal range. If opponent blocks with their Kaito (4/5), my Kaito survives the trade favorably. Forces immediate opponent response. Leaf 0 (no attack) at 40 is passiv"

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **21** vs MAD **9**
- Pilot board: Preacher of the Schism 2/4 (sick) | 6 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Kaito, Bane of Nightmares 5/6 (tapped), Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **30** (after combat: us 21 vs 9)
    - `Preacher of the Schism>Kaito, Bane of Nightmares` scored **70** (after combat: us 21 vs 9)
- Pilot's reasoning: "Leaf 0 (no-blocks): Take 9 damage to 12 life, but Kaito 5/6 remains as a major threat alongside Enduring Curiosity 4/3. Opponent likely wins next turn with repeated attacks. Leaf 1 (block): Block Preacher into Kaito. Take 4 damage to 17 life instead. Removing Kaito from the board significantly weake"

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **9**
- Pilot board: Kaito, Bane of Nightmares 5/6 | 5 lands (5 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 21 vs 9)
    - `Cast Deep-Cavern Bat` scored **75** (Cast Deep-Cavern Bat: us 21 vs 9)
    - `Cast Deep-Cavern Bat` scored **75** (Cast Deep-Cavern Bat: us 21 vs 9)
    - `+1: You get an emblem with "Ninjas you control get +1/+1."` scored **40** (+1: You get an emblem with "Ninjas you control get +1/+1.": us 21 vs 9)
    - `0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.` scored **65** (0: Surveil 2. <i>(Look at the top two cards of your library, then put any number of them into your graveyard and the rest on top in any order.)</i> Then draw a card for each opponent who lost life this turn.: us 21 vs 9)
    - `-2: Tap target creature. Put two stun counters on it.` scored **92** (-2: Tap target creature. Put two stun counters on it.: us 21 vs 9)
- Pilot's reasoning: "Leaf 0 (pass): Attack with Kaito for 5 damage (opponent at 4). Next turn: Kaito + 2 Deep-Cavern Bats = 7 damage for lethal. Simple, direct winning line. Leaf 1&2 (cast Bat): Wastes 2 mana, same winning line but less efficient. Leaf 3 (+1 emblem): Doesn't help this turn, delays our attack when we sho"

## Turn 13 — Precombat Main [target]
- Life: pilot **21** vs MAD **9**
- Pilot board: Kaito, Bane of Nightmares 5/6 | 5 lands (5 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Menu: [0] Kaito, Bane of Nightmares 5/6 (A); [1] Floodpits Drowner 2/1 (B); [2] Enduring Curiosity 4/3 (B)
- **Chose: target Enduring Curiosity 4/3 (B)**
- Pilot's reasoning: "Target Enduring Curiosity. This is opponent's only untapped creature and their main threat. Tapping it plus adding 2 stun counters prevents both blocking and attacking. Floodpits Drowner is already tapped (no value). This maximizes control and ensures my attack for 5 damage lands cleanly."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **9**
- Pilot board: Kaito, Bane of Nightmares 5/6 | 5 lands (5 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Enduring Curiosity 4/3 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **95** (pass (hold everything): us 21 vs 9)
    - `Cast Deep-Cavern Bat` scored **60** (Cast Deep-Cavern Bat: us 21 vs 9)
    - `Cast Deep-Cavern Bat` scored **60** (Cast Deep-Cavern Bat: us 21 vs 9)
- Pilot's reasoning: "Leaf 0 (pass and attack with Kaito for 5) is the clear winner. It advances our lethal clock from 9 to 4 life, guaranteeing a win next turn when we attack with Kaito (5) + 2x Deep-Cavern Bat (2) = 7 damage. Casting Deep-Cavern Bats now (Leafs 1-2) is inefficient: it taps 4 mana without progressing th"

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **21** vs MAD **9**
- Pilot board: Kaito, Bane of Nightmares 5/6 | 5 lands (5 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Enduring Curiosity 4/3 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **10** (unblocked: us 21 vs 9)
    - `attack-all` scored **95** (unblocked: us 21 vs 4)
- Pilot's reasoning: "Leaf 1 (attack-all) is dominant. Opponent is at 9 life with no way to block—both Enduring Curiosity (tapped + summoning sick) and Floodpits Drowner (tapped) cannot block. Declaring Kaito as attacker deals guaranteed 5 damage, bringing opponent to 4 life. Next turn we attack with Kaito (5) + 2x Deep-"

## Turn 13 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **4**
- Pilot board: Kaito, Bane of Nightmares 5/6 (tapped) | 5 lands (5 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (tapped), Enduring Curiosity 4/3 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **95** (pass (hold everything): us 21 vs 4)
    - `Cast Deep-Cavern Bat` scored **65** (Cast Deep-Cavern Bat: us 21 vs 4)
    - `Cast Deep-Cavern Bat` scored **65** (Cast Deep-Cavern Bat: us 21 vs 4)
- Pilot's reasoning: "Leaf 0 (pass) is clearly optimal. Opponent is at 4 life after our attack. Next turn, Kaito (5 damage) alone is lethal. Casting Deep-Cavern Bats now (Leafs 1-2) wastes 2-4 mana and adds creatures with summoning sickness that won't attack this turn or next turn—unnecessary redundancy in damage. We're "

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **4**
- Pilot board: no creatures | 5 lands (5 untapped)
- Pilot hand: Deep-Cavern Bat, Deep-Cavern Bat, Darkslick Shores
- MAD board: Floodpits Drowner 2/1, Enduring Curiosity 4/3 (tapped) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 21 vs 4)
    - `Cast Deep-Cavern Bat` scored **75** (Cast Deep-Cavern Bat: us 21 vs 4)
    - `Cast Deep-Cavern Bat` scored **75** (Cast Deep-Cavern Bat: us 21 vs 4)
    - `Play Darkslick Shores` scored **30** (Play Darkslick Shores: us 21 vs 4)
- Pilot's reasoning: "My Kaito is dead (in graveyard). Opponent at 4 life. Deep-Cavern Bats are now my only path to lethal. Leaf 1/2 (Cast Deep-Cavern Bat) adds a 1/1 creature. While it has summoning sickness this turn, next turn it attacks for 1 damage. Combined with the second Bat (cast next or later), I can deal the f"

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **4**
- Pilot board: no creatures | 5 lands (3 untapped)
- Pilot hand: Deep-Cavern Bat, Darkslick Shores
- MAD board: Floodpits Drowner 2/1, Enduring Curiosity 4/3 (tapped) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything): us 21 vs 4)
    - `Cast Deep-Cavern Bat` scored **85** (Cast Deep-Cavern Bat: us 21 vs 4)
    - `Play Darkslick Shores` scored **25** (Play Darkslick Shores: us 21 vs 4)
- Pilot's reasoning: "Leaf 1 (cast Deep-Cavern Bat) is optimal: deploys creature for postcombat casting of second bat, setting up 2-creature attack next turn (4 damage from untapped bats reduces opponent 4→0 life). Leaf 0 (pass) wastes main phase and loses momentum when opponent at lethal range, giving draw opportunity. "

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **4**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Pilot hand: Darkslick Shores
- MAD board: Floodpits Drowner 2/1, Enduring Curiosity 4/3 (tapped) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **52** (pass (hold everything): us 21 vs 4)
    - `Play Darkslick Shores` scored **48** (Play Darkslick Shores: us 21 vs 4)
- Pilot's reasoning: "Both leaves are roughly equivalent given imminent lethal (opponent at 4 life with 0 cards in hand). Leaf 0 (pass) slightly favored: keeps postcombat main available for reactive flexibility if needed, can play Darkslick Shores there. Leaf 1 (play land) acceptable but less flexible: plays the land now"

## Turn 15 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **4**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Pilot hand: Darkslick Shores
- MAD board: Floodpits Drowner 2/1, Enduring Curiosity 4/3 (tapped) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 21 vs 4)
    - `Play Darkslick Shores` scored **50** (Play Darkslick Shores: us 21 vs 4)
- Pilot's reasoning: "Postcombat Main: Both leaves are strategically equivalent. Opponent at 4 life with 0 cards in hand—no realistic comeback threats. Playing Darkslick Shores now vs. deferring to next turn (or holding) makes no material difference to lethal plan: attack with Deep-Cavern Bat next turn, gain additional c"

## Turn 16 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **21** vs MAD **4**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Pilot hand: Darkslick Shores
- MAD board: Restless Reef 4/4 (tapped), Floodpits Drowner 2/1, Enduring Curiosity 4/3 (tapped), Kaito, Bane of Nightmares 7/8 (tapped) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **15** (after combat: us 8 vs 4)
    - `Deep-Cavern Bat>Restless Reef` scored **50** (after combat: us 13 vs 4)
    - `Deep-Cavern Bat>Floodpits Drowner` scored **40** (after combat: us 11 vs 4)
    - `Deep-Cavern Bat>Kaito, Bane of Nightmares` scored **80** (after combat: us 16 vs 4)
- Pilot's reasoning: "Critical blocking decision during opponent's Turn 16 attack. Opponent at 4 life (lethal range). Leaf 3 (block Kaito) optimal: minimizes damage taken (5 damage → stay at 16 life) despite losing Deep-Cavern Bat. Opponent attacking with Restless Reef 4/4, Floodpits Drowner 2/1, and Kaito 7/8. Leaf 0 (n"

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **4**
- Pilot board: no creatures | 5 lands (5 untapped)
- Pilot hand: Darkslick Shores, Restless Reef
- MAD board: Floodpits Drowner 2/1, Enduring Curiosity 4/3 (tapped) | 7 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 16 vs 4)
    - `Play Darkslick Shores` scored **50** (Play Darkslick Shores: us 16 vs 4)
    - `Play Restless Reef` scored **50** (Play Restless Reef: us 16 vs 4)
- Pilot's reasoning: "Leaf 0 (pass) is optimal because I already have 5 untapped lands generating sufficient mana ({U}{U}{B}{B}{B} or {U}{B}{B}{B}{B}), and playing additional lands doesn't progress toward my win condition. With opponent at only 4 life, I need to draw a spell (creature or direct damage) to finish the game"

## Turn 17 — Postcombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **4**
- Pilot board: no creatures | 5 lands (5 untapped)
- Pilot hand: Darkslick Shores, Restless Reef
- MAD board: Floodpits Drowner 2/1, Enduring Curiosity 4/3 (tapped) | 7 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 16 vs 4)
    - `Play Darkslick Shores` scored **50** (Play Darkslick Shores: us 16 vs 4)
    - `Play Restless Reef` scored **50** (Play Restless Reef: us 16 vs 4)
- Pilot's reasoning: "Leaf 0 (pass) remains optimal. I already have 5 untapped lands generating {U}{U}{B}{B}{B} or {U}{B}{B}{B}{B}, which is more than sufficient for casting most spells. Playing additional lands (Leaves 1 and 2) doesn't advance my win condition—I'm at 16 life with opponent at only 4 life, meaning I need "
