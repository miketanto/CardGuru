# Capability plan — can the network play combat, tier by tier?

Design only; nothing here has been run. Branch `v7/lane-d`, written
against `LEVELSET.md`, `rl/V7-VALIDATION.md` §15/A4L, §15/C, §15/D and
`rl/CURRICULUM-LADDER.md`. Steps are gated one at a time.

## The ask, mapped onto what already exists

The request is a combat competence ladder — correct combat, then
keywords, tricks, removal, flash, global effects, activated abilities —
with, at each tier, evidence that the tier survives a slightly different
version of the same cards. Most of that ladder is already specified:

| Tier asked for | Ladder rung | Status |
|---|---|---|
| correct combat | `W0Base` | recorded; combat labels FAILED their gate |
| keywords | `W1Fly` / `W1Fst` / `W1Vig` / `W1Lif`, control `W1Ctrl` | 1a-1c run, all readings void or not interpretable; 1d unrun |
| composition | `W2FlyLif`, control `W2Ctrl` | unrun |
| removal | `W3Sorc`, black branch `B1Narrow` | unrun on this ladder |
| tricks / flash | `B1Fast` (instant twin of `B1Narrow`), `W4` | unrun; B1 timing A/B exists separately |
| global effects | — | no rung designed |
| activated abilities | — | no rung designed |

And the adaptation axis the request wants is the ladder's own control
design: `W1Ctrl` is the same four-card swap with **no** keyword, so
"trained on a deck whose 2/2s have different names" is already separated
from "learned the keyword". The built-but-unrun twin-deck probe
(`LEVELSET.md` §4: same stats, all-new names) is the second half of it.

So this is not a new ladder. It is the existing ladder, blocked.

## Three blockers, in the order they bind

### B1. The combat simulator is keyword-blind — and says so itself

`rl/xmage-src/CombatMath.java:33-36`, verbatim:

> SCOPE. Vanilla bodies only: no first strike, deathtouch, trample,
> flying or menace. Rung 1 introduces exactly those, and each one needs
> an explicit change here — `resolve()` will silently give wrong answers
> for them, so RUNG1 decks must not use this until it is extended.

`CombatMath.Body` (line 49) is power, toughness, name. Nothing else.

> **Correction (same session, before any run).** This section first
> claimed `JointCands.theirBlockers` (line 38) was defective for
> collecting untapped creatures with no `canBlock` check. That is wrong
> and the claim is withdrawn: `theirBlockers` is the defender's *body
> pool* for the attack-side simulation, and block legality is enforced
> where assignments are actually made — `RLPlayer.java:1156`, `:1182`,
> `:1258` each gate on `canBlock`, as does `TeacherLogPlayer.java:250`.
> What survives is the keyword blindness above: the attack-side pricing
> treats every one of those bodies as able to block the attackers,
> because `Body` has no evasion, which is the same B1 defect and not a
> second one.

Rungs 1a-1c ran on `W1Fly`, `W1Fst`, `W1Vig` anyway. Every combat
candidate on those decks was enumerated, priced and Pareto-filtered by a
simulator that cannot see the one card property the rung exists to test,
and the candidate *features* the network reads (`forAttackSet`'s damage
taken / value lost) are computed the same blind way. **This invalidates
the combat half of the keyword rungs independently of the logit-bound
freeze (§15/D) and independently of coverage (§15/C)** — three separate
reasons, one conclusion: no keyword-aspect combat result exists yet.

Tiers 2 and up cannot be attempted before this is fixed. Not "would be
noisy" — the instrument is documented as wrong for them.

### B2. Up to half of contested combat is not expressible

§15/C: joint-attack / joint-block coverage is 0.598 / 0.604 on `W0Base`
pooled, 0.503 / 0.450 in the mirror lane, against 0.948 / 0.974 on
`BenchDimir`. Coverage is opponent-dependent and worst where combat is
most contested.

Reading the generator explains the shape and makes it testable.
`JointCands.attacks` (line 93) enumerates with `CombatMath.bestAttack`
under caps (`attackCap` 4096, `attackReplyCap` 200000), then applies a
**five-objective Pareto filter**, then dedups by outcome key, then cuts
at `attackMaxCands` 64; `attackChoiceSet` (line 57) first drops all but
the 12 biggest bodies. Every one of those is a way to lose the teacher's
declared set, and they are distinguishable:

- **never enumerated** — outside the choice set, or a cap was hit;
- **enumerated then dominated** — the five objectives priced it worse;
- **enumerated then deduped** — collapsed into another set's outcome key
  (aliases already count as covered, so this should be small);
- **truncated** — fell past the 64-candidate cut.

**Pre-registered hypothesis: the hole scales with board width.**
`BenchDimir` is narrow and covers at 0.95; `W0Base` is a pure-creature
deck whose mirror lane produces 2.5x the combat consults and covers at
0.50. If that is right, coverage is a property of the filter under many
bodies, not of the decks, and it will follow the same curve on every
tier of this ladder. Stated in advance so a confirmation is not
presented later as a discovery.

### B3. There is no teacher-independent definition of "correct"

Combat is scored today by top-1 agreement with CP7's declaration. Two
problems for this request. Agreement measures imitation of one
depth-6 alpha-beta player, not correctness; and where coverage misses,
agreement is **capped by construction** — the policy could not have
chosen the label. A tier reading built on it cannot separate "played
combat badly" from "was never offered the move".

## The instrument I propose

One probe that answers both halves at every consult:

1. **expressible?** — is the correct declaration in the candidate list,
   and if not, which of B2's four reasons dropped it;
2. **chosen?** — did the policy pick it, scored among the candidates it
   actually had.

Run over two populations:

- **the real one** — teacher recordings, which is where coverage must be
  measured because it is opponent- and board-dependent;
- **constructed positions** — a small set of authored combat puzzles
  whose correct answer is fixed by construction (lethal / survive / kill
  the attacker and keep the blocker / do not trade down), giving a
  teacher-independent score and a per-concept failure name.

The puzzle half is what turns a tier from a win rate into a capability
claim, and it is cheap: single positions, no games played out. It has a
real limitation, stated now: an authored set is a sample of combat that
we chose, so it can only support "can it do X", never "how strong is
it". Strength stays on the held-out CP7 metric.

## Per-tier reading (pre-registered, applies to every tier)

Each tier gets three sets: **A** new positions with trained cards, **B**
the same positions with functional analogs (the "slightly different
version"), **C** a lookalike control where stats and cost match but the
mechanic differs and the correct answer flips (`W1Ctrl` is the deck-level
version of C).

- **Tier learned:** A ≥ 0.90, interval excluding the stats-only baseline.
- **Tier adapts:** B within 0.10 of A, interval excluding random.
- **Adapts for the right reason:** C ≥ 0.80. B high with C at chance
  reads **"stat-matching, not card reading"** — a real answer, and the
  one every previous encoder A/B was unable to distinguish.
- **Void:** any tier whose coverage on its own decks is below the A4L
  gate is reported as not measurable, never as a low score.

Wilson intervals, ≥100 games or ≥500 puzzle decisions per cell, per
`CLAUDE.md`.

## Step order

| # | Step | Gates |
|---|---|---|
| 1 | Miss-reason census (B2), on `W0Base` + `BenchDimir` | everything combat-shaped |
| 2 | Fix the generator per what Step 1 names; re-measure coverage | tier 1 |
| 3 | Extend `CombatMath` for the rung-1 keywords (B1) | tiers 2+ |
| 4 | Puzzle probe + tier 1 (`W0Base`) A/B/C | first capability claim |
| 5 | Tier 2 keyword rungs, re-run with labels that pass their gate | — |
| 6+ | Tricks / removal / flash, then design rungs for globals and activated abilities | — |

Steps 3 and 4 are independent of each other and of Step 2's fix; Step 1
is upstream of all of them.

---

# Step 1 — spec (for approval; not run)

**Build.** At the teacher's joint attack and block consult, log the
declared set beside the candidate list *and* the reason it was absent
when it is: `not-in-choice-set` / `cap-hit` / `dominated` (naming the
dominating option and the objectives that beat it) / `deduped` /
`truncated`. `JointCands` already computes everything needed — the
enumeration is in `search.options` before the Pareto filter, so the
classification is a re-check against structures that exist, not a second
search.

**Measures.** Which declarations `CombatMath` misses and why, per deck
and per lane; and whether the board-width hypothesis holds.

**Cannot measure.** Whether the missed sets are *better* play (§15/C's
caveat stands — unreachable is not the same as superior); anything about
keywords (B1 is settled by reading the source, not by this); anything
about the network, which is not involved.

**Reading, pre-registered.**
- Mostly `dominated` → the five-objective filter is the hole; the fix is
  retaining dominated sets under a budget, and coverage should be
  recoverable cheaply.
- Mostly `not-in-choice-set` / `cap-hit` → the 12-body choice set and the
  caps are the hole; the fix costs compute per consult and needs a
  throughput check before tier 4.
- Mixed with no reason above ~0.4 of misses → no single fix; report that
  and re-plan rather than patching.
- Coverage not correlated with board width → the hypothesis is wrong, say
  so plainly and treat coverage as per-deck, which makes every tier need
  its own coverage row before its capability row.

**Cost.** A re-record is needed either way: the existing NDJSON stores
candidates as feature vectors, not as sets, so no miss reason can be
recovered offline from it. One recording per deck at A4L rung-0 scale
(1,000 games, ~31k labelled consults there). The census itself is a
counter pass over that recording and is free by comparison.

**Where this runs.** In this container. `rl/setup_engine.sh` rebuilds
the pinned checkout here (clone + `phase9-engine.patch` + the
`rl/xmage-src` overlay), and the recording is CPU-only — no GPU is
involved in a teacher recording, which is CP7 playing itself and
logging. Only the training steps later in the ladder would want the
user's 3060. Throughput on a container of this shape was ~2.6 games/s
scripted (`rl/THROUGHPUT-LOCAL.md`), so a 1,000-game recording is
plausibly well under an hour, but that figure is from the old 4-core
box and is **not** a measurement of this one: the first thing the build
buys is a real throughput number, and the cost above is quoted in games
rather than hours until then.
