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

---

# One sample per rung (for review; none of these are validated)

Boards are written as mechanics, not card names — the swap rule picks
and engine-verifies the actual cards later. `lib` is the filler clock.
"Correct" below is my hand-derivation against a *best-playing* opponent;
the solver is what decides, and §"What hand-authoring got wrong" below
is the reason that distinction is not a formality.

## T1 — correct combat · `T1.HOLD`

A: 3 life, two 2/2 vanilla, lib 7 · B: 4 life, one 3/3 vanilla, lib 4 ·
A to act.

- attack with both → 3/3 blocks one and lives, 2 through; crack-back
  into tapped bodies kills A.
- **hold both → B is on the shorter clock and must come; A double-blocks,
  the 3/3 dies, A attacks out. A wins.**

The asymmetric library is load-bearing: without it both players sit and
the deck-out clock, not combat, decides. It survives gate 1 because
adding two cards to *both* libraries preserves the asymmetry.

*Measures:* that holding back can beat attacking, and that a double block
is one decision. *Cannot:* say anything about card identity — the bodies
are interchangeable.

## T2a — flying · `T2.FLY`

A: 3 life, one 2/2 flier + one 2/2 ground · B: 4 life, one 3/3 ground,
no reach · A to act.

- attack with both → the ground 2/2 is blocked and dies, B to 2, A is
  tapped out and dies to the crack-back.
- **attack with the flier only → B to 2, the ground 2/2 stays home as a
  blocker. B attacks or holds; A wins either way.**

*Measures:* evasion used as evasion — attack with the one that cannot be
blocked, keep the one that can. *Cannot:* separate "knows flying" from
"knows this card", which is what the B/C swap is for.
*C-control:* flier → same-stat ground body; the answer must change.

## T2b — first strike · `T2.FST`

A: 2 life, one 2/2 vanilla + one 3/3 vanilla, both untapped · B: attacks
with a 2/2 first striker · A to act (declare blockers).

- no block → A takes 2 and dies.
- block with the 2/2 → first strike kills it before it deals damage.
- **block with the 3/3 → it survives the 2 and kills the attacker.**

*Measures:* that first strike changes which blocker is correct without
changing which blocks are legal. *Cannot:* be passed by body-size
heuristics alone — "block with the biggest" happens to be right here, so
the family needs an instance where it is wrong before the rung counts.

## T2c — vigilance · `T2.VIG`

A: 3 life, three 2/2 **vigilance**, lib 3 · B: 6 life, one 3/3, lib 8 ·
A to act.

- **alpha strike → B blocks one, 4 through, and A's survivors are still
  untapped. A wins whether B attacks back or sits.**
- hold → A's short clock decks A out first.

*Measures:* the keyword that removes the attack-or-block tradeoff, on a
board where the same alpha without it is lethal to A. *Cannot:* be run
as a straight `W1Ctrl` twin — see below.

## T3 — combat trick · `T3.TRICK` (revealed-hand variant)

A: one 3/3 · B: one 2/2, two untapped lands, and a **revealed** +2/+2
instant in hand · A to act.

- attack → B pumps and eats the 3/3.
- **hold, or attack only when the trick cannot profit.**

*Measures:* playing around a known answer. *Cannot:* say anything about
hidden information — the hidden-hand variant is a separate rung scored
against a game value, never an optimality rate.

## T4 — removal · `T4.REMOVE`

A: 2 life, one 2/2, two untapped lands, an instant "destroy target
creature" in hand · B: attacks with a 4/4 · A to act.

- chump-block → A lives, loses the body, the 4/4 is still there.
- **cast the removal on the attacker → A keeps the body and the board.**

*Measures:* the project's sharpest known failure — a trained agent
offered instant-speed removal 5,504 times and cast it zero
(`LEVELSET.md` §3). This rung makes that decision the entire episode.

## T5 — flash · `T5.AMBUSH` (revealed-hand variant)

A: two attackers, a 2/2 and a 4/4 · B: untapped mana and a **revealed**
2/2 flash creature · A to act.

- attack with the 2/2 → it is ambushed and dies.
- **attack with the 4/4 → the ambush cannot profitably block it.**

*Measures:* anticipating a blocker that is not on the board yet.

## T6 — global effect · `T6.ANTHEM`

A: two 2/2, an anthem (+1/+1 to A's creatures) in hand and the mana for
it · B: two 3/3 · A to act.

- attack first, cast later → the 2/2s trade badly or bounce off.
- **cast the anthem precombat, then attack as 3/3s.**

*Measures:* a board-wide effect changing every combat number at once —
sequencing, not selection.

## T7 — activated ability · `T7.PUMP`

A: one 2/2 with "{1}: +1/+0" and two untapped lands · B: one 3/3
blocker · A to act.

- attack and pump precombat → the mana is spent before the information
  arrives.
- **attack, wait for blockers, then pump to win the fight.**

*Measures:* holding a decision until the information exists — the timing
axis every phase has found starved.

---

## What hand-authoring got wrong, and what that changes

Drafting these, the lifelink instance I intended as `T2.LIF` collapsed:
every board where lifelink looked decisive was one where the best
opponent simply *declines to attack* and wins the long game instead, and
the keyword stopped mattering. The vigilance instance has the mirror
problem — its `W1Ctrl`-style twin, same board minus the keyword, has no
correct action at all, because A loses down every line. A control
variant with no winning move is not a control.

Both failures are the same failure: **an instance is not a design, it is
a search result.** So instance creation is not authoring:

1. generate candidate boards from a family's parameter ranges;
2. solve each exactly, for the A, B and C card sets separately;
3. **keep only instances where the correct action is unique, where a
   stats-only heuristic gets it wrong, and where A and C have
   *different* correct actions;**
4. then run the four validation gates on what survives.

The samples above are therefore shapes to agree on, not the instances.
Anything hand-drawn that reaches a scoreboard without step 3 is a
position I talked myself into.
