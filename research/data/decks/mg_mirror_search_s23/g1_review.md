# Decision review — g1.jsonl

Result: **pilot won** in 13 turns. 32 real decisions out of 209 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Forest, Forest, Forest, Forest, Earthbender Ascension, Mossborn Hydra, Sazh's Chocobo
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "4 lands plus Chocobo, Hydra, and Ascension is a keepable curve with strong landfall synergy - Chocobo T1, then Hydra/Ascension by T3, land count is slightly high but the hand has real payoffs for hitting land drops."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Forest, Forest, Forest, Forest, Earthbender Ascension, Mossborn Hydra, Sazh's Chocobo
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Llanowar Elves | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Sazh's Chocobo | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. Then if you control four or more lands, untap that land. | I do nothing: us 20 vs 20)
    - `Play Forest` scored **55** (Play Forest | s0: they do nothing: us 20 vs 20; Play Forest | s1: they cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. Then if you control four or more lands, untap that land. | I do nothing: us 20 vs 20; Play Forest | s2: they cast Cast Llanowar Elves | I do nothing: us 20 vs 20)
    - `Play Forest` scored **None** ()
    - `Play Forest` scored **55** (Play Forest | s1: they cast Cast Sazh's Chocobo | I do nothing: us 20 vs 20)
    - `Play Forest` scored **None** ()
- Pilot's reasoning: "Playing our land on turn 1 is strictly better than holding it since we need to hit land drops for our landfall payoffs (Chocobo, Hydra, Ascension); passing with no land in play is pure tempo loss."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Forest, Forest, Forest, Earthbender Ascension, Mossborn Hydra, Sazh's Chocobo
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything) | s0: they cast Cast Llanowar Elves | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast Cast Sazh's Chocobo | I do nothing: us 20 vs 20; pass (hold everything) | s2: they do nothing: us 20 vs 20)
    - `Cast Sazh's Chocobo` scored **58** (Cast Sazh's Chocobo | s0: they cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. | I do nothing: us 20 vs 20; Cast Sazh's Chocobo | s1: they do nothing: us 20 vs 20)
- Pilot's reasoning: "Casting Sazh's Chocobo on turn 1 develops our board on curve and starts growing a landfall threat every turn, clearly better than passing with an empty board."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Sazh's Chocobo 0/1 | 1 lands (1 untapped)
- Pilot hand: Forest, Forest, Forest, Earthbender Ascension, Mossborn Hydra, Forest
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Badgermole Cub | I do nothing: us 20 vs 20; pass (hold everything) | s1: they cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. Then if you control four or more lands, untap that land. | I do nothing: us 20 vs 20; pass (hold everything) | s2: they cast Cast Llanowar Elves | I do nothing: us 20 vs 20)
    - `Play Forest` scored **53** (Play Forest | s0: they cast Cast Badgermole Cub | I do nothing: us 20 vs 20; Play Forest | s1: they cast Cast Esper Origins | I do nothing: us 20 vs 22; Play Forest | s2: they cast Cast Sazh's Chocobo | I do nothing: us 20 vs 20)
    - `Play Forest` scored **55** (Play Forest | s0: they do nothing: us 20 vs 20; Play Forest | s1: they cast Cast Sazh's Chocobo | I do nothing: us 20 vs 20)
    - `Play Forest` scored **55** (Play Forest | s0: they cast Cast Llanowar Elves | I do nothing: us 20 vs 20; Play Forest | s1: they do nothing: us 20 vs 20)
    - `Play Forest` scored **53** (Play Forest | s0: they cast Cast Sazh's Chocobo | I do nothing: us 20 vs 20; Play Forest | s1: they cast Cast Llanowar Elves | I do nothing: us 20 vs 20; Play Forest | s2: they cast Cast Esper Origins | I do nothing: us 20 vs 22)
- Pilot's reasoning: "Playing the land now triggers landfall on Chocobo (1/2) at no opportunity cost since we can't cast Earthbender Ascension or Mossborn Hydra yet anyway; passing just wastes the land drop for this turn."

## Turn 3 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Sazh's Chocobo 1/2 | 2 lands (2 untapped)
- Pilot hand: Forest, Forest, Earthbender Ascension, Mossborn Hydra, Forest
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 20 vs 20)
    - `attack-all` scored **53** (unblocked: us 20 vs 19)
- Pilot's reasoning: "Attacking for 1 is free damage since opponent has no creatures to punish the tapped-out Chocobo, and they can't attack back with an empty board anyway."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Sazh's Chocobo 1/2 | 2 lands (2 untapped)
- Pilot hand: Forest, Forest, Earthbender Ascension, Mossborn Hydra, Forest, Llanowar Elves
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (sick) | 1 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **46** (pass (hold everything) | s0: they cast Cast Earthbender Ascension | I do nothing: us 20 vs 19; pass (hold everything) | s1: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 19; pass (hold everything) | s2: they cast Cast Mightform Harmonizer with Warp | I do nothing: us 20 vs 19)
    - `Play Forest` scored **55** (Play Forest | s0: they cast Cast Mightform Harmonizer with Warp | I do nothing: us 20 vs 19; Play Forest | s1: they cast Cast Badgermole Cub | I do nothing: us 20 vs 19; Play Forest | s2: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 19)
    - `Play Forest` scored **55** (Play Forest | s0: they cast Cast Mossborn Hydra | I do nothing: us 20 vs 19; Play Forest | s2: they cast Cast Icetill Explorer | I do nothing: us 20 vs 19)
    - `Play Forest` scored **55** (Play Forest | s0: they cast Cast Earthbender Ascension | I do nothing: us 20 vs 19; Play Forest | s1: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 19; Play Forest | s2: they cast Cast Icetill Explorer | I do nothing: us 20 vs 19)
    - `Cast Llanowar Elves` scored **44** (Cast Llanowar Elves | s0: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 19; Cast Llanowar Elves | s1: they cast Cast Icetill Explorer | I do nothing: us 20 vs 19)
- Pilot's reasoning: "Playing a land grows Chocobo via landfall and gets us to 3 mana for Earthbender Ascension or Mossborn Hydra later this turn, clearly better than passing or skipping our land drop to cast Llanowar Elves instead."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Sazh's Chocobo 2/3 | 3 lands (3 untapped)
- Pilot hand: Forest, Earthbender Ascension, Mossborn Hydra, Forest, Llanowar Elves
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (sick) | 1 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything) | s0: they cast Cast Mossborn Hydra | I do nothing: us 20 vs 19; pass (hold everything) | s1: they cast Cast Mightform Harmonizer with Warp | I do nothing: us 20 vs 19; pass (hold everything) | s2: they cast Cast Surrak, Elusive Hunter | I do nothing: us 20 vs 19)
    - `Cast Earthbender Ascension` scored **60** (Cast Earthbender Ascension | s0: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 19; Cast Earthbender Ascension | s1: they cast Cast Mightform Harmonizer with Warp | I do nothing: us 20 vs 19; Cast Earthbender Ascension | s2: they cast Cast Llanowar Elves | I do nothing: us 20 vs 19)
    - `Cast Mossborn Hydra` scored **53** (Cast Mossborn Hydra | s0: they cast Cast Mossborn Hydra | I do nothing: us 20 vs 19; Cast Mossborn Hydra | s1: they cast Cast Icetill Explorer | I do nothing: us 20 vs 19; Cast Mossborn Hydra | s2: they cast Cast Esper Origins | I do nothing: us 20 vs 21)
    - `Cast Llanowar Elves` scored **46** (Cast Llanowar Elves | s0: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 19; Cast Llanowar Elves | s1: they cast Cast Earthbender Ascension | I do nothing: us 20 vs 19; Cast Llanowar Elves | s2: they cast Cast Badgermole Cub | I do nothing: us 20 vs 19)
- Pilot's reasoning: "Earthbender Ascension is clearly the strongest play: it grows Chocobo to 3/4 via the fetched land's landfall trigger, adds a 2/2 haste creature-land, and starts the quest-counter engine, far outpacing Mossborn Hydra (a lone 1/1) or Llanowar Elves (a mana dork with no immediate board impact)."

## Turn 5 — Precombat Main [target]
- Life: pilot **20** vs MAD **19**
- Pilot board: Sazh's Chocobo 2/3 | 4 lands (1 untapped)
- Pilot hand: Forest, Mossborn Hydra, Forest, Llanowar Elves
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (sick) | 1 lands (0 untapped)
- Menu: [0] Forest (A); [1] Forest (A); [2] Forest (A)
- **Chose: target Forest (A)**
- Pilot's reasoning: "All three Forests are already tapped from casting Ascension and are otherwise identical, so it doesn't matter which becomes the 2/2 haste creature-land."

## Turn 5 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **19**
- Pilot board: Sazh's Chocobo 3/4, Forest 2/2 (tapped) | 4 lands (1 untapped)
- Pilot hand: Forest, Mossborn Hydra, Forest, Llanowar Elves
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (sick) | 1 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 20 vs 19)
    - `attack-all` scored **60** (unblocked: us 20 vs 16; 1 block(s), response 1: us 20 vs 19)
- Pilot's reasoning: "Attacking with Chocobo is free value: if unblocked we deal 3, and if blocked by the summoning-sick Badgermole Cub, our 3/4 kills it while surviving easily."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **20**
- Pilot board: Sazh's Chocobo 3/4, Forest 2/2 | 4 lands (4 untapped)
- Pilot hand: Forest, Mossborn Hydra, Forest, Llanowar Elves, Esper Origins
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **46** (pass (hold everything) | s0: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 20; pass (hold everything) | s1: they cast Flashback {3}{G} | I do nothing: us 18 vs 22; pass (hold everything) | s2: they cast Flashback {3}{G} | I do nothing: us 18 vs 22)
    - `Play Forest` scored **60** (Play Forest | s0: they cast Flashback {3}{G} | I do nothing: us 18 vs 22; Play Forest | s1: they cast Cast Icetill Explorer | I do nothing: us 18 vs 20)
    - `Cast Mossborn Hydra` scored **50** (Cast Mossborn Hydra | s0: they cast Cast Icetill Explorer | I do nothing: us 18 vs 20; Cast Mossborn Hydra | s1: they cast Flashback {3}{G} | I do nothing: us 18 vs 22; Cast Mossborn Hydra | s2: they cast Flashback {3}{G} | I do nothing: us 18 vs 22)
    - `Play Forest` scored **60** (Play Forest | s0: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 20; Play Forest | s1: they cast Cast Icetill Explorer | I do nothing: us 18 vs 20; Play Forest | s2: they cast Flashback {3}{G} | I do nothing: us 18 vs 22)
    - `Cast Llanowar Elves` scored **52** (Cast Llanowar Elves | s0: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 20; Cast Llanowar Elves | s1: they cast Cast Icetill Explorer | I do nothing: us 18 vs 20; Cast Llanowar Elves | s2: they cast Cast Sapling Nursery | I do nothing: us 18 vs 20)
    - `Cast Esper Origins` scored **53** (Cast Esper Origins | s0: they cast Flashback {3}{G} | I do nothing: us 20 vs 22; Cast Esper Origins | s1: they cast Cast Sapling Nursery | I do nothing: us 20 vs 20; Cast Esper Origins | s2: they cast Cast Icetill Explorer | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Playing the land first grows Chocobo to 4/5 via landfall and advances Earthbender Ascension's quest counters at zero opportunity cost, since we still have mana left to cast a spell afterward this same turn."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **20**
- Pilot board: Sazh's Chocobo 4/5, Forest 2/2 | 5 lands (5 untapped)
- Pilot hand: Mossborn Hydra, Forest, Llanowar Elves, Esper Origins
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **46** (pass (hold everything) | s0: they cast Cast Sapling Nursery | I do nothing: us 18 vs 20; pass (hold everything) | s1: they cast Flashback {3}{G} | I do nothing: us 18 vs 22)
    - `Cast Mossborn Hydra` scored **58** (Cast Mossborn Hydra | s0: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 20; Cast Mossborn Hydra | s1: they cast Cast Icetill Explorer | I do nothing: us 18 vs 20)
    - `Cast Llanowar Elves` scored **50** (Cast Llanowar Elves | s0: they cast Cast Icetill Explorer | I do nothing: us 18 vs 20; Cast Llanowar Elves | s1: they cast Flashback {3}{G} | I do nothing: us 18 vs 22; Cast Llanowar Elves | s2: they cast Flashback {3}{G} | I do nothing: us 18 vs 22)
    - `Cast Esper Origins` scored **55** (Cast Esper Origins | s0: they cast Flashback {3}{G} | I do nothing: us 20 vs 22)
- Pilot's reasoning: "Casting Mossborn Hydra develops another growing threat while we still have mana to spare, better than just ramping with Llanowar Elves or passing with an empty board development."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **20**
- Pilot board: Sazh's Chocobo 4/5, Forest 2/2, Mossborn Hydra 1/1 (sick) | 5 lands (2 untapped)
- Pilot hand: Forest, Llanowar Elves, Esper Origins
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **46** (pass (hold everything) | s0: they cast Flashback {3}{G} | I do nothing: us 18 vs 22; pass (hold everything) | s1: they cast Flashback {3}{G} | I do nothing: us 18 vs 22; pass (hold everything) | s2: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 20)
    - `Cast Llanowar Elves` scored **50** (Cast Llanowar Elves | s0: they cast Cast Sapling Nursery | I do nothing: us 18 vs 20; Cast Llanowar Elves | s1: they cast Cast Icetill Explorer | I do nothing: us 18 vs 20; Cast Llanowar Elves | s2: they cast Flashback {3}{G} | I do nothing: us 18 vs 22)
    - `Cast Esper Origins` scored **60** (Cast Esper Origins | s0: they cast Cast Icetill Explorer | I do nothing: us 20 vs 20; Cast Esper Origins | s1: they cast Flashback {3}{G} | I do nothing: us 20 vs 22; Cast Esper Origins | s2: they cast Flashback {3}{G} | I do nothing: us 20 vs 22)
- Pilot's reasoning: "With 5 lands already and a well-developed board, Esper Origins' surveil 2 and life gain is more valuable right now than adding a redundant mana dork; passing wastes available mana."

## Turn 7 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Sazh's Chocobo 4/5, Forest 2/2 (tapped), Mossborn Hydra 1/1 (sick) | 5 lands (1 untapped)
- Pilot hand: Forest, Llanowar Elves
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 20 vs 20)
    - `attack-all` scored **60** (unblocked: us 20 vs 16)
- Pilot's reasoning: "Opponent's Forest and Badgermole Cub are both tapped and can't block, so attacking with Chocobo is free unblocked damage."

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **18**
- Pilot board: Sazh's Chocobo 4/5 (tapped), Forest 2/2 (tapped), Mossborn Hydra 1/1 (sick) | 5 lands (1 untapped)
- Pilot hand: Forest, Llanowar Elves
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped), Summon: Esper Maduin 4/4 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **58** (after combat: us 18 vs 18)
    - `Mossborn Hydra>Badgermole Cub` scored **48** (after combat: us 20 vs 18)
- Pilot's reasoning: "Losing 2 life from an unblocked 2/2 is trivial at 18 life with a dominant board, while trading away Mossborn Hydra (a growing landfall threat) for nothing beneficial (it doesn't even kill the attacker) is a bad trade."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Sazh's Chocobo 4/5, Forest 2/2, Mossborn Hydra 1/1 | 5 lands (5 untapped)
- Pilot hand: Forest, Llanowar Elves, Forest
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped), Summon: Esper Maduin 4/4 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **46** (pass (hold everything) | s0: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 18; pass (hold everything) | s1: they cast Cast Icetill Explorer | I do nothing: us 18 vs 18)
    - `Play Forest` scored **62** (Play Forest | s0: they cast Cast Icetill Explorer | I do nothing: us 18 vs 18; Play Forest | s1: they cast Cast Sapling Nursery | I do nothing: us 18 vs 18; Play Forest | s2: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 18)
    - `Cast Llanowar Elves` scored **46** (Cast Llanowar Elves | s0: they cast Cast Sapling Nursery | I do nothing: us 18 vs 18; Cast Llanowar Elves | s1: they cast Cast Sapling Nursery | I do nothing: us 18 vs 18; Cast Llanowar Elves | s2: they cast Flashback {3}{G} | I do nothing: us 18 vs 20)
    - `Play Forest` scored **62** (Play Forest | s0: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 18; Play Forest | s1: they cast Cast Icetill Explorer | I do nothing: us 18 vs 18; Play Forest | s2: they cast Cast Sapling Nursery | I do nothing: us 18 vs 18)
    - `Flashback {3}{G}` scored **55** (Flashback {3}{G} | s0: they cast Flashback {3}{G} | I do nothing: us 20 vs 20; Flashback {3}{G} | s1: they cast Cast Icetill Explorer | I do nothing: us 20 vs 18)
- Pilot's reasoning: "Playing our land is free value that grows both Chocobo (5/6) and doubles Mossborn Hydra's counters (2/2) via landfall, and we still have mana left to flashback Esper Origins afterward for a 4/4 body - clearly better than passing or spending mana on Llanowar Elves alone."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **18** vs MAD **18**
- Pilot board: Sazh's Chocobo 5/6, Forest 2/2, Mossborn Hydra 2/2 | 6 lands (6 untapped)
- Pilot hand: Llanowar Elves, Forest
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped), Summon: Esper Maduin 4/4 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything) | s0: they cast Cast Sapling Nursery | I do nothing: us 18 vs 18; pass (hold everything) | s1: they cast Flashback {3}{G} | I do nothing: us 18 vs 20; pass (hold everything) | s2: they cast Cast Icetill Explorer | I do nothing: us 18 vs 18)
    - `Cast Llanowar Elves` scored **55** (Cast Llanowar Elves | s0: they cast Cast Sapling Nursery | I do nothing: us 18 vs 18; Cast Llanowar Elves | s1: they cast Cast Mightform Harmonizer | I do nothing: us 18 vs 18)
    - `Flashback {3}{G}` scored **55** (Flashback {3}{G} | s0: they cast Cast Icetill Explorer | I do nothing: us 20 vs 18; Flashback {3}{G} | s1: they cast Cast Icetill Explorer | I do nothing: us 20 vs 18; Flashback {3}{G} | s2: they cast Flashback {3}{G} | I do nothing: us 20 vs 20)
- Pilot's reasoning: "Flashbacking Esper Origins nets a 4/4 body plus surveil 2 and 2 life for 4 mana, clearly the strongest value play with our remaining mana versus just adding a small Llanowar Elves or passing."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **18**
- Pilot board: Sazh's Chocobo 5/6, Forest 2/2, Mossborn Hydra 2/2, Summon: Esper Maduin 4/4 (sick) | 6 lands (2 untapped)
- Pilot hand: Llanowar Elves, Forest, Escape Tunnel
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped), Summon: Esper Maduin 4/4 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **58** (pass (hold everything) | s0: they cast Cast Icetill Explorer | I do nothing: us 20 vs 18; pass (hold everything) | s2: they cast Cast Sapling Nursery | I do nothing: us 20 vs 18)
    - `Cast Llanowar Elves` scored **53** (Cast Llanowar Elves | s0: they cast Flashback {3}{G} | I do nothing: us 20 vs 20; Cast Llanowar Elves | s1: they cast Cast Icetill Explorer | I do nothing: us 20 vs 18; Cast Llanowar Elves | s2: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 18)
- Pilot's reasoning: "Casting Llanowar Elves adds a body/mana source at no real cost since we have no better use for the mana this turn; passing wastes it for no benefit."

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **18**
- Pilot board: Sazh's Chocobo 5/6, Forest 2/2, Mossborn Hydra 2/2, Summon: Esper Maduin 4/4 (sick) | 6 lands (2 untapped)
- Pilot hand: Llanowar Elves, Forest, Escape Tunnel
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped), Summon: Esper Maduin 4/4 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 20 vs 18)
    - `attack-all` scored **75** (1 block(s), response 3: us 20 vs 11; 1 block(s), response 2: us 20 vs 11; unblocked: us 20 vs 9)
    - `hold[Sazh's Chocobo]` scored **63** (1 block(s), response 2: us 20 vs 16; 1 block(s), response 1: us 20 vs 16; unblocked: us 20 vs 14)
    - `hold[Forest]` scored **60** (1 block(s), response 2: us 20 vs 13; unblocked: us 20 vs 11; 1 block(s), response 1: us 20 vs 16)
    - `hold[Mossborn Hydra]` scored **62** (1 block(s), response 2: us 20 vs 13; unblocked: us 20 vs 11; 1 block(s), response 1: us 20 vs 16)
- Pilot's reasoning: "Attacking with everything forces at most one trade (losing Forest or Hydra, both replaceable) while dealing 7-9 damage, putting them to single digits; holding back attackers only reduces our clock for no real safety gain since their only blocker is one creature."

## Turn 9 — Postcombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **11**
- Pilot board: Sazh's Chocobo 5/6 (tapped), Forest 2/2 (tapped), Summon: Esper Maduin 4/4 (sick) | 6 lands (2 untapped)
- Pilot hand: Llanowar Elves, Forest, Escape Tunnel
- MAD board: Forest 1/1 (tapped), Badgermole Cub 2/2 (tapped), Summon: Esper Maduin 4/4 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **68** (pass (hold everything) | s0: they cast Flashback {3}{G} | I do nothing: us 20 vs 13; pass (hold everything) | s1: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 11; pass (hold everything) | s2: they cast Cast Sapling Nursery | I do nothing: us 20 vs 11)
    - `Cast Llanowar Elves` scored **74** (Cast Llanowar Elves | s0: they cast Cast Icetill Explorer | I do nothing: us 20 vs 11; Cast Llanowar Elves | s1: they cast Cast Sapling Nursery | I do nothing: us 20 vs 11)
- Pilot's reasoning: "Opponent is at 11 life with a strong board disadvantage against us; casting Llanowar Elves adds a body for free with our last mana and doesn't change the overwhelming favorable position."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **13**
- Pilot board: Sazh's Chocobo 5/6, Forest 2/2, Summon: Esper Maduin 4/4, Llanowar Elves 1/1 | 6 lands (6 untapped)
- Pilot hand: Forest, Escape Tunnel, Badgermole Cub
- MAD board: Forest 1/1, Badgermole Cub 2/2, Summon: Esper Maduin 4/4, Sazh's Chocobo 2/3 (sick), Summon: Esper Maduin 4/4 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **46** (pass (hold everything) | s0: they cast Cast Sapling Nursery | I do nothing: us 20 vs 13; pass (hold everything) | s1: they cast Flashback {3}{G} | I do nothing: us 20 vs 15; pass (hold everything) | s2: they cast Cast Sapling Nursery | I do nothing: us 20 vs 13)
    - `Play Forest` scored **66** (Play Forest | s0: they cast Cast Icetill Explorer | I do nothing: us 20 vs 13; Play Forest | s1: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 13; Play Forest | s2: they cast Cast Icetill Explorer | I do nothing: us 20 vs 13)
    - `Play Escape Tunnel` scored **68** (Play Escape Tunnel | s0: they cast Cast Mightform Harmonizer | on the stack I cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.: us 20 vs 13; Play Escape Tunnel | s0: they cast Cast Mightform Harmonizer | on the stack I cast {T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn.: us 20 vs 13; Play Escape Tunnel | s0: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 13; Play Escape Tunnel | s1: they cast Cast Icetill Explorer | on the stack I cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.: us 20 vs 13; Play Escape Tunnel | s1: they cast Cast Icetill Explorer | on the stack I cast {T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn.: us 20 vs 13; Play Escape Tunnel | s1: they cast Cast Icetill Explorer | I do nothing: us 20 vs 13)
    - `Cast Badgermole Cub` scored **58** (Cast Badgermole Cub | s0: they cast Cast Sapling Nursery | I do nothing: us 20 vs 13; Cast Badgermole Cub | s2: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 13)
- Pilot's reasoning: "Playing Escape Tunnel triggers landfall now and can be sacrificed later to fetch another basic land for a second landfall trigger, squeezing extra value from one land drop and growing Chocobo further than a plain Forest; Badgermole Cub is fine value but doesn't match the land's compounding upside."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **13**
- Pilot board: Sazh's Chocobo 5/6, Forest 2/2, Summon: Esper Maduin 4/4, Llanowar Elves 1/1 | 7 lands (7 untapped)
- Pilot hand: Forest, Badgermole Cub
- MAD board: Forest 1/1, Badgermole Cub 2/2, Summon: Esper Maduin 4/4, Sazh's Chocobo 2/3 (sick), Summon: Esper Maduin 4/4 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything) | s0: they cast Flashback {3}{G} | on the stack I cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.: us 20 vs 15; pass (hold everything) | s0: they cast Flashback {3}{G} | on the stack I cast {T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn.: us 20 vs 15; pass (hold everything) | s0: they cast Flashback {3}{G} | after it resolves I cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.: us 20 vs 15; pass (hold everything) | s0: they cast Flashback {3}{G} | after it resolves I cast {T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn.: us 20 vs 15; pass (hold everything) | s0: they cast Flashback {3}{G} | I do nothing: us 20 vs 15; pass (hold everything) | s1: they cast Cast Icetill Explorer | on the stack I cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.: us 20 vs 13; pass (hold everything) | s1: they cast Cast Icetill Explorer | on the stack I cast {T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn.: us 20 vs 13; pass (hold everything) | s1: they cast Cast Icetill Explorer | I do nothing: us 20 vs 13; pass (hold everything) | s2: they cast Cast Sapling Nursery | on the stack I cast {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.: us 20 vs 13; pass (hold everything) | s2: they cast Cast Sapling Nursery | on the stack I cast {T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn.: us 20 vs 13; pass (hold everything) | s2: they cast Cast Sapling Nursery | I do nothing: us 20 vs 13)
    - `{T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.` scored **65** ({T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. | s0: they cast Cast Icetill Explorer | I do nothing: us 20 vs 13; {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. | s1: they cast Cast Sapling Nursery | I do nothing: us 20 vs 13; {T}, Sacrifice {this}: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. | s2: they cast Flashback {3}{G} | I do nothing: us 20 vs 15)
    - `{T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn.` scored **50** ({T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn. | s0: they cast Cast Sapling Nursery | I do nothing: us 20 vs 13; {T}, Sacrifice {this}: Target creature with power 2 or less can't be blocked this turn. | s1: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 13)
- Pilot's reasoning: "Sacrificing Escape Tunnel to fetch a basic land triggers landfall a second time this turn, growing Chocobo to 9/10 - clearly the best value since it converts one land drop into two landfall pumps at no real cost."

## Turn 11 — Precombat Main [target]
- Life: pilot **20** vs MAD **13**
- Pilot board: Sazh's Chocobo 5/6, Forest 2/2, Summon: Esper Maduin 4/4, Llanowar Elves 1/1 | 7 lands (6 untapped)
- Pilot hand: Forest, Badgermole Cub
- MAD board: Forest 1/1, Badgermole Cub 2/2, Summon: Esper Maduin 4/4, Sazh's Chocobo 2/3 (sick), Summon: Esper Maduin 4/4 (sick) | 4 lands (0 untapped)
- Menu: [0] Forest 2/2 (A); [1] Summon: Esper Maduin 4/4 (A); [2] Llanowar Elves 1/1 (A); [3] Sazh's Chocobo 5/6 (A)
- **Chose: target Sazh's Chocobo 5/6 (A)**
- Pilot's reasoning: "Giving the +1/+1 counter and trample to Sazh's Chocobo (our biggest attacker) lets it push damage through blockers this turn, maximizing pressure on opponent at 13 life."

## Turn 11 — Precombat Main [target]
- Life: pilot **20** vs MAD **13**
- Pilot board: Sazh's Chocobo 7/8, Forest 2/2, Summon: Esper Maduin 4/4, Llanowar Elves 1/1 | 7 lands (6 untapped)
- Pilot hand: Forest, Badgermole Cub
- MAD board: Forest 1/1, Badgermole Cub 2/2, Summon: Esper Maduin 4/4, Sazh's Chocobo 2/3 (sick), Summon: Esper Maduin 4/4 (sick) | 4 lands (0 untapped)
- Menu: [0] Forest 2/2 (A); [1] Summon: Esper Maduin 4/4 (A); [2] Llanowar Elves 1/1 (A); [3] Sazh's Chocobo 7/8 (A)
- **Chose: target Sazh's Chocobo 7/8 (A)**
- Pilot's reasoning: "Giving trample and another +1/+1 to Sazh's Chocobo again lets it push lethal through blockers - opponent is at 13 and this makes Chocobo massive with trample."

## Turn 11 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **13**
- Pilot board: Sazh's Chocobo 9/10, Forest 2/2, Summon: Esper Maduin 4/4, Llanowar Elves 1/1 | 7 lands (6 untapped)
- Pilot hand: Forest, Badgermole Cub
- MAD board: Forest 1/1, Badgermole Cub 2/2, Summon: Esper Maduin 4/4, Sazh's Chocobo 2/3 (sick), Summon: Esper Maduin 4/4 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything) | s0: they cast Cast Mightform Harmonizer | I do nothing: us 20 vs 13; pass (hold everything) | s1: they cast Flashback {3}{G} | I do nothing: us 20 vs 15; pass (hold everything) | s2: they cast Cast Icetill Explorer | I do nothing: us 20 vs 13)
    - `Cast Badgermole Cub` scored **68** (Cast Badgermole Cub | s0: they cast Cast Sapling Nursery | I do nothing: us 20 vs 13; Cast Badgermole Cub | s1: they cast Flashback {3}{G} | I do nothing: us 20 vs 15)
- Pilot's reasoning: "With trample on a 9/10 Chocobo this turn, opponent's best block still lets excess damage through; casting Badgermole Cub adds more attacking power and doesn't cost us anything meaningful before we swing."

## Turn 11 — Precombat Main [target]
- Life: pilot **20** vs MAD **13**
- Pilot board: Sazh's Chocobo 9/10, Forest 2/2, Summon: Esper Maduin 4/4, Llanowar Elves 1/1, Badgermole Cub 2/2 (sick) | 7 lands (6 untapped)
- Pilot hand: Forest
- MAD board: Forest 1/1, Badgermole Cub 2/2, Summon: Esper Maduin 4/4, Sazh's Chocobo 2/3 (sick), Summon: Esper Maduin 4/4 (sick) | 4 lands (0 untapped)
- Menu: [0] Forest 2/2 (A); [1] Forest (A); [2] Forest (A); [3] Forest (A); [4] Forest (A); [5] Forest (A); [6] Forest (A)
- **Chose: target Forest (A)**
- Pilot's reasoning: "Turning an untapped Forest into a 1/1 haste creature adds one more attacker this turn since haste lets it join the attack immediately."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **13**
- Pilot board: Sazh's Chocobo 9/10, Forest 2/2, Forest 1/1, Summon: Esper Maduin 4/4, Llanowar Elves 1/1, Badgermole Cub 2/2 (sick) | 6 lands (5 untapped)
- Pilot hand: Forest
- MAD board: Forest 1/1, Badgermole Cub 2/2, Summon: Esper Maduin 4/4, Sazh's Chocobo 2/3 (sick), Summon: Esper Maduin 4/4 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **50** (unblocked: us 20 vs 13)
    - `attack-all` scored **100** (unblocked: us 20 vs -4; 1 block(s), response 1: us 20 vs -3; 1 block(s), response 2: us 20 vs -2)
    - `hold[Sazh's Chocobo]` scored **55** (1 block(s), response 11: us 20 vs 9; 1 block(s), response 9: us 20 vs 7)
    - `hold[Forest]` scored **60** (1 block(s), response 11: us 20 vs 2; 1 block(s), response 3: us 20 vs 2; 1 block(s), response 7: us 20 vs 2)
    - `hold[Forest]` scored **58** (1 block(s), response 11: us 20 vs 1; 1 block(s), response 3: us 20 vs 1; 1 block(s), response 7: us 20 vs 1)
    - `hold[Summon: Esper Maduin]` scored **58** (1 block(s), response 10: us 20 vs 2; 1 block(s), response 8: us 20 vs 1)
    - `hold[Llanowar Elves]` scored **58** (1 block(s), response 12: us 20 vs 1; 1 block(s), response 4: us 20 vs 1; 1 block(s), response 8: us 20 vs 1)
- Pilot's reasoning: "Attacking with everything is lethal this turn in every sampled scenario - even their best chump blocks can't stop trample damage from a 9/10 Chocobo plus the rest of our board from taking them well below 0."

## Turn 11 — Combat Damage [target]
- Life: pilot **20** vs MAD **5**
- Pilot board: Sazh's Chocobo 9/10 (tapped), Summon: Esper Maduin 4/4 (tapped), Badgermole Cub 2/2 (sick) | 7 lands (5 untapped)
- Pilot hand: Forest
- MAD board: Summon: Esper Maduin 4/4, Sazh's Chocobo 3/4 (sick), Summon: Esper Maduin 4/4 (sick) | 5 lands (0 untapped)
- Menu: [0] Badgermole Cub 2/2 (A); [1] Summon: Esper Maduin 4/4 (A); [2] Sazh's Chocobo 9/10 (A)
- **Chose: target Badgermole Cub 2/2 (A)**
- Pilot's reasoning: "Chocobo already dealt its damage this combat, so putting the permanent +1/+1 counter on Badgermole Cub (which is untapped and can block) gives us more lasting value."

## Turn 11 — Combat Damage [target]
- Life: pilot **20** vs MAD **5**
- Pilot board: Sazh's Chocobo 10/11 (tapped), Summon: Esper Maduin 4/4 (tapped), Badgermole Cub 3/3 (sick) | 8 lands (5 untapped)
- Pilot hand: Forest
- MAD board: Summon: Esper Maduin 4/4, Sazh's Chocobo 3/4 (sick), Summon: Esper Maduin 4/4 (sick) | 5 lands (0 untapped)
- Menu: [0] Badgermole Cub 3/3 (A); [1] Summon: Esper Maduin 4/4 (A); [2] Sazh's Chocobo 10/11 (A)
- **Chose: target Sazh's Chocobo 10/11 (A)**
- Pilot's reasoning: "Chocobo is our biggest threat and already has trample from the earlier grant; stacking another +1/+1 counter on it maximizes future damage output regardless of blocks."

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **9**
- Pilot board: Sazh's Chocobo 12/13 (tapped), Summon: Esper Maduin 4/4 (tapped), Badgermole Cub 3/3 (sick) | 8 lands (5 untapped)
- Pilot hand: Forest
- MAD board: Sazh's Chocobo 6/7 (tapped), Summon: Esper Maduin 6/6 (tapped), Summon: Esper Maduin 4/4 (sick), Summon: Esper Maduin 4/4 (sick) | 6 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **85** (after combat: us 8 vs 9)
    - `Badgermole Cub>Sazh's Chocobo` scored **82** (after combat: us 11 vs 9)
    - `Badgermole Cub>Summon: Esper Maduin` scored **None** ()
- Pilot's reasoning: "Both lines leave us safely ahead (8 or 11 life) with our board still dominant (Chocobo 12/13, Esper Maduin 4/4) and opponent at 9; no-blocks keeps Badgermole Cub alive as a future attacker and mana accelerant, which outweighs the 3 extra life from chump-blocking their trampling Chocobo since we're i"

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **8** vs MAD **9**
- Pilot board: Sazh's Chocobo 14/15, Badgermole Cub 5/5 | 8 lands (8 untapped)
- Pilot hand: Forest, Esper Origins
- MAD board: Sazh's Chocobo 4/5 (tapped), Summon: Esper Maduin 4/4 (tapped), Summon: Esper Maduin 4/4 (sick), Summon: Esper Maduin 4/4 (sick) | 6 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **86** (pass (hold everything) | s0: they cast Cast Sapling Nursery | I do nothing: us 8 vs 9; pass (hold everything) | s2: they cast Cast Icetill Explorer | I do nothing: us 8 vs 9)
    - `Play Forest` scored **87** (Play Forest | s0: they cast Cast Sapling Nursery | I do nothing: us 8 vs 9; Play Forest | s2: they cast Cast Icetill Explorer | I do nothing: us 8 vs 9)
    - `Cast Esper Origins` scored **90** (Cast Esper Origins | s0: they cast Cast Sapling Nursery | I do nothing: us 10 vs 9; Cast Esper Origins | s1: they cast Cast Sapling Nursery | I do nothing: us 10 vs 9)
    - `Flashback {3}{G}` scored **91** (Flashback {3}{G} | s0: they cast Cast Sapling Nursery | I do nothing: us 10 vs 9; Flashback {3}{G} | s1: they cast Cast Mightform Harmonizer | I do nothing: us 10 vs 9; Flashback {3}{G} | s2: they cast Cast Icetill Explorer | I do nothing: us 10 vs 9)
- Pilot's reasoning: "Chocobo (14/15 trample) alone already exceeds their 9 life even fully blocked, so the upcoming attack should be lethal in every line; flashbacking Esper Origins is best since it adds an extra 4/4 body plus 2 life and surveil for free (doesn't cost us any attackers) as insurance against a fog/removal"

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **10** vs MAD **9**
- Pilot board: Sazh's Chocobo 14/15, Badgermole Cub 5/5, Summon: Esper Maduin 4/4 (sick) | 8 lands (4 untapped)
- Pilot hand: Forest, Esper Origins, Forest
- MAD board: Sazh's Chocobo 4/5 (tapped), Summon: Esper Maduin 4/4 (tapped), Summon: Esper Maduin 4/4 (sick), Summon: Esper Maduin 4/4 (sick) | 6 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **90** (pass (hold everything) | s0: they cast Cast Icetill Explorer | I do nothing: us 10 vs 9; pass (hold everything) | s1: they cast Cast Sapling Nursery | I do nothing: us 10 vs 9)
    - `Play Forest` scored **90** (Play Forest | s0: they cast Cast Sapling Nursery | I do nothing: us 10 vs 9; Play Forest | s1: they cast Cast Icetill Explorer | I do nothing: us 10 vs 9)
    - `Cast Esper Origins` scored **91** (Cast Esper Origins | s0: they cast Cast Sapling Nursery | I do nothing: us 12 vs 9; Cast Esper Origins | s1: they cast Cast Sapling Nursery | I do nothing: us 12 vs 9; Cast Esper Origins | s2: they cast Cast Icetill Explorer | I do nothing: us 12 vs 9)
    - `Play Forest` scored **90** (Play Forest | s0: they cast Cast Sapling Nursery | I do nothing: us 10 vs 9; Play Forest | s1: they cast Cast Sapling Nursery | I do nothing: us 10 vs 9; Play Forest | s2: they cast Cast Icetill Explorer | I do nothing: us 10 vs 9)
- Pilot's reasoning: "All lines still lead into the same overwhelming lethal attack (Chocobo 14-16/x trample + Badgermole Cub 5/5 trample vastly exceeds their 9 life even fully blocked); casting Esper Origins from hand for the extra 2 life and surveil is marginally best as free resilience against a trick, with playing th"

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **10** vs MAD **9**
- Pilot board: Sazh's Chocobo 14/15, Badgermole Cub 5/5, Summon: Esper Maduin 4/4 (sick) | 8 lands (4 untapped)
- Pilot hand: Forest, Esper Origins, Forest
- MAD board: Sazh's Chocobo 4/5 (tapped), Summon: Esper Maduin 4/4 (tapped), Summon: Esper Maduin 4/4 (sick), Summon: Esper Maduin 4/4 (sick) | 6 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **35** (unblocked: us 10 vs 9)
    - `attack-all` scored **100** (unblocked: us 10 vs -10; 1 block(s), response 1: us 10 vs -6)
    - `hold[Sazh's Chocobo]` scored **50** (unblocked: us 10 vs 4; 1 block(s), response 1: us 10 vs 8)
    - `hold[Badgermole Cub]` scored **100** (unblocked: us 10 vs -5; 1 block(s), response 1: us 10 vs -1)
- Pilot's reasoning: "Opponent has zero untapped mana available (already tapped out from earlier plays), eliminating trick risk this combat; attacking with both Chocobo (14/15 trample) and Badgermole Cub (5/5 trample) is lethal even in the worst modeled block (opp to -6), while holding back either attacker still achieves"
