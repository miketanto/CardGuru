# Attacking as a joint decision — the instrument, the fix, and what
# neither of them says

Follows `rl/HANDOFF-ATTACK-JOINT.md`, which follows
`rl/ENCODER-AB-RESULT.md`. The one-line version of those: blocking was
one independent decision per blocker with no sight of the others, it was
fixed by replacing that with one decision per combat over complete
assignments, and `selectAttackers` still carried the original bug.

**What is settled here is the INSTRUMENT and the MECHANISM. Nothing here
is a policy result.** There is no trained v5 net, by decision, so no
number below says the fix makes the agent play better. What the numbers
do say is what the pre-fix agent actually does on attacks — which nobody
could measure before, because the measurement did not exist.

---

## 0. What was built, and what was deliberately not

Built:

- `auditAttacks` — the attack-side twin of `auditBlocks`. There was no
  way to say whether an attack was good; the entire evidence that
  attacking was broken was a human reading twelve consecutive `hold`
  lines out of one replay.
- `CombatMath.bestAttack` / `attackerScore` / `attackerScoreCA` — attack
  subsets valued under a best-replying defender (minimax one ply, §3).
- `RLPlayer.jointAttacks`, gated on encoder **v5** — one decision per
  combat over attack subsets, described by their simulated consequence.
- Constructed attack positions and a policy-free coverage check
  (`position_probe.py --coverage`).

Deliberately not:

- **No training.** A v4 checkpoint loads under v5 (dims are unchanged at
  32/94) but the `T_ATTACK` candidate changed MEANING from "this card
  attacks" to "this subset produces this outcome", so a v4-trained net
  driven through the v5 path is out of distribution. Every v5 policy
  number here is labelled accordingly and carries no claim. §6.
- **No change to `defenderScore`'s missing blockers-used term.** The
  handoff flags it; changing it re-baselines every block-optimality
  number ever reported and belongs to whoever decides to do that
  deliberately.
- **`bestDeduped` is not wired into `best()`**, which `auditBlocks` and
  `rl.solverBlocks` use, for the same reason. §4b.

---

## 1. The baseline: what the pre-fix agent actually does

`v4_ck512`, 100 games vs D0 on W0Base, seed 900512 — the same seed as
the committed `trained=512` battery row, so these are the same 100 games
that produced the published `.940`. Sequential. Wilson 95%.

```
attack rate            1362/4485   .304 [.290,.317]
attack-optimality       786/1264   .622 [.595,.648]
  ...where a choice existed  786/1264   (identical — see below)
attack-optimality (CA)  799/1264   .632 [.605,.658]

score gap (myopic)      3790 over 1264 combats
missed lethal              1       (own category, never a gap)
errors UNDER / OVER      277 / 197
truncated subsets/replies  1 / 0
```

**The agent sends 30% of the creatures that could legally attack, and
matches the reference on 62% of combats.** UNDER outruns OVER 277:197 —
it under-attacks more often than it over-attacks, and it does so against
a reference that is structurally biased TOWARD attacking (§7). Three
errors sent the right NUMBER of creatures and the wrong ones.

### Attacks always have a choice, and blocks do not

`attackCombatsWithChoice` is **1264 of 1264**. Not one attack position in
100 games had a single distinct outcome.

This matters because of the §2 caveat in the handoff: at t22 of the v4
replay the Pareto filter left the block policy ONE candidate, so the
MATCH belonged to the filter rather than the net, and
`blockOptimal/blockCombats` is an upper bound for that reason. The attack
side has no such collapse in these games. `attackOptimal/attackCombats`
is not inflated that way — which is a property of these positions, not a
guarantee, so the counter stays and is reported.

### The constructed positions, which are the clean part

`v4_ck512` through its own per-creature attack path — **in
distribution**, so this one is interpretable:

| position | reference | v4 policy |
|---|---|---|
| COMMIT: three 2/2s into one 3/1 | attack all three (+8) | **holds all three** ❌ |
| ALPHA33: three 2/2s into one 3/3 | hold (0) | holds all three ✓ |
| HOLD: one 2/2 into two 3/3s | hold | holds ✓ |
| **LETHAL: three 2/2s, they are at 4, no untapped blocker** | attack (game over) | **holds all three** ❌ |

**It declines a lethal attack against an empty board.** That is the
finding, and it is stronger than the handoff's diagnosis. The handoff
describes a COMMITMENT failure — nobody goes first because the first
attacker alone is bad. LETHAL needs no coordination at all: there is no
blocker, every creature is individually and unconditionally profitable,
and a per-creature marginal should take it. The pre-fix policy holds
anyway.

So on these positions the failure is not only that the decomposition
cannot express joint commitment; it is that this checkpoint's
per-creature attack marginal is near-constant "hold". That is the mirror
image of v1 blocking, which declined 0 of 15,674 opportunities.

**What that table cannot support.** Four constructed positions and one
checkpoint. And in real games the same checkpoint attacks at rate .304,
so "near-constant hold" is a property of these positions, not a global
property of the policy — the constructed board sits somewhere the net
holds, and the real-game rate says it does not hold everywhere. The two
observations are consistent and neither generalises the other.

---

## 2. The instrument

`auditAttacks`, `-Drl.attackAudit`, read AFTER the policy commits so it
never influences a decision. Same discipline as `auditBlocks`:

- **excluded**: positions with no available attacker. Counting those is
  the mistake that once inflated an untrained net to 98.4%
  block-optimality by scoring positions it had no creatures in.
- **split out**: `attackCombatsWithChoice` (>1 distinct OUTCOME, not >1
  distinct subset — two subsets that resolve identically are one
  decision).
- **truncation is two counters**: `attackTruncated` (subset enumeration
  hit `rl.attackCap`) and `attackReplyTruncated` (an inner defender reply
  hit `rl.attackReplyCap`). Different searches; either can be cut.
- **UNDER / OVER**: the direction of the error. Without it an agent that
  alpha-strikes every turn posts a high optimality against a reference
  that likes attacking, and the metric would call that success.
- **missed lethal** is its own category and never enters the score gap,
  because `attackerScore`'s lethal sentinel is `MAX_VALUE/2` and
  subtracting a sentinel into a running total is how `blockScoreGap`
  once read 1073743876.

**Cost: the audit is 76% of wall clock** — 584 s of a 763 s 100-game run,
because it runs a full minimax attack search per combat on top of any the
policy ran. It is therefore EVAL-ONLY in `rung0_lane.sh`; putting it in
the shared flags (as this branch first did) would have quadrupled every
training chunk for a number nothing reads during training.

---

## 3. The defence model: minimax one ply, and what it cost

Handoff option 1. For each attack subset, the defender replies with
`CombatMath.bestDeduped` under `defenderScore` — the same evaluator the
block side already uses, read from the other seat.

**Measured cost of the POLICY's own search** (audit off, 20 games, so the
instrument does not swamp it): **58 ms total, 0.10 ms per combat, 83
`resolve()` calls per combat.** Per turn, v5 ran marginally FASTER than
v4 (16.9 vs 15.4 turns/s); its lower games/sec is longer games, not
slower decisions.

The fallback rule was pre-registered before measuring — drop to option 3
(featurise without resolving) if the search exceeded 15% of wall clock.
It came in at **0.09%**, so minimax one ply stands.

**The caveat that number needs.** Cost scales with board width, and those
20 games stalled with small boards (A≈3). The audit's identical search on
the v4 baseline's 31-turn games, where boards reached A=12, cost 1.27 s
per combat — four orders of magnitude more. So the honest statement is:
the search is free on the boards these games reach, and `rl.attackCap` /
`rl.attackReplyCap` / `rl.attackMaxCreatures` exist because it is not
free in general. `attackCreaturesCapped` fired on 1 combat in 100 games.

Three limitations of the reference, all in the `CombatMath` header:

1. it inherits `defenderScore`, including the missing blockers-used term;
2. it assumes a perfect one-combat defender, which D0 is not — against a
   weaker defender the reference UNDERSTATES how good an attack is;
3. it is one combat deep. §7.

---

## 4. Two things found while building it

### 4a. `resolve()` broke damage ties by list order — and the search exploited it

`resolve()` assigns a blocked attacker's damage "smallest toughness
first" with a **stable** sort, so among equally-fragile blockers the one
earliest in the caller's list died. `RLPlayer` hands blockers over sorted
by `(toughness, power)`, so the CHEAPEST equal-toughness body died and
the defender collected the friendliest reading of a choice that is not
theirs to make — the attacking player assigns combat damage, and facing a
2/1 and a 3/1 they kill the 3/1.

The brute-force search then exploited it. Concretely, on a board of
`atk 3/3, 1/3` against `2/1, 3/1, 2/3, 3/1, 2/1` at 11 life, brute force
returned score 20 for an assignment that scores 17 once two identical
2/1s are swapped. The optimum was an artifact of list order.

This contradicts the module's own stated contract ("the defender must
assume the WORST ... assuming anything friendlier would make the
reference optimistic and the measurement useless"). Fixed: toughness
ascending, then value DESCENDING. Killing as many as possible stays
primary and unchanged; the tie-break can only make the reference harder
to match, never easier.

**The re-baseline, measured rather than argued.**
`-Drl.legacyTieBreak=true` restores the old behaviour, so the same
checkpoint and seed can be read both ways:

| | legacy | fixed |
|---|---|---|
| block-optimality | 702/737 = .953 [.935,.966] | 702/738 = .951 [.933,.965] |
| block score gap | 236 | 247 |
| blocks declared | 1642/2057 | 1578/2055 |
| attack-optimality | 791/1262 = .627 [.600,.653] | 786/1264 = .622 [.595,.648] |
| attack rate | 1353/4486 = .302 | 1362/4485 = .304 |
| win rate / turns | .940 / 31.0 | .940 / 31.1 |

**The legacy column reproduces the committed lane row exactly** —
`blocks=1642/2057, BLOCKOPT=702/737, gap=236, turns=31.0, D0=0.9400`.
That is a replication of a published number through a different script,
and it is what makes the fixed column readable as a delta.

The re-baseline is −.001 on block-optimality and −.005 on
attack-optimality, both far inside their intervals. **Previously reported
block-optimality numbers do not need restating.** The trajectories did
drift (64 fewer blocks declared), so this is a same-seed comparison of
two combat models, not a per-position one.

### 4b. With that fixed, the defender search becomes exactly deduplicable

Order-independence makes identical bodies genuinely interchangeable, so
`bestDeduped()` enumerates only canonical assignments — within a group of
identical bodies, only non-decreasing attacker-index sequences.

Verified, because an argument is not a check: **0 mismatches in 5000
random boards** against the brute force it replaces, and **6 in 5000
under the legacy tie-break** — the same bug seen from the other side.
`rl/xmage-src/CombatMathCheck.java`; output committed at
`artifacts/rung0/W0Base/combatmath_check.txt`.

It took defender-reply truncation from **15 of 79 combats to 0 of 79** on
a five-game probe, and 0 of 1264 on the 100-game baseline. That
truncation was not noise: `best()` enumerates from code zero and code
zero is all-decline, so a cut search systematically under-blocks and the
reference comes back too easy to match.

---

## 5. The fix

`jointAttacks`, encoder v5. Enumerate subsets → dedupe by body multiset
BEFORE the inner search (exact: minimax value reads nothing but power and
toughness) → value each under the defender's best reply → dedupe by
outcome → Pareto filter → one consult.

**The Pareto filter carries five objectives, not three, and that is
load-bearing.** Blocks use three. Attacks need retained POWER and
retained BODIES as well, because under a one-combat outcome holding a
creature back is dominated by attacking with it almost always — a
three-objective filter would delete every hold-back option from the
candidate list and the agent would alpha-strike by construction. The
filter must not decide the question the fix exists to let the policy
decide. Bodies as well as power because blocking capacity is bodies:
keeping one 3/3 beats keeping two 1/1s on power and loses on blockers.

**Mechanism verified two ways, neither involving a trained net.**

*Coverage* (`--coverage`, no policy server): the reference-best subset
survives dedupe and Pareto in all four constructed positions.

*Replay* (`game_v5_ck512_vs_D0_seed6001.txt`): at t9 and t11 the policy
commits all three creatures as ONE choice, and the `[atkjoint]` candidate
count, the `ATTACK`/`hold` lines, and the `[atkaudit]` line agree on the
same subset — and the audit recovers that subset by reading the engine's
combat groups, independently of the array `jointAttacks` chose. The
declaration mapping is verified end to end.

---

## 6. The v5 policy numbers, which say nothing

`v4_ck512` driven through the v5 attack path, 20 games. **Out of
distribution by construction** — the net has never seen these candidate
features. Recorded so the next person does not have to rediscover what it
looks like:

```
0 wins, 4 losses, 16 STALLS at the 60-turn limit, 54.0 turns/ep
attack rate            377/1650   .228 [.209,.249]
attack-optimality       74/460    .161 [.130,.197]
missed lethal          301 of 460 combats
errors UNDER / OVER     27 / 58
```

Constructed positions, same checkpoint, same caveat: takes COMMIT
(matches the reference), over-attacks ALPHA33, holds through LETHAL, and
its HOLD answer was decided by the Pareto filter (1 candidate survived),
not by the net.

**None of this compares v5 to v4.** It is one untrained-for-this-space
net on 20 games. In particular "v5 takes COMMIT and v4 does not" is NOT a
result: it shows the right answer is SELECTABLE, which the coverage check
already establishes without a net at all.

---

## 7. Confounds, named here rather than in chat

**The reference is biased toward attacking.** `attackerScore` is one
combat deep and prices at zero the fact that an attacking creature is
tapped through the opponent's entire next turn. Any fix that makes the
agent attack more scores better against it partly by construction. This
is the mirror of the v2 situation, where the metric's bias ran AGAINST
the arm that won.

**The reference is also biased against attacking**, and this was not
anticipated. It mirrors `defenderScore`, which prices material at 3 a
point and damage at 2, so it under-values racing. **The two biases run in
opposite directions and the net cannot be signed.** Concretely, this is
why the handoff's own ALPHA position does not survive its own evaluator:
three 2/2s into a 3/3 scores −4 for the alpha strike against 0 for
holding, because the 3/3 eats a 2/2 and survives. The handoff describes
that position as one where attacking with all three is right. The
evaluator disagrees. Neither settles it — a one-combat evaluator cannot
price a race — and the weights were NOT retuned to make the position come
out "right", because fitting the referee to the desired answer is how a
metric stops measuring anything. The battery was rebuilt around COMMIT
(three 2/2s into a 3/1: hold 0, one 0, two +4, all three +8) where
commitment genuinely pays under the evaluator in use.

**The CA arm is a sensitivity check, not a second reference.**
`attackerScoreCA` subtracts a crude crack-back: their surviving power
past what my retained bodies can absorb, one blocker eating one attacker
whole. It over-credits my blockers (a 1/1 does not really absorb a 5/5)
and ignores what they kill. It moved attack-optimality .622 → .632, i.e.
almost nothing, which is weak evidence that the tapped-out blindness is
not what is driving the baseline number — and weak is the right word for
one crude proxy on one checkpoint.

**The audit and the policy share a combat model.** Both call the same
`CombatMath`. A modelling error common to both is invisible to this
measurement by construction; only the constructed positions and the
engine itself can catch that class of error.

**`defenderScore` still has no blockers-used term**, so the defender's
best reply may pile blockers where a cheaper reply scores the same. Ties
break toward the lowest enumeration code, which is all-decline, so the
bias in the REPLY runs toward under-blocking — which makes attacks look
slightly better than they are.

**Everything here is one checkpoint, one seed, one deck, rung 0.**

---

## 8. What is left

- **Train a v5 arm.** The obvious next step and the one deliberately not
  taken. It needs a v4 control fine-tuned from the same checkpoint for
  the same budget, or "v5 is better" is confounded with "512 more
  episodes". Two seeds if the win rate is going to be quoted at all.
- **The LETHAL failure is worth chasing on its own.** A policy that
  declines an unblockable lethal attack has a problem that joint
  assignment may not touch, since no coordination is required. Whether
  v5 fixes it is exactly what a trained arm would answer.
- **`rl.attackMaxCreatures` truncation is hold-biased.** Above 12
  available attackers the choice covers the biggest 12 and the rest are
  forced to hold — the same direction as the bug. It fired on 1 combat in
  100 games, so it is currently harmless and counted, not fixed.
- **Rung 1 breaks all of this.** `CombatMath` is vanilla-bodies-only and
  the attack side inherits that scope exactly: first strike, deathtouch,
  trample, flying and menace each need an explicit change, and
  `bestAttack` will silently give wrong answers for them.

---

## 9. Reproduction

```bash
# attack audit off any checkpoint (sequential; ~13 min for 100 games)
bash rl/attack_audit.sh <ckpt> <encV> W0Base heuristic 100 900512 <out.txt>
ATTACK_AUDIT=false ...      # instrument off: measures the POLICY's search
AUDIT_EXTRA=-Drl.legacyTieBreak=true ...   # pre-fix combat damage tie-break

# constructed positions
python3 rl/position_probe.py --coverage            # no policy server needed
python3 rl/position_probe.py --port <p> --v4       # per-creature attacks
python3 rl/position_probe.py --port <p> --v5       # joint attacks

# annotated replay: [atkjoint] candidates + [atkaudit] verdict per combat
bash rl/rung0_replay.sh <ckpt> 5 W0Base heuristic 6001 <out.txt>

# the search self-test
java -cp "$(cat /tmp/rl_p9/cp.txt):Mage.Tests/target/test-classes" \
     org.mage.test.benchmark.rl.CombatMathCheck 5000
```

`rl.encoderV` AND `rl.legacyTieBreak` are both fixed at class-init, so a
driver JVM that served one arm cannot serve another. Every script here
kills it first; that is not optional.

Artifacts under `rl/artifacts/rung0/W0Base/`: `attack_audit_v4_fixed.*`,
`attack_audit_v4_legacy.*`, `attack_audit_v5_ood.*`,
`probe_attack_v4_ck512.txt`, `probe_attack_v5_ck512_ood.txt`,
`probe_attack_coverage.txt`, `combatmath_check.txt`,
`game_v5_ck512_vs_D0_seed6001.txt`.
