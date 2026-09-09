# Decision review — g1.jsonl

Result: **pilot lost** in 11 turns. 29 real decisions out of 149 requests (the rest were forced, auto-passed, or yielded).

Rate each decision **questionable / minor / moderate / major**, or leave it alone if it was right. Say what should have been done instead and why.


## Turn 1 — null [mulligan]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Anoint with Affliction, Preacher of the Schism, Faerie Mastermind, Floodpits Drowner, Spyglass Siren
- MAD board: no creatures | 0 lands (0 untapped)
- **Chose: keep**
- Pilot's reasoning: "Keep. 2 lands + early removal (Anoint) + two flying creatures (Faerie Mastermind, Spyglass Siren) for the clock. Island untaps for turn-1 blue plays. This is exactly the shape of hand the mirror wants: interaction + evasive clock. The deck plays plenty of flash creatures, so sequencing is flexible."

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 0 lands (0 untapped)
- Pilot hand: Darkslick Shores, Island, Anoint with Affliction, Preacher of the Schism, Faerie Mastermind, Floodpits Drowner, Spyglass Siren
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **42** (pass (hold everything): us 20 vs 20)
    - `Play Darkslick Shores` scored **56** (Play Darkslick Shores: us 20 vs 20)
    - `Play Island` scored **50** (Play Island: us 20 vs 20)
- Pilot's reasoning: "Darkslick Shores is the best play—it's a flexible mana source (taps for {U} or {B}, enters untapped on turn 1) that sets up turns 2+ better than a monocolored Island. Playing a land on turn 1 is essential for mana development in this control mirror; passing cedes tempo and is suboptimal. Darkslick S"

## Turn 1 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: no creatures | 1 lands (1 untapped)
- Pilot hand: Island, Anoint with Affliction, Preacher of the Schism, Faerie Mastermind, Floodpits Drowner, Spyglass Siren
- MAD board: no creatures | 0 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 20 vs 20)
    - `Cast Spyglass Siren` scored **54** (Cast Spyglass Siren: us 20 vs 20)
- Pilot's reasoning: "Cast Spyglass Siren. Turn 1 with only one land, passing just delays mana development—I'd be sitting idle while the opponent makes their next move. Casting Spyglass Siren establishes the flying clock (fliers are the real race in this mirror) and generates a Map token, giving me intrinsic value even i"

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1 | 2 lands (2 untapped)
- Pilot hand: Island, Anoint with Affliction, Preacher of the Schism, Faerie Mastermind, Floodpits Drowner, Island
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 20 vs 20)
    - `Play Island` scored **54** (Play Island: us 20 vs 20)
    - `Play Island` scored **54** (Play Island: us 20 vs 20)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **50** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 20)
- Pilot's reasoning: "Play Island is the best play. By turn 3, I've only developed one land (Darkslick Shores) and no Islands yet, so playing an Island now is essential mana development. It enables bigger plays next turn (e.g., Preacher of the Schism {2}{B}) and standard early-game progression. Passing is passive and slo"

## Turn 3 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1 | 3 lands (3 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Faerie Mastermind, Floodpits Drowner, Island
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **50** (pass (hold everything): us 20 vs 20)
    - `Cast Anoint with Affliction` scored **15** (Cast Anoint with Affliction: us 20 vs 20)
    - `Cast Faerie Mastermind` scored **65** (Cast Faerie Mastermind: us 20 vs 20)
    - `Cast Floodpits Drowner` scored **63** (Cast Floodpits Drowner: us 20 vs 20)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **48** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 20)
- Pilot's reasoning: "Cast Faerie Mastermind (65) or Floodpits Drowner (63) to establish more flying threats—fliers are the real clock in this mirror. Faerie Mastermind edges it out because it triggers on opponent draws for card advantage (mirrors the draw-penalty aspect of Sheoldred). Floodpits Drowner is also strong wi"

## Turn 3 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **20**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Floodpits Drowner, Island
- MAD board: no creatures | 1 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **48** (unblocked: us 20 vs 20)
    - `attack-all` scored **56** (unblocked: us 20 vs 19)
- Pilot's reasoning: "Attack with Spyglass Siren. Establishing the clock is essential in the mirror—a flying 1/1 that can't be blocked by ground creatures is exactly the evasive threat that wins long games. Spyglass Siren taps, but Faerie Mastermind (2/1) provides defense against flying creatures the opponent is likely t"

## Turn 5 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1 | 3 lands (3 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Floodpits Drowner, Island
- MAD board: Faerie Mastermind 2/1 (sick) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 20 vs 19)
    - `Cast Anoint with Affliction` scored **20** (Cast Anoint with Affliction: us 20 vs 19)
    - `Cast Floodpits Drowner` scored **65** (Cast Floodpits Drowner: us 20 vs 19)
- Pilot's reasoning: "Cast Floodpits Drowner (65). Adding a third flying creature to my board establishes a dominant clock—I'll have three flying creatures (Siren, Mastermind, Drowner) to the opponent's one Faerie Mastermind (which has summoning sickness). Floodpits Drowner has flash and vigilance, giving flexibility for"

## Turn 5 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1 (sick) | 3 lands (1 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Island, Undercity Sewers
- MAD board: Faerie Mastermind 2/1 (tapped) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **45** (pass (hold everything): us 20 vs 19)
    - `Play Island` scored **55** (Play Island: us 20 vs 19)
    - `Play Undercity Sewers` scored **60** (Play Undercity Sewers: us 20 vs 19)
- Pilot's reasoning: "Play Undercity Sewers (60). It develops your mana base while providing surveil 1, which filters your deck for answers in the control mirror. Though it enters tapped (same as Island for immediate untapped land count next turn), the surveil benefit gives card selection—finding Preacher of the Schism, "

## Turn 5 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **19**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1 (sick) | 4 lands (1 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Island
- MAD board: Faerie Mastermind 2/1 (tapped) | 2 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **40** (unblocked: us 20 vs 19)
    - `attack-all` scored **68** (unblocked: us 20 vs 16)
    - `hold[Spyglass Siren]` scored **55** (unblocked: us 20 vs 17)
    - `hold[Faerie Mastermind]` scored **50** (unblocked: us 20 vs 18)
- Pilot's reasoning: "Attack-all (68): Deal 3 damage (Spyglass Siren 1 + Faerie Mastermind 2) and reduce opponent to 16 life. Floodpits Drowner has summoning sickness so can't attack. This maintains aggressive clock pressure—in the mirror, being the beatdown is key. Both your flying creatures tap, but the opponent's Faer"

## Turn 7 — Upkeep [leaf_eval/priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Island
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **60** (pass (hold everything): us 20 vs 16)
    - `Cast Anoint with Affliction` scored **35** (Cast Anoint with Affliction: us 20 vs 16)
- Pilot's reasoning: "Pass (60). Your board is strong with three flying creatures (Siren, Mastermind, Drowner) and all mana untapped. The opponent's Preacher of the Schism has summoning sickness, so it's not an immediate threat—it can't attack yet. Casting Anoint with Affliction (35) appears to remove your own Faerie Mas"

## Turn 7 — Upkeep [priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Island
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Anoint with Affliction; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Pass priority. Upkeep with no triggered abilities to respond to. Casting Anoint with Affliction now is tactically wrong—the previous leaf_eval showed it results in losing your Faerie Mastermind (based on the board state after casting). Better to hold your removal for a more critical moment, or cast "

## Turn 7 — Draw [leaf_eval/priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Island, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **58** (pass (hold everything): us 20 vs 16)
    - `Cast Anoint with Affliction` scored **30** (Cast Anoint with Affliction: us 20 vs 16)
- Pilot's reasoning: "Pass (58). Keep your board intact with all three flying creatures (Siren, Mastermind, Drowner) and untapped mana going into your main phase. The opponent's Preacher of the Schism has summoning sickness, so it's not an immediate threat. Casting Anoint with Affliction (30) results in losing your Faeri"

## Turn 7 — Draw [priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Island, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Anoint with Affliction; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {T}: Add {U}.; [6] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Pass priority. Same situation as the draw step evaluation—casting Anoint with Affliction results in losing your Faerie Mastermind for no clear benefit (the opponent's Preacher remains on board). Better to proceed to your main phase with all creatures intact and full mana available to evaluate your o"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Island, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **48** (pass (hold everything): us 20 vs 16)
    - `Cast Anoint with Affliction` scored **20** (Cast Anoint with Affliction: us 20 vs 16)
    - `Cast Preacher of the Schism` scored **70** (Cast Preacher of the Schism: us 20 vs 16)
    - `Play Island` scored **52** (Play Island: us 20 vs 16)
    - `Play Swamp` scored **52** (Play Swamp: us 20 vs 16)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **54** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 16)
- Pilot's reasoning: "Cast Preacher of the Schism (70) is the best play. It establishes a strong threat (2/4 deathtouch) on the board alongside your fliers. Deathtouch is crucial here—it means your Preacher kills any creature that blocks it, controlling the opponent's board. Having two Preachers in play (yours and theirs"

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 4 lands (1 untapped)
- Pilot hand: Anoint with Affliction, Island, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **52** (pass (hold everything): us 20 vs 16)
    - `Play Island` scored **60** (Play Island: us 20 vs 16)
    - `Play Swamp` scored **60** (Play Swamp: us 20 vs 16)
- Pilot's reasoning: "Play Island or Swamp (both 60). After casting Preacher, you have four creatures on board (strong position) but all three lands are tapped. Playing a land develops your mana base for future turns—next turn you'll untap and have more resources to work with. Island and Swamp are equally valuable here, "

## Turn 7 — Precombat Main [leaf_eval/priority]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 5 lands (2 untapped)
- Pilot hand: Anoint with Affliction, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **54** (pass (hold everything): us 20 vs 16)
    - `{1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.` scored **60** ({1}, {T}, Sacrifice this artifact: Target creature you control explores. Activate only as a sorcery.: us 20 vs 16)
- Pilot's reasoning: "Sacrifice Map Token (60) to upgrade Preacher of the Schism to 3/5. The boost is significant—from 2/4 to 3/5 makes Preacher much harder for the opponent to kill or block effectively (especially with deathtouch). In the control mirror, a more powerful creature is better than keeping 1 untapped mana op"

## Turn 7 — Precombat Main [target]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1, Preacher of the Schism 2/4 (sick) | 5 lands (2 untapped)
- Pilot hand: Anoint with Affliction, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Menu: [0] Floodpits Drowner 2/1 (A); [1] Faerie Mastermind 2/1 (A); [2] Preacher of the Schism 2/4 (A); [3] Spyglass Siren 1/1 (A)
- **Chose: target Preacher of the Schism 2/4 (A)**
- Pilot's reasoning: "Target Preacher of the Schism (index 2). It's already your strongest creature (2/4 with deathtouch), and making it 3/5 maximizes the value of the explore effect. Whether you hit a land (gains time) or a non-land (+1/+1 boost), Preacher benefits the most. Upgrading a 2/4 deathtouch creature to 3/5 cr"

## Turn 7 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **20** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Floodpits Drowner 2/1, Preacher of the Schism 3/5 (sick) | 4 lands (0 untapped)
- Pilot hand: Anoint with Affliction, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (sick) | 3 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **45** (unblocked: us 20 vs 16)
    - `attack-all` scored **58** (1 block(s), response 1: us 20 vs 13; unblocked: us 20 vs 11)
    - `hold[Spyglass Siren]` scored **50** (1 block(s), response 1: us 20 vs 14; unblocked: us 20 vs 12)
    - `hold[Faerie Mastermind]` scored **45** (1 block(s), response 1: us 20 vs 15; unblocked: us 20 vs 13)
    - `hold[Floodpits Drowner]` scored **52** (unblocked: us 20 vs 13)
- Pilot's reasoning: "Attack-all (Siren + Mastermind + Drowner = 5 damage unblocked, 3 blocked; opponent 11 or 13). You've established a strong board (upgraded 3/5 Preacher, multiple fliers) and should press your advantage. Holding back creatures is too passive—you're the beatdown here with 4 untapped creatures vs oppone"

## Turn 8 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **20** vs MAD **13**
- Pilot board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 3/5 (sick) | 4 lands (0 untapped)
- Pilot hand: Anoint with Affliction, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **65** (after combat: us 16 vs 13)
    - `Preacher of the Schism>Preacher of the Schism` scored **35** (after combat: us 18 vs 13)
- Pilot's reasoning: "No-blocks. You're ahead on the board (Preacher clock still active and untapped), life totals are healthy (16 is safe), and opponent is already at 13 after your attack. Blocking with your Preacher trades away your best threat and gains only 2 life—not worth it when you should be closing the game. Kee"

## Turn 9 — Upkeep [leaf_eval/priority]
- Life: pilot **16** vs MAD **13**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **75** (pass (hold everything): us 16 vs 13)
    - `Cast Anoint with Affliction` scored **25** (Cast Anoint with Affliction: us 16 vs 13)
    - `{3}{U}: Each player draws a card.` scored **45** ({3}{U}: Each player draws a card.: us 16 vs 13)
- Pilot's reasoning: "Pass. You're in a winning position: 16 vs 13 life, with a strong, untapped board (Siren + Mastermind fliers + Preacher clock). The opponent's Sheoldred is summoning sick and is your main threat once it activates on turn 10. Your plan: attack for 3 damage/turn and close by turn 13, before Sheoldred b"

## Turn 9 — Upkeep [priority]
- Life: pilot **16** vs MAD **13**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 4 lands (0 untapped)
- Menu: [0] pass priority; [1] Cast Anoint with Affliction; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {3}{U}: Each player draws a card.; [6] {T}: Add {U}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.
- **Chose: PASS**
- Pilot's reasoning: "Pass priority. Proceed to main phase to execute your winning strategy: attack with Siren + Mastermind + Preacher for 6 damage across multiple turns and close the game before Sheoldred activates (turn 10). Casting Anoint with Affliction loses your Preacher (shown in Decision 24 leaf 1), sacrificing y"

## Turn 9 — Draw [leaf_eval/priority]
- Life: pilot **16** vs MAD **13**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5 | 4 lands (4 untapped)
- Pilot hand: Anoint with Affliction, Swamp, Enduring Curiosity
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **70** (pass (hold everything): us 14 vs 13)
    - `Cast Anoint with Affliction` scored **25** (Cast Anoint with Affliction: us 14 vs 13)
    - `Cast Enduring Curiosity` scored **85** (Cast Enduring Curiosity: us 14 vs 13)
    - `{3}{U}: Each player draws a card.` scored **50** ({3}{U}: Each player draws a card.: us 14 vs 13)
- Pilot's reasoning: "Cast Enduring Curiosity. You drew it this turn and it's a powerhouse: 4/3 creature with flash, triggers card draw when your creatures deal combat damage, and recursively returns as an enchantment when it dies. Combined with your Siren (1), Mastermind (2), and Preacher (3), you have 10 damage on turn"

## Turn 9 — Precombat Main [leaf_eval/priority]
- Life: pilot **14** vs MAD **13**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5, Enduring Curiosity 4/3 (sick) | 4 lands (0 untapped)
- Pilot hand: Anoint with Affliction, Swamp
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **65** (pass (hold everything): us 14 vs 13)
    - `Play Swamp` scored **75** (Play Swamp: us 14 vs 13)
- Pilot's reasoning: "Play Swamp. Both lines result in the same combat (attacking with Siren, Mastermind, Preacher for 6 damage, reducing opponent to 7 life), but playing your land gives you 1 untapped mana next turn (5 lands vs 4). In a control mirror where you're closing the game, extra mana flexibility is valuable for"

## Turn 9 — Declare Attackers [leaf_eval/attackers]
- Life: pilot **14** vs MAD **13**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5, Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Pilot hand: Anoint with Affliction
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (sick), Vampire Token 1/1 (sick) | 4 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `attack-none` scored **30** (unblocked: us 14 vs 13)
    - `attack-all` scored **70** (1 block(s), response 1: us 14 vs 10; 1 block(s), response 2: us 14 vs 11; unblocked: us 14 vs 7)
    - `hold[Spyglass Siren]` scored **50** (1 block(s), response 1: us 14 vs 11; 1 block(s), response 2: us 14 vs 12; unblocked: us 14 vs 8)
    - `hold[Faerie Mastermind]` scored **35** (1 block(s), response 1: us 14 vs 12; 1 block(s), response 2: us 14 vs 13; unblocked: us 14 vs 9)
    - `hold[Preacher of the Schism]` scored **70** (unblocked: us 14 vs 10)
- Pilot's reasoning: "Attack-all (Siren, Mastermind, Preacher for 6 damage). You're closing a clock: opponent at 13 life, getting low. Unblocked gets them to 7 (leaf 3, score 85)—one more attack away from dead. Even blocked scenarios get them to 10-11 (leaves 1-2, avg 72), continuing your tempo. Holding creatures (leaves"

## Turn 10 — Declare Blockers [leaf_eval/blockers]
- Life: pilot **5** vs MAD **16**
- Pilot board: Spyglass Siren 1/1 (tapped), Faerie Mastermind 2/1 (tapped), Preacher of the Schism 3/5 (tapped), Enduring Curiosity 4/3 (sick) | 5 lands (1 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Swamp, Kaito, Bane of Nightmares, Restless Reef
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped), Kaito, Bane of Nightmares 4/5 (sick) | 5 lands (0 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `no-blocks` scored **5** (after combat: us -3 vs 16)
    - `Enduring Curiosity>Preacher of the Schism` scored **10** (after combat: us -1 vs 16)
    - `Enduring Curiosity>Sheoldred, the Apocalypse` scored **90** (after combat: us 1 vs 16)
- Pilot's reasoning: "Block Sheoldred to survive: EC takes 4 damage and dies, we take 0 from Sheoldred. Unblocked scenarios lead to -3 or -1 life (losses). Only blocking Sheoldred keeps us at 1 life to fight next turn. Must survive to win."

## Turn 11 — Upkeep [leaf_eval/priority]
- Life: pilot **1** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5 | 6 lands (6 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Swamp, Kaito, Bane of Nightmares, Restless Reef
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **85** (pass (hold everything): us 1 vs 16)
    - `Cast Anoint with Affliction` scored **45** (Cast Anoint with Affliction: us 1 vs 16)
    - `{3}{U}: Each player draws a card.` scored **25** ({3}{U}: Each player draws a card.: us 1 vs 16)
- Pilot's reasoning: "Pass keeps full turn open to attack, cast, or control. At 1 life, need immediate win or stabilization—passing lets main phase execute. Anoint removes threat but wastes turn; drawing uses all mana with unclear benefit. Hold for maximum flexibility."

## Turn 11 — Upkeep [priority]
- Life: pilot **1** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5 | 6 lands (6 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Swamp, Kaito, Bane of Nightmares, Restless Reef
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 6 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Anoint with Affliction; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {3}{U}: Each player draws a card.; [6] {T}: Add {U}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Pass priority. Upkeep complete. Move to precombat main phase (Turn 11)—need to attack and cast threats while at 1 life. Execute win condition now."

## Turn 11 — Draw [leaf_eval/priority]
- Life: pilot **1** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5 | 6 lands (6 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Swamp, Kaito, Bane of Nightmares, Restless Reef, Island
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 6 lands (1 untapped)
- Engine simulated these lines; pilot scored the resulting boards (candidate value = worst leaf, highest wins):
    - `pass (hold everything)` scored **12** (pass (hold everything): us -1 vs 16)
    - `Cast Anoint with Affliction` scored **10** (Cast Anoint with Affliction: us -1 vs 16)
    - `{3}{U}: Each player draws a card.` scored **5** ({3}{U}: Each player draws a card.: us -1 vs 16)
- Pilot's reasoning: "Draw step: Sheoldred drains 2 life as I draw. At 1 life → -1 immediately. All options lose, but pass preserves resources, Anoint removes a threat before death, drawing wastes mana. Game is lost to life drain."

## Turn 11 — Draw [priority]
- Life: pilot **1** vs MAD **16**
- Pilot board: Spyglass Siren 1/1, Faerie Mastermind 2/1, Preacher of the Schism 3/5 | 6 lands (6 untapped)
- Pilot hand: Anoint with Affliction, Preacher of the Schism, Swamp, Kaito, Bane of Nightmares, Restless Reef, Island
- MAD board: Faerie Mastermind 2/1 (tapped), Preacher of the Schism 2/4 (tapped), Sheoldred, the Apocalypse 4/5 (tapped) | 6 lands (1 untapped)
- Menu: [0] pass priority; [1] Cast Anoint with Affliction; [2] {T}: Add {U}.; [3] {T}: Add {B}.; [4] {T}: Add {U}.; [5] {3}{U}: Each player draws a card.; [6] {T}: Add {U}.; [7] {T}: Add {B}.; [8] {T}: Add {U}.; [9] {T}: Add {B}.
- **Chose: PASS**
- Pilot's reasoning: "Pass priority. Draw phase triggers Sheoldred drain (1 → -1 life). Game lost to life drain. Concede."
