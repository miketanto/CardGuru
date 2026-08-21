# The agent casts removal at boards with nothing to kill

Found while running v6 on three decks. The visible symptom is that it
destroys its own creatures; the cause is not what the first version of
this document said it was, and §2 records the correction.

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

## 2. CORRECTION: it is a cast-decision failure, not a targeting one

The first version of this document claimed the policy ignores the
ownership bit. **That was wrong, and the measurement refutes it.**

Every window quoted in §1 had NO legal enemy target - the opponent's
board was empty, or their creatures were outside the spell's power
restriction. The target choice was forced. Measured on BenchDimir @1024,
25 eval games, with the census split by controller:

| | count |
|---|---|
| target decisions | 22 |
| ...with ZERO enemy creatures legally targetable | **11 (50%)** |
| ...with at least one enemy target available | 11 |
| of those, an ENEMY creature was chosen | **10 of 11 (91%)** |

So given something worth killing, it kills the right side nine times in
ten. The ownership bit is read. What fails is the decision to cast at
all: half of all removal casts happen into a board with no enemy target,
and once the spell is on the stack the engine demands a legal target, so
one of its own creatures dies.

**And there the encoding really is short.** Ownership is encoded twice -
`forTargetPermanent` sets `c[12] = controller == me`, and every v6
entity token carries `mine`/`theirs` plus the `controls` relation. But
the CAST candidate is this, in full:

```java
public static float[] forCard(int type, Card card, Game game) {
    c[6]  = card.getManaValue() / 6f;
    c[7..9] = power / toughness / is-creature;
    c[10] = card.isInstant(game);
    c[11] = card.isSorcery(game);
    identity(c, card.getName());
```

Mana value, body, type, name. **Nothing about whether the spell has a
legal target worth having.** The net can only get there by learning a
conjunction between the card's identity and the board state, from a
handful of casts per hundred games. v6 does not help: it widens the
state, and the missing feature is on the action.

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

1. ~~Split the target census by controller.~~ **Done** -
   `tgtChoseOpp` / `tgtLegalOpp` / `tgtNoOppAvail`, and the answer is
   in §2: the targeting is fine, the casting is not. §4's first item
   still stands: B3Open's power census was measured over the pooled
   population and needs re-running with the split before it can be read
   as threat assessment.
2. **Run the same census on v5.** If it self-targets at the same rate,
   the failure is confirmed as reward-side and the encoder A/B has
   nothing to say about it.
3. Only then consider whether a rung whose spell is cast this rarely can
   teach anything under terminal-only reward.

## 7. The Dimir run that produced the number

BenchDimir, v6, 512 -> 1024 episodes (the split was added before the
second half, so the 1024 battery carries it).

| | @512 | @1024 |
|---|---|---|
| D0 (10 games) | .200 [.057,.510] | .400 [.168,.687] |
| D1 | .000 | .200 |
| turns / game | 22.6 | 17.5 |
| actions / episode | 15.7 | 21.0 |
| instant casts (10 games) | 15 | 13 |
| ...cast inside a combat step | 0 | 0 |

The win rate doubled and means nothing at ten games - the intervals
overlap almost entirely. Two things are worth keeping: the agent is
closing games faster (22.6 -> 17.5 turns), and it has never once cast an
instant during a combat step, across every checkpoint measured on two
different instant-speed decks.

READ THE AUDIT COLUMNS NOWHERE. BenchDimir has 7 fliers and 3
deathtouch, and CombatMath models neither, so this deck's BLOCKOPT and
ATKOPT are computed against a reference that mis-simulates its own
creatures. They are excluded from this table deliberately.
