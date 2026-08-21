# Black branch, rung 3 — the agent does not assess threats

`CURRICULUM-LADDER.md` §5, first run. One arm: **v6** (`entattn`,
relations live), trained from scratch on `B3Open` for 512 episodes,
seed 0. The white branch asks "attack or block"; this branch asks *"of
everything on the battlefield, which one matters most"*.

---

## 0. Why this rung, and why the instrument had to be built first

`B3Open` is `B0Base` with four Gutter Skulk replaced by four **Fell**
(sorcery, destroy target creature). The deck is built around a power
census — 16 creatures at power 2, 8 at power 3, 4 at power 4, 8 at
power 5 — so "which one matters most" has an answer that is legal to
pick. It is fully vanilla plus one sorcery, so `CombatMath` stays in
scope (the constraint that rules out the white keyword rungs) and the
combat oracle still applies.

§5 designs the branch around a measurement and then records it as
missing: *"the action log records the spell but not the target it was
pointed at… Not built yet."* So `RLPlayer` now records, at every target
choice, the chosen creature's **power and combat status** plus the same
census over **everything it could legally have picked**. Both halves
matter: "killed a 5-power creature" says nothing without "and could
have killed these".

Forced targets never reach the policy — XMage assigns them — so they
are never counted. That is correct (a forced target is not a decision)
and it is why 200 games yield only ~139 recorded choices.

## 1. The headline: kills are worse than random on the thing that matters

Two censuses on the same frozen checkpoint, disjoint eval seeds, pooled:

| power | killed | expected if uniform over legal | cell χ² |
|---|---|---|---|
| 2 | 140 | 133.2 | 0.35 |
| 3 | 49 | 40.8 | 1.65 |
| 4 | 9 | 8.9 | 0.00 |
| **5** | **16** | **31.2** | **7.39** |

```
214 choices   chi2=9.39  df=3  p=0.024
kills on power>=4:  25/214 = 11.7%   available 18.7%   z=-2.63  p=0.008
mean power killed 2.53      mean power available 2.72
```

The deviation from uniform is significant, it is **almost entirely the
power-5 cell**, and it points the wrong way: the agent kills the
biggest creatures *less often than chance would*. It is not doing
threat assessment, and it is not merely ignoring the board either —
that would give a flat χ².

Each census on its own is not significant (p=0.13 and p=0.16); only
pooled do they cross 0.05. Two caveats hold that number down: the
choices within a game are correlated, so the p-value is optimistic, and
"uniform over the legal set" is one specific null — a policy could
deviate from it for reasons unrelated to threat.

## 2. The tempo hypothesis, and why this rung cannot test it

The obvious alternative story is that it kills for **tempo** — whatever
is attacking, blocking, or otherwise inconvenient now — rather than for
size. Measured the same way:

| tempo marker | chosen | available |
|---|---|---|
| attacking | 0 | **0** |
| blocking | 0 | **0** |
| tapped | 9/75 = 12.0% | 24/199 = 12.1% |

The first two rows are **structurally** zero: `Fell` is a sorcery, so it
is only ever cast in the agent's own main phase, where no opponent
creature is attacking or blocking. Tempo in the "kill the attacker"
sense is not available at this rung at all. The one proxy that does
exist — tapped, i.e. attacked last turn and cannot block now — tracks
availability to a tenth of a percent.

**But the behaviour shows up in the one window where it can.** In
`artifacts/v6/black/game_b3_seed931003.txt`:

```
t16  KILL  Cabal Evangel 2/2  [of 3: Cabal Evangel 2/2, Cabal Evangel 2/2, Cabal Evangel 2/2 tap]
t16  == my combat: 1 avail, 0 defenders          <- the kill cleared the blocker
t16  ATTACK Cabal Evangel 2/2
```

Three identical 2/2s, one of them tapped. Power cannot discriminate, and
it killed an **untapped** one — the one that could have blocked — and
then attacked into an empty board. That is a tempo kill. It is also n=1,
and the census says it is not a systematic policy.

**`B1Fast` is the deck that tests this properly**: Cruel Cut, the same
removal at instant speed, already built as the ladder's timing twin.
There the agent can kill during combat, `tgtChoseAtk`/`tgtChoseBlk`
stop being structurally zero, and the hypothesis becomes measurable
rather than anecdotal.

## 3. The battery, for completeness

25 games each, Wilson:

| | trained (512) |
|---|---|
| D0 | 0.400 [.234,.593] |
| D1 | 0.480 [.300,.665] |
| TWIN (`B3Twin`) | 0.640 [.445,.798] |
| block-optimal | 103/120 |
| attack-optimal | 95/122 |
| attacks declared | 143/156 |
| turns / game | 22.6, **0 stalls** |

Larger runs on the same checkpoint: 117-83 over 200 games (.585) and
.573 over 150, both stall-free. **This rung does not degenerate** — the
white rung 3 (`W3Sorc`) stalled 19 of 25 games with a 4.8% attack rate,
because removal that only hits *tapped* creatures makes attacking
suicidal. Fell has no such restriction, and the agent attacks 143 of
156 opportunities here.

`B3Twin` is new: the ladder builds a transfer arm for rung 0 only, so a
rung-3 run had none. It is generated by the ladder's own recipe (twin
shell, its ladder slot swapped for the same spell) so the transfer
probe moves card identities without also moving the rung.

## 4. What this does and does not say

- It says **v6 does not use power to choose removal targets**, on this
  deck, at this budget, on one seed.
- The collision gate (`ENCODER-V6-RESULT.md` §0) already showed the
  information reaches the network — power is in every entity row, and
  boards that were one vector under v5 are distinct under v6. So this
  is a statement about what the policy *learned to use*, not about what
  it can *see*.
- It says nothing about v5. There is no v5 arm on this branch; the
  target census is a within-net measurement, so a v5 arm would be
  readable on its own terms and is a ~50-minute matched run.
- It says nothing about whether killing the biggest creature is
  correct. The one-combat oracle does not model removal, so there is no
  ground truth here yet — only "chosen versus available".
