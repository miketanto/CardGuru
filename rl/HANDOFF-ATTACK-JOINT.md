# Handoff — attacking is the next joint decision

Read `rl/ENCODER-AB-RESULT.md` first, all of it. This document assumes
it. The one-line version: blocking was broken because the policy made
one decision per blocker with no sight of the others, and it was fixed
by replacing that with one decision per combat over complete
assignments. **Attacking still has the original bug, untouched.**

---

## 0. State of the world

Branch `claude/cardguru-p10-flagship-48r5lg`, all pushed. Never push to
phase-5.

Encoder arms, selected by `-Drl.encoderV` (read at class-init, so all
four run from one build):

| v | state/cand dims | what it is |
|---|---|---|
| v1 | 24 / 91 | original. No combat channels, no block context. Product of independent marginals. |
| v2 | 32 / 94 | conditioned autoregressive blocking. Fixes over-piling. |
| v3 | 32 / 94 | v2 + controller-blind combat channels fixed. **Never trained.** |
| v4 | 32 / 94 | v3 + joint block assignment, outcome-featurized. |

What is settled:

- v1 blocked **15,674 of 15,674** opportunities with zero declines. That
  is an observability failure, not a learning failure.
- v2 block-optimality .829 vs v1 .557 (+.272, z=16.2). Win rate +.055
  (z=1.27) — **not** a finding.
- v4 fixes the commitment failure, cleanly, on constructed positions.
- v4 at 512 eps, seed 0: D0 .940, D1 .920, TWIN .860, block-optimal
  95.3%. **One seed, 100 games a row.**

Checkpoint: `rl/artifacts/rung0/W0Base/v4_ck512.pt` (committed — load it
rather than retraining). Replay:
`rl/artifacts/rung0/W0Base/game_v4_ck512_vs_D0_seed6001.txt`.

---

## 1. The task

`RLPlayer.selectAttackers` is still this:

```java
for (Permanent creature : avail) {
    float[][] cands = {blank(T_PASS), forCombat(T_ATTACK, creature, game)};
    if (policy.choose(state, cands, phi(game)) == 1) { ... }
}
```

One independent yes/no per creature, and — exactly as with v1 blocking —
declaring an attacker taps nothing and changes no life total, so creature
2 sees a near-identical observation to creature 1. It is the same bug in
the same shape, and it produces the same behaviour: the attack probe
holds **all three** creatures back against a single blocker, in v2 and
v4 alike. In the committed v4 replay it holds everything for twelve
consecutive turns at 20-20 life, including turns at 4-1 and 3-1 on board.

`jointBlocks()` in `RLPlayer.java` is the template. What attacking needs
is the same move: **one decision per combat over attack subsets**, each
candidate described by its simulated consequence rather than by cards.

### Why this is harder than blocks, and do not pretend otherwise

`CombatMath.resolve()` answers "what happens if these blockers block
these attackers". Attacking needs "what happens if I attack with this
subset", and the answer depends on **what the defender does next**, which
is a different question with a different shape. Three honest options:

1. **Assume the defender blocks best** (minimax one ply). Uses
   `CombatMath.best()` as the inner loop, so the outer search is
   `2^A × (B+1)^B` — needs a cap and a truthful `truncated` counter.
2. **Assume the defender blocks as the current policy would.** Cheaper,
   self-consistent, and drifts as the policy changes.
3. **Featurize the subset without resolving it** — total power sent,
   power retained for defence, life swing if unblocked, worst-case trade.
   Loses exactness, keeps tractability.

Option 1 is the principled one and matches how `CombatMath` is already
documented ("the defender must assume the worst"). Start there, measure
the cost per combat, and fall back if it dominates wall-clock. Whatever
you pick, it goes in the doc — the project's rule is that a reference is
named "best by this evaluator", never "optimal play".

### An attack audit does not exist yet

`auditBlocks` gives block-optimality. There is no equivalent for attacks,
so **there is currently no way to say whether an attack was good.** Build
`auditAttacks` before you build the fix, or you will have no instrument
to detect success. Same discipline as `auditBlocks`: read it *after* the
policy commits, exclude positions with nothing to decide (no available
attackers is trivially optimal — that mistake already inflated an
untrained net to 98.4%), and count truncation separately.

---

## 2. Two known gaps you will trip over

**`defenderScore` has no term for blockers used.** So `MATCH` in the
audit means *scored the same*, not *chose the same*. The v4 replay at t10
throws three creatures at a 2/1 where the solver uses one, and both score
1. Piling is free at rung 0 and stops being free at rung 5 (`W5Trick`,
Aegis of the Heavens, +1/+7 instant) — three creatures die to one card
and nothing in the reward points away from it. If you touch the
evaluator, that is the term to add, and it changes every block-optimality
number ever reported, so it is a deliberate re-baseline, not a tweak.

**Pareto filtering can collapse to one candidate.** At t22 of the replay,
12 distinct outcomes became 1. The policy had no decision; the MATCH is
the filter's. `blockOptimal/blockCombats` does not distinguish, so it is
an **upper bound** on the policy's share of the credit. Consider counting
`blockCombatsWithChoice` separately.

---

## 3. Things worth doing that are not this task

Pick deliberately; do not silently fold them in.

- **v4 second seed.** One seed at 100 games says nothing about win rate.
  Cheapest real result available: `R0_ENCODER_V=4 bash rl/rung0_lane.sh
  W0Base W0Twin 512 1`.
- **v3 arm.** The clean control isolating the controller fix from joint
  assignment. Until it runs, "v4 wins more" stays unattributable across
  three simultaneous changes.
- **200-game CP7 probe.** The 10-game rows are decorative — the same arm
  gave .900 and .500.
- **Black branch.** `rl/HANDOFF-BLACK-BRANCH.md`, written, nobody has
  picked it up. It also flags that `EpisodeRunner` must log removal
  *targets* before threat assessment is measurable.
- **k-turn rollout reference.** `CombatMath` is one combat deep. Threat
  assessment is multi-turn, so the black branch needs this before it
  touches removal.

---

## 4. Environment, because the container will be recycled

It has already been lost four times. Rebuild:

```bash
git clone https://github.com/magefree/mage.git /home/user/mage
cd /home/user/mage && git checkout 7554968c
git apply /home/user/CardGuru/rl/engine-patches/phase9-engine.patch
mkdir -p Mage.Tests/src/test/java/org/mage/test/benchmark/rl
cp /home/user/CardGuru/benchmark/xmage/src/*.java Mage.Tests/src/test/java/org/mage/test/benchmark/
cp /home/user/CardGuru/rl/xmage-src/*.java        Mage.Tests/src/test/java/org/mage/test/benchmark/rl/
cp /home/user/CardGuru/rl/*.dck /home/user/CardGuru/benchmark/xmage/*.dck \
   /home/user/CardGuru/rl/m3_decks/*.dck Mage.Tests/
mvn -q -pl Mage.Tests -am install -DskipTests -Dfile.encoding=UTF-8   # ~15 min
pip install torch
```

**Do not apply `phase12-mana-recopy.patch`** — its hunks land fuzzy on
the phase9 playable-memo block and duplicate it. The only two things
needed from it (`MANA_RECOPY_CHECKED` / `MANA_RECOPY_MISMATCHES`, which
`EpisodeRunner` prints and without which the module does not compile) are
already carried in `phase9-engine.patch`.

After editing only `rl/xmage-src/`: `mvn -q -pl Mage.Tests test-compile`.
After editing anything under `Mage/`: `mvn -q -pl Mage install -DskipTests`
first. `Mage.Tests` targets **Java release 8**.

**Commit any checkpoint you care about.** `rung0_autosync.sh` keeps only
the newest, and the best is not the last — `ck_1919`, the .782 peak, was
lost that way, and the first v4 checkpoint was lost to a restart, costing
a rebuild and a retrain to produce one replay.

---

## 5. Running things

```bash
# train (conc4)
R0_ENCODER_V=4 R0_EVERY=512 bash rl/rung0_lane.sh W0Base W0Twin 512 <seed>

# constructed positions, over the wire, no engine
python3 rl/position_probe.py --port <p> [--validate] [--v4]

# annotated replay
bash rl/rung0_replay.sh <ckpt> <encV> W0Base heuristic <seed> <out.txt>
```

Gotchas that have each cost an hour:

- `RL_TORCH_THREADS=1` is not optional — worth 1.54x at conc4.
- `rl.encoderV` is fixed per JVM at class-init. A driver JVM that served
  one arm **cannot** serve another; the lane kills it per arm. Skipping
  this made v1 jobs handshake 32/94 against a 24/91 server, write no
  output, and record `NA` while the counter advanced.
- v4 needs the policy server started with `--max-k 64`.
- The `RLGAME` transcript is printed by the JVM that *plays* the game, so
  under `RL_PERSIST` it lands in `/tmp/rl_p9/driver_server_<port>.log`,
  not the client log. The mvn path is no escape — `run_driver.sh` passes
  `-q`, which suppresses surefire's console output entirely.
- `pkill -f 'pattern'` matches the invoking shell. Bracket it:
  `[R]LDriverServer`. This killed the session once.
- Eval must run sequentially (leave `RL_CONC` unset) or ratings are not
  reproducible.

---

## 6. Ground rules

These are the ones this project has actually violated and had to retract.

- **Wilson intervals, never Wald.** Wald reports ±0.000 at p=0, which
  once claimed 0/200 with zero uncertainty.
- **Pool only finished seeds.** A running seed at 512 was once pooled
  with a finished one at 2111 and the spread reported as between-seed
  variance.
- **A regression is not "flat."** The saturation test has three verdicts.
- **State what a number cannot support.** Every claim in
  `ENCODER-AB-RESULT.md` that could not be attributed is labelled as
  such. Keep that. Five claims were withdrawn in one session for want of
  it — including "D1 is weaker than D0" (`SearchPlayer` never overrides
  `selectAttackers`/`selectBlockers`, so D1 *is* D0 in combat) and "depth
  buys nothing" (the depth ladder varied depth in a subgame with no
  decisions).
- **Confounds get named in the doc, not just in chat.** v4 moves three
  things at once and says so.

---

## 7. Files

| file | why |
|---|---|
| `rl/ENCODER-AB-RESULT.md` | the whole v1→v4 story. Read first. |
| `rl/COMBAT-LITERATURE.md` | LOCM / Hearthstone / MTG-Causal-RL are all attacker-directed with no blocking. Nobody has solved this for us. |
| `rl/xmage-src/RLPlayer.java` | `jointBlocks()`, `auditBlocks()`, `selectAttackers()` |
| `rl/xmage-src/CombatMath.java` | exact resolution + brute-force reference. Vanilla bodies only — rung 1 adds keywords and each needs an explicit change here. |
| `rl/xmage-src/StateEncoder.java` | `forBlock`, `forAssignment`, the v1–v4 switch |
| `rl/position_probe.py` | constructed positions, includes a Python port of CombatMath |
| `rl/CURRICULUM-LADDER.md` | both branches, why each rung changes one variable |
| `rl/HANDOFF-BLACK-BRANCH.md` | the other branch, unclaimed |
