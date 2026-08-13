# Phase 7c — archetype curriculum: does opponent deck variety buy robustness the mirror can't?

**Status: IN PROGRESS.** Setup, instruments and pre-flight are complete
and reported below; the growth curve, robustness matrix and blocking
counters are filled in as checkpoints land.

## Question

Phase 7 grew a scratch lstm+attention agent from 46 to 916 Elo in 1024
episodes on a Dimir *mirror* — the agent and its opponents all piloted
`BenchDimir.dck`. It ended with three named holes: it never blocks, it
over-activates Kaito's emblem, and it essentially never acts on the
opponent's turn.

This phase changes exactly one thing: **what the agent faces**. The
agent still pilots `BenchDimir.dck` in every game. The opponent seat
gets a widening pool of archetype decks, one introduced every 512
episodes, easiest-first. The main session continues the same start on
mirror-PFSP, so the two runs are a clean A/B from a shared frozen
checkpoint.

## Setup

- **Starting agent:** `/tmp/rl_p7_lstmattn_s0/p7_final.pt` (lstmattn,
  cdim 91, 429k params, Elo 916, 1088 episodes / 34 updates). Frozen
  artifact snapshot, restored from `rl/artifacts` via
  `rl/restore_artifacts.sh`.
- **Engine:** XMage pin `7554968c` + the bounded `getAttackablePlayers`
  patch, with `rl/xmage-src/` and `benchmark/xmage/src/` overlaid.
  Rebuilt from scratch this session (fresh container).
- **Training:** `rl/league_lane_p7c.sh` — BPTT recurrent PPO via
  `policy_server.py`, LR 3e-4 (per the kickoff), no yields,
  `consultBudget` 4000, 64-episode chunks, updates every 32 episodes.
- **Opponent selection:** `rl/pfsp_pick_p7c.py` — the Phase 7b
  optimistic weighting (target = self + 100, sigma 150, floor .02) over
  pool rows that now carry a deck as well as a kind.

### Engine changes this phase (mirrored into `rl/xmage-src/`)

1. **`-Drl.oppDeck`** — the opponent seat can pilot a different deck.
   Unset keeps the historical mirror behaviour, so every earlier runner
   is unaffected.
2. **Decks bind to seats, not to play order.** The pre-existing code
   assigned `deckA` to whoever was on the play, which silently handed
   the agent the opponent's list on every other episode. Invisible while
   every match was a mirror; wrong the moment decks differ.
3. **`blocksDeclared` / `blockOpportunities`** on `RLPlayer`. A raw
   block count cannot tell "refused to block" from "was never able to",
   so the counter ships with its denominator.

## Pre-flight

### Deck budget tests (4 episodes each, the M3 hard rule)

All six candidates ran clean at the pin — no OOM, no consult-budget
burn, no hang.

| deck | archetype axis | consults/ep | turns/ep |
|---|---|---|---|
| M3WhiteWeenie | mono-white small-creature aggro | 62.0 | 14.5 |
| M3RedRush | mono-red fast aggro with reach | 76.3 | 14.8 |
| M3SelesnyaTokens | go-wide tokens (blocking math) | 66.3 | 15.3 |
| M3BlueSkies | blue flash/tempo fliers | 69.3 | 14.5 |
| M3GreenRamp | green ramp, big top-end | 76.3 | 15.5 |
| P7cSweepControl | azorius sweepers + counters | 149.8 | 23.5 |

`P7cSweepControl` is new this phase (`rl/p7c_decks.py`): 4x each of
Omenspeaker, Essence Scatter, Wall of Frost, Cancel, Divination, Day of
Judgment, Wrath of God, Serra Angel, Windreader Sphinx, 13 Plains / 11
Island. It is the one axis the M3 pool has no deck for, and the only
one that punishes committing a board. It is built and verified by the
same pipeline M3 used (implemented at the pin, E2 features present,
hazard list audited) and it is twice the cost per episode of the aggro
decks, which is what a deck full of sweepers does to game length.

### Curriculum order

Ordered empirically rather than by assumption: each deck played the
frozen starting agent for 40 games (D0 pilot, argmax, seed 952000) and
the order is agent win rate descending — easiest first.

## Results

*(filled in as checkpoints land)*

## Verdict

*(pending)*
