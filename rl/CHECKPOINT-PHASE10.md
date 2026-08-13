# PHASE 10 CHECKPOINT — three lanes merged, one convergent design

This branch (claude/cardguru-phase-5-kickoff-2usq4s) is the
consolidation point: Phase 7b (PFSP self-play league), Phase 7c
(archetype curriculum), and Phase 8/8b (transfer + channel
diagnostics) are all merged here, their driver fixes ported and
validated, on the Phase 9 fast path. Spawn every new session from
THIS branch.

## 1. What the three lanes established (each report stands alone;
##    this is the synthesis)

- **7b (PHASE7B.md)**: optimistic Elo-based PFSP doubles the learning
  rate; a scratch lstmattn line reached Elo 1101 (D1 parity) in 6144
  episodes with no teacher data. But an ungated pool drifts once the
  agent outgrows it: the 9216 net loses .40 h2h to the 6144 peak.
  => leagues need CHAMPION GATING and external pressure.
- **7c (PHASE7C-REPORT.md)**: opponent-deck diversity was the one
  axis four phases never varied and it beat every axis that was
  varied — search parity in 1536 episodes, every robustness residual
  improved, specialists lost even on their own decks. Blocking was
  never a policy hole (agents block ~100% when asked; the mirror
  rarely asks). The D0<D1<D1h ladder is BenchDimir-specific.
  => OPPONENT-DECK COMPOSITION is a primary training variable.
- **8/8b (PHASE8-TRANSFER.md, PHASE8B-CHANNEL.md)**: E2 graph
  features are massively load-bearing (scramble: .64->.26) but are
  consumed as LOCAL IDENTIFIERS, not compositional semantics — a
  single-deck-training artifact, not a representation ceiling.
  Deck-randomized fine-tuning shocked the nets but produced the
  project's first genuine draw-go (26-51 opp-turn casts/200g vs 2-6
  everywhere else). => deck diversity must start FROM INITIALIZATION;
  add condition-breadth feature axes; E0 cannot follow this road.

Convergence: all three point at the same next run. Train from
scratch, with deck diversity from episode 0, inside a gated
PFSP league, on the fast path. Each lane contributes the piece the
others lacked.

## 2. Current best agents (all in rl/artifacts, all cdim-91 unless noted)

| agent | where | mirror Elo | notes |
|---|---|---|---|
| p7b_champion (ck_6144) | rl_p7_lstmattn_s0/ | **1101** | best mirror player; D1 parity; blocks 13/13 vs redrush |
| 7c ck_1536 | p7c artifacts | 1096 | best curriculum mirror rating |
| 7c ck_3072 | p7c artifacts | 1046 | most ROBUST (all residuals +) |
| attn_desp | rl_c6_attn_s7/ | 1053 | feed-forward attn champion |
| e0_champ | rl_e0league_s0/ | 1083 | name-hash control, no transfer |
| D1 / D1h (scripted) | frozen instruments | 1085/1088 | mirror-specific ladder (7c) |

UNRESOLVED: p7b ck_6144 vs 7c ck_1536/3072 have never played each
other, and both "paritys" are 100g claims. See Course of Action #1.

## 3. Infrastructure state on this branch (all validated together)

- **Phase 9 fast path**: persistent driver JVM (rl/driver_server.sh,
  run_driver.sh), rl.concurrency=N (N=cores), per-worker opponent
  connections (concurrent rl-vs-rl works), --threads N policy server
  with per-session LSTM state, ParallelGC, playableCache (search
  seats only). ~25-30 train eps/min at conc4 vs ~7 on the mvn path.
- **7c driver features**: rl.oppDeck (opponent pilots a different
  deck; decks bind to seats — order-binding bug fixed),
  blocksDeclared/blockOpportunities counters in every summary line.
- **League machinery**: league_lane_p7.sh (P7_PFSP optimistic Elo
  selection via pfsp_pick.py, P7_RATE/P7_SNAP decoupled cadences,
  P7_CONC/P7_PERSIST fast path, orphan-port cleanup, encoding-family
  guard); league_lane_p7c.sh (curriculum variant); atomic checkpoint
  saves in policy_server.py (SIGKILL-safe).
- **Eval**: elo_tournament.sh + elo_fit.py (mirror scale, D0=1000);
  7c robustness matrix + deck-power normalization (p7c_report.py);
  Elo probes ALWAYS sequential.
- **Deck assets**: 6 curriculum archetypes (p7c_curriculum.tsv), M3
  pool (28), P8 swaps + Faeries, 24 p8b variants + 6 meta decks —
  all calibrated or calibratable via p7c_pilot_calib.sh.
- Known league smells + fixes: kill-mid-save (fixed, atomic), stale
  driver-server classes after rebuild (restart server), pkill
  self-match (use bracket patterns), wait-on-killed-pid returns 143
  (not a failure).

## 4. Course of action (recommended, in order)

1. **Crown the champion (cheap, do first, ~2h fast-path)**:
   500g ck_6144 vs D1; 200g ck_6144 vs 7c ck_1536 and ck_3072 (mirror
   AND 2-3 archetype rows). Converts two noise-level parity claims
   into one ranked answer and picks the Phase 10 opponent-pool seeds.
2. **Phase 10 flagship — the convergent run**: from-scratch lstmattn,
   PFSP league with champion gating (promote snapshots into the pool
   only if they beat the reigning champion h2h), opponent pool =
   archetype decks (7c's six, D0-piloted, Elo-rated rows) + gated
   snapshot ladder + prior champions. Agent-side deck ALSO drawn from
   a small rotation (Dimir-heavy early, widening) — 8b's from-init
   compositional bet. Rate on the mirror (comparability) + 7c
   robustness matrix + block/oppTurn counters every 2048. Budget
   12-16k episodes (fast path: overnight). Optional control arm:
   identical but agent locked to BenchDimir — isolates the agent-deck
   variable the way 7c isolated the opponent-deck one.
3. **E3 features session (parallel, independent)**: add (i) known
   top-of-library + hand-differential features (card-advantage/
   filtering visibility — Kaito-0 is currently never activated, an
   observability gap), (ii) condition-breadth axes (Force Spike
   incident), (iii) removal-scope axes. Re-extract, re-verify
   byte-compat harness, then BC-free A/B inside the Phase 10 design.
4. **Upper-bound opponents**: per-archetype random-init pilots
   trained to convergence (7c rec #4) — lifts the D0-piloted matrix
   caveat and supplies gated-league pressure at the top.
5. Deferred but staged: 5-seed replication gates (7c and 8b hints),
   BC-init comparison arm (student_e2lstm_seq.pt), C4 stage 2.

## 5. Spawn kit (paste-ready prompts for new sessions)

All sessions: branch from claude/cardguru-phase-5-kickoff-2usq4s,
work on a NEW branch, never push to phase-5. Setup: XMage pin
7554968c + rl/engine-patches/phase9-engine.patch + overlay
rl/xmage-src and benchmark/xmage/src -> Mage.Tests; mvn -pl
Mage.Tests -am install -DskipTests; bash rl/restore_artifacts.sh;
copy rl/*.dck + rl/m3_decks/*.dck into Mage.Tests. Fast path per
PHASE9-PERF.md "Recommendation" section. Operational rules in any
PHASE7*-KICKOFF doc apply verbatim.

- **Champion match (action #1)**: "Read rl/CHECKPOINT-PHASE10.md
  section 4.1. Run the three matches at the stated game counts on the
  fast path (eval sequential), report a single ranked table with CIs,
  and update the checkpoint doc's champion table."
- **Phase 10 flagship (action #2)**: "Read rl/CHECKPOINT-PHASE10.md
  sections 1-4. Implement champion gating in league_lane_p7.sh
  (promote ck into pool_elo.tsv only on h2h win vs reigning champion,
  50g), extend the pool schema with the 7c archetype rows
  (kind+deck), then run the flagship as specified in 4.2. Report per
  2048 episodes: mirror Elo, robustness matrix, block rate, oppTurn."
- **E3 features (action #3)**: "Read rl/CHECKPOINT-PHASE10.md 4.3,
  rl/PHASE8B-CHANNEL.md conclusions, and the E2 extractor. Add the
  three feature groups, bump cdim, re-extract e3_features.tsv,
  validate distances on the P8 swap pairs (Force Spike must separate
  from Spell Snare), and train a 512-episode pilot to verify the
  channel is read. Do not touch e2_features.tsv."

## 6. Rating-protocol caveats that now bind every future phase

- Mirror Elo is comparable across ALL phases (same anchors) but
  under-exercises combat (7c) — never draw robustness conclusions
  from it alone.
- The scripted ladder ordering is mirror-specific; D1 is a WORSE
  pilot than D0 on 4/6 archetypes. Cross-deck ratings need per-deck
  anchor calibration (p7c_pilot_calib.sh).
- 100g probes: ±.07 CI at 200g/cell, ~±25 Elo — phrase accordingly;
  500g for claims, 5 seeds for conventions.
