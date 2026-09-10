# Decision review — g1.jsonl

Result: **pilot won** in 13 turns. 34 real decisions out of 175 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Three lands (Darkslick Shores, Island, Swamp) covering both colors plus Sheoldred, two Preachers, and a Drowner is a strong curve with good density and no color issues - easy keep."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything) | s0: they do nothing: us 20 vs 20; pass (hold everything) | s1: they do nothing: us 20 vs 20; pass (hold everything) | s2: they do nothing: us 20 vs 20)
    - `Play Darkslick Shores` scored **55** (Play Darkslick Shores | s0: they do nothing: us 20 vs 20; Play Darkslick Shores | s1: they do nothing: us 20 vs 20; Play Darkslick Shores | s2: they do nothing: us 20 vs 20)
    - `Play Island` scored **51** (Play Island | s0: they do nothing: us 20 vs 20; Play Island | s1: they do nothing: us 20 vs 20)
    - `Play Swamp` scored **51** (Play Swamp | s0: they do nothing: us 20 vs 20; Play Swamp | s1: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Turn 1 with no board development possible either way; playing Darkslick Shores now while it enters untapped is strictly better long-term than Island/Swamp/no land, so its leaves score marginally higher."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `Play Island` scored **48** (Play Island | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Island | s1: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s1: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Play Island | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `Play Swamp` scored **46** (Play Swamp | s0: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s0: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; Play Swamp | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Swamp | s2: they cast Cast Spyglass Siren | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s2: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Missing my land drop (pass candidates) falls behind on development for no benefit since I have no 1-2 drop to protect; playing a land and holding Floodpits Drowner up to flash in and stun whatever they commit is the strongest use of my mana this turn."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **47** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **50** (Cast Floodpits Drowner | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s1: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Holding Floodpits Drowner to flash in reactively lets me stun whatever threat they actually commit (often bigger than the summoning-sick 1/1 Siren) while keeping information and flexibility; casting it now just to tap a Siren that can't attack anyway is lower value."

## Turn 4 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **58** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "It's only their upkeep with a 1/1 Siren as the sole target; stunning it now taxes a minor threat and taps out my mana before I even see their turn's play, whereas holding keeps Drowner available for a better target or as an ambush blocker."

## Turn 4 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **58** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Same reasoning as before: still just their draw step with only the 1/1 Siren available as a target, better to hold Drowner for a real threat during their main or combat."

## Turn 4 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **62** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **46** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Faerie Mastermind is still on the stack and can't be targeted yet; passing lets it resolve so I can then flash Drowner onto the better target (Mastermind) once it's in play, rather than wasting the stun on the 1/1 Siren now."

## Turn 4 — Declare Attackers [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **66** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Casting Floodpits Drowner now to stun the untapped Faerie Mastermind denies them a blocker through my next turn and its own next untap, a much better target than the already-tapped attacking Siren I can't block anyway (it's a flier)."

## Turn 4 — Declare Attackers [target]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Menu: [0] Spyglass Siren 1/1 (B); [1] Faerie Mastermind 2/1 (B)
- **Chose: target Faerie Mastermind 2/1 (B)**
- Pilot's reasoning: "Faerie Mastermind is untapped and can block; stunning it denies them a blocker through my next turn, while the Siren is already tapped from attacking so stunning it would be redundant."

## Turn 4 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **60** (after combat: us 19 vs 20)
- Pilot's reasoning: "I take a trivial 1 damage from the unblockable flier but successfully stunned their Faerie Mastermind, denying them a blocker for my turn and putting me ahead on board with a 2/1 while they're both tapped out."

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **19** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything) | s0: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; pass (hold everything) | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **38** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Anoint with Affliction | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Activating Floodpits Drowner's bounce ability now would sacrifice my own 2/1 (and my mana) just to remove their already-neutralized, stunned 2/1 Mastermind — poor value; better to hold Drowner as a blocker/attacker and save my mana for this turn's main phase plays like Preacher of the Schism."

## Turn 5 — Draw [leaf_eval/priority]
- Life: pilot **19** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **44** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Anoint with Affliction | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Faerie Mastermind | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Same as before — bouncing my own Drowner to remove their stunned, harmless Mastermind is a net loss of tempo and board presence; better to keep the Drowner and move to my main phase to develop with Preacher of the Schism."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; pass (hold everything) | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | I do nothing: us 19 vs 20)
    - `Play Swamp` scored **44** (Play Swamp | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; Play Swamp | s1: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Play Swamp | s2: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20)
    - `Play Island` scored **56** (Play Island | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20; Play Island | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **38** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Anoint with Affliction | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Playing a land (Swamp fits my B needs for Preacher/Sheoldred) keeps developing mana for this turn's Preacher cast; not playing a land wastes tempo, and activating Drowner's bounce ability trades away my own creature for no real gain against a harmless stunned Mastermind."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 3 lands (3 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **44** (pass (hold everything) | s0: they cast Cast Spyglass Siren | I do nothing: us 19 vs 20; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 20)
    - `Cast Preacher of the Schism` scored **40** (Cast Preacher of the Schism | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 20; Cast Preacher of the Schism | s1: they cast Cast Anoint with Affliction | I do nothing: us 19 vs 20; Cast Preacher of the Schism | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
    - `Cast Preacher of the Schism` scored **40** (Cast Preacher of the Schism | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 20; Cast Preacher of the Schism | s1: they cast Cast Go for the Throat | I do nothing: us 19 vs 20; Cast Preacher of the Schism | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **35** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Floodpits Drowner | I do nothing: us 19 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Go for the Throat | I do nothing: us 19 vs 20)
- Pilot's reasoning: "Casting Preacher of the Schism now develops my board with a solid deathtouch blocker/attacker alongside Floodpits Drowner, clearly better than passing undeveloped or bouncing my own Drowner for no real gain against their harmless stunned Mastermind; the risk is Go for the Throat answering the Preach"

## Turn 5 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **19** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 19 vs 20)
    - `attack-all` scored **62** (unblocked: us 19 vs 18)
- Pilot's reasoning: "Floodpits Drowner has vigilance so attacking costs nothing defensively, and both their creatures are tapped and can't block, so this is free unblocked damage."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **32** (pass (hold everything) | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 18; pass (hold everything) | s1: they cast Cast Cut Down | I do nothing: us 18 vs 18; pass (hold everything) | s2: they cast Cast Preacher of the Schism | I do nothing: us 18 vs 18)
    - `Play Swamp` scored **30** (Play Swamp | s0: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 18 vs 18; Play Swamp | s1: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s1: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 18; Play Swamp | s2: they cast Cast Preacher of the Schism | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s2: they cast Cast Preacher of the Schism | I do nothing: us 18 vs 18)
    - `Cast Preacher of the Schism` scored **48** (Cast Preacher of the Schism | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 18 vs 18; Cast Preacher of the Schism | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 18)
    - `Play Swamp` scored **32** (Play Swamp | s0: they cast Cast Enduring Curiosity | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s0: they cast Cast Enduring Curiosity | I do nothing: us 18 vs 18; Play Swamp | s1: they cast Cast Faerie Mastermind | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s1: they cast Cast Faerie Mastermind | I do nothing: us 18 vs 18; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Enduring Curiosity: us 18 vs 18; Play Swamp | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 18)
- Pilot's reasoning: "Playing Swamp costs nothing and sets up Sheoldred next turn while keeping mana open to flash Enduring Curiosity as a surprise blocker against whatever they commit (including their own Sheoldred); missing the land drop by passing or casting Preacher without it falls behind on curve."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: no creatures | 4 lands (4 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **28** (pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 18 vs 18; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 18 vs 18; pass (hold everything) | s2: they cast Cast Floodpits Drowner | on the stack I cast Cast Enduring Curiosity: us 18 vs 18; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 18 vs 18)
    - `Cast Sheoldred, the Apocalypse` scored **80** (Cast Sheoldred, the Apocalypse | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 20 vs 14)
    - `Cast Preacher of the Schism` scored **48** (Cast Preacher of the Schism | s0: they cast Cast Preacher of the Schism | I do nothing: us 18 vs 18; Cast Preacher of the Schism | s1: they cast Cast Cut Down | I do nothing: us 18 vs 18; Cast Preacher of the Schism | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 18 vs 18)
    - `Cast Enduring Curiosity` scored **58** (Cast Enduring Curiosity | s0: they cast Cast Cut Down | I do nothing: us 18 vs 18; Cast Enduring Curiosity | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 18)
- Pilot's reasoning: "Casting Sheoldred, the Apocalypse now is a huge life-swing threat (gains me life on my draws, drains them on theirs) backed by a 4/5 deathtouch body, clearly the best of my three castable options and much better than letting them resolve their own Sheoldred uncontested while I hold up mana."

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **18** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5 (sick) | 4 lands (0 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **62** (after combat: us 15 vs 16)
- Pilot's reasoning: "No legal blocks exist since Sheoldred lacks flying/reach against their two fliers; I take 3 unblockable damage but still hold a dominant board with Sheoldred plus a full grip, well ahead on card quality and life-drain potential."

## Turn 9 — Upkeep [leaf_eval/priority]
- Life: pilot **15** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Enduring Curiosity: us 15 vs 14; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Enduring Curiosity: us 15 vs 14; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 15 vs 14; pass (hold everything) | s1: they cast Cast Go for the Throat | on the stack I cast Cast Enduring Curiosity: us 15 vs 14; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 15 vs 14; pass (hold everything) | s2: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Enduring Curiosity: us 15 vs 14; pass (hold everything) | s2: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 15 vs 14)
    - `Cast Enduring Curiosity` scored **62** (Cast Enduring Curiosity | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 12; Cast Enduring Curiosity | s2: they cast Cast Anoint with Affliction | I do nothing: us 15 vs 14)
- Pilot's reasoning: "It's still my upkeep before the draw step; casting Enduring Curiosity now taps me out prematurely with no upside over waiting for my main phase or holding it as a flash response/ambush blocker, so passing keeps maximum flexibility."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **17** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 (sick) | 4 lands (0 untapped)
- Pilot hand: Preacher of the Schism, Swamp, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 17 vs 14; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 17 vs 14; pass (hold everything) | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 17 vs 14)
    - `Play Swamp` scored **50** (Play Swamp | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 19 vs 12; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 17 vs 14; Play Swamp | s2: they cast Cast Preacher of the Schism | I do nothing: us 17 vs 14)
- Pilot's reasoning: "Playing Swamp costs nothing and develops toward more mana next turn with no downside; missing the land drop for no reason is strictly worse, and one pass branch shows Go for the Throat killing my Sheoldred which is a serious blow regardless of land choice."

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **17** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Pilot hand: Preacher of the Schism, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **65** (unblocked: us 17 vs 16)
    - `attack-all` scored **38** (1 block(s), response 1: us 17 vs 16; unblocked: us 17 vs 12)
- Pilot's reasoning: "Preacher of the Schism has deathtouch too, so blocking Sheoldred trades both creatures evenly on damage despite the stat difference — a bad trade-down for me since Sheoldred is my premier threat/engine; a rational opponent blocks here, so attacking risks losing my best card for their vanilla body wh"

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **17** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Pilot hand: Preacher of the Schism, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **50** (after combat | after blocks they cast Cast Floodpits Drowner: us 12 vs 14)
    - `Sheoldred, the Apocalypse>Preacher of the Schism` scored **35** (after combat: us 14 vs 14)
    - `Enduring Curiosity>Preacher of the Schism` scored **72** (after combat: us 14 vs 14)
- Pilot's reasoning: "Enduring Curiosity's death trigger returns it as an enchantment that keeps its card-draw ability, so blocking Preacher of the Schism with EC removes their deathtouch blocker for free while I keep Sheoldred alive and only take 3 unblocked damage from the fliers — clearly better than losing Sheoldred "

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 6 lands (6 untapped)
- Pilot hand: Preacher of the Schism, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **38** (pass (hold everything) | s0: they cast Cast Enduring Curiosity | I do nothing: us 16 vs 12; pass (hold everything) | s1: they cast Cast Floodpits Drowner | I do nothing: us 16 vs 12; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 16 vs 12)
    - `Cast Preacher of the Schism` scored **55** (Cast Preacher of the Schism | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 16 vs 12; Cast Preacher of the Schism | they respond on the stack: Cast Anoint with Affliction | s1: they cast Cast Floodpits Drowner | I do nothing: us 16 vs 12; Cast Preacher of the Schism | they respond on the stack: Cast Floodpits Drowner | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 10)
    - `Cast Deep-Cavern Bat` scored **55** (Cast Deep-Cavern Bat | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 10; Cast Deep-Cavern Bat | they respond on the stack: Cast Cut Down | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 16 vs 12; Cast Deep-Cavern Bat | they respond on the stack: Cast Floodpits Drowner | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 10)
    - `Play Swamp` scored **30** (Play Swamp | they respond on the stack: Cast Anoint with Affliction | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 16 vs 12; Play Swamp | they respond on the stack: Cast Cut Down | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 16 vs 12; Play Swamp | they respond on the stack: Cast Cut Down | s2: they cast Cast Go for the Throat | I do nothing: us 16 vs 12)
- Pilot's reasoning: "Passing without developing wastes a turn where I have plenty of mana to deploy both Preacher of the Schism and Deep-Cavern Bat; casting a creature now (or playing the land to enable both later this turn) is clearly better, and several lines show a big Sheoldred-driven life swing when Kaito's shared-"

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 6 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Vampire Token 1/1 (sick) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 12; pass (hold everything) | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 10)
    - `Cast Preacher of the Schism` scored **50** (Cast Preacher of the Schism | they respond on the stack: Cast Floodpits Drowner | s0: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 12; Cast Preacher of the Schism | they respond on the stack: Cast Cut Down | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 16 vs 12; Cast Preacher of the Schism | they respond on the stack: Cast Cut Down | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 16 vs 12)
    - `Play Swamp` scored **45** (Play Swamp | they respond on the stack: Cast Floodpits Drowner | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 16 vs 12; Play Swamp | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 16 vs 12; Play Swamp | they respond on the stack: Cast Anoint with Affliction | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 16 vs 12)
- Pilot's reasoning: "Casting Preacher of the Schism now develops my board with another deathtouch body alongside Sheoldred, matching the plan; all lines are fairly comparable since I still get to play my land afterward regardless of order."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **16** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 6 lands (1 untapped)
- Pilot hand: Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 16 vs 12; pass (hold everything) | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 10; pass (hold everything) | s2: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 16 vs 12)
    - `Play Swamp` scored **54** (Play Swamp | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 18 vs 10; Play Swamp | s1: they cast Cast Preacher of the Schism | I do nothing: us 16 vs 12; Play Swamp | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 16 vs 12)
- Pilot's reasoning: "Playing the last land in hand costs nothing and gives me future mana flexibility, so it's strictly at least as good as passing; board remains ahead with Sheoldred and Preacher of the Schism regardless of their play."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **16** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 6 lands (1 untapped)
- Pilot hand: Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **58** (unblocked: us 16 vs 14)
    - `attack-all` scored **78** (unblocked: us 16 vs 10)
- Pilot's reasoning: "Attacking with Sheoldred is free damage since both their creatures are tapped and cannot block, and Preacher of the Schism stays back as a deathtouch blocker for their turn regardless, so there's no defensive downside to attacking."

## Turn 11 — Postcombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **8**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Preacher of the Schism 2/4 (sick) | 6 lands (1 untapped)
- Pilot hand: Swamp, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything) | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 20 vs 4; pass (hold everything) | s1: they cast Cast Cut Down | I do nothing: us 18 vs 6; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 18 vs 6)
    - `Play Swamp` scored **70** (Play Swamp | s0: they cast Cast Floodpits Drowner | I do nothing: us 18 vs 6; Play Swamp | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 18 vs 6; Play Swamp | s2: they cast Cast Enduring Curiosity | I do nothing: us 18 vs 6)
- Pilot's reasoning: "I'm dominating the race at 18 life vs their 8, with Sheoldred and Preacher both alive; playing the last land costs nothing and sets up more mana for next turn regardless of their response."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **18** vs MAD **6**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped), Preacher of the Schism 2/4 (sick) | 6 lands (1 untapped)
- Pilot hand: Swamp, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **70** (after combat: us 15 vs 6)
- Pilot's reasoning: "No legal blocks exist against their fliers; taking 3 is fine since I'm at 15 vs their 6 life and next turn Sheoldred plus Preacher represent lethal pressure even though they now have their own Sheoldred to contend with."

## Turn 13 — Draw [leaf_eval/priority]
- Life: pilot **15** vs MAD **6**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Swamp, Deep-Cavern Bat, Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything) | s0: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 15 vs 6; pass (hold everything) | s0: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 15 vs 6; pass (hold everything) | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 6; pass (hold everything) | s1: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 15 vs 6; pass (hold everything) | s1: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 15 vs 6; pass (hold everything) | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 6; pass (hold everything) | s2: they cast {3}{U}: Each player draws a card. | on the stack I cast Cast Go for the Throat: us 15 vs 6; pass (hold everything) | s2: they cast {3}{U}: Each player draws a card. | after it resolves I cast Cast Go for the Throat: us 15 vs 6; pass (hold everything) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 15 vs 6)
    - `Cast Go for the Throat` scored **65** (Cast Go for the Throat | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Cast Go for the Throat | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Cast Go for the Throat | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 15 vs 4)
- Pilot's reasoning: "Casting Go for the Throat now to kill their Sheoldred clears my only real blocker before combat — their Siren and Mastermind are tapped and can't block — setting up exactly lethal (6 damage from my Sheoldred+Preacher vs their 6 life) this turn."

## Turn 13 — Draw [target]
- Life: pilot **15** vs MAD **6**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 6 lands (6 untapped)
- Pilot hand: Swamp, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Menu: [0] Spyglass Siren 1/1 (B); [1] Sheoldred, the Apocalypse 4/5 (A); [2] Sheoldred, the Apocalypse 4/5 (B); [3] Preacher of the Schism 2/4 (A); [4] Faerie Mastermind 2/1 (B)
- **Chose: target Sheoldred, the Apocalypse 4/5 (B)**
- Pilot's reasoning: "Destroying their Sheoldred removes the only untapped blocker they have, clearing the way for my Sheoldred + Preacher of the Schism to swing for exactly 6 unblocked damage - lethal against their 6 life."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **15** vs MAD **6**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 6 lands (4 untapped)
- Pilot hand: Swamp, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **58** (pass (hold everything) | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; pass (hold everything) | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2)
    - `Play Swamp` scored **55** (Play Swamp | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Play Swamp | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Play Swamp | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 15 vs 4)
    - `Cast Deep-Cavern Bat` scored **74** (Cast Deep-Cavern Bat | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Cast Deep-Cavern Bat | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Cast Deep-Cavern Bat | s2: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2)
- Pilot's reasoning: "Casting Deep-Cavern Bat now lets me look at their hand and exile a nonland card (like a removal spell) before combat, protecting my lethal swing with Sheoldred+Preacher of the Schism against their tapped-out board; playing land or passing leaves that risk unaddressed."

## Turn 13 — Precombat Main [choose]
- Life: pilot **15** vs MAD **6**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 6 lands (2 untapped)
- Pilot hand: Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Menu: [0] Sheoldred, the Apocalypse; [1] Enduring Curiosity
- **Chose: target Sheoldred, the Apocalypse**
- Pilot's reasoning: "Neither card is castable this turn since they're fully tapped out, so my lethal swing isn't at risk either way; exiling their Sheoldred permanently denies them their best comeback threat in case anything goes wrong with the attack."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **15** vs MAD **6**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 6 lands (2 untapped)
- Pilot hand: Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything) | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 15 vs 4; pass (hold everything) | s1: they cast Cast Enduring Curiosity | I do nothing: us 15 vs 4; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 15 vs 4)
    - `Play Swamp` scored **72** (Play Swamp | s0: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Play Swamp | s1: they cast {3}{U}: Each player draws a card. | I do nothing: us 17 vs 2; Play Swamp | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 15 vs 4)
- Pilot's reasoning: "Playing Swamp costs nothing and keeps mana open; regardless of their response (animating Restless Reef, casting a blocker, or triggering shared draws), I'm well ahead with Sheoldred and Preacher of the Schism ready to swing for lethal against their sub-5 life total next combat."

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **15** vs MAD **6**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 7 lands (3 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **45** (unblocked: us 15 vs 6)
    - `attack-all` scored **100** (unblocked: us 16 vs 0)
    - `hold[Sheoldred, the Apocalypse]` scored **60** (unblocked: us 16 vs 2)
    - `hold[Preacher of the Schism]` scored **55** (unblocked: us 15 vs 2)
- Pilot's reasoning: "Attacking with both Sheoldred and Preacher of the Schism is unblockable (their only creatures are tapped) and results in exactly lethal damage - game over."
