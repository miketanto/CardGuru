# PHASE12-CP7 — warm start to competence against CP7 before any self-play league (runbook + pre-registration, 2026-09-14; v7/lane-d)

Why (chat, 2026-09-14 ~22:10Z): the Phase 11 drill-down was stopped by the
user at its halfway point. Both mains were flat on the fixed yardsticks (Dimir
0.59 → 0.62 → 0.59 vs the heuristic, 0.17 → 0.20 vs CP7; landfall 0.49 → 0.41
→ 0.53, 0.37 → 0.12 vs CP7) while winning 70–87 % inside the league, and
Dimir's card habits swung through three full cycles between "cast everything"
and "hold everything" without converging. The user's reading, recorded as the
leading hypothesis in the Phase 11 rows: **self-play drift** — 90 % of the
training opponents were league-internal and moved with the learner, the only
fixed opponent was the heuristic at 10 %, CP7 was never trained against, and
no exploiter ever entered a pool. The one result in this project that kept
improving was a continuation against a fixed opponent (L0: W0Base 0.86 →
0.91 vs the heuristic, 0.80 vs CP7). Decision (user): **warm-start each main to
consistent competence against CP7 first, even if slow; the self-play league
comes after, seeded with the graduates.**

Rules that bind: CLAUDE.md; HANDOFF-V7.md §K + the latest section; the STATE
lessons in rl/OVERNIGHT-7D.md, rl/PHASE8-DECKS.md, rl/PHASE10-LEAGUE.md,
rl/PHASE11-DRILL.md (session-independent WSL keepalive for every long run and
pgrep verification a minute after launch; at most two policy servers + two
driver JVMs; kill only via script files whose name cannot match their pattern;
never edit a script a running job executes — swap atomically in a gap; the
per-census full transcripts are kept by `rl/record_census.sh`). Wilson; ≥ 100
games per level (25/50-game rows are development probes); pre-register;
correct in the open; commit + push after each finding; commit messages end with
`Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`. Append a dated STATE
line at the bottom of this file after every step.

## Trainees, opponent, recipe

* **Trainees (one seed each, starting snapshots):** Dimir = the latest Phase 11
  drill snapshot of `M_D` (`rl/artifacts/v7/11/drill/pool/`, ~6,400 episodes);
  landfall = the latest `M_L` (~6,144); white = `M_W_s1end`
  (`rl/artifacts/v7/10/pool/`, the white main's best point: 0.72 home probes,
  0.77 unseen) — not its declined final. All carry the card path
  (`cand_refers_pool` from the checkpoint config).
* **Opponent mix per 256-episode block (pre-stated):** 75 % CP7 (`rl.aiSkill`
  6) piloting the trainee's own deck (mirror), 25 % the heuristic on the same
  deck (an anchor against over-fitting CP7's particular lines). No self-play,
  no league, no exploiters in this phase.
* **Recipe:** the Phase 10/11 learner recipe unchanged — lr 3e-5, 1 epoch,
  logit bound 5, AdamW wd 0.01 on the heads, `--adv-norm batch`,
  `--target-kl 0.02`, `--argmax-classes`, filter + attack-budget build, conc 4,
  cuda. Only the opponents change, so the comparison with Phase 11 isolates the
  opponent mix.
* **Schedule:** blocks rotate Dimir, landfall, white (one lane at a time). A
  main that graduates stops training (its blocks go to the others); a
  graduated main's snapshot is frozen as the Phase 13 seed.

## Yardsticks

* **Graduation level (the goal):** a **100-game** battery vs CP7 on the own
  mirror after every 1,024 episodes of that main. **Graduated** = point
  estimate ≥ 0.70 AND Wilson lower bound ≥ 0.60 (70/100 → [0.604, 0.781]).
* **Guards:** at the same points, 50 games vs the heuristic on the own mirror;
  and, at the start and at graduation (or the end), the 3-deck unseen suite (vs
  the heuristic piloting BenchBurn / HoldoutControl / HoldoutMidrange, 50 each,
  pooled 150) — the same suite as Phase 10.
* **Per-block check:** after every trainee block, the Phase 11 census vs CP7
  (25 games, own mirror, `rl/record_census.sh` + the census tools, full
  transcripts kept), one compact `check` line per block with the Phase 11
  fields (Dimir: win rate, selfrem, counter, flash_opp, ninja, biggest, cpg,
  consults_pg; landfall: smallbig with solver_no_block, landsearch, cpg,
  consults_pg; white: win rate, blocks matching the combat search, attacks,
  cpg).
* **Throughput** measured on the first block of each main and written down
  (CP7 games are slower); if a main cannot reach its first 1,024-episode level
  within 4 hours, say so and continue.

## Pre-registered readings (per main)

* **Competent**: graduated as defined above.
* **Improving vs CP7**: the last 100-game CP7 level clear above the first
  (the starting snapshot's own 100-game CP7 battery, run before training).
* **Over-fit to CP7**: CP7 level up while the heuristic level or the unseen
  suite ends clear below its starting value — a CP7 specialist is not the
  competence this phase is for; the row says so.
* **Card habits converge** (Dimir): the selfrem counter falls and stays below
  0.3 over the last four checks (CP7's own is 0/164), counter selectivity stays
  within [0.2, 0.5] (CP7 ~0.33) over the last four checks, creatures per game
  ≥ 3 over the last four checks. "Oscillates" if any of these swings across
  its range again as in Phase 11 — the drift hypothesis predicts it will not
  under a fixed opponent.
* **Landfall**: small-into-big blocks where the search would not block fall
  and stay below the Phase 10 final's level; land search not held (cast rate
  ≥ 0.3).
* **Drift hypothesis test** (the reason for the phase): under a 100 % fixed
  mix, the fixed-yardstick levels rise and the card counters settle, where
  Phase 11's league mix produced flat levels and oscillation. If the levels
  stay flat and the counters still oscillate against CP7, the drift
  hypothesis is not supported and the coarse terminal reward is the leading
  explanation instead — say so plainly.

Cannots: one seed per main; CP7 at skill 6 only; CP7's lines are
near-deterministic, so a policy can learn exploits the unseen suite must catch;
the payment sub-consult is still the engine's; no claim about the later
self-play league (Phase 13) from this phase.

## Phase 13 (pre-stated, not run here)

A self-play league seeded with the graduates, with CP7 and the heuristic kept
in every pool as fixed anchors (proposed ≥ 25 % combined), loss-weighted
opponent selection, and the same fixed yardsticks every 1,024 episodes. Its
runbook is written only after Phase 12 has graduates.

## Amendment 1 (2026-09-14 22:24Z, before any data) — implementation choices

Recorded in the 22:24Z STATE line: the 75/25 mix realised exactly by the rotation
cp7, heuristic, cp7, cp7 per main; start point = CP7 100 + heuristic 50 + unseen 150
+ the 25-game CP7 census (M_W's unseen rows reused from Phase 10, same checkpoint and
suite); fixed battery and census seeds (paired points); the white check fields;
snapshots carry no optimiser state.

## Amendment 2 (2026-09-14 ~23:45Z, user decision; before any M_D level beyond the start point) — tonight is Dimir only

Scope narrowed to Dimir by the user for tonight, to benchmark the hardest deck
faster. **Landfall (M_L) and white (M_W) are paused after their start points**;
no M_L or M_W training block had run (the controller stopped gracefully after M_D's
block n=0 and its check, before the rotation reached M_L). Their start points stand
as measured (the 23:36Z STATE line) and their saved state is untouched
(rl/artifacts/v7/12/state.json: trained = start, blocks = 0; lanes /tmp/rl_12_M_L,
/tmp/rl_12_M_W not created) — **their readings are deferred, not dropped**; they
resume later with `--mains` naming them.

Everything else is identical for M_D: the fixed cp7, heuristic, cp7, cp7 rotation
(M_D's block n=0 was its rotation slot 0, cp7), the per-block 25-game CP7 check
(seed 12500), the 100-game CP7 level + 50-game heuristic guard every 1,024 episodes
(fixed seeds), the graduation rule (≥ 0.70 AND Wilson lower bound ≥ 0.60), the unseen
suite at graduation or the end, the same hour-10.5 stop from the original 22:24Z
start (~08:54Z; no new block after it) and the end phase for M_D only. Code:
`rl/phase12.py --mains M_D` (default = all three, the original behaviour).

What this changes for the readings: the per-main readings for M_L / M_W cannot be
made tonight; the drift-hypothesis test rests on Dimir alone (one seed, one deck), and
the row says so. Dimir gets ~3x the wall time it had in the rotation, so its level
points come every ~2 h instead of ~5 h.

## STATE (append dated lines; newest last)
- 2026-09-14 ~22:15Z WSL: Phase 11 drill-down being stopped by the user (rl/stop_drill11.sh); Phase 12 not started.
- 2026-09-14 22:24Z WSL: LAUNCHED (nothing resident verified before; pgrep 60 s after: runner, controller, battery_xdeck, server 7947, driver JVM). Controller rl/phase12.py via rl/run_phase12.sh --hours 10.5 (no new block after hour 10.5, then the end phase); LOG rl/artifacts/v7/12/phase12.log; state/results/levels/census_lines/battery_lines in rl/artifacts/v7/12/; lanes /tmp/rl_12_<main>/ (seeds 21/22/23), snapshots rl/artifacts/v7/12/pool/<main>_<trained>.pt (opt stripped, gitignored). Start snapshots M_D_06400 (drill pool), M_L_06144 (drill pool), M_W_s1end (1,792 ep). Implementation choices stated before any data: (1) the 75/25 mix is realised EXACTLY by the rotation cp7,heuristic,cp7,cp7 per main (every 1,024-episode window is 3 CP7 blocks + 1 heuristic block; Phase 10 Amendment 3 showed random draws under-delivering); (2) the starting point per main = CP7 100 + heuristic 50 (same G as the guard) + unseen 150 + the 25-game CP7 census; M_W's unseen rows are Phase 10's own rows of the same checkpoint and suite (rl/artifacts/v7/10/eval/M_W_s1end_unseen, 116/150), copied in, not re-run; (3) battery row seeds and the census seed (12500) are fixed, so every level and every check sees the same deals (paired across points); (4) the white check (no census tool for W0Base) = win rate, blocks matching the combat search ([audit] MATCH share), attacks declared / attack windows and [atkaudit] MATCH share, creatures per game from rl/dimir_census.py's board line; (5) snapshots carry no optimiser state, so the first block of each main starts AdamW fresh. Lines: L12|start|<main>|..., L12|block|n=..|main=..|opp=..|wr=..|wall=.., L12|tput|<main>|opp=..|eps_per_h=.., L12|check|<main>|n=..|trained=..|opp=cp7|wr=..|<fields>, L12|level|<main>|point=start/train/end|trained=..|cp7=k/100 = p [lo,hi]|heur=k/50 = ..|graduated=0/1, L12|grad|<main>|..., L12|end|<main>|..., L12|done|reason=... Graceful stop: bash rl/stop_p12.sh; hard: bash rl/kill_p12.sh. Second 18 h keepalive started 22:18Z (to ~16:20Z).
- 2026-09-14 22:51Z WSL: START POINT M_D (M_D_06400, 0.45 h for 300 games): CP7 19/100 = 0.190 [0.125,0.278] (0 stalls), heuristic 35/50 = 0.700 [0.562,0.809], unseen 98/150 = 0.653 [0.574,0.725] (BenchBurn 29/50, HoldoutControl 39/50, HoldoutMidrange 30/50). Graduation needs >= 70/100 vs CP7 from 19/100.
- 2026-09-14 23:36Z WSL: START POINTS COMPLETE (h=0.85). M_L (M_L_06144): CP7 35/100 = 0.350 [0.264,0.447], heuristic 23/50 = 0.460 [0.330,0.596], unseen 93/150 = 0.620 [0.540,0.694]. M_W (M_W_s1end): CP7 58/100 = 0.580 [0.482,0.672], heuristic 33/50 = 0.660 [0.522,0.776], unseen 116/150 = 0.773 (Phase 10 rows). Start checks (25 CP7 games, seed 12500): M_D 4/25, selfrem 7/7, counter 31/38, flash_opp 5/74, ninja 2/3, biggest 18/24, cpg 3.84; M_L 11/25, smallbig 27/32 (solver_no_block 15/24), landsearch 42/738, cpg 4.76; M_W 16/25, blocks_match 92/119, attacks declared 225/245, attack_match 104/245, cpg 10.88 (dimir_census board line on W0Base, unvalidated for this deck: a caveat on the white cpg field). THROUGHPUT M_D vs CP7: block n=0 6400->6656 43/256 = 0.168, 1,249 s = 738 episodes/h (1.39 h of lane time per 1,024); a rotation round of three blocks + checks is ~75-80 min, so each main's first 1,024-episode level lands ~5 h of wall time after training starts (~04:30-05:30Z) - PAST the runbook's 4-hour line, said here as the runbook asks; continuing. Expected: no new block after hour 10.5 (~08:54Z), end phase (last level + unseen per non-graduated main) to ~10:15Z.
- 2026-09-14 23:43Z WSL: AMENDMENT 2 APPLIED (user: tonight Dimir only). Controller stopped gracefully (STOP 23:39:44Z; L12|done|reason=stopfile|blocks=1|h=1.30 after M_D's block n=0 check: opp=cp7|wr=7/25 = 0.28 [0.143,0.476]|selfrem=8/9|counter=32/44|flash_opp=3/83|ninja=3/3|biggest=23/24|cpg=4.32); nothing resident verified; rl/phase12.py --mains (default all three); RESUMED 23:42:35Z with --hours 10.5 --mains M_D (clock from the original 22:24Z start: no new block after ~08:54Z), verified by pgrep 60 s later (runner, controller, lane to 6,912, server 7950, driver JVM; L12|resume|n=1|h=1.31). M_L and M_W: 0 training blocks, start points only, state untouched. PROJECTED M_D level points (~26.5 min per block + check, ~0.25 h per level; ~2.0 h per 1,024 episodes): +1,024 (7,424) ~01:15Z, +2,048 ~03:15Z, +3,072 ~05:15Z, +4,096 ~07:15Z; blocks to ~08:54Z (~+4,864), then the end-phase level + unseen suite to ~09:40Z.
- 2026-09-14 23:51Z WSL: first post-resume block verified: L12|block|n=1|main=M_D|6656->6912|opp=heuristic|123/132/1/1 = 0.480|wall=503s (1,831 ep/h; a CP7 block is 1,249 s). CORRECTED PROJECTION (3 CP7 blocks + 1 heuristic block + 4 checks + level ~1.8 h per 1,024): +1,024 (7,424) ~01:05Z, +2,048 ~02:55Z, +3,072 ~04:45Z, +4,096 ~06:35Z, +5,120 ~08:25Z; no new block after ~08:54Z; end phase (level + unseen) to ~09:30Z.
