# Decision review — g1.jsonl

Result: **pilot lost** in 26 turns. 72 real decisions out of 312 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "3 lands with UB fixing (Darkslick, Island, Swamp), clean curve: T2 Drowner, T3 Preacher, T4 Preacher/Sheoldred. Two Preachers and Sheoldred is a very strong keep."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they do nothing: us 20 vs 20; pass (hold everything) | s1: they do nothing: us 20 vs 20; pass (hold everything) | s2: they do nothing: us 20 vs 20)
    - `Play Darkslick Shores` scored **65** (Play Darkslick Shores | s0: they do nothing: us 20 vs 20; Play Darkslick Shores | s1: they do nothing: us 20 vs 20; Play Darkslick Shores | s2: they do nothing: us 20 vs 20)
    - `Play Island` scored **60** (Play Island | s0: they do nothing: us 20 vs 20; Play Island | s1: they do nothing: us 20 vs 20; Play Island | s2: they do nothing: us 20 vs 20)
    - `Play Swamp` scored **58** (Play Swamp | s0: they do nothing: us 20 vs 20; Play Swamp | s1: they do nothing: us 20 vs 20; Play Swamp | s2: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Turn 1 must play a land; passing wastes tempo. Darkslick Shores enters untapped (we control 0 other lands, ≤2), and its dual-color ability preserves maximum flexibility — Island commits to U, Swamp commits to B. All three land plays are close; Darkslick is slightly best because it can produce either"

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `Play Island` scored **32** (Play Island | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Island | s1: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s1: they cast Cast Floodpits Drowner | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s1: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Play Island | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; Play Island | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `Play Swamp` scored **30** (Play Swamp | s0: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s0: they cast Cast Faerie Mastermind | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s0: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; Play Swamp | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Play Swamp | s2: they cast Cast Spyglass Siren | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s2: they cast Cast Spyglass Siren | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; Play Swamp | s2: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Must play a land — passing wastes T3. Island slightly beats Swamp: it enables a Drowner cast this turn while keeping Darkslick's B available for a future Preacher/Sheoldred line, and gives 2 U sources for Enduring Curiosity later. Swamp commits to B and doesn't help cast Drowner any better. Worst le"

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast Cast Floodpits Drowner | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s1: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Drowner is flash — holding it for their EOT is generally better. It lets me pick a target after seeing their T3 play, and pass leaves show I can still cast Drowner in response. Casting in main phase commits to stunning Siren (which is small and summoning-sick anyway) and exposes Drowner to Cut Down/"

## Turn 3 — Begin Combat [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **32** (pass (hold everything) | s0: they cast Cast Spyglass Siren | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast Cast Spyglass Siren | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Spyglass Siren | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Spyglass Siren | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Spyglass Siren | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Spyglass Siren | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Spyglass Siren | I do nothing: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **28** (Cast Floodpits Drowner | s0: they cast Cast Cut Down | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Pass: Drowner is flash, holding it lets me react to whatever they cast (and see if they tap out). Cast now: exposed to Cut Down/Go for the Throat during their T3 with mana up — sim confirms 2/3 leaves have my Drowner dying to their removal. Passing keeps Drowner as a live threat/response, and I have"

## Turn 3 — Declare Attackers [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **32** (pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Go for the Throat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Go for the Throat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Go for the Throat | I do nothing: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **40** (Cast Floodpits Drowner | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s1: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
- Pilot's reasoning: "No creatures to attack with. Hold Drowner — casting now still exposes it to their instant-speed removal (Cut Down/GftT sim shows). Pass and cast on their EOT when they've committed their turn. Leaf 6/7 (they blow Go for the Throat with no target) is best-case pass; leaves where they cast their own D"

## Turn 3 — End Combat [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything) | s0: they cast Cast Go for the Throat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast Cast Go for the Throat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Faerie Mastermind | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Faerie Mastermind | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Floodpits Drowner | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Floodpits Drowner | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **50** (Cast Floodpits Drowner | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
- Pilot's reasoning: "End of my combat, still no creatures — Siren is summoning-sick so no attacks coming this turn anyway. Holding Drowner for their EOT lets me see their T3 spell first: if they blow Go for the Throat (no target), great; if they cast Mastermind/Bat/Drowner, I can stun the best of them or wait. Casting n"

## Turn 3 — Postcombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Go for the Throat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Go for the Throat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **40** (Cast Floodpits Drowner | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s1: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Postcombat main, still no plays to make (Drowner is my only castable and best cast on their EOT). Passing lets me react at instant speed to their turn. Best pass leaves are when they blow removal on nothing (leaf 3/4)."

## Turn 3 — End Turn [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (sick) | 2 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Floodpits Drowner: us 20 vs 20; pass (hold everything) | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **25** (Cast Floodpits Drowner | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s1: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20; Cast Floodpits Drowner | s2: they cast Cast Go for the Throat | I do nothing: us 20 vs 20)
- Pilot's reasoning: "End of my turn — passing lets me flash Drowner on their EOT (or in response to a big spell mid-turn) rather than committing now. Cast-now leaf 11 shows Go for the Throat killing my Drowner outright for card advantage; leaf 9 has awkward tapped state. Pass keeps Drowner as reactive threat with full m"

## Turn 4 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **55** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Their upkeep — they haven't drawn or cast yet, and they're already mana-screwed with only 1 land. Wait to see their T4 play before committing Drowner's ETB target. If they draw+cast a bigger threat (Bat/Mastermind), I can stun that. If they can't cast anything, I still stun Siren at their EOT. Waiti"

## Turn 4 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **55** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "They just drew, still no main phase yet. Same reasoning — wait for their main-phase play to see what to stun. If they cast a Bat/Mastermind/second creature, that's a better target than Siren."

## Turn 4 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Floodpits Drowner, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything): us 20 vs 20)
    - `Cast Floodpits Drowner` scored **68** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Opp has both lands tapped (0 mana available) — can't respond to Drowner with removal/counter. Cast Drowner NOW to safely stun Siren and prevent their combat damage. Both leaves show opp with Mastermind eventually, but Cast Drowner leaf adds a 2/1 vigilance body on my side."

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Anoint with Affliction | I do nothing: us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **25** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Activating Drowner's shuffle ability trades my 2/1 blocker/attacker for a Siren that's already stunned (low value). Better to keep Drowner alive: use it as a Mastermind blocker or attack into a trade. Siren tapped means it can't attack; the real threat is Mastermind. Save Drowner activation for a ge"

## Turn 5 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything) | s0: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Go for the Throat | I do nothing: us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **30** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Cut Down | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Go for the Throat | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Activating Drowner's shuffle ability removes their already-tapped/stunned Siren — a very low value target. It costs my Drowner AND 2 mana. Passing keeps Drowner alive for combat (attack into Mastermind for a trade — kills their best creature) or as a blocker. Opp will likely GftT Drowner eventually,"

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 2 lands (2 untapped)
- Pilot hand: Swamp, Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Anoint with Affliction | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `Play Swamp` scored **60** (Play Swamp | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Play Swamp | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; Play Swamp | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
    - `Play Island` scored **55** (Play Island | s0: they cast Cast Anoint with Affliction | I do nothing: us 20 vs 20; Play Island | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; Play Island | s2: they cast Cast Anoint with Affliction | I do nothing: us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **25** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Play Swamp: enables Preacher T5 (Darkslick B + Island + Swamp) AND crucially sets up Sheoldred T6 (Darkslick + Swamp = 2 B sources for BB). Play Island: also enables Preacher but leaves only 1 B source (Darkslick) — can't cast Sheoldred. Passing wastes development. Activating Drowner loses value."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1 | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20)
    - `Cast Preacher of the Schism` scored **62** (Cast Preacher of the Schism | s0: they cast Cast Anoint with Affliction | I do nothing: us 20 vs 20; Cast Preacher of the Schism | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; Cast Preacher of the Schism | s2: they cast Cast Anoint with Affliction | I do nothing: us 20 vs 20)
    - `Cast Preacher of the Schism` scored **45** (Cast Preacher of the Schism | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Cast Preacher of the Schism | s1: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; Cast Preacher of the Schism | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20)
    - `{1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries.` scored **25** ({1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s0: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; {1}{U}, {T}: Shuffle {this} and target creature with a stun counter on it into their owners' libraries. | s2: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Cast Preacher of the Schism now — 2/4 deathtouch is a huge board presence, blocks Mastermind and any Bat/Drowner they play. Both Preacher candidates are identical (same card). Pass wastes my turn. Activating Drowner still bad (loses card for stunned Siren). Leaf 7 shows GftT on my Preacher — annoyin"

## Turn 5 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Island
- MAD board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **55** (unblocked: us 20 vs 20)
    - `attack-all` scored **62** (1 block(s), response 1: us 20 vs 20; unblocked: us 20 vs 18)
- Pilot's reasoning: "Only Drowner can attack (Preacher summoning sick). Opp has 0 mana so no removal at instant speed — attack is safe. If Mastermind blocks: trade Drowner for their best card (2/1 flyer with card draw trigger) — removes their only flyer permanently. If no block: 2 damage AND keep Drowner. Either way bet"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 3 lands (3 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Island, Swamp
- MAD board: Spyglass Siren 1/1 (tapped) | 4 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
    - `Cast Preacher of the Schism` scored **55** (Cast Preacher of the Schism | s0: they cast Cast Floodpits Drowner | I do nothing: us 20 vs 20; Cast Preacher of the Schism | they respond on the stack: Cast Cut Down | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 20 vs 20; Cast Preacher of the Schism | s2: they cast Cast Faerie Mastermind | I do nothing: us 20 vs 20)
    - `Play Island` scored **45** (Play Island | s0: they cast Cast Go for the Throat | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; Play Island | s0: they cast Cast Go for the Throat | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; Play Island | s0: they cast Cast Go for the Throat | I do nothing: us 20 vs 20; Play Island | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; Play Island | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; Play Island | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 20 vs 20; Play Island | s2: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; Play Island | s2: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; Play Island | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20)
    - `Play Swamp` scored **45** (Play Swamp | they respond on the stack: Cast Cut Down | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; Play Swamp | they respond on the stack: Cast Cut Down | s0: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; Play Swamp | they respond on the stack: Cast Cut Down | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; Play Swamp | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 20 vs 20; Play Swamp | s2: they cast Cast Preacher of the Schism | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; Play Swamp | s2: they cast Cast Preacher of the Schism | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; Play Swamp | s2: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Play a 4th land to enable Sheoldred {2}{B}{B} next priority window. Both Swamp and Island work (Sheoldred needs BB, have Darkslick+Swamp regardless). Cast Preacher now delays Sheoldred by a turn and doesn't help nearly as much as landing the 4/5 deathtouch drain engine. Pass wastes tempo."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 4 lands (4 untapped)
- Pilot hand: Sheoldred, the Apocalypse, Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped) | 4 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Enduring Curiosity | on the stack I cast Cast Enduring Curiosity: us 20 vs 20; pass (hold everything) | s2: they cast Cast Enduring Curiosity | after it resolves I cast Cast Enduring Curiosity: us 20 vs 20; pass (hold everything) | s2: they cast Cast Enduring Curiosity | I do nothing: us 20 vs 20)
    - `Cast Sheoldred, the Apocalypse` scored **78** (Cast Sheoldred, the Apocalypse | they respond on the stack: Cast Cut Down | s0: they do nothing: us 20 vs 18; Cast Sheoldred, the Apocalypse | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 18; Cast Sheoldred, the Apocalypse | they respond on the stack: Cast Cut Down | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 20 vs 18)
    - `Cast Preacher of the Schism` scored **55** (Cast Preacher of the Schism | they respond on the stack: Cast Cut Down | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 20 vs 20; Cast Preacher of the Schism | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; Cast Preacher of the Schism | s2: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20)
    - `Cast Enduring Curiosity` scored **58** (Cast Enduring Curiosity | s0: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; Cast Enduring Curiosity | s1: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20; Cast Enduring Curiosity | s2: they cast Cast Preacher of the Schism | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Cast Sheoldred! It's my win condition — 4/5 deathtouch with drain-gain. Mana value 4 means Cut Down cannot hit it (Cut Down only kills 2-cost creatures — my earlier Drowner deaths confirm). Only GftT/Anoint could remove it. All Sheoldred leaves show her on board, opp at 18 already. Preacher and Curi"

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 (sick) | 4 lands (0 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **70** (after combat: us 19 vs 18)
- Pilot's reasoning: "Only one option (no-blocks) — nothing to attack me visible. Leaf shows minor 1-life loss but I keep Sheoldred and opp is at 18. Position strongly in my favor."

## Turn 9 — Upkeep [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism, Enduring Curiosity, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Enduring Curiosity: us 19 vs 16; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | after it resolves I cast Cast Enduring Curiosity: us 19 vs 16; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 16; pass (hold everything) | s1: they cast Cast Go for the Throat | on the stack I cast Cast Enduring Curiosity: us 19 vs 16; pass (hold everything) | s1: they cast Cast Go for the Throat | after it resolves I cast Cast Enduring Curiosity: us 19 vs 16; pass (hold everything) | s1: they cast Cast Go for the Throat | I do nothing: us 19 vs 16; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Enduring Curiosity: us 19 vs 16; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Enduring Curiosity: us 19 vs 16; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 16)
    - `Cast Enduring Curiosity` scored **78** (Cast Enduring Curiosity | s0: they cast Cast Preacher of the Schism | I do nothing: us 19 vs 16; Cast Enduring Curiosity | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 16; Cast Enduring Curiosity | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 16)
- Pilot's reasoning: "Cast Enduring Curiosity NOW while opp has all lands tapped (0 mana = can't counter/remove it). Flash 4/3 creature-enchantment sets up card draw when Sheoldred attacks. Even if opp has GftT for Sheoldred, Curiosity persists (returns as enchantment on death). Pass leaves that skip Curiosity are weaker"

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 (sick) | 4 lands (0 untapped)
- Pilot hand: Preacher of the Schism, Swamp, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 16; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 16; pass (hold everything) | s2: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 21 vs 16)
    - `Play Swamp` scored **68** (Play Swamp | s0: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 16; Play Swamp | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 21 vs 16; Play Swamp | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 16)
- Pilot's reasoning: "Play Swamp for 5th land — future flexibility. Can't cast anything this turn with all mana tapped from Curiosity (need 2+ for Bat, 3 for Preacher). Both Preachers have deathtouch — attacking Sheoldred into their Preacher trades unfavorably, so plan is to hold Sheoldred as blocker and win via drain-li"

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **21** vs MAD **18**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Pilot hand: Preacher of the Schism, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **75** (unblocked: us 21 vs 18)
    - `attack-all` scored **55** (1 block(s), response 1: us 21 vs 18; unblocked: us 21 vs 14)
- Pilot's reasoning: "Don't attack. If opp blocks with Preacher (correct play), Sheoldred dies via deathtouch — bad trade of my 5-mana drain engine for their 3-mana blocker. Attack-none keeps Sheoldred alive draining them 2/turn on their draws (they're at 18, I'm gaining life on my draws too). Worst-case for attack-all ("

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **21** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Pilot hand: Preacher of the Schism, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **55** (after combat | after blocks they cast Cast Cut Down: us 18 vs 16)
    - `Sheoldred, the Apocalypse>Preacher of the Schism` scored **45** (after combat | after blocks they cast Cast Go for the Throat: us 20 vs 16)
    - `Enduring Curiosity>Preacher of the Schism` scored **82** (after combat | after blocks they cast Cast Cut Down: us 20 vs 16)
    - `Sheoldred, the Apocalypse>Preacher of the Schism, Enduring Curiosity>Preacher of the Schism` scored **25** (after combat | after blocks they cast Cast Floodpits Drowner: us 20 vs 16)
- Pilot's reasoning: "Block Preacher with Curiosity — Curiosity's 4 power kills Preacher outright; Preacher's deathtouch kills Curiosity but Curiosity's ability returns it as an enchantment (still triggers card draw on combat damage). Net: I keep Sheoldred + Curiosity enchantment, take 0 damage, kill their Preacher. Bloc"

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 6 lands (6 untapped)
- Pilot hand: Preacher of the Schism, Deep-Cavern Bat, Swamp
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (sick) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 14; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 14; pass (hold everything) | s2: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 14)
    - `Cast Preacher of the Schism` scored **35** (Cast Preacher of the Schism | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 14; Cast Preacher of the Schism | they respond on the stack: Cast Floodpits Drowner | s1: they cast Cast Go for the Throat | I do nothing: us 22 vs 14; Cast Preacher of the Schism | s2: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 22 vs 14)
    - `Cast Deep-Cavern Bat` scored **55** (Cast Deep-Cavern Bat | they respond on the stack: Cast Anoint with Affliction | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 22 vs 14; Cast Deep-Cavern Bat | they respond on the stack: Cast Floodpits Drowner | s1: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 14; Cast Deep-Cavern Bat | s2: they cast Cast Enduring Curiosity | I do nothing: us 22 vs 14)
    - `Play Swamp` scored **55** (Play Swamp | they respond on the stack: Cast Cut Down | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 14; Play Swamp | they respond on the stack: Cast Anoint with Affliction | after it resolves they cast: Cast Cut Down | s1: they do nothing: us 22 vs 14; Play Swamp | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 14)
- Pilot's reasoning: "Play Swamp first — safe mana development, then cast Bat/Preacher in subsequent windows. Cast Preacher first is risky (leaf 4 shows opp burning GftT on Sheoldred). Bat/Swamp both have decent worst-case; Swamp gives max flexibility (6 mana next window allows Bat + Preacher both). Life lead 22 vs 16 — "

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 7 lands (7 untapped)
- Pilot hand: Preacher of the Schism, Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (sick) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 14; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 14; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 14)
    - `Cast Preacher of the Schism` scored **55** (Cast Preacher of the Schism | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 22 vs 14; Cast Preacher of the Schism | they respond on the stack: Cast Floodpits Drowner | s1: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 14; Cast Preacher of the Schism | they respond on the stack: Cast Anoint with Affliction | s2: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 14)
    - `Cast Deep-Cavern Bat` scored **32** (Cast Deep-Cavern Bat | they respond on the stack: Cast Floodpits Drowner | s0: they cast Cast Go for the Throat | I do nothing: us 22 vs 14; Cast Deep-Cavern Bat | they respond on the stack: Cast Anoint with Affliction | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 14; Cast Deep-Cavern Bat | they respond on the stack: Cast Cut Down | s2: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 14)
- Pilot's reasoning: "Cast Preacher — 2/4 deathtouch is safer than 1/1 Bat, and Preacher survives Cut Down (mv 3, unless power-based). Cast Bat worst-case (leaf 6) has GftT killing Sheoldred, terrible. Preacher worst-case just has Sheoldred stunned, not dead. Pass just lets opp develop."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 7 lands (4 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (sick) | 4 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 22 vs 14; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 22 vs 14; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 14)
    - `Cast Deep-Cavern Bat` scored **60** (Cast Deep-Cavern Bat | they respond on the stack: Cast Floodpits Drowner | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 14; Cast Deep-Cavern Bat | they respond on the stack: Cast Floodpits Drowner | s1: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 14; Cast Deep-Cavern Bat | s2: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 14)
- Pilot's reasoning: "Cast Bat — its ETB lets me peek at opp hand and exile a nonland card. Given opp has 5 cards including possibly their own Sheoldred (per leaf 0/1 sim), Bat can pre-empt their biggest threat. Even if Bat dies, ETB peek resolved. Passing lets opp resolve their game plan freely."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **22** vs MAD **16**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 7 lands (2 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 (sick) | 4 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **62** (unblocked: us 22 vs 16)
    - `attack-all` scored **60** (1 block(s), response 1: us 22 vs 17; unblocked: us 22 vs 12)
- Pilot's reasoning: "Attack Sheoldred. If unblocked (leaf 2): 4 dmg + Curiosity card draw (huge). If blocked by VT (leaf 1): I remove their blocker for cost of 1 life gain, Sheoldred survives easily. Attack-none is safe but wastes tempo — I'm dominating and need to close."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **22** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 (sick) | 7 lands (2 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1, Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **65** (after combat: us 21 vs 14)
- Pilot's reasoning: "Only one option (no-blocks). Opp attacked with Siren (flying) only. Take 1 damage → life 21. Still ahead 21 vs 14."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 7 lands (7 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1, Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 14; pass (hold everything) | s1: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 14; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 14)
    - `Cast Deep-Cavern Bat` scored **60** (Cast Deep-Cavern Bat | s0: they cast Cast Faerie Mastermind | I do nothing: us 21 vs 14; Cast Deep-Cavern Bat | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 21 vs 14; Cast Deep-Cavern Bat | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 21 vs 14)
- Pilot's reasoning: "Cast Bat. ETB gives info + can exile a nonland card from opp's hand (probably Cut Down/GftT). Additional flying lifelink attacker."

## Turn 13 — Precombat Main [choose]
- Life: pilot **21** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 7 lands (5 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1, Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Menu: [0] Enduring Curiosity; [1] Cut Down; [2] Anoint with Affliction
- **Chose: target Anoint with Affliction**
- Pilot's reasoning: "Exile Anoint with Affliction — it's the versatile removal that can kill Sheoldred (Cut Down only hits low-mv creatures, can't touch Sheoldred at mv 4). Removing Anoint protects my drain engine."

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **21** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 7 lands (5 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1, Sheoldred, the Apocalypse 4/5 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **72** (unblocked: us 21 vs 14)
    - `attack-all` scored **45** (1 block(s), response 3: us 21 vs 12; 1 block(s), response 1: us 21 vs 13; 2 block(s), response 5: us 21 vs 15)
    - `hold[Sheoldred, the Apocalypse]` scored **55** (1 block(s), response 1: us 21 vs 15; unblocked: us 21 vs 12; 1 block(s), response 2: us 21 vs 14)
    - `hold[Preacher of the Schism]` scored **40** (1 block(s), response 2: us 21 vs 14; 1 block(s), response 1: us 21 vs 15; unblocked: us 21 vs 10)
- Pilot's reasoning: "Attack-none has best worst-case. Attack-all worst (leaf 1) loses Sheoldred in a bad trade. If I hold defensive posture, on their turn I can block their Sheoldred with mine (trade), Preacher blocks VT (deathtouch kills VT), Bat blocks Siren. Wipe their board defensively. Then push next turn with life"

## Turn 14 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **21** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5, Preacher of the Schism 2/4 | 7 lands (5 untapped)
- Pilot hand: empty
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1, Sheoldred, the Apocalypse 4/5 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **45** (after combat: us 16 vs 14)
    - `Sheoldred, the Apocalypse>Sheoldred, the Apocalypse` scored **62** (after combat: us 20 vs 14)
    - `Preacher of the Schism>Sheoldred, the Apocalypse` scored **75** (after combat | after blocks they cast Cast Floodpits Drowner: us 20 vs 14)
    - `Sheoldred, the Apocalypse>Sheoldred, the Apocalypse, Preacher of the Schism>Sheoldred, the Apocalypse` scored **55** (after combat: us 20 vs 14)
- Pilot's reasoning: "Preacher blocks Sheoldred — both die from deathtouch (Preacher 2/4 vs Sheoldred 4/5, both have deathtouch, mutual kill). Best trade: my 3-mana Preacher for their 5-mana Sheoldred. Keeps my Sheoldred alive as the drain engine + kills theirs (drain-gain no longer cancels). Life 20 vs 14 with only Sire"

## Turn 15 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 12; pass (hold everything) | s1: they cast Cast Enduring Curiosity | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Enduring Curiosity | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Enduring Curiosity | I do nothing: us 22 vs 12; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12)
    - `Cast Go for the Throat` scored **55** (Cast Go for the Throat | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; Cast Go for the Throat | they respond on the stack: Cast Cut Down | s1: they cast Cast Enduring Curiosity | I do nothing: us 22 vs 12; Cast Go for the Throat | they respond on the stack: Cast Floodpits Drowner | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12)
- Pilot's reasoning: "Hold Go for the Throat as instant response — perfect for their next big creature (Bat/Curiosity/Kaito). Casting now wastes it on a 1/1. Pass through and use GftT reactively."

## Turn 15 — Draw [leaf_eval/priority]
- Life: pilot **22** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 12; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; pass (hold everything) | s2: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 12)
    - `Cast Go for the Throat` scored **55** (Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 12; Cast Go for the Throat | s1: they cast Cast Spyglass Siren | I do nothing: us 22 vs 12; Cast Go for the Throat | they respond on the stack: Cast Faerie Mastermind | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12)
- Pilot's reasoning: "Hold Go for the Throat as instant response — perfect for their next big creature (Bat/Curiosity/Kaito). Casting now wastes it on a 1/1. Pass through and use GftT reactively."

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 12; pass (hold everything) | s1: they cast Cast Floodpits Drowner | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 12; pass (hold everything) | s2: they cast Cast Enduring Curiosity | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Enduring Curiosity | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Enduring Curiosity | I do nothing: us 22 vs 12)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat | they respond on the stack: Cast Floodpits Drowner | s0: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 12; Cast Go for the Throat | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 12; Cast Go for the Throat | s2: they cast Cast Enduring Curiosity | I do nothing: us 22 vs 12)
- Pilot's reasoning: "Pass and hold GftT as reactive. Best sub-branches: stack-response on Drowner keeps Sheoldred untapped and kills the 2/1. Casting GftT on Siren (candidate 2) is a total waste — Siren is tapped, only trades removal for a 1/1, and leaves me with no answer to Preacher/Curiosity/Bat."

## Turn 15 — Begin Combat [leaf_eval/priority]
- Life: pilot **22** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **55** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 12; pass (hold everything) | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 12; pass (hold everything) | s2: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 12)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Spyglass Siren | I do nothing: us 22 vs 12; Cast Go for the Throat | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; Cast Go for the Throat | s2: they cast Cast Enduring Curiosity | I do nothing: us 22 vs 12)
- Pilot's reasoning: "Pass through Begin Combat — best line is post-resolution GftT on their Preacher next turn (kills the 2/4 deathtouch/lifelink threat). Stack-response on Siren leaves Preacher alive (much bigger threat). Casting GftT now during my combat step wastes it on Siren AND draws out opp's Anoint response, lea"

## Turn 15 — Declare Attackers [leaf_eval/priority]
- Life: pilot **22** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 22 vs 12; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 22 vs 12; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; Cast Go for the Throat | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s2: they cast Cast Faerie Mastermind | I do nothing: us 22 vs 12)
- Pilot's reasoning: "Pass — hold GftT reactively. Best branch by far: leaf 1, post-resolution GftT on opp's Sheoldred (must-kill target — mirror Sheoldred would drain 2/turn and offset my Curiosity value). Also good: kill an activated Restless Reef (4/4 deathtouch). Kaito is a planeswalker so GftT can't touch it — hold "

## Turn 15 — Declare Blockers [leaf_eval/priority]
- Life: pilot **22** vs MAD **14**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped), Vampire Token 1/1 | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **22** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 12; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; pass (hold everything) | s2: they cast Cast Spyglass Siren | on the stack I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Spyglass Siren | after it resolves I cast Cast Go for the Throat: us 22 vs 12; pass (hold everything) | s2: they cast Cast Spyglass Siren | I do nothing: us 22 vs 12)
    - `Cast Go for the Throat` scored **22** (Cast Go for the Throat | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; Cast Go for the Throat | they respond on the stack: Cast Floodpits Drowner | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12; Cast Go for the Throat | they respond on the stack: Cast Faerie Mastermind | after it resolves they cast: Cast Cut Down | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 12)
- Pilot's reasoning: "Deep-Cavern Bat scenario is CRITICAL: doing nothing (leaf 1) lets Bat ETB exile my only card (GftT) — devastating. Stack-response (leaf 0) kills Bat and denies the exile — best pass branch. Kaito is a planeswalker so GftT can't target it (leaves 2/3 wasted); nothing (leaf 4) keeps GftT for future. S"

## Turn 15 — Combat Damage [leaf_eval/priority]
- Life: pilot **22** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **22** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 22 vs 15; pass (hold everything) | s1: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 13; pass (hold everything) | s2: they cast Cast Go for the Throat | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Go for the Throat | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Go for the Throat | I do nothing: us 22 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat | they respond on the stack: Cast Cut Down | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 13; Cast Go for the Throat | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 13; Cast Go for the Throat | they respond on the stack: Cast Floodpits Drowner | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactively. Best branch: leaf 2 (stack-response on opp's Preacher denies its 2-life drain ETB AND kills the 2/4 deathtouch/lifelink threat). Leaf 1 is the disaster case: doing nothing lets Bat ETB exile my GftT — must respond to Bat. Opp GftT scenarios (5-7) are painful but survivab"

## Turn 15 — End Combat [leaf_eval/priority]
- Life: pilot **22** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **22** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 13; pass (hold everything) | s2: they cast Cast Floodpits Drowner | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 13; Cast Go for the Throat | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 13; Cast Go for the Throat | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactively. Best branch: leaf 5 (stack-response on Drowner, prevents Sheoldred from being tap-locked next turn AND kills the 2/1). Leaf 0 (stack GftT on Bat) is also good — denies Bat's ETB from exiling my GftT. Leaf 1 is disaster — Bat exiles my only card. Kaito is a planeswalker s"

## Turn 15 — Postcombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Spyglass Siren | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s0: they cast Cast Spyglass Siren | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s0: they cast Cast Spyglass Siren | I do nothing: us 22 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 22 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 22 vs 13; Cast Go for the Throat | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 13; Cast Go for the Throat | s2: they do nothing: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactively. Best branch: leaf 3, stack-response on Preacher denies its 2-drain ETB and kills a 2/4 threat. Second best: post-resolution GftT on Preacher (leaf 4). Siren scenarios: waste of GftT on a 1/1 — hold. Kaito is a PW so GftT can't touch it. Casting GftT proactively (candidat"

## Turn 15 — End Turn [leaf_eval/priority]
- Life: pilot **22** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (4 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **22** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 22 vs 13; pass (hold everything) | s1: they cast Cast Floodpits Drowner | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s1: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s1: they cast Cast Floodpits Drowner | I do nothing: us 22 vs 13; pass (hold everything) | s2: they cast Cast Enduring Curiosity | on the stack I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Enduring Curiosity | after it resolves I cast Cast Go for the Throat: us 22 vs 13; pass (hold everything) | s2: they cast Cast Enduring Curiosity | I do nothing: us 22 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | they respond on the stack: Cast Go for the Throat | s0: they cast Cast Spyglass Siren | I do nothing: us 22 vs 15; Cast Go for the Throat | they respond on the stack: Cast Go for the Throat | s1: they cast Cast Spyglass Siren | I do nothing: us 22 vs 15; Cast Go for the Throat | they respond on the stack: Cast Floodpits Drowner | s2: they cast Cast Spyglass Siren | I do nothing: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Best branch: leaf 2 (stack-response on Drowner denies Sheoldred tap-lock AND kills 2/1). Leaf 6 (post GftT on Curiosity) removes 4/3 flyer body. Leaf 1 disaster: Bat ETB exiles my GftT. Casting GftT now (candidate 2) is catastrophic — leaves 8/9 show opp responds with their own Gft"

## Turn 16 — Upkeep [leaf_eval/priority]
- Life: pilot **22** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **82** (pass (hold everything): us 22 vs 15)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 22 vs 15)
- Pilot's reasoning: "Pass — hold GftT reactive. Opp's upkeep triggers Sheoldred drain (opp 15→13 on their draw). Casting GftT on Siren (only opp creature) wastes removal on a 1/1 flyer that Sheoldred deathtouch handles anyway. Keep GftT for real threats: Drowner (tap-lock protection), Bat (hand-exile protection), Preach"

## Turn 16 — Draw [leaf_eval/priority]
- Life: pilot **22** vs MAD **15**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **82** (pass (hold everything): us 22 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactive. Opp draw confirmed drain: 15→13. Casting GftT on Siren (only opp creature) wastes removal on a 1/1 flyer that Sheoldred deathtouch handles anyway. Opp now has 4 cards, so a real threat is coming — save GftT for it."

## Turn 16 — Draw [leaf_eval/priority]
- Life: pilot **22** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **82** (pass (hold everything): us 22 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactive. Same state as previous priority window. Opp at 13, Sheoldred drain triggered. Casting GftT on Siren wastes removal on a 1/1 flyer."

## Turn 16 — Precombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **13**
- Pilot board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 22 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactive. Both leaves project Sheoldred dying (opp likely has Anoint with Affliction or GftT that they'll deploy). But casting GftT proactively on Siren burns my only interaction on a 1/1 and doesn't save Sheoldred anyway. Better to keep GftT for opp's next big threat (Preacher, Cur"

## Turn 16 — Precombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 22 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 22 vs 13)
- Pilot's reasoning: "Sheoldred died to opp GftT. Now I'm in trouble but not lost — 22 life, Curiosity engine, 6 lands, GftT in hand. Casting GftT on Siren (only opp creature) wastes my last interaction on a 1/1 chip damage flyer. Opp has 3 cards and will develop threats — save GftT for real threats (Preacher, Curiosity,"

## Turn 16 — Begin Combat [leaf_eval/priority]
- Life: pilot **22** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 22 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Opp beginning combat, only attacker is Siren 1/1 flyer (1 damage to me if unblocked). Not worth burning my only removal on. Save GftT for opp's real threats (Preacher, Curiosity as creature, opp Sheoldred, Bat). I still have 22 life and can absorb chip damage from Siren while I try"

## Turn 16 — Declare Attackers [leaf_eval/priority]
- Life: pilot **22** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 22 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Opp declared Siren as attacker (now tapped). Killing Siren with GftT prevents only 1 chip damage — not worth burning my only removal. 22 life gives me lots of runway. Save GftT for opp's real threats coming next turns."

## Turn 16 — Declare Blockers [leaf_eval/priority]
- Life: pilot **22** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 22 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 22 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Same rationale: Siren is 1/1 attacker, 1 damage isn't worth burning removal. Save GftT for real threats."

## Turn 16 — Combat Damage [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Siren hit for 1 (life 22→21 confirmed). Still ahead on life 21 vs 13. Save GftT for real threats."

## Turn 16 — End Combat [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. End of combat, no reason to burn removal on tapped Siren. Save for real threats."

## Turn 16 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Postcombat main, opp yet to cast their sorcery-speed threats. Save removal for real threats."

## Turn 16 — End Turn [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. End of opp's turn 16. Nothing to interact with. Save for real threats coming next turn."

## Turn 17 — Upkeep [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Faerie Mastermind | I do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Cut Down | s1: they cast Cast Enduring Curiosity | I do nothing: us 21 vs 13; Cast Go for the Throat | s2: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactive. My upkeep, about to draw. Best branch: stack GftT on Drowner if opp casts one (leaf 0). Kaito is PW — GftT can't touch it. Casting GftT now (candidate 2) draws opp's Anoint/Cut Down response AND lets them deploy Preacher/Curiosity uncontested."

## Turn 17 — Draw [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat, Island
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **38** (pass (hold everything) | s0: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Spyglass Siren | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Spyglass Siren | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Spyglass Siren | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | s0: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13; Cast Go for the Throat | s1: they do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s2: they do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Drew an Island, still hunting a creature. Best branch: stack-response on Preacher (denies ETB drain + kills 2/4 threat). Kaito is PW, GftT can't touch it. Siren is 1/1 — waste of GftT. Casting GftT proactively (candidate 2) burns removal for nothing and lets opp deploy Preacher una"

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 7 lands (7 untapped)
- Pilot hand: Go for the Throat, Island
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 21 vs 13; Cast Go for the Throat | s2: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13)
    - `Play Island` scored **50** (Play Island | s0: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 21 vs 13; Play Island | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 21 vs 13; Play Island | they respond on the stack: Cast Cut Down | s1: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 21 vs 13; Play Island | they respond on the stack: Cast Cut Down | s1: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 13; Play Island | s2: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 21 vs 13; Play Island | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Play Island — free land development, no reason to skip. Then still holds GftT reactive. Best branch: stack GftT on Bat (denies exile) or Preacher (denies ETB). Casting GftT proactively wastes removal. Passing without playing land wastes tempo."

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Go for the Throat | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Go for the Throat | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Faerie Mastermind | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Faerie Mastermind | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Faerie Mastermind | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Cut Down | s1: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13; Cast Go for the Throat | s2: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT reactive. Best branch: stack-response on Preacher (denies 2-drain ETB, kills 2/4). Faerie Mastermind is mid-value threat. Casting GftT proactively (candidate 2) draws opp's Anoint/Cut Down response and lets opp deploy Preacher unanswered."

## Turn 17 — Begin Combat [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Faerie Mastermind | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Faerie Mastermind | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Faerie Mastermind | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13; Cast Go for the Throat | s1: they cast Cast Spyglass Siren | I do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Cut Down | s2: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. CRITICAL: if opp casts Sheoldred (s0), stack-response GftT kills it before ETB — huge win, must not let it live. Kaito = PW, GftT can't touch it (hold instead). Faerie Mastermind is a card-draw problem but manageable. Casting GftT proactively burns removal with no target."

## Turn 17 — Declare Attackers [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat | s0: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s1: they do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s2: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. No creatures to attack with. Kaito scenarios (s0, s2): PW, GftT can't target — hold. Bat scenario (s1): stack-response denies exile of my hand (leaf 3) is best; nothing lets Bat exile GftT. Casting GftT proactively wastes removal."

## Turn 17 — End Combat [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Floodpits Drowner | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat | they respond on the stack: Cast Go for the Throat | s0: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 13; Cast Go for the Throat | they respond on the stack: Cast Anoint with Affliction | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 21 vs 13; Cast Go for the Throat | s2: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Best branch: stack-response on Preacher (leaf 3, denies 2-drain ETB + kills 2/4). Second: stack GftT on Drowner (leaf 6). Map explore = artifact ability, not a creature spell — GftT does nothing useful there. Casting GftT proactively wastes it."

## Turn 17 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat | s0: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13; Cast Go for the Throat | s1: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13; Cast Go for the Throat | s2: they cast Cast Deep-Cavern Bat | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. TOP branch: stack-response on opp Sheoldred (leaf 0, must-kill target — kills 4/5 threat + drain engine). Kaito = PW, can't target. Casting GftT proactively wastes removal."

## Turn 17 — End Turn [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 (tapped) | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything) | s0: they cast Cast Floodpits Drowner | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Floodpits Drowner | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s0: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 13; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s1: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 21 vs 13; pass (hold everything) | s2: they cast Cast Preacher of the Schism | on the stack I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Preacher of the Schism | after it resolves I cast Cast Go for the Throat: us 21 vs 13; pass (hold everything) | s2: they cast Cast Preacher of the Schism | I do nothing: us 21 vs 13)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat | they respond on the stack: Cast Cut Down | s0: they cast Cast Sheoldred, the Apocalypse | I do nothing: us 21 vs 13; Cast Go for the Throat | s1: they cast Cast Faerie Mastermind | I do nothing: us 21 vs 13; Cast Go for the Throat | s2: they cast Cast Floodpits Drowner | I do nothing: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. TOP branch: stack-response on opp Sheoldred (leaf 3, must-kill). Second: stack on Preacher (leaf 6, deny ETB), stack on Drowner (leaf 0). Casting GftT proactively wastes removal and lets opp deploy Sheoldred unanswered."

## Turn 18 — Upkeep [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Opp's upkeep, save removal for reactive use. Killing Siren wastes GftT on a 1/1."

## Turn 18 — Draw [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 13)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 21 vs 13)
- Pilot's reasoning: "Pass — hold GftT. Opp draw phase, wait for their main phase threats. Casting GftT on Siren wastes removal."

## Turn 18 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Go for the Throat
- MAD board: Spyglass Siren 1/1 | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything): us 21 vs 13)
    - `Cast Go for the Throat` scored **95** (Cast Go for the Throat: us 21 vs 13)
- Pilot's reasoning: "CAST GO FOR THE THROAT NOW! Opp just cast Sheoldred and TAPPED OUT (0 mana available). This is exactly the trigger from my standing plan. Killing opp's Sheoldred is critical — otherwise their drain engine punishes every card I draw. Opp cannot respond with counter/removal since they have no mana. Pa"

## Turn 19 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **13**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Sheoldred, the Apocalypse 4/5 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **25** (pass (hold everything) | s0: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 15; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 19 vs 15; pass (hold everything) | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 15)
    - `Cast Preacher of the Schism` scored **70** (Cast Preacher of the Schism | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 19 vs 15; Cast Preacher of the Schism | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 19 vs 15; Cast Preacher of the Schism | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 15)
- Pilot's reasoning: "Cast Preacher of the Schism NOW! Critical: if I pass and opp casts Bat (leaf 0), Bat's ETB exiles my only card (Preacher). Casting Preacher puts a 2/4 deathtouch on board — locks opp Sheoldred from attacking (mutual deathtouch trade), threatens Kaito planeswalker, and forces opp to burn removal."

## Turn 20 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **19** vs MAD **15**
- Pilot board: Preacher of the Schism 2/4 (sick) | 8 lands (5 untapped)
- Pilot hand: empty
- MAD board: Sheoldred, the Apocalypse 4/5 (tapped) | 7 lands (6 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **40** (after combat | after blocks they cast Cast Anoint with Affliction: us 15 vs 15)
    - `Preacher of the Schism>Sheoldred, the Apocalypse` scored **82** (after combat | after blocks they cast Cast Anoint with Affliction: us 19 vs 15)
- Pilot's reasoning: "BLOCK Sheoldred with Preacher! Both have deathtouch — mutual kill. My Preacher 2/4 kills Sheoldred (any damage + deathtouch), Sheoldred 4/5 kills Preacher (4 damage matches toughness). Net: both dead, my life stays at 19 vs opp 15. No blocks = take 4 damage, life drops to 15 vs 15 (even) AND Sheoldr"

## Turn 21 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **15**
- Pilot board: no creatures | 8 lands (8 untapped)
- Pilot hand: Spyglass Siren
- MAD board: no creatures | 7 lands (6 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast Cast Enduring Curiosity | I do nothing: us 19 vs 15; pass (hold everything) | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 19 vs 15; pass (hold everything) | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 19 vs 15)
    - `Cast Spyglass Siren` scored **55** (Cast Spyglass Siren | they respond on the stack: Cast Floodpits Drowner | s0: they cast Cast Anoint with Affliction | I do nothing: us 19 vs 15; Cast Spyglass Siren | s1: they cast Cast Deep-Cavern Bat | I do nothing: us 19 vs 15; Cast Spyglass Siren | they respond on the stack: Cast Floodpits Drowner | s2: they cast {1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery. | I do nothing: us 19 vs 15)
- Pilot's reasoning: "Cast Spyglass Siren! Board is empty on opp's side (no creatures). Siren is 1/1 flyer + creates Map token. It can attack next turn unblocked (opp has no flyers). Combat damage triggers Curiosity — free card draw engine online. Passing gives opp a turn to develop Curiosity/Kaito unimpeded."

## Turn 23 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **15**
- Pilot board: no creatures | 9 lands (9 untapped)
- Pilot hand: Island
- MAD board: Enduring Curiosity 4/3 (sick) | 8 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything) | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 19 vs 15; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 19 vs 15; pass (hold everything) | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 19 vs 15)
    - `Play Island` scored **55** (Play Island | s0: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 19 vs 15; Play Island | s1: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 19 vs 15; Play Island | s2: they cast Cast Kaito, Bane of Nightmares | I do nothing: us 19 vs 15)
- Pilot's reasoning: "Play Island for free tempo — extra land, no downside. Nothing else to do with empty hand. Passing without playing Island wastes tempo. Cannot use Map Token (no creature target on my side)."

## Turn 25 — Precombat Main [leaf_eval/priority]
- Life: pilot **11** vs MAD **15**
- Pilot board: no creatures | 10 lands (10 untapped)
- Pilot hand: Darkslick Shores
- MAD board: Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick) | 9 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **30** (pass (hold everything) | s0: they cast Cast Enduring Curiosity | I do nothing: us 11 vs 15; pass (hold everything) | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 11 vs 15; pass (hold everything) | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 11 vs 15)
    - `Play Darkslick Shores` scored **45** (Play Darkslick Shores | s0: they cast Cast Enduring Curiosity | I do nothing: us 11 vs 15; Play Darkslick Shores | s1: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 11 vs 15; Play Darkslick Shores | s2: they cast {2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land. | I do nothing: us 11 vs 15)
- Pilot's reasoning: "Play Darkslick Shores for free tempo. Empty of spells anyway. All leaves have similar bleak outcomes — opp will kill me next combat. Playing the land at least keeps mana available for any topdecked removal."
