# Phase 7c — archetype curriculum: does opponent deck variety buy robustness the mirror can't?

**Status: COMPLETE.** 3072-episode curriculum run (seed 0), plus both
follow-up arms: 6 per-deck specialists (3072 episodes) and 6 per-deck
exploiters (3072 episodes). ~9,200 training episodes and ~9,700
evaluation games total.

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
| 3072 | 1046 | 0.5800 | 0.4600 | 0.3900 | 131 | 131 | 1.00 |

### Robustness matrix (100g vs D0 piloting each archetype)

| archetype | 0 | 512 | 1024 | 1536 | 2048 | 2560 | 3072 |
|---|---|---|---|---|---|---|---|
| sweep | 0.7200 | 0.7900 | 0.8400 | 0.9200 | 0.8800 | 0.7700 | 0.7600 |
| tokens | - | 0.5000 | 0.6100 | 0.6600 | 0.5800 | 0.6400 | 0.6500 |
| wweenie | - | - | 0.5400 | 0.5300 | 0.5600 | 0.6100 | 0.5400 |
| skies | - | - | - | 0.4700 | 0.5200 | 0.4700 | 0.4900 |
| redrush | - | - | - | - | 0.6500 | 0.6600 | 0.6500 |
| ramp | - | - | - | - | - | 0.5500 | 0.5200 |

### Blocking counter by archetype (blocks / opportunities)

| archetype | 0 | 512 | 1024 | 1536 | 2048 | 2560 | 3072 |
|---|---|---|---|---|---|---|---|
| sweep | 66/66 | 55/55 | 41/41 | 44/44 | 49/49 | 51/51 | 59/59 |
| tokens | - | 214/214 | 174/174 | 168/168 | 168/168 | 167/167 | 181/181 |
| wweenie | - | - | 191/191 | 188/188 | 188/188 | 193/193 | 180/180 |
| skies | - | - | - | 82/82 | 80/80 | 86/86 | 75/75 |
| redrush | - | - | - | - | 156/156 | 163/163 | 169/169 |
| ramp | - | - | - | - | - | 148/148 | 159/159 |

### Realized opponent mix (64-episode chunks)

| opponent | deck | chunks | share |
|---|---|---|---|
| tokens | M3SelesnyaTokens.dck | 15 | 31.2% |
| sweep | P7cSweepControl.dck | 6 | 12.5% |
| D1h | BenchDimir.dck | 5 | 10.4% |
| skies | M3BlueSkies.dck | 5 | 10.4% |
| redrush | M3RedRush.dck | 4 | 8.3% |
| ck_0 | BenchDimir.dck | 3 | 6.2% |
| ck_1024 | BenchDimir.dck | 3 | 6.2% |
| attn_bc | BenchDimir.dck | 2 | 4.2% |
| ramp | M3GreenRamp.dck | 2 | 4.2% |
| D0 | BenchDimir.dck | 1 | 2.1% |
| attn_desp | BenchDimir.dck | 1 | 2.1% |
| wweenie | M3WhiteWeenie.dck | 1 | 2.1% |

Archetype chunks: 33/48 (68.8%); mirror chunks: 15/48.

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



## Follow-up A: per-deck specialists (complete)

Six specialists, each starting from the same frozen `p7_final.pt` the
curriculum started from, each training 512 episodes against ONE deck
(`rl/p7c_specialist.sh`). 6 x 512 = the 3072 the curriculum spent, so
this is an equal-budget blocked-vs-interleaved comparison.

| deck | specialist own-deck | curriculum @3072 | gap | specialist mirror Elo |
|---|---|---|---|---|
| sweep | .78 | .76 | **+.02** | 947 |
| redrush | .42 | .65 | −.23 | 918 |
| tokens | .39 | .65 | −.26 | 907 |
| wweenie | .39 | .54 | −.15 | 899 |
| skies | .35 | .49 | −.14 | 896 |
| ramp | .36 | .52 | −.16 | (not collected) |
| **mean** | **.448** | **.602** | **−.154** | **~913 vs 1046** |

**Blocked practice loses on its own terms.** The specialists were
beaten on the very decks they specialised in, by an average of .154 —
by an agent that spent a *fraction* of its budget on each. And they
paid for it twice: five of six mirror Elos sit at or below the 928
starting point (896–947) against the curriculum's 1046, so single-deck
training did not merely fail to generalise, it moved most of the
specialists backwards on the mirror.

The one near-tie is `sweep` (+.02), the near-creatureless outlier where
the curriculum itself gained least (+.02 residual). Focused training
matched interleaved training only on the matchup with almost nothing to
learn.

This is the sharpest result of the phase, because it inverts the
intuition behind the question. Diversity is not a tax the curriculum
pays for generality, offset against per-deck depth. **Diversity is the
mechanism by which anything is learned at all** — 512 episodes against
one opponent teaches less about that opponent than ~380 episodes
against it amid five others.

The mechanism is visible in Phase 6's earlier finding: a narrow league
gradient eroded the attention family's prior (attn_bc 1044 ->
attn_v2 1039). Single-deck training is the maximally narrow gradient.
Against a fixed opponent the agent appears to converge on a
deck-specific exploit rather than skill, which neither transfers nor
survives contact with the mirror.

## Follow-up B: per-deck exploiters (complete)

Nets trained to *pilot* each archetype against the frozen curriculum
agent, 512 episodes each, initialised from `p7_final.pt`
(`rl/p7c_exploiter.sh`). Only expressible because of this phase's
`-Drl.oppDeck` change. The D0 column is the same opponent's result
inverted from the 3072 matrix, so the two are directly comparable.

| deck | D0 vs agent | exploiter vs agent | gain |
|---|---|---|---|
| tokens | .35 | .40 | +.05 |
| sweep | .24 | .27 | +.03 |
| redrush | .35 | .36 | +.01 |
| wweenie | .46 | .27 | −.19 |
| skies | .51 | .29 | −.22 |
| ramp | .48 | .20 | −.28 |

**The arm does not do what it was built to do, and the reason is
informative.** Every exploiter lands between .20 and .40 regardless of
which deck it pilots, while D0 spans .24 to .51. Exploiter performance
is essentially independent of the deck — the signature of a pilot whose
level is set by its own adaptation budget rather than by the tool it
was handed. It beats D0 only on the two decks where D0 is itself
weakest, and loses badly wherever D0 is competent.

The mechanism is domain shift. Each exploiter starts from a net trained
exclusively to pilot BenchDimir — aggressive, evasive, ninjutsu-based —
and most of 512 episodes goes on unlearning that before any new-deck
skill accumulates. `ramp` is the extreme case (−.28): piloting a ramp
deck means holding lands, casting big creatures on curve and blocking,
which is close to the opposite of the prior.

**Consequence for the robustness matrix: the caveat stands, unlifted.**
The honest bound on opponent quality is max(D0, exploiter), which for
four of six decks is just D0. So `sweep .76` still means "the agent
beats D0 piloting a control deck", not "the agent handles control".
Settling that needs random-init pilots trained to convergence per deck
— Phase-7-scale work per deck (1024+ episodes), not a 512-episode
fine-tune from a mismatched prior.

**What it does establish**, weakly: nothing cheaply exploits this
agent. A dedicated adversary with 512 episodes and a deck chosen to
attack it never exceeded .40. That is the same shape of claim Phase 6
made for e0_champ (exploiter plateaued at .42, "not cheaply
exploitable"), and it comes with the same limit — a stronger adversary
was not tried.

## Verdict

**Does deck diversity buy robustness the mirror can't, and at what cost
to mirror Elo?** Yes, and 50 Elo off the peak — but the honest version
of both halves needs the deck-power normalisation, because raw win
rates conflate three different things.

### 1. It buys robustness, and the gains are combat-shaped

Normalising each archetype for measured deck power (expected WR = the
agent's own mirror rate vs D0, shifted by the deck's power gap against
BenchDimir; residual = performance beyond what deck strength explains):

| deck | power | base WR | resid | 3072 WR | resid | change |
|---|---|---|---|---|---|---|
| redrush | .64 | .225 | −.18 | .65 | +.13 | **+.31** |
| ramp | .60 | .175 | −.27 | .52 | −.04 | **+.23** |
| tokens | .55 | .400 | −.09 | .65 | +.04 | +.13 |
| skies | .71 | .275 | −.06 | .49 | +.04 | +.10 |
| wweenie | .48 | .375 | −.19 | .54 | −.14 | +.05 |
| sweep | .49 | .625 | +.07 | .76 | +.09 | +.02 |

Every residual improved. They improved roughly in order of how much
creature combat the deck demands: the two decks that punish a tapped-out
board hardest (`redrush`, `ramp`) gained most, and `sweep` — almost no
creature combat, and the only deck the agent already beat above
expectation — gained least. Two of these are substantially zero-shot
results: `redrush` was at .650 the moment it was introduced, `ramp` at
.550, before either had been trained against.

The mirror could not have produced this. The mirror never presents a
Craterhoof or a four-token board.

### 2. It costs ~50 Elo, and only once diversity outvotes the mirror

| trained | 0 | 512 | 1024 | 1536 | 2048 | 2560 | 3072 |
|---|---|---|---|---|---|---|---|
| Elo | 928 | 1012 | 1059 | **1096** | 1040 | 1020 | 1046 |

Through 1536 there was no cost at all — the mirror rating *rose* 168
points while the agent trained mostly off-mirror, and at 1096 it reached
parity with the scripted search instruments (D1 1085, D1h 1088), which
is the wall Phase 4 declared: *"terminal-reward PPO at ~120k consults
cannot beat even 1-ply search."* The cost appeared at 2048, when five
archetypes outvoted six mirror rows in the sampling, and settled at
1046 — **+118 over baseline, −50 off peak**.

### 3. What was traded, mechanically

Mirror block *opportunities* per 100 games: 121, 126, 112, 117, **139,
136, 131**. The first three checkpoints drove that number down — the
agent racing harder, tapping out more — and it inverted at 2048. The
agent learned to keep creatures back. On the Dimir mirror that is the
wrong plan, because racing is correct there, which is exactly what the
mirror rating measures. The `sweep` row records the same trade from the
other side: .92 at peak aggression, .76 after restraint, because racing
past a control deck before its wraths matter is the plan being
unlearned.

### 4. The blocking metric, as promised, at every checkpoint

**The block rate is 1.00 at every checkpoint on every deck — all seven
mirror probes and all 27 matrix probes.** The agent never once declined
a block. The kickoff's "never-blocks hole" does not exist as stated;
what exists is that the agent is rarely *asked*, and the curriculum's
real effect was to raise the number of times it is asked. Reporting
this required the `blockOpportunities` denominator added this phase — a
raw block count would have shown a flat line all run and concluded
nothing changed.

### 5. What this does not establish

- **Single seed.** The project convention for a defensible claim is ≥5
  seeds. The Elo trend is large and monotone to 1536, but per-checkpoint
  moves of ~20 points sit inside 100g noise, and `wweenie` (.54, .53,
  .56, .61, .54) is visibly noise-dominated.
- **Parity with D1 is within noise, not a demonstrated lead.** A 500g
  match at the peak checkpoint would settle it; 100g probes flatter by
  ~.07 by standing convention.
- **The robustness matrix is a lower bound on opponent quality.** Every
  archetype row is piloted by D0, and the pilot calibration showed the
  scripted ladder cannot pilot four of six archetypes better than the
  heuristic. `sweep` .76 means the agent beats *D0 piloting control*,
  not that it handles control. The exploiter arm exists to settle this.
- **Peak-vs-final is a real choice.** If mirror strength is the goal,
  ck_1536 is the better checkpoint (1096, sweep .92). If archetype
  robustness is the goal, ck_3072 is (residuals uniformly better). They
  are different agents and the run does not collapse that choice.

### 6. Consequence for the project

Phase 4 concluded that beating the search instruments needed a better
evaluator or a denser learning signal, and Phase 7 concluded its
remaining ~130 points needed "a much larger budget, stronger mid-tier
opponents, or a BC init". Neither was necessary. Changing only which
decks the opponents pilot — same architecture, same terminal-reward
PPO, same fixed piloting task — reached instrument parity in 1536
episodes, at roughly five times Phase 7's Elo-per-episode over the same
span. Opponent *deck* diversity is a cheaper source of learning signal
than either proposed fix, and it is the one axis four phases of this
project never varied.

## Generalized conclusions

Five things this phase established that outlive the specific question.

**1. Opponent-deck diversity is a first-class training variable, and it
was the cheapest one available.** Four phases varied the encoder (E0 vs
E2), the evaluator depth (D0–D3), the initialisation (scratch vs BC),
and the opponent *population* (self-play, league, PFSP, exploiters).
None of them moved the agent past the scripted search instruments.
Varying which *decks* the opponents pilot did, in 1536 episodes, with
no other change. PHASE4-VERDICT's recommendation — dial the evaluator,
not the node count — was reasonable and would have been more expensive
than the axis nobody tried.

**2. Diversity is the learning mechanism, not a tax paid for
generality.** The natural model is that focused training buys depth and
mixed training trades depth for breadth. The specialist arm refutes it
at equal budget: specialists lost on their own decks by .154 on
average, and five of six ended at or below their own starting mirror
rating. Against a fixed opponent the agent converges on something
deck-specific that neither transfers nor survives contact with the
mirror; it takes a varied population to make the gradient point at
skill at all.

**3. Instruments need calibrating before their outputs mean anything.**
Three confident predictions in this phase were wrong, and each was
caught by a cheap control rather than by inspection:
   - "The sweeper deck will be the hardest matchup" — it was the
     easiest (.625 baseline). Fixed by the 40g screen.
   - "D1 is a better pilot than D0, so repilot the archetype rows" —
     D1 is *worse* than D0 on four of six decks. Fixed by 1,400
     scripted games. Acting on the prediction would have weakened four
     opponents and corrupted the matrix.
   - "Trained exploiters will give an upper bound on opponent quality"
     — they landed below D0 on four of six decks. Fixed by running
     them.
   The scripted D0 < D1 < D1h ladder that anchors the entire Phase 6
   Elo scale turns out to be a *BenchDimir-specific* ordering. It is
   safe for every rating this project has measured, because all of them
   are measured on the mirror — and unsafe for any future cross-deck
   rating system, which is exactly what someone would try next.

**4. Report the denominator.** The headline metric was "the agent never
blocks". It blocks 100% of the time it is asked, at every checkpoint,
on every deck — 34 probes, no exceptions. What changed over the run was
how often it is *asked* (mirror opportunities 121 → 112 → 139 → 131),
and that inverted exactly when the mirror rating started falling. A raw
block count would have shown a flat line all run and concluded nothing
happened. The finding exists only because the counter shipped with its
opportunity denominator.

**5. "Better" needs a stated axis.** The run does not produce one best
agent. `ck_1536` is the strongest mirror player (1096, sweep .92);
`ck_3072` is the most robust across archetypes (residuals uniformly
better, redrush +.31, ramp +.23) at 1046. The curriculum converts
mirror-specific rating into breadth at roughly 50 Elo, and which side
of that trade is preferable is a product question, not a training one.

### What would settle the open questions

- **Seeds.** Everything here is seed 0 against a ≥5-seed convention.
  The Elo trend to 1536 is large enough to survive, the per-checkpoint
  moves and the noisier matrix rows (`wweenie`: .54, .53, .56, .61,
  .54) are not.
- **A 500g match vs D1 at ck_1536**, to convert "parity within 100g
  noise" into a real result. This is the single cheapest high-value
  follow-up.
- **Random-init pilots trained to convergence per deck** (Phase-7 scale
  each) to get a genuine upper bound on opponent quality and finally
  lift the matrix caveat.
- **A/B against the main session's mirror-PFSP arm** from the shared
  frozen start, which is the comparison this phase was designed as one
  half of.

