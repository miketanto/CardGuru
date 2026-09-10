# Engine rewrite feasibility — is a lean Rust/C++ engine for the curriculum fragment 100x–1000x faster than XMage, and is it worth building?

Read-only study, 2026-09-10. XMage at pin 7554968c with CardGuru patches
(`C:/Users/sutanto4/xmage-pin`), harness in `rl/xmage-src/`. Nothing in
either tree was modified. Every number below is either quoted from a
file (cited) or marked **[estimate]** with what it rests on. The code
paths for the ladder cards themselves (`Mage.Sets`) are not in the local
pin, so card semantics are taken from `rl/CURRICULUM-LADDER.md` and
oracle text, not from the card classes (see §6).

---

## 0. Verdict in ten lines

1. **The premise is right about the engine and wrong about the game.** Roughly 78% of XMage's CPU on the policy workload is `PlayerImpl.getPlayable` (`rl/PHASE12-PERF-SCOPE.md:32-35`), and reading it confirms almost all of that is generality: two full deep copies of the game per call, seven-zone scans, alternative-cost and rule-modification scans — none of which the mono-basic, no-trigger ladder decks need. Engine-only, a specialised engine on rung 0 plausibly is 1000x faster **[estimate, §5]**.
2. **But per-game wall clock is not engine-bound on the fragment.** On W0Base the harness already runs 4.5–4.8 games/s sequentially with ~20 policy consults per game at 3.4–4.5 ms each; inference is ~30–40% of the game (`rl/artifacts/rung0/W0Base/*`, `rl/THROUGHPUT-LOCAL.md:103-104`). A zero-cost engine gives at most ~3x per game unless inference is batched.
3. **And training wall clock is not game-bound at all.** At conc4, 32 episodes play in 5–10 s and the PPO update takes 35–65 s; play is 7–10% of the loop (`rl/THROUGHPUT-LOCAL.md:90-100`). A 1000x engine makes training ~1.1x faster until the update is fixed.
4. **100x per game is defensible only as "new engine + batched inference across hundreds of environments" — a redesign of the policy server as much as the engine.** 1000x per game is not defensible for anything the research measures; it requires per-consult inference below ~10 µs.
5. **Feasibility by tier:** (a) rung 0 vanilla combat — feasible, ~3–5 engineer-weeks including differential testing **[estimate]**; (b) + flying/first strike/vigilance/lifelink — +1–2 weeks; (c) + sorcery-speed targeted removal — +1–2 weeks; (d) + instants and a real stack — +2–3 weeks; (e) BenchBurn/BenchDimir/holdouts — not feasible: it is a re-implementation of XMage's event/layer/replacement system, and every transfer-study deck lives there.
6. **The largest hidden cost is not rules but parity:** `HeuristicPlayer` (574 lines) + `ComputerPlayer` (1355 lines; mulligan, mana auto-pay, multi-blocker damage split) must be reproduced decision-for-decision or every historical baseline breaks; `SearchPlayer`, `cp7`, `mcts` and the DAgger shadow teacher cannot be ported at all — they run XMage's own simulation.
7. **XMage is deterministic enough for differential testing** (seeded `java.util.Random`, name-sorted then reseeded shuffles, insertion-ordered collections) — but bit-for-bit reproducibility across runs has never been demonstrated in this project's docs and should be the first experiment.
8. **The cheap alternative is worth ~2–3x and is exact for the fragment:** a mana-arithmetic pre-check that skips `getPlayable` on the 59.9% of windows where the seat can do nothing (`rl/PHASE12-PERF-SCOPE.md:76-84`), plus dropping the redundant second copy inside `getManaAvailable` (already measured 1.28x, `PHASE12:172-184`), plus the yield interface already in `RLPlayer.priority`.
9. **Recommendation:** do not build the engine now. Fix the update step and batch inference first — those two dominate wall clock and they are prerequisites for the rewrite paying off anyway. Re-open the rewrite only if, after that, rung 0–3 play is again the bottleneck and the black/white ladders are the only decks that matter for the next year.
10. If it is built anyway, build it as a vectorised environment (N games per thread, batched observation tensors) with a Java-side transcript replay for differential tests, and stop at tier (d).

---

## 1. What the curriculum fragment requires of an engine

Decks read from `rl/*.dck` (W-, B-, R-rungs) and `benchmark/xmage/BenchBurn.dck`, `rl/BenchDimir.dck`. Card texts: the four keyword creatures and all spells are described in `rl/CURRICULUM-LADDER.md:119-128` (white) and `:202-206` (black); the vanilla status of the base decks is the ladder's design premise (`:58-70`, `:212-219`). Keyword availability per colour is the ladder's own census (`rl/CURRICULUM-LADDER.md:38-46`): white has **zero** deathtouch, trample, menace or haste stat lines, so those keywords appear in no ladder deck.

### 1a. Per-rung mechanics

| rung / deck | card types | keywords | effect kinds | timing | targeting predicates | mana | zones touched | engine tier |
|---|---|---|---|---|---|---|---|---|
| W0Base, W0Twin, R0Base, R0Twin, R0Novel, B0Base, B0Twin | creature, basic land | none | none | sorcery-speed casts only (creatures, land drop) | none | one basic type, scalar count | library, hand, battlefield, graveyard (deaths) | **(a)** |
| W1Ctrl, W2Ctrl | same | none | none | same | none | same | same | (a) |
| W1Fly | same | flying (block legality) | none | same | none | same | same | (b) |
| W1Fst | same | first strike (two damage steps) | none | same | none | same | same | (b) |
| W1Vig | same | vigilance (no tap on attack) | none | same | none | same | same | (b) |
| W1Lif | same | lifelink (life gain with damage, not a trigger) | none | same | none | same | same | (b) |
| W2FlyLif | same | flying + lifelink | none | same | none | same | same | (b) |
| W3Sorc, W3Twin | + sorcery | none | destroy target creature | sorcery | "tapped creature" | {1}{W} | + stack (depth 1, no responses possible) | **(c)** |
| B1Narrow / B2Mid / B3Open / B3Twin | + sorcery | none | destroy target creature | sorcery | power ≤2 / ≤3 / any | {1}{B} | + stack (depth 1) | (c) |
| B4Card | + sorcery | none | target opponent discards at random | sorcery | player target | {1}{B} | + RNG-consuming hand→graveyard | (c) |
| W4Inst | + instant | none | destroy target tapped creature | **instant** | tapped creature | {1}{W} | + stack with responses, opponent-turn priority | **(d)** |
| B1Fast, B1FastTwin | + instant | none | destroy target creature power ≤2 | instant | power ≤2 | {1}{B} | same | (d) |
| W5Trick | + instant | none | +1/+7 until end of turn (timed continuous P/T effect, layer 7c) | instant | any creature | {1}{W} | same + cleanup-step effect expiry | (d) |
| BenchBurn | creature, instant, sorcery, land | haste, prowess (triggered), vanishing (counters, upkeep trigger, sacrifice) | direct damage to creature/player, attack trigger revealing library top (Goblin Guide), damage-redirection trigger (Jackal Pup), "can't be regenerated" replacement, "damage can't be prevented / players can't gain life" rule-modifying effect (Skullcrack), ETB/LTB triggers (Keldon Marauders) | both | creature-or-player, any target | mono-red | + exile? no; counters, revealed cards | **(e)** |
| BenchDimir | + planeswalker, enchantment, creature-land, dual/conditional lands | flash, ninjutsu, loyalty, transform, stun counters, tokens, "return as enchantment" replacement | counterspells (stack interaction), tap+stun, alternative additional costs (Bitter Triumph), creature-land activation, planeswalker attack/damage redirection | both, including on the stack | spells on the stack as targets | two colours with conditional sources | exile, command? no; token creation; library shuffles mid-game | (e) |

Card mechanics in the BenchBurn/BenchDimir rows are from oracle text as recalled and from the categorical bits in `rl/e2_features.tsv` (e.g. `Goblin Guide`, `Keldon Marauders`, `Skullcrack` rows); the card classes are not local (§6).

### 1b. Which rungs are vanilla-only

`W0Base`, `W0Twin`, `W1Ctrl`, `W2Ctrl`, `R0Base`, `R0Twin`, `R0Novel`, `B0Base`, `B0Twin` — **9 of the 22 ladder decks** are "vanilla creatures + basic lands + combat" and nothing else. This is exactly the scope `rl/xmage-src/CombatMath.java:33-38` declares for itself ("Vanilla bodies only: no first strike, deathtouch, trample, flying or menace"). The other 13 need at most tier (d).

What the fragment therefore never needs: triggered abilities, replacement/prevention effects, cost modification, alternative costs, split/MDFC/adventure dispatch, the seven-layer continuous-effects system beyond one timed P/T boost, watchers, tokens, counters (except damage), exile, command zone, planeswalkers, multi-colour mana, conditional mana. Every one of those is scanned on every `getPlayable` call today (§2).

---

## 2. Where XMage's per-decision cost comes from

### 2a. The priority loop and what runs before the player is even asked

`GameImpl.playPriority` (`Mage/src/main/java/mage/game/GameImpl.java:1719-1790`) is entered once per step that has priority (`Step.java:69-75`, 13 `PhaseStep`s, untap and cleanup normally without priority). Per pass through the inner loop, **before** `player.priority(this)` is called:

| call | file:line | what it does in the fragment | generality cost |
|---|---|---|---|
| `bookmarkState()` once per `playPriority` | `GameImpl.java:1743`, `:979-986`, `:835-841` | rollback support (GUI "undo") | **one full `GameState.copy()` per step** (`GameStates.java:22-24`) — unconditional in non-simulation games |
| `checkStateAndTriggered()` | `GameImpl.java:2320-2335` | loop: SBA → simultaneous events → triggers → `processAction` | `checkStateBasedActions` is 640 lines with 26 distinct action sites (`GameImpl.java:2387-3027`); the fragment needs three of them (life ≤ 0, lethal damage, empty-library draw) |
| `checkTriggered()` | `GameImpl.java:2341-2384` | nothing (no triggers in W/B decks) | iterates all players, `TriggeredAbilities.checkTriggers` copies the trigger list per event (`TriggeredAbilities.java:102-120`) |
| `applyEffects()` | `GameImpl.java:1991`, `GameState.java:668-678` | reset every player, every permanent (`PermanentImpl.java:259-269`), combat; then `ContinuousEffects.apply` | the seven-layer system: `getLayeredEffects` builds and sorts a list every call (`ContinuousEffects.java:189-223`), then applies layer 1 copy, layer 2 control (looping until control stabilises), … (`ContinuousEffects.java:971-1010`) — for W5 this carries one +1/+7 effect; for every other rung it is empty |
| `saveState(false)` | `GameImpl.java:1747`, `:835-841` | nothing unless `saveGame` | — |

Each priority window thus already pays a state copy (for rollback) and a full layer/SBA pass before the seat's own work begins. Then:

### 2b. `getPlayable` — one logical call, two deep copies, seven zone scans

`RLPlayer.priority` calls `getPlayable(game, true)` unconditionally at every window (`rl/xmage-src/RLPlayer.java:648`); `HeuristicPlayer.priority` does the same (`Mage.Tests/.../HeuristicPlayer.java:208`). Both seats, every window: 447 calls/episode on BenchDimir rl-vs-heuristic, 893 in self-play (`rl/PHASE12-PERF-SCOPE.md:63-67`). The chain (`rl/PHASE12-PERF-SCOPE.md:55-58`):

```
getPlayable(Game,boolean)                       PlayerImpl.java:4393
 -> getPlayable(Game,boolean,Zone,boolean)      PlayerImpl.java:4409   (memo wrapper, off by default, 0 hits on RL workload)
 -> getPlayableUncached(...)                    PlayerImpl.java:4442
     game = originalGame.createSimulationForPlayableCalc()      :4448   FULL COPY #1 (GameImpl.java:278-283 -> GameState copy ctor :140-190)
     availableMana = getManaAvailable(game)                     :4449
         game = originalGame.createSimulationForPlayableCalc()  :3574   FULL COPY #2 ("workaround to fix a triggers list modification bug")
         ManaOptions built from every mana ability in hand and battlefield  :3576-3640, ManaOptions.java:43-150 (nested loops over net-mana variations)
     for each card in hand: 3 x preventedByRuleModification scans (PLAY_LAND, CAST_SPELL, CAST_SPELL_LATE)   :4462-4485 -> ContinuousEffects.java:811-850
                            findActivatedAbilityFromPlayable -> canPlay                                       :4487, :3767-3836
                                ability.copy(); canActivate; adjustX; costModification scan; spellCanBeActivatedNow;
                                canPayMinimumManaCost -> getMinimumCostToActivate (all cost combinations)      :3837-3838
                                alternative-cost scans (dynamic + AlternativeSourceCosts)                      :3802-3826
     then GRAVEYARD, EXILED, LIBRARY, HAND(again, other players), BATTLEFIELD, STACK, COMMAND zones            :4497-4610
        each object dispatched on SplitCard / MDFC / TDFC / CardWithSpellOption / Card / StackObject           :4148-4180
```

What the GameState copy constructor duplicates (`GameState.java:140-190`): players (with hand, library, graveyard as `CardsImpl`), battlefield, stack, exile, command, `effects` (all nine effect lists, `ContinuousEffects.java:42-53`), `triggers`, `delayed`, `watchers`, `combat`, `turnMods`, and `deepCopyObject` of `triggered`, `cardState`, `values`, `permanentCostsTags`, `mageObjectAttribute`. The profile's self-time is exactly this allocation: `ManaCostsImpl.<init>` 8.1%, `ManaOptions.<init>` 7.6%, `HashMap.putAll` 5.5%, `deepCopyObject` 5.0%, `Effects.<init>` 4.9%, `AbilitiesImpl.<init>` 3.9%, ~12% collection growth (`rl/PHASE12-PERF-SCOPE.md:37-41`). Inclusive: `getPlayable` 77.8%, of which `createSimulationForPlayableCalc` 67.2% and `getManaAvailable` 38.2% (`:32-35`).

### 2c. Generality vs. what the fragment needs — per priority window

| work item | XMage today | what a rung-0 engine must do | verdict |
|---|---|---|---|
| "what can I play?" | 2 deep copies + 7-zone scan + per-ability alt-cost scans | for ≤7 cards in hand: `manaValue <= untappedBasics`, plus `landDropAvailable && isMainPhase && stackEmpty` — tens of integer ops | **generality** (all of it) |
| mana availability | `ManaOptions` combinatorics over net-mana variations | count untapped lands | generality (mono-basic decks collapse mana to a scalar) |
| mana payment | `ManaCostsImpl.pay` → `ComputerPlayer.playMana` (`ComputerPlayer.java:394-406`) choosing which sources | tap N lands | generality; **but** which lands tap is a player choice and irrelevant only because all 24 lands are identical |
| SBA | 640 lines, 26 sites | 3 checks over ≤30 permanents | mostly generality |
| layer system | list build + sort + 7 layers per `applyEffects` | W5 only: one "+1/+7 until EOT" — a timed stat delta | generality |
| triggers / watchers / replacement | list copies and scans per event | none through W5/B4 | pure generality |
| rollback bookmark | full copy per step | none (RL harness never rolls back) | pure generality |
| turn/step sequencing, priority passing | `Turn/Phase/Step` (`Phase.java:72-260`), `skipStep` rules (`DeclareAttackersStep.java:28`, `DeclareBlockersStep.java:27`, `CombatDamageStep.java:41`) | must be reproduced exactly (window counts are a published metric) | **not** generality — must be re-implemented |
| combat | `Combat.java` 1967 lines, `CombatGroup` damage split with player-chosen amounts (`CombatGroup.java:260-330, :490, :531-538`), first-strike bookkeeping via `FirstStrikeWatcher` (`:234`) | declare / legality / assign / lethal-damage split / simultaneous death; first-strike step for W1Fst | not generality, but simpler: no banding, no trample, no menace, no multiple-blocker requirements |
| mulligan, shuffle, draw | London mulligan (`MulliganType.java:28-35`) with `ComputerPlayer.chooseMulligan` (`ComputerPlayer.java:106-116`) and its bottoming choice | same | must be reproduced |

**Adversarial note:** the 78% figure is the *engine's* share of the engine's own thread. It is not the share of wall clock (§5). Phase 12 itself found that cutting engine work by a third moved conc4 throughput by 5% (`rl/PHASE12-PERF-SCOPE.md:178-188`).

---

## 3. What the RL harness needs from an engine

The engine boundary in this project is XMage's `Player` interface (283 abstract methods, `Mage/src/main/java/mage/players/Player.java`), of which `RLPlayer` overrides a handful and inherits the rest from `ComputerPlayer`. A replacement engine must expose equivalents of:

### 3a. Decision sites (RLPlayer, `rl/xmage-src/RLPlayer.java`)

| site tag | method | line | what is chosen | candidate encoding |
|---|---|---|---|---|
| `prio` | `priority(Game)` | 634-720, consult at 696 | PASS or one `ActivatedAbility` (cast / land drop); list sorted by `name|rule` at 659-662; phantom land drop filtered at 650-651 | `cands[0]=blank(T_PASS)`, then `forCard(T_LAND|T_SPELL, card)` |
| `target` | `choose/chooseTarget(Target…)` | 820-860, consult at 798 | one legal target (permanent or player) | `forTargetPermanent` / `forTargetPlayer` (`StateEncoder.java:275-303`) |
| `targetCard` | `choose(Cards, TargetCard…)` | 862-905, consult at 854 | a card among a set (discard, bottoming) | card features |
| `attack1` / `atkjoint` | `selectAttackers` | 910-1120, consults at 944 / 1099 | v≤4: per-creature attack; v5+: one attack **subset** from `CombatMath.bestAttack` options, dominance-filtered, capped at `rl.attackMaxCands`=64 (1047) | `forAttackSet(AttackOption…)` (`StateEncoder.java:341-357`) — afterstate features from `CombatMath.resolve` |
| `block1` / `blkjoint` | `selectBlockers` | 1123-1350, consults at 1228 / 1347 | v≤3: per-blocker; v4+: one complete **assignment**, capped at `rl.jointMaxCands`=48 (1307) | `forAssignment(Outcome…)` (`StateEncoder.java:304-314`), `forBlock` (380-416) |
| fallbacks (counted, not consulted) | `announceX`, `chooseMode`, `chooseUse`, `getAmount` | 1608-1629 | inherited `ComputerPlayer` logic, counted in `fallbackCalls` | — |

Yield logic (`priority:636-641`, `setYieldAfterPass`, `YieldKind {NONE, REACTIVE, MY_NEXT_MAIN}` at 479) skips consults but still receives the priority call — an engine must still *offer* the window so `windows` and `yieldSkipped` counters stay comparable.

### 3b. Observation

- Flat state `s[0..31]` (`StateEncoder.java:115-244`): life ×2, hand sizes, untapped/total lands ×2, creature counts, total P/T ×2, turn number, active-player flag, four step flags, stack depth, graveyard sizes, library size; v2+: attackers, unblocked count/power, life-after-unblocked, free blockers, top-of-stack controller/kind/instant flags. Every field is a count or sum over zones — trivially available from any engine.
- Candidate vectors (`StateEncoder.java:250-416`): type one-hot, mana value, P/T, creature/instant/sorcery flags, controller flag, identity (16-bucket name hash or E2/E3 table from `rl/e2_features.tsv` via `-Drl.cardFeatures`), plus the combat afterstate fields listed above.
- v6 (entity tokens + typed relation edges, `rl/HANDOFF-STACK-TIMING.md:14-17`) is not read at the flat-state level (`RLPlayer.java:665-668`); its emission code was not audited here (§6).

### 3c. Episode protocol and counters (`rl/xmage-src/EpisodeRunner.java`)

- Game construction: `TwoPlayerDuel(LEFT, ONE, GAME_DEFAULT mulligan → London, 60 cards, 20 life, 7 cards)` (`:117-118`), `testMode=false` (real mulligans, `:287`), `stopOnTurn` default 60 at `END_TURN` (`:288-289`, `:516`), on-play alternates `i % 2` (`:546`, `:692`).
- Seeding: `RandomUtil.setSeed(seed)` before `game.start` (`:291`); each shuffle name-sorts the library then reseeds with `benchSeed + 1000003·name.hashCode() + shuffleCount` (`RLPlayer.java:519-533`); concurrency requires `-Dmage.randomPerThread=true` (`:657-661`, `RandomUtil.java:17-30`).
- Opponents: `heuristic` (`HeuristicPlayer`, 574 lines), `search` (`SearchPlayer`), `cp7`, `mcts` (XMage's own AIs, need a fake `Match`, `:270-284`), `rl` (self-play).
- Output line (`:571-583`): `episodes, wins, losses, draws, stalls, win_rate, games_per_sec, agent_consults_per_ep, agent_windows_per_ep, agent_actions_per_ep, turns_per_ep, fallbacks=…`; plus per-decision censuses referenced by the ground rules (`tgtLegal_p0..p6`/`tgtChose_p0..p6`, `under_over`, `autoPassK0`, `yieldSkipped`, `instantCasts`, `instantCastsOppTurn`).
- IPC: `SocketPolicyClient` — newline-delimited JSON over localhost TCP, handshake carrying `STATE_DIM`/`CAND_DIM` (`rl/README.md:20-24`).
- Teacher/DAgger paths (`TeacherLogPlayer`, `shadowLabel` at `RLPlayer.java:540-570`) call `SearchPlayer.searchBest`, which simulates on XMage (`createSimulationForAI`). These cannot move to a new engine without porting the search player too.

---

## 4. Feasibility per fragment tier

Effort figures are **[estimates]** for one engineer already fluent in the rules and this harness, and include a differential-test harness but not the policy-server changes of §5. They rest on the line counts above and on the fact that each tier adds a small, closed set of mechanics.

| tier | must implement | subtle XMage semantics to match exactly | effort [est.] | verification |
|---|---|---|---|---|
| **(a) rung 0 vanilla combat** (9 decks) | zones (library/hand/battlefield/graveyard), London mulligan + `ComputerPlayer.chooseMulligan` rule (keep if <6 cards; mulligan if lands <2 or > hand−2, `ComputerPlayer.java:106-116`) **and its bottoming choice**; seeded Fisher–Yates with `java.util.Random` semantics (`Library.java:37-46`, 48-bit LCG — replicable); turn/step machine with priority passing (`playPriority:1719-1790`: active player first, both must pass with empty stack, `resetPassed` after any action) and step skipping (`DeclareAttackersStep:28`, `DeclareBlockersStep:27`, `CombatDamageStep:41`); land drop once/turn at sorcery speed; summoning sickness; declare attackers (tap), declare blockers (one blocker per attacker allowed, several blockers on one attacker), damage assignment among multiple blockers **as `ComputerPlayer.getMultiAmountWithIndividualConstraints` chooses it** (`CombatGroup.java:300,319`) with `getLethalDamage` accounting (`:531-538`); simultaneous damage → SBA deaths; draw-out loss; stopTurn stall; `HeuristicPlayer` opponent in full (land first, `bestSpell`, `bestSorcery`, attack/block heuristics, `HeuristicPlayer.java:293-490`) | (1) multi-blocker damage order is a *player* decision in XMage; `CombatMath` assumes "kill as many as possible, lowest toughness first, value-desc tiebreak" (`CombatMath.java:140-170`) — whether `ComputerPlayer` agrees is unverified; (2) the mulligan bottoming heuristic; (3) exact window count per turn (published metric: ~110 agent windows / 10.5 turns on W0Base); (4) `getPlayable` lists a land drop at illegal steps and the harness filters it (`RLPlayer.java:650-651`) — candidate lists after filtering must match; (5) both players losing simultaneously = draw | engine core ~3–5k lines Rust; **3–5 weeks** including opponent port and differential tests | replay XMage transcripts: same seed ⇒ same shuffles ⇒ feed the same decision indices ⇒ compare the 32-dim state at every window and the final result. Requires the record/replay experiment in §4b first |
| **(b) + flying, first strike, vigilance, lifelink** (W1Fly/Fst/Vig/Lif, W2FlyLif) | block legality (flying); two combat-damage steps with SBA between (first strike; XMage tracks who dealt damage in step 1 via `FirstStrikeWatcher`, `CombatGroup.java:234`); no tap on attack; life gain simultaneous with damage (rule 510.2, not a trigger) | first-strike + multi-block interactions; lifelink on a blocked-and-killed creature still gains life; `CombatMath` itself must be extended (its header says it silently gives wrong answers, `CombatMath.java:33-38`) — a harness gap regardless of engine | **+1–2 weeks** | same as (a); the W1 decks are already built and gated |
| **(c) + sorcery-speed targeted effects** (W3Sorc/Twin, B1Narrow, B2Mid, B3Open/Twin, B4Card) | a one-object stack; target legality on cast (tapped / power ≤ N / any) and re-check on resolution (fizzle); destroy → graveyard; random discard consuming the RNG stream in XMage's order (Mind Knives); opponent receives priority with a spell on the stack even though it can never respond | RNG consumption order for `randomFromCollection` (`RandomUtil.java:55-67`) must match or later shuffles diverge; `tgtLegal/tgtChose` censuses must be reproduced | **+1–2 weeks** | same; add the target census |
| **(d) + instants and a real stack** (W4Inst, B1Fast/Twin, W5Trick) | priority on the opponent's turn at every step; holding priority; LIFO resolution with responses; "until end of turn" P/T modification with cleanup-step expiry (W5; XMage layer 7c, `ContinuousEffects.java:971+`); combat damage using modified stats; yields (`RLPlayer.java:479-491, 636-641`) replicated so consult counts match | response windows after each resolution (`playPriority:1775-1784`: active player regains priority, `resetPassed`); a creature pumped in response to removal still dies; Aegis cast on an attacker after blocks changes damage assignment | **+2–3 weeks** | same; the W4 timing experiment is the cleanest test of window parity |
| **(e) beyond** (BenchBurn, BenchDimir, Holdout*, P8*, M3*, Bench{Control,Midrange,Triggers}) | triggered abilities, replacement/prevention, rule-modifying effects, cost modification, planeswalkers, flash/ninjutsu, counterspells, creature-lands, conditional mana, tokens/counters, transform, adventures — i.e. XMage's `ContinuousEffects` (1429 lines), `TriggeredAbilities`, `Combat` (1967), and a per-card scripting layer | everything | **months to years**; this is XMage | not realistic; every transfer / holdout study in the project uses these decks |

### 4b. Is XMage deterministic enough for differential testing?

Evidence for:
- One `RandomUtil` stream, `java.util.Random` (`RandomUtil.java:15`), seeded per episode (`EpisodeRunner.java:291`) and re-seeded at every shuffle after a name sort (`RLPlayer.java:525-532`; `HeuristicPlayer.shuffleLibrary` at `:146` overrides similarly). `java.util.Random` is a fully specified 48-bit LCG and can be replicated in Rust exactly.
- Ordered collections on the decision path: `Battlefield.field` is a `LinkedHashMap` (`Battlefield.java:20`), `CardsImpl` a `LinkedHashSet` (`CardsImpl.java:19`), `Players` a `LinkedHashMap` (`Players.java:12`). `RLPlayer` canonicalises candidate order (`:659-662`). The project already relies on fixed seed blocks for Elo probes (`rl/PHASE6-ELO.md:26`).
- Per-thread streams under `-Dmage.randomPerThread` make concurrent games independent (`RandomUtil.java:17-30`).

Evidence against / unverified:
- `UUID.randomUUID()` for every object and ability (`CardImpl.java:147`, `AbilityImpl.java:102`), and `HashMap<UUID,…>` for `zones`, `cardState`, `zoneChangeCounter` (`GameState.java:102-107`). Iteration over these would be run-dependent; I did not audit whether any decision-relevant path iterates them.
- `ComputerPlayer` has its own `new Random(` (`PlayerImpl.java` also — one hit) — whether any choice on the fragment path draws from it is unverified.
- No document in `rl/` reports a same-seed-twice transcript diff. **That is the first, cheap, decisive experiment** (two runs, `diff` the `RLGAME` transcripts in `/tmp/rl_p9/driver_server_<port>.log`).

Replay vehicle: `TeacherLogPlayer` already captures "the exact (state, candidates) vectors StateEncoder would hand the RL agent, labeled with the index of the action the teacher actually took" (`rl/xmage-src/TeacherLogPlayer.java` header) — the natural source of decision sequences for a differential test.

---

## 5. The speed claim

### 5a. Measured baselines

| workload | games/s | agent consults/ep | agent windows/ep | turns/ep | source |
|---|---|---|---|---|---|
| heuristic vs heuristic, BenchBurn mirror, persistent JVM | ~2.6 | — | — | — | `rl/SETUP-WSL-LOCAL.md:53` |
| policy (socket) vs heuristic, **W0Base**, sequential | 4.49–4.75 | 19.6–20.7 | 109–120 | 10.5–11.3 | `rl/artifacts/rung0/W0Base/rl_rung0_W0Base_s0/probe_D0_*.txt`, `ft_v*_1024_D0.txt` |
| policy vs heuristic, W0Twin | 3.9–4.8 | 20–21 | 112–122 | 10.7–11.4 | `rl/artifacts/rung0/W0Base/attack_audit_*.txt` |
| policy vs heuristic, B3Open | 0.44–0.66 | 181–211 | 234–260 | 22–25 | `rl/artifacts/**` summary rows |
| policy vs heuristic, BenchDimir, sequential | 0.50–0.68 | 76–200 | 173–252 | 15–24 | same; and 0.516 g/s in `rl/PHASE12-PERF-SCOPE.md:182` |
| in-process random policy, mid decks | 3.7–6.1 | — | — | 13–20 | same |
| inference cost per consult | 3.40 ms held (sequential), 4.5 ms at conc4 | | | | `rl/PHASE12-PERF-SCOPE.md:242`, `rl/THROUGHPUT-LOCAL.md:103-104` |

The ladder's "12–17 games/sec per deck" (`rl/CURRICULUM-LADDER.md:298`) is not matched by any summary row I found; the fastest policy-driven rung-0 row is 4.8 g/s. Treat 12–17 as unverified.

### 5b. Cost decomposition of one W0Base game today [estimate, from the rows above]

- Wall: 1/4.7 g/s ≈ **213 ms/game**.
- Inference: ~20 consults × 3.4 ms ≈ **68 ms** (32%). IPC ~2% (`PHASE12:34`).
- Engine (both seats): ≈ **140 ms** over ~220 priority windows (agent 110 + heuristic ~110) plus ~10 combats ⇒ **~0.6 ms per window** all-in (two `getPlayable` deep copies, SBA, layers, bookmark copy). On BenchDimir the same arithmetic gives ~4 ms/window — larger states copy slower.

### 5c. Specialised engine, rung 0 [estimate]

Per window: playable = ≤7 comparisons of mana value against an untapped-land count, plus step/stack flags: **~50–200 ns**. Per turn: untap/draw/SBA over ≤30 permanents: ~1 µs. Per combat: legality and damage O(A·B) ≤ 100 ops: ~1 µs. Per game (~220 windows, ~11 turns, ~10 combats): **~50–100 µs engine time**, i.e. 10–20k games/s per thread, ~150–300k games/s on 16 threads, before observation encoding. Versus ~0.6 ms/window in XMage this is **~3,000–10,000x engine-only** on rung 0, and 500–2,000x on the heavier rungs where XMage copies bigger states. Rests on: op counts above, ~1 ns/op, no allocation in the hot loop. This is the part of the claim that survives — even 1000x engine-only is conservative for rung 0.

Note the harness's own combat search is not free: `CombatMath.best` runs `resolve` (A+1)^B times and `bestAttack` runs that once per attack subset (`CombatMath.java:100-105`), capped at 64/48 candidates and a 200k reply cap (`RLPlayer.java:1047, 1307, 1517`). Ported as-is it is the same cost in Rust as in Java after JIT — roughly µs to low ms per combat on wide boards — and would dominate the engine on big boards.

### 5d. What that buys per game and per training hour — the adversarial part

| what is sped up | per-game bound (W0Base) | why |
|---|---|---|
| engine only, inference untouched (single torch server, 3.4 ms/consult) | 213 ms → ~70 ms: **≈3x** | 20 consults × 3.4 ms is the floor; a single-threaded server saturates at ~290 consults/s ≈ 15 rung-0 games/s **regardless of thread count** |
| engine + batched inference across ~256 environments (small MLP on CPU, ~20–50 µs/consult amortised) | ~0.5–1.5 ms/game: **≈100–400x** | inference becomes ~0.4–1 ms/game; engine ~0.1 ms; this is a rewrite of `policy_server.py` and the IPC protocol, not only the engine |
| 1000x per game (≤0.2 ms/game) | requires ≤10 µs per consult including encoding and transport | only with a tiny net, SIMD/GPU batching and zero-copy shared memory; not defensible as a claim about "the engine" |
| training wall clock at current settings | **≤1.1x** | play is 7–10% of the update loop; the PPO update is 25 ms per stored consult, 35–65 s per 32 episodes (`rl/THROUGHPUT-LOCAL.md:90-100`) |
| evaluation batteries (100–200 games, sequential) | 20–40 s → seconds | real but already cheap on rung 0; on BenchDimir (400 s) the new engine does not apply |

So: **100x is defensible as a system claim (vectorised engine + batched inference), 1000x is not; and neither number changes training throughput until the update step is addressed.**

### 5e. The alternative that skips a new engine

1. **Exact pre-check for the fragment.** 59.9% of agent windows pay two deep copies to learn the seat has nothing to do (`rl/PHASE12-PERF-SCOPE.md:76-84`). For mono-basic decks with no activated abilities, "no card in hand with mana value ≤ untapped lands, and no legal land drop" is an exact emptiness test. Phase 12's own gate applies: `consults` and `autoPassEmpty` must be identical under the pre-check (`:114-124`). Amdahl ceiling for removing the copy: 3.05x (`:89-91`).
2. **Drop the redundant second copy** in `getManaAvailable` when it is called from `getPlayableUncached` with an already-simulated game (`PlayerImpl.java:3572-3574`): built as `manaNoRecopy`, 22,825 calls / 0 mismatches, 1.28x sequential (`:155-176`). Never adopted (`PlayerImpl.java:4311-4316`).
3. **Yields** are already in `RLPlayer.priority` (`:636-641`) and the README's chain shows both-seat 216 → agent ~108 → ~42 consults/episode with gate + phantom-land filter + yields (`rl/README.md:11-17`), i.e. ~2.6x fewer consults; the "3.3x" figure given in the brief is not in any `rl/*.md` I could find.
4. **Skip the rollback bookmark copy** for RL games (`GameImpl.java:1743`) — one `GameState.copy()` per step for a feature the harness never uses. Not measured; **[estimate]** a few percent.
5. The `mage.playableCache` memo cannot help: every call is on a distinct state, 0 hits in 207,830 calls (`:61-70`).

Combined 1–4 on rung 0 is plausibly 2–3x sequential **[estimate]**, which lands within a factor of ~1.5 of what the rewrite can deliver while inference stays unbatched — for days of work instead of months, with no parity risk.

---

## 6. What this study could not determine

- **Card implementations.** `Mage.Sets` is not in `C:/Users/sutanto4/xmage-pin` (only Mage, Mage.Common, Mage.Server, Mage.Server.Plugins, Mage.Tests, Mage.Verify), so the ladder cards' exact XMage semantics (e.g. how `Take Vengeance` re-checks "tapped" on resolution) were taken from `rl/CURRICULUM-LADDER.md` and oracle text, not from code.
- **Whether `ComputerPlayer`'s multi-blocker damage split matches `CombatMath`'s assumption** (`CombatMath.java:140-170` vs `CombatGroup.java:300-319`). This matters for the current afterstate features as much as for a rewrite.
- **Same-seed reproducibility of XMage transcripts** has never been demonstrated in the repo's docs; it is the prerequisite for differential testing and is a one-hour experiment.
- **The v6 entity/relation emission** (`ENCODER-V6-*.md`) was not audited; its interface surface for a new engine may be larger than the flat 32-dim state suggests.
- **The 12–17 games/s per deck figure** in `rl/CURRICULUM-LADDER.md:298` — no artifact row supports it; the source of that number is unknown.
- **Absolute per-window engine cost on rung 0** is inferred from summary rows (§5b), not profiled; a JFR run on W0Base (as Phase 12 did on BenchDimir) would replace the estimate with a measurement.
- **Effort estimates** in §4 are unvalidated engineering judgement; the largest uncertainty is the opponent/`ComputerPlayer` parity work, not the rules.

## 7. Correction (2026-09-10, same day)

§5 said the brief's "3.3x fewer consults" figure "does not appear in any
`rl/*.md`" and read the README chain as ~2.6x. The 3.3x is real and
recorded: `EXPERIMENTS.md` #3 (repo root, outside `rl/`), the yield
act-rate study, consults 880 → 244 over 800 scripted games. The 2.6x in
`rl/README.md` is the agent seat only, after the consult gate and the
phantom-land filter. Different baselines, both correct; neither changes
this study's verdict, which rests on the update-step share of wall clock.
