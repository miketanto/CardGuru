# Agent design: line-minimax MTG player (PokeChamp transposition)

Branch: `agent/pokechamp-minimax`. Companion to `pokechamp-mtg-agent-research-brief.md`
(the feasibility case); this doc is the build plan.

## Thesis

PokeChamp (arXiv 2503.04094) showed an untrained LLM reaches expert play when three
modules — action sampling, opponent modeling, leaf valuation — sit inside a shallow
minimax over a real simulator. We transpose it to MTG with one structural change:
**the search unit is a line, not an action.** MTG's priority system makes per-action
minimax intractable (mostly-trivial passes punctuated by combinatorial combat), but a
turn compresses into a handful of coherent plans. The claim we are building toward:
an agent whose harness is CardGuru's machine-mined knowledge graph beats both a raw
prompted frontier LLM and XMage's built-in AI — the repo's structured-beats-prose
thesis, extended from retrieval to play.

## Core loop (one decision)

```
game state
  → ENCODER        state → scenario-JSON prefix + prompt rendering
  → PROPOSER       LLM emits 3–5 candidate lines (scenario action scripts)
  → OPPONENT MODEL believed decklist → 2–3 likely response lines per candidate
  → SIMULATOR      strict-choose runner executes line × response × determinization
  → VALUE          LLM scores each resulting state over computed factors
  → CONTROLLER     minimax over the (line, response) matrix → play best line's next action
```

Depth-2 (my line, their best answer) — the effective depth PokeChamp ran at; they cite
lookahead depth, not module quality, as their ceiling.

## Why the existing adjudicator is already the simulator

Two facts from `docs/scenario-spec.md` / `cardguru/adjudicate.py` make Phase A cheap:

1. **A scenario encodes an arbitrary mid-game state** — per-player life, battlefield
   (with tapped), hand, graveyard, exile, `library_top`. So "simulate this line from the
   current board" = re-serialize the current state as a scenario whose `actions` are the
   candidate line and whose `stop` is the horizon. No new engine capability needed.
2. **The outcome JSON already returns the resulting state** (`state`: life, battlefield
   with P/T + tapped, graveyard, exile, hand_count), not just expectation pass/fails.
   The value function consumes driver output as-is.

Hidden information is handled PokeChamp-style by **determinization**: the opponent
model produces a believed remaining-list; we sample K concrete hands/library-tops from
it, run each rollout against each sample, and average values. (PokeChamp collapses
damage rolls to expected value; our stochasticity lives in draws and unknown hands
instead, so we sample rather than analytically average.)

`status:"error"` stays first-class: an unimplemented card or illegal line is a rollout
that returns "invalid," and the proposer resamples — the same fallback discipline the
product already uses for adjudication.

## Driver changes (the only new Java)

| Change | Why | Size |
|---|---|---|
| **Server mode**: keep the JVM alive, accept scenario JSONs over a socket/stdin loop, emit outcomes | Batch mode pays ~40s maven+DB warmup; interactive search needs the ~0.1–12s marginal cost only. One JVM, `reset()` between rollouts — the batching path already does this per-batch | ~100 LOC in the runner + a thin client in `adjudicate.py` |
| **Richer state dump**: counters on permanents, remaining untapped mana sources, hand contents for the owning player, cards-in-library counts | Value-function inputs; hand_count alone loses information we legitimately have | ~40 LOC |
| **`stop` short-circuit on game over** + winner field in outcome | Lethal lines currently just… stop; the single most important value signal must be explicit | small |

Everything else is Python.

## New modules (all in `cardguru/`, following house style: stdlib-only, evidence-carrying)

- **`encoder.py`** — bidirectional: XMage outcome `state` (or live bridge state) ↔
  scenario player blocks; plus prompt rendering with *computed* annotations in the
  PokeChamp "turns-to-KO" spirit: clock (turns to lethal each way, via goldfish-style
  math), per-threat `answers.py` connect-verdicts for cards in hand, linchpin flags
  from the opponent's fingerprint graph.
- **`lines.py`** — proposer: prompt → candidate lines as scenario action arrays;
  client-side legality pre-screen (reuse `validate_scenario` + mana arithmetic) so
  obviously illegal lines are resampled before spending a rollout.
- **`believe.py`** — opponent model: archetype classifier over cards seen (prior = a
  meta decklist corpus, new `data/meta_decks/`), believed-remaining-list maintenance,
  determinization sampling, and response-line proposal (LLM prompted from their seat
  with the believed list — PokeChamp's perspective-flip, but with a far stronger
  information position: in a defined meta, ~6 seen cards ≈ the whole 75 known).
- **`value.py`** — leaf scorer: computed factor block (life trajectory, clock delta,
  board delta weighted by fingerprint centrality, answers spent vs held, cards drawn)
  → LLM verdict with the factors in the prompt, or — measure this — a hand-weighted
  linear score with **no LLM call at all** as the ablation arm. PokeChamp never ablated
  its value LLM; we should, and it's a paper contribution if the linear score holds up.
- **`play.py`** — controller: the loop above + match orchestration against an
  environment backend (`scenario` backend first; `mage-bench`/live-XMage backend later).

Every candidate line, rollout outcome, and value verdict is logged with its evidence —
same explainability contract as DSL search results. This is also the replay substrate:
`agent_bridge.py`'s ReplayClient pattern extends directly (deterministic everything,
model turn swappable, zero API spend on re-runs).

## Evaluation (before any live play)

1. **Puzzle suite** — curate "find the line" decision puzzles (lethal-on-board,
   correct blocks, counter-or-tap-out) from the 6,021 harvested XMage scenario records
   + hand-built ones. Graded by execution: does the agent's chosen line, run through
   the adjudicator, reach the winning `expect`? All-or-nothing, no string matching.
2. **A/B arms**, fixed model per comparison (house finding: model choice dominates
   interventions): (a) raw LLM, no tools, no search · (b) +CardGuru context, no search
   · (c) +search, linear value · (d) full stack. ≥7 seeds, exact permutation test.
3. **Matches** — vs XMage `COMPUTER_MAD`, then the mage-bench ladder for external
   Elo. 1v1 only; Commander politics is out of scope (breaks two-player minimax).
4. Fixed deck pairing first (one aggro–midrange Standard pairing), formats widen later.

## Milestones & kill criteria

- **M0 (spike, days):** driver server mode + encoder round-trip (state → scenario →
  run 0-action line → state′ ≡ state). *Kill:* if round-tripping real board states
  through scenario setup is lossy for common permanents (auras, counters, tokens),
  stop and fix the spec before anything else.
- **M1:** puzzle suite v1 (≥50 puzzles) + arm (a) baseline numbers. This alone is
  publishable data ("raw LLMs blunder X% of forced-win MTG positions").
- **M2:** proposer + simulator loop solving puzzles (arm c/d). *Kill:* if median
  decision latency exceeds ~60s with K=2 determinizations × 4 lines × 3 responses,
  cut determinizations before cutting search.
- **M3:** believe.py + full matches vs COMPUTER_MAD. Target: >50% win rate, then
  compare arms.
- **M4:** mage-bench integration + writeup. (Spike its custom-agent surface early —
  if the MCP bridge can't host our loop, our own driver extension carries matches too.)

## Cost model (rough)

Per decision: 1 proposer call + ~3 opponent calls + ~12 value calls (4 lines × 3
responses, K=1) ≈ 16 calls, most tiny; ~12 rollouts ≈ 4–15s engine time. A 15-turn
game ≈ ~10 real decision points/side → ~160 calls/game. Haiku-class models for
proposer/value keep a full 100-game A/B in single-digit dollars; replay makes
iteration on prompts free after the first collection.
