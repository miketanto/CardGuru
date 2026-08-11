# Task D results — Dimir Midrange control mirror

The user's real 22-card Dimir Midrange v2 list (Kaito, Enduring
Curiosity, Rooms, transform, creature-lands), mirror match vs
**HeuristicPlayer instrument v2** — the v1 heuristic with We Say Thee
Nay!/Spell Snare/Spell Pierce added to its counterspell set so it
fights on the stack. v2 is a DIFFERENT yardstick: numbers here are not
comparable to the burn-mirror RESULTS.md.

Pin: XMage `7554968c` + local patches, same stack as Task B (E0
encoder, PPO terminal-only reward, IPC V1). Deck: BenchDimir.dck.
Eval: argmax; rolling gate 100 games @seed 950000; confirmation 500
games @seed 960000-960499 in five 100-game slices. Agent alternates
play/draw. Training in 64-episode chunks (games run ~8x slower than
burn: 0.36 games/sec random-policy, ~0.8 games/sec argmax eval).

## Smoke (10 random-policy episodes, pre-training)

0 crashes, 0 stalls, 31 turns/ep, 120 agent consults/ep,
fallbacks: chooseUse=61, announceX=3 across 10 games (Room doors,
ninjutsu, ward). Random-policy floor vs heuristic: ~30%.

## Episodes to competence (>=55% over 500 games, 95% CI excluding 50%)

| Seed | rolling evals (100 games) | 500-game confirmation | episodes |
|---|---|---|---|
| 0 | 256: 0.66 | 0.642 (CI [0.60, 0.68]) | **256** |
| 2 | 256: 0.70 | 0.656 (CI [0.61, 0.70]) | **256** |
| 3 | 256: 0.63 | 0.594 (CI [0.55, 0.64]) | **256** |
| 1 | 256: 0.49 -> 512: 0.56 -> **confirm FAILED 0.536** -> 768: 0.58 | 0.566 (CI [0.52, 0.61]) | **768** |

## THE HEADLINE

**Median 256 episodes (spread 256-768, 4/4 seeds confirmed) to beat
the v2 heuristic on the real Dimir Midrange control mirror.** The real
deck is NOT harder than the synthetic burn mirror for E0+PPO — same
competence point, same bimodal curves, similar confirmed win rates
(56.6-65.6% vs burn's 62.4-65.2%).

Notes:
- Seed 4 was deliberately skipped: after 4 seeds the distribution was
  already decisive and the marginal seed adds no information to the
  next decision (the graph A/B). Documented as a protocol deviation.
- Seed 1 produced the SECOND false gate caught by the 500-game CI
  confirmation (0.56 rolling -> 0.536 confirmed; burn seed 4 was
  0.55 -> 0.468). Two catches in ~9 uses: the confirmation stays.
- Stalls: 0 across all Dimir training and eval (~5,000+ games). The
  turn-80 bound never fired; games avg 19-31 turns.
- Fallback callbacks (Room door choices, ninjutsu/ward prompts) run
  ~2-6 per game, handled by inherited ComputerPlayer heuristics and
  counted in every summary line — the policy does not control them.
- Consult convention: agent-seat consults, ~54-120 per episode
  (vs ~30 on burn) — the decision-density gap Phase 2 predicted for
  control matchups is real and the stack handles it.
