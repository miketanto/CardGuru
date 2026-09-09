# Decision review — g6.jsonl

Result: **pilot won** in 17 turns. 77 real decisions out of 231 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Strong keepable hand: 3 lands (including Darkslick Shores fixing both colors) plus Sheoldred, two Preacher of the Schism, and Floodpits Drowner give a full curve and both colors covered."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 20 vs 20)
    - `Play Darkslick Shores` scored **75** (Play Darkslick Shores: us 20 vs 20)
    - `Play Island` scored **40** (Play Island: us 20 vs 20)
    - `Play Swamp` scored **40** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Darkslick Shores enters untapped with two or fewer other lands, so playing it turn 1 gets both-color fixing for free; Island/Swamp are fine but less flexible, and passing wastes a land drop."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **75** (Play Island: us 20 vs 20)
    - `Play Swamp` scored **80** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Missed a land drop already, so playing a land now is clearly correct; Swamp edges out Island since I have two Preachers and a Sheoldred needing black mana while I'll still play the Island next turn anyway."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Floodpits Drowner has flash, so holding it lets me wait for a better stun target (or their turn) instead of spending it now on a mere 1/1 Spyglass Siren while tapping out; no other play is available this turn anyway."

## Turn 3 — Begin Combat [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Same decision as before — no attackers to send, and holding Floodpits Drowner keeps flash flexibility for a better target or their turn rather than committing now."

## Turn 3 — Declare Attackers [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "No creatures to attack with; still correct to hold Floodpits Drowner's flash for a better window rather than commit now."

## Turn 3 — End Combat [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Still my turn 3, no board change; continue holding Floodpits Drowner's flash for better timing (their turn/end step or a bigger target)."

## Turn 3 — Postcombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Still nothing else to spend mana on this turn; better to wait through their turn and flash Floodpits Drowner in at their end step (or in response to whatever they develop) than commit now with less information."

## Turn 3 — End Turn [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "This is still my end step; better to wait and flash Floodpits Drowner during their turn (end step or in response to a threat) for max information rather than commit now."

## Turn 4 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Still early in their turn; waiting lets me see what they cast this turn before committing Floodpits Drowner's stun to the best target (their new threat rather than just the 1/1 Siren) or use it defensively before their attack if nothing better shows up."

## Turn 4 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Still their draw step, before their main phase; keep waiting to see what they develop before committing Floodpits Drowner's stun."

## Turn 4 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **75** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Opponent has tapped both their lands casting Faerie Mastermind, so they cannot interact — this is a safe window to flash in Floodpits Drowner and stun their best threat (Faerie Mastermind, the bigger body) before it can attack, with no further information to gain by waiting since they're tapped out."

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **15** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.: us 20 vs 20)
- Pilot's reasoning: "Spending {1}{U} and sacrificing my own 2/1 vigilance blocker to shuffle away a mere 1/1 Spyglass Siren is a bad trade — I'd rather keep Floodpits Drowner on the battlefield as a body and use my mana to play a land into Preacher of the Schism this turn."

## Turn 5 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **15** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.: us 20 vs 20)
- Pilot's reasoning: "Same as before — better to keep Floodpits Drowner as a body and get to my main phase to play a land and cast Preacher of the Schism, rather than trade it for a 1/1 Siren."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Island, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **80** (Play Island: us 20 vs 20)
    - `Play Island` scored **80** (Play Island: us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **15** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.: us 20 vs 20)
- Pilot's reasoning: "Playing a land is clearly correct to hit 3 mana this turn and set up Preacher of the Schism; the two Island options are identical. Activating Floodpits Drowner's ability to trade my 2/1 for their 1/1 Siren remains a bad trade."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 20 vs 20)
    - `Cast Preacher of the Schism` scored **85** (Cast Preacher of the Schism: us 20 vs 20)
    - `Cast Preacher of the Schism` scored **85** (Cast Preacher of the Schism: us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **15** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.: us 20 vs 20)
- Pilot's reasoning: "Casting Preacher of the Schism develops a strong deathtouch 2/4 body and starts the value engine; clearly better than passing or trading Floodpits Drowner for a 1/1."

## Turn 5 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 20 vs 20)
    - `attack-all` scored **80** (1 block(s), response 1: us 20 vs 20; unblocked: us 20 vs 18)
- Pilot's reasoning: "Floodpits Drowner has vigilance, so attacking costs nothing defensively — worst case they block with Faerie Mastermind and we trade 2/1s, which removes their card-advantage engine while Preacher of the Schism (deathtouch 2/4) still guards the back; best case is 2 free damage while keeping both block"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **20**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Island, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 18 vs 20)
    - `Cast Preacher of the Schism` scored **85** (Cast Preacher of the Schism: us 18 vs 20)
    - `Play Island` scored **78** (Play Island: us 18 vs 20)
    - `Play Swamp` scored **82** (Play Swamp: us 18 vs 20)
- Pilot's reasoning: "Opponent is fully tapped out (all 3 lands tapped) with no possible interaction, so this is a safe window to develop — casting Preacher of the Schism now (deathtouch 2/4) rebuilds my board after the last trade, and I can still make my land drop this same main phase for a Sheoldred follow-up next turn"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Enduring Curiosity, Island, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 18 vs 20)
    - `Play Island` scored **70** (Play Island: us 18 vs 20)
    - `Play Swamp` scored **82** (Play Swamp: us 18 vs 20)
- Pilot's reasoning: "Playing a land is correct; Swamp slightly favored to guarantee double black for Sheoldred next turn without needing Darkslick Shores to cover it."

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **18** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **70** (after combat: us 15 vs 20)
- Pilot's reasoning: "Both Spyglass Siren and Faerie Mastermind have flying, so my non-flying Preacher of the Schism cannot block either — this is the only legal outcome and losing 3 life to two 1-power/2-power fliers is manageable at 15 life."

## Turn 9 — Upkeep [leaf_eval/priority]
- Life: pilot **15** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 15 vs 20)
    - `Cast Enduring Curiosity` scored **20** (Cast Enduring Curiosity: us 15 vs 20)
- Pilot's reasoning: "Passing now lets me draw, play my land (5th land), and cast Sheoldred, the Apocalypse this main phase — a far stronger play than Enduring Curiosity given I need life stabilization at 15 against their 3-creature board. Casting Enduring Curiosity now during upkeep would tap out and forfeit the much be"

## Turn 9 — Draw [leaf_eval/priority]
- Life: pilot **15** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Enduring Curiosity, Island, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 15 vs 20)
    - `Cast Enduring Curiosity` scored **20** (Cast Enduring Curiosity: us 15 vs 20)
- Pilot's reasoning: "Still my draw step before main phase; hold to play the Island land drop and cast Sheoldred, the Apocalypse main phase with a land to spare, rather than tapping out now for the weaker Enduring Curiosity."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **15** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Enduring Curiosity, Island, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 15 vs 20)
    - `Cast Sheoldred, the Apocalypse` scored **80** (Cast Sheoldred, the Apocalypse: us 15 vs 20)
    - `Cast Enduring Curiosity` scored **30** (Cast Enduring Curiosity: us 15 vs 20)
    - `Play Island` scored **82** (Play Island: us 15 vs 20)
    - `Cast Deep-Cavern Bat` scored **25** (Cast Deep-Cavern Bat: us 15 vs 20)
- Pilot's reasoning: "Playing Island first preserves full flexibility (5 lands) before committing to Sheoldred, the Apocalypse this same main phase — the correct game-defining play given I need life stabilization and a massive blocker/threat. Enduring Curiosity and Deep-Cavern Bat are worse uses of this turn's mana than "

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **15** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 15 vs 20)
    - `Cast Sheoldred, the Apocalypse` scored **88** (Cast Sheoldred, the Apocalypse: us 15 vs 20)
    - `Cast Enduring Curiosity` scored **40** (Cast Enduring Curiosity: us 15 vs 20)
    - `Cast Deep-Cavern Bat` scored **45** (Cast Deep-Cavern Bat: us 15 vs 20)
- Pilot's reasoning: "Land is already played; now deploy Sheoldred, the Apocalypse — a 4/5 deathtouch that stabilizes life total and punishes their draws, clearly the best use of 5 mana here."

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **15** vs MAD **20**
- Pilot board: Preacher of the Schism 2/4, Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 15 vs 20)
    - `attack-all` scored **78** (1 block(s), response 1: us 15 vs 20; unblocked: us 15 vs 18)
- Pilot's reasoning: "Preacher of the Schism triggers its token-creation ability whenever it attacks a player with more life than me, which the opponent has (20 vs 15) — so attacking guarantees a 1/1 lifelink Vampire token regardless of outcome. If blocked by their Preacher, both die to deathtouch (fine even trade plus t"

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **15** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4, Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **20** (after combat: us 10 vs 15)
    - `Preacher of the Schism>Preacher of the Schism` scored **40** (after combat: us 12 vs 15)
    - `Sheoldred, the Apocalypse>Preacher of the Schism` scored **90** (after combat: us 12 vs 15)
- Pilot's reasoning: "I can't block the two fliers (Siren, Mastermind) so I'll take 3 regardless, but blocking their Preacher of the Schism with Sheoldred (4/5 deathtouch) kills it while Sheoldred easily survives 2 damage — far better than trading away my own Preacher or taking the full 5."

## Turn 11 — Upkeep [leaf_eval/priority]
- Life: pilot **12** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 15)
    - `Cast Enduring Curiosity` scored **25** (Cast Enduring Curiosity: us 12 vs 15)
- Pilot's reasoning: "Enduring Curiosity has flash, so better to wait until my main phase to also deploy Deep-Cavern Bat (sorcery-speed, gives flying blocker vs their fliers and hand disruption) rather than tap out in upkeep with no informational gain."

## Turn 11 — Draw [leaf_eval/priority]
- Life: pilot **12** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **25** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "Sheoldred's static ability now punishes my draws too — nothing to do about that here. Better to wait for main phase to play my land and cast Deep-Cavern Bat (flying blocker + hand disruption) rather than commit Enduring Curiosity now."

## Turn 11 — Draw [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **25** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "Same window; hold to main phase and play Swamp + Deep-Cavern Bat for a flying blocker and hand disruption rather than commit Enduring Curiosity now."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **40** (Cast Enduring Curiosity: us 10 vs 15)
    - `Cast Deep-Cavern Bat` scored **78** (Cast Deep-Cavern Bat: us 10 vs 15)
    - `Play Swamp` scored **75** (Play Swamp: us 10 vs 15)
- Pilot's reasoning: "Play the land first to maximize mana, then deploy Deep-Cavern Bat for a flying blocker against their fliers plus hand info/exile; hold Enduring Curiosity for flash value later rather than committing it now."

## Turn 11 — Precombat Main [choose]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Menu: [0] Anoint with Affliction; [1] Cut Down; [2] Enduring Curiosity
- **Chose: target Anoint with Affliction**
- Pilot's reasoning: "Anoint with Affliction can likely kill my Preacher of the Schism (my key deathtouch blocker/attacker, mana value 3), while Cut Down can't touch it due to its high power+toughness — removing their best answer to my Preacher matters more than protecting the smaller Deep-Cavern Bat."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 5 lands (3 untapped)
- Pilot hand: Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 10 vs 15)
    - `Play Swamp` scored **78** (Play Swamp: us 10 vs 15)
- Pilot's reasoning: "Playing the land is straightforward value with no downside, giving more mana for Enduring Curiosity flash later. Their remaining hand is just Cut Down (can't hit my Preacher) so no urgent threat."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **40** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "Enduring Curiosity can't attack this turn regardless (summoning sickness) and doesn't fly so it wouldn't block their fliers anyway — holding it with flash preserves bluff equity (4 mana up looks like a trick) and flexibility to deploy at the ideal moment on their turn."

## Turn 11 — Begin Combat [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **40** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "Still begin combat; no new information. Continue holding Enduring Curiosity as a flash blocker/bluff."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **45** (unblocked: us 10 vs 15)
    - `attack-all` scored **90** (unblocked: us 10 vs 13; 1 block(s), response 1: us 10 vs 15)
- Pilot's reasoning: "Attacking with Preacher of the Schism is fantastic here: if unblocked, I get 2 damage plus the token trigger (opponent has more life); if they block with Sheoldred, both die to the mutual deathtouch/lethal damage trade, which trades my 2/4 for their far scarier 4/5 Sheoldred. Both outcomes are stron"

## Turn 11 — Declare Attackers [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "They didn't block, so my Preacher connects for 2 unblocked plus the token trigger; still no immediate need to commit Enduring Curiosity — hold it for flash flexibility."

## Turn 11 — Declare Attackers [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "Same window; hold Enduring Curiosity for flash value rather than commit now."

## Turn 11 — Declare Blockers [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "No attack was made against my unblocked attacker on this pass (it's my turn still); hold Enduring Curiosity for flash flexibility."

## Turn 11 — Combat Damage [leaf_eval/priority]
- Life: pilot **10** vs MAD **13**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 13)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 10 vs 13)
- Pilot's reasoning: "Combat damage went through, opponent now at 13. Still hold Enduring Curiosity for flash flexibility."

## Turn 11 — End Combat [leaf_eval/priority]
- Life: pilot **10** vs MAD **13**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 13)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 10 vs 13)
- Pilot's reasoning: "End of combat; hold Enduring Curiosity for flash value on their turn."

## Turn 11 — Postcombat Main [leaf_eval/priority]
- Life: pilot **10** vs MAD **13**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 13)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 10 vs 13)
- Pilot's reasoning: "Postcombat main; still hold Enduring Curiosity for flash value on their turn rather than commit here."

## Turn 11 — End Turn [leaf_eval/priority]
- Life: pilot **10** vs MAD **13**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 13)
    - `Cast Enduring Curiosity` scored **45** (Cast Enduring Curiosity: us 10 vs 13)
- Pilot's reasoning: "My end step; still hold Enduring Curiosity for flash flexibility going into their turn."

## Turn 12 — Upkeep [leaf_eval/priority]
- Life: pilot **10** vs MAD **13**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 13)
    - `Cast Enduring Curiosity` scored **30** (Cast Enduring Curiosity: us 10 vs 13)
- Pilot's reasoning: "Sheoldred and their fliers are now untapped and threaten a big attack (~7 damage), but I already have decent blocks lined up (Vampire Token chumps Sheoldred, Deep-Cavern Bat trades favorably with Faerie Mastermind via lifelink). Enduring Curiosity would just die for nothing if it blocks the deathtou"

## Turn 12 — Draw [leaf_eval/priority]
- Life: pilot **10** vs MAD **13**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **30** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "They drew and gained 2 life via Sheoldred (now 15). Still their draw step, no reason to commit Enduring Curiosity yet — wait for attackers before deciding blocks."

## Turn 12 — Draw [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **30** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "Still their draw step; no new info. Continue holding Enduring Curiosity for combat blocking decisions."

## Turn 12 — Precombat Main [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 10 vs 15)
    - `Cast Enduring Curiosity` scored **30** (Cast Enduring Curiosity: us 10 vs 15)
- Pilot's reasoning: "Opponent is now tapped out; they may be about to attack. Continue holding Enduring Curiosity for the blocking decision."

## Turn 12 — Precombat Main [leaf_eval/priority]
- Life: pilot **10** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 8 vs 17)
    - `Cast Enduring Curiosity` scored **30** (Cast Enduring Curiosity: us 8 vs 17)
- Pilot's reasoning: "They used Faerie Mastermind's {3}{U} draw-both-players ability, punished by their own Sheoldred (I lost 2 more life, they gained 2). Nothing to respond to; still hold Enduring Curiosity for the blocking decision once they attack."

## Turn 12 — Precombat Main [leaf_eval/priority]
- Life: pilot **8** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything): us 8 vs 17)
    - `Cast Enduring Curiosity` scored **35** (Cast Enduring Curiosity: us 8 vs 17)
- Pilot's reasoning: "Same window as before; still hold Enduring Curiosity for blocking flexibility as they haven't attacked yet."

## Turn 12 — Precombat Main [leaf_eval/priority]
- Life: pilot **8** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything): us 8 vs 17)
    - `Cast Enduring Curiosity` scored **35** (Cast Enduring Curiosity: us 8 vs 17)
- Pilot's reasoning: "Enduring Curiosity lacks flying, so it can't block their fliers, and Vampire Token already handles Sheoldred as a chump — casting it now adds no blocking value against this specific attack. Better to hold it and deploy post-combat."

## Turn 12 — Begin Combat [leaf_eval/priority]
- Life: pilot **8** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Sheoldred, the Apocalypse 4/5 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything): us 8 vs 17)
    - `Cast Enduring Curiosity` scored **35** (Cast Enduring Curiosity: us 8 vs 17)
- Pilot's reasoning: "Still before attackers declared; hold Enduring Curiosity since it can't block fliers and Vampire Token already handles Sheoldred as a chump."

## Turn 12 — Declare Attackers [leaf_eval/priority]
- Life: pilot **8** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything): us 8 vs 17)
    - `Cast Enduring Curiosity` scored **25** (Cast Enduring Curiosity: us 8 vs 17)
- Pilot's reasoning: "Only Faerie Mastermind and Sheoldred are attacking (Siren held back); my existing blockers handle this well — Vampire Token chumps Sheoldred, Deep-Cavern Bat trades with and kills Faerie Mastermind while gaining 1 life via lifelink. No need to commit Enduring Curiosity now."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **8** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **5** (after combat: us 2 vs 17)
    - `Deep-Cavern Bat>Faerie Mastermind` scored **85** (after combat: us 5 vs 17)
    - `Deep-Cavern Bat>Sheoldred, the Apocalypse` scored **45** (after combat: us 7 vs 17)
    - `Vampire Token>Sheoldred, the Apocalypse` scored **40** (after combat: us 7 vs 17)
    - `Deep-Cavern Bat>Sheoldred, the Apocalypse, Vampire Token>Sheoldred, the Apocalypse` scored **35** (after combat: us 8 vs 17)
- Pilot's reasoning: "Faerie Mastermind's {3}{U} ability (draw for both players) has already been used to drain 2 life from me and gain 2 for them via their Sheoldred — leaving it alive risks repeated punishment each turn. Blocking it with Deep-Cavern Bat kills it (1 dmg to 1 toughness) and gains 1 life via lifelink, whi"

## Turn 12 — Declare Blockers [leaf_eval/priority]
- Life: pilot **8** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything): us 8 vs 17)
    - `Cast Enduring Curiosity` scored **25** (Cast Enduring Curiosity: us 8 vs 17)
- Pilot's reasoning: "Blocks are declared (Deep-Cavern Bat on Faerie Mastermind), damage hasn't resolved yet; hold Enduring Curiosity, no reason to cast it here."

## Turn 12 — Combat Damage [leaf_eval/priority]
- Life: pilot **5** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 6 lands (4 untapped)
- Pilot hand: Enduring Curiosity, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything): us 5 vs 17)
    - `Cast Enduring Curiosity` scored **85** (Cast Enduring Curiosity: us 5 vs 17)
- Pilot's reasoning: "Opponent is fully tapped out (0 untapped lands) so there's no risk in committing now, and casting Enduring Curiosity during their turn means it won't be summoning sick on my next turn — letting it attack immediately instead of waiting a turn if cast on my own turn."

## Turn 13 — Draw [leaf_eval/priority]
- Life: pilot **5** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Enduring Curiosity 4/3 | 6 lands (6 untapped)
- Pilot hand: Deep-Cavern Bat, Go for the Throat
- MAD board: Spyglass Siren 1/1, Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **10** (pass (hold everything): us 3 vs 17)
    - `Cast Go for the Throat` scored **95** (Cast Go for the Throat: us 3 vs 17)
- Pilot's reasoning: "I'm at 3 life and their Sheoldred is draining 2 life every time I draw a card — an existential threat. Go for the Throat can destroy it now (nonartifact creature), stopping the bleeding and removing their biggest threat before it attacks me for lethal."

## Turn 13 — Draw [target]
- Life: pilot **5** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Enduring Curiosity 4/3 | 6 lands (6 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1, Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (1 untapped)
- Menu: [0] Preacher of the Schism 2/4 (A); [1] Vampire Token 1/1 (A); [2] Spyglass Siren 1/1 (B); [3] Sheoldred, the Apocalypse 4/5 (B); [4] Enduring Curiosity 4/3 (A)
- **Chose: target Sheoldred, the Apocalypse 4/5 (B)**
- Pilot's reasoning: "Destroy Sheoldred, the Apocalypse to stop it from draining 2 life on my every future draw (I'm at 5 life) and remove their biggest attacking threat."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **3** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Enduring Curiosity 4/3 | 6 lands (4 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 3 vs 17)
    - `Cast Deep-Cavern Bat` scored **85** (Cast Deep-Cavern Bat: us 3 vs 17)
- Pilot's reasoning: "At 3 life, casting Deep-Cavern Bat gives me crucial information about their 5-card hand (possible removal/threats) plus another flying blocker and lifelink — much better than passing with mana unused."

## Turn 13 — Precombat Main [choose]
- Life: pilot **3** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Enduring Curiosity 4/3, Deep-Cavern Bat 1/1 (sick) | 6 lands (2 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 | 5 lands (1 untapped)
- Menu: [0] Sheoldred, the Apocalypse; [1] Go for the Throat; [2] Anoint with Affliction; [3] Cut Down; [4] Enduring Curiosity
- **Chose: target Sheoldred, the Apocalypse**
- Pilot's reasoning: "At 3 life, if they resolve Sheoldred, the Apocalypse, its 'opponent draws, lose 2 life' trigger kills me outright on my very next draw step — this is the only card in their hand that's immediately lethal regardless of board state, so it must be exiled."

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **3** vs MAD **17**
- Pilot board: Preacher of the Schism 2/4, Vampire Token 1/1, Enduring Curiosity 4/3, Deep-Cavern Bat 1/1 (sick) | 6 lands (2 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **40** (unblocked: us 3 vs 17)
    - `attack-all` scored **55** (1 block(s), response 3: us 4 vs 14; 1 block(s), response 2: us 4 vs 11; unblocked: us 4 vs 10)
    - `hold[Preacher of the Schism]` scored **52** (1 block(s), response 2: us 4 vs 16; 1 block(s), response 1: us 4 vs 13; unblocked: us 4 vs 12)
    - `hold[Vampire Token]` scored **None** (1 block(s), response 2: us 3 vs 15; unblocked: us 3 vs 11; 1 block(s), response 1: us 3 vs 13)
    - `hold[Enduring Curiosity]` scored **None** (1 block(s), response 2: us 4 vs 15; unblocked: us 4 vs 14; 1 block(s), response 1: us 4 vs 16)
- Pilot's reasoning: "Opponent is fully tapped out (0 untapped mana) with only a 1/1 Spyglass Siren as a blocker, so there's no risk of a trick. Attacking with everything is safe: Vampire Token's lifelink guarantees I end at 4 life regardless of their block choice, while dealing 3-7 damage and potentially killing their o"

## Turn 13 — Postcombat Main [leaf_eval/priority]
- Life: pilot **4** vs MAD **14**
- Pilot board: Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Pilot hand: Island, Preacher of the Schism
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 4 vs 14)
    - `Play Island` scored **78** (Play Island: us 4 vs 14)
- Pilot's reasoning: "Playing the land is free value, setting up more mana for next turn (potentially recasting Preacher of the Schism at 3 mana with land to spare)."

## Turn 13 — Postcombat Main [leaf_eval/priority]
- Life: pilot **4** vs MAD **14**
- Pilot board: Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 7 lands (3 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: no creatures | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 4 vs 14)
    - `Cast Preacher of the Schism` scored **82** (Cast Preacher of the Schism: us 4 vs 14)
- Pilot's reasoning: "Casting the second Preacher of the Schism adds another deathtouch blocker (usable immediately for blocking despite summoning sickness), important since I'm at only 4 life and want maximum defense."

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **4** vs MAD **14**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1 | 7 lands (7 untapped)
- Pilot hand: Spyglass Siren
- MAD board: no creatures | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything): us 4 vs 14)
    - `Cast Spyglass Siren` scored **75** (Cast Spyglass Siren: us 4 vs 14)
- Pilot's reasoning: "Opponent is tapped out with no creatures; casting Spyglass Siren is free value — adds a body/future blocker at minimal mana cost with mana still available for the rest of the turn."

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **4** vs MAD **14**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1 (sick) | 8 lands (7 untapped)
- Pilot hand: empty
- MAD board: no creatures | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything): us 4 vs 14)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **25** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 4 vs 14)
- Pilot's reasoning: "Opponent has no blockers and no mana; the priority is moving to combat to attack with Preacher of the Schism, Enduring Curiosity, and Vampire Token rather than spending mana on the Map Token's minor value."

## Turn 15 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **4** vs MAD **14**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1 (sick) | 8 lands (7 untapped)
- Pilot hand: empty
- MAD board: no creatures | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **15** (unblocked: us 4 vs 14)
    - `attack-all` scored **95** (unblocked: us 5 vs 7)
    - `hold[Preacher of the Schism]` scored **60** (unblocked: us 5 vs 9)
    - `hold[Enduring Curiosity]` scored **58** (unblocked: us 5 vs 11)
    - `hold[Vampire Token]` scored **45** (unblocked: us 4 vs 8)
- Pilot's reasoning: "Opponent has zero blockers and zero available mana — there's no risk at all. Attacking with everything deals 7 damage (14→7) and Vampire Token's lifelink pushes me to 5 life, the best of all options with no downside since Spyglass Siren stays back anyway (summoning sick)."

## Turn 15 — Combat Damage [leaf_eval/priority]
- Life: pilot **5** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (tapped), Vampire Token 1/1 (tapped), Spyglass Siren 1/1 (sick), Vampire Token 1/1 (sick) | 8 lands (7 untapped)
- Pilot hand: Island, Restless Reef, Floodpits Drowner
- MAD board: no creatures | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything): us 5 vs 7)
    - `Cast Floodpits Drowner` scored **75** (Cast Floodpits Drowner: us 5 vs 7)
- Pilot's reasoning: "Opponent is tapped out with no creatures, so casting Floodpits Drowner now (its ETB simply won't find a target, no downside) adds a vigilant 2/1 body to the board for free while completely safe from any response."

## Turn 15 — Postcombat Main [leaf_eval/priority]
- Life: pilot **5** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (tapped), Vampire Token 1/1 (tapped), Spyglass Siren 1/1 (sick), Vampire Token 1/1 (sick), Floodpits Drowner 2/1 (sick) | 8 lands (5 untapped)
- Pilot hand: Island, Restless Reef
- MAD board: no creatures | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **20** (pass (hold everything): us 5 vs 7)
    - `Play Island` scored **72** (Play Island: us 5 vs 7)
    - `Play Restless Reef` scored **30** (Play Restless Reef: us 5 vs 7)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **15** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 5 vs 7)
- Pilot's reasoning: "Play Island since it enters untapped (unlike Restless Reef), preserving more mana flexibility for next turn."

## Turn 15 — Postcombat Main [leaf_eval/priority]
- Life: pilot **5** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (tapped), Vampire Token 1/1 (tapped), Spyglass Siren 1/1 (sick), Vampire Token 1/1 (sick), Floodpits Drowner 2/1 (sick) | 9 lands (6 untapped)
- Pilot hand: Restless Reef
- MAD board: no creatures | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything): us 5 vs 7)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **68** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 5 vs 7)
- Pilot's reasoning: "Opponent is tapped out with no way to interact; using the Map Token to explore is free value (a land goes to hand, or a nonland gives a +1/+1 counter to one of my creatures) with no downside this turn."

## Turn 15 — Postcombat Main [target]
- Life: pilot **5** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (tapped), Vampire Token 1/1 (tapped), Spyglass Siren 1/1 (sick), Vampire Token 1/1 (sick), Floodpits Drowner 2/1 (sick) | 9 lands (6 untapped)
- Pilot hand: Restless Reef
- MAD board: no creatures | 6 lands (1 untapped)
- Menu: [0] Vampire Token 1/1 (A); [1] Preacher of the Schism 2/4 (A); [2] Spyglass Siren 1/1 (A); [3] Vampire Token 1/1 (A); [4] Enduring Curiosity 4/3 (A); [5] Floodpits Drowner 2/1 (A)
- **Chose: target Enduring Curiosity 4/3 (A)**
- Pilot's reasoning: "Opponent is tapped out (0 untapped lands) and has no creatures, so this explore is completely free — no risk of blowout. Enduring Curiosity is my key card-advantage engine (draws me a card whenever any creature deals combat damage to a player) and it recurs as an enchantment if it dies, so a permane"

## Turn 17 — Draw [leaf_eval/priority]
- Life: pilot **5** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1, Vampire Token 1/1, Floodpits Drowner 2/1 | 8 lands (8 untapped)
- Pilot hand: Restless Reef, Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 3 vs 7)
    - `Cast Anoint with Affliction` scored **15** (Cast Anoint with Affliction: us 3 vs 7)
- Pilot's reasoning: "Anoint with Affliction can only legally target a creature with mana value 3 or less (I'm not corrupted — opponent has no poison counters), and Sheoldred, the Apocalypse is mana value 4, so it can't be targeted at all. The only legal targets right now would be my own creatures, which would be a pure "

## Turn 17 — Draw [leaf_eval/priority]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1, Vampire Token 1/1, Floodpits Drowner 2/1 | 8 lands (8 untapped)
- Pilot hand: Restless Reef, Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 3 vs 7)
    - `Cast Anoint with Affliction` scored **15** (Cast Anoint with Affliction: us 3 vs 7)
- Pilot's reasoning: "Same situation as last decision — Anoint with Affliction still cannot legally target Sheoldred, the Apocalypse (mana value 4, and no corrupted condition active), so casting it now would waste it on one of my own creatures. Better to hold it for a cheap threat later and move to combat, where my 11 po"

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1, Vampire Token 1/1, Floodpits Drowner 2/1 | 8 lands (8 untapped)
- Pilot hand: Restless Reef, Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 3 vs 7)
    - `Play Restless Reef` scored **90** (Play Restless Reef: us 3 vs 7)
    - `Play Swamp` scored **65** (Play Swamp: us 3 vs 7)
    - `Cast Anoint with Affliction` scored **15** (Cast Anoint with Affliction: us 3 vs 7)
- Pilot's reasoning: "No reason to skip my land drop — it's free value. Between the two lands, playing Restless Reef now is correct sequencing: it enters tapped, but I have zero use for extra mana this turn (already 8 untapped lands, nothing to cast), so playing it now means it'll be untapped and ready next turn. Saving "

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1, Vampire Token 1/1, Floodpits Drowner 2/1 | 9 lands (8 untapped)
- Pilot hand: Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 3 vs 7)
    - `Cast Anoint with Affliction` scored **10** (Cast Anoint with Affliction: us 3 vs 7)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **8** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 3 vs 7)
- Pilot's reasoning: "Restless Reef just entered this turn, so if animated it would be summoning sick and unable to attack, and the animation only lasts until end of turn — it would wear off long before opponent's turn, so it provides no blocking value either. Spending {2}{U}{B} on it now is pure waste. Anoint with Affli"

## Turn 17 — Begin Combat [leaf_eval/priority]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1, Vampire Token 1/1, Floodpits Drowner 2/1 | 9 lands (8 untapped)
- Pilot hand: Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **88** (pass (hold everything): us 3 vs 7)
    - `Cast Anoint with Affliction` scored **10** (Cast Anoint with Affliction: us 3 vs 7)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **8** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 3 vs 7)
- Pilot's reasoning: "Same reasoning as before: Restless Reef just entered this turn so it's summoning sick and can't attack even if animated, and the animation expires at end of turn so it won't help block later either — wasted mana. Anoint with Affliction still cannot legally target Sheoldred (MV4). Best line is to pas"

## Turn 17 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4, Enduring Curiosity 4/3, Vampire Token 1/1, Spyglass Siren 1/1, Vampire Token 1/1, Floodpits Drowner 2/1 | 9 lands (8 untapped)
- Pilot hand: Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **5** (unblocked: us 3 vs 7)
    - `attack-all` scored **100** (unblocked: us 5 vs -4; 1 block(s), response 1: us 5 vs -2; 1 block(s), response 2: us 5 vs 0)
    - `hold[Preacher of the Schism]` scored **40** (1 block(s), response 1: us 5 vs 2; unblocked: us 5 vs -2; 1 block(s), response 2: us 5 vs -1)
    - `hold[Enduring Curiosity]` scored **32** (1 block(s), response 4: us 5 vs 2; 1 block(s), response 2: us 5 vs 1; 1 block(s), response 3: us 5 vs 1)
    - `hold[Vampire Token]` scored **35** (1 block(s), response 2: us 4 vs 1; unblocked: us 4 vs -3; 1 block(s), response 1: us 4 vs -1)
    - `hold[Spyglass Siren]` scored **38** (1 block(s), response 2: us 5 vs 1; unblocked: us 5 vs -3; 1 block(s), response 1: us 5 vs -1)
    - `hold[Vampire Token]` scored **35** (1 block(s), response 2: us 4 vs 1; unblocked: us 4 vs -3; 1 block(s), response 1: us 4 vs -1)
    - `hold[Floodpits Drowner]` scored **30** (1 block(s), response 2: us 5 vs 2; unblocked: us 5 vs -2; 1 block(s), response 1: us 5 vs 0)
- Pilot's reasoning: "Attacking with everyone (11 total power: Preacher 2, Enduring Curiosity 4, two Vampire tokens 1+1, Spyglass Siren 1, Floodpits Drowner 2) is lethal in EVERY possible block outcome against their lone Sheoldred blocker at 7 life: unblocked deals 11 (opp to -4), Sheoldred blocking Enduring Curiosity le"

## Turn 17 — Declare Attackers [leaf_eval/priority]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (tapped), Vampire Token 1/1 (tapped), Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (tapped), Floodpits Drowner 2/1 | 9 lands (8 untapped)
- Pilot hand: Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 3 vs 7)
    - `Cast Anoint with Affliction` scored **8** (Cast Anoint with Affliction: us 3 vs 7)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **6** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 3 vs 7)
- Pilot's reasoning: "Attackers are already locked in for lethal damage across all block scenarios. Anoint with Affliction still can't target Sheoldred (MV4), and Restless Reef remains summoning sick with its animation only lasting until end of turn, so neither play helps. Just pass and let combat resolve."

## Turn 17 — Declare Attackers [leaf_eval/priority]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (tapped), Vampire Token 1/1 (tapped), Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (tapped), Floodpits Drowner 2/1, Vampire Token 1/1 (sick) | 9 lands (8 untapped)
- Pilot hand: Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 3 vs 7)
    - `Cast Anoint with Affliction` scored **8** (Cast Anoint with Affliction: us 3 vs 7)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **6** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 3 vs 7)
- Pilot's reasoning: "Same as before — combat is already lethal across all block scenarios, no interaction is needed. Anoint with Affliction still can't target Sheoldred (MV4), and animating Restless Reef does nothing useful this turn. Just pass and let damage resolve."

## Turn 17 — Declare Blockers [leaf_eval/priority]
- Life: pilot **3** vs MAD **7**
- Pilot board: Preacher of the Schism 2/4 (tapped), Enduring Curiosity 4/3 (tapped), Vampire Token 1/1 (tapped), Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (tapped), Floodpits Drowner 2/1, Vampire Token 1/1 (sick) | 9 lands (8 untapped)
- Pilot hand: Swamp, Anoint with Affliction
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything): us 3 vs 7)
    - `Cast Anoint with Affliction` scored **8** (Cast Anoint with Affliction: us 3 vs 7)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **6** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 3 vs 7)
- Pilot's reasoning: "Blockers have been declared; nothing left to do but let combat damage resolve, which is lethal in every branch given the attack math already established. Anoint with Affliction still cannot target Sheoldred, and animating Restless Reef is pointless (summoning sick, effect expires end of turn)."
