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

### P2 — Annotations A/B (the thesis in miniature) — **T2 built 2026-09-08**

Status: 30 tier-2 choice-trap puzzles in `puzzles/t2/`, 10 per family,
admitted 30/30 through strict-choose XMage (and at the verdict level
through the local runner). Families: `face-not-decoy`, `right-burn`,
`creature-only` — every board a forced win where one plausible wrong
choice loses. Two engine findings folded in:

- `spike-block-unscripted`: strict-choose **auto-declines** a defender's
  unscripted blocks. So no trap is premised on "they would block", and
  every tier-2 defender creature is tapped (enforced by test) so the
  engine artifact never contradicts real Magic. Remove-the-blocker traps
  wait for a scripted-opponent mechanism (P4's response rounds).
- A creature-only spell cast at a player is refused *silently* (the cast
  never happens; status stays `executed`), not errored — the trap still
  loses by shortfall, and the notes record the observed mechanism.

**A/B run 2026-09-08** (`research/data/eval_t2_ab_haiku_2026-09-08.json`):
fable arm (a) saturated T2 (30/30, after the winner-short-circuit driver
fix), so the comparison moved to haiku per the pre-registered contingency.
Haiku: arm (a) 28/30 vs arm (b) 28/30 — a tie at one seed, both near the
instrument ceiling. Family movement: annotations closed creature-only
(9→10); right-burn slipped (9→8, one agent over-cast against an explicit
cannot-cast-everything annotation). All four losses across both arms are
the same failure mode — casting past available mana, dying as a strict-mode
unexecutable cast — which one engine rollout catches: P3's arm (c) should
eliminate it by construction. Seeds debt on record: the tie is 1-seed
exploratory; ≥7 seeds or a harder tier before any published claim.
- `cardguru/lines.py`: parse/validate proposed lines client-side (reuse
  `validate_scenario` + mana arithmetic); illegal → one bounded retry with the
  validator's message, exactly like the compile loop's repair signal.
- Run **arm (b)** — annotated prompt, still no search — same 7 seeds.
- T2 puzzles built (~30), using P1's observed failures as trap templates.
- Exact permutation test over arm (a) vs (b), per tier.
- **Exit:** an honest verdict on "does structured knowledge alone help?" —
  either direction is publishable; the repo's methodology holds us to it.

### P3 — Search, linear value first (no new model turns) — **arm (c) DONE 2026-09-08**

Result (`research/data/eval_t2_armC_haiku_2026-09-08.json`): **haiku arm (c)
is 30/30 on T2 — the pre-registered prediction confirmed.** Same model,
same seed, same instrument: bare 28/30, annotated 28/30, search+linear
30/30. 114 candidates simulated, 13 engine-vetoed across 7 puzzles; on
`t2-right-burn-017` three of four candidates over-cast and died in
simulation while the lone legal line won. haiku+search ties
fable-without-search. Built: `value.py` (5-term linear scorer, wins
dominate, errors score None), search mode in `puzzlerun` (3-5 candidate
lines, one engine batch, audited picks), `--search` CLI flags. Encoder
context gaps closed the same day (no-summoning-sickness note; graveyard/
exile rendering) — instrument v2. Remaining in P3: arm (d) (LLM value over
the same outcomes) when a tier exists where the linear pick is ever wrong —
on T2 it never was, so c-vs-d needs T3 positions where "which winning line"
or "least-bad loss" is a real question.
- `cardguru/value.py`: the **linear scorer** — life trajectory, clock delta,
  centrality-weighted board delta, cards held — pure Python over outcome JSON.
- Round structure for **arm (c)**: subagent proposes 3–5 lines (one turn),
  all lines batch-simulate between rounds, linear value picks. Note arm (c)
  adds *zero* model turns over arm (b) — search cost is engine-only.
- Then **arm (d)**: one more round where a subagent scores each outcome with
  the factors in the prompt. c-vs-d is the value-function ablation PokeChamp
  never ran.
- **Exit:** arms (a)–(d) on T1+T2, one table, permutation-tested.

### P4 — Opponent model + T3 (first real minimax) — **T3 + experiment DONE 2026-09-08**

Result (`research/data/eval_t3_abc_haiku_2026-09-08.json`): 30 minimax
puzzles (`t3-bestblock`) where the defender's responses are ENUMERATED and
a line wins only against all of them. haiku, seed 1, instrument v2:
**arm (a) 27/30 → arm (c) search 28/30 → arm (c) + one bounded repair
30/30.** Search removed every strategic loss (the toughness-misjudgment
class); it cannot hedge a format error shared by all of one author's
candidates — the validator-message repair (pre-declared as lines.py's
signal) removes that class, firing only on validation failures, never on
executed losses. Instrument v2 findings folded in: the impossible-response
rule (a scripted block by a blocker the line killed is the opponent losing
an option, not the line losing) and required-field action validation.
**believe.py + T4 DONE 2026-09-08** (`11fda6f`, `072913d`): the
hidden-information step. `believe.py` classifies cards seen into a
posterior over a meta corpus (`meta_decks/`, 3 archetypes), subtracts seen
to get the hidden pool, determinizes hands, and — the payoff —
`materialize_responses` turns the believed archetype into concrete
`opponent_responses` (its single best instant-speed removal, seated in
hand). Tier 4 (`generate_t4`, 20 puzzles) hides the opponent's hand and
gives only cards_seen; the response set is BELIEVED, not enumerated, and
drops into the existing minimax grading. Robust line keeps face-burn reach
that beats "they Bolt your biggest attacker"; greedy loses to it. Belief
logic is engine-free (6 tests) and generation has an engine-independent
face-damage proof gate. **Result (`eval_t4_ac_haiku_2026-09-08.json`),
graded on a dedicated 2nd XMage checkout (`~/Documents/mage-beliefs`) so it
ran parallel to live-matches without clobber:** 20/20 engine admission;
haiku arm (a) single-answer 19/20 (one real hidden-info misplay — burned
the blocker, lost to the believed Bolt), arm (c) search recovers it →
20/20 after one bounded format repair (18/20 pre-repair: two harness/format
misses, not strategy). Search plays around removal it never sees. Ceiling
effect: strategic discrimination is one puzzle at this difficulty.
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

### P5 — Live matches (the Java finally happens) — **server mode DONE 2026-09-08**

Driver server mode shipped and verified (`0d810f5`): persistent JVM via a
spool directory (`-Dcardguru.server.spool`), atomic file handshake, READY/
SHUTDOWN markers, `reset()` between runs; Python `MageServer` wraps it with
atexit cleanup and a process-wide singleton; CLI `--engine xmage-server`.
A full 30-puzzle T3 minimax grade (~350 scenarios) runs in 3–4.5s after a
one-time ~7s warmup, identical verdicts to batch mode. This is the
decision-loop latency the interactive match loop needs. **Remaining in P5:
the interactive bridge** — a genuinely new capability (drive XMage's real
game loop against `COMPUTER_MAD`, injecting the agent's decision at each
priority) rather than executing a predetermined script. That is the first
step that is NOT a variation of the scenario adjudicator, and the fork
point below.
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
