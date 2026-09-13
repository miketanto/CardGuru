# PHASE8-DECKS — does the v7 recipe survive a real deck, and does a diverse league help? (runbook + pre-registration, 2026-09-14; v7/lane-d = 1c458fa)

Why (chat, after OVERNIGHT-7D): every v7 number so far is W0Base, a mono-white
creature mirror, and the one league tried was two frozen ancestors of the
policy itself — it overfit to them. Two questions, in order:
(Q3) does the C1 recipe train on **BenchDimir** (a real constructed
midrange deck: removal, instants, payment choices) and where does it land
against v6's Dimir result; (Q4) does a league of **diverse strategies across
decks** (mono-white aggro, Dimir midrange, Burn) improve a policy where the
ancestors-only league hurt it.

Rules that bind (unchanged): CLAUDE.md; HANDOFF-V7.md §K environment + §L;
rl/OVERNIGHT-7D.md STATE lessons — **the WSL VM dies without an open
session** (keep a `wsl -e bash -lc 'sleep 10800'` background task alive and
re-arm it; verify every detached launch with pgrep a minute later), **at
most two policy servers + two driver JVMs at once** (11 GB box), side
batteries one at a time, the lane's `server.log` race and `jobs.log` fixes
are in, `--argmax-classes` works on the serving path (fixed protocol for
every battery here). Wilson; ≥ 100 games per level; pre-register what a
change cannot move; correct in the open; commit + push after each finding;
commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
Checkpoint a dated STATE line at the bottom of THIS file after every step.

Reference points (all fixed protocol unless marked):
- v6 Dimir (`rl/DIMIR-V6-2K-RESULT.md`, `rung0_lane.sh BenchDimir BenchDimir`,
  entattn, one seed, D0+TWIN pooled = two samples of the same matchup):
  D0 **.555 [.486, .622]** at 1024, .585 [.516, .651] at 2048; D1 .290 at 1024, .430 at 2048.
- v7 C1 on W0Base: D0 0.86 [0.81, 0.90] pooled 2 seeds at 2048; L0 (+1024 heuristic)
  0.91 vs D0, 0.80 vs CP7; the ancestors-only league L1: 0.68 vs D0, 0.67 vs CP7.
- Consult volume: BenchDimir ≈ 126 consults/game (7a amendment: 506/4 with the
  filter) vs W0Base ≈ 20–40 → expect ~3–4× slower episodes; at 58 ms per stored
  consult the update alone is ~7 s/episode → ~1.3 h per 512 episodes (+ batteries).
  Measure it in the first 512 and write it down; if a seed to 1024 exceeds 6 h,
  drop to one seed and say so.

## Phase A — prepare (no lane running; check `pgrep -fc 'rung0_lan[e]'` = 0)

A1. **Dimir census set.** The census tools need a consult set on the deck:
    `rl/artifacts/v7/wire3a/mcL_off_BenchDimir.jsonl` (7a amendment, PREFER=1
    echo, 4 games) exists on disk; record a larger one on driver 7911 with the
    three echo policies (p1 / p99 / sf, 8 games each, the 7c_W0Base pattern) as
    `7c_BenchDimir_{p1,p99,sf}.jsonl`. `v7_land_census.py` counts land plays
    by lands in play — on Dimir also report P(cast) by lands (the tool may
    need a `--type` switch; add it, test).
A2. **Lane for the league across decks.** Extend `rl/rung0_lane_league.sh`
    with `R0_OPP_SPEC="kind:arg:deck,..."` entries used per 512-block in turn
    (block i uses entry i mod n): `heuristic::BenchDimir.dck`,
    `cp7::BenchBurn.dck`, `rl:/path/ck.pt:BenchDimir.dck` (frozen eval server
    on OPP_PORT serving that checkpoint, `-Drl.oppDeck` from the spec). The
    agent's own deck stays `$BASE`. Log the choice per block as `R0_OPP|`.
    Verify the v7 hello carries both decklists on a cross-deck job (5b had
    BenchDimir; `rl/wire_validate.py` on 100 consults of a 4-game smoke).
A3. **Cross-deck battery script** `rl/battery_xdeck.sh <ckpt> <agentDeck> <out>`:
    100 games each, fixed protocol, own server/driver ports (7947/7913), one
    at a time: vs heuristic on W0Base / BenchDimir / BenchBurn and vs CP7 on
    the same three (`rl.aiSkill` 6, `rl.stopTurn` 60; stalls reported). Six
    rows = "the suite". Smoke 4 games first.
A4. **Pre-register** (append to rl/V7-VALIDATION.md as "Phase 8 pre-registration"):
    * **8a — Dimir**: `rl/run_8a.sh` = the C1 recipe exactly (lr 3e-5, 1 epoch,
      logit bound 5, AdamW wd 0.01 heads, `--adv-norm auto --target-kl 0.02
      --argmax-classes`, filter + attack-budget build) on
      `rung0_lane.sh BenchDimir BenchDimir 1024 <seed>`, seeds 0 and 1
      sequential, batteries at 512 and 1024 (D0 / D1 / TWIN = second D0 sample,
      100 games each) plus the suite (A3) on ck_1024; land census + P(cast)
      census + type census on every ck; `jobs.log` kept for stalls.
      Readings: **trains on Dimir** if pooled-2-seed D0 at 1024 (200 games) is
      clear above 0.5 and the sampled last-4 rate at 1024 is clear of the
      first-4; **vs v6**: state whether the pooled D0 interval is above /
      overlapping / below v6's .555 [.486, .622] — parity is a finding here
      (v6 needed a deck-specific encoder; v7 is the deck-agnostic one);
      **not collapsed** as in C1 (argmax-PASS in [5 %, 90 %], gap > 0.5,
      entropy > 0.3, logits inside the bound); **behaviour**: does it cast
      instants at instant speed (the `holdsInstant` / yield counters), does
      it keep removal for threats (TARGET census), does it play its lands.
      Cannots: beat v6 at 2048 (not run); the payment sub-consult is still
      the engine's; CP7's Dimir strength is not calibrated (the suite gives it
      as a by-product); one deck says nothing about Burn.
    * **8b — diverse league**: **L2** = the W0Base policy L0 ck_3072 continued
      +1024 episodes on W0Base with `R0_OPP_SPEC` rotating per block:
      `heuristic::BenchDimir.dck`, `cp7::BenchBurn.dck`,
      `rl:<8a s0 ck_1024>:BenchDimir.dck`, `heuristic::BenchBurn.dck`
      (four blocks of 256 if the lane allows `R0_EVERY=256`, else two of 512
      with the first two entries). **Control = L0** (already run, same
      checkpoint, +1024 vs the heuristic on W0Base). Yardstick = the suite
      (A3) on L0 ck_3072 and L2 ck_3072 (600 games each, pooled and per row)
      + the home battery + head-to-head L2 vs L0 (100 games, stalls separate).
      Readings: **diverse league helps** if L2's pooled suite rate is clear
      above L0's AND the home D0 is not clear below L0's 0.91; **hurts** if
      the suite is clear below; else "no difference shown at n=600". Cannots:
      one seed; the pool is fixed-strength (no PFSP weighting, no refresh);
      the trainee plays one deck (deck-general play is 8c, not run); CP7 on
      Burn is CP7's Burn, not a trained Burn policy.
    * **8c (only if 8a trains and time remains)**: the Dimir trainee variant —
      L2d = 8a s0 ck_1024 continued +1024 on BenchDimir with the same spec
      (the W0Base opponent entry = `rl:<L0 ck_3072>:W0Base.dck`), same
      yardstick against its own control (8a continued +1024 vs the heuristic).


**Amendment (2026-09-13 17:40 next-session clock; decided by the user
before any Phase B result was read; development-phase budget).** Games
per row stay at 100 (the project rule; n=100 is already +-0.09); the
NUMBER of rows is cut:
1. **8a**: at 512 only D0 (heuristic on BenchDimir); at 1024 D0 and D1;
   TWIN on Dimir is dropped entirely (it is a second D0 sample, not a
   second matchup) — the lane's `R0_ROWS="D0"` / `R0_ROWS_FINAL="D0 D1"`
   knobs (a skipped row prints `LB=skip`). Seed 1 runs only if seed 0's
   1024 reading is worth confirming: clear above 0.5, or inside v6's
   [.486, .622]; the decision is stated in the 8a row. With one seed the
   "trains on Dimir" reading is read on 100 games (a level, not the
   pooled 200 the original text asked for) and says so.
2. **The cross-deck suite is four rows**: the heuristic on W0Base /
   BenchDimir / BenchBurn + CP7 on the checkpoint's home deck only
   (`rl/battery_xdeck.sh` default `ROWS`; 400 games per suite).
3. **8b**: one battery row per block (D0 on the home deck, `R0_ROWS="D0"`),
   the four-row suite on L2's final checkpoint (labelled ck_4096 in the
   lane's absolute count = L0 ck_3072 + 1,024) and on L0 ck_3072, plus
   the head-to-head (`SKIP_CP7=1` in `rl/hard_battery.sh`: no duplicate
   CP7 row). The "helps / hurts" readings are read on the pooled 400-game
   suites instead of 600.
Everything else in the pre-registration stands.


**Amendment 2 (2026-09-13 19:10, user; two-tier game budget, replaces the "100 games per row" clause above).** Interim battery points (every point before a run's final one) and every cross-deck suite row: 50 games, labelled "development probe" with their Wilson interval, go/no-go only, never a level. A run's final point: 100 games per row, the only point called a level. The suite is read POOLED across its four rows (200 games); per-row numbers are descriptive. Knobs: R0_EVAL_G_INTERIM=50 (both lanes; R0| rows carry games=N), G=50 in battery_xdeck.sh. Also decided: 8a seed 0 STOPPED at 512 (the reading is decisive; 1024 cannot rescue a never-cast argmax policy), seed 1 not run; 8a-b (C1 + --adv-norm batch, one seed, 512, probes 50 at 256 / level 100 at 512) runs NOW before 8b; if it rails too, 8a-c = C1 + --target-kl 0.1; if 8a-b trains its ck_512 is the 8b Dimir entry; if neither trains, 8b uses cp7::BenchDimir.dck in that slot and says why.

## Phase B — run, sequential on the one GPU (two servers max)

B1. `run_8a.sh` seed 0 detached under a keepalive; read the 512 battery and
    the throughput; write the seed-0 interim (as "C1 seed 0 interim" did);
    seed 1; pooled 8a row. Suite on both ck_1024 (one at a time).
B2. L2 (needs 8a s0 ck_1024 for its `rl:` entry) detached; batteries each
    block; suite on L2 ck_3072; suite on L0 ck_3072 (once; it is the control
    for everything); head-to-head; the 8b row.
B3. 8c if warranted; else write why not.
B4. Handoff: UPDATE line + §M prompt in rl/HANDOFF-V7.md with the two one-line
    answers and the owed items.

## STATE (append dated lines; newest last)
- 2026-09-14 (start): nothing running; Phase A not started.
- 2026-09-13 16:55 (WSL 16:50; the runbook date 2026-09-14 is the session clock, the WSL clock is a day behind): A1 DONE - rl/record_8a_census.sh recorded 7c_BenchDimir_{p1,p99,sf}.jsonl on driver 7911 (8 games each, 292/311/300 consults = 903 with consults; echo win rates .625/.375/.625, ~37 consults per game, ~22 turns - NOT the ~126 the runbook expected from the PREFER=1 mcL_off set: the p1/p99 echoes cast less); rl/v7_land_census.py --type {LAND|SPELL} (LAND output byte-identical to census.txt: s0 ck_2048 lands>=3 140/219; SPELL on the mcL_off set = P(cast) by lands, tag SPELLCENSUS); rl/BenchBurn.dck copied from Mage.Tests (the runbook names it; it was never in rl/). Log rl/artifacts/v7/8a/record_census.log.
- 2026-09-13 17:50 (WSL 17:00): A2 DONE - rl/rung0_lane_league.sh R0_OPP_SPEC="kind:arg:deck,..." (heuristic | cp7 skill 6 | rl frozen ckpt; -Drl.oppDeck per entry; R0_OPP|kind=..|arg=..|deck=.. per block; R0_OPP_CKPTS kept as the old rl-only form). Cross-deck check: a 4-game W0Base-vs-BenchDimir echo job (8x_W0Base_vs_BenchDimir.jsonl, 133 consults) reports oppDeck=BenchDimir.dck and its v7_opp_deck_name carries the Dimir cards (0 W0Base names), wire_validate ok - the v7 HELLO carries no decklists (its keys are dims/emb only); the decks ride on the consults (own hand/ents + v7_opp_deck). Smoke rl/smoke_xdeck_league.sh (rl/artifacts/v7/8a/smoke_xdeck_league.log): from C1 s0 ck_2048, three 64-episode blocks heuristic:BenchDimir (45/64, 0.67 g/s) / cp7:BenchBurn (17/64, 0.98 g/s) / rl(ck_2048):BenchDimir (56/64, 0.60 g/s, 4 opp-server conns), 4-game batteries between, rc=0. First attempt failed: the two job-line substitutions had not applied (the job still said -Drl.opponent=rl -> connection refused on 7961); fixed. A3 DONE - rl/battery_xdeck.sh (smoke rl/artifacts/v7/8a/smoke_xdeck_suite.log: 4 rows x 4 games on C1 s0 ck_2048/W0Base: heuristic W0Base 4/4, BenchDimir 4/4, BenchBurn 1/4 (17 turns - Burn races), CP7 W0Base 3/4 with 1 stall; XDECK|pooled line). A4 DONE - "Phase 8 pre-registration" appended to rl/V7-VALIDATION.md + the AMENDMENT (user, before any Phase B result): 100 games per row, fewer rows - 8a D0 only at 512, D0+D1 at 1024, no TWIN, seed 1 conditional; suite = 4 rows (heuristic x3 decks + CP7 on the home deck); 8b one D0 row per block, 4-row suites, H2H without the CP7 duplicate. Knobs: rung0_lane.sh + league R0_ROWS / R0_ROWS_FINAL (LB=skip), hard_battery.sh SKIP_CP7=1. Runners written: rl/run_8a.sh (SEEDS default "0"), rl/run_8b.sh.
- 2026-09-13 18:05 (WSL 17:02): B1 LAUNCHED - rl/run_8a.sh seed 0 detached (log rl/artifacts/v7/8a/run_8a.log; lane /tmp/rl_8a_s0, driver 7910 / server 7940; keepalive Bash task bgvl4f9qj started 16:40, 3 h - RE-ARM by ~19:30). Verified by pgrep after a minute. trained=0 D0 row 0/100 (untrained loses in ~20 turns; D1/TWIN print skip as the amendment asks). THROUGHPUT: first 64-episode job 0.68 games/s at conc 4 (50.7 consults per game, 20.5 turns) = ~95 s per job -> 512 episodes ~15 min of play + updates: the runbook fear (~1.3 h per 512) does not materialise on Dimir; the 512 battery is expected ~17:25 WSL. Idle driver 7912 (league smoke) stopped: the lane stops only its own port now.
- 2026-09-13 18:25 (WSL 17:22): 8a seed 0 at 320 episodes: the C1-style dead stretch, sampled (jobs 2-5: 0/64 each, 1 stall) with consults per game CLIMBING 51 -> 84 -> 115 -> 143 -> 137 (the losing Dimir policy consults more, not less: activations/payments on a board it cannot close) and throughput falling 0.68 -> 0.19 games/s; update_s 70-90 s for ~4,500 stored consults (~18 ms per consult, below the 58 ms 5d figure); KL budget stopped 4 of the first 8, none of 9-10 (approx KL 0.014 / 0.004); entropy 0.18-0.33, max |logit| 4.79. Projected: ~7 min per 64-episode job -> the 512 battery ~17:50 WSL, 1024 ~18:50 WSL (well under the 6 h bar).
- 2026-09-13 18:55 (WSL 17:50): 8a SEED 0 AT 512 = COLLAPSE TO "LAND, PASS": D0 0/100 [0.000,0.037], attacks 0/0 blocks 0/0 (no creature ever), 3.6 actions per game vs 124 consults; census ck_512: argmax-SPELL 0/257, P(SPELL) <= 0.01 at every land count, argmax-PASS 58 %, LAND 190/221; sampled 3/512 wins (all after job 1). Interim section "8a - seed 0 interim at 512" written (the SPELL census pre-stated as the deciding not-collapsed counter on Dimir; the 1024 rule: still 0/100 -> failed gate, no seed 1; follow-up arm 8a-e = C1 + --ent-coef 0.01 to 512, after 8b). Lane continues to 1024 (~18:50-19:00 WSL). Keepalive re-armed (task bd74u6xgx, 3 h from 18:50).
- 2026-09-13 19:05 (WSL 18:00): CORRECTION written under the interim: --ent-coef already defaults to 0.01 (C1 carries it) -> "8a-e" void; replacement follow-up 8a-b = C1 + --adv-norm batch (mechanism test: all-lost batches centre to zero instead of pushing every taken action down), one seed to 512, after 8b. Lane at ~600 episodes.
- 2026-09-13 19:20 (WSL 18:15): 8a seed 0 STOPPED at 512 by decision (rl/stop_8a.sh; 576 episodes, 19 updates), post-processed to rl/artifacts/v7/8a/s0 (STOPPED.txt); row "8a - seed 0: STOPPED at 512 by decision" written (trains: NO; not-collapsed clauses hold while the SPELL census says collapsed - a clause-set limitation recorded; vs v6 not made as pre-registered: no valid v6 512 level). Amendment 2 (two-tier budget) written in both docs; lanes got R0_EVAL_G_INTERIM. 8a-b LAUNCHED 17:57 WSL (rl/run_8ab.sh; log rl/artifacts/v7/8ab/run_8ab.log; lane /tmp/rl_8ab_s0; 7910/7940), pre-registration "8a-b pre-registration" written at launch; verified by pgrep; expect the 256 probe ~18:35 WSL and the 512 level ~19:15 WSL.
