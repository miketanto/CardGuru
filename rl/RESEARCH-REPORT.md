# CardGuru MTG-RL — Research Report (Phases 0–5 + extensions)

**Goal.** Determine whether XMage (a full Magic: The Gathering rules
engine) can serve as an RL environment, and how far a small policy
network can be pushed against calibrated scripted opponents — with
every claim gated by fixed-seed, CI-scale evaluation.

**Stack.** XMage pin `7554968c` (+1 engine patch); Java driver with a
policy-delegated agent seat (`RLPlayer`), NDJSON-over-TCP policy server
(PyTorch, PPO); deterministic seeding throughout. Opponent instruments:
D0 = deterministic heuristic, D1 = 1-ply×8 minimax over
`GameStateEvaluator2` (material evaluator). Decks: 4 training mirrors
(Burn/Control/Midrange/Dimir) + 3 zero-overlap holdouts + 28 verified
novelty decks. Conventions: agent-seat consults as the unit; 500-game
CI for headlines; instruments never retuned mid-experiment.

---

## Phases 0–4 (pre-existing results this work built on)

| finding | number |
|---|---|
| Engine throughput (rollout = pure engine; IPC cost) | 1.00×; 2% |
| Engine share of training wall-clock | 87% |
| D1 vs D0 calibration (v2 instruments) | .776 @500g |
| Depth D2/D3 vs D1 — evaluator ceiling, ladder has 2 rungs | .52 (flat) |
| Terminal-reward PPO plateau vs D1 (~1,280 eps) | .26–.42 |
| E0 (16-bucket hash) vs E2 (graph features): win rate | parity ×4 measurements |
| E0 vs E2: freeze (stall) rate on holdouts | E2 lower, seed-noisy |

## Phase 5 experiment tree (this work)

### C0 — Is perfect information load-bearing in the search instrument?
Built `SearchPlayerIP`: same search, but each candidate averaged over
K=4 determinizations (opponent hand+library re-dealt, own library
shuffled).
**Data:** D1ip vs D0 **.728** @500g (D1: .776). D1ip vs D1 head-to-head
**.482** @500g (v3 recheck: .484). D2ip vs D1 .52.
**Verdict:** perfect info worth ~0 at 1 ply → D1 licensed as a fair
teacher.

### C1 — Behavioral cloning of D1
`TeacherLogPlayer` logs the exact (state, candidates, action) the RL
agent would see at every decision point; 1,000 episodes → 199,457
examples, 0 unmatched labels; supervised training of the same net.
**Data:** offline 96.8% top-1 (83.2% non-pass). Online @500g:
**.428 vs D0, .396 vs D1** (teacher: .776/.504). 3× data bought +.10;
compounding error: 0.97^73 ≈ 10% of episodes stay on-trajectory.
**Verdict:** BC lands in the old PPO plateau at a fraction of the
interaction, but cannot approach the teacher. Covariate shift suspected.

### v3 — Instrument fix (user-directed): flash/ninjutsu blindness
Transcript review showed no instrument could ever ninjutsu or cast at
flash speed (yield gates + action filters + featureless encodings).
Fixed all three layers; verified by same-seed transcripts (Kaito
ninjutsu line appears; Elektra "Sneak" generalized).
**Data:** D1 vs D0 recalibrated **.776 → .614** @500g — the fix
strengthened the heuristic floor more than the searcher. Only the Dimir
deck carries flash cards → all non-Dimir numbers carry over.
**Verdict:** action-surface blindness was worth ~16 points of ladder;
all later work on v3.

### C2a — BC-init PPO ± potential-based reward shaping
Φ = tanh(GameStateEvaluator2/2000), policy-invariant shaping; arms
shaped ×2 seeds vs terminal-only ×1, 1,280 eps each vs D1.
**Data @500g:** no-shape **.442**, shaped **.434/.434** vs D1
(BC baseline .396). Stalls worsened 8.6% → 10–13%. Rolling 100g evals
overestimated every arm by ~.07 (caught by the CI gate).
**Verdict:** fine-tuning works (+.04); **shaping is a null** — a
materialist potential teaches nothing a BC-initialized policy lacks.

### C3 — DAgger (is covariate shift the bottleneck?)
Round 1: noise-injected teacher (ε=.25 deviations, exact labels),
115,798 examples → **no change** (.398 vs D1). Round 2: true on-policy
shadow labels — student plays, teacher labels every consulted window
(39,021 labels; measured covariate gap: **35% act-labels on student
states vs 8% on teacher trajectories**).
**Data @500g:** **.396 vs D1** — exactly the BC number.
Validation on the student's own states: **90.2%** vs 96.8% on teacher
trajectories — the 43k-param net **underfits its own distribution**.
**Verdict:** covariate shift rejected; **representation capacity is
the wall**. Imitation family ceiling ≈ .40, imitation+PPO ≈ .44,
teacher ≈ .50.

### M3 — Novelty sweep (does deck diversity move the E0/E2 gap?)
28 new verified decks; nested pools 2/4/8/16/32; fixed 640-ep budget;
2 encoders × 5 pools × 2 seeds; zero-shot holdout evals (12,800 train
eps + 12,000 eval games). Engine hazard found: **delve castability
checking explodes `getPlayable`** (OOM) — plus recursion/token bombs;
all bisected and defused.
**Data (pooled 6,000g/arm):** freeze rate **E2 2.5% vs E0 4.1%**
(3rd replication of the liveness edge; does NOT widen with pool size);
zero-shot win rate **E2 .401 vs E0 .365** — first-ever win-rate
daylight between the arms (short-budget only; needs the 5-seed gate).
**Verdict:** graph features = robustness story, still not a strength
story at standard budgets.

### C4 — Open-mana timing (user-directed): is draw-go worth anything?
All players deploy at the first legal window (the evaluator cannot
price "untapped mana + card in hand"). Built `SearchPlayerHold` (D1h):
never casts flash/instants at sorcery speed.
**Data @500g:** D1h vs D1 **.504**; D1h vs D0 .596 (D1: .614).
**Verdict:** draw-go worth **~0.000 vs non-adaptive opposition** — the
insight about the evaluator is right, but timing only pays against
opponents who use information or fear mana. Motivate self-play.

### C5 — Clean self-play league (user-directed): no shaping, no yields,
### snapshot-pool opponents, D0/D1 as probes only
Both seats policy-driven; opponent = frozen past self from a rotating
snapshot pool; every hand-written strategic prior removed
(`rl.noYields`: policy sees all ~230 windows/game).
**Data (BC-init arm, 2,560 eps, BenchDimir):** probes rose
.49→**.58 peak / .56 final** vs D1 and .58→**.67–.71** vs D0 — above
D1's own .614 vs D0. Self-ladder: current beats its BC origin **.62**,
but is flat vs its 1024/1536-selves → real growth confined to the
first ~1,000 episodes. Scratch arms (no BC): stuck at .01–.08 through
384 eps (paused in favor of the BC arm). Cast-timing histogram:
opponent-turn instant casts nearly doubled (42%→57% share — real stack
interaction learned) but flash *threats* remain 0% opponent-turn — no
draw-go emergence.
**Verdict:** self-play beats every fixed-opponent method (+12 over BC
origin; probes above both rulers) and then saturates at the same
capacity wall.

### C6 — Bigger nets (user-directed; in progress)
Since training is engine-bound (87%), capacity is free: E2 features
(cdim 91) + transformer over [state+candidates] (297k params;
candidates finally attend to each other), and an LSTM-attention
variant (429k). Quick BC warm-start → same clean league → head-to-head
vs the frozen C5 champion. Running.

---

## Master numbers (all @500g unless noted, v3 instruments)

| agent | vs D0 | vs D1 |
|---|---|---|
| D0 (heuristic floor) | — | .386 |
| D1 (1-ply search yardstick) | .614 | ~.50 mirror |
| D1ip (honest search) | .728* | .482* (*v2) |
| BC student | .428 | .396 |
| BC + PPO (best C2a) | .476 | .442 |
| BC + true DAgger | .456 | .396 |
| **BC + self-play league (2.5k eps)** | **.67–.71 (probes)** | **.56–.58 (probes)** |

## The three load-bearing conclusions

1. **Measure the instrument before the agent.** Perfect information at
   1 ply: worth ~0 (C0). Flash blindness: worth 16 points (v3).
   Draw-go timing vs non-adaptive opponents: worth 0 (C4). Each
   audit changed what later numbers meant.
2. **The failure chain was: signal → data → capacity.** Terminal PPO
   starved (P4) → imitation saturated (C1) → on-policy labels changed
   nothing because the 43k-param net can't fit them (C3). Each cheaper
   hypothesis was killed by a designed experiment before scaling up.
3. **Adaptive opposition beats reward engineering.** Shaping: null
   (C2a). Self-play with zero hand-written priors: the best agent in
   the project and the only one that learned genuine stack interaction
   (C5) — and it saturated exactly where the capacity diagnosis
   predicted, which is why C6 upsizes the net and nothing else.

## Cost ledger
≈45,000 games/episodes total across Phase 5; ~24h wall-clock on 4 CPU
cores; 2 container losses (fully recovered from disk); every incident
(silent task kill, path bug, OOM class, RNG bias, cross-JVM jitter)
detected by guards or profile-implausibility checks and documented.

*Full per-experiment writeups: `rl/PHASE5-*.md` in the repo
(miketanto/cardguru, branch `claude/cardguru-phase-5-kickoff-2usq4s`).*
