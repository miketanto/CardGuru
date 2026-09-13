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
