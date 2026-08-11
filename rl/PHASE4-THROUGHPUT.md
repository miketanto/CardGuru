# Phase 4 M0 — throughput breakdown

Fixed workload: 50 episodes, BenchDimir mirror vs HeuristicPlayer v2,
seed block 950000, single lane unless stated, 4-core box. IPC
instrumentation added to the driver (RL|ipc line: round trips, mean
RTT, total in-consult time).

## The matrix

| condition | games/sec | consults/ep | mean RTT/consult | notes |
|---|---|---|---|---|
| (a) in-process random (engine+wrapper) | 0.843 | 92.5 | — | pure-engine baseline, THIS deck |
| (b) + socket IPC (server random mode) | 0.842 | 88.5 | 281 us | IPC total 1.2s of ~59s = **2%** |
| (c) + torch argmax inference (eval) | 1.136* | 44.8 | 2098 us | *not comparable: fresh ckpt plays short losing games |
| (d) + sampling + PPO updates (train) | 0.654 | 96.4 | 1620 us | training overhead ~22% |
| (e) 2 concurrent train lanes | 0.581 + 0.638 = 1.22 agg | — | — | **1.87x scaling**, ~7%/lane contention |

## The 4x gap, explained

Phase 3's "0.61 games/sec vs Phase 2's 2.36" compared different
workloads. Phase 2's 2.36 was the archetype MIX (burn games run ~3x
faster than Dimir control); Task C's 0.61 was Dimir-heavy TRAINING
plus eval batteries plus stall-bound control games. On the same deck:

- rollout-only socket throughput = **1.00x pure engine** (0.842 vs
  0.843) — the milestone gate (<=1.5x) is met with no changes;
- training mode costs 22% (torch single-sample forward ~1.3ms x ~4.8k
  consults + PPO update stalls every 32 episodes);
- two lanes scale at 1.87x — core contention is minor.

**Engine simulation is 87%+ of wall-clock in every configuration.**

## IPC V2 decision: NOT BUILT, and here is the arithmetic

Batched inference (N workers -> 1 server) can recover only the
inference slice: ~1.3-1.8ms per consult, ~90-160ms per game, against
an engine cost of ~1,190ms per game. Best case at this topology
(2-3 JVM lanes on 4 cores, JVMs are the core consumers) is a ~10-15%
aggregate gain, bounded by Amdahl on the 87% engine share. The
spec's own out ("report the breakdown even if you choose not to
optimize") applies: the profile shows V2 cannot pay until the engine
share shrinks or the box grows. Revisit if Track B moves to a
many-core machine.

## Budget implication for Track A (search opponent)

Search multiplies ENGINE decisions, not IPC. Phase 1 measured 647
engine decisions/sec/core; with 0.5ms copy + cheap static eval, a
node costs ~1-2ms. Per REAL opponent decision:
- D1=8 nodes: ~10-15ms — negligible
- D2=32: ~40-60ms — ~1.3-2x game slowdown on Dimir (~90 opp decisions)
- D3=128: ~0.15-0.25s — ~3-5x slowdown
- D4=512: ~0.6-1.0s — ~30-70s/game; a 500-game calibration is 5-10h

Consequence (recorded before the sweep): if wall-clock forces a cut,
drop D4 seeds first and say so — per spec section 9, prioritize D2-D3.

## Primary unit correction (spec §1) adopted

All Phase 4 numbers report CONSULTS as the primary unit. Phase 3
restated: burn competence ~32k consults (512 eps x ~63); Dimir control
~62k consults (256 x ~244) — the real deck is ~2x harder per the
corrected unit, not equal.
