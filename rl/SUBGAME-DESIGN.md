# Subgame design — what a subgame actually is

Companion to `rl/CAPABILITY-PLAN.md` (Revisions 1-2). Design only;
nothing here has been run. The engine is built in this container
(`.rl_ready`, pin `7554968c`) and a 4-game plumbing smoke passed at
1.465 games/s — n=4 including JVM and card-DB warmup, so that is a floor
on throughput and carries no information about play.

## The principle

**A subgame is a complete game of Magic, just a very short one.**

Not a position with a cutoff and a score. Both libraries are small, so
the game *terminates on its own* — someone dies, or someone draws from
an empty library and loses, which is a real rule, not a harness
invention. Because it terminates, the tree is finite and win/loss is
exact, so ground truth comes from full minimax over real engine states:
no evaluator, no teacher, no horizon score.

That is the whole point. Every previous combat instrument in this
project bottomed out in something arguable — CombatMath's one-combat
material evaluator, or agreement with CP7. This one bottoms out in the
rules.

## Anatomy

Extends the existing board format in `docs/scenario-spec.md` with four
fields:

```json
{
  "family": "T1.HOLD",
  "instance": 17,
  "players": {
    "A": {"life": 3, "battlefield": [{"card": "<vanilla 2/2>", "count": 2}],
          "hand": [], "library": {"filler": 5}},
    "B": {"life": 4, "battlefield": [{"card": "<vanilla 3/3>", "count": 1}],
          "hand": [], "library": {"filler": 5}}
  },
  "to_act": "A",
  "start": {"turn": 1, "phase": "PRECOMBAT_MAIN"},
  "criterion": "A_wins",
  "swap_group": "t1.vanilla.aXb"
}
```

- `library.filler` — N inert cards (basic lands with no play to make).
  They are the clock: the game cannot last beyond them.
- `criterion` — **binary**: `A_wins` or `A_survives`. Not a score.
- `swap_group` — ties the A / B / C variants of one instance together.

## The horizon must include the crack-back

A one-combat subgame teaches the wrong lesson: with no return swing,
attacking with everything is nearly always right, and a policy trained
on it learns exactly the habit that lost the project two phases. The
minimum closed loop is **my combat, then theirs** — that is where an
attack first has a cost. The library clock then carries the game out to
its real end rather than to a cutoff.

## Worked example — `T1.HOLD`

A at 3 life, two vanilla 2/2s, empty hand. B at 4 life, one vanilla 3/3
untapped, empty hand. Five filler cards each. A to act.

| A's line | what happens | result |
|---|---|---|
| attack with both | 3/3 blocks one and survives; 2 through, B to 2. B swings back into two tapped/dead bodies; A takes 3 | **A dead** |
| attack with one | it is blocked and dies for nothing | A behind |
| **hold both** | B attacks; A double-blocks; the 3/3 takes 4 and dies, A loses one body. A then attacks freely into an empty board | **A wins** |

Correct play is *pass on attack, then double-block*. Three things this
one instance does that no existing instrument does: it makes holding
back the right answer (so "attack with everything" scores zero), it
requires a **joint** block (the double-block is one decision, not two
independent ones), and its answer is decided by the rules, not by an
evaluator's opinion about a trade.

## Per-family validation gates

A family is not usable until all four pass. Pre-registered here so a
family cannot be rescued after seeing the agent's score.

1. **Horizon insensitivity.** Add two filler cards to both libraries; the
   optimal action must not change. If it does, the family is measuring
   the deck-out clock rather than the concept — cut it, do not tune it.
2. **Discrimination.** Random-legal play must be well below ceiling. A
   family everything passes measures nothing.
3. **Expressibility.** The optimal action must be in the candidate list
   the policy selects from — the §15/C coverage check, verified per
   instance rather than estimated. A family where it is not is reported
   as an action-space finding, and is not scored against the network.
4. **Solve cost.** Time to exact solution, recorded per family. Families
   that do not fit the budget get smaller boards, not a cheaper solver.

## Tier 1 families (vanilla bodies, decidable)

| family | the question | criterion |
|---|---|---|
| `T1.LETHAL` | an attack that wins now exists | `A_wins` |
| `T1.HOLD` | attacking kills you to the crack-back | `A_wins` |
| `T1.SURVIVE` | their swing kills you unless you block right | `A_survives` |
| `T1.BLOCKPICK` | several blocks survive, one keeps the body | `A_wins` |

`T1.LETHAL` exists because a real checkpoint failed exactly it —
declining a lethal attack into an empty board
(`rl/ATTACK-JOINT-RESULT.md`). It is the regression test of the ladder.

Deliberately excluded from tier 1: anything whose answer is "the better
trade". Value judgements need an evaluator, which is what this design
exists to avoid. If a valued family is ever needed, it goes in a
separate section labelled as evaluator-scored and is never pooled with
the decidable ones.

## The A / B / C swap

One instance, three card sets:

- **A** the cards the arm trained on;
- **B** a different card with the same stats and the same relevant
  mechanic — the "slightly different version";
- **C** same stats and cost, mechanic changed so the correct action
  **flips**.

Swaps are chosen by rule, not by hand-picked names: query the card DB
for same power/toughness/mana value/colour and the required keyword
(present for B, absent-or-different for C), then verify every pick loads
and behaves in the engine before it enters a set. Names go in the family
file once verified; none are guessed here.

**Tier 1's adaptation axis is weak by construction** and is reported that
way: swapping one vanilla 2/2 for another only tests name-invariance,
and there is no C variant because there is no mechanic to flip. Real
adaptation evidence starts at tier 2.

## Randomising everything the concept does not need

Within a family, life totals, filler counts, spare untapped lands, dead
cards in hand and irrelevant extra bodies are randomised per instance,
subject to the family's answer staying what it is. The concept is the
only invariant. Without this, a family becomes a single memorisable
board and the held-out split measures nothing.

## What is still unpriced

The solver. Exact minimax over engine state copies, with transposition
on a canonical board signature; branching is small for tier 1 (empty
hands mean priority windows are trivial and only combat branches), but
the per-node cost of an XMage state copy on this box is unmeasured.
That number sets how wide a subgame board can be, and it is the first
thing the build should produce.
