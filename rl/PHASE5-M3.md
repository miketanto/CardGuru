# Phase 5 M3 — novelty sweep: does pool diversity move the E0/E2 gap?

## Question (from PHASE4-VERDICT)

The one live E0-vs-E2 differentiator after Task C / Phase 4 was
LIVENESS: the graph arm (E2) froze less on holdout decks, on average
but noisily per seed. M3 sweeps training-pool size (deck diversity) to
harden or kill that finding: does the freeze gap grow as identity
generalization gets harder?

## Setup

- 28 new verified decks (`rl/m3_decks.py`, `rl/m3_decks/`): mono +
  allied-pair archetypes, 4x9+24-basics template, every card verified
  implemented at the pin and present in e2_features.tsv. Three
  engine-safety substitutions found by OOM bisect (documented below).
- Nested pools P2 c P4 c P8 c P16 c P32 (bench 4 = core).
- Task C regime at v3: scratch terminal-PPO vs D0, FIXED 640-episode
  budget for every pool size (exposure-per-deck is the variable),
  arms e0 (cdim 38) / e2 (cdim 91), 2 seeds.
- Zero-shot holdout evals: 3 holdout decks x 200g @970000 per config.
  20 configs, 12,800 training episodes + 12,000 eval games.

Engine hazards found while standing up the 32-deck pool (all bisected
on the p32 mirror, all reproducible): **delve castability checking
(Gurmag Angler) enumerates graveyard subsets in getPlayable and
exhausts a 4.5G heap by midgame**; graveyard-recursion engines
(Reassembling Skeleton, Gravecrawler) + token copiers (Pack Rat)
were removed prophylactically; rl.consultBudget sysprop added (4000
for M3). Any future deck additions should audit for
delve/convoke-granting cards.

## Results (stall %% = freeze rate, zero-shot)

Pooled over all 3 holdouts x 2 seeds (1,200g per cell):

| pool | e0 freeze | e2 freeze | e0 win | e2 win |
|---|---|---|---|---|
| 2 | 3.1% | 2.0% | .367 | .452 |
| 4 | 4.2% | 3.8% | .407 | .432 |
| 8 | 6.4% | 2.8% | .398 | .457 |
| 16 | 1.2% | 1.8% | .340 | .328 |
| 32 | 5.8% | 2.2% | .313 | .337 |
| **all (6,000g/arm)** | **4.1%** | **2.5%** | **.365** | **.401** |

HoldoutControl (the known freeze surface) per-config spread: 0-24%
per 200g — seed noise remains large at config level.

## Findings

1. **The liveness advantage REPLICATES at v3, in direction and
   robustness: e2 freezes ~40% less, pooled over 6,000 games/arm**
   (2.5% vs 4.1%), and is the lower-freeze arm at 4 of 5 pool sizes.
   This is the third independent replication of the direction (Task C,
   Phase 4 pooled, now M3).
2. **The gap does NOT widen monotonically with novelty.** e0-e2 freeze
   gap by pool: +1.1, +0.4, +3.6, -0.6, +3.6 points - present but
   config-noisy, largest at p8/p32, one small reversal at p16. The
   "diversity amplifies the graph's liveness edge" hypothesis is NOT
   confirmed as a trend; the edge looks roughly constant-in-expectation
   with heavy seed variance, exactly Phase 4's caveat writ larger.
3. **NEW and unexpected: a pooled zero-shot WIN-RATE edge for e2**
   (.401 vs .365, 6,000g/arm - pooled CI ~ +-.012 per arm), the first
   win-rate daylight between the arms in the entire project, after
   four prior parity measurements. It concentrates at small pools
   (+.085 at p2, +.059 at p8) and vanishes at p16. Caveats before
   anyone headlines this: 640-episode budget (half the Task C/P4
   standard - the arms may converge with more training, consistent
   with all prior parity results), v3 instruments, 2 seeds per config.
   The convention gate (>=5 seeds) is NOT met at per-pool level.
4. Fixed-budget diversity tax: both arms' zero-shot win rates fall as
   the pool grows past 8 (exposure per deck halves each doubling).

## Verdict for the E0/E2 decision

The graph encoder's product story (fewer lock-ups on unseen decks)
survives its third and largest test. Its strength story remains
unproven at standard budgets but is no longer parity-everywhere:
the short-budget zero-shot edge is a concrete, cheap follow-up
(5 seeds x p2/p8, 640 eps, both arms) if the E0/E2 choice ever
becomes load-bearing. For everything Phase 5 measured, E0 remains the
default (cheaper, no feature pipeline), with E2 the pick where
liveness-on-novelty matters.
