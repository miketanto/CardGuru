# The curriculum ladder — two branches, designed and built

**White branch (§1-4): combat.** Attack, block, trade math, then timing
and hidden information. 12 decks.

**Black branch (§5): threat assessment.** Of everything on the
battlefield, which one matters most — plus one rung on card advantage
with no board effect at all. 7 decks.

They share nothing but a design rule and are meant to run at the same
time (§6). All 19 decks are built, load clean, and have passed the stall
gate.

---


Every prior phase changed several things at once. 7c swapped whole
archetypes; 8b swapped twelve cards; Phase 10 varied the agent's deck,
the opponent pool and the gating rule in the same run. When a number
moved there was never one candidate cause.

This ladder is the opposite discipline. **Each rung is the previous
deck with one thing changed**, and in every rung below that one thing is
four cards out of sixty.

---

## 1. Why the combat branch is white, and why it is one card slot

A keyword rung has to swap vanilla creatures for creatures with the
**same mana cost and the same power/toughness** that differ by one
keyword — otherwise "flying" and "a bigger body" move together.

Scanning the pin for mono-colour creatures whose entire rules text is a
single keyword, and keeping only stat lines that *also* have ≥2 distinct
vanilla cards (so a control arm exists), gives:

| colour | flying | first str | vigilance | lifelink | deathtouch | trample | menace | haste |
|---|---|---|---|---|---|---|---|---|
| **W** | 4 | 1 | 2 | 5 | 0 | 1 | 0 | 0 |
| U | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B | 1 | 0 | 0 | 2 | 2 | 0 | 1 | 0 |
| R | 1 | 0 | 1 | 0 | 0 | 3 | 0 | 5 |
| G | 0 | 0 | 3 | 0 | 1 | 9 | 0 | 0 |

*(counts are stat lines, not cards)*

No colour covers everything. The decisive fact is finer than the totals:
**only white puts several keywords on one stat line.** White's 2cmc 2/2
slot has

```
6 vanilla    Fresh Volunteers, Glory Seeker, Knight Errant,
             Shrine Keeper, Silvercoat Lion, Traveling Philosopher
flying       Leonin Skyhunter, Silverbeak Griffin
first strike Head of Security
vigilance    Sun Sentinel, Alpine Watchdog, +4 more
lifelink     Mesa Unicorn, Ajani's Sunstriker, +4 more
```

Everywhere else the best line carries two keywords. So the entire
keyword ladder is **one slot of one deck**, which buys three things:

1. every keyword rung is the same 4-card diff, so the rungs are
   comparable **to each other**, not only to rung 0;
2. six vanilla cards is exactly enough for three disjoint roles — 2 for
   the base deck, 2 for the twin, 2 for the control arm;
3. one control run covers all four keyword rungs, because they all swap
   the same slot.

White also happens to hold the pair that makes the timing rung possible
(§3), so the trunk never changes colour.

---

## 2. Rung 0 — vanilla combat

`W0Base.dck`, 60 cards, mono-white, no instants, no keywords, tops at 4:

```
4  Elite Vanguard            [EMA:8]     1cmc 2/1
4  Glory Seeker              [W17:2]     2cmc 2/2
4  Silvercoat Lion           [M11:31]    2cmc 2/2   <- THE LADDER SLOT
4  Blade of the Sixth Pride  [FUT:19]    2cmc 3/1
4  Dromoka Warrior           [DTK:14]    2cmc 3/1
4  Knight of the Keep        [ELD:19]    3cmc 3/2
4  Regal Unicorn             [POR:22]    3cmc 2/3
4  Shu Elite Infantry        [PTK:22]    4cmc 3/3
4  Foot Soldiers             [POR:16]    4cmc 2/4
24 Plains                    [FDN:272]
```

The 3/1 · 2/3 · 2/2 triangle is the design: a 3/1 trades up into anything
but dies to a 1/1 chump, a 2/3 eats both a 3/1 and a 2/2 profitably, a
2/2 is the baseline. So "attack?" and "block with which?" have
board-dependent answers rather than card-dependent ones — which is
exactly the skill being probed. The curve skews power > toughness on
purpose: vanilla creatures with no removal and no evasion is the classic
board-stall configuration, and a stall runs the game to `stopTurn` and
turns terminal reward into a coin flip.

`W0Twin.dck` is the transfer test: **every** creature replaced by a
different card of identical cost and identical stat line. The two decks
are strategically indistinguishable — same curve, same combat math,
nothing different but names. A performance drop there has exactly one
available explanation: card-identity dependence. This is the sharpest
form of 8b's "features degrade into local identifiers" finding, which
was inferred from a 12-card swap where roles only approximately matched.

---

## 3. Rungs 1 to 5

Every rung below is `W0Base` with the four `Silvercoat Lion` replaced.
Nothing else moves.

| rung | deck | the four cards become | what it introduces |
|---|---|---|---|
| 1a | `W1Fly` | 4 Leonin Skyhunter `[MBS:11]` | **flying** — changes which blocks are *legal* |
| 1b | `W1Fst` | 4 Head of Security `[TRC:133]` | **first strike** — changes the *math* of a trade, not its legality |
| 1c | `W1Vig` | 4 Sun Sentinel `[RIX:26]` | **vigilance** — removes the attack-vs-hold-back tradeoff |
| 1d | `W1Lif` | 4 Mesa Unicorn `[J25:224]` | **lifelink** — changes the arithmetic of a race |
| — | `W1Ctrl` | 4 Shrine Keeper `[ANB:19]` | **control**: same swap, no keyword |
| 2 | `W2FlyLif` | 4 Leonin Skyhunter + 4 Mesa Unicorn *(both 2/2 blocks)* | **composition** — two keywords at once |
| — | `W2Ctrl` | 4 Shrine Keeper + 4 Traveling Philosopher | control for rung 2 |
| 3 | `W3Sorc` | 4 Take Vengeance `[GN2:13]` — *sorcery*, destroy target tapped creature | **removal**: creatures are not permanent, and tapping is a liability |
| 4 | `W4Inst` | 4 Swift Response `[J25:269]` — *instant*, **identical text and cost** | **timing** — and nothing else |
| 5 | `W5Trick` | 4 Aegis of the Heavens `[M19:1]` — instant, +1/+7 | **hidden information** — blocking now risks a trick |

### Rung 1's control is the point

`W1Ctrl` is why the keyword rungs mean anything. An agent trained on
`W1Fly` beating an agent trained on `W0Base` could be flying, or could
just be "trained on a deck whose 2/2s have different names." `W1Ctrl` is
that second story with the keyword removed. The residual is the keyword.
One control run covers all four keyword rungs — that is the payoff of
anchoring them on a single slot.

### Rung 4 is the cleanest experiment in the project

Scanning cheap single-line instants and sorceries for the same effect
printed at both speeds turns up a white pair at identical cost:

```
Take Vengeance  {1}{W}  SORCERY  destroy target tapped creature
Swift Response  {1}{W}  INSTANT  destroy target tapped creature
```

Same colour, same cost, same text, same count, same deck slot. Between
rung 3 and rung 4 the **only** variable in the universe is when the card
may be cast. A player that has learned to hold priority and act inside
the combat step gains from the swap; a player that only acts at sorcery
speed gains nothing. The measured delta is a direct read on whether the
policy learned timing, with no confound to argue about.

The effect was chosen as much as the timing: "destroy target tapped
creature" is *combat-conditional*. It only hits creatures that attacked,
which makes attacking a decision with a cost and makes rung 3 a lesson
rather than a card-advantage tax.

### Rung 5 changes the problem class

Once the opponent holds a trick, blocking stops being arithmetic. The
diagnostic here is not win rate — it is **block rate as a function of
the opponent's untapped mana**. A policy that ignores hidden information
blocks identically whether the opponent has `{1}{W}` open or is tapped
out. That is a *within-net* measurement on fixed weights, which is the
class of claim that `POOLED-ANALYSIS.md` §6 found actually replicates.

---

## 4. Where exact optimal play stops being cheap

This ordering is not arbitrary. It tracks a structural boundary:

| rungs | combat subgame | oracle |
|---|---|---|
| 0 – 2 | no instants at all; each combat is a finite perfect-information game | **minimax is tractable** — measure *distance from optimal*, not just win rate |
| 3 | sorcery removal; opponent still cannot respond during combat | perfect information preserved, oracle still works |
| 4 | instant removal; the opponent may be holding it | **imperfect information** — needs a belief state |
| 5 | tricks; the whole block decision is under uncertainty | fully imperfect information |

Rungs 0-3 admit ground truth. That is worth more than any win rate this
project has published: for the first time a number can say *how far from
optimal* the agent plays, rather than *who it beat*. Rung 4 is where the
problem class changes, and it is deliberately the rung where the deck
change is smallest.

---

## 5. The black branch — threat assessment, run in parallel

The white branch never asks *"of everything on the battlefield, which
one matters most?"* Its removal targets a **tapped** creature, which on
a real board is one or two attackers — the choice is close to forced.
That question is this branch, and the axis is **how wide the legal
target set is**. The pin supports it at a fixed cost, in one colour,
with one template:

| rung | deck | the four cards become | legal targets |
|---|---|---|---|
| 1 | `B1Narrow` | 4 Defeat `[DTK:97]` — sorcery, power ≤2 | near-forced |
| 2 | `B2Mid` | 4 Reave Soul `[J22:459]` — sorcery, power ≤3 | a real but small choice |
| 3 | `B3Open` | 4 Fell `[BLB:383]` — sorcery, **destroy target creature** | full threat assessment |
| — | `B1Fast` | 4 Cruel Cut `[ANB:47]` — **instant**, power ≤2 | Defeat's timing twin |
| 4 | `B4Card` | 4 Mind Knives `[POR:100]` — sorcery, opponent discards at random | *no board effect, no choice* |

Every one of those is `{1}{B}`, four copies, replacing the same four
`Gutter Skulk` in `B0Base`. Cost, colour, count, type and slot are held
constant; **only the card name changes**. That is tighter than the white
branch's keyword rungs, which at least alter a creature's body.

### The deck exists to make the thresholds bite

A targeting ladder is vacuous unless the board has creatures on both
sides of each threshold, so `B0Base` is built around its **power
census**:

```
power 2   16 creatures   <- everything Defeat can ever hit
power 3    8 creatures   <- Reave Soul adds these
power 4    4 creatures   <- only Fell reaches these
power 5    8 creatures   <- and these, which are the actual threats
```

So the rungs do not merely differ in wording — they differ in whether
the best target on a typical board is *legal at all*. At B1 the choice
is nearly made for you; at B3, picking a 2/1 over a 5/3 is an
unambiguous error.

### `B1Fast` is a free replication

`Cruel Cut` is `Defeat` at instant speed — identical restriction,
identical cost. So `B1Narrow → B1Fast` is the white branch's `W3 → W4`
timing experiment repeated in a second colour with a different effect,
at no extra design cost. Given that every claim in `POOLED-ANALYSIS.md`
comparing two separately-trained nets at one seed turned out
provisional, having the same question asked twice by two independent
decks is worth more than either asking alone.

### `B4Card` is a prediction, recorded before the run

`Mind Knives` costs the same, sits in the same slot, and does nothing to
the battlefield. The discard is random, so there is no target to choose
either. It is pure card advantage — value that never becomes visible.

Phase 4 recorded terminal-reward PPO failing to beat 1-ply search, and a
card whose worth never appears on the board is the hardest possible case
for a terminal signal. **Prediction, stated up front: this is the rung
the agent fails.** If it learns to cast Mind Knives at a sensible rate,
the prediction is wrong, and that is a more interesting result than any
win rate in this document.

### The measurement this branch makes possible

Win rate is the weak instrument here. The strong one is the
**distribution of chosen targets by power**: a policy doing threat
assessment concentrates its kills on high power; a policy ignoring the
board is uniform over the legal set. That is a chi-square on fixed
weights — a within-net measurement, the class §6 of
`POOLED-ANALYSIS.md` found actually replicates, and it needs no second
training run.

Everything except `B1Fast` is sorcery speed, so the opponent can never
respond during combat, the combat subgame stays perfect information, and
minimax still gives ground truth for *which creature should have died*.

**One instrumentation gap**: the action log records the spell but not
the target it was pointed at, so the target-by-power distribution needs
a small `EpisodeRunner` change before it can be read. Not built yet.

---

## 6. Running the two branches in parallel

They are independent by construction — different colours, different
skills, no shared card, no shared instrument. Two lanes, two policy
servers, two ports.

The one thing that must be got right is already known: three separate
branches independently hit torch thread oversubscription
(`POOLED-ANALYSIS.md` §3), and the fix is **`RL_TORCH_THREADS=1` on
every server**. Two servers left at the default will each grab four
intra-op threads on a four-core box and cost more than the second lane
gains.

At 12-17 games/sec per deck, a rung is minutes rather than hours, which
is what makes running both at once affordable — and what finally makes
the project's standing 5-seed convention, asserted since Phase 3 and
never once met, practical.

---

## 7. What red rung 0 is now for

`R0Base` / `R0Twin` / `R0Novel` (mono-red, already built and gated)
stay. They are not superseded — they become two extra probes:

- **colour transfer**: a W0-trained agent playing the red mirror. Same
  curve philosophy, same combat, different colour and different cards.
- **novel stat lines**: `R0Novel` uses P/T combinations that never
  appear in training. White cannot support this arm — its vanilla pool
  is 25 stat lines but shallow and lopsided (its only 5cmc line is 3/5,
  its only novel 2cmc lines have one card each, and the remainder are
  1/7 and 2/10 walls). Forcing a white novel deck would smuggle a
  *strategic* change — a wall deck — in beside the stat lines and defeat
  the point. So that probe stays in red, and this is stated as a
  limitation rather than papered over.

---

## 8. Honest accounting of what else changed

Rungs 3-5 replace four **creatures** with four **spells**, so the
creature count drops 36 → 32. That is a second change, and it cannot be
removed: there is no genuinely inert white card to pad with (life gain
and card draw both matter in a damage race, and extra lands change the
flood curve).

It is handled by holding it constant instead. All three spell decks have
32 creatures, so `W3 → W4` and `W4 → W5` are single-variable
comparisons, and those are the comparisons the rungs actually make. The
`W3 vs W0` comparison is the one carrying the extra confound, and the
baseline for it is a W0-trained agent playing the W3 mirror — which
measures how much the removal is worth to a player who never learned to
use it.

---

## 9. Gate results

Two things must hold before a deck is worth training on. It must
**load** — `.dck` silently loads zero cards on a bad `[SET:NUM]`, and a
0-card deck still "runs" — and it must **end**.

`DeckImporter` on all nineteen: **60 cards, no errors, no auto-fixes.**
(This also caught that the red decks' `[FDN:277]` Mountain was an
outdated printing being silently auto-replaced; fixed to `[FDN:278]`.)

Scripted D0 mirror, 40 games each, conc4:

```
deck         stalls  draws     turns  win_rate  games/sec
W0Base         0/40      0      13.2    0.4750     12.213
W0Twin         0/40      0      13.0    0.3500     14.515
W1Fly          0/40      0      12.5    0.4500     14.755
W1Fst          0/40      0      12.7    0.4250     15.959
W1Vig          0/40      0      13.3    0.4750     14.433
W1Lif          0/40      0      12.9    0.4000     15.940
W1Ctrl         0/40      0      13.2    0.4000     13.598
W2FlyLif       0/40      0      13.1    0.4500     14.450
W2Ctrl         0/40      0      13.1    0.5000     13.656
W3Sorc         0/40      0      13.6    0.5250     12.940
W4Inst         0/40      0      13.4    0.4750     13.512
W5Trick        0/40      0      12.9    0.4500     13.720

B0Base         0/40      0      12.8    0.4250     14.756
B0Twin         0/40      0      13.6    0.5250     14.308
B1Narrow       0/40      0      12.7    0.4500     17.253
B2Mid          0/40      0      12.7    0.4750     13.671
B3Open         0/40      0      13.2    0.4000     13.548
B1Fast         0/40      0      13.0    0.4500     15.183
B4Card         0/40      0      12.4    0.4750     16.195
```

Zero stalls anywhere, ~13 turns, and every mirror win rate is inside
±.155 of .5 (the 95% band at 40 games) — no deck has a structural seat
advantage, so measured differences will be skill rather than seat.

Loading a deck is not the same as the cards being reachable, so every
spell rung was checked separately by logging the agent's chosen actions:

```
W3Sorc    destroy target tapped creature.               chosen 3x
W4Inst    destroy target tapped creature.               chosen 5x
W5Trick   target creature gets +1/+7 until EOT.         chosen 5x
B1Narrow  destroy target creature with power 2 or less. chosen 3x
B2Mid     destroy target creature with power 3 or less. chosen 3x
B3Open    destroy target creature.                      chosen 2x
B1Fast    destroy target creature with power 2 or less. chosen 8x
B4Card    target opponent discards a card at random.    chosen 8x
```

Every spell is enumerable and castable — no rung is a silently vanilla
deck. The `B1Narrow` 3× vs `B1Fast` 8× gap is incidental but pointed:
the same card at instant speed gets more than twice the casting windows
from an identical random policy, so the timing variable is real at the
engine level before any agent has been trained on it.

**12-16 games/sec** against BenchDimir's ~2.5 on the same scripted
workload. That 5-6x comes from simpler cards alone, no engine work, and
it is what makes the ladder affordable: a rung-0 training run is
minutes, so the project's standing 5-seed convention — asserted since
Phase 3 and never once met — is finally practical.

---

## 10. Reproduction

```
python3 rl/wladder_decks.py          # white branch, 12 decks
python3 rl/bladder_decks.py          # black branch, 7 decks
bash    rl/wladder_gate.sh 40        # white: load + stall + seat balance
bash    rl/wladder_gate.sh 40 B0Base B0Twin B1Narrow B2Mid B3Open \
                                B1Fast B4Card          # black
```

Card pools come from the pin's own database: `rl/r0_scan.txt` (vanilla
creatures) and the keyword/spell scans in `/tmp/rl_p12/`, produced by
`VanillaScan` / `LadderScan` / `SpellScan`.
