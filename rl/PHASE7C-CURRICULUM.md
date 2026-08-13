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

| # | archetype | deck | agent WR (40g) | seeded Elo | blocks/opps |
|---|---|---|---|---|---|
| 1 | sweep | P7cSweepControl | .625 | 827 | 27/27 |
| 2 | tokens | M3SelesnyaTokens | .400 | 986 | 86/86 |
| 3 | wweenie | M3WhiteWeenie | .375 | 1004 | 77/77 |
| 4 | skies | M3BlueSkies | .275 | 1084 | 42/42 |
| 5 | redrush | M3RedRush | .225 | 1130 | 90/90 |
| 6 | ramp | M3GreenRamp | .175 | 1185 | 71/71 |

**The intuition-ordered guess would have been wrong.** The deck built to
punish committing a board — 8 sweepers and 8 counters — is the *easiest*
matchup in the pool, not the hardest. It cannot race a curve-out Dimir
draw, so its wraths mostly arrive after the game is already decided.
Green ramp, which simply presents bigger bodies, is the hardest. Any
schedule ordered by archetype folklore would have run this curriculum
backwards.

### Baseline reproduction (trained = 0)

| source | Elo | vs D0 | vs D1 | vs D1h |
|---|---|---|---|---|
| Phase 7 final (main session, 1024 eps) | 916 | .43 | .25 | .26 |
| this lane, trained=0 (same checkpoint) | **928** | .46 | .30 | .23 |

The frozen start re-rates to 928 here against 916 there — a 12-point
gap on 100-game probes, well inside the noise those probes carry (the
standing convention is that 100g probes flatter by ~.07 relative to
500g). The rebuilt environment reproduces the main session's
instrument, so the A/B against its mirror-PFSP arm is sound.

## The blocking metric, corrected

The kickoff names the never-blocks hole as the headline metric. The
instrument added this phase says that hole, as stated, does not exist.

At trained=0 the agent's block rate is **1.00 — on every deck measured,
including the mirror**: 121/121 opportunities over 100 mirror games,
and 27/27, 42/42, 71/71, 77/77, 86/86, 90/90 across the six archetypes.
It does not decline to block. It blocks every single time it is asked.

What is true is that it is *rarely asked*: 1.21 block opportunities per
game on the mirror. The agent attacks with its board and taps out, so
by the time blockers are declared it usually has no untapped creature
and the window never opens. Phase 7 read "never blocks" off transcripts
full of `unblocked` attackers and attributed to the policy what is
mostly a property of the matchup and of its own attack pattern.

The mechanism behind the 1.00 rate is visible in `StateEncoder`: at a
block window the pass candidate is `blank(T_PASS)` — an all-zero vector
with a single flag set — while every block candidate comes from
`forCombat`, carrying power, toughness and the full E2 identity block.
A head that has seen almost no block windows in training has no reason
to prefer the sparse vector, so it takes a block by default.

This reframes what the curriculum has to prove. The question is not
whether blocking appears — it is already saturated — but whether deck
diversity produces *selective* blocking: a rate that moves off 1.00 in
the direction of good blocks, and more opportunities created by
choosing to hold creatures back. Both are tracked at every checkpoint.

## Results

### Mirror growth curve (BenchDimir, 100g vs each anchor, seed 950000)

| trained | Elo | vs D0 | vs D1 | vs D1h | block rate | opp-turn casts |
|---|---|---|---|---|---|---|
| 0 | 928 | .46 | .30 | .23 | 121/121 = 1.00 | 0 |
| 512 | 1012 | .60 | .35 | .36 | 126/126 = 1.00 | 3 |
| 1024 | **1059** | .65 | .42 | .43 | 112/112 = 1.00 | 1 |

For scale, the Phase 6 leaderboard: D1h 1088, D1 1085, e0_champ 1083,
attn_desp 1053, attn_bc 1044, attn_v2 1039, D0 1000, e0_bc 995. At 1024
the agent has passed every learned agent in the project and sits ~25
points under the scripted instruments.

### Robustness matrix (100g vs D0 piloting each archetype, seed 951000)

The `0` column is the 40-game pre-flight screen (seed 952000); an
archetype only enters the 100g matrix once it has been introduced, so
the screen is its pre-training reference.

Bold = the archetype was in the training pool for that block. Plain =
zero-shot (introduced at that checkpoint, not yet trained against).

| archetype | 0 (40g screen) | 512 | 1024 |
|---|---|---|---|
| sweep | .625 | **.790** | **.840** |
| tokens | .400 | .500 | **.610** |
| wweenie | .375 | — | .540 |

### Blocking counter (blocks / opportunities)

| archetype | 0 | 512 | 1024 |
|---|---|---|---|
| mirror | 121/121 | 126/126 | 112/112 |
| sweep | 66/66 | 55/55 | 41/41 |
| tokens | (86/86 at 40g) | 214/214 | 174/174 |
| wweenie | (77/77 at 40g) | — | 191/191 |

### Realized opponent mix

| opponent | deck | chunks | share |
|---|---|---|---|
| sweep | P7cSweepControl.dck | 6 | 37.5% |
| tokens | M3SelesnyaTokens.dck | 4 | 25.0% |
| D1h | BenchDimir.dck | 3 | 18.8% |
| ck_0 | BenchDimir.dck | 2 | 12.5% |
| D0 | BenchDimir.dck | 1 | 6.2% |

Archetype chunks 10/16 (62.5%), mirror 6/16. The share drifts toward
the mirror as the agent's rating rises into the band where the mirror
ladder sits — PFSP is doing its job, and the 50% archetype floor keeps
the curriculum from being abandoned entirely.

### Reading at 1024

1. **The curriculum closed most of the gap Phase 7 could not.** Phase 7
   ended at 916 and concluded that its remaining ~130 points to the
   teacher-seeded agents needed "a much larger budget, stronger mid-tier
   opponents, or a BC init". Changing only the opponent *decks* bought
   +131 Elo in 1024 episodes, past every learned agent in the project.
   Read against Phase 7's own slope over the same span — 889 → 916,
   +27 — the curriculum is roughly five times more productive per
   episode than more mirror self-play was.
2. **Robustness rises on every archetype, trained or not.** `wweenie`
   went .375 → .540 having never been a training opponent, and `tokens`
   gained .100 in the block where it *was* trained plus .100 in the
   block before it. Diversity is transferring, not just fitting the
   deck in front of it.
3. **Still no selective blocking.** 1.00 at every checkpoint on every
   deck. The block *denominator* keeps falling (sweep 66 → 55 → 41,
   tokens 214 → 174) while win rates rise, which says the agent is
   winning by racing harder and tapping out more, not by learning
   combat. The curriculum is buying general strength through a channel
   other than the one the kickoff hypothesised.

### Reading at 512

1. **There is no diversity tax so far — the opposite.** The agent spent
   six of eight chunks on a non-mirror deck and its *mirror* rating rose
   84 points, from 928 to 1012, clearing the D0 anchor. The kickoff's
   framing ("at what cost to mirror Elo?") anticipated a trade; through
   512 episodes there is no trade to report. The gains are broad —
   +.14 vs D0, +.05 vs D1, +.13 vs D1h — not a single anchor moving.
2. **Robustness climbs on both introduced archetypes**, including the
   one it was not training against (`tokens`, .400 → .500 zero-shot).
3. **Blocking is still saturated at 1.00 everywhere.** No selectivity
   has emerged. The one thing that moved is the *denominator* on
   `sweep`: 66 opportunities → 55, i.e. the agent is tapping out more,
   not blocking better. Against `tokens` it faces 214 opportunities per
   100 games and takes all of them.
4. **Opponent-turn casts went 0 → 3**, the first movement on another
   Phase 7 hole, though 3 in 300 rating games is barely off zero.

## Verdict

*(pending — run in progress)*
