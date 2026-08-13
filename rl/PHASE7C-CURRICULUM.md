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

Generated from the lane's own log lines by `rl/p7c_report.py`.

### Mirror growth curve (BenchDimir, 100g vs each anchor)

| trained | Elo | vs D0 | vs D1 | vs D1h | blocks/100g | block opps | block rate |
|---|---|---|---|---|---|---|---|
| 0 | 928 | 0.4600 | 0.3000 | 0.2300 | 121 | 121 | 1.00 |
| 512 | 1012 | 0.6000 | 0.3500 | 0.3600 | 126 | 126 | 1.00 |
| 1024 | 1059 | 0.6500 | 0.4200 | 0.4300 | 112 | 112 | 1.00 |
| 1536 | 1096 | 0.6800 | 0.4800 | 0.4900 | 117 | 117 | 1.00 |
| 2048 | 1040 | 0.5700 | 0.4000 | 0.4400 | 139 | 139 | 1.00 |
| 2560 | 1020 | 0.5500 | 0.3800 | 0.3900 | 136 | 136 | 1.00 |

### Robustness matrix (100g vs D0 piloting each archetype)

| archetype | 0 | 512 | 1024 | 1536 | 2048 | 2560 |
|---|---|---|---|---|---|---|
| sweep | 0.7200 | 0.7900 | 0.8400 | 0.9200 | 0.8800 | 0.7700 |
| tokens | - | 0.5000 | 0.6100 | 0.6600 | 0.5800 | 0.6400 |
| wweenie | - | - | 0.5400 | 0.5300 | 0.5600 | 0.6100 |
| skies | - | - | - | 0.4700 | 0.5200 | 0.4700 |
| redrush | - | - | - | - | 0.6500 | 0.6600 |
| ramp | - | - | - | - | - | 0.5500 |

### Blocking counter by archetype (blocks / opportunities)

| archetype | 0 | 512 | 1024 | 1536 | 2048 | 2560 |
|---|---|---|---|---|---|---|
| sweep | 66/66 | 55/55 | 41/41 | 44/44 | 49/49 | 51/51 |
| tokens | - | 214/214 | 174/174 | 168/168 | 168/168 | 167/167 |
| wweenie | - | - | 191/191 | 188/188 | 188/188 | 193/193 |
| skies | - | - | - | 82/82 | 80/80 | 86/86 |
| redrush | - | - | - | - | 156/156 | 163/163 |
| ramp | - | - | - | - | - | 148/148 |

### Realized opponent mix (64-episode chunks)

| opponent | deck | chunks | share |
|---|---|---|---|
| tokens | M3SelesnyaTokens.dck | 13 | 32.5% |
| sweep | P7cSweepControl.dck | 6 | 15.0% |
| D1h | BenchDimir.dck | 4 | 10.0% |
| skies | M3BlueSkies.dck | 4 | 10.0% |
| ck_0 | BenchDimir.dck | 3 | 7.5% |
| redrush | M3RedRush.dck | 3 | 7.5% |
| attn_bc | BenchDimir.dck | 2 | 5.0% |
| ck_1024 | BenchDimir.dck | 2 | 5.0% |
| D0 | BenchDimir.dck | 1 | 2.5% |
| attn_desp | BenchDimir.dck | 1 | 2.5% |
| wweenie | M3WhiteWeenie.dck | 1 | 2.5% |

Archetype chunks: 27/40 (67.5%); mirror chunks: 13/40.

### Opponent calibration: deck power vs pilot skill

The matrix measures the agent against D0 piloting each archetype. Two
scripted-only controls (`rl/p7c_pilot_calib.sh`, 100g each) separate
what that number is made of.

**Deck power** — D0 piloting X vs D0 piloting BenchDimir, so both seats
are equally (in)competent and the gap is the deck. The Dimir mirror
returns .58 rather than .50, so read .58 as the empirical even point.

| deck | power | reading |
|---|---|---|
| wweenie | .48 | weaker than BenchDimir |
| sweep | .49 | weaker |
| tokens | .55 | about even |
| ramp | .60 | slightly stronger |
| redrush | .64 | stronger |
| skies | .71 | clearly stronger |

**Pilot skill headroom** — D1 vs D0 on the same deck, so the gap is the
pilot. BenchDimir returns .62, reproducing the .614 calibrated over
500g in Phase 5.

| deck | D1 over D0 | reading |
|---|---|---|
| wweenie | .69 | search helps — D0 underplays it |
| dimir | .62 | reference (reproduces .614) |
| ramp | .58 | roughly neutral |
| sweep | .53 | no help (and 12% stalls in the mirror) |
| tokens | .48 | search is *worse* than the heuristic |
| redrush | .44 | worse |
| skies | .43 | worse |

**The ladder is deck-specific.** D1 beats D0 on BenchDimir, the deck it
was calibrated on, and on `wweenie`. On four of the six archetypes it
is a *worse* pilot than the plain heuristic. Its 1-ply materialistic
evaluator appears to mis-serve precisely the decks whose value is not
in material trades — evasion, tokens, tempo.

Three consequences:

1. **There is no free pilot upgrade.** Repiloting the archetype rows
   with D1/D1h — the obvious cheap fix once D0's competence is in doubt
   — would have made four of six opponents measurably weaker.
2. **The robustness matrix is a lower bound on opponent quality**, not
   a ceiling. `sweep` at .92 says the agent beats *D0 piloting a
   control deck*; since neither scripted pilot can play that deck
   competently, it does not establish that the agent handles control.
   Settling that needs a trained pilot, which is what the exploiter
   lane is for.
3. **The Phase 6 Elo scale is safe but not portable.** All ratings are
   measured on the mirror, where the anchors are calibrated, so the
   growth curve is unaffected. But the anchors should not be assumed to
   carry their ordering onto other decks, which is what any future
   cross-deck rating system would want from them.

### Reading at 2560 — what the curriculum actually bought

Normalising each archetype for deck power makes the result legible.
Expected win rate = the agent's own mirror rate against D0, shifted by
that deck's power gap against BenchDimir (even point .58). The
*residual* is what the agent does beyond what deck strength explains.

| deck | power | base WR | resid | 2560 WR | resid | change |
|---|---|---|---|---|---|---|
| redrush | .64 | .225 | −.17 | .660 | +.17 | **+.34** |
| ramp | .60 | .175 | −.27 | .550 | +.02 | **+.29** |
| tokens | .55 | .400 | −.09 | .640 | +.06 | +.15 |
| wweenie | .48 | .375 | −.19 | .610 | −.04 | +.15 |
| skies | .71 | .275 | −.05 | .470 | +.05 | +.10 |
| sweep | .49 | .625 | +.07 | .770 | +.13 | +.06 |

**Every residual improved, and they improved in rank order of how much
creature combat the deck demands.** At baseline the agent was in
deficit against five of six decks, worst against `ramp` (−.27) and
`redrush` (−.17) — the two decks that punish a tapped-out board hardest.
Those two gained the most (+.34, +.29). `sweep`, the deck with almost
no creature combat and the only one the agent already beat above
expectation, gained the least (+.06).

That is the kickoff's hypothesis confirmed, in the form the evidence
actually supports. Deck diversity did force the skills the mirror never
demanded. It did *not* show up as the block rate moving off 1.00 —
that stayed saturated all run. It showed up as the agent learning to
have creatures available at all: mirror block opportunities rose
117 → 139 → 136 after declining for three checkpoints, and the decks
that reward holding a board are exactly the ones whose residuals moved.

**The trade, stated precisely.** Mirror Elo peaked at 1536 (1096) and
settled to 1020 — still +92 over the 928 baseline, so nothing regressed
below the starting point. What was given up was the *last 76 points* of
mirror-specific rating, earned by racing, which is the correct plan on
the mirror and the wrong one against creature decks. The `sweep` row
tracks the same trade from the other side: it peaked at .92 when the
agent was maximally aggressive and fell to .77 as it learned restraint,
because racing past a control deck before its wraths matter is precisely
the plan being unlearned.

### Reading at 2048 — the trade appears

The first regression of the run, and it looks like a genuine trade
rather than degradation.

Mirror Elo fell 1096 -> 1040 (-56): vs D0 .68 -> .57, vs D1 .48 -> .40.
Over the same block the robustness matrix went sideways to up —
sweep -.04, tokens -.08, but wweenie +.03, skies +.05 — and `redrush`
entered **zero-shot at .650**, against .225 on the pre-flight screen.
That is the largest transfer gain of the run, on a deck the agent had
never trained against and one of the strongest in the pool (.64 power).

The mechanism is visible in the block denominator. Mirror block
opportunities rose 117 -> 139, the first substantial increase after a
steady decline (121, 126, 112, 117). The agent is holding creatures
back instead of tapping out. On the Dimir mirror that is a *worse*
plan — racing is correct there, which is what the mirror rating
measures — while against creature decks it is what the kickoff hoped
the curriculum would force.

So the cost the kickoff asked about ("at what cost to mirror Elo?")
does exist, it just did not appear until the pool was wide enough to
outvote the mirror: 5 archetypes against 6 mirror rows. Through 1536
there was no trade to report; at 2048 there is one, and it is priced
at roughly 56 Elo for a broad archetype gain including +.43 zero-shot
on redrush.

The competing explanation is plain drift — LR 3e-4 is high for
fine-tuning a 916-Elo prior, and Phase 6 recorded league training
eroding the attention family's prior at 1e-4. Two things argue against
it: the decline is not uniform (three of five archetype rows rose),
and the block denominator moved in a specific, hypothesis-consistent
direction rather than randomly. The 2560 and 3072 checkpoints will
settle it — continued broad decline is drift, continued archetype gain
against a soft mirror is the trade.

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
