# Encoder A/B — conditioned autoregressive blocking, and v4 joint assignment

Two arms, two seeds each, rung 0 (`W0Base`), 1024 episodes, identical
budget / init procedure / concurrency / build. The **only** difference is
`-Drl.encoderV`, read at class-init so both arms run from one compiled
tree.

| | v1 | v2 |
|---|---|---|
| state dims | 24 | 32 |
| combat state | none | attackers declared, still-unblocked count, incoming power, **life after that damage**, free blockers |
| stack | depth only | top-of-stack: mine?, mana value, instant? |
| block candidate | attacker's P/T + identity | **+ blocker's own body**, blockers already on this attacker, power/toughness already committed, kills-attacker, loses-blocker, already-dead |
| blocker order | card **name** | body (toughness, power) |

Both are autoregressive in *structure* — the engine has always assigned
blockers one at a time. v1 lacked the **conditioning**: declaring a block
taps nothing and changes no life total or creature count, so blocker 2
received a byte-identical observation to blocker 1, and greedy argmax
returned the identical answer. v1 was a product of independent marginals
in all but name.

---

## Result

```
trained=768                                                    diff      z
  win rate    v2 .775 [.712,.827]   v1 .720 [.654,.778]      +.055    1.27
  block-opt   v2 .829 [.809,.847]   v1 .557 [.530,.584]      +.272    16.2

trained=1024
  win rate    v2 .745 [.680,.800]   v1 .680 [.612,.741]      +.065    1.44
  block-opt   v2 .730 [.707,.753]   v1 .589 [.563,.614]      +.142     8.2
```

Per seed at 768: v1 .720/.720 win and 53.9%/57.7% block; v2 .780/.770 and
82.7%/83.1%.

**The conditioned encoder blocks correctly ~83% of the time against ~56%.**
That is the finding. The win-rate difference is **not** a finding at
either checkpoint.

### The behavioural discontinuity

**v1 blocked 15,674 of 15,674 opportunities — across both seeds, every
checkpoint, without a single decline.** v2 declines between 0% and 39%
depending on checkpoint and seed. Every prior phase of this project
reported "agents block ~100% when asked" as a property of the policy
class; it is a property of the *encoder*.

---

## Why the block number is believable

**Replication is tight, which this project has never had.**
`POOLED-ANALYSIS.md` §6 catalogues claims that moved +.175 on one seed
and +.020 on the next, and an E3 faeries result that reversed outright.
The four cells at 768 do not move.

**The complexity confound is controlled.** Block-optimality correlates
**−0.60** with game length across all collected rows — longer games mean
bigger boards and harder assignments, so a shorter-game arm scores higher
for free. Mean turns at 768: 28.5 (v1) vs 28.1 (v2). At 1024: 26.7 vs
26.0. The gap is not that.

**The metric's bias runs against v2.** `CombatMath` scores one combat
deep with no notion of tempo, so a decline made to keep a creature for
offence is recorded as an error — and v2 is the only arm that ever
declines. It wins by 27 points while being the only arm the metric can
penalise.

---

## Four things this does not say

**It does not say v2 wins more.** +.055 and +.065 at z≈1.3 are inside
noise at 200 games per arm.

**It does not say blocking is solved.** Constructed positions
(`rl/position_probe.py`) show v2 handles one attacker needing a double
block correctly, and **declines everything** when two attackers each need
one — taking 5 damage for nothing. Adding a spare blocker does not fix
it, so this is commitment, not scarcity: blocking a 3/3 with one 2/2 is
bad and only becomes good if a second joins, so no blocker goes first.
Autoregressive conditioning is on the **past**; that failure needs joint
assignment.

**It does not say the metric tracks strength.** Between 768 and 1024, v2
seed 0's block-optimality fell 82.7% → 65.0% while its win rate rose.
A one-combat reference cannot referee decisions that pay off next turn.
Block-optimality is retired as a primary metric; the replacement is the
k-turn rollout the black branch needs anyway.

**Both numbers are floors.** The v2 arm carries a controller-blind combat
channel — `s[24..28]` counts *all* combat groups, so during the agent's
own turn its own attackers register as incoming damage and `s[27]` reads
"my life after my own attack". v2 trained under an explicit anti-attack
signal. Fix pending as a v3 arm against this same v1 control.

### CP7, and why it says nothing

10 games per seed: v2 .900/.500, v1 .600/.500. Pooled, v2 .700
[.481,.857] against v1 .550 [.344,.741] on 20 games each - overlapping
almost entirely. The same arm produced .900 and .500 on consecutive
seeds, which is exactly what a +-.31 band predicts. This column is
decorative at n=10 and was known to be when it was cut from 50; settling
it needs a one-off 200-game probe, not a row in every seed.

---

## What it changes about the plan

The solver-blocks bound (`.705 → .815`, +.11) says perfect blocking is
worth about a tenth of a win rate. v2 may have taken half of that. So
further *blocking-only* work is competing for ~+.05.

That reprioritises the remaining options:

- **Joint assignment** rises: it is the only option that touches
  commitment at all, it covers attacking as well as blocking (attacks
  remain fully unconditioned in both arms), and A1 de-risks it by showing
  the policy exploits structure when given it.
- **Afterstate features** rise and get cheaper: `c[20]`/`c[21]` are baby
  afterstate features and they are part of what produced +.272.
  `CombatMath` is written. Joint assignment *needs* them — scoring whole
  assignments from raw stat lines is the arithmetic this experiment
  showed is hard.
- **Solver-DAgger falls.** v2 got +.272 without touching the learning
  signal, so credit assignment was not the binding constraint here —
  observability was. And DAgger against a myopic teacher would train out
  the strategic declines v2 discovered on its own.

---

## v4: joint assignment (512 episodes, 1 seed)

The A/B's conclusion was that conditioning fixes over-piling and
**provably cannot** fix under-committing. v4 removes the sequential
decomposition instead of patching it: one decision per combat over
complete assignments, Pareto-filtered, each described by its simulated
outcome rather than by cards.

```
trained   D0     block-optimal     gap    turns
  256    .550    91.4% (550/602)   416    19.2
  512    .850    93.0% (635/683)   349    23.6
```

`.850` at 512 episodes exceeds every checkpoint of every other arm — v2's
best was .790 at 1024, v1's .730 at 512. Block-optimality 93.0% against
v2's best 83.1% and v1's 66.1%, and the score gap is 349 where v1 ran
2,000–6,000.

### The constructed positions, which are the clean part

| position | v2 | v4 |
|---|---|---|
| one attacker needing a double | 12 = 12 ✅ | 12 = 12 ✅ |
| **two attackers, three blockers** | **0 vs 12 ❌** | **12 = 12 ✅** |
| two attackers, four blockers | 12 vs 19 ❌ | **19 = 19 ✅** |
| control at 20 life | 12 = 12 ✅ | 12 = 12 ✅ |

v2 declined all three blockers in the two-attacker position and took 5
damage for nothing — blocking a 3/3 with one 2/2 is bad and only becomes
good if a second joins, so nobody went first. v4 never faces that
question. With four blockers it splits them two and two and kills both
attackers, which is an allocation rather than a threshold rule.

### What is confounded, and what is not

v4 moves **three** things at once: joint assignment, the v3 controller
fix, and credit assignment (one action per combat instead of B actions
sharing one terminal reward). The win rate cannot be attributed among
those from one seed.

The constructed positions can. RANK is a defensive position, so the
controller fix is irrelevant to it, and a position probe involves no
credit assignment at all. **"Commitment is fixed" is clean; "v4 wins
more" is not.**

### Still broken

Attacking. The attack probe holds all three creatures back against a
single blocker, exactly as v2 did — `selectAttackers` is still a product
of independent per-creature marginals, because joint assignment was
implemented for blocks only.

### Replication, and what a replay shows that the counters hide

The container was recycled and took `/tmp` with it, so the run above was
repeated from scratch on the same seed and budget (this time with the
battery only at 0 and 512, so no mid-run server restart):

```
              D0     D1     TWIN    block-optimal      gap   turns
first run    .850     -       -     93.0% (635/683)    349   23.6
replication  .940   .920    .860    95.3% (702/737)    236   31.0
untrained    .000     -       -           -              -   11.0
```

100 games a row, one seed each. This is a replication that came out high,
**not** an improvement — do not report the delta as one.

The replay (`game_v4_ck512_vs_D0_seed6001.txt`, won on t27 at 17 life)
carries two new lines per combat: `[joint]` with the candidate count and
`[audit]` with the solver's assignment beside the policy's. Reading it
turns up two things the block-optimality counter cannot show.

**`MATCH` means scored the same, not chose the same.** At t10 the policy
throws a 3/1 and two 2/2s at an Elite Vanguard 2/1; the solver uses the
3/1 alone. Both score 1, because the 2/1 has 2 damage and kills exactly
one blocker either way — and because `defenderScore` has **no term for
blockers used**. So the policy is still over-piling; piling is merely
free at rung 0. `forAssignment` passes `c[12] = blockers used` as a
feature and nothing in the reward or the reference pushes against it.
This is a live gap, not a curiosity: at rung 5 (`W5Trick`, Aegis of the
Heavens, +1/+7 instant) over-committing to a 2/1 is how three creatures
die to one card, and there is currently no gradient away from it. Same
shape at t16, a triple block on a 2/3.

**Some combats have no decision in them.** t22 enumerated 12 distinct
outcomes and the Pareto filter left **1**. The MATCH there belongs to the
filter, not the net. Five of the six combats in this game had >1
candidate; `blockOptimal/blockCombats` does not distinguish, so treat it
as an upper bound on how much of the credit is the policy's.

The attacking failure is on full display in the same game: twelve
consecutive turns of `hold` at 20-20 life, including turns at 4-1 and 3-1
on board, before it alpha-strikes on t25.

## Reproduction

```
bash rl/rung0_lane.sh W0Base W0Twin 1024 <seed>   # R0_ENCODER_V=1|2|3|4
python3 rl/position_probe.py --port <p> [--validate] [--v4]
bash rl/rung0_replay.sh <ckpt> <encV> W0Base heuristic <seed> <out>
```

Artifacts under `rl/artifacts/rung0/W0Base/`. **Commit checkpoints you
care about** — `rung0_autosync.sh` syncs only the white-branch seeds, and
the first v4 checkpoint was lost to a container restart, costing a full
rebuild and retrain to answer "show me a replay".
