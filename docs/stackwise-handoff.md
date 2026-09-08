# Stackwise handoff (session refresh) — 2026-09-08

A PokeChamp-style MTG agent built on CardGuru. This doc is written to survive a
session reset: it says where everything is, what's proven, how to run it, and
what's next. Read `docs/agent-design.md` (architecture) and `docs/agent-plan.md`
(phase log with results) alongside this.

## Worktrees & checkouts (IMPORTANT — non-obvious layout)

All work lives in git worktrees of the CardGuru repo, NOT the primary
`/Users/michaelsutanto/Documents/CardGuru` dir (that's on an unrelated branch).

| path | branch | role |
|---|---|---|
| `~/Documents/CardGuru-agent` | `build/stackwise-p0` | **TRUNK** — everything is merged here |
| `~/Documents/CardGuru-live` | `agent/live-matches` | interactive bridge — **already merged into trunk** |
| `~/Documents/CardGuru-minimax` | `agent/live-minimax` | sim-backed minimax — **IN FLIGHT** (see bottom) |

XMage checkouts (gitignored, external): `~/Documents/mage` and
`~/Documents/mage-beliefs` (a 2nd, built so two tracks could grade in parallel
without driver clobber). Both built (Java 24, Maven 3.9). Pass `--mage-repo` or
set `CARDGURU_MAGE_REPO`.

**Gotcha:** the driver `driver/CardGuruScenarioRunner.java` is copied into the
mage checkout by `adjudicate.ensure_driver` on every engine run. Two processes
running the driver against the SAME checkout clobber each other — that's why a
2nd checkout exists. One checkout per concurrent engine user.

`data/` is gitignored (large artifacts, hardlinked/copied between worktrees).
The meta-deck corpus is source, so it lives in `meta_decks/` (NOT `data/`).

## What's built and proven (all on trunk, 304 tests green)

The benchmark is graded by EXECUTION through XMage (strict-choose): a proposed
line is spliced into a board and run; any line that wins, wins (no golden-line
matching). Model turns in testing are in-session Claude subagents (the
`agent_bridge` replay pattern) — zero API spend.

- **P0** `cardguru/puzzle.py` (format/splice/grade/admit), `localrunner.py`
  (provisional no-engine tier-1 grader), `puzzlegen.py` (generators with
  brute-force/independent win proofs). 30 T1 puzzles, 30/30 engine-admitted.
- **P1** `encoder.py` (board→prompt; `bare` and `annotated` modes),
  `puzzlerun.py` (subagent run bridge). **Result: fable T1 arm(a) 60/60,
  saturated** (`research/data/eval_t1_armA_2026-09-08.json`).
- **P2** annotated mode + T2 choice-trap puzzles (30, `puzzles/t2/`).
  **fable arm(a) 30/30 (saturated) → moved to haiku: arm(a) bare 28/30,
  arm(b) annotated 28/30** (tie; both near ceiling). Losses were all
  over-cast-past-mana → pointed at search.
- **P3** `value.py` (5-term linear leaf value, no LLM) + search in `puzzlerun`
  (propose 3–5 candidate lines, simulate all, pick argmax). **haiku arm(c)
  search 30/30 on T2** — beat annotations at the same model; the PokeChamp
  "scaffold beats the model" result in miniature.
- **P4** T3 minimax puzzles (30, `puzzles/t3/`, enumerated opponent responses;
  a line must beat ALL). **haiku a 27/30 → c search 28/30 → c+repair 30/30.**
  Then `believe.py` (opponent model: classify cards-seen → archetype posterior
  → hidden pool → determinized hands → `materialize_responses`) + T4 belief
  puzzles (20, `puzzles/t4/`, responses BELIEVED not enumerated).
  **haiku a 19/20 → c search 20/20** — search plays around removal it never
  sees (`research/data/eval_t4_ac_haiku_2026-09-08.json`).
- **P5** driver **server mode** (persistent JVM, spool protocol,
  `--engine xmage-server`, ~3–4.5s/grade after one warmup) + **interactive
  mode** (real 1v1 game, decisions over spool) + **live minimax** (`--minimax`:
  sim-backed max-over-min at declare-attackers via `createSimulationForAI`,
  `GameStateEvaluator2` leaf; PokeChamp-shaped, engine-executed leaves; see
  `docs/live-minimax.md`). `cardguru/play.py` MatchClient + policies
  (dumb/pass/belief) and `--minimax`. `belief_policy` reads the live opponent,
  classifies via believe.py, plays around unseen removal.
  **CORRECTION: the live opponent is PASSIVE, not COMPUTER_MAD.**
  `TestComputerPlayer extends ComputerPlayer` (base), whose `priority()` just
  `pass(game)`s, and `mage-player-ai-mad` (the real alpha-beta ComputerPlayer6)
  is NOT on the Mage.Tests classpath. So the opponent never plays/blocks —
  every live "win" (dumb/belief/minimax) is integration proof only, NOT
  strength. The minimax search is nonetheless real: the `--opp-blockers N`
  scaffold seats blockers and shows a genuine max-over-min declining a bad
  attack. #1 next step: put `mage-player-ai-mad` on the classpath, seat
  `ComputerPlayer6` as playerB.

Result records: `research/data/eval_t{1,2,3,4}_*.json`. Full narrative +
concrete examples: the **research log artifact**
(https://claude.ai/code/artifact/9b43666c-c9c8-4e4d-83a2-345c4cd8d64e) and the
**design page** (https://claude.ai/code/artifact/2b0c287b-9536-4d6b-89b7-55bf4fe10969),
both owned by the user (private).

## How to run things (from `~/Documents/CardGuru-agent`)

```bash
# generate + engine-admit a tier
python3 -m cardguru puzzle gen --tier 4 --seed 23 --count 20
python3 -m cardguru puzzle admit puzzles/t4/*.json --engine xmage --mage-repo ~/Documents/mage

# subagent benchmark run (the arms): init tasks, spawn one subagent per
# pending/<id>.md to write answers/<id>.txt, then collect+grade
python3 -m cardguru puzzle agent-init  puzzles/t4/*.json --run runs/X --arm a --seed 1 [--search] [--mode annotated]
#   (spawn: one Agent per pending file; model haiku for the discriminating tier)
python3 -m cardguru puzzle agent-collect puzzles/t4/*.json --run runs/X [--search] --engine xmage --mage-repo ~/Documents/mage

# live match vs the built-in AI
python3 -m cardguru play --games 2 --policy belief --mage-repo ~/Documents/mage-beliefs

python3 -m pytest tests/ -q     # 304 green
```

**Subagent run protocol (the core testing loop):** each `pending/<id>.md` is a
self-contained task (board + action vocabulary + answer format). Spawn ONE
subagent per file (fresh context, no tools, no goldens) to write
`answers/<id>.txt` raw. `agent-collect` parses (raw, uncleaned — replay must be
as unkind as the API), grades in one engine batch, writes `results.json`.
**Repair rounds** (used in T3/T4): if a run has validation/format losses (not
strategic), append the validator/engine error to a `<id>.repair.md`, re-run
that one subagent, re-grade. Preserve `results.pre-repair.json`. Repair fires
ONLY on validation failures, never on executed losses.

## Key gotchas (learned the hard way)

- **Multi-block**: duplicate blockers need `Name:index`; 2+ blockers on one
  attacker need the attacker's damage assignment scripted as `X=<n>` choices
  (`docs/scenario-spec.md`).
- **Unscripted defender blocks auto-decline** in strict mode → T2 puts the
  agent on defense; T3/T4 enumerate/believe the opponent's responses.
- **impossible-response rule** (`puzzle.response_impossible`): a scripted
  response the agent's line made illegal (e.g. blocker already killed) is
  excluded, not counted as a loss.
- **winner short-circuit** in the driver: a line ending the game before its
  trailing scripted actions is a win, not a leftover-actions error.
- **no summoning sickness** on setup-placed creatures — stated in every task.
- **arm (d)** (LLM value function) is built into the plan but has NEVER run:
  the linear value was never wrong on T1–T4, so there's no headroom yet. It
  needs positions where "which winning line / least-bad loss" is a real
  multi-turn question.
- **seeds debt**: every arm result is 1 seed, exploratory. ≥7 seeds + exact
  permutation tests before any published claim.

## The rollout primitive & minimax status

- Puzzle rollout = serialize state → splice line → execute fresh (works because
  we author the start state). This IS depth-2 line-minimax already: MAX over our
  candidate lines, MIN over opponent responses (enumerated T3 / believed T4),
  engine at the leaves, linear value. That's PokeChamp's shape.
- **Live** search needs a fork-the-live-game rollout. Verified primitive:
  XMage's MAD AI uses `game.createSimulationForAI()` (in
  `Mage.Player.AI.MAD/.../ComputerPlayer6.java`) to copy+simulate. Wiring that
  into our player is the in-flight build below.
- PokeChamp's value fn = LLM zero-shot over a factor rubric (no training, no
  dataset); ours = measured linear over real engine outcomes. Our leaves are
  executed, not estimated — the advantage to lean on.

## IN FLIGHT: agent/live-minimax

A background agent is building simulation-backed minimax over the attackers
decision in `~/Documents/CardGuru-minimax` (branch `agent/live-minimax`): at
declare-attackers, enumerate candidate attack sets → `createSimulationForAI()`
copy → declare each on the copy → built-in AI supplies the block (the min
layer) → evaluate the leaf → play the argmax to the real game. Depth ~1.5,
PokeChamp-shaped, engine-executed leaves.

**To pick it up:** check the branch's commits + `docs/live-minimax.md`, run its
tests, then merge into `build/stackwise-p0` (expect conflicts only in
`driver/CardGuruScenarioRunner.java`, `cardguru/play.py`, `cardguru/cli.py` —
all additive, like the live-matches merge). Its report will name the verified
`createSimulationForAI` usage and the biggest remaining limitation.

## Next steps (priority order)

1. **Put `mage-player-ai-mad` on the `Mage.Tests` classpath and seat
   `ComputerPlayer6` (MAD) as playerB.** Until this, the live opponent is
   passive and no live win/loss means anything. This unblocks 2–4.
2. A real constructed deck (replace the hardcoded mono-red plumbing deck) so
   live win/loss becomes a strength signal.
3. Externalize in-cast sub-choices (targets/mana/X) for full LLM control — the
   live-match feasibility doc names this as the last blocker.
4. Pay down seeds debt (≥7) on the arm comparisons that would go in a writeup.
5. Then: mage-bench ladder for external Elo; the arm (d) LLM-value ablation
   once a tier gives it headroom.

Done since first draft: `agent/live-minimax` merged (`538a2ad`); sim-backed
minimax over attacks shipped (`docs/live-minimax.md`); COMPUTER_MAD overclaim
corrected.
