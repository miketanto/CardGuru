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

## Amendment 3 (2026-09-15 ~02:20Z, user decision) — stop extended to controller hour 12

The user extended tonight's Dimir run: training stops at controller hour 12 from the
original 22:24Z start (no new block after ~10:24Z) instead of hour 10.5 (~08:54Z); the
end phase (final 100-game CP7 level + 50-game heuristic guard + unseen suite) follows as
before. Applied at a block boundary without losing training (graceful stop after M_D's
CP7 block n=6 and its check; relaunch `--mains M_D --hours 12`). **No other change**: the
rotation, the per-block checks, the 1,024-episode level cadence, the seeds and the
graduation rule are unchanged; M_L / M_W stay paused (Amendment 2).

## Amendment 4 (2026-09-15 ~03:40Z, coordinator; before any of its results) — sampled-play diagnostic

Observation at +2,048: the sampled training win rate vs CP7 stayed flat (~0.16) and vs the
heuristic rose (0.48 → 0.605) while the argmax levels fell (CP7 0.19 → 0.18 → 0.09, heuristic
0.70 → 0.64 → 0.50). Hypothesis (main session): the policy's acting mass is spread over several
distinct candidates, so the argmax-over-classes readout picks PASS / hold even when P(act) > 0.5 —
which would produce the census's "hold" shape and a falling argmax level while the sampled policy
holds or improves. **This adds a measurement only; the pre-registered argmax levels and the
graduation rule are unchanged.**

1. **Sampled levels** of the three level snapshots (M_D 6,400 start, 7,424, 8,448 in
   `rl/artifacts/v7/12/pool/`, the start = the drill's M_D_06400): frozen server (`--frozen`, no
   updates), sampled as in training (`-Drl.mode=train`, as `rl/run_7b0.sh`), otherwise the level
   battery's flags and seeds exactly — 100 games vs CP7 and 50 vs the heuristic on the Dimir
   mirror — `rl/battery_p12s.sh` (a copy of `battery_xdeck.sh` with the mode switched; the
   original is in use by the running controller and is not edited). Side job beside training:
   server 7949 / driver 7914 (7948 is the census proxy's port), one evaluation at a time; the
   controller always frees the lane before its own census / level, so the total stays ≤ 2 servers
   + 2 JVMs.
2. **Rescoring the census consults** already recorded at those three points (25 CP7 games each:
   `rec_p12_M_D_start`, `rec_p12_M_D_n003_t07424`, `rec_p12_M_D_n007_t08448`) with the snapshot
   that played them, on CPU, raw logits with the bound applied as the server does: per consult
   offering PASS, count "the argmax-over-classes choice is PASS while the summed probability of
   the non-PASS candidates > 0.5"; and "the choice is not a creature spell while the summed
   probability of the creature-spell candidates > the chosen class's probability".

**Reading, pre-stated:** "**argmax artifact**" if the sampled levels stay flat or rise across the
three points while the argmax levels fall, AND the PASS-despite-majority rate rises across the
points; "**real regression**" if the sampled levels fall with the argmax ones. Anything else
(e.g. sampled flat but the PASS-despite-majority rate flat) is reported as neither, with what it
does show. Cannots: 100/50 games per point — a sampled level is a level of the stochastic policy,
not of a deployable argmax player; the census consults are argmax-play states (the rescoring
measures the readout on the states argmax play reaches, not on the sampled policy's own states);
one seed, one deck.

## Amendment 5 (2026-09-15 ~03:35Z, coordinator; before any result) — a two-stage argmax readout

After the Amendment 4 readout (PASS-despite-majority 0.153 → 0.167 → 0.428), one more
EVALUATION-side readout is pre-registered for the post-training reruns: a **two-stage argmax** —
first act vs pass by summed probability (act iff Σ P(non-PASS) > P(PASS)), then, if acting, the
argmax over the acting candidates by class (the existing `--argmax-classes` grouping; PASS
excluded); at a consult without a PASS candidate it equals `--argmax-classes`. A server flag
`--argmax-two-stage` (default OFF = today's behaviour bit for bit), eval path only; training
(sampling) untouched. **Implemented and tested only after training ends** (the lane restarts its
server from disk every block; no server-side edit while it runs). Then, one at a time after the
controller's final `L12|done` (box rule: lane + at most one other model-holding process — with the
lane gone, one evaluation at a time): the sampled battery (Amendment 4, `rl/after_p12.sh` launches
it) and the two-stage battery, both on the same three snapshots (6,400 / 7,424 / 8,448) with the
level seeds, 100 vs CP7 + 50 vs the heuristic on the Dimir mirror. The argmax-classes readout is the
recorded levels themselves (same seeds), not re-run.

**Reading, pre-stated:** if the two-stage levels track the sampled levels and both stay flat or rise
across the three points while the argmax-classes levels fall, the Phase 12 decline is a **readout
artifact** and the argmax-classes protocol is retired for this policy family; if all three fall
together, it is a **real regression**. Anything else is reported as neither, with what it shows.
Cannots: 100/50 games per point; one seed, one deck; two-stage is a readout choice made after
seeing Amendment 4's readout — the pre-registration is of its levels, not of the rule's merit in
general.

## STATE (append dated lines; newest last)
- 2026-09-14 ~22:15Z WSL: Phase 11 drill-down being stopped by the user (rl/stop_drill11.sh); Phase 12 not started.
- 2026-09-14 22:24Z WSL: LAUNCHED (nothing resident verified before; pgrep 60 s after: runner, controller, battery_xdeck, server 7947, driver JVM). Controller rl/phase12.py via rl/run_phase12.sh --hours 10.5 (no new block after hour 10.5, then the end phase); LOG rl/artifacts/v7/12/phase12.log; state/results/levels/census_lines/battery_lines in rl/artifacts/v7/12/; lanes /tmp/rl_12_<main>/ (seeds 21/22/23), snapshots rl/artifacts/v7/12/pool/<main>_<trained>.pt (opt stripped, gitignored). Start snapshots M_D_06400 (drill pool), M_L_06144 (drill pool), M_W_s1end (1,792 ep). Implementation choices stated before any data: (1) the 75/25 mix is realised EXACTLY by the rotation cp7,heuristic,cp7,cp7 per main (every 1,024-episode window is 3 CP7 blocks + 1 heuristic block; Phase 10 Amendment 3 showed random draws under-delivering); (2) the starting point per main = CP7 100 + heuristic 50 (same G as the guard) + unseen 150 + the 25-game CP7 census; M_W's unseen rows are Phase 10's own rows of the same checkpoint and suite (rl/artifacts/v7/10/eval/M_W_s1end_unseen, 116/150), copied in, not re-run; (3) battery row seeds and the census seed (12500) are fixed, so every level and every check sees the same deals (paired across points); (4) the white check (no census tool for W0Base) = win rate, blocks matching the combat search ([audit] MATCH share), attacks declared / attack windows and [atkaudit] MATCH share, creatures per game from rl/dimir_census.py's board line; (5) snapshots carry no optimiser state, so the first block of each main starts AdamW fresh. Lines: L12|start|<main>|..., L12|block|n=..|main=..|opp=..|wr=..|wall=.., L12|tput|<main>|opp=..|eps_per_h=.., L12|check|<main>|n=..|trained=..|opp=cp7|wr=..|<fields>, L12|level|<main>|point=start/train/end|trained=..|cp7=k/100 = p [lo,hi]|heur=k/50 = ..|graduated=0/1, L12|grad|<main>|..., L12|end|<main>|..., L12|done|reason=... Graceful stop: bash rl/stop_p12.sh; hard: bash rl/kill_p12.sh. Second 18 h keepalive started 22:18Z (to ~16:20Z).
- 2026-09-14 22:51Z WSL: START POINT M_D (M_D_06400, 0.45 h for 300 games): CP7 19/100 = 0.190 [0.125,0.278] (0 stalls), heuristic 35/50 = 0.700 [0.562,0.809], unseen 98/150 = 0.653 [0.574,0.725] (BenchBurn 29/50, HoldoutControl 39/50, HoldoutMidrange 30/50). Graduation needs >= 70/100 vs CP7 from 19/100.
- 2026-09-14 23:36Z WSL: START POINTS COMPLETE (h=0.85). M_L (M_L_06144): CP7 35/100 = 0.350 [0.264,0.447], heuristic 23/50 = 0.460 [0.330,0.596], unseen 93/150 = 0.620 [0.540,0.694]. M_W (M_W_s1end): CP7 58/100 = 0.580 [0.482,0.672], heuristic 33/50 = 0.660 [0.522,0.776], unseen 116/150 = 0.773 (Phase 10 rows). Start checks (25 CP7 games, seed 12500): M_D 4/25, selfrem 7/7, counter 31/38, flash_opp 5/74, ninja 2/3, biggest 18/24, cpg 3.84; M_L 11/25, smallbig 27/32 (solver_no_block 15/24), landsearch 42/738, cpg 4.76; M_W 16/25, blocks_match 92/119, attacks declared 225/245, attack_match 104/245, cpg 10.88 (dimir_census board line on W0Base, unvalidated for this deck: a caveat on the white cpg field). THROUGHPUT M_D vs CP7: block n=0 6400->6656 43/256 = 0.168, 1,249 s = 738 episodes/h (1.39 h of lane time per 1,024); a rotation round of three blocks + checks is ~75-80 min, so each main's first 1,024-episode level lands ~5 h of wall time after training starts (~04:30-05:30Z) - PAST the runbook's 4-hour line, said here as the runbook asks; continuing. Expected: no new block after hour 10.5 (~08:54Z), end phase (last level + unseen per non-graduated main) to ~10:15Z.
- 2026-09-14 23:43Z WSL: AMENDMENT 2 APPLIED (user: tonight Dimir only). Controller stopped gracefully (STOP 23:39:44Z; L12|done|reason=stopfile|blocks=1|h=1.30 after M_D's block n=0 check: opp=cp7|wr=7/25 = 0.28 [0.143,0.476]|selfrem=8/9|counter=32/44|flash_opp=3/83|ninja=3/3|biggest=23/24|cpg=4.32); nothing resident verified; rl/phase12.py --mains (default all three); RESUMED 23:42:35Z with --hours 10.5 --mains M_D (clock from the original 22:24Z start: no new block after ~08:54Z), verified by pgrep 60 s later (runner, controller, lane to 6,912, server 7950, driver JVM; L12|resume|n=1|h=1.31). M_L and M_W: 0 training blocks, start points only, state untouched. PROJECTED M_D level points (~26.5 min per block + check, ~0.25 h per level; ~2.0 h per 1,024 episodes): +1,024 (7,424) ~01:15Z, +2,048 ~03:15Z, +3,072 ~05:15Z, +4,096 ~07:15Z; blocks to ~08:54Z (~+4,864), then the end-phase level + unseen suite to ~09:40Z.
- 2026-09-14 23:51Z WSL: first post-resume block verified: L12|block|n=1|main=M_D|6656->6912|opp=heuristic|123/132/1/1 = 0.480|wall=503s (1,831 ep/h; a CP7 block is 1,249 s). CORRECTED PROJECTION (3 CP7 blocks + 1 heuristic block + 4 checks + level ~1.8 h per 1,024): +1,024 (7,424) ~01:05Z, +2,048 ~02:55Z, +3,072 ~04:45Z, +4,096 ~06:35Z, +5,120 ~08:25Z; no new block after ~08:54Z; end phase (level + unseen) to ~09:30Z.
- 2026-09-15 ~01:15Z WSL: FIRST M_D LEVEL (+1,024, 7,424 ep, h=2.83): CP7 18/100 = 0.180 [0.117,0.267] (start 0.190), heuristic 32/50 = 0.640 [0.501,0.759] (start 0.700); not graduated. Checks n=0..3: CP7 7,6,5,4 /25; selfrem 8/9 -> 6/115 -> 2/255 -> 5/258; counter 32/44 -> 6/88 -> 7/105 -> 3/103; flash_opp 3/83 -> 0/73 -> 23/62 -> 8/66; consults/game 69 -> 71 -> 106 -> 85; training blocks vs CP7 0.168, 0.156, 0.137 (heuristic block 0.480). Reading: CP7 level flat; card counters stepped to 'hold' after the heuristic block and stayed three checks (self-destroy near CP7's 0, counterspells almost never cast vs CP7 ~1/3, longer games); no pre-registered reading fires yet (one of up to five points; convergence clauses need four checks). Row: V7-VALIDATION '12 / M_D - first level point'. Next level ~02:55Z.
- 2026-09-15 02:27Z WSL: AMENDMENT 3 APPLIED (user: stop extended to controller hour 12). STOP touched 02:20:45Z; block n=6 (cp7, 7936->8192, 41/215 = 0.160, 1,365 s) and its check (CP7 4/25; selfrem 7/154, counter 2/80, flash_opp 10/66, cpg 3.72, consults/game 80.6) completed; clean L12|done|reason=stopfile|blocks=7|h=4.04; nothing resident; RESUMED 02:26:43Z with --hours 12 --mains M_D, verified by pgrep 60 s later (runner, controller, lane to 8,448, server 7950, driver JVM; L12|resume|n=7|h=4.05|todo=0). No new block after ~10:24Z. Keepalive sleep 64800 pid 92509 (started 22:18Z) runs to ~16:18Z: covers the end. Also at n=4/n=5 (not in a STATE line before): n=4 cp7 check and n=5 heuristic block 155/101 = 0.605, check 3/25, selfrem 4/57, counter 6/95. PROJECTED M_D levels: +2,048 (8,448) ~03:12Z, +3,072 ~05:00Z, +4,096 ~06:50Z, +5,120 ~08:40Z, +6,144 ~10:30Z if its fourth block starts before 10:24Z (else the end-phase level at ~+5,888); end phase done ~10:45-11:00Z.
- 2026-09-15 ~03:20Z WSL: SECOND M_D LEVEL (+2,048, 8,448 ep, h=4.88): CP7 9/100 = 0.090 [0.048,0.162] (0.190 -> 0.180 -> 0.090), heuristic 25/50 = 0.500 [0.366,0.634] (0.700 -> 0.640 -> 0.500); not graduated. Checks n=4..7: CP7 6,3,4,2 /25; selfrem 4/294, 4/57, 7/154, 1/148; counter 3/92, 6/95, 2/80, 6/81; flash_opp 9/49, 6/47, 10/66, 8/38; cpg 3.00, 2.88, 3.72, 2.36; consults/game 98, 90, 81, 100. Training blocks vs CP7 flat ~0.16 (n=4 0.164, n=6 0.160, n=7 0.176); heuristic block n=5 0.605. Reading: both yardsticks falling, neither yet clear below start (intervals overlap narrowly) - a regression in the point estimates, not flat; 'improving vs CP7' not met; 'over-fit to CP7' does not apply (CP7 level itself falling); selfrem clause met, counter clause fails every check since n=1, cpg < 3 at two of the last four -> 'card habits converge' not met, habits settled on 'hold' (no oscillation yet); sampled training rates flat/rising while argmax levels fall. Row: V7-VALIDATION '12 / M_D - second level point'. Next level (+3,072) ~05:00Z.
- 2026-09-15 03:22Z WSL: AMENDMENT 4 recorded (sampled-play diagnostic, before any of its results). Side job rl/run_p12s.sh launched 03:21Z (rl/battery_p12s.sh: frozen server 7949, driver 7914, -Drl.mode=train, the level battery's seeds; start/p1024/p2048 x CP7 100 + heuristic 50; log rl/artifacts/v7/12/sampled/p12s.log, lines P12S|<point>|XDECKS|...), verified by pgrep (server 7949 + driver JVM beside the lane's 7950 + JVM = 2 + 2); memory 1.26 GB available + 8 GB swap. Readout rl/p12_readout.py (CPU, 2 threads) on the three census recordings -> rl/artifacts/v7/12/sampled/readout.txt.
- 2026-09-15 03:27Z WSL: AMENDMENT 4 SAMPLED BATTERY PAUSED FOR MEMORY AND RESCHEDULED. Right after its launch the box swapped (03:23Z: 336 MB available, 2.5 GB swap, heavy swap-out; the lane's update_s rose from ~20 s to 35-37 s); the main session stopped ONLY the side job (rl/pause_p12s.sh: server 7949, driver 7914, run_p12s/battery_p12s; no probe file had been finished). The lane and the CPU readout were not touched; memory back to ~4.8 GB available at 03:25Z. BOX RULE from now on: the lane + at most ONE other model-holding process (the old '2 servers + 2 JVMs' is too much with a CP7 JVM at 4.7 GB RSS). The battery reruns unattended via rl/after_p12.sh (detached, pgrep-verified): it waits for the controller's FINAL L12|done (reason hours/all_graduated/errors - after the end phase), then for no policy server resident, deletes any partial probe file, and runs the resumable rl/run_p12s.sh (log rl/artifacts/v7/12/sampled/p12s.log). Readout (rl/p12_readout.py) still running.
- 2026-09-15 ~03:35Z WSL: AMENDMENT 4 READOUT DONE (rl/p12_readout.py -> rl/artifacts/v7/12/sampled/readout.txt; recomputed argmax-classes choice = recorded at 6,160/6,160 consults). start / +1,024 / +2,048: argmax PASS when offered 0.649 / 0.748 / 0.870; PASS while P(act) > 0.5 0.153 / 0.167 / 0.428 (of all argmax passes 0.235 / 0.223 / 0.492); act rate sampled 0.594 / 0.511 / 0.553 vs argmax 0.351 / 0.252 / 0.130; creature spell cast when offered argmax 0.807 / 0.150 / 0.041 vs sampled mass 0.530 / 0.362 / 0.282. Reading: the READOUT half of 'argmax artifact' is MET (PASS-despite-majority rises, sharply at +2,048; sampled act rate stable while argmax act rate falls); but the sampled creature rate also falls (0.53 -> 0.28), so part of the shift is real, amplified by the readout. The win-rate half waits for the sampled battery after training. AMENDMENT 5 pre-registered (two-stage argmax, --argmax-two-stage default off, implemented only after training; run after L12|done one evaluation at a time). Row: V7-VALIDATION '12 / M_D - Amendment 4 diagnostic'. Memory/lane: 23.67 21.07 35.68 avail=4779MB (update_s values listed newest last).
- 2026-09-15 ~05:25Z WSL: THIRD M_D LEVEL (+3,072, 9,472 ep, h=7.02): CP7 8/100 = 0.080 [0.041,0.150] (0.19 -> 0.18 -> 0.09 -> 0.08; overlaps the start interval [0.125,0.278] only at its edge), heuristic 26/50 = 0.520 [0.385,0.652] (0.70 -> 0.64 -> 0.50 -> 0.52); not graduated. Blocks n=8..11: cp7 0.191, heuristic 0.574, cp7 0.168, cp7 0.102 (lowest CP7 block). Checks n=8..11: CP7 7,5,5,3 /25; selfrem 11/18, 9/89, 3/154, 1/114; counter 20/37, 14/41, 7/88, 3/108; flash_opp 17/76, 3/73, 13/62, 3/35; cpg 4.04, 4.00, 3.24, 2.36; consults/game 76, 73, 96, 109. Reading: 'improving vs CP7' not met; card counters OSCILLATED again under the fixed opponent (swing to act at n=8: selfrem 0.61, counter 0.54, cpg 4.0; back to hold by n=10-11) -> 'oscillates' per the runbook; the Phase 11 oscillation is not specific to the league mix, which weakens self-play drift as the main explanation (coarse terminal reward = the pre-registered next candidate, not established). Amendment 4's readout artifact applies; the sampled/two-stage reruns after training decide how much of the level decline is real. Owed: a readout at the n=8 snapshot (act-swing state). Row: V7-VALIDATION '12 / M_D - third level point'. Next level (+4,096) ~06:50Z.
- 2026-09-15 ~07:30Z WSL: FOURTH M_D LEVEL (+4,096, 10,496 ep, h=9.21): CP7 31/100 = 0.310 [0.228,0.406] (0.19 -> 0.18 -> 0.09 -> 0.08 -> 0.31: best of the phase, first above the start, interval still overlaps the start's [0.125,0.278] -> 'improving vs CP7' NOT met by the overlap test), heuristic 38/50 = 0.760 [0.626,0.857] (best; start 0.70); not graduated. Blocks n=12..15: cp7 0.188, heuristic 0.637, cp7 0.191, cp7 0.246 (best sampled CP7 block). Checks n=12..15: CP7 7,10,2,6 /25; selfrem 3/256, 15/132, 4/127, 7/122; counter 4/107, 16/114, 5/110, 14/79; flash_opp 20/47, 31/86, 21/52, 34/68; ninja 3/3, 8/8, 2/8, 1/6; cpg 2.88, 4.84, 3.00, 3.80; consults/game 119, 108, 108, 97. Carried plainly: the 0.08 -> 0.31 swing in 1,024 episodes is as large as the night's range, consistent with the Amendment 4 readout artifact on an oscillating policy; no single point is a trend; the sampled / two-stage reruns decide. RERUN SET EXTENDED: rl/run_p12s.sh now start, 7,424, 8,448, 9,472, 10,496 (edited while idle - after_p12.sh invokes it only after the final L12|done); the two-stage (Amendment 5) uses the same set; the n=8 (8,704) census readout is owed. Row: V7-VALIDATION '12 / M_D - fourth level point'.
- 2026-09-15 ~09:55Z WSL: FIFTH M_D LEVEL (+5,120, 11,520 ep, h=11.49): CP7 33/100 = 0.330 [0.246,0.427] (0.19 -> 0.18 -> 0.09 -> 0.08 -> 0.31 -> 0.33; still overlaps the start interval at its edge -> 'improving vs CP7' NOT met by the overlap test; observation: two consecutive points at 0.31-0.33 after two at 0.08-0.09 make a single-checkpoint fluke less likely), heuristic 39/50 = 0.780 [0.648,0.872] (best); over-fit to CP7 does not apply; not graduated. Blocks n=16..19: cp7 0.238, heuristic 0.672, cp7 0.234, cp7 0.199. Checks n=16..19: CP7 6,10,5,9 /25; selfrem 16/144, 17/148, 2/133, 11/144 (all < 0.3: met); counter 47/76 = 0.62, 25/72 = 0.35, 8/107 = 0.07, 23/85 = 0.27 -> in [0.2,0.5] at TWO of four (correction in the open: the coordinator's summary said three) -> not met; cpg 4.36, 4.24, 3.80, 4.40 (>= 3: met); consults/game 89, 77, 91, 89 -> 'card habits converge' not met (counter clause). 11,520 added to the rerun set (rl/run_p12s.sh, idle). Row: V7-VALIDATION '12 / M_D - fifth level point'.
- 2026-09-15 ~10:55Z WSL: TRAINING OVER - L12|done|reason=hours|blocks=21|h=12.50|graduated=none (M_D +5,376; M_L/M_W 0). Block n=20 cp7 0.207; check n=20 CP7 2/25, selfrem 5/111, counter 9/101, ninja 0/15, cpg 3.32. END POINT (11,776): CP7 21/100 = 0.210 [0.142,0.300], heuristic 32/50 = 0.640 [0.501,0.759], unseen 95/150 = 0.633 [0.554,0.706] (start 0.190 / 0.700 / 0.653). Argmax CP7 series 0.19, 0.18, 0.09, 0.08, 0.31, 0.33, 0.21 (0.33 -> 0.21 in ONE 256-episode block). Argmax-yardstick readings: not competent; improving vs CP7 not met; over-fit n/a; card habits oscillate; drift test -> per the runbook's sentence the drift hypothesis is not supported and the coarse terminal reward is the leading explanation, qualified by Amendment 4 (the argmax yardstick flips with the act/pass balance) pending the sampled / two-stage levels. after_p12.sh launched the sampled battery 10:53:48Z on the six snapshots. Row: V7-VALIDATION '12 / M_D - end point'.
