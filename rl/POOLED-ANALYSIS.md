# Pooled analysis — five work streams, one picture

Written after the Phase 10 flagship finished, pooling results from every
branch that has landed. Sources, with what each contributed:

| branch | state | contributes |
|---|---|---|
| `p10-flagship-48r5lg` | **complete** (12288 eps) | gated league result, saturation finding, perf diagnosis |
| `e3-features-topn0q` | **complete** | E3 encoder, 3 gates, 512-ep pilot, 2-seed control arm, per-channel ablations |
| `pilots-phase-10-g4ov6z` | **2 of 3 pilots** | trained archetype pilots for sweep + tokens vs the champion |
| `pilots-2-17r9vj` | infrastructure only | pilot lane, picker, supervisor — **no completed runs** |
| `deck-curriculum`, `phase-8-transfer`, `engine-perf` | 0 commits ahead | already merged into phase-5 |

Nothing here is a new experiment. Everything below is a claim that only
becomes visible when two or more branches are read together.

---

## 1. The robustness matrix overstates the agent — by a deck-dependent amount

Every archetype number this project has published, including the Phase
10 flagship's headline table, is measured against a **D0 pilot**. The
pilots branch built the missing instrument: a from-random-init net
trained to pilot the archetype itself, then played against ck_6144.

| deck | trained pilot vs champion | D0 in the same seat | lift |
|---|---|---|---|
| P7cSweepControl | .325 | .140 | **+.185** |
| M3SelesnyaTokens | .465 | .450 | +.015 |

**The looseness is not a constant.** D0 is a bad control pilot and a
perfectly adequate go-wide-and-attack pilot, so the correction is large
on the deck whose plan is "hold priority and answer" and vanishes on the
deck whose plan is "make creatures and attack".

Consequences, stated precisely:

- **Absolute readings of the matrix are inflated on control-style decks.**
  The flagship's "sweep .85, matching ck_6144's .87" is a statement
  about beating a weak sweep pilot. A competent sweep pilot takes .675
  off the champion.
- **Agent-vs-agent comparisons on the matrix survive.** Both agents face
  the same instrument, so its looseness cancels. The flagship's
  "beats ck_6144 on redrush (.60 vs .52), ties on ramp" is a fair
  comparison and stands.
- **7c's caveat is now quantified** rather than asserted: "sweep .76
  means beats D0 piloting control, not handles control" (PHASE7C-REPORT
  §Confidence) — the gap is ~.19 on that deck and ~0 on tokens.

The champion still wins both matchups, so no robustness conclusion
*reverses*; the margins shrink, unevenly.

---

## 2. Blocking: a falsified finding and a confirmed one, which agree

Two branches produced apparently opposite results about declining blocks,
and reading them together resolves both.

- **Flagship (this branch)**: at 4096 the go-wide decks dropped to 85-90%
  blocking with rising win rates — logged as a *candidate* with a named
  falsification test. At 6144 every deck returned to ~100% with higher
  win rates still. **Falsified**; recorded as such.
- **Pilots branch**: the tokens pilot declines blocks — 191/217 on the
  anchor, 503/565 in the champion match — described as "the project's
  first agent to DECLINE blocks".

These are not in conflict, because **the agent is piloting a different
deck in each case**:

| | flagship | tokens pilot |
|---|---|---|
| agent's deck | BenchDimir (few creatures) | M3SelesnyaTokens (go-wide) |
| reason to decline a block | none — blockers are scarce and precious | keeping attackers back is the plan |
| observed | ~100% blocks | 88% / 89% |

The synthesis neither branch could reach alone: **7c's "agents block
~100% when asked" is a property of the Dimir seat, not of the policy
class.** Declining blocks emerges when the agent's *own deck* gives it a
reason to, and the flagship never gave it one — BenchDimir was 2/5 of
its rotation and every matrix cell is measured with the agent on
BenchDimir. My 4096 dip really was sampling noise; the real effect lives
in a seat the flagship does not measure.

**Actionable**: the robustness matrix should be run with the agent on
its *rotation* decks, not only BenchDimir, or it structurally cannot see
this class of behaviour.

---

## 3. Three independent discoveries of one performance bottleneck

| branch | observation | response |
|---|---|---|
| pilots-2 | conc3 = 0.715 g/s beats conc4 = 0.562 on 4 cores; "two policy servers plus the driver JVM oversubscribe 4 cores" | ran the lanes at conc3 |
| pilots-1 | "two servers with `--threads 4` on 4 cores oversubscribe torch on batch-1 matmuls" | pinned servers to 1 intra-op torch thread |
| flagship (P12) | measured it: lock wait 7.19 ms/call vs 5.75 ms held (55.6% waiting); inference itself 69% slower under concurrency | `RL_TORCH_THREADS=1` → **1.54x**, policy workload from 56% to 86% of the scripted ceiling |

Three sessions hit the same wall independently and two worked around it
before one diagnosed it. The diagnosis dominates both workarounds:
dropping to conc3 costs a worker; pinning torch threads keeps conc4
*and* fixes the root cause.

**Actionable, and free**: every lane should set `RL_TORCH_THREADS=1`.
This is worth more than the verified engine patch (1.04x at conc4) that
took a rebuild, a verify harness and 22,825 equivalence checks to land.

---

## 4. Everything saturates early, and always against a fixed population

| run | budget | plateau |
|---|---|---|
| flagship | 12288 | ~6144; mean matrix change −.013 then +.007 |
| sweep pilot | 4096 | anchor flat 2048 → 4096 ("the anchor saturates before the pilot does") |
| tokens pilot | 4096 | anchor .51 → .50 |
| 7b (prior) | 9216 | peak 6144, then drift |
| 7c (prior) | 3072 | peak 1536 |

Five runs, five plateaus, all between 1.5k and 6k episodes. The
flagship's diagnosis — **no opponent in the league adapts** — applies to
the pilots too: their pools are D0/D1/D1h + frozen champions + their own
snapshots. The only lane that ever had a continuously-adapting opponent
was 7b's self-play, and it drifted because nothing gated it.

This is the strongest cross-branch result in the pool: **the budget has
never been the binding constraint. The opponent population has.** Phase
10 spent 6,144 episodes past its own plateau; that is ~7 hours of the
15-hour run buying nothing measurable.

`rl/PHASE11-KICKOFF.md` is the design that follows (self-play fraction,
pool entry decoupled from crowning, PFSP by measured win rate,
champion-initialised exploiters).

---

## 5. E3: the channel is correct, and it is a distractor where it was tested

The E3 branch is the most careful experiment in the pool — three gates
against measured baselines, byte-reproducible extraction, per-channel
ablation with two nulls, and a matched control arm.

Its headline is a **negative result about its own feature**:

| condition (pooled, 2 seeds, 400g) | Δ win rate | ±95% |
|---|---|---|
| text block scrambled | **+.105** | .069 |
| text block zeroed | **+.117** | .069 |
| mechanical block scrambled | −.093 | .066 |

Zeroing 32 dims the net trained with makes it play **better**. The
channel is read (behaviour moves 6-9× the jitter band) but on a single
deck it is fitted noise.

Cross-referencing the other branches sharpens this rather than
contradicting it:

- 8b said card features degrade into **local identifiers** when training
  is single-deck. E3 is that result measured from the other side, on a
  channel built specifically to carry semantics.
- The E3 branch's own recommendation is to A/B it "where 8b said the
  mechanism lives — deck diversity from initialization (the Phase 10
  flagship)".
- **That run now exists** — but it is an E2 run. `p10_final.pt` has no
  text block to scramble, so the E3 branch's item 2 ("re-run this
  battery on the flagship's champion") is *not* directly executable. It
  requires matched E2/E3 arms **inside** the flagship design, which at
  current throughput is ~9h per arm, ~18h for one seed of each — and E3
  itself demonstrated that one seed decides nothing.

**This is the single most expensive open question in the pool**, and the
pooled evidence says do not run it yet: it needs the Phase 11 league
(so the arms do not both saturate at 6k against a frozen pool) and it
needs ≥3 seeds per arm to resolve an effect that moved .175 one way and
.110 the other between two seeds of the same arm.

---

## 6. Seeds: the convention exists because of results like these

| claim | seeds | status |
|---|---|---|
| E3 beats E2 at home (+.175, seed 0) | 1 | **did not replicate** (seed 1: +.020) |
| E3 loses on faeries (seed 0) | 1 | **reversed** on seed 1 |
| flagship Elo 1047, residual +.172 | 1 | provisional |
| sweep pilot +.185 lift | 1 | provisional, but large |
| tokens pilot +.015 lift | 1 | provisional, consistent with zero |
| text block is a distractor (+.105 pooled) | 2 | **replicated in both seeds** |
| torch oversubscription | 3 branches | **replicated independently** |

The two claims that replicate are the ones measured *within* a net
(ablation: same weights, same eval seeds, one input block corrupted) or
*across independent sessions*. Every claim that compares two separately
trained nets at 1-2 seeds is provisional. That is not a coincidence —
between-run variance is the dominant noise source in this project, and
within-run comparisons dodge it entirely.

**Design implication**: prefer within-net ablations and paired
comparisons over arm-vs-arm training runs wherever the question allows
it. They are cheaper *and* they replicate.

---

## 7. What the pool says to do next, in order

1. **`RL_TORCH_THREADS=1` everywhere** (free, 1.54x, three-branch
   evidence).
2. **Adopt `manaNoRecopy=on`** (verified safe, 1.28x on the sequential
   probes that make up every rating).
3. **Finish the pilot set** — 4 of 6 archetypes are unmeasured, and the
   two that exist disagree by an order of magnitude (+.185 vs +.015).
   Until they are done, the matrix's absolute numbers have a
   deck-dependent unknown correction. pilots-2 has the lane built and
   ran zero episodes; the infrastructure is not the blocker.
4. **Re-run the flagship's matrix with the agent on its rotation decks**,
   not only BenchDimir — otherwise the design's own central variable
   (agent-deck diversity) is invisible to its main instrument, and the
   blocking behaviour in §2 stays unmeasurable.
5. **Phase 11** (self-play fraction + decoupled pool entry) — the fix for
   the plateau that every lane in this pool hit.
6. **Only then** the E2-vs-E3 arms, inside Phase 11, ≥3 seeds.

Deliberately *not* on this list: further engine optimisation. §3 is the
argument — the last engine change cost a rebuild, a verify harness and
22,825 equivalence checks to buy 1.04x at conc4, while an environment
variable bought 1.54x.
