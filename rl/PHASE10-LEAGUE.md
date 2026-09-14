# PHASE10-LEAGUE — per-deck self-play leagues with exploiters, then cross-deck (runbook + pre-registration, 2026-09-14; v7/lane-d)

Why (chat, 2026-09-14): the v7 policies look like one-trick overfits, and
Phase 9 P1 found the reason is partly architectural — the candidate token
is built from its action type and a 40-float row only (`v7_net.TokenBuilders`:
`cand_mlp(ctype_emb, cand)`), the card's embedding reaches it only through the
`refers_to` attention bias, which starts at zero behind a zero-init output
projection and never moved (≤ 0.0027 after training; card swaps move the
output by < 1e-4 in every subject). Decision (user, 2026-09-14): **fix the
candidate-to-card path first, then run fresh per-deck leagues.** Design (user):
one main learner per deck that specialises in it and improves by self-play,
one exploiter per main; after the mains are "kind of good" on their own deck,
introduce the other decks' mains into each league; see whether that yields
general capability.

Rules that bind: CLAUDE.md; HANDOFF-V7.md §K + the latest section; the
operational lessons in rl/OVERNIGHT-7D.md and rl/PHASE8-DECKS.md STATE
(**WSL VM dies without an open session** — use the session-independent
keepalive the Phase 8 agent used (`cmd /c start /min wsl -e bash -lc "sleep 36000"`
or equivalent) and verify every detached launch with pgrep a minute later;
**at most two policy servers + two driver JVMs at once** on the 11 GB box;
kill only via script files whose own name cannot match their pattern; never
edit a lane script or server-side Python while a lane runs; the server.log
race + jobs.log fixes are in; `--argmax-classes` works). Wilson intervals;
pre-register; correct in the open; commit + push after each finding; commit
messages end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
Append a dated STATE line at the bottom of this file after every step.
**Coordination:** a Phase 9 probe agent may still be running (`rl/probes/`,
P2/P3 may start a server on 7947 and a driver on 7911). Do not edit
`rl/probes/*` while it runs; before launching any lane, check
`pgrep -fa 'policy_serve[r]|RLDriverServe[r]'` and wait until no probe
server/JVM is resident.

## Phase A — build and verify (no lane running)

A1. **Candidate-to-card path, behind a flag.** `policy_server.py --cand-refers-pool`
    (default OFF = today's network bit-for-bit). ON: in `TokenBuilders.forward`,
    `refers` ([B, K, T_wire] multi-hot over game/players/ents) restricted to the
    entity slice, row-normalised, pools the entities' `[c, unk, ent-fields]`
    (the same `x` the zone MLPs read) into `[B, K, d_c+1+64]`; a new
    `cand_ref = Linear(d_c+1+64, d)` with **default (non-zero) init** adds it to
    the candidate token before masking. The same for `opp_act` with
    `opp_act_refers` if cheap (state which). Checkpoints without the new
    parameter load with the flag off exactly as before; with the flag on they
    load `strict=False` and say so. Tests: an equality test (flag off →
    identical outputs to HEAD on a fixture batch), a sensitivity test (flag on,
    untrained net: swapping one referenced entity's card id changes that
    candidate's logit by > 1e-3), 13+ server tests, `rl/v7_check.py` 15/15.
    Commit.
A2. **Verify with the Phase 9 probe** (after the Phase 9 agent is done with
    `rl/probes/cardswap.py`, else copy it): P1 on a fresh untrained net with
    the flag ON vs OFF, W0Base + Dimir consult sets. Pre-registered gate:
    ON's mean Δp on text-only swaps ≥ 0.01 AND ≥ 10× OFF's; otherwise the path
    does not carry identity — fix (two attempts) or record a failed gate and
    stop Phase 10 (do not run a league on a network that cannot see cards).
A3. **Landfall deck** `rl/G1Landfall.dck` (+ copy to `Mage.Tests/`): a
    60-card green-based landfall deck from cards that exist in the pinned
    XMage (`Mage.Sets`) AND in `rl/artifacts/cards_v1/index.json` (both
    confirmed for: Plated Geopede, Scute Mob, Lotus Cobra, Oran-Rief
    Survivalist, Rampaging Baloths, Tireless Tracker, Harrow, Evolving Wilds,
    Adventuring Gear, Khalni Heart Expedition, Elvish Visionary, Steppe Lynx,
    Explorer's Scope, Nissa's Pilgrimage, Turntimber Symbiosis, Roiling
    Regrowth, Zendikar's Roil, Oracle of Mul Daya). Two colours at most, ~24
    lands incl. Evolving Wilds, the landfall payoffs as the creature base,
    land-search spells to trigger them. Resolve `[SET:num]` from the set
    classes. Smoke: 20 games heuristic-vs-heuristic mirror on 7911, games end,
    no exceptions, turns reported; a 4-game v7 wire check (`wire_validate`)
    so every card resolves to an embedding id (unknown count reported).
A4. **League controller** `rl/league10.py` (+ `rl/run_league10.sh` detached
    wrapper): owns the schedule and the pools; runs ONE learner block at a
    time by invoking `rl/rung0_lane_league.sh` for that learner (its own OUT
    dir `/tmp/rl_10_<learner>`, resumed from its agent.pt, `R0_INIT` only for
    the first block) with the budget raised by one block and a single-entry
    `R0_OPP_SPEC` it chose; reads the block's per-job `RL|summary` lines from
    `jobs.log` (wins / losses / draws / stalls vs that opponent) into a
    persistent table `rl/artifacts/v7/10/results.tsv`; snapshots every
    learner's agent.pt after each block into `rl/artifacts/v7/10/pool/`
    (gitignored .pt, a committed `pool.tsv` index). Learners (6):
    `M_W` (W0Base), `M_D` (BenchDimir), `M_L` (G1Landfall) and their
    exploiters `X_W`, `X_D`, `X_L` (each plays its main's deck).
    All from FRESH nets (P10INIT, one seed per learner, recorded), all with
    `--cand-refers-pool`, recipe = C1 with `--adv-norm batch` (the Dimir fix;
    in a mirror the outcomes vary so it matters little): lr 3e-5, 1 epoch,
    logit bound 5, AdamW wd 0.01 on the heads, `--target-kl 0.02`,
    `--argmax-classes`, filter + attack-budget build, conc 4, cuda.
    Block = 256 episodes. Smoke the controller with 2 blocks of 32 episodes
    on W0Base before the real launch.

**Opponent selection per block (pre-stated):**
* Main `M_d`, stage 1 (own deck only): 40 % its own latest snapshot (true
  self-play, mirror), 30 % PFSP over its past snapshots and the exploiter's
  snapshots with weight (1 − p)² where p = M_d's win rate vs that snapshot
  in results.tsv (unplayed = 0.5), 15 % its exploiter's latest, 15 % the
  heuristic on the same deck (anchor against drift). The first block of a
  fresh main is the heuristic (a mirror of two random nets is fine too, but
  the anchor gives a battery-comparable first point).
* Exploiter `X_d`: always the frozen latest `M_d`. Reset to a fresh net when
  its win rate vs the current `M_d` over its last block ≥ 0.70 (its snapshot
  is added to `M_d`'s pool first) or after 4 blocks without that (snapshot
  added only if ≥ 0.55).
* Schedule: round-robin `M_W, M_D, M_L, X_W, M_W, M_D, M_L, X_D, M_W, M_D, M_L, X_L, …`
  (mains get 3 blocks per exploiter block).
* **Graduation** ("kind of good", pre-stated): a main graduates when its
  50-game development probe vs the heuristic on its own mirror (run after
  every 4th block) has a point estimate ≥ 0.65 (Wilson lower bound ≈ 0.51).
  **Stage 2** starts for everyone when ≥ 2 mains have graduated, or at
  controller hour 5 regardless (stated in the row if forced): each main's
  mix becomes 30 % self, 20 % PFSP own pool, 10 % exploiter, 10 % heuristic,
  **30 % the other graduated mains' latest snapshots (cross-deck: the
  opponent plays its own deck)**, PFSP-weighted among them. Snapshot the
  three mains at the stage-1/stage-2 boundary (`<main>_s1end`).
* Hard stop: controller hour 10, or morning; the controller finishes the
  current block and exits cleanly; every state is resumable.

## Phase B — run (detached under the keepalive), then evaluate

B1. Launch `run_league10.sh`; verify with pgrep; STATE line with the log path.
B2. Evaluation, one job at a time after the controller stops (100 games per
    final row, 50 per development row):
    * **Home**: each main's final snapshot vs the heuristic on its own mirror
      (100) and vs CP7 on its own deck (100).
    * **Unseen opponents** (the generalisation yardstick): each main playing its
      own deck vs the heuristic piloting BenchBurn, HoldoutControl and
      HoldoutMidrange (50 each, pooled 150), for BOTH `<main>_s1end` and final.
    * **Cross matrix**: final mains vs each other, own decks, 50 per pair.
    * **Exploiter health**: each exploiter's win rate vs its main per block
      from results.tsv (the league-health counter: should fall as mains harden).
    * **Card use**: P1 card-swap on the three final mains vs a fresh flag-ON
      net; and zero-shot keyword decks for `M_W`: W1Fly, W1Lif, W1Fst, W1Vig
      (W0Base with keyword creatures) vs the heuristic, 50 each, vs W0Base's
      home rate — does it use flying / lifelink / first strike / vigilance?

**Pre-registered readings:**
* **Q5 self-play per deck works**: a main's final home rate vs the heuristic
  (100) is clear above its first development probe AND ≥ the deck's reference
  where one exists (W: C1 0.86 [0.81, 0.90] — parity is fine given a fresh
  net and fewer episodes; D: 8a-b 0.41 [0.32, 0.51]; L: none, first number).
* **Q6 cross-deck introduction helps generalisation**: pooled unseen-opponent
  rate (150 per main, 450 pooled) for final clear above `_s1end`, AND home not
  clear below. "Hurts" if clear below; else "no difference shown". Confound
  stated in advance: final has more episodes than `_s1end`; the control is the
  exploiter-and-self-only continuation, which is NOT run (one GPU) — so a
  positive result is "cross-deck stage + more episodes", and the row says it.
* **Q7 card use**: final mains' text-only Δp vs the fresh flag-ON net:
  sharpened / preserved / erased (CIs); `M_W` "uses keyword X" if its rate on
  W1X is clear above its W0Base rate against the same heuristic (or,
  equivalently, the keyword deck does not drop it below W0Base while the
  heuristic's own W1X-vs-W0Base shift is the reference).
* **League health**: exploiters' win rates vs their mains trend down across
  resets; if an exploiter still beats its final main ≥ 0.7, the main is
  exploitable — say so.
Cannots: one seed per learner; a 10-hour budget (~2–3k episodes per main)
is small; the pool is small; landfall is a new deck with no v6 reference;
the payment sub-consult is still the engine's; cross-deck opponents only
include the three trained mains and the heuristic.

## Phase C — write-up

Rows in rl/V7-VALIDATION.md (A1/A2 gate, A3 deck smoke, the league run with
the per-block results table summarised, Q5, Q6, Q7, league health), a
"Phase 10 verdict" paragraph (two sentences with the numbers), a dated
UPDATE line + new section prompt in rl/HANDOFF-V7.md.

### Amendment 3 (sampling shortfall) — 2026-09-14, WSL ~11:00Z, controller at block 40 / hour ~7; written BEFORE any Q6 number exists

Found by the main session. `league10.py` draws each block's bucket from
`random.Random(10000 + n).random()`. The generator is sound (29 % of first draws ≥ 0.7 over
5,000 seeds), but which n values happened to land on main blocks left the realized mix well
short of the pre-registered one:

| | main picks | self | pfsp | expl | heur | cross |
|---|---|---|---|---|---|---|
| stage 1 (n 0–26; first blocks excluded) | 18 (6 per main) | 5 | 10 | 3 | **0** (pre-reg. 15 %) | — |
| stage 2 (n 27–39) | 9 (3 per main) | 4 | 2 | 3 | **0** (pre-reg. 10 %) | **0** (pre-reg. 30 %) |

The precomputed draws for n = 40..55 give cross only at n = 40, 41 and 54, and heur only at
n = 48. Stage 2 would therefore have ended at ~14 % cross instead of 30 %, about one
256-episode cross-deck block per main, which is too little for Q6 to mean anything.

**Stage 1 ran with no heuristic anchor at all.** That is a condition, and it goes into the Q5
row. The flat development probes coincide with it: M_D 0.48 → 0.46 and M_L 0.44 → 0.42 at
1024 → 2048, while M_W went 0.74 → 0.70. Stage 2 was forced at hour 5.10 (n = 27) with only
M_W graduated (probe 0.74 [0.604, 0.841] at 1024). So M_W's cross pool is every other main
(the forced rule), and M_D's and M_L's cross pool is M_W.

**Change (stops the controller cleanly after block 40, then resumes it; nothing else moves):**
in stage 2, before the bucket is used, each main gets a quota on its **realized** stage-2
shares (rc-0 rows, a fallback counted as what it fell back to). If its cross share is below
0.30, the pick is forced to cross; else if its heur share is below 0.10, it is forced to
heur; else the MIX2 draw stands. The draw is still consumed, so seeding, PFSP, resolve, the
exploiters and the hour-10 hard stop are identical. Forced picks are logged as
`bucket=cross(quota)` / `heur(quota)`. The quota restores the pre-registered stage-2 shares;
it does not change them. With 3 stage-2 blocks already played per main, the next picks per
main are forced to cross, cross, heur, then sampled; with ~3 h left, most mains reach ≈ 2
cross + 1 heur blocks in stage 2. Q6's confound statement (cross-deck stage + more
episodes; no control arm) is unchanged. The small cross-deck episode count is stated in the
Q6 row whatever it reads.

## STATE (append dated lines; newest last)
- 2026-09-14 (start): nothing running from Phase 10; Phase 9 agent may be running P2–P4.
- 2026-09-14 (session clock): A1 DONE (ce38ccc: --cand-refers-pool in v7_net/v7_policy/policy_server/p10_init_net, default OFF = HEAD bit for bit via golden fixture; 18/18 server tests, v7_check 15/15). A2 DONE - GATE PASSED: rl/p10_a2.sh (probe copy rl/p10_cardswap.py), ON text dp 0.0516 [0.0490,0.0542] vs OFF 0.00000 (pt 0.040, cost 0.043, type 0.069; strict flips 0.13), row 10 / A1-A2 in V7-VALIDATION.md, artifacts rl/artifacts/v7/10/a2/. Phase 9 probe still resident (server 7947 + JVM 7911) - no lane launched. A3 smoke running on driver 7913 (rl/p10_a3_smoke.sh -> rl/artifacts/v7/10/a3/).
- 2026-09-14 (session clock): A3 DONE - rl/G1Landfall.dck (R/G, 24 lands incl. 4 Evolving Wilds; 16 distinct cards, set numbers from Mage.Sets), smoke on driver 7913: 20-game heuristic mirror 9-11, 13.0 turns, 0 exceptions; 4-game wire check validate ok 136 consults, 0 unknown cards (3 stack-ability names only); row 10 / A3. Phase 9 probe no longer resident (pgrep empty). A4 controller rl/league10.py + rl/run_league10.sh written; smoke (2 blocks x 32 on W0Base: M_W vs heuristic, X_W vs frozen M_W) running.
- 2026-09-14 (session clock; WSL 03:57Z): A4 SMOKE PASSED (rl/artifacts/v7/10/smoke/: league10.log, results.tsv, pool.tsv, state.json): block 0 M_W vs heuristic 32 eps 9/23, probe0 0/4, probe 2/4, 74 s; block 1 X_W vs frozen M_W_00032 (rl opponent, opp server built cand_refers_pool=True from config, no strict=False) 12/20, 86 s; both rc=0, snapshots opt-stripped, L10|done|reason=max_blocks, driver 7912 stopped. Not exercised by the smoke (logic only): self/pfsp/cross buckets, exploiter reset, graduation, stage 2. Keepalive: hidden cmd start /min wsl sleep 43200 (12 h, started ~03:55Z WSL).
- 2026-09-14 (session clock; WSL 03:58Z): B1 LAUNCHED - rl/run_league10.sh detached (setsid nohup) at 03:57:44Z WSL, verified by pgrep after the launching call ended: controller python3 rl/league10.py, lane rung0_lane_league.sh W0Base (M_W, budget 256, seed 1), learner server 7950, driver JVM 7912 (opp server 7960 only in rl-opponent blocks), keepalive sleep 43200. LOG rl/artifacts/v7/10/league10.log; per block one line L10|block|n=..|h=..|stage=..|learner=..|gen=..|trained=a->b|bucket=..|opp=..|odeck=..|W/L/D/S=..|wr=..|probe=..|wall=..s|rc=..; also L10|probe0 / L10|grad / L10|stage2 / L10|reset / L10|error; at exit L10|done|reason=..|blocks=..|h=..|stage=..|graduated=.. then L10|wrapper|rc=. Tables rl/artifacts/v7/10/results.tsv, pool.tsv, state.json; lane state /tmp/rl_10_<learner>[_g<gen>]/ (lane.log, jobs.log, agent.pt); pool .pt in rl/artifacts/v7/10/pool/ (gitignored). Hard stop at controller hour 10 (~13:58Z WSL + the running block). Clean stop: touch rl/artifacts/v7/10/STOP. Resume: rerun the launch line (state.json; a running block is re-run with the same opponent). NEXT at L10|done: check pgrep empty, then setsid nohup bash rl/p10_eval.sh > rl/artifacts/v7/10/eval/eval.log (B2, one job at a time, E10| lines, E10|done), then Phase C rows + HANDOFF section.
- 2026-09-14 (WSL ~11:05Z): AMENDMENT 3 (sampling shortfall) written above STATE and in V7-VALIDATION '10 - pre-registration and Amendment 3': stage 1 drew heur 0/18 main picks, stage 2 cross 0/9 and heur 0/9; rl/league10.py stage-2 quota (f23c67b: cross < 0.30 -> cross(quota), else heur < 0.10 -> heur(quota), else MIX2; draw still consumed). STOP touched at 11:02Z; the controller finishes block 40 and exits; resume with the same launch line.
- 2026-09-14 (WSL 11:10Z): RESUMED after Amendment 3 - controller stopped cleanly at L10|done|reason=stopfile|blocks=41|h=7.21; STOP removed, nothing resident, relaunched with the same line (log appended to rl/artifacts/v7/10/league10.log), L10|resume|n=41|h=7.21 (clock persisted in state.json: hard stop stays at original hour 10). Post-resume n=41 M_D cross(quota) vs M_W_02816 on W0Base 67/256 = 0.262; n=42 M_L cross(quota) vs M_W_02816 on W0Base 58/256 = 0.227. Keepalive sleep 43200 alive (to ~15:57Z).
- 2026-09-14 (WSL 12:10-12:25Z): PAUSED BY THE USER for the card-swap check and replays. STOP touched 12:10Z; controller stopped cleanly after block 48 (L10|done|reason=stopfile|blocks=48|h=8.33). Interim card-swap on M_W_03072 / M_D_03072 / M_L_02816 written as "10 - interim card-swap check" in V7-VALIDATION (3d4c5dd). Replays: rl/replay_mains10.sh (replay_ck.sh now takes a deck, 51ea7a9; first runner attempt failed on relative output paths - nothing ran, rerun with absolute paths): M_W won vs heuristic (23 t) and CP7 (19 t); M_D lost both (15 / 19 t); M_L lost both (14 / 16 t); transcripts rl/artifacts/v7/10/replay/. RESUMED 12:24:50Z with `--hours 10.2` appended to league10.log (resume line h=8.45; the pause cost 0.12 h, the budget was raised by 0.2 h).
- 2026-09-14 (WSL 14:20Z): B2 LAUNCHED - league ended L10|done|reason=hours|blocks=62|h=10.32|stage=2|graduated=M_W; nothing resident; rl/p10_eval.sh detached at 14:19:46Z (verified by pgrep: runner, battery_xdeck, server 7948, JVM 7914). LOG rl/artifacts/v7/10/eval/eval.log; lines E10|home|<main>|XDECK..., E10|unseen|<main>|<final|s1end>|XDECK..., E10|cross|HARD|H2H..., E10|kw|M_W|XDECK..., E10|kwref|heuristic|<deck>|..., E10|p1|..., end E10|done=<utc>. Finals: pool/M_W_04096.pt etc. (state.json latest). NEXT at E10|done: Phase C rows (Q5 with the no-anchor stage-1 condition and in-league probes M_W 4096 0.46, M_D 4096 0.46; Q6; Q7; league health), verdict, HANDOFF section. Start nothing else (Phase 11 agent waits for E10|done).
