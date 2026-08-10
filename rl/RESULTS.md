# RL results — episodes to competence

Pin: XMage `7554968c` + two local patches (bounded `getAttackablePlayers`
scan; benchmark package). 4-core Xeon 2.8GHz, 15GB, JDK 21, torch CPU.
E0 encoder (fixed features), PPO (terminal-only reward, per-consult
discounting), IPC V1 synchronous. Deck: BenchBurn mirror. Eval: argmax,
fixed seed blocks disjoint from training (rolling gate 100 games @seed
950000; confirmation 500 games @seed 960000). Agent alternates
play/draw by episode parity.

## Throughput with the policy in the loop (milestones 2-3)

| Config | games/sec |
|---|---|
| random policy, in-process | 3.01 |
| random policy, socket IPC | 2.81 (**-6.6%** — V1 synchronous confirmed, no V2) |
| PPO training vs heuristic, 2 concurrent seeds | ~0.4-0.6 per seed (CPU inference + updates + JVM sharing 4 cores) |

## Task A — sanity gate (vs uniform-random opponent)

**PASSED at 512 training episodes: 93/100 eval wins (gate: 70%).**
Training batches reached 97% by update 16. The trained transcript shows
the burn gameplan reconstructed from terminal reward alone: hasty
threats deployed on curve, attacks every turn, all burn at the
opponent's face, lethal finisher at the first legal window.

## Task B — THE measurement (vs HeuristicPlayer, burn mirror)

Competence = >=55% over 500 eval games with 95% CI excluding 50%.

| Seed | rolling evals (100 games, by episodes trained) | 500-game confirmation | episodes-to-competence |
|---|---|---|---|
| 1 | 256: 0.70 | 0.648 (CI [0.61, 0.69]) | **256** |
| 2 | 256: 0.64 | 0.624 (CI [0.58, 0.67]) | **256** |
| 0 | 256: 0.00 -> 512: 0.71 | 0.652 (CI [0.61, 0.69]) | **512** |
| 3 | 256: 0.30 -> 512: 0.69 | 0.634 (CI [0.59, 0.68]) | **512** |
| 4 | 256: 0.00 -> 512: 0.55 -> **confirm FAILED 0.468** -> 768: 0.69 | 0.644 (CI [0.60, 0.69]) | **768** |

## THE HEADLINE

**Episodes to competence vs HeuristicPlayer (burn mirror, E0 + PPO,
terminal reward only): median 512, spread 256-768, 5/5 seeds passed.**
Confirmed win rates are tightly clustered (62.4-65.2%) despite 3x spread
in training time.

Notes:
- Seed 4's curve.txt says "episodes=1024" for its confirmation: the
  chunk script counts confirmation lines in its batch counter; actual
  training was 3 x 256 = **768** episodes. Recorded correctly here.
- Seed 4 also demonstrates why the 500-game CI confirmation exists: its
  100-game rolling eval hit 0.55 at 512 episodes but the confirmation
  scored 0.468 - a false gate that 100-game noise (+-10%) fully explains.
- Learning curves are bimodal: every slow seed sat at 0-30% until it
  found the aggressive line, then crossed the gate within a single
  256-episode window. No seed plateaued mid-range.
- Stalls: 0 across all training and eval runs (burn mirrors end).
