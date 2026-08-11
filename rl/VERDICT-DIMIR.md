# VERDICT — Task D (real-deck control mirror)

## The finding

**A real competitive deck adds no measurable learning difficulty for
E0+PPO at this opponent depth.** Median 256 episodes to confirmed
competence — identical to the burn mirror — despite 4x the decision
density, complex card mechanics (ninjutsu, transform, Rooms,
creature-lands), and a heuristic upgraded to contest the stack.

## What this changes

The Task B verdict said "move the measurement, not the architecture."
Task D moves it and gets the same answer, which sharpens the
conclusion: **opponent depth, not deck complexity, is the binding
constraint on measurement difficulty.** A stationary
heuristic — however competent per-decision — has fixed exploitable
gaps, and PPO finds them in a few hundred episodes regardless of the
card pool's sophistication.

Corollary: making the heuristic stronger buys nothing. The system has
proven RL-learnability end-to-end (Tasks A, B, D). The next question
is not "can it learn?" but "does the knowledge graph transfer?" — and
that is measured by the encoder A/B on held-out cards (TASKC-SPEC.md),
where identity memorization is impossible by construction.

## Fixed-deck ceiling, restated

On any fixed pool, E0's 16-bucket name-hash is a de-facto per-card
learned embedding; a graph encoder cannot beat it there. Task D's
256-episode result on a 22-card real deck is direct evidence the hash
suffices at this depth. The graph's only winnable game is
generalization — exactly what Task C isolates.

## Caveats carried

- Instrument v2 yardstick (3 counters added); not comparable to v1
  numbers. The instrument remains a documented floor — do not tune it
  further per-deck without versioning again.
- 4 seeds, not 5 (deviation documented in RESULTS-DIMIR.md).
- Sub-action fallbacks (Room doors, ward) are inherited heuristics,
  uncounted in the policy's action space — a real gap if a future deck
  hinges on them; fallback counts are reported per run to watch this.
- Same pin + patches as Task B.
