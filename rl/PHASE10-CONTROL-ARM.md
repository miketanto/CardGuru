# Phase 10 control arm — how to run it against this flagship

The flagship (`rl/p10_flagship.sh`) and its control arm differ in
**exactly one variable**: whether the agent's own deck rotates. Keep
everything else byte-identical or the A/B is not an A/B.

## The command

```bash
# same init, same pool, same gate, same cadences - rotation OFF
P10_DECK_SCHEDULE= \
P7_OUT=/tmp/rl_p10_control_s0 \
P10_APORT=7821 P10_OPORT=7822 \
bash rl/p10_flagship.sh 12288 0
```

`P10_DECK_SCHEDULE=` (set but empty) makes `agent_decks` fall back to
`BenchDimir.dck` for every chunk, which is the 7c piloting task. Do not
simply omit the variable: `p10_flagship.sh` uses `${P10_DECK_SCHEDULE-...}`
so an unset variable takes the flagship's rotation.

## What must be shared

| thing | why |
|---|---|
| `/tmp/rl_p10_scratch_init.pt` | same random net, or the arms differ at episode 0. Restore it from `rl/artifacts/tmp/rl_p10_scratch_init.pt`, do not re-mint it. |
| `rl/p10_pool_seed.tsv` | same 44-row opponent population |
| `P10_CHAMPION` = ck_6144, `P10_GATE_G=50` | same ratchet |
| `P7_LR=3e-4`, `P7_RATE=2048`, `P7_SNAP=512`, `P7_CONC=4` | same optimisation and cadence |
| `P10_ARCHSHARE` schedule | same opponent-deck curriculum |
| probe seeds 950000 / 951000 / gate 952000 | same instruments |

## What must NOT be shared

- **Ports.** Use 7821/7822 so the two lanes' policy servers never collide.
- **`$P7_OUT`.** Separate output trees.
- **The driver server.** One persistent JVM can serve both lanes (jobs
  are serialized inside it), but that halves each lane's throughput.
  Prefer a second server on another port and set `RL_DRIVER_PORT`.
- **Chunk RNG.** Both lanes use seed formula
  `80000000 + SEED*1000000 + trained`, so run the control arm with a
  DIFFERENT `<seed>` argument only if you want independent games; pass
  the same `0` if you want the two arms to see the same game seeds,
  which is the tighter comparison and what the tables above assume.

## What the comparison answers

7c isolated the *opponent* deck variable and found it was the axis that
mattered. This pair isolates the *agent* deck variable, which nothing in
the project has varied from initialization. The reads to make at the
end:

1. **Mirror Elo** — does rotation cost mirror rating (it should, some;
   the agent spends only 40-75% of its episodes on BenchDimir)?
2. **Robustness matrix residuals** — does rotation buy generalisation
   the mirror-locked arm cannot get, over and above what the shared
   opponent-deck curriculum already buys both arms?
3. **Opponent-turn casts** — 8b's draw-go signature (26-51/200g under
   deck randomisation vs 2-6 everywhere else) appeared only under deck
   randomisation. Does it appear here from initialization, and only in
   the rotating arm?
4. **Gate promotions** — how many snapshots of each arm ever beat
   ck_6144, and when.
