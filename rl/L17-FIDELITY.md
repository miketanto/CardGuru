# L17-FIDELITY — how faithfully XMage rebuilds 17Lands DSK games (one-set trial, 2026-09-15)

Plan and pre-stated readings: `rl/L17-CLOUD.md` §3 (not changed after seeing data).
Data: `rl/l17_dsk/DSK_top2000.jsonl.gz` (2,000 DSK PremierDraft games, strong players, seed 17).
Harness: `rl/l17/`. Results as text/CSV in `rl/l17_dsk/`.

Status: **engine, coverage and the 20-game debug done; 200-game run in progress.**

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

### 3.2 20-game debug (development probe; 20 games is not a level)

| rebuild | median turns matched | ≥ 8 turns | fully matched | first-mismatch fields |
|---|---|---|---|---|
| base | 2.5 | 0/20 [0, 0.16] | 0/20 | user_creatures 6, oppo_life 4, user_life 3, oppo_hand 3, user_hand 3, user_lands 1 |
| guided | 3 | 0/20 [0, 0.16] | 0/20 | oppo_life 4, user_life 4, oppo_hand 3, user_creatures 3, user_hand 3, user_lands 2, user_noncreatures 1 |

Guided matched longer in 5 of 20 games and shorter in none. Per-game rows:
`rl/l17_dsk/fidelity_games_debug20{,g}.csv`; summaries `fidelity_summary_debug20{,g}.txt`,
`causes_summary_debug20.txt`.

## 4. 200-game run (seeded sample: `random.Random(17).sample(range(2000), 200)`)

Preliminary (base rebuild only; guided and cause classification to follow).
`rl/l17_dsk/fidelity_games_s200.csv`, `fidelity_summary_s200.txt`.

| reading (base, 200 games, all engine runs ok) | value |
|---|---|
| median turns matched before first mismatch | **2** (mean 2.58; median turns logged 9) |
| games matching ≥ 8 turns | **0/200 = 0.000**, Wilson 95% [0.000, 0.019] |
| same, among the 143 games logged ≥ 8 turns | 0/143, [0.000, 0.026] |
| games fully matched to their logged end | 1/200 = 0.005, [0.001, 0.028] |
| turns-matched histogram | 1: 31, 2: 73, 3: 59, 4: 27, 5: 6, 6: 4 |
| first mismatching field | user_creatures 57, user_life 42, user_hand 41, oppo_life 30, user_lands 13, oppo_hand 11, user_noncreatures 5 |
| labels per game before the first mismatch | land 2.62, spell 1.64, attack 0.58, block 0.08 (total 4.92) |
| unambiguous share of those labels | land 0.421, spell 0.034, attack 1.000, block 0.938 (all 0.368) |
| user turns with more than one possible order | 1058/1759 = 0.601 (all logged user turns) |
| targeted user spells cast by the engine | 248 |
