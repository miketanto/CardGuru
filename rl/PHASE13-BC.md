# PHASE13-BC — behaviour cloning from CP7 on a fresh card-aware network, then training against CP7 (runbook + pre-registration, 2026-09-15; v7/lane-d)

Why (chat, 2026-09-15, after Phase 12): RL against CP7 from the existing
Dimir main moved its sampled CP7 rate only from 0.12 to 0.22 in 5,376
episodes, with card habits still swinging; the per-game win/loss signal is
too coarse to teach decisions one at a time. Decision (user): **clone CP7 on
a fresh network, then train against CP7.** The last clone (Phase 7d, W0Base)
learned action types, not cards (held-out card top-1 0.606 vs a 0.833 copy
ceiling), and PPO from it did worse than PPO from scratch. Two causes are now
known and fixable: (1) that network was card-blind (Phase 9 P1: every subject
incl. the clone at < 1e-4 card-swap sensitivity); the `--cand-refers-pool`
path fixes it and survives training (Phase 10 interim check); (2) only CP7's
priority decisions were labelled (`rl.agent=cp7`, `CP7TeacherPlayer`); its
attacks, blocks and target choices were not, so the clone attacked and
blocked with an untrained head. Deck: **BenchDimir** (the deck under study;
landfall and white stay paused).

Rules that bind: CLAUDE.md; HANDOFF-V7.md §K + the latest section (§P); the
STATE lessons in rl/OVERNIGHT-7D.md, rl/PHASE8-DECKS.md, rl/PHASE10-LEAGUE.md,
rl/PHASE11-DRILL.md, rl/PHASE12-CP7.md — session-independent WSL keepalive;
pgrep verification a minute after every detached launch; **the box holds
the training lane plus at most one other model-holding process** (Phase 12
swapped at two servers + two JVMs + a CPU readout); kill only via script
files whose name cannot match their pattern; never edit a script or
server-side Python a running job executes (swap atomically in a gap; flags
default off); census recordings keep full transcripts. Wilson; ≥ 100 games
per level; pre-register; correct in the open; commit + push after each
finding; commit messages end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
Append a dated STATE line at the bottom of this file after every step.

**Evaluation protocol for this phase (from the Phase 12 verdict):** every
level is read three ways on the same seeds — **sampled** (frozen, sampled as
in training), **two-stage** (`--argmax-two-stage`: act vs pass by summed
probability, then the class argmax among acting candidates; built and tested
in 5ed6f66, off by default), and argmax-classes (reported for continuity,
never decisive). Readings below use sampled and two-stage; where they
disagree, say so and report both.

## 13a — the recording (CP7 in the seat, labels on every decision kind)

* Seat: `rl.agent=cp7` (`CP7TeacherPlayer`, `rl.aiSkill` 6) on BenchDimir,
  through the v7 recorder (the 7d1b / `record_p9.sh cp7` path). Opponents:
  the heuristic AND CP7 (mirror), both seats by play/draw parity, so the
  labels include CP7 against a competent opponent.
* **Labels to add (Java, `rl/xmage-src`, compiled with `bash rl/sync_lane_b.sh`
  while nothing runs the engine):**
  1. priority (exists: the first ability CP7 activates in the window);
  2. **target choices** — when CP7 picks targets for a spell or ability, label
     the matching target candidate on the corresponding TARGET consult
     (removal targets are where Dimir's card sense shows);
  3. **joint attack / block** — build the same CombatMath candidate list the
     RL seat gets (`jointAttacks` / `jointBlocks`, lifted to package-static if
     needed), let CP7 declare, label the candidate whose set matches (−1 when
     none matches: counted as `teacherJointMiss`).
  Time-box: two attempts each for (2) and (3); if one is not done, record
  without it and say so in the row — the clone's head for that decision kind
  then starts untrained, which is the Phase 7d failure the phase is trying to
  avoid, so the row must carry it.
* Volume: ≥ 60,000 labelled consults (priority + target + joint), expected
  ~1,000–1,500 games; counters in the summary (labelled fraction by kind,
  `y=-1`, multi-act, joint-miss); CP7's own win rate over the recording games
  (the teacher's level, reported). Faithfulness: `wire_validate` on 100
  consults; `rl/probes/faithfulness.py` on 100 (the 5b gate).
* Pre-registered gate: labelled fraction (−1 excluded) ≥ 0.9 per decision
  kind recorded; otherwise that kind is not cloned.

## 13b — the clone

* Network: a **fresh** P10INIT net with `--cand-refers-pool` (the card path),
  seed recorded. `rl/v7_bc.py` extended for target and joint labels
  (cross-entropy over each consult's candidates, per decision kind), 10 %
  hold-out **by game**, early stopping on held-out CE, AdamW, cuda.
* Report per decision kind: held-out CE, card-level top-1 agreement, type
  agreement, and the **copy ceiling** computed on this data the Phase 7d way
  (the best achievable top-1 given identical-candidate ties).
* Card use: the card-swap probe (`rl/p10_cardswap.py`, same pair lists) on
  bc.pt vs a fresh flag-ON net; the Dimir census counters (25 CP7 games,
  `rl/record_census.sh` + `rl/dimir_census.py`) vs CP7's own reference.
* Levels: 100 games vs CP7 and 50 vs the heuristic, Dimir mirror, in the
  three readouts.

Pre-registered readings (13b):
* **Card-level clone** if held-out priority top-1 ≥ 0.8 × its copy ceiling
  AND the text-only card-swap Δp of bc.pt ≥ the fresh flag-ON net's; else
  "type-level clone again" (the Phase 7d failure) — say which ceiling fraction.
* **Competent start** if the sampled or two-stage BC level vs CP7 is ≥ 0.35
  (above Phase 12's best sampled level, 0.22) — both reported.
* **Habits cloned**: self-destroy below 0.2, counterspells cast in [0.2, 0.5]
  of offers, creatures per game ≥ 3 on the BC census.
* Cannot: exceed its teacher in expectation (a faithful clone in the CP7
  mirror sits near 0.5 at best); say anything about other decks.

## 13c — training against CP7 from the clone

* From bc.pt, the Phase 12 recipe and rotation unchanged (75 % CP7 / 25 %
  heuristic on the Dimir mirror, lr 3e-5, 1 epoch, logit bound 5, AdamW wd
  0.01 on the heads, `--adv-norm batch`, `--target-kl 0.02`; the card path
  comes from the checkpoint config), the controller `rl/phase12.py --mains`
  pattern with the new start snapshot; per-block 25-game CP7 check; a
  100-game level every 1,024 episodes in the three readouts.
* Graduation: sampled OR two-stage level vs CP7 ≥ 0.70 with Wilson lower bound
  ≥ 0.60 (the argmax-classes level is not a graduation readout in this phase).
* Pre-registered readings (13c):
  - **RL improves on the clone** if the last sampled or two-stage level is
    clear above bc.pt's;
  - **RL forgets the clone** if it is clear below bc.pt's (the Phase 7d
    signature) — the pre-stated remedy, not run unless this happens, is a
    KL-to-bc.pt penalty in the update;
  - **habits hold** if the three census clauses above stay met over the
    last four checks.
* Cannots: one seed; CP7 skill 6 only; no league claim (that is Phase 14, run
  only with a graduate and with CP7 kept in the pool).

Order: 13a → 13b → 13c, each its own row in rl/V7-VALIDATION.md, then a
Phase 13 verdict and a HANDOFF-V7 UPDATE + section.

## STATE (append dated lines; newest last)
- 2026-09-15 (start): nothing running; Phase 12 closed (bcabffd).
- 2026-09-15 12:50Z WSL (13a Java + launch): target and joint attack/block labels built in ONE attempt each (time-box not needed). rl/xmage-src/JointCands.java = RLPlayer.jointAttacks / jointBlocks (+ attackChoiceSet, theirBlockers) candidate builders lifted verbatim to package-static; RLPlayer now calls them (one code path). CP7TeacherPlayer: target labels (a) at activateAbility for targets preset by CP7's search (the engine skips the choice; view taken there, spell still in hand - stated for the row), (b) wrapped chooseTarget / choose (Target and Cards forms) for triggered / choose-style targets; one consult per required target as policyPickTargets / policyPickCards; min-0 targets not consulted (tgtOptional). Joint labels: list built before CP7 declares, declared set read back, matched by body multiset (exact) or outcome key (alias), else y=-1 (teacherJointMiss). Two fixes found by the smokes: CP7's pass is itself an activated PassAbility (had been captured as 'outside', 27/266 priority consults) - now y=0; priority fallback to the unique same-source same-class candidate (prioAlias). Compiled with rl/sync_lane_b.sh (3 builds, OK). Smokes rl/artifacts/v7/13/rec/smoke13_*: after the fix 4 games vs heuristic 222/223 labelled (priority 178/179, one token ActivateAsSorcery miss; targets 22/22; attacks 20/20; blocks 15/15); CP7 passes 92 of 179 priority windows on Dimir (it never passed on W0Base); one attack miss in the earlier smokes = CP7 declared a Pareto-dominated subset (a real miss). wire_validate ok on both smoke files. RECORDING RUNNING since 12:49:42Z: rl/run_13a.sh (lane H: driver 7911 / echo 7784 vs the heuristic, seeds 13000+; lane C: driver 7912 / echo 7785 CP7 mirror, seeds 13500+; 50-game jobs, consultBudget 4000, rl.aiSkill 6, target 66,000 labelled), pgrep-verified (runner x3, echo x2, drivers x2; no model-holding process). Log rl/artifacts/v7/13/rec/run_13a.log (RUN13A| lines), per-job REC13| lines in rl/artifacts/v7/13/rec/counts.txt; per-kind counters: python3 rl/rec13_summary.py rl/artifacts/v7/13/rec/rec13_*.jsonl. Stop between jobs: touch rl/artifacts/v7/13/rec/STOP. Expected ~2-3 h (smokes: ~10 s/game vs heuristic, ~24 s/game mirror, ~55 consults/game).
- 2026-09-15 12:59Z WSL (13a relaunch, attempt 2 for targets): the first recording (12:49-12:56Z, attempt-1 build) was STOPPED by rl/stop_13a.sh and moved to rl/artifacts/v7/13/rec/attempt1/ (not used): dimir_census keys removal on the top own stack object, and attempt 1 built preset-target consults with the spell still in HAND - the targeting spell was invisible to the clone and to the census. Attempt 2 (b03cf7f): picks read at activateAbility, consults built AFTER the activation (spell / ability on the stack, costs paid - the remaining difference from the RL seat, stated for the row). Smokes on the new build: 241/241 and 66/66 labelled (priority, target, attack, block: no misses), dimir_census finds the removal consults (8, highest-power enemy 8/8) and CP7 self-removal 0/127. Recording RELAUNCHED 12:59:03Z, same runner and paths (log rl/artifacts/v7/13/rec/run_13a.log), pgrep-verified 12:59:20Z (runner x3, echo x2, drivers x2).
- 2026-09-15 13:02Z WSL (13c prep, nothing launched): rl/phase13.py GENERATED by rl/make_phase13.py from rl/phase12.py (untouched): one main M_B on BenchDimir from P13_START (default rl/artifacts/v7/13/bc/bc.pt), lane seed 31, state /tmp/rl_13_M_B, artifacts rl/artifacts/v7/13/c; Phase 12 recipe (league11 SRVEXTRA, printed by --dry-run: --device cuda --epochs 1 --logit-bound 5 --weight-decay 0.01 --adv-norm batch --target-kl 0.02 --argmax-classes --cand-refers-pool; lr 3e-5 via R0_LR) and rotation cp7,heuristic,cp7,cp7 unchanged; per-block 25-game CP7 check (record_census.sh, seed 13700); levels every 1,024 in three readouts (sampled battery_p12s.sh / two-stage battery_xdeck.sh + --argmax-two-stage / argmax-classes battery_xdeck.sh), graduation sampled OR two-stage >= 0.70 with Wilson lower >= 0.60; no unseen suite; start level + census = the 13b rows unless --start-level / --start-census; --hours default 12; lines L13|block / L13|check / L13|level. Also rl/run_13_levels.sh (the 13b three-readout levels, same seeds) and rl/v7_bc.py per-kind (46a28b8).
