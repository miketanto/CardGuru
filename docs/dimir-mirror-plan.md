# Dimir mirror: prove the agent is the better pilot

## Context

Last night's campaign measured our Haiku pilot across five *different* deck
matchups (4W–11L overall). That design can't answer the question we actually
care about: every cell confounds pilot skill with deck strength, and the
results showed it — Dimir went 3–0 into stompy and 0–2 into prowess, which
tells us about the decks, not the agent.

A **mirror match removes the confound entirely**: same 60 cards on both
sides, so any deviation from 50% is piloting skill and nothing else. Dimir
midrange is the right mirror because it has the widest decision surface —
removal targeting and timing, counterspell windows, ninjutsu, surveil,
blocks, sequencing, and who takes the beatdown role.

Working mode is **1–2 games at a time**, reviewed by you before the next
run — so this plan optimizes for *per-game legibility*, not statistical
throughput. No overnight batches until you've judged enough games to say
the pilot is playing well. Statistical power comes later, and only once
the qualitative bar is met.

## Step 1 — Make the mirror a real mirror

**`benchmark/pilot_dimir_mirror.md`** (new, derived from the existing
`benchmark/pilot_dimir.md`). The current Dimir briefing tells the pilot its
opponent is Mono-Green Stompy ("no removal, no fliers") — in a mirror that
is actively harmful: it would walk spells into counterspells, over-commit
into removal, and misjudge blocks against fliers. The mirror briefing keeps
the deck section and replaces the opponent + tips sections with mirror
strategy:

- The opponent has *your* cards: Cut Down / Go for the Throat / Anoint,
  Three Steps Ahead, Deep-Cavern Bat, Preacher, Kaito, Sheoldred.
- Card advantage and Sheoldred decide long games; whoever runs out of
  answers first loses. Do not trade resources down without a reason.
- Someone must become the beatdown — usually whoever resolves the first
  threat the other can't answer. Fliers (Bat, Siren) are the real clock.
- Play around a counterspell when they hold {1}{U}{U} and around removal
  when they hold {1}{B}; bait with the second-best threat first.
- Deathtouch (Preacher) and flying blocks change combat math on both sides.

## Step 2 — Determinism, so a game can be re-run after a fix

Two small driver changes in `driver/CardGuruScenarioRunner.java`, both
plumbed through `cardguru/play.py` (`MatchClient._launch`) and
`benchmark/llm_bridge.py` as flags:

1. **Seed** — `-Dcardguru.seed=<n>` → `RandomUtil.setSeed(n)` before the
   game starts. **Measured result: this does NOT pin the opening hand.**
   Two sequential runs with seed 777 dealt different hands. Root cause:
   `Deck.getMaindeckCards()` collects the deck's ordered `LinkedHashSet`
   through `Collectors.toSet()`, so `PlayerImpl.init` builds the library
   from a `HashSet` whose iteration order follows each `Card`'s randomly
   generated UUID. The seeded shuffle applies the same permutation to a
   different starting order every run. Pinning the deal would require
   rebuilding the library in a canonical order (e.g. sorted by card name)
   after `init` populates it and before the shuffle — not yet done. Until
   then, treat every game as an independent sample and do not rely on
   `--same-seed` for A/B comparisons.

2. **Pin MAD's effort** — call `setMaxThinkTimeSecs(large)` on the seated
   `TestComputerPlayer7` in `createNewPlayer`, so the existing 5000-node
   cap (`MAX_SIMULATED_NODES_PER_CALC`) becomes the binding constraint
   instead of wall-clock. Today MAD's search is time-bounded at
   `skill * 3` = 18s, which means **the opponent gets weaker whenever the
   machine is busy** — results are not comparable across runs, and any
   future parallel batch would silently inflate our win rate. This makes
   opponent strength a property of the config, not the load.

## Step 3 — The per-game review loop (the actual deliverable)

**`benchmark/run_mirror.py`** (new, modeled on `run_campaign.py` but much
smaller): run N games (default 1) of `dimir_midrange` vs `dimir_midrange`
with `--search llm`, alternating who starts, export the playback replay via
the existing `replay_export.py`, and write results to
`research/data/mirror/`.

**`benchmark/review_game.py`** (new): turn one game log into a compact
review digest — every *non-forced* pilot decision (skip auto-passes, yields,
and single-option menus) rendered as: turn/phase, both boards, the options
offered, what the pilot chose, and its stated reasoning. This is the
mage-bench "blunder analysis" input, built from data we already log.

Each game then gets a review pass by a subagent reading that digest, rating
decisions **questionable / minor / moderate / major** with what it should
have done instead. I relay the result: outcome, replay link, and the
handful of decisions worth your judgment. Zero API cost — same
subscription-auth path the pilot uses.

## Step 4 — Fix what the reviews find (deliberately unspecified)

Do **not** pre-build more machinery. The obvious next candidate is
extending LLM-leaf search to *targets* (today, target sub-choices inside
rollouts fall to the built-in AI via the `searching` guard). Whether that,
briefing changes, or something unforeseen is what's actually costing games
should come from the reviews — that's the point of running 1–2 at a time.

## Files

- New: `benchmark/pilot_dimir_mirror.md`, `benchmark/run_mirror.py`,
  `benchmark/review_game.py`
- Modified: `driver/CardGuruScenarioRunner.java` (seed + think-time pin),
  `cardguru/play.py` (`MatchClient` seed/think-time params),
  `benchmark/llm_bridge.py` (`--seed`, `--opp-think-secs` passthrough)
- Reused as-is: `benchmark/pilot_daemon.py`, `benchmark/replay_export.py`,
  `benchmark/analyze_campaign.py`

## Verification

1. `python3 -m pytest tests/ -q` — 327 tests must stay green.
2. Compile the driver in the second checkout before any game runs:
   `cp driver/CardGuruScenarioRunner.java ~/Documents/mage-beliefs/Mage.Tests/src/test/java/org/mage/test/serverside/` then
   `mvn -q -pl Mage.Tests test-compile` in that checkout.
3. Seed check: run two games with the same `--seed` and confirm the pilot's
   opening hand is identical in both logs (compare the `mulligan` request's
   hand list) — this is the observable proof the seed binds.
4. Run one mirror game end-to-end; confirm the log has `leaf_eval` rows for
   both `attackers`/`blockers` and `priority`, no `fallback-timeout`, and
   that a replay HTML was written.
5. Generate the review digest for that game and sanity-check that forced
   decisions are excluded and each entry carries board state + reasoning.

## Out of scope for now

Cross-deck matchups (the confounded design), overnight batches, parallel
workers, and the statistical run. When you're satisfied the pilot plays
well, the pre-registered batch is a one-line change to the game count —
for reference, ~40 games detects a true 70% win rate at p<0.05, ~74 games
detects 65%, and ~158 detects 60%.
