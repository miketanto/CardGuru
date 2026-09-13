# OVERNIGHT-7D — imitation vs no imitation, and what a league adds (runbook + pre-registration, 2026-09-13 08:10 next-session clock; WSL clock 23:10 the evening before)

Decision (chat): C1 stops after seed 1 (`rl/stop_c1_parent.sh` killed the
parent `run_7c1.sh`; the seed-1 lane runs to its end untouched, ~02:50 WSL
clock). Seeds 0 and 1 of C1 are the **no-IL baseline** (2 seeds). Seed 2 is
resumable later (`rl/run_7c1.sh` skips finished seeds). Goal by morning:
(Q1) does behaviour cloning from CP7 before PPO beat PPO from scratch on
W0Base, and (Q2) what does a league opponent add on top of the C1 policy.

Rules that still bind: CLAUDE.md; HANDOFF-V7.md §K environment (one JVM per
class-init constant; never edit Java or server-side Python while a lane
runs — the seed-1 lane runs until ~02:50; drivers: 7910 is the lane's, 7911
is the recording driver, use 7912+ for new lanes; kill only via script
files whose own name cannot match their pattern; long jobs via one
`setsid nohup ... &` inside a `wsl -e bash -lc` call, logs on /mnt/c;
Wilson; ≥ 100 games per level; pool only finished seeds; write every
finding into rl/V7-VALIDATION.md and commit + push after each; commit
messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`).
Checkpoint your state into THIS file (a dated "STATE" line at the bottom)
after every step, so a fresh session can pick up cold.

## Phase A — while the seed-1 lane trains (no compile, no server-side edits)

A1. **Seed-1 post-processing script** `rl/post_7c1_seed.sh <seed>`: the tail
    of `run_seed` in `rl/run_7c1.sh` (append server.log to server_all.log,
    copy train.csv/lane.log/server_all.log, train_lines, battery, budget
    hits, census loop over ck_512..2048 with `v7_init_logits.py` and
    `v7_land_census.py`, census.txt, copy ck_2048.pt, **plus** copy
    `probe_*.txt`). Run it for seed 1 when `R0_DONE|W0Base|s1` appears in
    `/tmp/rl_7c1_s1/lane.log` (watch through wsl: `tail -F` on that file).
    Then `python3 rl/summ_7c1.py rl/artifacts/v7/7c1/s0 rl/artifacts/v7/7c1/s1`
    and write the **C1 row (two seeds)** in V7-VALIDATION.md against the four
    pre-registered readings ("C1 pre-registration"); the "seed 0 complete"
    section shows the shape. State plainly that C1 is a two-seed row by the
    decision above, seed 2 owed.
A2. **Java, source only** (`rl/xmage-src/`; compile in Phase B):
    `CP7TeacherPlayer extends mage.player.ai.ComputerPlayer7` and
    `rl.agent=cp7` in `EpisodeRunner` (mirror the cp7 opponent branch:
    `RangeOfInfluence.ONE`, `rl.aiSkill` 6, the fake match at line ~290 must
    also cover the agent seat), per the design in V7-VALIDATION "7d piece
    (1b) design": build the candidate list exactly as `RLPlayer.priority`
    (lines ~666–730: `getPlayable`, phantom-land filter, mana-ability
    filter unless `rl.manaCands`, same order) and the consult (`StateEncoder
    .encodeEntityView`, `forCard` rows, `CandMeta` with `v7AfterPlayable`,
    `RLKnowledgeWatcher.ensure`), call `super.priority(game)`, capture the
    first `activateAbility`/`playLand` of that window (override them;
    `ComputerPlayer6.act` may fire several — count `teacherMultiAct`),
    label `y` = matching candidate index by `sourceId|rule` (0 = passed,
    −1 = outside the set), then `policy.choose(view, cands, phi, meta)` with
    the label attached. Joint sites (`selectAttackers`/`selectBlockers`):
    build the same CombatMath candidate list `RLPlayer` builds (its
    `jointAttacks`/`jointBlocks`; lift them to package-static if needed),
    delegate to CP7, read the declared set from the game, label the matching
    candidate (−1 → `teacherJointMiss`). If the joint lift is not cheap,
    priority-only for tonight and say so in the row.
    Wire: `SocketPolicyClient` gets an optional per-consult `y` (int) —
    find where the consult JSON is assembled (`choose(view, cands, phi,
    meta)` ~line 353) and add `"y":<int>` only when set; hello gets
    `"teacher":"cp7"` when `rl.agent=cp7`. Server side is read-only tonight
    except `rl/wire_validate.py` may need to *accept* `y` (edit only after
    the lane stops — it is not imported by the running server; check).
    Summary counters: `teacherLabelled`, `teacherOutside`, `teacherMultiAct`,
    `teacherJointMiss` in the `fallbacks=` field.
A3. **`rl/v7_bc.py`** (new file; do not touch policy_server.py / v7_*.py):
    loads a recorded jsonl (the recorder's consult records; `rl/v7_init_logits.py`
    shows how to load a checkpoint and score every candidate of a recorded
    consult — reuse its loading path), keeps consults with `y >= 0`,
    cross-entropy over candidates with the label, AdamW, held-out 10 % of
    *games* (split by episode, not by consult) for early stopping, `--init`
    from a P10INIT-style init.pt (make one with the lane's P10INIT step or
    load `rl/artifacts/v7/7c1/s0`'s init shape: seed 10, cdim 94), writes
    `bc.pt` in the lane's checkpoint format (whatever `agent.pt`/`init.pt`
    carry: state dict + dims record + episodes=0 — inspect `torch.load` of
    `/tmp/rl_7c1_s0/init.pt` keys). Prints per epoch: train/held-out CE and
    top-1 agreement, then the type census and land census commands on bc.pt.
A4. **League lane** `rl/rung0_lane_league.sh`: a COPY of `rung0_lane.sh`
    (never edit the original while it runs) whose training jobs use
    `-Drl.opponent=rl -Drl.oppPort=$OPP_PORT` (EpisodeRunner line ~184; the
    C5 league mechanism) with a frozen eval-mode policy server on
    `$OPP_PORT` started from a checkpoint list `R0_OPP_CKPTS` (alternate per
    512-block, or per job: ck_1024 then ck_2048 of C1 seed 0 — record which).
    Batteries unchanged (D0/D1/TWIN argmax-classes, 100 games). It must
    honour `RL_DRIVER_PORT` (use 7912) and `R0_PORT` so it never touches
    7910/7940-7942. The init checkpoint: the lane creates `$OUT/init.pt`
    only if absent (verify at `rung0_lane.sh` ~line 114), so copying a
    checkpoint to `$OUT/init.pt` before launch starts from it; `resume_at`
    reads `episodes` from agent.pt — check whether an init.pt with
    episodes=2048 is treated as trained=2048 (we want the +512/+1024
    batteries labelled relative to the start; if the lane counts from the
    checkpoint's episodes, set the budget to 2048+1024 and read the rows at
    2560/3072).
    CORRECTION (checked 08:20): `rung0_lane.sh` ~line 114–120 regenerates
    `$OUT/init.pt` UNCONDITIONALLY with `p10_init_net.py`. Starting from a
    checkpoint needs an `R0_INIT` hook: `if [ -n "${R0_INIT:-}" ]; then cp
    "$R0_INIT" $INIT; else python3 $RL/p10_init_net.py ...; fi`. Put it in
    the league COPY now; add the same hook to `rung0_lane.sh` itself in
    Phase B once the seed-1 lane is idle (D-PPO uses it). Check how
    `resume_at` / `trained` is derived (grep `resume_at`, `agent.pt`,
    `episodes`) so an init.pt carrying episodes=2048 does not make the lane
    think it is already done — strip or reset the episode counter in the
    copied checkpoint if it does.
A5. Pre-register in V7-VALIDATION.md (one section, before any Phase B result):
    * **D-BC**: bc.pt from ≥ 20k CP7-labelled consults on W0Base (both
      seats). Readings: held-out top-1 agreement (report), BC battery 100
      games each D0/D1/TWIN (argmax-classes) — expected ≤ CP7's 0.68 vs D0.
      Cannot: beat CP7; say anything off W0Base.
    * **D-PPO** = PPO from bc.pt with C1's exact flags, 2048 episodes, seeds
      0 and 1, batteries every 512. **Q1 readings** (pooled two seeds vs C1's
      pooled two seeds, 200 games per opponent per point): "IL helps" if
      D-PPO's pooled D0 at 2048 has a Wilson interval clear above C1's, OR
      D-PPO's D0 at 512 is clear above C1's 512 (a faster start counts,
      stated separately); "IL hurts" if clear below at 2048; else "no
      difference shown at n=200". Also report the first-8-batch sampled
      wins (C1 seed 0: 14/256 — does BC remove the dead stretch) and the
      land census. Cannot: separate BC's effect from its consult budget;
      generalise off W0Base; call any of this a level from < 2 finished seeds.
    * **L0 / L1** from C1 seed 0 `ck_2048` (`rl/artifacts/v7/7c1/s0/ck_2048.pt`),
      1024 more episodes each, one seed: **L0** vs the heuristic (the same-
      compute control), **L1** vs frozen C1 checkpoints (ck_1024 / ck_2048).
      **Q2 reading**: L1's D0/D1/TWIN at +1024 vs L0's at +1024 (100 games
      each; one seed → only "clear of" counts, and the row says one seed);
      plus L1's rate against its league opponent per 512-block (from the
      TRAIN lines) as the behaviour counter. Cannot: claim a league level
      from one seed; say anything about self-play from scratch.
    Pre-state what each cannot move: BC cannot change the argmax k-copy
    bias (B7 is on); nothing here changes the attack-budget caveat.

## Phase B — at the seed-1 boundary (`R0_DONE|W0Base|s1`, ~02:50 WSL clock)

B1. Confirm nothing of C1 runs (`pgrep -fc 'rung0_lan[e]'` = 0, no
    policy_server on 7941; `stop_c1_parent.sh` already removed the parent).
    Run A1's post-processing + the C1 two-seed row; commit; push.
B2. Compile: `bash rl/sync_lane_b.sh`; restart 7911 alone
    (`bash rl/driver_server.sh start 7911 "-Dmage.randomPerThread=true
    -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7"`); 13 server
    tests + `python3 rl/v7_check.py` must still pass (server untouched, this
    is the regression check). A 4-game `rl.agent=cp7` smoke with the echo
    policy on 7911 through the recorder: the consults carry `y`, counters
    print, `rl/wire_validate.py` passes on 100 of them, faithfulness probe
    on 100 (`rl/probes/faithfulness.py`, 5b protocol).
B3. Record: `rl/record_5b.sh` pattern (server recorder, echo policy) with
    `-Drl.agent=cp7 -Drl.opponent=heuristic`, W0Base both seats (parity),
    `rl.consultBudget` 300, until ≥ 20k labelled consults (~700 games at
    3 games/s). Artifacts `rl/artifacts/v7/7d1b/` (jsonl gitignored, counts
    committed). Row "7d piece (1b) — recording" with the counters and the
    label type census.
B4. `python3 rl/v7_bc.py ... --device cuda` → `rl/artifacts/v7/7d2/bc.pt`;
    BC battery: the lane's `--frozen` path as B0 did (`rl/run_7b0.sh`) but
    100 games per opponent with `--argmax-classes`; land census + type
    census on bc.pt. Row "7d piece (2) — BC".
B5. Launch **D-PPO** (`rl/run_7d3.sh` = `run_7c1.sh` with ART `7d3`,
    `/tmp/rl_7d3_s<seed>`, `cp bc.pt $OUT/init.pt` before the lane call,
    seeds 0 1) detached, log `rl/artifacts/v7/7d3/run_7d3.log`.
B6. Launch **L0 then L1** (`rl/run_7l.sh`, driver 7912, R0_PORT 7950/7951,
    OPP_PORT 7960, ART `7l/{L0,L1}`) detached, in parallel with D-PPO if
    the GPU holds both (C1 used 4.9 GB of 12; watch `nvidia-smi`; if the
    second lane OOMs or D-PPO's update_s doubles, run L0/L1 after D-PPO
    instead and say so). Log `rl/artifacts/v7/7l/run_7l.log`.

## Phase C — morning readings

C1. `python3 rl/summ_7c1.py rl/artifacts/v7/7d3/s0 rl/artifacts/v7/7d3/s1`
    (the summariser is generic over the s<seed> layout) and the same for
    `7l/L0`, `7l/L1` (their rows are at 512/1024 relative or 2560/3072
    absolute — see A4). Write the **Q1 row** and the **Q2 row** against the
    pre-registration, with the pooled tables, the first-8-batch counters,
    the land census, and every cannot. Update HANDOFF-V7.md with a dated
    UPDATE line and a new §L prompt. Commit; push.

## STATE (append dated lines; newest last)
- 2026-09-13 08:10 (WSL 23:10): C1 parent stopped; seed-1 lane running; Phase A not started.
- 2026-09-13 08:50 (WSL 01:40): A1 DONE (rl/post_7c1_seed.sh; rl/wait_7c1_s1.sh detached in WSL, log rl/artifacts/v7/7c1/wait_s1.log - it runs post_7c1_seed.sh 1 when R0_DONE|W0Base|s1 lands; seed 1 was at its 512 battery at WSL 01:33, expect R0_DONE ~04:00-04:30 WSL). A2 DONE source-only (9e24145; PRIORITY-ONLY, joint lift not done). A3 DONE (e863751, smoke-tested on a synthetic-label recording, CPU). A4 DONE: rl/rung0_lane_league.sh (R0_INIT hook, R0_OPP_CKPTS per 512-block, RL_DRIVER_PORT 7912, R0_PORT 7950, R0_OPP_PORT 7960, R0_BATTERY_START=1; bash -n ok, not yet smoked). A5 DONE (V7-VALIDATION "7d overnight pre-registration"). FINDING: --argmax-classes is inert on the v7 serving path (act_v7 eval = plain argmax) - correction row written; fix in Phase B + re-battery C1 s0/s1 checkpoints in Phase C. Phase B scripts to write next: run_7d3.sh, run_7l.sh, record_7d1b.sh, smoke_cp7.sh, the rung0_lane.sh R0_INIT hook (apply only after the lane idles).
- 2026-09-13 09:00 (WSL 01:45): Phase A COMPLETE and pushed (0596ab9, d1f7d8e, 886ae2f). Seed 1 at 512: D0 0.61 [0.512,0.700] / D1 0.61 / TWIN 0.58 (plain-argmax protocol; seed 0 was 0.77) - block 2 training, R0_DONE expected ~04:00 WSL. Phase B scripts written + syntax-checked, NOT run: rl/smoke_cp7.sh, rl/record_cp7.sh, rl/record_7d1b.sh, rl/post_lane_seed.sh, rl/run_7d3.sh, rl/run_7l.sh. summ_7c1.py takes SUMM_FIRST/SUMM_FINAL (L lanes: 2560/3072).
  PHASE B, COLD-START ORDER (only after wait_s1.log shows WAIT7C1|end and `wsl -e bash -lc "pgrep -fc 'rung0_lan[e]'"` = 0):
  B1. `wsl -e bash -lc "cd /home/user/CardGuru && python3 rl/summ_7c1.py rl/artifacts/v7/7c1/s0 rl/artifacts/v7/7c1/s1"` -> write "C1 - two seeds" row in V7-VALIDATION.md (plain-argmax protocol, per the correction row); commit s1 artifacts WITHOUT *.pt; push.
  B2. Apply the scratchpad patch (a copy is rl/patch_phaseb.py if this session saved it there; else re-create: rung0_lane.sh R0_INIT + R0_BATTERY_START hooks + own-port driver stop; policy_server.py act_v7 eval -> _argmax_classes when ARGMAX_CLASSES; test test_act_v7_eval_honours_argmax_classes). Then `wsl -e bash -lc "cd /home/user/CardGuru && bash rl/sync_lane_b.sh 2>&1 | tail -3"`; restart 7911 alone: `bash rl/driver_server.sh start 7911 "-Dmage.randomPerThread=true -XX:+UseParallelGC -Dmage.playableCache=on -Drl.encoderV=7"`; `python3 -m pytest tests/test_v7_server.py -q` (14 tests) and `python3 rl/v7_check.py` (failures=0); then `bash rl/smoke_cp7.sh` (SMOKE| lines: hello_teacher=cp7, y present, validate ok, FAITH5B pass). WIRE-V7.md §8 entry for y/teacher. Commit.
  B3. `setsid nohup bash rl/record_7d1b.sh > /mnt/c/.../rl/artifacts/v7/7d1b/record_7d1b.log 2>&1 < /dev/null &` (~10-15 min; CP7 is ~3 games/s at conc 2). Row "7d piece (1b) - recording" from counts.txt (labelled fraction >= 0.9 gate, label type census).
  B4. `mkdir -p rl/artifacts/v7/7d2; python3 rl/v7_bc.py --init /tmp/rl_7c1_s0/init.pt --out rl/artifacts/v7/7d2/bc.pt --device cuda rl/artifacts/v7/7d1b/7d1b_s*.jsonl | tee rl/artifacts/v7/7d2/bc.log` (init.pt of s0 = seed 10 cdim 94; if /tmp/rl_7c1_s0 is gone use rl/artifacts/v7/7a/B0/init.pt = the same P10INIT seed 10). Census commands from the BC| lines. Row "7d piece (2) - BC" (the BC battery comes from D-PPO's trained=0 row).
  B5. `setsid nohup bash rl/run_7d3.sh > .../7d3/run_7d3.log 2>&1 < /dev/null &`  then B6. `setsid nohup bash rl/run_7l.sh > .../7l/run_7l.log 2>&1 < /dev/null &` (watch nvidia-smi; if OOM run 7l after 7d3). Monitors on the /c logs for 7D3|/7L|/R0_.
  C. Phase C per the runbook; plus re-battery C1 s0/s1 ck_512..2048 on the fixed server (script to write: frozen server per ck, 100 games D0/D1/TWIN, --argmax-classes) for the Q1 comparison.
- 2026-09-13 09:45 (WSL 03:45): B1 DONE - C1 two-seed row written (pooled 2048 D0 170/200 = 0.850 [0.794,0.893]; third land fails on seed 1: 0.38; seed 1 first-8 137/256 vs seed 0 16/256). B2 DONE - patches applied (rung0_lane.sh R0_INIT/R0_BATTERY_START/own-port driver stop; act_v7 honours --argmax-classes; test), sync_lane_b.sh OK, 14/14 server tests, v7_check 15/15, 7911 restarted (v7 flags), smoke_cp7.sh: 4 games / 60 consults all labelled (y act 60, pass 0, outside 0, multiAct 0; windows 793, autoPassEmpty 733), hello teacher=cp7, wire_validate ok, FAITH5B L3 25/1 L4 26/0 on 60 consults. B3 RUNNING: rl/record_7d1b.sh detached (log rl/artifacts/v7/7d1b/record_7d1b.log; counts.txt), Monitor armed. Gotcha: the RL|summary fallbacks field is space-separated k=v (no braces) - record_cp7.sh's counter grep prints nothing; read the probe files.
- 2026-09-13 09:50 (WSL 03:42): B6 LAUNCHED EARLY (GPU free, no dependency on BC): rl/run_7l.sh detached - L0 started from C1 s0 ck_2048 (R0_INIT ok, resume_at=2048, budget 3072, battery at 2048 first), then L1; log rl/artifacts/v7/7l/run_7l.log, R0 rows mirrored to rl/artifacts/v7/7l/lanes_R0.log by rl/tee_lane_rows.sh; lane state /tmp/rl_7l_L0, /tmp/rl_7l_L1. Recording at ~1456 labelled/100 games, 45 s per job: MAXJOBS=12 gives ~17.5k - relaunch with MAXJOBS=16 after the done line (resumable) to pass 20k.
- 2026-09-13 10:00 (WSL 03:55): B3 DONE - 14 jobs / 1,400 games / 20,735 labelled consults (all labelled, 0 passes by CP7, 0 outside, 0 multi-act; LAND 41 % / SPELL 59 %; CP7 0.684 [0.660,0.708]); row '7d piece (1b) - recording'. B4 RUNNING: v7_bc.py on cuda detached, log rl/artifacts/v7/7d2/bc.log -> bc.pt. L0 at its 2048 battery.
- 2026-09-13 10:15 (WSL 04:00): B4 BC DONE: rl/artifacts/v7/7d2/bc.pt (bc.log, census.txt): early stop at epoch 4 / best 1, held-out CE 0.713, top-1 0.606, type agreement 0.887 - vs the copy ceiling (mean log #copies of the labelled class 0.280 nats; label-first-of-class 0.833): BC learned CP7's TYPE, not its card choice; bc.pt census: argmax-PASS 0/1070, P(PASS) 0.03, entropy 0.58, gap 3.96, LAND 224/313, SPELL 348/368, ATTACK 279/279, BLOCK 207/207 (the shared head generalised 'never pass' to combat), P(land) at >=3 lands 0.80. B5 LAUNCHED: rl/run_7d3.sh detached at WSL 03:56 (log rl/artifacts/v7/7d3/run_7d3.log, rows mirrored to 7d3/lanes_R0.log; state /tmp/rl_7d3_s<seed>); its trained=0 battery = the BC battery (fixed protocol). Also running: rl/rebattery_c1.sh (server 7947, driver 7913; log rl/artifacts/v7/7c1/rebattery/rebattery.log, rows in rebattery/s<seed>/rows.txt), L0 (7l). BC row waits for the trained=0 battery.
