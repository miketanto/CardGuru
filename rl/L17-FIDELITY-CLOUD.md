# L17-FIDELITY-CLOUD — rebuilding 17Lands DSK games in XMage: reproduction and five rebuilder variants (cloud instance, 2026-09-15)

Continues `rl/L17-FIDELITY.md` (the local session's trial, base result and
NO-GO) and `rl/L17-CLOUD.md` (plan and pre-stated readings). Branch
`data/l17-cloud`, branched from `data/l17-dsk` at `b2978ac`.

**The base result recorded in `rl/L17-FIDELITY.md` §4 and the pre-stated go/no-go
in §6 stand unchanged.** This document adds (1) an independent reproduction of
that base result on a from-scratch engine build, and (2) five named variants of
the rebuilder, each reported separately. Nothing here re-scores the go/no-go.

Status: engine built, base result reproduced, variants run.

## 1. Engine (step 1, from scratch)

Unlike the local run (`rl/L17-FIDELITY.md` §1, which compiled against an
existing `/home/user/mage` build because a `mvn install` would have disturbed a
running Phase 13 lane), this instance built the engine from nothing:

| | |
|---|---|
| JDK | OpenJDK 21.0.10+7 (Ubuntu 24.04) |
| Maven | 3.9.11 |
| XMage | `git clone https://github.com/magefree/mage`, `git checkout 7554968c96211009ad1f1208b83d6de8c2b7746d` (the pin) |
| patch | `git apply rl/engine-patches/phase9-engine.patch` — applied, 3 files (Combat, PlayerImpl, RandomUtil) |
| `phase12-mana-recopy.patch` | **not applied**; forward dry-run fails hunk 3 on PlayerImpl, as `rl/engine-patches/README.md` requires |
| overlay | `rl/xmage-src/*.java` → `Mage.Tests/.../benchmark/rl/`, `benchmark/xmage/src/*.java` → `.../benchmark/` |
| build | `mvn -q -T 1C -DskipTests -Dmaven.javadoc.skip=true install` — clean |
| box | 4 cores, 15 GB RAM, no GPU, no other job on the machine |

`rl/setup_engine.sh` ran unedited: its hardcoded `/home/user/mage` and
`/home/user/CardGuru` are this container's real paths.

Harness port: `rl/l17/classpath_cloud.txt`, regenerated here with
`mvn dependency:build-classpath` on `Mage.Tests`. It resolves to **the same 125
artifacts as the local `rl/l17/classpath.txt`** (`diff` after stripping the
`$HOME/.m2/repository` prefix is empty), so the rebuild runs against the same
dependency set, not merely a similar one. `rl/l17/run_l17_cloud.sh` is
`run_l17.sh` with the local box's resource caps removed (no shared training
job here): no `MemAvailable` gate, no `nice`, `-Xmx3g`, batches of 100.
No other change to the harness was made before the reproduction run.

## 1a. Step 2 — reproduction of the base 200-game rebuild

Same 200 games (`random.Random(17).sample(range(2000), 200)`), the unmodified
`rl/l17/build_specs.py` (the spec file it writes for the base run is
**byte-identical** to the one the local session built — verified with `diff`
after the variant code was added, which emits its extra lines only when a
variant asks for them), the unmodified `rl/l17/L17Rebuild.java` as of
`b2978ac`, the unmodified `rl/l17/analyze.py`. All 200 games finished `ok`, no
timeouts, about 3 minutes of wall time.

| reading | local (`rl/L17-FIDELITY.md` §4) | cloud (`fidelity_games_s200_cloud.csv`) |
|---|---|---|
| median turns matched | 2 | **2** |
| mean turns matched | 2.60 | **2.59** |
| games ≥ 8 turns | 0/200, Wilson [0.000, 0.019] | **0/200, [0.000, 0.019]** |
| same, among the 143 games logged ≥ 8 turns | 0/143, [0.000, 0.026] | **0/143, [0.000, 0.026]** |
| fully matched | 1/200 | **1/200** |
| turns-matched histogram | 1:31 2:73 3:57 4:27 5:7 6:5 | 1:30 2:76 3:55 4:29 5:5 6:5 |
| first-mismatch field | creatures 59, hand 43, life 36, oppo_life 28, oppo_hand 15, lands 13, noncre 5 | creatures 61, hand 43, life 36, oppo_life 29, lands 14, oppo_hand 11, noncre 5 |
| labels per game / unambiguous | 5.00 / 0.368 | 4.94 / 0.365 |
| user turns with > 1 possible order | 1058/1759 = 0.601 | 1058/1759 = **0.601** (identical; it is a property of the log) |

**Per-game: 193 of 200 games match the local `turns_matched` exactly.** The
seven that differ are games 252, 528, 688, 712, 822, 886 and 1348.

**Reason for all seven: the harness is not deterministic run to run, and these
are the games sitting on the boundary.** XMage's `RandomUtil` at the pin holds
an *unseeded* shared `java.util.Random` (`-Dmage.randomPerThread` is off by
default), and the AI that resolves every unforced choice draws from it; on top
of that, permanent and card UUIDs are freshly random each run, so any iteration
over a UUID-keyed map runs in a different order. Four independent cloud runs of
the same 200 games disagree with **each other** in 3–5 games, and with the local
run in 5–7 — the same band. Running the seven games eight more times gives the
distribution below; **every local value reappears in the cloud distribution**,
so none of the seven is a port difference:

| game | local | 8 cloud repeats |
|---|---|---|
| 252 | 1 | 1×7, 2×1 |
| 528 | 3 | 2×4, 3×4 |
| 688 | 5 | 3×5, 5×3 |
| 712 | 3 | 3×2, 4×1, 5×5 |
| 822 | 5 | 3×6, 5×2 |
| 886 | 3 | 2×1, 3×7 |
| 1348 | 3 | 3×1, 4×7 |

None of it touches the pre-stated readings: `≥ 8 turns` is 0/200 in every one
of the twelve cloud runs, and the median is 2 in all of them. The base result
and the NO-GO reproduce.

*What this reproduction cannot support*: it is a reproduction of the **harness**,
not an independent implementation of it. The same spec builder and the same
Java replay were used, so a systematic modelling error would reproduce
faithfully. What it does establish is that the engine build, the dependency
set and the platform are not what produced the base numbers.

## 1b. Cascading divergence is not what breaks the replay (step 3a, first half)

`rl/l17/cascade.py`, on the base run's own output. For each mismatched game it
compares the game turn of the first **failed forced action** with the game turn
of the first **state mismatch**.

| reading (base, 200 games, 199 mismatched) | value |
|---|---|
| first failed forced action strictly **before** the first state mismatch | **8/199 = 0.040**, Wilson 95 % [0.021, 0.077] |
| same turn as the first mismatch | 49/199 |
| **after** the first mismatch | 138/199 |
| no failed forced action anywhere in the game | 4/199 |
| when before: median lead | 3 side-turns |

This is the opposite of what the failure counts suggest. The base run records
322 absent attackers, 300 casts whose card was not in hand, and so on — but in
**96 %** of games the state has already visibly diverged by the time the first
one happens. The impossible forced actions are overwhelmingly a *consequence*
of divergence, not its cause, so a rebuilder that only made forced actions more
robust would be repairing symptoms. `rl/L17-FIDELITY.md` §5 assigned 0.28 of
games to "forced action impossible after unseen drift" using a looser rule (a
failure on the mismatching turn **or the one before**); that class is real, but
this sharper measurement says the drift is nearly always visible first in the
compared state itself, which is why the remaining variants attack choices,
abilities and the opponent seat rather than action robustness.

## 2. Pre-registration (written before any variant was run)

Per `CLAUDE.md` → "Ground rules for results": each variant states in advance
what it is expected to move and — the part that matters — what it **cannot**
move. A variant that moves a metric it was declared incapable of moving is a
bug to find, not a result to report.

Shared caveat for every row below: the *unit* is unchanged from the base run —
`turns_matched` = N−1 where side-turn N is the first with any mismatch in
{user life, opponent life, user lands, user creatures, user non-creatures,
user hand, opponent hand count}, counted in full rounds, so "≥ 8" is ~16
side-turns.

### a. `resync` — cascading divergence

Two separate things:

* **Cascade measurement** (no new run): the share of mismatched games whose
  first failed forced action (`F` line) occurs strictly *before* the first
  state mismatch. Computed from the base run's own output. Expected to move
  nothing — it is a reading, not a variant.
* **`resync` variant**: at the first priority of every turn, after the
  snapshot for the previous turn is written, the engine state is pushed to the
  logged end-of-previous-side-turn state — both players' life, the user's hand,
  the opponent's hand *size*, and both players' battlefields (remove engine-only
  permanents silently, add log-only ones with
  `CardUtil.putCardOntoBattlefieldWithEffects`). Tokens and `[Face-Down Card]`
  entries that the engine does not already have cannot be reconstructed from
  the log and are recorded as unmet.

  * Expected to move: **per-turn fidelity**, which is the point — the share of
    side-turns whose *end* state matches given a correct *start*. This is a
    different quantity from `turns_matched` and is reported as its own reading.
  * Expected NOT to move: the go/no-go readings. `turns_matched` is not
    comparable under resync (the state is overwritten each turn, so a "first
    mismatch" no longer means what it means in the base run) and is therefore
    **not reported** for this variant. Per-turn fidelity cannot be compared with
    any base-run number either; the base run has no such reading.
  * Cannot move, and must not: coverage; the opponent-seat caveat (its hand
    *contents* are still invented — only the count is logged, so a resync that
    fixes the count does not fix what it holds).

### b. `abil` — logged abilities

`rl/l17/ability_map.py` infers, from co-occurrence over all 2,000 games, which
**card** owns each logged ability id (217 of 278 ids accepted, 74.7 % of ability
occurrences; see §3.1). The rebuilder forces, once per logged occurrence, a
non-mana activated ability of a permanent or hand card of that name.

* Expected to move: the ~0.27 of base first-mismatches classified "ability id
  logged on the breaking side-turn" (`rl/L17-FIDELITY.md` §5). Concretely,
  opponent hand count (Found Footage-style draw abilities), user hand, and
  creature counts where an ability made or removed a body.
* Expected NOT to move: first mismatches at user turn 1–2, which are almost
  all before any ability is logged; the "life total only" class, except where
  the ability drains.
* **Cannot** move: anything for the 61 unmapped ids (25.3 % of occurrences),
  and it cannot pick *which* ability of a multi-ability card was used — the map
  identifies a card, not an ability. Where a card has more than one non-mana
  activated ability the rebuilder picks the first playable one, which is a guess.

### c. `choice` — hidden choices

Extends the existing `guided` steering (removal targets from logged non-combat
kills, manifest dread, library searches, draws rescued from the graveyard) with:
surveil / scry library-order choices steered so that cards the log shows being
drawn later stay in the library; and discards steered to the logged
`cards_discarded` column (rare in this sample: about 0.5 logged discards per
game, so it cannot carry the variant on its own). Mill is not a choice in these
cards and is not steered.

* Expected to move: the "drift in state the check does not see" class (0.28 of
  base first-mismatches), whose single biggest verified mechanism is a surveil
  putting a future logged draw into the graveyard (game 167). Also the measured
  "hidden choice" class (0.18, a floor).
* Expected NOT to move: within-turn ordering, opponent-seat hand contents,
  combat arithmetic.
* **Cannot** be claimed as a fidelity a label-producing pipeline would get: it
  steers using the logged *outcome*. It is a measurement of how much hidden
  choices cost, exactly as the base `guided` run was.

### d. `oppo` — opponent seat

The opponent's hand is logged only as a count. Base rebuild swaps the cards it
is about to use into its hand at its first priority of the turn. This variant
(i) sizes its hand to the logged count at every turn boundary rather than
keeping the size fixed, (ii) puts its instants/flash cards in hand a turn early
so they are available at instant speed, and (iii) casts its logged
instants/sorceries on the user's turn in the step the log's damage implies —
before blockers when the user attacked and the log shows a creature of the
user's dying non-combat that turn, otherwise at end of turn.

*(Implementation note added after writing the code, before running it: (ii)
turned out to be already true. The base harness swaps the opponent's cards into
its hand at its FIRST priority of the turn, which on the user's turn is the
user's upkeep — before the user's main phase — so its flash and instant cards
are already in hand at instant speed. Only (i) and (iii) are new in this
variant.)*

* Expected to move: `oppo_hand` and `oppo_life` first mismatches (28 + 15 of 200
  in the base run), and user creature counts killed by opponent removal.
* Expected NOT to move: `user_lands`, `user_hand` (the user's own draws and
  plays are forced from the log and do not depend on the opponent's hand).
* **Cannot** support a claim about the engine: the opponent deck is synthetic
  (logged cards + basic filler) and its hidden choices are the AI's. Improving
  this seat improves a reconstruction, not a measurement of XMage.

### e. `order` — within-turn order

The base rule is fixed: land, then casts by ascending mana value, all in
precombat main. 60 % of user turns had ≥ 2 distinct cards and so more than one
possible order. This variant tries orders consistent with the log's end state:
when a forced cast fails for a payment/timing reason, the remaining casts of
that turn are retried in the other orders (bounded search, at most 24
permutations per turn), and casts are allowed in the postcombat main phase when
the precombat attempt failed and the seat attacked that turn.

* Expected to move: the "cast not payable / activation failed" and "land or
  card not in hand" failure reasons (17 + 13 of 199 base cause rows), and the
  `unambiguous share` of spell labels only insofar as fewer games break early.
* Expected NOT to move: the ambiguity *count* itself — the share of turns with
  more than one possible order is a property of the log, not of the rebuilder,
  and must stay at 0.601. If it moves, that is a bug.
* **Cannot** determine the true order. Several orders can be consistent with
  the same end state; picking one that works is not evidence the human used it.

### Combined

`all` = `abil` + `choice` + `oppo` + `order` (not `resync`, which is a different
measurement). Reported on the same 200 games.

## 3. Step 3/4 — the variants on the 200 seeded games

All seven rebuilds below ran on the same 200 games, all 200 finishing `ok` in
each, on the same engine build. Per-game rows are
`rl/l17_dsk/fidelity_games_s200_<variant>_cloud.csv`.

| variant | median | mean | ≥ 8 turns (Wilson 95 %) | fully matched | vs base: longer / shorter | first-mismatch field (top 3) | labels/game | unambiguous |
|---|---|---|---|---|---|---|---|---|
| `base` | 2 | 2.59 | 0/200 = 0.000 [0.000, 0.019] | 1/200 | — | creatures 61, hand 43, life 36 | 4.94 | 0.365 |
| `guided` (the local run's variant, rerun here) | 3 | 2.96 | 0/200 = 0.000 [0.000, 0.019] | 1/200 | 46 / 3 | hand 46, life 44, creatures 42 | 6.03 | 0.360 |
| `abil` | 2 | 2.60 | 0/200 = 0.000 [0.000, 0.019] | 1/200 | 6 / 6 | creatures 59, hand 48, life 31 | 5.02 | 0.371 |
| `choice` | 3 | 2.94 | 0/200 = 0.000 [0.000, 0.019] | 1/200 | 44 / 3 | hand 47, life 43, creatures 42 | 6.01 | 0.360 |
| `oppo` | 2 | 2.60 | 0/200 = 0.000 [0.000, 0.019] | 1/200 | 4 / 2 | creatures 58, hand 44, life 37 | 4.99 | 0.367 |
| `order` | 2 | 2.59 | 0/200 = 0.000 [0.000, 0.019] | 1/200 | 5 / 4 | creatures 58, hand 43, life 38 | 5.00 | 0.370 |
| `all` (abil+choice+oppo+order) | 3 | 2.91 | 0/200 = 0.000 [0.000, 0.019] | 1/200 | 45 / 6 | life 48, hand 47, creatures 41 | 5.95 | 0.363 |

Labels per game by kind, and the unambiguous share of each:

| rebuild | land | spell | attack | block | total | unambiguous: land / spell / attack / block / all |
|---|---|---|---|---|---|---|
| `base` | 2.62 | 1.67 | 0.57 | 0.08 | 4.94 | 0.420 / 0.033 / 1.000 / 0.938 / **0.365** |
| `choice` | 2.98 | 2.08 | 0.84 | 0.11 | 6.01 | 0.381 / 0.038 / 1.000 / 0.955 / **0.360** |

The ambiguity denominator is unchanged in every variant — 1058/1759 = 0.601 of
user turns had more than one possible order — as pre-registered. It is a
property of the log.

**Read plainly: four of the five new variants move nothing.** `abil`, `oppo`
and `order` sit inside the run-to-run noise band established in §1a (two reruns
of the same configuration disagree on 3–5 of 200 games); their longer/shorter
columns (6/6, 4/2, 5/4) are that noise, not an effect. `choice` reproduces the
existing `guided` gain (about a third of a turn) and adds nothing measurable on
top of it. **No variant moves a single game to 8 turns**: the pre-stated bar's
numerator stays 0 in all seven rebuilds, so the NO-GO of `rl/L17-FIDELITY.md`
§6 is not disturbed by any of them.

### 3.1 Why each variant failed to move what it was supposed to move

**`abil` (expected to move the 0.27 "ability id logged" class).** The mapping
worked: `rl/l17/ability_map.py` traced 217 of 278 ability ids to an owning card
(74.7 % of all logged ability occurrences; 211 ids to a non-basic-land card).
The *replay* is what failed, and `rl/l17/AbilityKinds.java` says why:

| reading | value |
|---|---|
| mapped non-basic-land ability ids | 211 |
| …whose card has a non-mana **activated** ability in XMage at the pin | **44** |
| …17 ids whose "card" is a token name, not a card | 1,464 occurrences |
| share of mapped ability occurrences on a card that has one | **4,627/28,006 = 0.165** |
| activations the `abil` run actually performed | 286 |
| attempts that found no activatable ability (card on battlefield 1,510, in hand 412, in graveyard 384, in library 136) | 2,528 |

So **five sixths of the logged ability ids are triggered or static abilities**,
which the engine fires by itself — `*_abilities` is a log of abilities that
*resolved*, not of abilities the player *activated*. This is a correction to
`rl/L17-FIDELITY.md` §5 cause 2 ("activated abilities are not replayed", 0.27
of games): the class is real as a *co-occurrence* — the breaking side-turn does
log an ability id — but replaying the activated ones is not the fix, because
almost none of them are activated. The 0.27 figure should be read as "an
ability resolved on the turn that broke", which is nearly always true of any
turn past turn 3, not as a diagnosis.

**`choice` (expected to move the unseen-drift and hidden-choice classes).**
The steering fires: 134 removal targets, 103 surveils, 87 manifest-dread swaps,
82 library searches on the 200 games. It buys the same ~0.35 turns the existing
`guided` rebuild buys, and the surveil steering — added here specifically for
the one mechanism `rl/L17-FIDELITY.md` §5 verified by hand (game 167) — adds
nothing on top: `choice` 2.94 vs `guided` 2.96, a difference smaller than the
noise band. The reason is visible in the failure counts: `guided` already
rescues a logged draw out of the graveyard when it finds one there (78 rescues
in 200 games), so preventing the burial and repairing it afterwards are the
same repair.

*Correction, in the open:* the first `choice` run reported no surveil steering
at all and was identical to `guided` by construction. `TestPlayer.doSurveil`
and `TestPlayer.scry` delegate straight to the wrapped `TestComputerPlayer`
(which is `final`), so the `chooseTarget` the engine makes inside them is the
AI's and never reaches the harness's player; the hook on
`chooseTarget(Outcome, Cards, TargetCard, …)` was dead code. `L17Player` now
overrides `doSurveil` and `scry` themselves. The numbers in the table are from
the fixed run; the unfixed one gave mean 2.96, i.e. the fix changed nothing
measurable either.

**`oppo` (expected to move `oppo_hand` and `oppo_life`).** Sizing the
opponent's hidden hand to the logged count at every turn boundary does not
help: `oppo_hand` as a first-mismatch field goes 11 → 13 and as any field at
the first mismatch 23 → 27, both inside the noise. It also makes the hand
reconstruction fight itself — `no_spare_hand_grew` records go 87 → 144, because
trimming to the logged count throws out a card the swap then has to fetch
again. The count was never the binding constraint; the *contents* are, and the
log does not hold them.

*Correction, in the open:* the first `oppo` run was a large regression (median
1, `oppo_hand` the first mismatch in 176 of 200 games) because the sizing added
one for the turn's draw. It runs at the seat's first priority, which is the
**upkeep** — before the draw step — so no draw should be added. Fixed; the
table is the corrected run. The bug was caught by the pre-registration: `oppo`
was declared unable to move `user_lands` or `user_hand`, and the regression
showed up as `oppo_hand` swamping everything, which is not a result to write up.

**`order` (expected to move "cast not payable" and "card not in hand" failures).**
Leaving a failed cast pending and retrying it at every later priority of the
same turn, including the postcombat main phase, changes nothing: mean 2.59 vs
2.59. That is consistent with §1b — the impossible casts are downstream of a
state that has already diverged, so no ordering of them is payable.

## 4. Per-turn fidelity after resync (`resync`, the reading that does move)

`-Dl17.variant=resync`, same 200 games, all `ok`. At the start of every turn the
engine state is pushed to the logged end-of-previous-side-turn state — both
lives, the user's hand, the opponent's hand size, and both battlefields. Over
the 200 games: 3,414 resyncs, 996 permanents removed, 1,356 added, 1,340 hand
cards moved, and **177 unmet items** (a token or a `[Face-Down Card]` the engine
did not already have, which the log does not describe well enough to
reconstruct), leaving **3,313 of 3,466 evaluated side-turns (0.956) with a
provably correct start**.

`turns_matched` is **not reported** for this variant, as pre-registered: the
state is overwritten every turn, so "the first mismatch" no longer means what it
means in the base run.

| reading (`rl/l17/perturn.py`, `rl/l17_dsk/perturn_s200_resync_cloud.csv`) | value |
|---|---|
| side-turns whose end state matches, **given a correct start** | **1755/3313 = 0.530**, Wilson 95 % [0.513, 0.547] |
| same, over every evaluated side-turn | 1793/3466 = 0.517, [0.501, 0.534] |
| fields that mismatch (counting every mismatching field) | creatures 919, hand 594, non-creatures 469, opp life 387, opp hand 385, user life 365, lands 340 |

And, by how deep into the game the side-turn is (clean starts only) — this is
the shape that matters:

| side-turns | per-turn fidelity (Wilson 95 %) |
|---|---|
| 1–2 | 400/400 = **1.000** [0.990, 1.000] |
| 3–4 | 367/400 = **0.917** [0.886, 0.941] |
| 5–6 | 284/400 = **0.710** [0.664, 0.752] |
| 7–8 | 212/393 = **0.539** [0.490, 0.588] |
| 9–12 | 259/740 = 0.350 [0.316, 0.385] |
| 13–16 | 138/526 = 0.262 [0.227, 0.302] |
| 17+ | 95/454 = 0.209 [0.174, 0.249] |
| **1–8 pooled** | **1263/1593 = 0.793** [0.772, 0.812] |
| **9+ pooled** | **492/1720 = 0.286** [0.265, 0.308] |

This is the one place the picture changes. Whole-game replay reaches a median of
2 rounds and never 8; **one-turn replay from a correct start is right about 4
times in 5 for the first eight side-turns and about 2 times in 7 after that.**
The decline is not drift — every one of these side-turns starts from the logged
state — so it measures how much *more* there is to get wrong per turn as boards
grow: more permanents with triggers, more targets to choose, more combat.

### 4.1 `resync` + `choice`: per-turn fidelity with hidden choices steered too

The `resync` row above uses the **base** decision rules inside each turn — the
AI still picks every target, manifest and search. Running `resync` and `choice`
together (`-Dl17.variant=resync,choice`) gives the ceiling this data can reach
per turn when the logged outcome is also used to steer those choices:

| side-turns | `resync` | `resync` + `choice` |
|---|---|---|
| 1–2 | 1.000 [0.990, 1.000] | 1.000 [0.990, 1.000] |
| 3–4 | 0.917 [0.886, 0.941] | **0.943** [0.915, 0.961] |
| 5–6 | 0.710 [0.664, 0.752] | **0.812** [0.771, 0.848] |
| 7–8 | 0.539 [0.490, 0.588] | **0.641** [0.593, 0.687] |
| 9–12 | 0.350 [0.316, 0.385] | **0.426** [0.391, 0.463] |
| 13–16 | 0.262 [0.227, 0.302] | **0.315** [0.277, 0.356] |
| 17+ | 0.209 [0.174, 0.249] | **0.282** [0.243, 0.324] |
| **1–8** | 0.793 [0.772, 0.812] | **0.850** [0.832, 0.867] |
| **9+** | 0.286 [0.265, 0.308] | **0.353** [0.331, 0.376] |
| **all** | 0.530 [0.513, 0.547] | **0.592** [0.575, 0.608] |

The intervals do not overlap at any depth past side-turn 2, so this is a real
effect and not the noise the whole-game variants produced. It is the same
steering that bought only a third of a turn in the whole-game rebuild: **the
gain from knowing the outcome is worth much more per turn than it is per game,
because in a whole-game replay one un-repaired divergence ends the count
anyway.**

## 5. The top three remaining causes

Taken on the side-turns that started from a provably correct state and still
ended wrong (1,558 of 3,313 in the `resync` run), so that drift is excluded by
construction and what is left is what one turn of replay gets wrong.

| class | share of failing clean side-turns |
|---|---|
| 1. a permanent differs — identity or presence | 1047 = 0.672 |
| 2. life totals only | 159 = 0.102 |
| 3. the user's hand only | 149 = 0.096 |
| 4. the opponent's hand count only | 114 = 0.073 |
| mixed / other | 89 = 0.057 |

**1. A hidden choice put a different permanent on the battlefield (0.672).**
Example, **game 19, user turn 5**: the log has *Fear of Falling* among the
user's creatures where the engine has a *Plains* — a manifest dread that turned
up a different card. No forced action failed on that turn and no ability id was
logged; the divergence is entirely the choice. Fix: the `choice` steering,
which is exactly what §4.1 measures — it lifts side-turns 5–6 from 0.710 to
0.812 — plus steering the choices it still does not cover (modes, "may"
triggers, which copy of a permanent an effect hits). Ceiling: whatever the log
does not name still cannot be steered, and a `[Face-Down Card]` never is.

**2. A target on a trigger changed the combat arithmetic (0.102).** Example,
**game 39, opponent turn 4**: the user's life is 16 logged, 19 rebuilt. The
turn logs ability id `174277`, which `rl/l17/ability_map.py` traces to *Friendly
Ghost* with coverage 1.00 — and `AbilityKinds` says that card's only ability is
an enters-the-battlefield **trigger** that gives a target creature +2/+4. The
engine did fire the trigger; the AI aimed it at a different creature, so a
different body survived combat and 3 damage landed elsewhere. Fix: steer
trigger targets the way spell targets are already steered, using the logged
kills, the logged combat damage on each side, and the logged end-of-turn
toughness implied by which creatures died. Ceiling: the log records *that* a
creature died and how much damage each player took, not which permanent a pump
was aimed at, so this is inference from consequences and will be wrong whenever
two targets produce the same end state.

**3. The opponent's hand is invented (0.073 as the only broken field, and it
also drives an unknown share of class 1).** Example, **game 55, user turn 8**:
the opponent's life is 25 logged, 26 rebuilt, with ability id `174430`
(*Glassworks // Shattered Yard*, a DSK room) logged that turn. Only the *count*
of the opponent's hand is logged, so the synthetic deck holds the cards it was
seen using plus basic-land filler, and everything it never visibly used is
wrong. The `oppo` variant shows the count is not the binding constraint (§3.1).
Fix: none available from this data — it would need the opponent's deck list,
which 17Lands does not log for the opponent. The honest move is to stop
comparing opponent-side fields and score only the user's seat, which would
remove this class and shrink class 1.

## 6. What these numbers cannot support

`rl/L17-FIDELITY.md` §7 applies unchanged; everything there is still true of
every variant here. The additions this work forces:

* **The opponent seat is reconstructed, and the `oppo` variant did not change
  that.** Its deck is synthetic (the cards it was seen using, plus basic-land
  filler), its hand contents are invented, and its hidden choices are the AI's.
  Forcing its hand *size* to the logged count moved nothing, which says the
  count was never what was wrong. Any reading that includes `oppo_life` or
  `oppo_hand` — including the per-turn fidelity of §4, where those two fields
  account for 385 and 387 of the mismatching fields — is partly a measurement
  of that reconstruction, not of the engine or of the log.
* **Order and targets are still guessed.** 60.1 % of user turns had more than
  one possible order and the `order` variant did not improve on the fixed rule;
  every target on every spell and every trigger is the AI's choice unless
  `choice` steers it, and `choice` steers it *using the logged outcome*.
* **The `choice` and `guided` gains are not fidelity a pipeline could claim.**
  Both use what the log says happened to decide what to do. The §4.1 ceiling of
  0.850 over side-turns 1–8 is an upper bound on a *reconstructor* that already
  knows the answer, not on a policy that does not.
* **The ability map is an inference, and it maps to a card, not an ability.**
  217 of 278 ids are accepted by a co-occurrence rule with a coverage threshold;
  the 61 rejected ids carry 25.3 % of ability occurrences and are unmapped. Even
  for an accepted id, the map names the owning card — which ability of that card
  it is remains unknown, and for 5 of 6 occurrences the card has no activated
  ability at all, so the id is a trigger and the map cannot say which.
* **Per-turn fidelity is measured with the log's own end state as the start.**
  The resync writes the logged lives, hands and battlefields into the engine; it
  cannot write graveyards, exile, counters, tapped status, or library order,
  because the log does not hold them. A side-turn that "started correct" started
  correct *in the seven compared fields*, and 4.4 % of side-turns could not even
  reach that (a token or face-down permanent the engine did not already have).
  The 0.530 and 0.592 figures are therefore optimistic about the start and
  strict about the end.
* **Silent removal is not a legal game action.** To rebuild a battlefield the
  resync yanks permanents off it without firing leave-the-battlefield triggers
  and puts logged ones on without enters-the-battlefield triggers
  (`CardUtil.putCardOntoBattlefieldWithEffects`, XMage's own cheat path). That
  is the right thing for a state reset and the wrong thing for a rules test: a
  card whose value is in its ETB or LTB trigger is silently mishandled at every
  resync boundary.
* **One set, strong players only**, `TestPlayer`/`TestComputerPlayer` in local
  test mode, not a server game. And: the harness is **not deterministic** —
  two runs of the same configuration disagree on 3–5 of 200 games (§1a), so no
  difference below about ±0.05 turns of mean is a result. Three of the five
  variants sit inside that band.

## 7. Label yield: what each design would actually produce

The point of the whole exercise is labelled human decisions. Over the 200
games, the log records **23.32 user decisions per game** (land 6.61, spell 8.57,
attack 6.25, block 1.90). How many survive each design:

| design | labelled decisions per game | share of all logged user decisions | unambiguous share |
|---|---|---|---|
| whole-game rebuild, `base` (decisions before the first mismatch) | 4.94 | 0.212 | 0.365 |
| whole-game rebuild, `choice` | 6.01 | 0.258 | 0.360 |
| **per-turn, `resync`+`choice` (decisions in side-turns that replayed correctly)** | **9.91** | **0.425** | — |

Per-turn resync roughly doubles the yield of the whole-game rebuild, and it
concentrates it where the replay is most trustworthy: side-turns 1–8, where
per-turn fidelity is 0.850 [0.832, 0.867].

## 8. Recommendation

**Full-game imitation from these logs is not viable. Per-turn labels after a
resync are, for the first eight side-turns only, and only as a *reconstruction*
that uses the logged outcome.**

The three findings that decide it:

1. **No rebuilder change gets whole games back.** Five variants, chosen to
   attack the causes the local run measured, in the order of their counts. Four
   moved nothing outside the harness's own ±0.05-turn noise, and the fifth
   reproduced a gain already known. `≥ 8 turns` stayed 0/200 — Wilson upper
   bound 0.019 — in every one of the seven rebuilds. The bar was 0.50. The gap
   is not a tuning gap.
2. **The whole-game framing was the wrong unit, and the cascade reading shows
   why.** Only 8 of 199 mismatched games [0.021, 0.077] fail a forced action
   before the state visibly diverges, so failures are symptoms; and one visible
   divergence ends the count regardless of what the replay gets right
   afterwards. The same steering worth ⅓ of a turn per *game* is worth 0.06 of
   fidelity per *turn* (§4.1) — the whole-game metric throws that away.
3. **Per-turn fidelity is a usable number, and it has a cliff.** Given a
   correct start, 0.850 [0.832, 0.867] of side-turns 1–8 replay correctly with
   outcome-steered choices, against 0.353 [0.331, 0.376] from side-turn 9 on.
   The cliff is not drift — every one of these turns starts from the log — it is
   board complexity, and it is where the remaining causes of §5 live.

What it would take to make the per-turn design real, in order of leverage:

* **Score only the user's seat.** The opponent's hand contents are unknowable
  from this data and its life and hand count are 772 of the mismatching fields
  in §4. Dropping `oppo_life` and `oppo_hand` from the comparison removes a
  class the data cannot fix, at the cost of no longer testing anything about the
  opponent. This is a half-day of work in `analyze.py` and `perturn.py`.
* **Steer trigger targets from consequences**, not just spell targets (§5, class
  2): use the logged kills, combat damage and survivors to pick the target of
  every triggered pump, removal and tap. Days, not weeks; it is the same
  machinery `chooseTarget` already uses.
* **Cap the label harvest at side-turn 8** (roughly the first 4 rounds) and
  state the cap. That is where 1,354 of the 1,964 correct side-turns are, and
  where fidelity is above 0.8.
* **Do not buy the abilities table.** The finding that changes the plan most is
  that the `*_abilities` column is a log of abilities that *resolved*, not of
  activations: only 16.5 % of mapped occurrences are even on a card with a
  non-mana activated ability. Downloading the real 17Lands ability table would
  replace an inference (coverage ≥ 0.90 over 2,000 games) with a fact, but it
  would not make the other five sixths replayable, because the engine already
  replays them.
* **Accept that this is a reconstructor, not a demonstrator.** Every number
  above past `base` uses the logged outcome to make choices. A dataset built
  this way teaches a policy what a human's *result* looked like with hindsight,
  and the honest way to use it is as a source of *state → action* pairs for the
  four logged decision kinds, never as a source of ground-truth play quality.

If the per-turn design is not worth that work, the alternative this trial
supports is: **stop**, and keep the 17Lands data for what it measures without
any engine at all — card win rates, deck composition, and the ~23 logged
decisions per game as features, none of which need a replay to be correct.

## 10. Files and how to rerun

New in this branch (`data/l17-cloud`), alongside everything in
`rl/L17-FIDELITY.md` §8:

* `rl/l17/classpath_cloud.txt` — the `Mage.Tests` test classpath of the
  from-scratch build here (same 125 artifacts as `classpath.txt`).
* `rl/l17/run_l17_cloud.sh` — driver without the local box's resource caps;
  `L17_VARIANT` selects the rebuilder variant.
* `rl/l17/run_variants_cloud.sh`, `rl/l17/run_all2000_cloud.sh` — the batteries.
* `rl/l17/ability_map.py` — ability id → owning card by co-occurrence →
  `rl/l17_dsk/ability_map_cloud.csv`.
* `rl/l17/AbilityKinds.java` — does that card have an activated ability? →
  `rl/l17_dsk/ability_kinds_cloud.csv`.
* `rl/l17/cascade.py` — first failed action vs first state mismatch →
  `rl/l17_dsk/cascade_<tag>.csv`.
* `rl/l17/perturn.py` — per-turn fidelity of a `resync` run →
  `rl/l17_dsk/perturn_<tag>.csv`.
* `rl/l17/build_specs.py`, `rl/l17/L17Rebuild.java` — extended with the five
  variants; **with no `--variant` / `-Dl17.variant` the base spec and the base
  behaviour are unchanged**, which is what makes §1a a reproduction.
* Per-game results: `rl/l17_dsk/fidelity_games_s200{,g,_abil,_choice,_oppo,_order,_all,_resync}_cloud.csv`,
  `perturn_s200_resync{,choice}_cloud.csv`, `cascade_s200_cloud.csv`, and the
  `all2000_*_cloud` files for the full-sample runs.

```
bash rl/setup_engine.sh                                   # step 1
bash rl/l17/run_l17_cloud.sh s200_cloud --sample 200 --seed 17          # step 2
python3 rl/l17/cascade.py  /home/user/l17run/spec_s200_cloud.tsv \
                           /home/user/l17run/out_s200_cloud.tsv --tag s200_cloud
python3 rl/l17/ability_map.py
bash rl/l17/run_variants_cloud.sh                         # step 3, all variants
bash rl/l17/run_all2000_cloud.sh                          # step 4, full sample
```
