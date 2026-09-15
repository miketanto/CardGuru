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
- 2026-09-15 ~13:15Z WSL (13a faithfulness, on the running recording's finished games): GATE as pre-registered, 100 consults evenly sampled over 24 games of rec13_H_s13000: wire_validate ok; v7_faith_real L3 53 pass / 0 fail (113 not exercised), L4 52 / 1 (ent.mana_left_if_cast R2 0.896 vs 0.90 - the 5b 'small-scale real at the random wake' class), edges 3/0 (rl/artifacts/v7/13/rec/faith13.{md,json}). CONTEXT (not the gate): all 25 finished games (1,271 consults): L3 101 / 7, L4 99 / 9, edges 6/0 (faith13_full.*); CONTROL = the same probe on an RL-seat BenchDimir census of 25 games (rec_p12_M_D_n012_t09728, 2,972 consults): L3 85 / 0, L4 83 / 2 (faith_ctrl_p12n012.*). The teacher's consults exercise 23 more fields; its failing entries are small-n fields (stack_pos / stack_mine n_test 49, opp_hand.age 512, game.n_cand 288, threat_count 288, ctr_m1m1 138 exercised) or grouped fields whose pooled score is >= 0.995 (identity 0.9996, mv 0.9992, power 0.997, mine 0.995) but whose grouped verdict fails on a sub-slice. Which sub-slice is OWED (not chased). Reading: the gate passes at L3 and misses one L4 real by 0.004; the teacher seat cannot be called field-for-field identical to an RL seat at 25 games - the encoder path is the same code, so any difference comes from the states CP7 reaches, stated in the 13a row.
- 2026-09-15 13:13Z WSL (13a -> 13b chain): rl/chain_13ab.sh launched detached 13:13:00Z (log rl/artifacts/v7/13/chain_13ab.log, lines C13|...), pgrep-verified (13:13:38Z 1): waits for RUN13A|done, writes rl/artifacts/v7/13/rec/summary.txt (rec13_summary.py), clones only kinds with gate=pass (extraction tested on the smoke summary: prio,target,attack,block), stops drivers 7911/7912, runs rl/run_13b.sh (log rl/artifacts/v7/13/bc/run_13b.log, lines B13|...). First real job rec13_H_s13000 (50 games vs heuristic): 2,620 / 2,634 labelled (y=-1: priority 2, attack 11, block 1; targets 0), CP7 35-15, 794 s (16 s/game, 53 consults/game) - the recording ends nearer 16:00Z than 15:30Z. Do not edit run_13b.sh, v7_bc.py, run_13_levels.sh or the battery scripts while the chain waits (it executes them from disk).
- 2026-09-15 ~13:35Z WSL (13a gate view, CORRECTION in the open): rl/rec13_summary.py first gated per CANDIDATE-TYPE class, where a PASS-only joint consult (k = 1, no untapped blocker / a single option) falls under 'trivial' - on the first two jobs (100 games, 5,474 consults) that view read blocks 114/129 = 0.884 (FAIL) and would have made the chain drop the block kind. The pre-registered gate is per DECISION KIND; the teacher's Java counters know the kind: priority 4,107/4,110 = 0.999, target 534/534 = 1.000, attack 439/462 = 0.950 (exact 439, miss 23), block 353/368 = 0.959 (exact 346, alias 7, miss 15) - all pass. rec13_summary.py now prints REC13GATE lines from the probe counters (the gate; chain_13ab.sh's KINDS grep matches them, tested: prio,target,attack,block) and keeps the type view as REC13SUM|types=...|gate_types= (not a gate). Swapped atomically (mv of a tested .new) while the chain is still in its wait loop, before it calls the script. First two jobs: lane H CP7 35-15 vs heuristic (794 s), lane C CP7 26-24 in the mirror (981 s); joint misses are CP7 choices outside CombatMath's list (the vanilla model has no evasion: it can offer illegal blocks and prune the legal alternative) - counted, not labelled.
- 2026-09-15 15:24Z WSL (13a recording DONE): RUN13A|done=15:23:56Z, 68,500 labelled consults (y >= 0, all kinds), 25 jobs x 50 games = 1,250 games, every job rc=0 (per-job REC13| lines in rl/artifacts/v7/13/rec/counts.txt). CP7's own level over the recording (Wilson 95 %): vs the heuristic 623/750 = 0.831 [0.802, 0.856] (15 jobs, lane H); CP7 mirror 246/500 = 0.492 [0.448, 0.536] (10 jobs, lane C; 1 draw, 1 stall). The chain (chain_13ab.sh) picked it up at 15:25:01Z; per-kind gate summary -> rl/artifacts/v7/13/rec/summary.txt, then 13b.
- 2026-09-15 15:30Z WSL (13a ROW WRITTEN): rl/V7-VALIDATION.md '13a — the recording': 68,500 labelled / 68,952 consults, 1,250 games; gate by decision kind priority 1.000, target 1.000, attack 0.948, block 0.974 - all pass, all four cloned; PASS 54.7 % of CP7's priority labels; CP7 0.831 vs heuristic, 0.492 mirror. 13b RUNNING since 15:26:23Z (chain -> rl/run_13b.sh, KINDS=prio,target,attack,block, drivers 7911/7912 stopped; log rl/artifacts/v7/13/bc/run_13b.log, BC log rl/artifacts/v7/13/bc/bc.log).
- 2026-09-15 ~15:50Z WSL (13a flash check, coordinator): NOT a recording gap - addendum '13a — addendum: are instant-speed flash decisions recorded?' in rl/V7-VALIDATION.md. Teacher and RL seat build the priority list on the same path; memo test (verify mode, 60 games): hits 0 / mismatches 0. Full recording: flash offered on the opponent's turn 141x, cast 11x; cast on own turn 3,775x - CP7 casts its flash cards main-phase and is rarely holding one with the right mana open; per card Wondrous Wasp offered 21/21 when castable, Nowhere to Run not castable (conditional black on Gloomlake Verge / Hidden Lair), Floodpits Drowner never held with mana up, Enduring Curiosity offered 0/178 (and 0/135 to the RL seat: engine/card-level, owed). Consequence: the clone cannot learn instant-speed flash from these labels; the phase goes on. Scans rl/probes/flash13_scan*.py.
- 2026-09-15 ~15:48Z WSL (13b BC DONE, rc=0, 1,299 s): rl/v7_bc.py defaults on the fresh flag-ON init (init_on_s13.pt, cand_refers_pool=True), kinds prio,target,attack,block; best epoch 6 (early stop); held-out (10 % of games) overall CE 0.2920, top-1 0.884, class top-1 0.898, type 0.932. Per kind held-out top-1 vs copy ceiling: priority 0.876 vs 0.977 (0.897 of ceiling; CE 0.318 vs floor 0.059), target 0.889 vs 0.960 (CE 0.257), attack 0.977 vs 1.000 (CE 0.070), block 0.799 vs 1.000 (CE 0.366). bc.pt = rl/artifacts/v7/13/bc/bc.pt (gitignored), log bc.log. Card-swap, census and levels next in the chain.
- 2026-09-15 ~15:55Z WSL (13b card-swap + positional baselines): rl/p10_cardswap.py, same pairs and 10/A2 consult sets (rl/artifacts/v7/13/bc/cardswap/): text-only mean dp BC 0.0424 [0.0375, 0.0477] vs FRESH flag-ON init 0.0430 [0.0405, 0.0456] - the pre-registered clause 'bc.pt >= fresh' is NOT met (by 0.0006, intervals overlap); BC's dlogit 0.289 vs 0.235 and strict flips 0.207 vs 0.119 are higher, its logits far sharper (top gap 4.21 vs 0.35), which compresses dp; other classes BC vs FRESH: pt 0.025 vs 0.018, cost 0.028 vs 0.038, type 0.104 vs 0.099, self_mana control 0.015 vs 0.002. Positional baselines over the recording (rl/bc13_baseline.py): priority modal PASS 0.547 (BC 0.876), target index 0 0.623 (BC 0.889), attack LAST candidate 0.924 (BC 0.977 - only +0.05 over a positional rule), block modal 0.517 (BC 0.799). CP7 census reference done (census_cp7ref.txt); bc.pt census + levels next.
- 2026-09-15 ~16:00Z WSL (13b CP7 census reference, rl/artifacts/v7/13/bc/census_cp7ref.txt, dimir_census over the 1,250 recording games): self-removal cast 62/9,438 = 0.007 [0.005, 0.008]; counterspells taken 649/1,374 = 0.472 [0.446, 0.499]; creatures cast per game 3.84 [3.74, 3.94]; flash cast at instant speed 141/3,786 = 0.037; flash on the opponent's turn taken 11/141; ninjutsu taken 92/271 = 0.339; removal on the highest-power enemy 2,103/2,156 = 0.975. CORRECTION appended to the 13a flash addendum: Enduring Curiosity IS offered at instant speed on CP7's own turn (1,684, taken 9); never on the opponent's turn. bc.pt census (record_census.sh, 25 CP7 games, seed 13700) running, then levels.
- 2026-09-15 15:52Z WSL (13b -> 13c chain): rl/chain_13bc.sh launched detached 15:52:27Z (log rl/artifacts/v7/13/chain_13bc.log, lines C13C|...), pgrep-verified (time, chain_13bc count, 13a/13b chain+pipeline count: 15:53:44Z 1 2). It waits for B13|done, then for no resident policy server / driver JVM (30 min cap, else it does not launch), checks bc.pt exists, starts a fresh 18 h keepalive (cmd.exe /c start /min wsl ... sleep 64800; interop checked: cmd_ok), and launches rl/phase13.py detached (log rl/artifacts/v7/13/c/phase13.log; L13|block / L13|check / L13|level lines; state rl/artifacts/v7/13/c/state.json, lane /tmp/rl_13_M_B). Do not edit phase13.py, make_phase13.py, the battery scripts or record_census.sh from now on while chains wait.
- 2026-09-15 ~16:05Z WSL (13b census of bc.pt, rl/record_census.sh bc.pt BenchDimir cp7 25 p13_bc 13700 - argmax-classes play vs CP7, 25 games, transcripts kept, cand_refers_pool=True; rl/artifacts/v7/13/bc/census_bc.txt): W/L 10/15 (a census, not a level); HABITS vs the pre-registered clauses: self-destroy 2/120 = 0.017 [0.005, 0.059] < 0.2 MET (CP7 0.007); counterspells taken 22/35 = 0.629 [0.463, 0.768] - the [0.2, 0.5] band NOT MET (above it; CP7's own 0.472 [0.446, 0.499], intervals overlap); creatures cast per game 3.88 [2.99, 4.77] >= 3 MET (CP7 3.84). So 'habits cloned' holds on 2 of 3 clauses. Also: flash cast at instant speed 13/75 = 0.173 (CP7 0.037), removal on the highest-power enemy 24/24, ninjutsu 2/9, turns/game 17.8. Levels (three readouts) next in the chain.
- 2026-09-15 16:15Z WSL (13b levels, SAMPLED readout of bc.pt, rl/run_13_levels.sh via battery_p12s.sh, row seed 930000): vs CP7 33/100 = 0.330 [0.246, 0.427] (17.2 turns, 0 stalls); vs heuristic 39/50 = 0.780 [0.648, 0.872]. Phase 12's best sampled CP7 level was 0.22 [0.150, 0.311] - bc.pt's point is above it, the intervals overlap; 'competent start' needs >= 0.35 on sampled OR two-stage: sampled misses by 0.02, two-stage pending. Two-stage then argmax-classes rows running (~40 min); rl/artifacts/v7/13/levels/levels.txt.
- 2026-09-15 16:57Z WSL (13b ROW WRITTEN + 13c LAUNCHED): rl/V7-VALIDATION.md '13b — the clone'. Levels of bc.pt vs CP7 sampled 0.330 [0.246, 0.427] / two-stage 0.310 [0.228, 0.406] / argmax 0.320 [0.237, 0.417]; vs heuristic 0.780 / 0.740 / 0.740. SCRIPT FAULT (not a failed measurement): run_13_levels.sh grepped ^XDECKS (battery_p12s.sh) and missed battery_xdeck.sh's XDECK| lines, so run_13b.log marks the two-stage and argmax rows L13|FAIL; numbers read from the rows' probe files; fixed (^XDECKS?|). The same mismatch the other way round was in the generated phase13.py (phase12's battery() kept only XDECK| lines: the sampled readout would have parsed 0/0 at every 13c level) - fixed in make_phase13.py (accepts both prefixes; tested on a real XDECKS line), phase13.py regenerated and swapped atomically BEFORE 13c launched. Readings: card-level clone NOT met by the letter (priority 0.897 of ceiling; card-swap text dp 0.0424 vs 0.0430, missed by 0.0006, overlapping; flips 0.207 vs 0.119, same-row separation 0.42 vs 0.10) -> 'type-level clone again' recorded with those caveats; competent start NOT met (0.33 / 0.31 < 0.35, bar inside both intervals; clear above Phase 12's sampled start 0.12); habits 2 of 3 (counterspells 0.63 above the band). chain_13bc.sh blocked on its keepalive step (WSL-side cmd.exe interop of 'cmd.exe /c start' never returned; the keepalive itself started) - unblocked with rl/unblock_13c.sh (pid-checked kill of that interop process only). 13c LAUNCHED 16:55:38Z (rl/phase13.py, pid 124516), pgrep-verified 16:56:45Z: controller, lane rung0_lane_league.sh, learner server 7950, driver 7912, keepalives x3 (newest 18 h from 16:55Z). WATCH rl/artifacts/v7/13/c/phase13.log: L13|block|n=..|trained=a->b|opp=..|wr=.. per 256 episodes; L13|check|M_B|... per block (25 CP7 argmax games, dimir counters); L13|level|M_B|point=train|trained=..|sampled_cp7=..|twostage_cp7=..|argmax_cp7=..|graduated=.. every 1,024; L13|grad / L13|done. Lane log /tmp/rl_13_M_B/lane.log; state rl/artifacts/v7/13/c/state.json (resumable: python3 rl/phase13.py). Stop cleanly: touch rl/artifacts/v7/13/c/STOP (after the current block). --hours 12 from 16:55Z.

## Amendment 1 — the 2,048 level is make-or-break (user decision, 2026-09-15 20:15Z)

Registered before any training block past 1,024 had reported (last log line at
registration: the 1,024 level). The 1,024 level: sampled CP7 0.220 [0.150,0.311],
two-stage 0.350 [0.264,0.447], argmax 0.390 [0.300,0.488]; heuristic 0.72 / 0.72 /
0.74; bc.pt was sampled 0.330 [0.246,0.427] / two-stage 0.310 / argmax 0.320.
Pooled CP7 training blocks 0→1,024: 214/768 = 0.279 [0.248, 0.311].

At the 2,048 level (the controller's normal 100-game CP7 / 50-game heuristic level):

* **MAKE** (continue under this runbook to the 3,072 level) if either
  (a) the **sampled or two-stage** level vs CP7 is **≥ 43/100** (the smallest count
  whose Wilson lower bound, 0.337, clears bc.pt's 0.33), or
  (b) the pooled win rate of the **CP7 training blocks 1,024→2,048** has a Wilson
  lower bound **> 0.311** (above the 0→1,024 interval; with 768 games that is ≥ 265/768).
* **BREAK** otherwise: stop 13c gracefully after the level (STOP file), keep every
  checkpoint, write the 13c row with the reading "does not learn past the clone on
  this recipe in 2,048 episodes", and hand the next step to the user (candidates,
  not chosen here: KL-to-bc.pt, a larger or cleaner BC set, a different learning
  signal).
* The argmax readout is reported but cannot MAKE (as in the graduation rule).
* The pre-registered "forgets the clone" reading still applies at 2,048.
* Cannots: one seed; 100-game levels resolve only ~±0.09; rule (b) mixes a moving
  policy within each block and includes exploration, so it can MAKE but is not a level.
* Evaluator: `rl/p13_makebreak.py` (reads `rl/artifacts/v7/13/c/phase13.log`, prints
  `MB|MAKE|...` or `MB|BREAK|...`).
- 2026-09-15 22:49Z WSL (13c BREAK, Amendment 1): 2,048 level sampled CP7 29/100, two-stage 24/100, argmax 32/100; heuristic 31/33/30 of 50. rule (a) not met, rule (b) CP7 training blocks 1,024->2,048 168/768 lower 0.191 not met -> BREAK; STOP touched (rl/stop_13c.sh), controller finishes block 2,048->2,304 then exits. Row '13c' in rl/V7-VALIDATION.md. Next step is the user's.
- 2026-09-15 23:16Z WSL (13c EXITED): phase13.log ends `L13|block|n=8|h=6.34|main=M_B|trained=2048->2304|opp=cp7|W/L/D/S=59/197/0/0|wr=0.230|errors=0|wall=1634s|rc=0` then `L13|done|reason=stopfile|blocks=9|h=6.34|graduated=none|M_B_trained=2304`; pgrep phase13.py 0, RLDriverServer 0, no policy server. The extra block 2,048->2,304 (CP7, 59/256 = 0.230) is not part of the 13c verdict. Box handed to Phase 14 (rl/PHASE14-DIAG.md).
