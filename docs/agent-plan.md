# Build plan: Stackwise in phases, subagent-tested from day one

Companion to `docs/agent-design.md` (architecture) — this is the execution order.
Two commitments shape everything here:

1. **A simple benchmark comes before any agent.** We build the graded puzzle
   suite first and get a raw-LLM baseline on it before writing a line of search
   code, so every later phase has a number to move.
2. **Every model turn in testing is an in-session Claude subagent**, via the
   `agent_bridge.py` replay pattern — no API keys, no spend, and the loop that
   runs is the production loop with the client swapped. When we later point the
   same code at the API, nothing else changes.

## The round protocol (how subagent testing works)

`agent_bridge` already proves the shape on the NL→DSL compiler: everything but
the model turn is deterministic, so a run advances by replay. We generalize
`RunDir` from compile tasks to gameplay tasks; the loop is unchanged:

```
round N:  orchestrator replays all recorded answers
          → every puzzle/game that needs a model turn writes pending/<id>.md
            (self-contained: board rendering, annotations, answer format)
          → BATCH-simulate anything simulatable (one maven invocation,
            all scenarios from all puzzles together — warmup paid once/round)
          → stops
          (in-session: Claude spawns subagents that answer pending/*.md
           into answers/<id>.txt — one subagent per task, no shared context,
           forbidden from reading goldens/dataset, same rules as compile tasks)
round N+1: collect_answers() folds them in; replay continues past them for free
```

Key consequence: **we never need interactive engine access for benchmarks.**
Search itself is roundable — propose lines in one round, batch-simulate all
rollouts between rounds, value them in the next. The Java server mode
(persistent JVM) is deferred all the way to live matches (P5). Until then the
existing batch adjudicator is the only engine path, unmodified.

Puzzles are 1–3 rounds each; a whole tier of 30 puzzles resolves in a handful
of subagent wall-clock minutes. Determinism note (learned from the compile
bridge): answer files are raw model output, never cleaned — the replay must be
exactly as unkind as the API.

## Benchmark tiers (simple first)

Graded by execution, all-or-nothing: the agent's chosen line is spliced into
the puzzle's state as a scenario, batch-run through the adjudicator, and the
puzzle's `win` expectations checked (`life`, `permanent_count`, winner). No
string matching against a "correct answer" — any line that wins, wins.

| Tier | Skill | Example | Needs |
|---|---|---|---|
| **T1 lethal** | count damage, attack correctly | opponent tapped out at 6, you have lethal on board through blockers | encoder + one model turn |
| **T2 traps** | one right interaction | kill the right threat (ward/indestructible decoy present); block to survive, not to trade | + annotations (verdicts, windows) |
| **T3 lines** | worst-case reasoning | tap out for the walker vs hold up removal, counter in their hand in k of K determinizations | + multi-line search + opponent turn |

Sources: hand-built (adapting the 32 existing `scenarios/`), the 6,021
harvested XMage test records mined for positions with a forcing win, and — for
T1 volume — generated: random legal boards where a lethal attack provably
exists (a generator can verify "lethal exists" by brute-forcing attack subsets
through the damage math before we ever ask an agent).

## Phases

### P0 — Puzzle format + grader (no agent, no new Java) — **DONE 2026-09-08**

Status: `cardguru/puzzle.py` (format/splice/grade/admit), `cardguru/
localrunner.py` (provisional tier-1 grader; see below), `cardguru/
puzzlegen.py` (generator with brute-force win proofs), `puzzle` CLI,
30 T1 puzzles in `puzzles/t1/` at 30/30 admitted, 15 tests. Two findings:

- **Blocks are decisions.** Strict-choose XMage fails on any unscripted
  decision, and the defender's blocks depend on the agent's attackers — so
  T1 boards guarantee the defender has NO untapped creatures. T2 "block
  correctly" puzzles put the *agent* on defense (its blocks are its line);
  puzzles that need a *defending opponent policy* wait for P4's response
  rounds.
- **Grading runs before the engine does.** Admission first ran through a
  local combat-arithmetic runner that executes exactly the tier-1 slice and
  errors loudly outside it; grades are stamped `engine: local-combat`.
  **Engine verification since done** (2026-09-08): an XMage checkout now
  lives at `~/Documents/mage` (shallow clone, prebuilt; pass
  `--mage-repo`), and all 30 puzzles re-admitted 30/30 with
  `--engine xmage` — the local runner and the engine agree on all 60 known
  lines, which is the provisional instrument's own validation.
- **Multi-block is solved, with a vocabulary cost.** Verified by spike
  (`scenarios/spike/`): duplicate blockers need `Name:index` notation, and
  2+ blockers on one attacker surface a hidden ATTACKER decision — a
  multi-amount damage assignment scripted as consecutive `X=<n>` choice
  entries. Documented in `docs/scenario-spec.md`. Consequence for T2/P3:
  a line that attacks into possible multi-blocks must carry its damage
  assignment, and the line proposer's action vocabulary must teach this.
- `puzzles/` format: a scenario minus `actions`, plus `win:[...]` checks and
  `tier`, `trap`, `notes` fields (mirroring the benchmark questions' schema).
- `cardguru/puzzle.py`: splice a proposed line into a puzzle → scenario;
  batch-grade many (puzzle, line) pairs in one adjudicator run.
- `cli`: `puzzle validate`, `puzzle grade <run>`.
- ~30 T1 puzzles, adjudicator-verified: for each, a known winning line runs
  green and a known losing line runs red *through the engine* before the
  puzzle is admitted. (Instrument before system — a puzzle that can't
  distinguish a good agent from a bad one is measurement noise.)
- **Exit:** `puzzle grade` on hand-written good/bad lines scores 30/30 vs 0/30.

### P1 — Encoder + bridge + raw baseline (the first number) — **DONE 2026-09-08**

Result (`research/data/eval_t1_armA_2026-09-08.json`): **arm (a) on T1 is
60/60 — saturated.** Two seeds × 30 puzzles, fable-class subagents on bare
boards, engine-graded, zero invalid or unparseable lines. Two consequences,
both applications of the repo's own findings:

- **Stopped at 2 of 7 planned seeds.** "Saturated, not noisy" — with 60/60
  and no line-format failures, additional seeds buy no resolution; the
  deviation is recorded here rather than silently normalized. T1 stays in
  the suite as the regression floor (any future harness change that breaks
  it has broken something basic) and as the sanity check for *smaller*
  models, where it may well not saturate.
- **The discrimination lives in T2+, as designed.** A frontier model does
  not blunder open lethal with clean arithmetic. The a-vs-b comparison
  (annotations) moves to T2 traps, where the P2 exit criterion always
  lived. Build T2 before spending another model call on T1.

Also worth keeping: line diversity was real (minimal-lethal single-attacker
lines, leave-the-crab-home partial attacks, exact-mana double-burn lines) —
every one legal and winning, which exercises the execution-grading claim
that any winning line counts, no golden-line matching anywhere.
- `cardguru/encoder.py`: puzzle/outcome state → prompt rendering; two modes,
  `bare` (board only) and `annotated` (clock, connect-verdicts, windows —
  computed, PokeChamp's turns-to-KO trick).
- Extend `agent_bridge` with gameplay task files: board rendering + the action
  vocabulary from `docs/scenario-spec.md` + "answer with a line as JSON."
- `cli`: `agent-run init/collect` for puzzle runs (same UX as compile runs).
- Run **arm (a)** — bare board, single answer, no search — with subagents,
  7 re-runs (fresh subagent per seed, prompts identical; variance is the
  model's). Grade. This is the "raw LLMs blunder X% of forced wins" headline.
- **Exit:** arm (a) T1 number recorded in `research/data/`, with per-puzzle
  outcomes and the failed lines kept (they seed T2's trap list).

### P2 — Annotations A/B (the thesis in miniature)
- `cardguru/lines.py`: parse/validate proposed lines client-side (reuse
  `validate_scenario` + mana arithmetic); illegal → one bounded retry with the
  validator's message, exactly like the compile loop's repair signal.
- Run **arm (b)** — annotated prompt, still no search — same 7 seeds.
- T2 puzzles built (~30), using P1's observed failures as trap templates.
- Exact permutation test over arm (a) vs (b), per tier.
- **Exit:** an honest verdict on "does structured knowledge alone help?" —
  either direction is publishable; the repo's methodology holds us to it.

### P3 — Search, linear value first (no new model turns)
- `cardguru/value.py`: the **linear scorer** — life trajectory, clock delta,
  centrality-weighted board delta, cards held — pure Python over outcome JSON.
- Round structure for **arm (c)**: subagent proposes 3–5 lines (one turn),
  all lines batch-simulate between rounds, linear value picks. Note arm (c)
  adds *zero* model turns over arm (b) — search cost is engine-only.
- Then **arm (d)**: one more round where a subagent scores each outcome with
  the factors in the prompt. c-vs-d is the value-function ablation PokeChamp
  never ran.
- **Exit:** arms (a)–(d) on T1+T2, one table, permutation-tested.

### P4 — Opponent model + T3 (first real minimax)
- `cardguru/believe.py`: archetype prior from a small `data/meta_decks/`
  corpus; believed-list updates from cards seen; K determinization samples.
- Response round: subagent-as-opponent proposes responses per line (prompted
  from their seat with the believed list); line × response × K batch-simulates;
  controller takes max over min.
- ~20 T3 puzzles where the greedy line and the minimax line *differ* and the
  engine confirms the greedy line loses to the best response.
- **Exit:** arm (d) beats arm (b) on T3 specifically — search earns its cost
  where worst-case reasoning is the tested skill. If it doesn't, we learn that
  before building any live-match plumbing.

### P5 — Live matches (the Java finally happens)
- Driver server mode (~100 LOC: persistent JVM, socket loop) + richer state
  dump + winner short-circuit, per `docs/agent-design.md`.
- `cardguru/play.py` match loop vs XMage `COMPUTER_MAD`, fixed Standard
  aggro–midrange pairing; the subagent bridge still serves model turns for
  local matches (a game is just a longer replay), API client optional.
- **Exit:** >50% vs COMPUTER_MAD across ≥25 matches; then the mage-bench
  spike for external Elo and replays.

## What we deliberately defer

- mtg-engine's branch/rewind timeline (better search substrate, ~4/200 effect
  handlers today) — revisit when search depth, not the environment, binds.
- Commander/multiplayer (politics breaks two-player minimax), sideboarding,
  mulligans-as-decisions (T1–T3 puzzles start post-mulligan; mulligan policy
  is its own small benchmark later).
- Any LLM training or fine-tuning — the PokeChamp result we're transposing is
  precisely that none is needed.

## Risk register (short)

- **Scenario spec can't express a needed line** (e.g. activated abilities in
  combat, split second) → P0 surfaces this while puzzles are cheap to reshape;
  extend the spec vocabulary before P3, not during.
- **Harvested corpus yields few forcing wins** → the T1 generator carries
  volume; harvested records still serve T2 traps.
- **Subagent runs drift from API behavior** → the bridge's own rule already
  covers this: raw answers, no cleaning, no tool access, no goldens; and P5
  runs a small API-client spot-check of one tier before any external claim.
