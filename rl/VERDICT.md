# VERDICT — episodes to competence

## The headline

**Median 512 episodes (spread 256–768, 5/5 seeds) to beat
`HeuristicPlayer` on the burn mirror**, each seed confirmed at 62–65%
over 500 fixed-seed argmax games with 95% CIs excluding parity. At
measured single-core throughput that is **under 10 minutes of wall-clock
training per seed.** Terminal-only reward, E0 flat encoder, vanilla PPO,
synchronous IPC.

## What the number means (spec §9 decision table)

**"Task B under ~10k episodes → task is too easy; the real measurement
needs Control or a wider card pool."** That branch fired, two orders of
magnitude under the line. The correct reading is NOT "MTG RL is nearly
solved" — it is:

1. **The environment stack works end-to-end and is not the bottleneck.**
   Engine, wrapper filters, yields, IPC, PPO plumbing: all confirmed by
   an agent that actually learns through them.
2. **Burn-mirror-vs-heuristic is a shallow task.** The heuristic's known
   gaps (never blocks well against lethal races, casts instants only at
   end steps, no burn-allocation logic) are exploitable by a policy that
   masters race arithmetic — which E0 evidently can.
3. **Sample efficiency is not yet load-bearing at this task depth** —
   the Phase 1 fear (10^5 games barely enough) is refuted for this
   tier; the question re-opens at Control/held-out-card depth.

## Encoder ablation status

Per the spec's own prediction ("E0 likely matches E1/E2 on a fixed
20-card burn pool — the graph should only pay off on Task C"), and per
its instruction to STOP at milestone 5: **E1/E2 were not built.** E0
passing this fast strengthens the prediction; building the graph
encoders against THIS task would measure nothing. They should debut on
the harder task where generalization exists to measure.

## Recommendation

**Continue — but move the measurement, not the architecture.** Next
session should:
1. Port Task B to the **control mirror** (BenchControl vs the heuristic
   counterspell logic) and/or **Task C held-out cards** — that is where
   episodes-to-competence becomes the number the project actually needs.
2. Run the E0/E1/E2 ablation THERE (the ablation is the experiment).
3. Add trigger-ordering and X-announcement heads only when a deck
   forces them (spec §10 warning stands; burn never exercised either).
4. Keep the 500-game CI confirmation — it caught a false gate (seed 4,
   0.55 rolling vs 0.468 confirmed) within its first five uses.

## Projected cost to Task C

Control games run ~2.5x slower with ~4x the consults; if
episodes-to-competence scales an order of magnitude (5k-10k), a control
measurement is hours-per-seed on this 4-core box - still cheap. The
budget concern only returns if held-out-card generalization needs 10^5+
episodes, which is exactly what Task C will measure.

## Ranked surprises

1. **256–768 episodes to beat the heuristic** — expected thousands to
   tens of thousands; got hundreds. (Caveat repeated: floor-quality
   opponent on the shallowest archetype.)
2. **Bimodal learning curves** — seeds don't climb, they jump: 0–30%
   plateau, then through the gate inside one 256-episode window. Credit
   assignment finds "attack + face-burn" as a package, not gradually.
3. **A 100-game eval false-gated a seed** (0.55 rolling, 0.468/500
   confirmed) — rolling-eval noise is ±10% and would have corrupted the
   headline without the CI confirmation.
4. **Confirmed win rates cluster at 62–65% across all seeds** despite 3×
   training-time spread — the policy quality endpoint is stable even
   when the path is not.
5. **Infrastructure bugs outnumbered RL bugs ~5:1** — engine infinite
   loop (no live opponent), lost/left flags surviving player reuse,
   card-DB rebuild race, sandbox reaping detached daemons, surefire
   silently skipping FQN filters. The RL itself worked nearly first try.

## Conventions / caveats carried

- Episodes counts are TRAINING episodes (evals excluded); seed 4's
  script-reported "1024" is 768 actual (confirm lines inflate the
  script's batch counter — RESULTS.md table is authoritative).
- Agent-seat consult convention (M1) throughout.
- Opponent is a documented floor, unchanged from Phase 2; do not tune it.
- Pin: XMage 7554968c + two local patches (bounded getAttackablePlayers
  scan; benchmark/rl test packages).
