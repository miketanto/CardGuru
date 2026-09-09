# Decision review — g5.jsonl

Result: **pilot lost** in 18 turns. 82 real decisions out of 255 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Undercity Sewers, Kaito, Bane of Nightmares, Cut Down, Sheoldred, the Apocalypse, Deep-Cavern Bat, Faerie Mastermind, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: MULLIGAN**
- Pilot's reasoning: "Only 1 land (Undercity Sewers) in a 7-card hand full of great spells (Kaito, Sheoldred, Cut Down, Bat, Mastermind, Drowner) is unkeepable — even a 2-lander would be risky, but 1 land is a near-certain non-functional hand."

## Turn 1 — null [target]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Menu: [0] Floodpits Drowner; [1] Go for the Throat; [2] Island; [3] Swamp; [4] Island; [5] Restless Reef; [6] Deep-Cavern Bat
- **Chose: target Island**
- Pilot's reasoning: "Keep 3 lands (Island, Restless Reef, Swamp) covering both colors plus Go for the Throat, Deep-Cavern Bat, Floodpits Drowner — a great curve-out hand. Bottoming the extra duplicate Island since I already have a blue source and don't need a 4th land."

## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "3 lands covering both colors (Island, Restless Reef, Swamp) plus Go for the Throat, Deep-Cavern Bat, Floodpits Drowner is a clean, castable 6-card hand with removal and disruption on curve. Keeping."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Island, Restless Reef, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **55** (Play Island: us 20 vs 20)
    - `Play Restless Reef` scored **70** (Play Restless Reef: us 20 vs 20)
    - `Play Swamp` scored **55** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Turn 1 with no play to make, best sequencing is to play the tapped land (Restless Reef) now since it costs nothing this turn, preserving Island/Swamp for turns I need untapped mana to curve into Bat/Drowner on 2."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **80** (Play Island: us 20 vs 20)
    - `Play Swamp` scored **80** (Play Swamp: us 20 vs 20)
- Pilot's reasoning: "Playing a second land is clearly correct — Restless Reef can flex to either color, so either Island or Swamp gives me 2 mana this turn to cast a 2-drop (Bat or Drowner) on curve. Passing wastes a land drop for no reason."

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 2 lands (2 untapped)
- Pilot hand: Swamp, Go for the Throat, Deep-Cavern Bat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **35** (pass (hold everything): us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **82** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **55** (Cast Floodpits Drowner: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **82** (Cast Deep-Cavern Bat: us 20 vs 20)
- Pilot's reasoning: "Casting Deep-Cavern Bat now gets me info on their hand, lets me exile their best nonland card, and starts an evasive lifelink clock — great proactive play with no opposing creatures to punish it. Floodpits Drowner's ETB has no legal target yet since they have no creatures, and it has flash so it's b"

## Turn 3 — Precombat Main [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (sick) | 2 lands (0 untapped)
- Pilot hand: Swamp, Go for the Throat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: no creatures | 1 lands (1 untapped)
- Menu: [0] Floodpits Drowner; [1] Floodpits Drowner; [2] Kaito, Bane of Nightmares; [3] Kaito, Bane of Nightmares; [4] Deep-Cavern Bat
- **Chose: target Kaito, Bane of Nightmares**
- Pilot's reasoning: "Kaito, Bane of Nightmares is by far their strongest card — hexproof 3/4 body on their turn, repeatable tap+stun removal, and a growing emblem — far more dangerous than the Drowners or their own Bat. Exiling it denies their best play."

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Swamp, Go for the Throat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Their Floodpits Drowner is a 2/1 that trades naturally with my Bat in combat (1 dmg kills its 1 toughness) — not worth spending Go for the Throat on, especially since Kaito can never be a legal target for it (not a creature on my turn, hexproof on theirs), so I need to save removal for Sheoldred/Pre"

## Turn 5 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Swamp, Go for the Throat, Floodpits Drowner, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **30** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
- Pilot's reasoning: "Still my draw step, nothing changed since upkeep — no reason to spend Go for the Throat on a 2/1 that trades with my Bat in combat, and Floodpits Drowner is better held with flash for later value or defense. Pass and act from main phase instead."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 2 lands (2 untapped)
- Pilot hand: Swamp, Go for the Throat, Floodpits Drowner, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 20 vs 20)
    - `Play Swamp` scored **88** (Play Swamp: us 20 vs 20)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **40** (Cast Floodpits Drowner: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **45** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **45** (Cast Deep-Cavern Bat: us 20 vs 20)
- Pilot's reasoning: "Playing the land is a free, strictly-good action (no downside, enables more plays) — the other candidates each skip the land drop for this turn, which is worse than just playing the land first. After playing Swamp I'll have 3 mana next priority to develop with Bat/Drowner as appropriate."

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 3 lands (3 untapped)
- Pilot hand: Go for the Throat, Floodpits Drowner, Deep-Cavern Bat, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 20 vs 20)
    - `Cast Go for the Throat` scored **25** (Cast Go for the Throat: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **45** (Cast Floodpits Drowner: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **82** (Cast Deep-Cavern Bat: us 20 vs 20)
    - `Cast Deep-Cavern Bat` scored **82** (Cast Deep-Cavern Bat: us 20 vs 20)
- Pilot's reasoning: "Casting the second Deep-Cavern Bat keeps developing my board with an evasive lifelink threat while giving me more info and another chance to exile a card from their hand — strong proactive value with no risk since they have no attackers. Go for the Throat is still not worth spending on their 2/1, an"

## Turn 5 — Precombat Main [choose]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Go for the Throat, Floodpits Drowner, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1 (sick) | 2 lands (0 untapped)
- Menu: [0] Floodpits Drowner; [1] Kaito, Bane of Nightmares; [2] Deep-Cavern Bat; [3] Go for the Throat
- **Chose: target Kaito, Bane of Nightmares**
- Pilot's reasoning: "Kaito remains their most powerful and otherwise-unanswerable threat (untargetable by my removal in every window) — exile it again to keep it off the board entirely."

## Turn 6 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Floodpits Drowner, Deep-Cavern Bat
- MAD board: Floodpits Drowner 2/1, Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **45** (after combat: us 18 vs 20)
    - `Deep-Cavern Bat>Floodpits Drowner` scored **82** (after combat: us 21 vs 20)
- Pilot's reasoning: "Blocking trades my Bat (already delivered its ETB value) for their Floodpits Drowner, netting a 3-life swing (21 vs 18) and removing their only ground blocker plus its bounce-shuffle utility, while I still keep my other Bat and Bat/Drowner in hand to redevelop. Taking the hit unblocked preserves a b"

## Turn 7 — Upkeep [leaf_eval/priority]
- Life: pilot **21** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1 | 3 lands (3 untapped)
- Pilot hand: Floodpits Drowner, Deep-Cavern Bat
- MAD board: Deep-Cavern Bat 1/1 (sick) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 21 vs 20)
    - `Cast Floodpits Drowner` scored **90** (Cast Floodpits Drowner: us 21 vs 20)
- Pilot's reasoning: "Casting Floodpits Drowner now taps and stuns their only creature (their Deep-Cavern Bat, otherwise able to block) before combat, clearing the way for my Bat to attack unblocked with lifelink. Waiting until after combat would let their Bat block instead."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Deep-Cavern Bat, Swamp
- MAD board: Deep-Cavern Bat 1/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything): us 21 vs 20)
    - `Play Swamp` scored **85** (Play Swamp: us 21 vs 20)
- Pilot's reasoning: "Playing the land is free and strictly better — it gives me mana to cast the Deep-Cavern Bat in hand this turn or hold up more instant-speed options, with zero downside versus passing."

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (sick) | 4 lands (2 untapped)
- Pilot hand: Deep-Cavern Bat
- MAD board: Deep-Cavern Bat 1/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 21 vs 20)
    - `Cast Deep-Cavern Bat` scored **82** (Cast Deep-Cavern Bat: us 21 vs 20)
- Pilot's reasoning: "Casting my last Deep-Cavern Bat continues building an evasive lifelink board and nets another look at their hand with a possible exile — good proactive value with their only creature tapped down and no way to punish me."

## Turn 7 — Precombat Main [choose]
- Life: pilot **21** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (sick), Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped) | 3 lands (1 untapped)
- Menu: [0] Floodpits Drowner; [1] Kaito, Bane of Nightmares; [2] Go for the Throat
- **Chose: target Kaito, Bane of Nightmares**
- Pilot's reasoning: "Kaito remains their scariest card and it's untargetable by my removal in every window — keep exiling it to deny them the play entirely."

## Turn 7 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **21** vs MAD **20**
- Pilot board: Deep-Cavern Bat 1/1, Floodpits Drowner 2/1 (sick), Deep-Cavern Bat 1/1 (sick) | 4 lands (0 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped) | 3 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **30** (unblocked: us 21 vs 20)
    - `attack-all` scored **88** (unblocked: us 22 vs 19)
- Pilot's reasoning: "Their only creature is tapped and can't block, so attacking with the untapped Bat is a free unblocked hit with lifelink — gains me a life swing (22 vs 20) with zero risk since I still have Floodpits Drowner and the other Bat back to block their crackback."

## Turn 9 — Upkeep [leaf_eval/priority]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 (tapped) | 4 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 22 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 22 vs 19)
- Pilot's reasoning: "Animating Restless Reef now would tap it (my 4th land) to pay its own cost, so it can't attack this turn and it reverts to a plain land by cleanup — before my opponent's turn — so it also can't serve as a surprise blocker then. Activating it does nothing this window; better to hold the mana untapped"

## Turn 9 — Draw [leaf_eval/priority]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 (tapped) | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 22 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 22 vs 19)
- Pilot's reasoning: "I drew Preacher of the Schism — a strong 2/4 deathtouch creature I want to cast in my main phase. Animating the Reef now still taps it for no attack/block value this turn, and doing so would leave me unable to cast Preacher. Pass to main phase."

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 (tapped) | 4 lands (4 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 22 vs 19)
    - `Cast Preacher of the Schism` scored **85** (Cast Preacher of the Schism: us 22 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 22 vs 19)
- Pilot's reasoning: "Casting Preacher of the Schism develops a strong 2/4 deathtouch body that draws me cards on attack (I have the most life) and generates lifelink tokens — clearly the best use of mana this turn. Animating the Reef instead wastes all my mana on a tapped creature with no attack/block value and forgoes "

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **30** (unblocked: us 22 vs 19)
    - `attack-all` scored **88** (unblocked: us 23 vs 18)
- Pilot's reasoning: "Their only untapped creature (Floodpits Drowner) can't block flying, so my untapped Bat gets through for free lifelink damage, pushing the life gap wider (23 vs 18) with no risk since Preacher and my other Bat stay back."

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **23** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1, Enduring Curiosity 4/3 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **70** (after combat: us 22 vs 19)
- Pilot's reasoning: "No attackers were declared this turn, so there's nothing to block — safe turn for me with Preacher of the Schism and my Bat back as blockers regardless."

## Turn 11 — Upkeep [leaf_eval/priority]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 22 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 22 vs 19)
- Pilot's reasoning: "Still before my draw step with an empty hand — no reason to commit all my mana to a tapped, non-attacking Reef animation now. I want to see my draw first, and this turn I'll attack with both untapped Bats and now-unsick Preacher for good value (card draw trigger since I have the most life) without n"

## Turn 11 — Draw [leaf_eval/priority]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Cut Down
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything): us 22 vs 19)
    - `Cast Cut Down` scored **82** (Cast Cut Down: us 22 vs 19)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 22 vs 19)
- Pilot's reasoning: "Cut Down can't hit Enduring Curiosity (7 total P/T, too big) but easily kills Floodpits Drowner (3 total). Removing it pre-combat takes away their cheap chump-block option against my attacking Preacher, forcing them to either eat more damage or sacrifice Enduring Curiosity's creature-type to trade w"

## Turn 11 — Draw [target]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Floodpits Drowner 2/1, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Menu: [0] Floodpits Drowner 2/1 (B); [1] Deep-Cavern Bat 1/1 (B); [2] Deep-Cavern Bat 1/1 (A); [3] Deep-Cavern Bat 1/1 (A)
- **Chose: target Floodpits Drowner 2/1 (B)**
- Pilot's reasoning: "Kill Floodpits Drowner to remove their untapped blocker/attacker and strip their cheap chump-block option against my attacking Preacher."

## Turn 11 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **22** vs MAD **19**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (3 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **30** (unblocked: us 22 vs 19)
    - `attack-all` scored **55** (1 block(s), response 1: us 24 vs 17; unblocked: us 24 vs 15)
    - `hold[Deep-Cavern Bat]` scored **55** (1 block(s), response 1: us 23 vs 18; unblocked: us 23 vs 16)
    - `hold[Deep-Cavern Bat]` scored **None** (1 block(s), response 1: us 23 vs 18; unblocked: us 23 vs 16)
    - `hold[Preacher of the Schism]` scored **None** (unblocked: us 24 vs 17)
- Pilot's reasoning: "Attacking with everything guarantees Preacher's attack trigger (draw a card, lose 1 life) regardless of blocks, and even in the worst case where Enduring Curiosity blocks and kills Preacher, my life/opponent-life totals match the safe 'hold Preacher' line exactly — but I additionally get a free card"

## Turn 12 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **24** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 4 lands (3 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **75** (after combat: us 19 vs 18)
    - `Preacher of the Schism>Enduring Curiosity` scored **40** (after combat: us 23 vs 18)
- Pilot's reasoning: "I'm far ahead on life (24 vs 17) and can easily absorb Enduring Curiosity's hit without blocking. Trading Preacher to kill Curiosity's creature-type only saves 4 life I don't need, while keeping Preacher preserves a repeatable card-draw engine (its attack trigger) and a deathtouch blocker for future"

## Turn 13 — Upkeep [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 19 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **25** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 18)
- Pilot's reasoning: "Still upkeep with no hand — animating the Reef now wastes all mana on a tapped, non-attacking body. Pass to draw and see what I get before committing mana."

## Turn 13 — Draw [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Darkslick Shores
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 19 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **25** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 18)
- Pilot's reasoning: "Drew a land, no spell to cast. Still no reason to animate the Reef now with no attack/block value. Pass to main phase to play the land."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 4 lands (4 untapped)
- Pilot hand: Darkslick Shores
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 19 vs 18)
    - `Play Darkslick Shores` scored **82** (Play Darkslick Shores: us 19 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 18)
- Pilot's reasoning: "Playing the land is free and gives more mana available for future turns with no downside — clearly better than passing. Animating the Reef still wastes all mana for no attack value."

## Turn 13 — Precombat Main [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 19 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 18)
- Pilot's reasoning: "Land already played this turn and hand is empty — nothing else to develop. Animating the Reef still wastes mana on a tapped, non-attacking body; pass to combat."

## Turn 13 — Begin Combat [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 19 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 18)
- Pilot's reasoning: "Same reasoning — nothing to cast, animating the Reef wastes mana with no attack value this turn. Pass to declare attackers."

## Turn 13 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **30** (unblocked: us 19 vs 18)
    - `attack-all` scored **55** (1 block(s), response 4: us 21 vs 16; 1 block(s), response 1: us 21 vs 15; 1 block(s), response 2: us 21 vs 15)
    - `hold[Deep-Cavern Bat]` scored **68** (1 block(s), response 3: us 20 vs 17; unblocked: us 20 vs 15; 1 block(s), response 1: us 20 vs 16)
    - `hold[Deep-Cavern Bat]` scored **None** (1 block(s), response 3: us 20 vs 17; unblocked: us 20 vs 15; 1 block(s), response 1: us 20 vs 16)
    - `hold[Preacher of the Schism]` scored **None** (unblocked: us 21 vs 16; 1 block(s), response 1: us 21 vs 17; 1 block(s), response 2: us 21 vs 17)
- Pilot's reasoning: "Attacking with everything forces a worst case where both Preachers trade via mutual deathtouch (a fair, symmetric trade that also removes their ongoing threat) while still pushing opponent life down to 15-16 versus 17 if I hold Preacher back — and I'm already far ahead on life either way. Holding Pr"

## Turn 13 — Declare Attackers [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 19 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 18)
- Pilot's reasoning: "Attackers already declared; nothing left to spend mana on before blocks. Animating the Reef still gives no value."

## Turn 13 — Declare Blockers [leaf_eval/priority]
- Life: pilot **19** vs MAD **18**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 19 vs 18)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 19 vs 18)
- Pilot's reasoning: "Nothing to do at this priority window — Bats are already attacking, Preacher held back. No reason to animate the Reef now."

## Turn 13 — Combat Damage [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Combat resolved well, both Bats connected unblocked (21 vs 16 life). Nothing to spend mana on now."

## Turn 13 — End Combat [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "End of combat, nothing to do — same reasoning as before."

## Turn 13 — Postcombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Postcombat main with empty hand — nothing to develop. Animating the Reef still has no value now that combat is over and it would revert before their attack anyway."

## Turn 13 — End Turn [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (sick), Preacher of the Schism 2/4 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "End of my turn, nothing to spend mana on now — animating the Reef here would immediately fizzle since it reverts before their combat."

## Turn 14 — Upkeep [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Animating the Reef still taps it (I only have 4 untapped lands, exactly the ability's cost) so it can't block — no value here. Pass and use Preacher as my one real blocker if they swing."

## Turn 14 — Draw [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4 | 5 lands (5 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Still no benefit to tapping out for a Reef that would end up tapped and unable to block. Hold up mana and let Preacher handle blocking."

## Turn 14 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4 | 5 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "They deployed another Deep-Cavern Bat; still nothing for me to do and no value from animating the Reef. Hold mana and Preacher as my blocker."

## Turn 14 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped), Preacher of the Schism 2/4 | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Same reasoning — nothing to respond to, my hand is empty so their Bat's ETB has nothing to exile. Hold mana and Preacher as blocker."

## Turn 14 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "They killed my Preacher with Go for the Throat, so I have zero blockers this turn (both Bats tapped) — animating the Reef would still tap out and can't block anyway. I'm at 21 life with a big cushion even if they swing with everything (~9 damage puts me at 12, still ahead of their 16), so nothing ur"

## Turn 14 — Precombat Main [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Same board state as before — no blockers available, Reef animation still useless. I have a solid life cushion (21 vs 16) to absorb an attack."

## Turn 14 — Begin Combat [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Same board state, no blockers available, Reef trick still useless. Comfortable life cushion to absorb an attack."

## Turn 14 — Declare Attackers [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "They've committed to an all-out attack (Bat, Enduring Curiosity, Faerie Mastermind, Preacher all tapped attacking); I have no blockers this turn regardless. Reef animation still provides nothing useful."

## Turn 14 — Declare Attackers [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Attackers fully declared, Vampire token created — no blockers available for me regardless. Reef animation gives nothing here."

## Turn 14 — Declare Blockers [leaf_eval/priority]
- Life: pilot **21** vs MAD **16**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 21 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 21 vs 16)
- Pilot's reasoning: "Declare blockers, no blockers available for me, nothing changes from prior analysis."

## Turn 14 — Combat Damage [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Took 9 damage (21→12); they're now ahead 17-12. Still nothing to respond to here — need to rebuild on my turn with removal/blockers from hand."

## Turn 14 — Combat Damage [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Same combat aftermath, nothing to respond to."

## Turn 14 — Combat Damage [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Same aftermath, nothing to respond to."

## Turn 14 — Combat Damage [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Same aftermath, nothing to respond to."

## Turn 14 — Combat Damage [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Their Enduring Curiosity drew them a card per attacker (now 5 cards in hand) — dangerous going forward, but nothing to respond to right now."

## Turn 14 — End Combat [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 5 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "End of combat, nothing to respond to."

## Turn 14 — Postcombat Main [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Postcombat main on their turn, empty hand, nothing to respond to."

## Turn 14 — End Turn [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 5 lands (4 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "End of their turn, nothing to respond to."

## Turn 15 — Upkeep [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 | 5 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **25** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "My turn's upkeep with empty hand — still no reason to tap out for the Reef, which would waste all mana with no attack value this early. Wait to see my draw."

## Turn 15 — Draw [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 | 5 lands (5 untapped)
- Pilot hand: Undercity Sewers
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **25** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Drew a land, nothing to cast. Still no value from animating the Reef this early. Pass to main phase to play the land."

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 | 5 lands (5 untapped)
- Pilot hand: Undercity Sewers
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **40** (pass (hold everything): us 12 vs 17)
    - `Play Undercity Sewers` scored **82** (Play Undercity Sewers: us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **18** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Playing Undercity Sewers is free, gives a surveil trigger to dig for removal/action, and adds mana for next turn — no downside since I have nothing else to cast. Animating the Reef still tapped-out for no attack value."

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Land played, surveil resolved, hand empty — nothing left to cast. Move to combat."

## Turn 15 — Precombat Main [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Nothing to cast, moving toward combat decision."

## Turn 15 — Begin Combat [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Still nothing to cast before declaring attackers."

## Turn 15 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1, Deep-Cavern Bat 1/1 | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **72** (unblocked: us 12 vs 17)
    - `attack-all` scored **30** (1 block(s), response 1: us 14 vs 17; 1 block(s), response 2: us 14 vs 17; unblocked: us 14 vs 15)
    - `hold[Deep-Cavern Bat]` scored **None** (1 block(s), response 1: us 13 vs 18; unblocked: us 13 vs 16)
    - `hold[Deep-Cavern Bat]` scored **None** (1 block(s), response 1: us 13 vs 18; unblocked: us 13 vs 16)
- Pilot's reasoning: "Attacking taps out both Bats, leaving zero blockers against their much bigger board (4/3, 2/1, 2/4, plus two 1/1s) next turn — repeating this turn's 9-damage alpha strike could put me in lethal range from 12 life. Holding both Bats back as blockers (able to eat their Bat and Vampire token, or chump "

## Turn 15 — Declare Attackers [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Attack already resolved (my Bats are tapped), nothing to spend mana on now."

## Turn 15 — Declare Blockers [leaf_eval/priority]
- Life: pilot **12** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped), Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Deep-Cavern Bat 1/1 (sick), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 12 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 12 vs 17)
- Pilot's reasoning: "Nothing to respond to during declare blockers."

## Turn 15 — Combat Damage [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **20** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "Combat resolved — traded one Bat for their Bat, other connected for lifelink (14 life now). Nothing to respond to."

## Turn 15 — End Combat [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **76** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **18** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "Combat has resolved and there's nothing on the stack to respond to. Passing keeps my 6 lands untapped for instant-speed interaction on their turn. Activating Restless Reef would tap it (one of only 6 sources) for a 4/4 deathtouch body that has no attack or block to make right now since combat is ove"

## Turn 15 — Postcombat Main [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **15** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "Nothing to respond to postcombat with an empty hand — no spell to hold up, just land drops made already. Passing keeps 5 lands untapped for instant-speed interaction (though I have no cards, keeping mana up costs nothing and there's no reason to tap out). Animating Restless Reef here taps out all my"

## Turn 15 — End Turn [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (sick) | 6 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **12** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "End of turn with an empty hand — nothing to cast or respond to. Passing costs nothing and simply moves to opponent's turn. Animating the Reef here would tap all my mana for a body that immediately expires at end of turn before it could ever block on their turn — pure waste."

## Turn 16 — Upkeep [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Vampire Token 1/1 | 6 lands (6 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **52** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "Reef's animation cost ({2}{U}{B}) doesn't require tapping the Reef itself — with 5 untapped lands I can pay with Island/Swamp/Swamp/Darkslick Shores and leave the Reef untapped as a 4/4 deathtouch blocker, unlike every prior turn where it was one of only 4 sources. That's genuinely valuable now sinc"

## Turn 16 — Draw [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Vampire Token 1/1 | 6 lands (6 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **52** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "Still their draw step, before their main phase and combat. Same logic as last window: activating the Reef doesn't require tapping the Reef itself (I can pay {2}{U}{B} with Island/Swamp/Swamp/Darkslick Shores), so waiting costs nothing and preserves information — I'd rather see what they cast in main"

## Turn 16 — Precombat Main [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Vampire Token 1/1 | 6 lands (3 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **78** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **50** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "They just cast a second Preacher of the Schism, growing their board to 6 creatures but that doesn't change my calculus — I still want to see their actual attack before committing mana to animate the Reef. My 5 untapped lands (Reef, Island, Swamp, Swamp, Darkslick Shores) are unaffected by their spen"

## Turn 16 — Precombat Main [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4 (sick) | 7 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **48** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "They've now tapped out completely (0 untapped lands) after casting Sheoldred, the Apocalypse plus their second Preacher — both summoning sick, so at most 5 attackers (Bat, Curiosity, Faerie Mastermind, first Preacher, Vampire Token) are possible this turn. Since they're fully tapped, there's zero ri"

## Turn 16 — Precombat Main [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4 (sick), Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **48** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "Still their precombat main, still fully tapped out (0 untapped lands) — no risk in waiting further. Sheoldred is also deathtouch and summoning sick, so it can't attack this turn but will drain me 2 life every time I draw starting next turn, adding new pressure to think about for future turns. For no"

## Turn 16 — Begin Combat [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1, Enduring Curiosity 4/3, Faerie Mastermind 2/1, Preacher of the Schism 2/4, Vampire Token 1/1, Preacher of the Schism 2/4 (sick), Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **80** (pass (hold everything): us 14 vs 17)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **48** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 17)
- Pilot's reasoning: "Beginning of Combat, still before attackers are declared and they remain tapped out. No new information yet — still want to see the actual attack before committing the Reef's mana."

## Turn 16 — Declare Attackers [leaf_eval/priority]
- Life: pilot **14** vs MAD **17**
- Pilot board: Deep-Cavern Bat 1/1 (tapped) | 6 lands (5 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Preacher of the Schism 2/4 (sick), Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **15** (pass (hold everything): us 14 vs 16)
    - `{2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.` scored **92** ({2}{U}{B}: Until end of turn, {this} becomes a 4/4 blue and black Shark creature with deathtouch. It's still a land.: us 14 vs 16)
- Pilot's reasoning: "Attackers are now declared: Bat, Curiosity, Faerie Mastermind, Preacher, and the Vampire Token are all attacking (5 attackers, up to 10 damage if unblocked, which would put me from 14 to 4 life — dangerous with Sheoldred coming online next turn). I have zero other untapped blockers (Bat is tapped), "

## Turn 16 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **14** vs MAD **18**
- Pilot board: Restless Reef 4/4, Deep-Cavern Bat 1/1 (tapped) | 5 lands (0 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Enduring Curiosity 4/3 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Preacher of the Schism 2/4 (sick), Sheoldred, the Apocalypse 4/5 (sick) | 7 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **8** (after combat: us 4 vs 20)
    - `Restless Reef>Enduring Curiosity` scored **90** (after combat: us 8 vs 20)
    - `Restless Reef>Preacher of the Schism` scored **42** (after combat: us 6 vs 20)
    - `Restless Reef>Vampire Token` scored **30** (after combat: us 5 vs 20)
- Pilot's reasoning: "Blocking Enduring Curiosity with the animated Restless Reef prevents the most damage (4, since Curiosity has the highest power) and leaves me at 8 life instead of 4-6, which matters enormously now that Sheoldred is about to start draining me 2 life per draw next turn. It also permanently strips Curi"

## Turn 17 — Precombat Main [leaf_eval/priority]
- Life: pilot **6** vs MAD **28**
- Pilot board: Deep-Cavern Bat 1/1 | 5 lands (5 untapped)
- Pilot hand: Preacher of the Schism
- MAD board: Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Preacher of the Schism 2/4 (sick), Sheoldred, the Apocalypse 4/5 (sick) | 8 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **10** (pass (hold everything): us 6 vs 28)
    - `Cast Preacher of the Schism` scored **90** (Cast Preacher of the Schism: us 6 vs 28)
- Pilot's reasoning: "At 6 life against a board with Sheoldred (4/5 deathtouch), two Preachers, Faerie Mastermind, a Vampire Token, and their Bat, I desperately need blockers. Casting my own Preacher of the Schism gives me a 2/4 deathtouch body that can trade with or deter almost anything they attack with (deathtouch mak"

## Turn 17 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **6** vs MAD **28**
- Pilot board: Deep-Cavern Bat 1/1, Preacher of the Schism 2/4 (sick) | 5 lands (2 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Vampire Token 1/1 (tapped), Preacher of the Schism 2/4 (sick), Sheoldred, the Apocalypse 4/5 (sick) | 8 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **72** (unblocked: us 6 vs 28)
    - `attack-all` scored **42** (unblocked: us 7 vs 27)
- Pilot's reasoning: "The Bat (1/1 flying) is currently unblockable — their only untapped blockers (summoning-sick Preacher and Sheoldred) lack flying — so attacking is a free +1 life and 1 damage. But at 6 life facing a lethal-looking alpha strike next turn (Bat, Faerie Mastermind, two Preachers, Vampire Token, and Sheo"

## Turn 18 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **6** vs MAD **32**
- Pilot board: Preacher of the Schism 2/4 (sick) | 5 lands (2 untapped)
- Pilot hand: empty
- MAD board: Deep-Cavern Bat 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped), Spyglass Siren 1/1 (sick), Deep-Cavern Bat 1/1 (sick) | 10 lands (2 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **5** (after combat: us -5 vs 33)
    - `Preacher of the Schism>Sheoldred, the Apocalypse` scored **85** (after combat: us -1 vs 33)
    - `Preacher of the Schism>Preacher of the Schism` scored **20** (after combat: us -3 vs 33)
    - `Preacher of the Schism>Preacher of the Schism` scored **20** (after combat: us -3 vs 33)
- Pilot's reasoning: "All lines are lethal this turn (I'm at 6 life facing 11 total attacking power with only one blocker), but blocking Sheoldred, the Apocalypse minimizes the overkill (ending at -1 vs -3 or -5), which is the best available choice given the situation is unavoidable."
