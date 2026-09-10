# Overnight suite: pilots vs MAD across models, then the best against each other

Branch: `build/stackwise-campaign`. Depends on the search work in
`docs/stack-search-plan.md` (arms (e) and (f)). Written 2026-09-10 before
any of it has run; treat the numbers as estimates until the first game
lands.

## What we want

1. Two seeds vs MAD, **Sonnet 5**
2. Two seeds vs MAD, **Haiku 4.5**
3. Two seeds vs MAD, **Opus 4.7**
4. Two seeds vs MAD, **Opus 5**
5–8. The three best of those pilots playing each other

Every game under one fixed configuration so the model is the only variable:
arm (f) search (`cardguru.project_turn=3 cardguru.respond=true`), required
plans, the current baseline briefing, `--start A`, sonnet-style latency
budget (`--game-timeout 9000`). If g10 (the first valid arm-(f) game,
running now) shows a defect, the suite falls back to arm (e) — it is one
environment variable in the runner, and the plan doc records which ran.

**Models** (verified under this login, all four honoured by `--model`):
`claude-haiku-4-5`, `claude-sonnet-5`, `claude-opus-4-7`, `claude-opus-5`.
Trivial-call cost index: haiku 0.013, sonnet 0.033, opus 4.7 0.082, opus 5
0.078 USD — a proxy for per-call load, and the reason the Opus rows are the
long pole.

**Seeds:** 23 and 31. Both passed the fairness screen (≥3 lands each side
at turn 7) for sonnet. Fairness is partly the pilot's own mulligan, so a
different model can turn the same deal into a screw; the runner does **not**
re-screen (a rejected probe costs 5–10 min unattended) — it logs both sides'
land count at turn 7 and flags the game post hoc. A flagged game still
counts; it is just labelled.

## Honest sizing

| game type | est. wall | why |
|---|---|---|
| haiku vs MAD, arm (f) | ~30 min | ~4s call floor |
| sonnet vs MAD, arm (f) | ~45 min | g8 was 44 min |
| opus 4.7 / opus 5 vs MAD | ~60–90 min | ~2× sonnet per call, more thinking |
| pilot vs pilot | ~1.5–2.5 h | two LLM seats, every window escalates twice |

Items 1–4: 2 × (30 + 45 + 75 + 75) ≈ **7.5 h**. Items 5–8: 4 × ~2 h ≈
**8 h**. Sequential that is ~15 h — two nights, not one. Two levers:

- **Concurrency 2.** The bottleneck is LLM latency, not CPU, so two games
  at once is close to 2× throughput if rate limits hold. Unknown for Opus on
  a subscription login; the runner starts at 2 and drops to 1 if a game
  sees three consecutive `claude -p` failures.
- **Split across two nights**: 1–4 tonight, 5–8 tomorrow after the
  pilot-vs-pilot harness has been validated in daylight. This is the
  recommended shape regardless — 5–8 needs new code that should not be
  first exercised unattended.

## Selection for 5–8 (noisy by construction)

Two games per model cannot rank four pilots — every record is 0, 1 or 2.
Rank by **wins, then average life margin at the end, then tap-out rate
(lower is better)**. Pairings with three pilots A>B>C: A–B, A–C, B–C, each
with the higher-ranked pilot on the play, plus a fourth game re-running A–B
with seats swapped. Four games, every pilot plays twice.

State up front what this can and cannot say: it is a **qualitative** read —
which model's plans and holds look better in the digests — not a ranking
with error bars. The handoff's power table (≈40 games for a 70% rate) still
applies to any claim about win rate.

## Build list (before anything runs unattended)

1. **Suite runner** — `benchmark/run_suite.py`: a queue of `(model, seed,
   props, opponent)` jobs, N workers, each job = one `run_mirror.py` call
   with its own out-dir, `CARDGURU_DRIVER_PROPS` set. After every game:
   append one self-describing row to `research/data/suite.jsonl` (model,
   seed, arm props, opponent, result, turns, wall, tap-out count, hellbent
   turn, land counts at t7, review-digest path), then `git commit` + `git
   push` the game's files. A game that dies is recorded as such and the
   queue moves on. Writes `research/data/suite_status.json` every 60 s:
   current jobs, turn, life, elapsed, last error — this is what the
   heartbeat reads, so the heartbeat itself costs nothing.
2. **Model in the game record** — `run_mirror.py` writes the model and the
   driver props into its `mirror.jsonl` row. Today only the seed and search
   mode are recorded; the suite must not depend on file naming to know
   which model played.
3. **Pilot-vs-pilot harness** (items 5–8 only):
   - driver: seat `PlayerB` as a second `InteractiveTestPlayer` when
     `cardguru.interactive.spool.b` is set; tag every request with `seat`;
     make `observableState` **self-relative** so each pilot sees itself as
     "A" (hand, `our_*` leaf fields, attack/block indices all assume that);
   - bridge: route requests by `seat` to two esc-dirs, one `YieldGate` per
     seat, `belief_summary` against the other seat;
   - runner: two daemons with two models, one game record naming both.
   Validate in daylight on one short game before it is queued.
4. **Heartbeat** — `CronCreate` `*/10 * * * *` in this session (session-only,
   fires only while idle, 7-day expiry). Each fire reads
   `suite_status.json` and prints one line: `alive HH:MM | job k/N model
   seed | turn T | A L1 vs B L2 | elapsed | last event`. Pushes a
   notification only on: a game finishing, a game dying, the queue
   emptying, or the status file going stale (> 15 min), which is how a dead
   container shows up. Not every 10 minutes — that would be noise, and the
   line in the session is the "I am alive".

## Risks, stated

- **The container is ephemeral.** The heartbeat is also what keeps the
  session active; if the container is reclaimed, the games die with it.
  Per-game commit+push means nothing already finished is lost; the queue
  restarts from `suite.jsonl` (done jobs skipped).
- **Opus rate limits on a subscription login** are unmeasured. First Opus
  game is the canary; the runner backs off concurrency on repeated CLI
  failures rather than burning the night retrying.
- **Same-seed reproducibility is only up to the mulligan.** Two models on
  seed 23 do not see the same game after the first decision. That is fine
  for "how does each model play this deal"; it is not a paired test.
- **Pilot-vs-pilot self-relativity bugs are silent.** A seat-B pilot that
  sees its own hand under "B" will play confidently and wrong. The
  daylight validation must check the B pilot's `why` text refers to its
  own cards correctly.
- **`pgrep -f` self-matching** has bitten three watchers this session. The
  runner and the heartbeat use `[b]racket` patterns or pid files, never a
  plain `pgrep -f name`.

## Order of operations

1. Let g9 and g10 finish (arm (e) and arm (f) on seed 31). Confirm g10:
   `resp_fired > 0`, no failed samples, no wrong-turn projections. Pick the
   suite's arm.
2. Build 1, 2, 4. Dry-run: one haiku game through the suite runner with the
   heartbeat armed, ~30 min, watched.
3. Queue items 1–4 (8 games, concurrency 2, ~4–5 h). Sleep.
4. Next day: read the eight digests, rank, build and validate 3, queue 5–8.

## Status (05:22 UTC)

- Dry run aborted at turn 13 after 61 min: every pilot call was resuming
  one shared session (see the harness-bug entry in
  `docs/stack-search-plan.md` §8 Status), so the game was both slow and
  cross-contaminated with g10. Fixed in 173be2d; partial data kept under
  `research/data/suite/aborted/`.
- Full suite launched at 05:22: 8 jobs, 2 workers, arm (f) props, haiku
  seeds 23 and 31 first. Per-game rows land in `research/data/suite.jsonl`
  and each game commits and pushes on completion.
- Keepalive: in-session heartbeat every 10 min plus a server-side hourly
  Routine that restarts the queue from `suite.jsonl` if the runner dies.
- First clean calls (05:25): both haiku games on their own session ids,
  contexts 22k–45k tokens. Residual per-decision time is **thinking
  output**, not context: 1.5k–5k output tokens per decision at haiku's
  ~100 tok/s = 15–56 s. The pilot inherits `CLAUDE_EFFORT=high` and
  `MAX_THINKING_TOKENS=31999` from the launching environment. Left as-is
  for the suite so effort is not a confound across models; it is the one
  knob if games need to be faster.
- **06:31 haiku s23 FAIL at turn 12 (69 min): `IllegalStateException:
  JsonNull`.** The pilot answered `{"choice": null, "why": "Awaiting next
  game state…"}` at its own upkeep and the driver's `getAsInt()` threw.
  Fixed on both sides: the driver reads every integer field through
  null-tolerant helpers (`intOr`/`intOf`/`arrOr`, a non-number is "no
  pick" and falls through to the existing fallback), and the daemon
  treats a null required key as a schema violation and retries with the
  reminder. The two games already running (haiku s31, sonnet s23) carry
  the old code; the runner only skips *completed* jobs, so haiku s23 is
  re-queued by the next `launch_suite.sh` (the hourly Routine issues it
  when the runner has exited with jobs unfinished).
- **06:38 sonnet s23 "loss in 12 turns, 6 min" is a harness artifact,
  row dropped, directory archived.** With a fresh session per game the
  pilot has no earlier examples of the leaf_eval format, and sonnet
  scored one number per *candidate* (4 scores for 12 leaves) on eight
  straight searches. The driver drops a short list and escalates the
  window as a plain priority decision — but the pilot had attached
  `yield_until` to the search reply, so the bridge auto-passed the
  escalation. Net effect: zero lands played through turn 9. Three fixes:
  the daemon's leaf_eval schema now says "exactly leaf_count numbers, one
  per LEAF, not per candidate" and a short list is retried with the count
  spelled out; the bridge's YieldGate does not cover the escalation of
  the window the yield was set in; and sonnet s23 re-runs on the relaunch.
  haiku s31 (loss, kept) had 3 short replies out of 63, all late; haiku
  s23 and sonnet s31 none so far. g9's 14 mismatches were all *over*-long
  lists on 88–119-leaf searches, which the driver truncates.

## Exit

`research/data/suite.jsonl` has 12 rows; `docs/overnight-suite-results.md`
summarises each pilot's record, tap-out rate, hellbent turn and one
sentence on how it played, with the three digests worth reading linked.
