# L17-FIDELITY — how faithfully XMage rebuilds 17Lands DSK games (one-set trial, 2026-09-15)

Plan and pre-stated readings: `rl/L17-CLOUD.md` §3 (not changed after seeing data).
Data: `rl/l17_dsk/DSK_top2000.jsonl.gz` (2,000 DSK PremierDraft games, strong players, seed 17).
Harness: `rl/l17/`. Results as text/CSV in `rl/l17_dsk/`.

Status: **engine, coverage, 20-game debug and 200-game run done (NO-GO, §6); 2,000-game run in progress.**

## 1. Engine

**Not run in the cloud.** The trial ran locally on the project's 11 GB WSL box
beside Phase 13c (two driver JVMs and one policy server training), under
these caps set by the coordinator: one harness JVM at a time, `-Xmx1536m
-XX:+UseSerialGC`, `nice -n 15`, games never in parallel; before each batch of
50 games the driver reads `/proc/meminfo` and pauses 10 minutes while
MemAvailable < 2,000 MB or swap used > 1 GB (`rl/l17/run_l17.sh`); no Phase 13
process, nothing in `/home/user/mage` and nothing in `~/.m2` was touched; the
2,000-game run only if the 200-game run finished within about 2 hours.

Instead of rebuilding XMage (a full `mvn install` would
overwrite the `~/.m2` jars the running Phase 13 driver JVM loads, and the
reactor build would starve it of RAM), the harness compiles against the
engine already built at `/home/user/mage`, after checking it is the pinned one:

* checkout HEAD = `7554968c96211009ad1f1208b83d6de8c2b7746d` (the pin);
* `patch -R --dry-run` of `rl/engine-patches/phase9-engine.patch` applies
  cleanly on all three files (Combat, PlayerImpl, RandomUtil), i.e. the patch
  is applied exactly;
* `phase12-mana-recopy.patch` forward dry-run fails a hunk on PlayerImpl
  (not applied), as required;
* JDK `openjdk 21.0.12.1`, Maven 3.9.9 (the ones that built it).

The harness classes are compiled with `javac` into a private directory and run
from a private working directory holding a copy of `Mage.Tests/db` and
`config/`, so nothing in `/home/user/mage` or `~/.m2` is modified. The
`rl/xmage-src` overlay in that build is whatever Phase 13 uses; the harness
touches none of it (it uses only XMage core, Mage.Sets and the Mage.Tests
`CardTestPlayerBase` / `TestPlayer` framework).

## 2. Coverage (`rl/l17/coverage.py` → `rl/l17_dsk/coverage_games.csv`)

Card database = every name registered by a `SetCardInfo` in any
`Mage.Sets/src/mage/sets/*.java` at the pin (32,456 names; CardRepository is
built by scanning these classes). A 17Lands name matches if it is registered
as-is, or for "A // B" names (rooms, double-faced) if the halves are.

| reading | value |
|---|---|
| games whose user `deck` is fully implemented | **2000/2000 = 1.000**, Wilson 95% [0.998, 1.000] |
| games whose user deck AND every mapped opponent card logged played/cast (lands, creatures, non-creatures, instants/sorceries on either turn) is implemented | **2000/2000 = 1.000**, [0.998, 1.000] |
| distinct user-deck card names | 278, missing 0 |
| missing card names | none |
| deck sizes | 40: 1894, 41: 85, 42: 11, 43–48: 10 |

Coverage bar (≥ 0.6): **met** (it is a DSK-only sample and the pin registers the whole set). Cannot support: that the implementations are
*correct* — a registered card can still be implemented differently from Arena;
the rebuild (§3) is what tests behaviour. Unmapped small ids (0–33, 25 ids) are
excluded from the opponent check; they are assumed to be tokens.

## 3. Rebuilder (`rl/l17/`)

* `build_specs.py` turns a logged game into a spec; `L17Rebuild.java` (a
  `CardTestPlayerBase` subclass run from `main`, one game at a time) replays it;
  `analyze.py` compares states; `causes.py` classifies first mismatches;
  `run_l17.sh` drives it (compile, specs, batched JVM, analysis).
* Seats. Player A always starts in the XMage test framework, so the seat on
  the play is A; `user_turn_N` is game turn 2N−1 on the play, 2N on the draw.
* **User seat**: hand = the logged `opening_hand` (final hand; mulligans are
  skipped, London bottoms = `candidate_hand_{m+1}` minus the kept hand, put at
  the library bottom); library = the logged draws in order on top, then the
  rest of the logged deck in a seeded shuffle. At each user upkeep that turn's
  logged draws are moved to the top again (so a scry/surveil/manifest
  divergence earlier does not shift the draws).
* **Opponent seat**: synthetic 40-card deck = every card instance it was
  logged playing or casting (lands, creatures, non-creatures, instants and
  sorceries on either turn), plus basics in `opp_colors` as filler. Its hand is
  hidden (only a count is logged), so at its first priority of each turn the
  cards it is logged using that turn are swapped from its library into its
  hand in exchange for a card not needed then (hand size unchanged).
* **Forced actions, both seats**: logged land plays and casts, by card name,
  through `L17Player` (a `TestPlayer` subclass overriding `priority`,
  `selectAttackers`, `selectBlockers`): a forced action that is impossible is
  recorded (`F` line) and skipped instead of failing the game. Fixed order
  rule (order is not logged): land first, then casts by ascending mana value,
  all in precombat main; instants in the declare-blockers step if the active
  seat attacked that turn, else precombat main (own turn) / end step (other
  seat's turn). Attackers: the logged `creatures_attacked`. Blocks: the logged
  blockers and blocked attackers; the pairing (not logged) is the one whose
  predicted combat deaths (power vs toughness, deathtouch, menace legality) are
  closest to the logged `*_creatures_killed_combat`; ties are counted.
* Two rules use logged end-of-turn state rather than logged actions:
  (a) a land with a "sacrifice … search your library" ability (Terramorphic
  Expanse is in 673 of 2,000 user decks) that the engine still holds but the
  log's end-of-turn lands no longer do is cracked in the end step, fetching the
  basic the log gained; (b) a permanent that appears for the non-active seat
  without a logged cast is cast on that turn if the card has flash (only
  instants/sorceries are logged as casts on the other seat's turn).
* Everything else — targets, modes, "may" choices, payments, library searches,
  manifest dread, surveil, discard — is left to the `TestComputerPlayer` AI, as
  the plan specifies ("targets are not logged, so let the engine/AI choose").
  This is the **base** rebuild; the pre-stated readings are taken on it.
* A second, **guided** rebuild (`-Dl17.guide=true`, reported separately, not
  used for the go/no-go) steers hidden choices with logged outcomes, to measure
  how much of the loss is hidden choices: harmful targeted choices prefer a
  permanent the log says died non-combat that turn; manifest dread manifests the
  card the log shows arriving (swapped in from deeper in the library when it is
  not in the top two); user library searches take the card the log shows
  arriving; a logged draw found in the graveyard is put back on top.
* Check: at the first priority of every turn the previous turn's state is
  written (after cleanup): user life, opponent life, user lands / creatures /
  non-creatures in play (multisets of names, "A // B" reduced to "A", tokens
  by token name, face-down by card), user hand (multiset), opponent hand count.
  The game is replayed to its logged end; `analyze.py` walks the side-turns in
  game order and stops at the first one with any mismatch, which is the same
  count as stopping the engine there.
* **turns matched** = N−1 where `user_turn_N` or `oppo_turn_N` is the first
  side-turn with a mismatch (`num_turns` if none) — the unit of `num_turns`,
  so the ≥ 8 bar needs 8 complete rounds (about 16 side-turns). Labels are
  counted only in side-turns before the first mismatch. A side-turn "had more
  than one possible order" if the user played/cast ≥ 2 distinct cards in it.

### 3.1 Harness faults found in the 20-game debug (fixed before the 200 run)

1. `on_play` is stored as the string `'True'`/`'False'`; `bool('False')` is
   True, so every on-the-draw game was first built with the seats' turns
   swapped (all 12 on-the-draw games broke at user turn 1).
2. Life, mana and damage columns are filled for all 30 turns; a side-turn is
   real only if it has card lists or a non-0/0 life pair (and N ≤ `num_turns`).
3. Turn-1 draws on the draw were not stacked.
4. Tokens: the log names them ("Glimmer", rarity `token` in cards.json); the
   engine appends " Token". Also, token names must never enter the synthetic
   opponent deck (`addCard` throws on them).

5. **(Correction, found after the first 200-game run.)** 17Lands names a
   face-down permanent (manifest dread) `[Face-Down Card]` in attacker and
   blocker lists; the harness matched attackers/blockers by card name only,
   so every logged attack or block by a face-down creature failed (159
   failure records in the first 200-game run: 99 attacks, 57 blocks, 3 block
   assignments). The preliminary 200-game numbers committed in `0ef778d`
   (base median 2 turns, 0/200 ≥ 8) were produced with this fault and are
   superseded by §4, which reruns both rebuilds with the fix. The first
   2,000-game run was stopped at 131 games for the same reason and restarted.
   The v1 outputs are kept outside the repo (`/home/miketanto/l17run/v1_*`);
   the v1 per-game CSV is in git history at `0ef778d`.

### 3.2 20-game debug (development probe; 20 games is not a level)

| rebuild | median turns matched | ≥ 8 turns | fully matched | first-mismatch fields |
|---|---|---|---|---|
| base | 2.5 | 0/20 [0, 0.16] | 0/20 | user_creatures 6, oppo_life 4, user_life 3, oppo_hand 3, user_hand 3, user_lands 1 |
| guided | 3 | 0/20 [0, 0.16] | 0/20 | oppo_life 4, user_life 4, oppo_hand 3, user_creatures 3, user_hand 3, user_lands 2, user_noncreatures 1 |

Guided matched longer in 5 of 20 games and shorter in none. Per-game rows:
`rl/l17_dsk/fidelity_games_debug20{,g}.csv`; summaries `fidelity_summary_debug20{,g}.txt`,
`causes_summary_debug20.txt`.

## 4. 200-game run (seeded sample: `random.Random(17).sample(range(2000), 200)`)

Per-game rows `rl/l17_dsk/fidelity_games_s200.csv` (base) and `fidelity_games_s200g.csv`
(guided); summaries `fidelity_summary_s200{,g}.txt`; causes `causes_s200.csv`,
`causes_summary_s200.txt`. All 200 engine runs finished without error or timeout;
about 1 minute of wall time per 200-game rebuild under the caps. These are the
rerun after harness fault 5 (§3.1); the first run's preliminary numbers
(`0ef778d`) differed only slightly (mean 2.58 vs 2.60 turns matched).

| reading (base, 200 games) | value |
|---|---|
| median turns matched before first mismatch | **2** (mean 2.60; median turns logged 9) |
| games matching ≥ 8 turns | **0/200 = 0.000**, Wilson 95% [0.000, 0.019] |
| same, among the 143 games logged ≥ 8 turns | 0/143, [0.000, 0.026] |
| games fully matched to their logged end | 1/200 = 0.005, [0.001, 0.028] |
| turns-matched histogram | 1: 31, 2: 73, 3: 57, 4: 27, 5: 7, 6: 5 |
| most frequent first-mismatch field | **user_creatures** (59); then user_hand 43, user_life 36, oppo_life 28, oppo_hand 15, user_lands 13, user_noncreatures 5 |
| labels per game before the first mismatch | land 2.63, spell 1.68, attack 0.61, block 0.07 (total 5.00) |
| unambiguous share of those labels | land 0.417, spell 0.033, attack 1.000, block 0.933 (all 0.368) |
| user turns with more than one possible order | 1058/1759 = 0.601 (all logged user turns) |
| targeted user spells cast by the engine | 250 |

Guided rebuild on the same 200 games (hidden choices steered by logged
outcomes — 134 removal targets, 85 manifest dread picks, 84 library searches):

| reading (guided, 200 games) | value |
|---|---|
| median turns matched | 3 (mean 2.96) |
| ≥ 8 turns | 0/200 = 0.000, [0.000, 0.019] |
| fully matched | 1/200 |
| turns-matched histogram | 1: 22, 2: 53, 3: 65, 4: 38, 5: 16, 6: 5, 7: 1 |
| first mismatching field | user_hand 48, user_life 43, user_creatures 41, oppo_life 36, oppo_hand 15, user_lands 10, user_noncreatures 6 |
| labels per game / unambiguous share | 6.04 / 0.361 (land 2.99, spell 2.09, attack 0.85, block 0.11) |
| vs base, same games | longer in 45, shorter in 2, equal in 153 |

Steering hidden choices buys about a third of a turn on average and moves no
game near 8 turns; the most frequent first break moves from the user's
creatures to the user's hand and life totals.

### 4.1 All 2,000 games (base; the 200-game run finished well inside the 2-hour gate)

`rl/l17_dsk/fidelity_games.csv` (the requested per-game file; identical to
`fidelity_games_all.csv`), `fidelity_summary_all.txt`. 2000/2000 engine runs
ok, about 22 minutes of wall time under the caps.

| reading (base, 2,000 games) | value |
|---|---|
| coverage | 2000/2000 (§2) |
| median turns matched before first mismatch | **2** (mean 2.58; median turns logged 9) |
| games matching ≥ 8 turns | **1/2000 = 0.0005**, Wilson 95% [0.000, 0.003] |
| same, among the 1,409 games logged ≥ 8 turns | 1/1409, [0.000, 0.004] |
| games fully matched to their logged end | 15/2000 = 0.007, [0.005, 0.012] |
| turns-matched histogram | 0: 8, 1: 336, 2: 702, 3: 569, 4: 265, 5: 85, 6: 25, 7: 9, 8: 1 |
| most frequent first-mismatch field | **user_creatures 634 (0.317)**; user_hand 456, oppo_life 278, user_life 277, oppo_hand 161, user_lands 131, user_noncreatures 48 |
| labels per game before the first mismatch | land 2.63, spell 1.64, attack 0.66, block 0.07 (total 5.00) |
| unambiguous share of those labels | land 0.438, spell 0.028, attack 1.000, block 0.993 (all 0.387) |
| user turns with more than one possible order | 10221/17433 = 0.586 |
| targeted user spells cast by the engine | 2,414 |

The 200-game sample was representative: every reading agrees with §4 within
its interval.

## 5. Why the replay breaks (base, 200 games; `rl/l17/causes.py`)

One cause per game with a mismatch (199 of 200), first rule that applies:
a forced logged action failed on the mismatching turn or the one before →
the replay had already drifted in state the check does not compare
(graveyard, library, exile, counters, tapped status); the guided run went
further → a hidden choice; the side-turn logs an ability id for the seat that
broke → an activated or triggered ability; otherwise the field.

| cause (base, 199 mismatched games) | games | share |
|---|---|---|
| forced action impossible after unseen drift (logged draw already in the graveyard 11, cast not payable / activation failed 17, land or card not in hand 13, opponent card unavailable 7, attacker absent or tapped 4, blocker absent 3) | 55 | 0.28 |
| ability id logged on the breaking side-turn (activated abilities are not replayed, except fetch lands) | 54 | 0.27 |
| life total only (user 21, opponent 15) | 36 | 0.18 |
| hidden choice (the guided run matched longer) | 35 | 0.18 |
| other single fields (user creatures 10, hand 7, non-creatures 1, opponent hand 1) | 19 | 0.10 |

The classes are heuristic: "ability id logged" includes triggered abilities
the engine does replay, and "hidden choice" only counts choices the guided
rules cover, so it is a floor.

The three biggest causes, with an example each and what would fix them:

1. **Drift in state the check does not see, surfacing as an impossible
   forced action (0.28).** Game 167: on user turn 2 the engine's AI resolved
   Wary Watchdog's enter-the-battlefield surveil (verified in the card class)
   by putting Paranormal Analyst into the graveyard; the log draws and casts it
   on user turn 3, so the rebuilt turn 3 has it in neither hand nor play.
   Fix: steer every library-order choice (surveil, scry, mill "may"s) so the
   logged future draws stay in the library, and compare — or re-synchronise to
   — more of the logged state each turn instead of stopping at the first
   visible field.
2. **Activated abilities are not replayed (0.27).** Their ids are logged
   (about 9–10 per game per side) but not mapped to cards, so only fetch lands
   (which the logged lands determine) are replayed. Verified example, debug
   game 5: the opponent's Found Footage (sacrifice: surveil 2, draw a card)
   was used on the user's turn 2 — the log's opponent hand is 6, the rebuild's
   5. In the 200 run (games 10, 55, 102) the breaking side-turn logs an
   ability id whose card is not identified. Fix: download the 17Lands
   abilities table, map ability ids to (card, ability) and force them like
   casts (cycling-type draws, sacrifice effects, room doors, activated pumps).
3. **Hidden choices resolved differently by the AI (0.18 measured; a floor).**
   Game 36: Moldering Gym's search (verified: search library, put onto the
   battlefield) fetched an Island where the human fetched a Forest. Game 19:
   manifest dread turned a Plains face down where the human chose Fear of
   Falling. Fix: the guided rules (outcome-steered removal targets, searches,
   manifest dread) help in 45/200 games; steering surveil, "may" choices and
   modes from later logged draws and boards is the remaining part.

Life-only breaks (0.18) are the next class: combat and drain arithmetic after
guessed timing (combat tricks, flash blockers, the step an instant was cast
in) and triggers whose sources differ; game 39, user life 16 logged vs 19
rebuilt at opponent turn 4, mechanism not identified.

## 6. Go / no-go (pre-stated bar, `rl/L17-CLOUD.md` §3)

Bar: coverage ≥ 0.6 **and** ≥ 50 % of covered games match ≥ 8 turns.

* Coverage 2000/2000 = 1.000 [0.998, 1.000] — met.
* ≥ 8 turns matched: base 0/200 = 0.000, Wilson 95 % [0.000, 0.019] — the
  upper bound is 26× below the bar. Even restricted to the 143 games logged
  ≥ 8 turns: 0/143 [0.000, 0.026].

**Outcome: NO-GO** for building the rebuilder properly in this form. Per the
plan, the dominant mismatch is recorded (§5) and the work stops here.

Diagnostic spot checks on four 200-run games with unexplained mismatches
(games 36, 153, 100, 55) found engine-side / hidden-information causes, not
comparison faults: Moldering Gym's library search fetched a different basic
than the human (36, 153), a room door's play-from-exile effect and an
unforced mill choice produced cards the replay never saw (55), and Patchwork
Beastie's attack was refused by its own restriction because an unforced "may
mill" upkeep choice was declined by the AI (100). That last case exposed that a
refused attack declaration left no failure record; an `attack_rejected` record
was added (diagnostic only, no behaviour change) before the 2,000-game run.

## 7. What these numbers cannot support

* **Not a verdict on XMage's rules engine.** Most first mismatches are the
  replay drifting because information the log does not hold was guessed:
  within-turn order, targets, modes, "may" choices, library searches, manifest
  dread, surveil, which activated abilities were used (logged only as unmapped
  ability ids), and the exact step of instants and flash casts. A card
  implemented differently from Arena would look the same in these readings.
* **The opponent seat is reconstructed.** Its deck is synthetic (logged cards
  + basics), its hidden hand is swapped to contain what it casts, and its own
  hidden choices are the AI's. Opponent-driven mismatches (opponent life, hand
  count, removal targets) measure the reconstruction as much as the engine.
* **Order and targets are guessed.** 60 % of user turns had more than one
  possible order; the fixed order rule (land, then casts by mana value, all
  precombat) is wrong whenever a human cast post-combat, and every targeted
  spell's target is the AI's choice.
* **The unit is strict.** A single one-point life difference or one card
  differing anywhere in the compared state ends the count; nothing is
  tolerated or re-synchronised. A tolerant or re-synchronising rebuild (reset
  the state to the log each turn) would yield many more usable per-turn labels
  than this count suggests; this trial does not measure that.
* **Labels per game are a lower bound for a re-synchronising design** and an
  upper bound for this one: they count decisions before the first mismatch
  only, and "unambiguous" treats every attack as unambiguous (the attacker set
  is logged) while treating any spell in a multi-card turn as ambiguous.
* **The guided rebuild uses logged outcomes to steer hidden choices**; its
  gain is an estimate of how much hidden choices cost, not a fidelity a
  label-producing pipeline could claim without the same outcome information.
* **One set, strong players only** (win-rate bucket ≥ 0.58, ≥ 50 games), and
  the engine ran in local test mode (`TestPlayer`/`TestComputerPlayer`), not a
  server game.

## 8. Files and how to rerun

* `rl/l17/coverage.py` — step 2 (reads the Mage.Sets set classes directly).
* `rl/l17/build_specs.py` — game → spec (`G/H/L/A/K/B/D/P/Q/N/W` lines, format in its docstring).
* `rl/l17/L17Rebuild.java` — the replay (`CardTestPlayerBase` + `L17Player`), output `R/F/T/X/G/Z` lines.
* `rl/l17/analyze.py` — per-game CSV + summary; `rl/l17/causes.py` — cause classes, base vs guided.
* `rl/l17/run_l17.sh` — driver with the resource caps; `rl/l17/classpath.txt` — the Mage.Tests test classpath of the pinned build.
* `rl/l17_dsk/coverage_games.csv`, `fidelity_games_<tag>.csv` (the requested per-game file; tags
  `debug20`, `s200`, `all` = base, suffix `g` = guided), `fidelity_summary_<tag>.txt`,
  `causes_<tag>.csv`, `causes_summary_<tag>.txt`.

Rerun (inside WSL, run dir with `db/`, `config/`, `RB Aggro.dck` copied from `Mage.Tests`):

```
bash rl/l17/run_l17.sh s200 --sample 200 --seed 17
L17_GUIDE=1 bash rl/l17/run_l17.sh s200g --sample 200 --seed 17
python3 rl/l17/causes.py s200 s200g --out-base /home/miketanto/l17run/out_s200.tsv
```
