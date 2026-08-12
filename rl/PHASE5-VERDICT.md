# PHASE 5 VERDICT

## What was asked

Phase 4 ended with: terminal-reward PPO can't beat 1-ply search (D1);
the ladder has two rungs; the E0/E2 gap is closed except liveness.
Phase 5 ran the decision tree C0 -> C3 (search honesty -> imitation ->
shaped RL -> DAgger) plus the M3 novelty sweep, with one user-directed
instrument bump (v3) in the middle. Every branch point is documented in
its own file (PHASE5-C0/C1/C2A/C3, PHASE5-V3, PHASE5-M3).

## The through-line, milestone by milestone

- **C0**: Honest determinized search (SearchPlayerIP) keeps the whole
  D0->D1 step; head-to-head vs perfect-info D1 is even (.482@500g v2,
  .484 v3). The perfect-info "cheat" is not load-bearing at 1 ply ->
  D1 licensed as imitation teacher.
- **C1**: Behavioral cloning of D1 (200k exact-labeled decisions, novel
  TeacherLogPlayer capture with 0 unmatched labels) reaches 97%
  offline accuracy but only .36-.40 online vs D1 - inside the old PPO
  plateau for a fraction of the interaction, far below the teacher.
- **v3 (user-directed)**: The instruments were structurally blind to
  flash-speed deployment (ninjutsu never fired; REACTIVE yields closed
  the windows; non-cast candidates encoded featureless). Fixed at all
  three layers and recalibrated: D1 vs D0 fell .776 -> .614 (the FLOOR
  gained more than the searcher - the ladder's one rung halved).
  Same-seed transcripts confirm the Kaito ninjutsu line and even
  Elektra's Sneak. Remaining honest caveat: the searcher deploys at
  its own upkeep, not at the opponent's end step - the materialist
  evaluator cannot price holding mana open. Only BenchDimir carries
  flash/ninjutsu cards, so all non-Dimir v2 numbers carry over.
- **C2a**: BC-init PPO adds +.04 (.434-.442 vs D1 @500g). Potential-
  based shaping from GameStateEvaluator2 is a NULL (shaped == unshaped)
  - the dense-signal hypothesis is dead at this potential. Stalls
  worsen under PPO. The v3 flash lines never reach the learned policy
  (100% main-phase casts in sampled transcripts).
- **C3**: DAgger, done right (true on-policy shadow labels after a
  noise-injected round), moved vs-D1 by exactly 0.000. The covariate
  gap is real (35% act-labels on student states vs 8% on teacher
  trajectories) but the E0 net UNDERFITS its own distribution (90.2%
  vs 96.8% val) - the binding constraint is representation capacity,
  not data. C-track concluded: imitation family ~.40, +RL ~.44,
  teacher ~.50.
- **M3**: The E2 liveness edge replicates a third time (2.5% vs 4.1%
  freezes, 6,000g/arm, 5 pool sizes) but does NOT widen with novelty.
  Surprise: a pooled zero-shot win-rate edge for E2 at short budget
  (.401 vs .365) - first win-rate daylight ever between the arms;
  needs the 5-seed gate before believing it. Plus a catalog of engine
  hazards for large pools (delve getPlayable subset explosion is an
  OOM).

## The honest synthesis

1. **The agent's ceiling moved from "can't beat the plateau" to "can't
   beat the teacher," and the reason is now measured, not guessed.**
   Signal (PPO) beat supervision once supervision saturated; on-policy
   labels changed nothing; the E0 net cannot even FIT the teacher on
   the student's states. Capacity/encoding is the wall. Everything
   cheaper than that wall has now been tried and priced.
2. **Instrument honesty was the sleeper result of the phase.** Two
   findings that reframe earlier numbers: perfect information is worth
   ~nothing at 1 ply (C0), and action-surface blindness was worth 16
   points of D1-vs-D0 (v3). Yardsticks earn trust by being attacked;
   both attacks made the conclusions stronger.
3. **The graph encoder's story is liveness, and it keeps surviving.**
   Three replications of fewer-freezes-on-novelty; still no confirmed
   strength story at standard budgets - but M3's short-budget edge is
   the first crack in "parity everywhere" and is cheap to test
   properly.
4. **What beating D1 would actually take**, in evidence order: a wider
   candidate encoder + larger net trained RL-from-BC (attacks the
   measured capacity wall); combat/target coverage (never
   shadow-labeled); then Track B self-play for graded opponents - with
   "beats D1v3" (.614-anchored) as its success bar, per
   PHASE4-VERDICT's re-anchoring.

## Cost ledger (Phase 5)

~30,000 games/episodes across C0-C3 + M3 + v3 recalibration + 2
instrument-validation batteries. Two containers died mid-phase (all
state recovered from disk); harness incidents: 1 silent background-task
kill, 1 path bug voiding one eval battery (caught by profile
implausibility), 1 OOM class bisected to delve, RandomUtil first-draw
bias caught by rate check, cross-JVM tie-break jitter documented. Every
headline number is a 500g+ CI or a 6,000g pool.
