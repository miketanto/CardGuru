# Phase 7c — Opponent deck diversity closes the gap four phases could not

**Branch:** `claude/cardguru-deck-curriculum` · **Full writeup:** `rl/PHASE7C-CURRICULUM.md`
**Cost:** ~9,200 training episodes, ~9,700 evaluation games, ~11h wall-clock on 4 cores.

## Question

Phase 7 grew a scratch lstm+attention agent to 916 Elo on a Dimir *mirror* and
stalled ~170 points short of the scripted search instruments, concluding the
remainder needed "a much larger budget, stronger mid-tier opponents, or a BC
init." Phase 4 had earlier concluded that terminal-reward PPO "cannot beat even
1-ply search," and that fixing it meant a better evaluator.

This phase changed exactly one thing: **which decks the opponents pilot**. The
agent still pilots BenchDimir in every game. Six archetype decks were introduced
one per 512 episodes, easiest-first, piloted by the scripted D0 seat.

## Headline result

**Opponent-deck diversity reached parity with the search instruments in 1536
episodes** — same architecture, same PPO, same terminal reward, same piloting
task. No evaluator work, no BC init, no budget increase.

| trained | 0 | 512 | 1024 | **1536** | 2048 | 2560 | 3072 |
|---|---|---|---|---|---|---|---|
| Mirror Elo | 928 | 1012 | 1059 | **1096** | 1040 | 1020 | 1046 |

For scale (Phase 6 leaderboard): D1h 1088, D1 1085, e0_champ 1083, attn_bc 1044,
D0 1000. At 1536 the agent passed every learned agent in the project and matched
the scripted search seats (head-to-head .48 / .49).

## Robustness, normalised for deck power

Raw win rates conflate deck strength, pilot skill and agent skill, so each deck's
power was measured separately (D0 vs D0, both seats equally competent; 100g).
Residual = agent performance beyond what deck power alone predicts.

| deck | power | baseline resid | final resid | change |
|---|---|---|---|---|
| redrush | .64 | −.18 | +.13 | **+.31** |
| ramp | .60 | −.27 | −.04 | **+.23** |
| tokens | .55 | −.09 | +.04 | +.13 |
| skies | .71 | −.06 | +.04 | +.10 |
| wweenie | .48 | −.19 | −.14 | +.05 |
| sweep | .49 | +.07 | +.09 | +.02 |

**Every residual improved, in rank order of how much creature combat the deck
demands.** The two decks that punish a tapped-out board hardest gained most, and
both were substantially zero-shot (.650 and .550 on introduction, from .225 and
.175). The near-creatureless control deck gained least. The mirror cannot produce
this — it never presents a Craterhoof or a four-token board.

**The trade:** mirror Elo peaked at 1536 and settled to 1046, still +118 over
baseline. What was surrendered is ~50 points of *mirror-specific* rating earned
by racing — correct on the mirror, wrong against creature decks.

## Two follow-up arms

**Specialists (equal budget, 6 × 512 episodes, one deck each).** Blocked practice
lost on its own terms: specialists were beaten **on the decks they specialised
in** by .154 on average (mean .448 vs the curriculum's .602), and five of six
finished at or below their own 928 starting mirror rating (896–947 vs 1046).
Diversity is not a tax paid for generality — it is the mechanism by which
anything is learned.

**Exploiters (nets trained to pilot each archetype against the frozen agent).**
Did not deliver the intended upper bound on opponent quality. All six landed in
.20–.40 regardless of deck while D0 spans .24–.51 — performance independent of
the tool, the signature of a pilot limited by its own 512-episode adaptation
budget from a mismatched (Dimir) prior. Establishes only the weak claim that
nothing *cheaply* exploits the agent.

## Three corrections to prior assumptions

1. **The "never blocks" hole does not exist as stated.** The agent blocks 100% of
   the time it is asked — all 34 probes, every checkpoint, every deck, including
   the mirror. It is rarely *asked*; the curriculum's real effect was raising
   opportunities (121 → 112 → 139 → 131), inverting exactly when mirror Elo began
   falling. Visible only because the counter shipped with its denominator.
2. **The D0 < D1 < D1h ladder is BenchDimir-specific.** D1 is a *worse* pilot
   than D0 on four of six archetypes (.43–.53 against a .62 mirror reference).
   Safe for every rating measured to date — all are on the mirror — but not
   portable to a cross-deck rating system.
3. **A latent driver bug was fixed:** decks were bound to play order rather than
   seats, which would have handed the agent the opponent's decklist on every
   other episode the moment decks differed. Invisible while every match was a
   mirror.

## Confidence and limits

- **Single seed** against the project's ≥5-seed convention. The Elo trend to 1536
  is large and monotone; per-checkpoint moves (~20 pts) and the noisier matrix
  rows are not individually reliable.
- **D1 parity is within 100g noise**, not a demonstrated lead.
- **The robustness matrix is a lower bound on opponent quality.** Every archetype
  row is D0-piloted and the exploiter arm failed to improve on that, so
  `sweep .76` means "beats D0 piloting control," not "handles control."
- **No single best checkpoint.** ck_1536 is the strongest mirror player; ck_3072
  the most robust. The choice is a product question.

## Recommended next steps, in cost order

1. **500g match vs D1 at ck_1536** — converts "parity within noise" into a
   result. Cheapest high-value follow-up by a wide margin.
2. **Replicate at 3–5 seeds** to meet the convention.
3. **A/B against the main session's mirror-PFSP arm** from the shared frozen
   start — the comparison this phase was designed as one half of.
4. **Random-init pilots trained to convergence per deck** (Phase-7 scale each) to
   get a genuine upper bound on opponent quality and lift the matrix caveat.

## Bottom line

Deck diversity was the one axis four phases never varied, and it outperformed
every axis that was varied. The recommendation is to treat opponent-deck
composition as a primary training-design variable rather than an evaluation
detail — and to re-examine any conclusion that was drawn from mirror-only
measurement, since the mirror systematically under-exercises combat.
