# Phase 11 kickoff — the league that does not starve

Written from Phase 10's measured result (`rl/PHASE10-FLAGSHIP.md`).
This is the design the saturation finding implies; it is not a guess.

## What Phase 10 established

1. **Champion gating works as an anti-drift ratchet.** 7b's line fell
   1101 -> 1044 once its pool filled with its own drifting snapshots.
   Phase 10's Elo held flat (1050 -> 1046) and its pool never admitted a
   single row the run produced. 7b's recommendation #1 is validated.
2. **And gating alone starves the league.** All 44 pool rows were
   frozen; gating kept all 16 of the run's own snapshots out; from
   ~6144 episodes there was nothing left to climb. Mean matrix residual
   change 6144 -> 8192 was **-.013**, mirror Elo flat, vs-D0 pinned at
   .58 for three consecutive checkpoints, gate mean .392 over 600 games.
3. **Deck diversity from initialization pays on the axis it targets.**
   At equal episode counts the flagship BEAT ck_6144 on redrush
   (.63 vs .52), TIED it on ramp, and MATCHED it on sweep (.87) — while
   sitting ~60 Elo below it on the mirror.

The gap is structural, and AlphaStar names it: this league contains no
opponent that adapts.

## The four changes, in leverage order

### 1. Self-play fraction (~35%) — the missing ingredient

AlphaStar's main agents spend roughly a third of their games against
their OWN CURRENT PARAMETERS. Neither 7b (own frozen snapshots) nor
Phase 10 (frozen externals only) had this. An opponent that tracks the
agent is automatically at the right difficulty forever, which is
precisely what a frozen pool stops providing once saturated.

Implementation: the lane already runs two policy servers per chunk. For
a self-play chunk, point the OPPONENT server at the same live
checkpoint the agent is training from (eval mode, no updates), and
re-serve it each chunk so it tracks. `P11_SELFPLAY_SHARE=0.35`.

### 2. Decouple pool entry from crowning

Phase 10 conflated "who is the current best" with "who is in the
training population". AlphaStar never gates main-agent league entry —
entry is SCHEDULED; the win-rate gate applies to exploiters, and even
that has a step-budget escape.

- Snapshots enter `pool_elo.tsv` on the P7_SNAP schedule, as in 7b,
  entering at the current self-Elo estimate.
- The 50g h2h gate is kept, but it decides CHAMPION status and the
  reported result only — `champion.tsv`, not pool membership.
- Anti-drift protection is retained by the PFSP weighting below plus
  the anchor fraction (7b's rec #4), not by starving the pool.

### 3. PFSP by measured win rate, not Elo distance

Phase 10 weighted opponents by a Gaussian on Elo distance, a proxy.
AlphaStar weights by measured win probability:

    f_hard(x) = (1 - x)^p        # favour opponents that beat us
    f_var(x)  = x * (1 - x)      # concentrate on near-even opponents

We already pay for the measurement — every gate is 50 games against a
known opponent, and every chunk's win rate is logged in `train.csv`.
Maintain a per-opponent win-rate table and weight from it, falling back
to the Elo Gaussian for rows with no games yet. `f_var` would have
parked Phase 10's training on the ~.40 opponents where the gradient was
richest instead of spreading it by rating distance.

### 4. Main exploiters initialised from ck_6144

7c's exploiters failed (.20-.40 regardless of deck) because they had
512 episodes from a mismatched Dimir prior. AlphaStar resets exploiters
to the SUPERVISED init for exactly this reason — an exploiter must
start strong enough to find a real weakness.

Initialise from ck_6144 (the strongest available prior, cdim 91),
train against the CURRENT agent only, promote into the pool on 70% h2h
or a budget timeout, then reset. `rl/exploiter_lane.sh` exists and
needs the champion-init and promotion-rule changes.

## Measurement plan

Unchanged instruments, so the curve stays comparable to phases 6-10:
mirror Elo (100g vs D0/D1/D1h, sequential, seed 950000) and the 7c
robustness matrix (100g vs D0 per archetype, seed 951000), both every
2048; gate every 512; block counters with denominators; transcripts.

**The A/B that matters**: Phase 11 vs Phase 10 from the SAME init
(`rl/artifacts/tmp/rl_p10_scratch_init.pt`) and the SAME seed pool
(`rl/p10_pool_seed.tsv`). Phase 10 is then the control arm for "does an
adapting opponent break the ceiling", with its saturation curve already
measured and committed.

Primary question: **does the mean matrix residual keep rising past
episode 6144, where Phase 10 flattened at -.013 per checkpoint?**

## Operational notes carried forward

- Rate often enough that PFSP's target is not stale, or run
  `rl/p10_selfelo_daemon.sh` (Phase 10's fix: the gate is a free
  50-game rating probe, and it agreed with the 300-game fit to within
  3 and 21 Elo at two checkpoints).
- PFSP floor is a SHARE of total mass (`--floor-total`), not a per-row
  constant — a per-row floor scales with pool size and swamps the
  signal exactly when the agent is weakest.
- Eval and gate probes stay sequential; training runs conc4.
- **Commit artifacts every checkpoint.** Phase 10's container was
  reclaimed during an idle gap and everything in /tmp was lost; the
  phase survived intact only because each checkpoint had been pushed.
- Budget caveat to keep stating: this is a 428k-parameter net on 4
  cores. AlphaStar ran three agent types for 44 days on 32 TPUs each.
  Nothing in these phases separates capacity limits from league design.
