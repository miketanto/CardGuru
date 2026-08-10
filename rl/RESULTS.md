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

| Seed | episodes to rolling gate | 500-game confirmation | episodes-to-competence |
|---|---|---|---|
| 1 | 256 (eval 0.70) | **0.648** (CI [0.61, 0.69]) — GATE_PASSED | **256** |
| 0 | >256 (eval 0.00 at 256; training batches 6-16%) | — | in progress |
| 2 | — | — | in progress |
| 3 | — | — | queued |
| 4 | — | — | queued |

Early observation (why the 5-seed protocol exists): identical
architecture and hyperparameters span 0% -> 70% eval at the same
256-episode budget depending on init seed.

<!-- CURVES -->
