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
