# How the literature handles combat — and why it mostly doesn't help us

Research note, August 2026. Prompted by "there have been papers for
Legends of Code and Magic and Hearthstone, which I think have this
combat system too, how do they handle it".

**Caveat on sourcing.** This session's egress policy blocks `arxiv.org`,
`eprints.whiterose.ac.uk` and `legendsofcodeandmagic.com`, so most of
what follows comes from search-engine summaries of those papers rather
than fetched primary text. Claims about *abstract-level* facts (action
space sizes, keyword semantics, method families) are reliable; claims
about implementation detail inside a paper should be re-checked against
the PDF from a machine that can reach it.

---

## 1. The premise is wrong, and that is the finding

**Neither LOCM nor Hearthstone has blocking.** Both are
*attacker-directed*: the attacking player picks the target, and the
defender never assigns anything.

- **Hearthstone**: "the attack action is a two-phase action where one
  first chooses a minion from their side of the board to attack with,
  and second, one chooses an opponent's hero or minion". Taunt
  *constrains* which targets are legal.
- **LOCM**: Guard means "enemy creatures must attack creatures with
  Guard first" — again a constraint on the attacker's target choice.

So in both games a combat action is a **pair** `(attacker, target)`.
The action space is `O(A x T)` — flat, enumerable, maskable. There is no
joint assignment, no simultaneity, and no combinatorial blowup.

MTG's declare-blockers step is a different object: the defender chooses
a **whole assignment at once**, `(A+1)^B` in the worst case, and it is
simultaneous, so there is no "already assigned" state in the rules.

**Consequence: the LOCM and Hearthstone literature cannot be borrowed
here, because those games do not have the problem.** Their hard problem
is a different one — Hearthstone's difficulty is *within-turn action
sequencing* ("a player may perform several actions in each turn and the
ordering of those actions is pivotal"), which is sequential, not
simultaneous.

---

## 2. What the MTG-specific work actually does

**Cowling, Ward & Powley (2012), "Ensemble Determinization in MCTS for
the Imperfect Information Card Game Magic: The Gathering"** — the
standard citation. Determinizes hidden information and runs MCTS over
ensembles, with pruning strategies to get more from each
determinization. I could not fetch the PDF, so I cannot say how their
move generator enumerates blocks. Worth reading properly before we
design ours.

**MTG-Causal-RL (Cunha, Mian, French & Liu, May 2026)** — a Gymnasium
benchmark on MTG with a 3,077-dim partial observation and a
**478-action masked discrete action space** across 16 categories, of
which "only 2 to 15 actions are typically legal" in any state.

That number is the tell. **478 total actions cannot encode joint block
assignments** — `(A+1)^B` blows past 478 at four attackers and four
blockers. So the benchmark must be doing what we do: per-blocker or
per-attacker actions, decided one at a time, with masking. The modern
MTG RL benchmark has the same decomposition we have, not a solution to
it.

**Forge** — the mature open-source MTG engine, whose AI is the closest
thing to a production answer. Its `AiBlockController.getBlockers`
mutates a `Combat` instance to assign blockers, and the described
algorithm "uses a `for` loop that looks at each attacking creature
individually and asks whether it should be blocked, **rather than
evaluating the whole combat situation at once like a human player
would**".

That is our bug, named as a known limitation by the people who wrote the
most-played MTG AI in existence. It is strong external evidence that we
did not invent this difficulty and that greedy per-unit assignment is
where implementations land by default.

---

## 3. The techniques that DO transfer

Since the card-game literature sidesteps the problem, the relevant
precedents are general.

**Autoregressive action heads (AlphaStar).** StarCraft II has ~10^26
legal actions per step; DeepMind factorises one action into a chain of
heads where "each subsequent action head conditions on all previous
ones, via an additive auto-regressive embedding going through all
heads". Sampling is sequential and each component conditions on the
ones already chosen.

This is exactly the factorisation our `selectBlockers` loop performs,
and it validates the direction: the conditioning is not a hack, it is
what makes a sequential decomposition of a joint decision *correct*.
Without it the model is a product of independent marginals — which is
literally the blocker-piling bug.

**Conditional Action Trees (Bamford & Ovalle, 2021).** Formalises this:
action selection as traversal of a chained sequence of components with
dependency levels, which "significantly reduces the action space by
decomposing it into multiple sub-spaces" and composes with invalid
action masking. This is the principled version of what we should build
for combat, and it says the decomposition should be a declared
structure rather than an accident of a `for` loop.

**Afterstate value functions.** The classical trick: evaluate the state
that results from the deterministic part of an action rather than the
action itself. There is one afterstate per state-action pair but many
possible next states, so learning on afterstates is both cheaper and
generalises better.

This is the strongest single recommendation for us. At rungs 0-3 combat
is a **deterministic function of the assignment** — no instants, no
replacement effects — so the afterstate is exactly computable. Giving
the policy "what the board looks like after this block" instead of
"block a 3/3 with a 2/4" converts a rule-inference problem into a
comparison problem.

---

## 4. What this says to do

1. **Stop looking for a card-game paper to copy.** LOCM and Hearthstone
   do not have blocking; the MTG RL benchmark decomposes exactly as we
   do; Forge's AI has our exact limitation and knows it.
2. **Keep the autoregressive decomposition** — AlphaStar is the
   precedent and the conditioning we added is what makes it valid.
   Formalise it as a conditional action tree rather than loop order.
3. **Move to afterstate features.** Simulate the combat outcome and
   feed that, rather than stat lines the net must do arithmetic on.
   Exactly computable at rungs 0-3.
4. **Read Cowling et al. properly** from a machine that can reach the
   PDF, specifically for their combat move generation — it is the one
   source likely to have confronted block enumeration directly.
5. **Note the open niche.** If MTG-Causal-RL really does flatten blocks
   into a 478-action masked space, then *joint* block assignment in a
   learned agent looks genuinely unaddressed. That is a publishable gap
   for the repo the project is heading toward, not just an
   implementation detail.

## Sources

- [Legends of Code and Magic (CodinGame)](https://github.com/CodinGame/LegendsOfCodeAndMagic)
- [Summarizing Strategy Card Game AI Competition](https://arxiv.org/abs/2305.11814)
- [Mastering Strategy Card Game (LOCM) via End-to-End Policy and Optimistic Smooth Fictitious Play](https://arxiv.org/abs/2303.04096)
- [RL agents playing Hearthstone: influence of state description](https://fse.studenttheses.ub.rug.nl/21526/)
- [Improving Hearthstone AI by Learning High-Level Rollout Policies](https://skatgame.net/mburo/ps/cig17-hsai.pdf)
- [Ensemble Determinization in MCTS for MTG (Cowling, Ward, Powley)](https://eprints.whiterose.ac.uk/id/eprint/75050/)
- [Causal RL for Complex Card Games: A Magic The Gathering Benchmark](https://arxiv.org/abs/2605.06066)
- [AlphaStar (DeepMind)](https://deepmind.google/blog/alphastar-mastering-the-real-time-strategy-game-starcraft-ii/)
- [Generalising Discrete Action Spaces with Conditional Action Trees](https://arxiv.org/abs/2104.07294)
- [Forge's AI blocking code](http://mtgrares.blogspot.com/2010/05/forges-awesome-ai.html)
