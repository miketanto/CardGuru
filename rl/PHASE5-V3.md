# Phase 5 — instrument v3: flash/ninjutsu awareness (user-directed)

## Why

Mid-Phase 5 review of a sample Dimir mirror transcript surfaced a
structural blindness in the v2 instrument line: **flash-speed permanent
deployment never happened.** BenchDimir's core gameplan is built on it —
16 of 60 cards (4x Kaito ninjutsu, 4x Floodpits Drowner, 3x The Wondrous
Wasp, 3x Enduring Curiosity, 2x Nowhere to Run). Three stacked causes:

1. The REACTIVE yield predicate (a Phase 2 throughput optimization)
   only stayed open when a literal INSTANT was in hand — the
   declare-blockers / end-step windows where flash lines live were
   auto-passed unseen with (say) only Kaito in hand.
2. HeuristicPlayer's off-turn action surface only recognized
   counterspells and end-step instants; its card filter (`cardOf`)
   dropped every non-SpellAbility candidate, so NinjutsuAbility could
   never be chosen. Flash permanents were castable at sorcery speed
   only.
3. RLPlayer/TeacherLogPlayer encoded non-cast candidates (ninjutsu,
   creature-land activations) with a null card - featureless vectors
   the policy could not distinguish.

## The v3 change (both instruments + agent wrapper, versioned)

- REACTIVE predicate: hand holds instant OR flash card OR ninjutsu card
  (HeuristicPlayer + RLPlayer).
- HeuristicPlayer v3: casts the highest-MV flash card alongside
  instants at the opponent's end step; activates a playable ninjutsu at
  its own declare-blockers step.
- Candidate encoding: source card resolved for EVERY priority
  candidate. Dims unchanged (still E0, sdim 24 / cdim 38).
- SearchPlayer/SearchPlayerIP unchanged: search now simply sees the
  richer windows and inherits the richer D0 fallback.

Same-seed verification (Dimir mirror, seed 950004): the v2 transcript
hard-cast every Kaito; the v3 transcript shows the textbook line - T8
declare-blockers, unblocked Wasp returned to hand, Kaito enters tapped
and attacking via ninjutsu, +1 activated post-combat.

**Scope of comparability break**: an ability audit of all 7 decks shows
BenchDimir is the ONLY deck (pool or holdout) containing flash/ninjutsu
cards. Burn/control/midrange behavior is bit-identical under v2/v3;
only Dimir-involving numbers moved. All v2 numbers remain valid as v2
numbers; Phase 5 continues on v3.

## v3 recalibration (500g each, BenchDimir mirror, seed block 960000)

| match | v2 | **v3** |
|---|---|---|
| D1 vs D0 | .776 [.74,.81] | **.614 [.57,.66]** |
| D1ip (K=4) vs D1 | .482 | **.484** |

Two findings:

1. **The fix strengthened the floor more than the searcher.** D0's new
   deterministic lines (ninjutsu swap, end-step flash) are worth far
   more than what 1-ply search adds on top of them: the D0->D1 rung
   compressed from +27.6 to +11.4 points. The ladder still has two
   rungs, but the step is half the size - every Phase 5 comparison now
   uses .614 as the search-parity anchor on Dimir.
2. **C0's verdict survives v3.** Honest determinized search remains
   statistically even with perfect-info search (.484 vs .482 under v2).
   D1 stays licensed as the imitation teacher.

## v3 pipeline redo (C1/C2a)

- Teacher dataset regenerated under v3: 1,000 teacher-vs-D1 episodes,
  4-deck pool, seeds 13000000+, 191,181 examples, 0 unmatched labels,
  teacher mirror win rate .504.
- v2 C2a partials (recorded before stopping the lanes at the version
  bump): BC-init PPO reached ~.45-.54 vs D1v2 by 1,024-1,280 episodes
  (rolling 100g), shaped arm .49-.54 vs unshaped .45-.50 - a small,
  not-yet-conclusive shaping edge. These runs answered feasibility
  (fine-tuning escapes the BC plateau) and are superseded for headline
  purposes by the v3 arms.
- v3 student + C2a results: see PHASE5-C1.md / PHASE5-C2A.md v3
  sections as they land.
