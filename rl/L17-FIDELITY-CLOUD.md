# L17-FIDELITY-CLOUD — rebuilding 17Lands DSK games in XMage: reproduction and five rebuilder variants (cloud instance, 2026-09-15)

Continues `rl/L17-FIDELITY.md` (the local session's trial, base result and
NO-GO) and `rl/L17-CLOUD.md` (plan and pre-stated readings). Branch
`data/l17-cloud`, branched from `data/l17-dsk` at `b2978ac`.

**The base result recorded in `rl/L17-FIDELITY.md` §4 and the pre-stated go/no-go
in §6 stand unchanged.** This document adds (1) an independent reproduction of
that base result on a from-scratch engine build, and (2) five named variants of
the rebuilder, each reported separately. Nothing here re-scores the go/no-go.

Status: engine built; reproduction run and variants below.

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
occurrences; see §4). The rebuilder forces, once per logged occurrence, a
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
surveil / scry / mill library-order choices steered so that cards the log shows
being drawn later stay in the library and cards the log shows in the graveyard
go there; and discards steered to the logged `cards_discarded` column.

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
