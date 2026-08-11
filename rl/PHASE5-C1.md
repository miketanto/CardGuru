# Phase 5 C1 — imitation from D1: does the teacher's policy transfer?

## Question

Phase 4 ended with: terminal-reward PPO (~120k consults, 1280 episodes)
plateaus at .26–.42 vs D1 — the training SIGNAL, not the encoder, is
the ceiling. C1 asks how far pure supervised imitation of the D1 search
teacher gets on the same net (E0Policy, cdim 38), with zero RL.

## Setup

- Teacher: SearchPlayer D1 (1x8) — licensed by C0 (.482 head-to-head vs
  the honest D1ip over 500g; its policy is ~equivalent to an
  imperfect-info player's, so its demonstrations don't launder hidden
  information).
- Data: `TeacherLogPlayer` logs RLPlayer's exact (state, candidate)
  vectors at every consult surface (priority, attack, block, target,
  card picks), labeled with the teacher's actual action. 1,000
  teacher-vs-D1 episodes on the 4-deck training pool (seeds 12010000+),
  199,457 examples, **0 unmatched labels**. Teacher win rate in the
  generation games: .47–.55 by chunk (mirror-even, logging is inert).
  Composition ~95% priority windows (91.6% of those pass-labeled), the
  rest combat/targets.
- Training: `rl/imitate.py` — cross-entropy over the candidate softmax
  + value head regressed on per-consult-discounted terminal reward
  (gamma .997, PPO-compatible), 6 epochs, ~15 min CPU. Checkpoint is
  policy_server.py-format; eval served by the stock server
  (`rl/c1_eval.sh`).

## Results

Offline (5% episode-holdout validation):

| data | val acc | non-pass acc | atk / blk / prio / tgt |
|---|---|---|---|
| 341 eps (~64k ex) | .963 | .793 | .89 / .82 / .97 / .72 |
| 1000 eps (~199k ex) | **.968** | **.832** | .95 / .79 / .98 / .81 |

Online (argmax, 4-deck pool, fixed eval seeds; 500g CI ~±.04):

| matchup | games | win rate | stalls |
|---|---|---|---|
| student(341ep) vs D0 | 100 | .300 | 3 |
| student(341ep) vs D1 | 100 | .260 | 3 |
| **student(1000ep) vs D0** | **500** | **.412** | 32 |
| **student(1000ep) vs D1** | **500** | **.362** | 38 |
| teacher (D1) vs D0 (ref) | 500 | .776 | 0 |
| terminal-PPO plateau vs D1 (Phase 4 ref) | — | .26–.42 | — |

## Findings

1. **Pure imitation lands inside the PPO plateau band for a fraction of
   the interaction.** .362 vs D1 from 1,000 demonstration episodes and
   ~15 min of supervised training, vs .26–.42 after 1,280 PPO episodes.
   As a warm start it effectively buys the plateau for free.
2. **Behavioral cloning does NOT reach the teacher, and offline accuracy
   is the wrong lens.** 96.8% per-decision match still means
   0.97^73 ≈ 10% of episodes stay on the teacher's trajectory
   (73 consults/ep); once off-distribution the student has no signal —
   textbook covariate shift. The gap to the teacher is huge
   (.412 vs .776 against D0).
3. **Data scaling is positive but shallow.** 3x data bought ~+.10-.11
   online; extrapolating that slope to teacher parity is implausible
   before the compounding-error floor binds. More demonstrations are
   not the fix; interaction is.
4. New failure surface: the student stalls 6–8% of games (teacher: 0) —
   pass-heavy priors resurface off-distribution. Same liveness signature
   Task C flagged; worth watching in every later eval.

## BRANCH TAKEN: C2a — imitation-initialized PPO with potential-based
## shaping (Φ = GameStateEvaluator2)

C1's failure mode (off-distribution, no signal) and Phase 4's failure
mode (on-policy signal too sparse) are complementary; C2a attacks both:
start PPO from `student_full.pt` (its value head was fit to discounted
terminal reward for exactly this) and densify the reward with
potential-based shaping from the same evaluator the teacher searches
with — r' = r + gamma*Φ(s') − Φ(s), which preserves the optimal policy.
Java side emits Φ per consult (protocol bump, hello-validated both
sides). Gate for C2a: beat the plateau band decisively (>.45 vs D1 at
500g) and cut the stall rate; teacher-parity vs D0 (~.75+) is the
stretch mark.
