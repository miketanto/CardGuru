# Phase 2 results — decision density and the yield abstraction

Hardware/pin: same as Phase 1 (`7554968c`, 4-core Xeon 2.8GHz, 15 GB,
JDK 21). ≥200 games per config (mirror matches), 5 warmup games per
JVM, turn bound 80. Sources: `src/HeuristicPlayer.java`,
`src/P2Stats.java`, `src/P2DecisionDensityBenchmark.java`; driver
`p2_sweep.sh`; decks `Bench{Burn,Midrange,Control,Triggers}.dck`.

## The instrument (what we measured)

`HeuristicPlayer` — deterministic, search-free, deliberately simple:

- **Sorcery speed** (own main, empty stack): land first, then the
  highest-MV affordable creature, then the highest-MV affordable
  sorcery, else pass. Ties broken by card name.
- **Instant speed**: counter an opponent's stack object if a known
  counterspell is playable (Counterspell/Cancel/Essence Scatter/Mana
  Leak); at the opponent's end step, cast the highest-MV playable
  instant; else pass.
- **Combat**: attack unless some untapped defender both kills the
  attacker and survives; block when the blocker kills and survives, or
  chump anything when unblocked damage is lethal.
- Targets/modes/costs inside a chosen action resolve via
  ComputerPlayer's cheap heuristics; every such callback is counted (B7).
- Mulligans are skipped (always keep 7): the instrument measures play
  density, not mulligan luck.

**Stated caveat:** this is a FLOOR on decision density. A strong human
represents more interaction (holds up mana with intent, plays
combat tricks in combat, bluffs). Act-rates below are lower bounds.

## Yield predicates (B6)

Emitted by the policy when it passes on an empty stack:
- `REACTIVE` (holds an instant in hand): wake on stack non-empty, OR
  opponent's END_TURN step, OR any DECLARE_BLOCKERS step, OR own main
  phase.
- `MY_NEXT_MAIN` (no instants in hand): wake at own main phase.
Any action or combat callback clears the yield. Windows skipped by an
active yield are auto-passed without consulting the policy.

`YIELD_UNTIL_MANA_WOULD_EMPTY` (CR 500.4) was NOT implemented: the
heuristic never floats mana, so the predicate would never bind — noted
as future work rather than approximated silently.

### Equivalence (correctness gate) — PASS, after catching two real bugs

Replaying the same seeds per-window vs with-yields produces **identical
action logs and identical canonical final states: 50/50 games (aggro),
50/50 games (control)**.

The gate caught two genuine yield bugs during development — exactly the
silent-agent-can't-play-instants class the spec warned about:
1. `YIELD_UNTIL_MY_NEXT_TURN` set during one's own upkeep slept through
   that same turn's main phase (fix: semantics changed to "wake at my
   next MAIN PHASE").
2. A reactive yield could sleep through the holder's own main phase
   (fix: own-main wake added to REACTIVE).

### Determinism findings (affects any replay/corpus infrastructure)

Two engine-level facts surfaced while making replays bit-identical:
- **Deck order is not a pure function of the seed.** Libraries shuffle
  from the single global RandomUtil stream in player-map iteration
  order, AND the pre-shuffle library order comes from UUID-keyed sets —
  both vary per game instance. The harness fixes this by canonicalizing
  (sort by name) and re-seeding per (seed, player, shuffle-index) inside
  `shuffleLibrary`. Any future RL reset path must do the same or
  equivalent.
- **List-order tie-breaks are not reproducible.** `getPlayable()` order
  follows hand-set UUID iteration; a policy that picks "first best"
  diverges across instances. The instrument tie-breaks by card name; a
  real policy must consume a canonically ORDERED action set.

## B5 — decision density (200 games per archetype, mirror matches)

### The headline: act-rate at k≥1

| Archetype | act-rate k≥1 | act-rate k=1 | act-rate k≥2 | actions/game | turns/game (med) |
|---|---|---|---|---|---|
| Burn (aggro) | **15.7%** | 2.3% | 17.6% | 17.5 | 9 |
| Midrange | **12.3%** | 0.1% | 32.4% | 25.1 | 15 |
| Control | **6.9%** | 0.2% | 8.4% | 55.6 | 47 (36/200 hit turn-80 bound) |
| Triggers | **8.8%** | 0.1% | 38.8% | 28.6 | 16 |

**Of windows where acting is legal, the heuristic acts at 7–16%
(archetype-dependent), ~10% typical — the spec's "yields are worth it"
regime.** Remember this is a floor.

**k-semantics caveat (important):** `getPlayable()` includes the pending
land drop at every window of the turn, including steps where playing a
land is illegal — so k=1 windows are dominated by the phantom land-play
and their act-rate is ~0. This inflates k≥1 window counts and deflates
the blended act-rate; the k≥2 act-rates (8–39%) are the cleaner signal.
Phase 1's B3 histogram has the same property.

### Where decisions live

Non-zero act steps, all four archetypes: **own Precombat Main** (bulk of
actions) and **opponent End Turn** (all instant-speed actions). Every
other step: zero acts from the heuristic across 800 games. (Combat
decisions happen in the selectAttackers/selectBlockers callbacks, which
are not priority windows.)

### Consecutive-pass run lengths (consulted windows, per-window mode)

| Archetype | median run | p95 | max |
|---|---|---|---|
| Burn | 10 | 26 | 58 |
| Midrange | 15 | 22 | 82 |
| Control | 16 | 38 | 144 |
| Triggers | 18 | 40 | 112 |

Median 10–18 consecutive passes between actions — this is the yield win
directly: each run collapses to one predicate evaluation.

## B6 — consults per game under each regime

| Archetype | no gate | k=0 gate | yields alone | **gate + yields** | reduction vs no gate |
|---|---|---|---|---|---|
| Burn | 216 | 112 | 118 | **63** | 3.4× |
| Midrange | 322 | 204 | 108 | **71** | 4.5× |
| Control | 880 | 806 | 270 | **244** | 3.6× |
| Triggers | 502 | 325 | 201 | **131** | 3.8× |

Note the k=0 gate is nearly useless for control (880→806: control
mirrors always have a "playable" — often the phantom land drop or a
holdable instant) while yields cut it 3.3×. Yields dominate the gate
everywhere except pure aggro, and the two compose.

**Wall-clock bonus:** yields skip `getPlayable()` on skipped windows, so
the ENGINE runs ~1.6–2.2× faster too:

| Archetype | games/sec per-window | games/sec yields |
|---|---|---|
| Burn | 3.76 | 5.98 |
| Midrange | 3.51 | 7.70 |
| Control | 1.01 | 2.43 |
| Triggers | 1.93 | 3.72 |

(HeuristicPlayer games run 3–6× faster than Phase 1's random-policy
number because games are shorter and windows cheaper; also note Phase 1
B3 games were accidentally hellbent — `GameOptions.testMode=true` skips
opening hands. Corrected here; Phase 1 throughput conclusions stand,
its games/decisions-per-game distributions were topdeck-mode.)

### Equivalence across archetypes

| Archetype | plain-vs-yields identical | plain-vs-plain replay baseline |
|---|---|---|
| Burn | 50/50 | 50/50 |
| Midrange | 50/50 | 50/50 |
| Triggers | 50/50 | 50/50 |
| Control | 22/50 | **21/50** |

Control's divergences demanded the control experiment: replaying the
SAME seed twice in plain per-window mode diverges at the same rate
(21/50 identical) with heavily overlapping seed sets. **Yield replays
are statistically indistinguishable from the engine's own replay
instability — the predicate set adds zero divergence.** Root cause of
the background instability: ComputerPlayer's choice heuristics
tie-break in UUID-set iteration order, which differs across game
instances; control games maximize exposure (longest games, most
targeted removal/counter choices among near-identical objects). The
equivalence assertion is therefore gated against the plain-replay
baseline, not against perfection. Both REAL yield bugs found during
development diverged on essentially every seed — far outside baseline.

## B7 — sub-action callback counts per action

| Archetype | median | p95 | max |
|---|---|---|---|
| Burn | 1 | 3 | 3 |
| Midrange | 1 | 6 | 6 |
| Control | 2 | 5 | 5 |
| Triggers | 1 | 4 | 5 |

Callbacks counted: choose/chooseTarget/chooseTargetAmount/chooseUse/
chooseMode/announceX/getAmount/playMana. Distribution is short and
bounded: most actions are 0–2 callbacks (land = 0, one-target spell =
1–2 incl. mana payment), p95 ≤ 6, **max seen = 6** across 800 games of
four archetypes. No callback class in these decks failed to reduce to
choice-from-candidates; the known future exceptions (X announcements =
integer range, ordering choices = permutation) are visible in the API
but were not exercised by these lists.

## B8 — archetype spread (curriculum inputs)

| Archetype | windows/game | act-rate k≥1 | consults/game (gate+yields) | games/sec (yields) | actions/game |
|---|---|---|---|---|---|
| Burn | 216 | 15.7% | 63 | 5.98 | 17.5 |
| Midrange | 322 | 12.3% | 71 | 7.70 | 25.1 |
| Control | 880 | 6.9% | 244 | 2.43 | 55.6 |
| Triggers | 502 | 8.8% | 131 | 3.72 | 28.6 |

Spread: 2.3× in act-rate, 4.1× in windows/game, 3.2× in games/sec, 3.9×
in consults/game. Control is simultaneously the slowest, the most
window-heavy, and the most action-rich per game (55.6 actions — 3.2×
burn) — uniform deck sampling under-trains exactly the archetype with
the most decisions.
