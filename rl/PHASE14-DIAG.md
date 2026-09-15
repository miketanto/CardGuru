# PHASE14-DIAG — why RL does not climb against CP7: two diagnostics (runbook + pre-registration, 2026-09-15 ~23:10Z)

Context: Phase 13c (RL vs CP7 skill 6 from the CP7 clone `bc.pt`) failed its make-or-break at 2,048 episodes
(row '13c' in rl/V7-VALIDATION.md): levels drifted below the clone, the CP7 training win rate fell 0.279 → 0.219,
the online value function explained only 0.05–0.22 of outcome variance, and updates moved the policy ~0.0012 KL
each. User (2026-09-15): a league would only drift when RL cannot climb against one fixed opponent; "go and test
those if it doesn't take long". Two diagnostics, each answering one question. Budget: ~3 h wall; D1 and D2 run
side by side (D1 = one GPU python process; D2 = one policy server + one driver JVM; box rule respected).

## D1 — can the network predict game outcomes from what it sees? (offline, GPU, ~30–60 min)

* Data: the 13a recordings `rl/artifacts/v7/13/rec/rec13_*.jsonl` (25 files, 1,250 BenchDimir games, CP7 deciding
  the recorded seat vs CP7; each game ends with `{"t":"end","r":±1}`). Every consult with a v7 state gets the
  recorded seat's final outcome as its target. Game-grouped hold-out: the same 10 % of games as 13b (`v7_bc.py`
  split, seed 0).
* Models (same parsed v7 observations as `rl/v7_bc.py`):
  - **N1** the v7 network initialised from `bc.pt`, value head (and encoder) trained on the outcome;
  - **N2** the same with the encoder frozen (what the clone's representation already holds);
  - **B0** a scalar baseline: logistic regression on simple features taken from the same consults (life me / opp,
    cards in hand me / opp, lands and creatures in play me / opp, turn) — whatever of these the observation exposes;
    list what was used.
* Readings on held-out games: explained variance of the ±1 target (1 − MSE / Var) and AUC of the sign, overall and
  by stage (own-turn buckets early ≤ 6, mid 7–12, late ≥ 13).
* Pre-registered:
  - **"The encoding can predict outcomes"** if N1's held-out EV ≥ 0.35 AND N1 beats B0 by ≥ 0.05 EV → the online
    critic is the weak link (candidates: value pre-training from recordings, a privileged-information critic).
  - **"Outcomes are barely predictable from observations"** if N1's EV ≤ 0.25 → noise from hidden information and
    shuffles (or the encoding) caps the signal; RL tuning alone cannot fix it; a privileged critic is the candidate.
  - Between: "partial", reported with the stage breakdown.
  - If B0 ≥ N1, say so: the network is not using the state better than a handful of counters.
* Cannots: states are CP7-vs-CP7 positions, not the learner's; EV depends on the stage mix; one seed.

## D2 — is CP7 skill 6 the ceiling, or is the recipe itself stuck? (GPU server + JVM, ~2–2.5 h)

* D2a (ladder, no training): `bc.pt` sampled levels, 100 games each, vs CP7 at `rl.aiSkill` 1 and 3 on BenchDimir
  (skill 6 is known: 33/100). Needs a copy of `rl/battery_p12s.sh` with the skill as a parameter (default 6; the
  original is not edited).
* Training rung: the lowest of {1, 3} where `bc.pt`'s sampled level is ≤ 0.70 (headroom); if both are > 0.70, use 3
  and say the ladder is too shallow; if skill 1 is already ≤ 0.35, use 1.
* D2b (training): from `bc.pt`, the Phase 13 recipe unchanged (lr 3e-5, 1 epoch, logit bound 5, AdamW wd 0.01 on
  heads, `--adv-norm batch`, `--target-kl 0.02`), opponent = CP7 at the rung skill only (no heuristic blocks),
  **1,024 episodes** in 256-episode blocks, then 100-game sampled and two-stage levels vs the rung skill.
* Pre-registered:
  - **"Climbs against a weaker CP7"** if the sampled or two-stage level at 1,024 is clearly above `bc.pt`'s level
    at that skill (Wilson intervals do not overlap), OR the pooled training win rate of blocks 512→1,024 is clearly
    above blocks 0→512 → skill 6's search is (part of) the ceiling; lookahead or a curriculum are the candidates.
  - **"Does not climb even against a weaker CP7"** otherwise → the learning signal / recipe is the block regardless
    of opponent strength; D1 says which part.
* Cannots: one seed; 1,024 episodes is short (a "does not climb" here is about this recipe at this scale); CP7's
  skill scale is not linear.

## Combined reading (stated before either runs)

| D1 | D2 | reading |
|---|---|---|
| predicts | climbs vs weaker | the critic and opponent strength both matter: pre-train the critic, then a CP7 curriculum |
| predicts | does not climb | the online critic / update is the block: value pre-training, larger steps with a KL-to-bc.pt anchor |
| barely predicts | climbs vs weaker | the signal is noisy but usable against weaker play: curriculum + privileged critic |
| barely predicts | does not climb | the win/loss signal from this encoding is too weak for this RL at this scale: privileged critic, denser rewards, or search |

## STATE (append-only)
- 2026-09-15 23:16Z WSL: 13c has exited (L13|done|reason=stopfile, recorded in rl/PHASE13-BC.md STATE); box free (no server, no driver JVM; three old `sleep 64800` keepalives left alone). D1 and D2 both start now.
- 2026-09-15 23:18Z WSL (D2a LAUNCHED): rl/battery_p14s.sh = copy of rl/battery_p12s.sh with `SKILL` (default 6) in `-Drl.aiSkill` and `skill=` in the XDECKS line (diff: 3 lines + header; the original is untouched); rl/battery_x14.sh = the same change on rl/battery_xdeck.sh (for the two-stage levels). Runner rl/run_14d2a.sh (cmd start /min wsl): bc.pt sampled, 100 games vs CP7 on BenchDimir, row seed 930000 (= 13b's skill-6 level), skill 1 on 7949/7914 and skill 3 on 7947/7913 in parallel. Output rl/artifacts/v7/14/d2a/run.log (XDECKS|...|skill=N| lines), probes in d2a/s1, d2a/s3. pgrep-verified 23:18:50Z (runner, server 7949, JVM).
- 2026-09-15 23:24Z WSL (D1 written, HELD until D2a finishes - memory, not a change of plan): rl/p14_d1.py (N1 = bc.pt's critic trained on the outcome; N2 = a value MLP on the FROZEN clone game vector, computed from an untouched load of bc.pt BEFORE N1 trains, because the critic shares the card-table adapter with the policy path; B0 = logistic regression on life/hand/lands/non-land-permanents me+opp, turn, my-turn flag read from v7_game / v7_players). Hold-out = the 13b split reproduced exactly (labelled games, sorted, Random(0).shuffle, first 10 %); early stopping uses a validation split of 10 % of the TRAINING games (Random(1)), so the hold-out is never used for model selection - a deviation from v7_bc.py, which early-stops on its hold-out. 95 % intervals = 1,000 bootstrap resamples of held-out GAMES. Smoke (1 file, 50 games) OK end to end; 3-file probe gives RSS ~420 MB + ~62 MB/file, so 25 files is ~2.0 GB. With D2a resident (2 servers + 2 JVMs) MemAvailable is 3.4 GB, so D1 starts when D2a finishes and runs beside D2b's lane (1 server + 1 JVM) instead: the box rule's 1.5 GB floor decides the order, the runbook's content is unchanged.
