# Encoder v6 — both halves landed, and what the gate says

`ENCODER-V6-BUILD.md` steps 1–4 and 6 of §7, in one session.
`ENCODER-V6-NETWORK.md` is the network half's record; this is the
emission side, the wire-up, and the gate the whole change is gated on.

---

## 0. The gate, first, because §0 says nothing else can settle this

§0 pre-registered that attack- and block-optimality **cannot** improve
from a state-path change. So the acceptance test is §5b's collision
probe, and it now runs on **real emission** rather than constructed
rows:

```
python3 rl/entity_gate.py /tmp/v6_gate.jsonl --emax 48

GATE|positions=1983|distinct_v5=1574|v5_groups_with_2plus=193
GATE|v5_groups_hiding_different_boards=90|pairs=853
GATE|embedding_separation|pairs=853|closest=0.014141|below_tol=0
GATE|PASS
```

Read it as: over 1983 rung-0 consults, 193 v5 state vectors covered
more than one position, and **90 of those covered positions with
genuinely different boards** — 853 pairs that are byte-identical to the
v1–v5 encoder. Under v6 all 853 are distinct embeddings. Nothing was
trained to produce that; it is a property of the emission and the
sum-pool.

What it does **not** say: nothing about win rate, nothing about
attack- or block-optimality, and nothing about whether the agent can
USE the separation. It says the information is now in the observation
instead of being destroyed before the net sees it.

The positions come from 40 sampling-mode games; an eval-mode untrained
net passes every window, so the boards would have been empty and the
gate would have had nothing to test. `entity_gate.py` prints
`INCONCLUSIVE` rather than `PASS` in that case, on purpose.

## 1. EMAX was wrong, and the counter is why we know

The build plan said `EMAX = 24`. That was a guess made before anything
had been emitted. Measured over 40 rung-0 games:

| EMAX | consults | truncated | entities dropped | largest board |
|---|---|---|---|---|
| 24 | 1944 | **458 (23.6%)** | 3172 | 45 |
| 48 | 1983 | 0 | 0 | 43 |

At 24, a quarter of the agent's consults would have been blind to part
of its own board — the exact failure v6 exists to remove, reintroduced
by a buffer size. The default is now 48 on both sides.
`entityTrunc`/`entityDropped`/`entityMaxSeen` are reported in every
driver summary, so the next time the buffer is wrong it says so instead
of degrading quietly. 43 against 48 is not much headroom: rung 4+ or
longer games should re-read the counter rather than assume.

EMAX is a BUFFER — raising it changes no weights and no checkpoint —
which is why this is a one-line fix and not a re-baseline.

## 2. Two wire bugs the wire-up found

Both are the same species: a failure that was designed to be loud, and
wasn't quite.

- **The refusal reply did not match.** The server refused a bad
  handshake with `{"ok": 0, "err": ...}` (json.dumps' default spacing)
  while the driver matched on the literal `"ok":0`. So an `emax`
  mismatch — which the server DID catch, correctly — surfaced three
  frames deep in a later consult as `policy IPC failed`. Fixed on both
  sides: the server writes compact JSON, and the driver now fails
  CLOSED on anything that is not `"ok":1`.
- **The entity dump buffered its last line.** The driver JVM is
  persistent, so the tail sat unwritten while the gate was already
  reading and tripped over half a JSON object. It flushes per line, and
  `entity_gate.py` reports any line it cannot parse rather than
  skipping it silently.

`SocketPolicyClient` used to discard the hello reply entirely. It reads
it now: a refused handshake looked exactly like an accepted one, which
is the failure mode §4b was written about.

## 3. What the emission does

`StateEncoder.encodeEntityView`, behind `ENCODER_V >= 6`:

- **The 48-dim token** of §1, per card and per player. Damage marked
  (idx 10) is in it — invisible to `encodeState` and decisive in every
  combat.
- **The fourteen combat keywords by INDEXING `e2_features.tsv`**, not
  re-derived, so "deathtouch" has one definition in this codebase.
  `indestructible` has no column in `e2_extract.py`'s keyword list, so
  its slot is always zero and says so in a comment; adding the column
  would change `FEAT_DIM`, hence `CAND_DIM`, hence every checkpoint —
  a rung-4+ decision, not one to take in passing.
- **§2's typed edge list**, built in the SAME pass as the index map, so
  edge indices cannot drift from token order. Edges whose endpoints
  were truncated are dropped rather than clamped.
- **Deterministic emission order**: priority band, body descending,
  then `createOrder` (stable across replays; UUIDs are not, they come
  from `SecureRandom`), then name. None of it is observable — the pool
  is a SUM and `entattn_check.py` measures the invariance — but a
  replay has to reproduce it and the edge list indexes into it.
- **Truncation drops from the bottom band**, so player tokens and
  creatures survive a board that overflows the buffer; lands, hand and
  graveyards go first.

`RLPlayer` routes all six consult sites through one `consult()` helper.
Exactly one place knows which state path is live, and the candidate
lists are untouched at every site — v6 changes what the agent sees,
never what it can choose.

## 4. Training arms

Three matched short arms, W0Base, seed 0, 512 episodes, 25-game
battery, CP7 skipped symmetrically. v5 → v6 moves the state path; v6 →
R0 moves only the edge list.

| arm | encoder | state path | relations |
|---|---|---|---|
| v5 | 5 | flat 32-dim | n/a |
| v6 | 6 | entity tokens | live |
| v6-R0 | 6 | entity tokens | dropped at the server |

Results go in §5 when they finish. Read them with §0 in hand:
**attack- and block-optimality cannot improve from this change**, so if
they move up, that is a bug to find and not a result to write up; and
25 games cannot resolve a win-rate difference at all — the interval is
±0.13 at p=0. What these arms CAN say is whether the wider observation
costs sample efficiency (§8's predicted risk), and whether relations do
anything at rung 0–3 (§8 says they may not; R0 is how that gets
answered).

## 5. Arm results

W0Base, seed 0, 512 episodes, 25-game battery, CP7 skipped
symmetrically. One seed. Every rate is Wilson.

| | v5 (flat) | v6 (entities+relations) | v6-R0 (no relations) |
|---|---|---|---|
| D0 | 1.000 [.867,1.000] | 0.960 [.805,.993] | 0.880 [.700,.958] |
| D1 | 1.000 [.867,1.000] | 0.920 [.750,.978] | 0.880 [.700,.958] |
| TWIN | 0.920 [.750,.978] | 0.840 [.653,.936] | **not obtained** (see 5c) |
| block-optimal | 146/158 **.924** [.872,.956] | 155/167 **.928** [.879,.958] | 152/160 **.950** [.904,.974] |
| attack-optimal | 160/242 **.661** [.599,.718] | 196/236 **.831** [.777,.873] | 207/260 **.796** [.743,.841] |
| attack-optimal (CA ref) | .678 | .805 | .792 |
| creatures sent / combat | 1.40 (ref 0.96) | 1.31 (ref 0.92) | 0.97 (ref 0.85) |
| consults / episode | 134.8 | 187.3 | 217.8 |
| turns / episode | 25.4 | 25.1 | 27.0 |

**Win rate: no arm separates from another.** Every interval overlaps
every other at 25 games. v5 is nominally highest on all three probes,
which is the direction §8 predicted for 16× the input width on the same
budget, and 25 games cannot resolve it. Nothing here is a win-rate
result and it should not be quoted as one.

### 5a. The anomaly: attack-optimality moved, and §0 says it cannot

Both v6 arms beat v5 on attack-optimality by ~14–17 points with
**non-overlapping Wilson intervals** (v5 [.599,.718] vs v6 [.777,.873]
and R0 [.743,.841]). §0 pre-registered that this number cannot improve
from a state-path change. So this is recorded as an **anomaly to
explain, not a result** — exactly what the pre-registration is for.

What has been ruled out:

- **Not truncation.** `attackTruncated` = 0 (v5), 0 (v6), 5 (R0);
  `attackReplyTruncated` = 0 everywhere. The reference searches were
  exhaustive.
- **Not the audit code.** `auditAttacks` runs after the policy commits,
  reads the board through `CombatMath`, and never touches the encoder.
  All three arms ran the same build.
- **Not a different decision path.** `selectAttackers` gates on
  `ENCODER_V >= 5`, so v5 and both v6 arms take the same `jointAttacks`
  route over the same candidate features.
- **Not a global audit shift.** Block-optimality is the internal
  control and it does NOT move: .924 / .928 / .950, all three intervals
  overlapping. A bug that made the audit easier should have moved both.
- **Not relations.** R0 has the effect without any edges, so whatever
  this is, it is not the relation bias.

What has NOT been ruled out, and is the leading hypothesis:

- **The arms are not paired.** Attack-optimality is aggregated over the
  combats each policy chose to reach, and the three policies reach
  different boards — R0 in particular faced 3.58 available attackers
  per combat against v5's 2.62. A metric averaged over self-selected
  positions is not a within-position comparison, and §6c's proof is
  about within-position answers.
- **"Attacks less" does not cleanly explain it either.** All three
  over-attack relative to the reference, but not monotonically with the
  score: 1.47× the reference count → .661, 1.42× → .831, 1.15× → .796.
  So the simple story does not survive its own numbers.

The strongest evidence that the arms face different combats is not a
board-size average — those look alike (2.62 / 2.65 / 3.58 available
attackers per combat) — it is the **combat search cost**, which is
exponential in board size and therefore reads the tail the mean hides:

| per 25-game D0 probe | v5 | v6 | v6-R0 |
|---|---|---|---|
| policy attack search | **2.1 s** | 67.8 s | **937 s** |
| attack audit | 2.3 s | 68.4 s | 937 s |
| games / sec | 0.690 | 0.129 | **0.013** |

A 450× spread in search time cannot come from 2.62 vs 3.58 average
attackers. It means the v6 arms reach combats with far more creatures
than v5 ever does — the tail that `2^A × (B+1)^B` prices — and
attack-optimality is being averaged over those different tails. That is
the hypothesis the paired test has to kill.

It is also an operational finding in its own right, and a worse one
than the anomaly: `attackSearchMs` is the POLICY's own search, not the
instrument, so it is paid during training too. At rung 0 the v6 arms
are 5–50× slower per game than v5 for reasons that have nothing to do
with the network. Rung 1+ boards will be larger. Either
`CombatMath.bestAttack` gets a real cap for these arms or the joint
attack search stops being affordable — stream D's k-turn reference work
now has a second reason to exist.

**The test that would settle it does not exist yet**: a paired
evaluation, both nets scored on the SAME fixed positions — §4d's probe
port plus §5c's constructed pair. Until that runs, no attribution is
made, and in particular **this is not evidence that v6 attacks better**.

One honest note on §0 itself: its premise is that the reference's answer
is RECOVERABLE from candidate features alone (400/400 positions with the
state discarded). That establishes the state is not *necessary* for
attack-optimality. The inference drawn from it — that no state change
can move the metric — is stronger than the premise, because two nets can
differ in how well they learned an available function in 512 episodes.
That does not license reading the gap as a v6 win; it means the
pre-registration and the measurement disagree, and the paired test is
what resolves which one is wrong.

### 5b. What the R0 arm does say

R0 was built so that "entity rows helped" and "relations helped" could
not be confounded. On every comparable number — win rate, block
optimality, attack optimality — **R0 is indistinguishable from v6**.
That is a null result on relations at rung 0, exactly as §8 predicted:
the only live edges here are `blocks` / `blocked_by` /
`attacking_player`, and the candidate already carries the resolved
combat outcome. It is worth having as a null: without it, the anomaly
in 5a would have been read as "relations helped".

### 5c. R0's transfer probe was abandoned, and why that matters

R0's TWIN probe was killed after it spent **12 minutes inside a single
game**, CPU-bound, with 15 games still to play. It is reported as NOT
OBTAINED rather than as a number.

The cause is the cap structure, and it is a defect worth naming:
`rl.attackCap` bounds subset enumeration at 4096 and
`rl.attackReplyCap` bounds each defender best-reply at 200,000 nodes,
so **each stage is capped and the product is not** — a single combat
can cost 4096 × 200,000 node evaluations. `attackTruncated` counts the
outer cap and reports 5 for this arm, so the run looked "not
truncated" while being unable to finish. A per-combat wall-clock or
total-node budget is the missing guard.

This is not a v6 property as such — v5 runs the same search — but the
v6 arms reach the boards that trigger it, so in practice it arrived
with them.
