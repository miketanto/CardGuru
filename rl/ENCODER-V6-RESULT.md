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

_pending — the runs are sequential because `rl.encoderV` is fixed at
class-init._
