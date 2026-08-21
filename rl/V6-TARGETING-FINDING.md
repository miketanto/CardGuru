# The agent points its own removal at its own board

Found while running v6 on three different decks. It is the clearest
behavioural defect this encoder work has turned up, and it is not an
encoder defect.

---

## 1. The observation

Three decks, three checkpoints, same behaviour. Transcript lines, with
the legal target set the policy was choosing from:

**B1Fast @1086** (`Cruel Cut`, destroy a creature with power ≤2), the
opponent has NO creatures on board:

```
t28  == my combat: life 6-5, creatures 3-0
t28  KILL Felhide Minotaur 2/3
       [of 3: Felhide Minotaur 2/3, Felhide Minotaur 2/3, Felhide Minotaur 2/3]
t28  Cruel Cut (destroy target creature with power 2 or less.)
```

**B1Fast @1086**, mid-combat, killing one of its own declared attackers:

```
t24  ATTACK Cabal Evangel 2/2 + Felhide Minotaur 2/3 + Felhide Minotaur 2/3
t24  KILL Cabal Evangel 2/2 atk tap
       [of 4: Cabal Evangel 2/2 atk tap, Felhide 2/3 atk tap,
              Felhide 2/3 atk tap, Felhide 2/3]
```

**BenchDimir @512**, two legal targets, both its own, opponent empty:

```
t23  KILL Elektra, Daughter of the Hand 3/3
       [of 2: Elektra, Daughter of the Hand 3/3, Spyglass Siren 1/1]
t23  Bitter Triumph (destroy target creature or planeswalker.)
```

It destroyed its own 3/3 and kept its own 1/1.

## 2. It is NOT an encoding gap, and v6 could not have fixed it

Ownership is in the observation twice:

- **The candidate** carries it explicitly —
  `StateEncoder.forTargetPermanent` sets `c[12] = controller == me`.
- **The v6 state** carries it again — every entity token has
  `mine`/`theirs` one-hot at idx 1–2, and relation type 4 (`controls`)
  links each player token to its permanents.

So the bit is there, in the action representation and in the state, and
the policy ignores it. v6 adds *vision*; vision was never the missing
thing. That also predicts v5 fails identically here, which is a testable
claim rather than a hedge — and it is the cheapest next experiment.

## 3. The likely cause is exposure, not representation

The decision is vanishingly rare. Measured target choices per 25 eval
games: **7** at B1Fast@574, **1** at B1Fast@1086, **13** on Dimir.
Attack decisions in the same games run to ~200. With terminal-only
reward discounted per consult (γ=0.997) over ~200 consults an episode, a
handful of target choices per hundred games is close to no gradient at
all, and the cost of killing your own 2/2 is a small material swing
buried in a win/loss signal many decisions later.

`CURRICULUM-LADDER.md` §5 predicts exactly this failure mode for
`B4Card` — "value that never becomes visible" to a terminal signal.
This is the same disease on a card whose value *is* visible, which
makes it the stronger version of that prediction.

## 4. What it invalidates

**The B3Open threat-assessment census pooled both controllers.** It
counted every legal creature target, the agent's own included, so
"kills power-5 less often than chance" was measured over the wrong
population. The number stands as reported - kill distribution
indistinguishable from uniform over the LEGAL set - but it cannot be
read as a statement about threat assessment until the census is split by
controller. That split is the first thing to build here.

**It plausibly explains the collapse in casting.** B1Fast cast removal
25 times per 25 games at 574 episodes and 3 times at 1086. That was read
as "it stopped using the card". A policy that mostly destroys its own
creatures when it casts removal *should* learn to stop casting removal;
that is the correct response to the reward it is actually getting.

## 5. A second defect, found by the same instrument

`entityUnknown` read **64289 over ten Dimir games** and looked like the
card feature table was missing the whole deck. Logging the names showed
otherwise:

```
Map Token
stack ability (When {this} enters, create a Map token.)
stack ability (Ninjutsu {1}{U}{B} ...)
stack ability (+1: You get an emblem with "Ninjas you control get +1/+1.")
...
```

A triggered ability's `getName()` is its rule text, so every trigger on
the stack counted as an unknown card AND lost the keyword bits of the
permanent that produced it. Fixed: stack entities now look their
features up by the SOURCE CARD. Genuine tokens (`Map Token`) still count
as unknown, which is what the counter is for. The vanilla decks read 0
because they have no triggers, which is why this hid until Dimir.

## 6. What to do next, in order

1. **Split the target census by controller** (`tgtChoseMine` /
   `tgtLegalMine`). One number - the share of kills aimed at its own
   board - decides how much of §4 needs re-reading.
2. **Run the same census on v5.** If it self-targets at the same rate,
   the failure is confirmed as reward-side and the encoder A/B has
   nothing to say about it.
3. Only then consider whether a rung whose spell is cast this rarely can
   teach anything under terminal-only reward.
