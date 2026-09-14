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

## STATE (append dated lines; newest last)
- 2026-09-14 ~22:15Z WSL: Phase 11 drill-down being stopped by the user (rl/stop_drill11.sh); Phase 12 not started.
- 2026-09-14 22:24Z WSL: LAUNCHED (nothing resident verified before; pgrep 60 s after: runner, controller, battery_xdeck, server 7947, driver JVM). Controller rl/phase12.py via rl/run_phase12.sh --hours 10.5 (no new block after hour 10.5, then the end phase); LOG rl/artifacts/v7/12/phase12.log; state/results/levels/census_lines/battery_lines in rl/artifacts/v7/12/; lanes /tmp/rl_12_<main>/ (seeds 21/22/23), snapshots rl/artifacts/v7/12/pool/<main>_<trained>.pt (opt stripped, gitignored). Start snapshots M_D_06400 (drill pool), M_L_06144 (drill pool), M_W_s1end (1,792 ep). Implementation choices stated before any data: (1) the 75/25 mix is realised EXACTLY by the rotation cp7,heuristic,cp7,cp7 per main (every 1,024-episode window is 3 CP7 blocks + 1 heuristic block; Phase 10 Amendment 3 showed random draws under-delivering); (2) the starting point per main = CP7 100 + heuristic 50 (same G as the guard) + unseen 150 + the 25-game CP7 census; M_W's unseen rows are Phase 10's own rows of the same checkpoint and suite (rl/artifacts/v7/10/eval/M_W_s1end_unseen, 116/150), copied in, not re-run; (3) battery row seeds and the census seed (12500) are fixed, so every level and every check sees the same deals (paired across points); (4) the white check (no census tool for W0Base) = win rate, blocks matching the combat search ([audit] MATCH share), attacks declared / attack windows and [atkaudit] MATCH share, creatures per game from rl/dimir_census.py's board line; (5) snapshots carry no optimiser state, so the first block of each main starts AdamW fresh. Lines: L12|start|<main>|..., L12|block|n=..|main=..|opp=..|wr=..|wall=.., L12|tput|<main>|opp=..|eps_per_h=.., L12|check|<main>|n=..|trained=..|opp=cp7|wr=..|<fields>, L12|level|<main>|point=start/train/end|trained=..|cp7=k/100 = p [lo,hi]|heur=k/50 = ..|graduated=0/1, L12|grad|<main>|..., L12|end|<main>|..., L12|done|reason=... Graceful stop: bash rl/stop_p12.sh; hard: bash rl/kill_p12.sh. Second 18 h keepalive started 22:18Z (to ~16:20Z).
- 2026-09-14 22:51Z WSL: START POINT M_D (M_D_06400, 0.45 h for 300 games): CP7 19/100 = 0.190 [0.125,0.278] (0 stalls), heuristic 35/50 = 0.700 [0.562,0.809], unseen 98/150 = 0.653 [0.574,0.725] (BenchBurn 29/50, HoldoutControl 39/50, HoldoutMidrange 30/50). Graduation needs >= 70/100 vs CP7 from 19/100.
