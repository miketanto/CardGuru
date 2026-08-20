# Encoder v6 build plan — entity tokens with relations (Option B)

Concrete plan for the architecture in `rl/ENCODING-DESIGN.md` §4d,
Option B of `rl/artifacts/encoding-options.html`. Read `ENCODING-DESIGN.md`
first; this file assumes its findings and does not restate them.

**The one-line shape.** Replace the six board scalars with one token per
card, run attention over the tokens with the game's relations as edge
biases, sum-pool to a state embedding, and leave the entire candidate /
action path untouched.

**The insertion point is better than it looks.** `AttnPolicy` in
`policy_server.py` already builds a sequence `[state_token ‖ candidate
tokens]`, runs `nn.TransformerEncoder` over it with a padding mask, reads
logits off the candidate positions and the value off position 0. Entity
tokens go into that same machinery. We are not introducing attention —
it is already there, applied to the wrong thing.

---

## 0. Pre-registration, because this cannot be gated on the usual metric

`ATTACK-JOINT-RESULT.md` §6c proves the current reference's answer is a
linear function of three candidate features, recovered from candidates
alone in 400/400 positions **with the state discarded**. It follows that:

> **Attack-optimality and block-optimality CANNOT improve from this
> change.** Any such improvement would be noise or a bug.

So the acceptance gate is NOT the audit. It is §5's collision probe.
Stating this before building is the whole point — this project has
withdrawn five claims for want of it.

---

## 1. The entity token, 48 dims (v1)

`EDIM = 48`. Every card in every zone gets one token, plus one token per
player. Zero-padded to `EMAX = 24`, masked.

| idx | group | features |
|---|---|---|
| 0–7 | slot & zone | occupancy · mine · theirs · zone one-hot: battlefield / hand / stack / graveyard / player |
| 8–15 | body | power ÷6 · toughness ÷6 · **damage marked ÷6** · toughness remaining ÷6 · is-creature · is-land · is-other-permanent · mana value ÷6 |
| 16–23 | status | tapped · summoning-sick · attacking · blocking · can-attack-now · can-block-now · entered-this-turn · is-token |
| 24–37 | combat keywords | flying · reach · first strike · double strike · deathtouch · trample · vigilance · menace · defender · lifelink · indestructible · ward · hexproof · protection |
| 38–43 | stack & targeting | stack position ÷4 · is-instant · is-sorcery · targets-creature · targets-player · targets-spell |
| 44–47 | player token only | life ÷20 · hand size ÷10 · lands ÷10 · untapped lands ÷10 |

Two notes that matter:

- **Damage marked (idx 10) is invisible today and decides every combat.**
  A 3/3 with 2 damage blocks nothing like a fresh 3/3, and no current
  channel carries it.
- **Rows 24–37 are a projection of E2's `kw_*` columns, not a second
  copy.** `e2_extract.py` already emits all fourteen. Build the token by
  indexing the existing table, so there is one source of truth for what
  "deathtouch" means.

**Extension, not v1:** appending the full 68-dim E2 vector gives
`EDIM = 116` and is what rung 4+ needs for spells on the stack. Do not
pay for it at rung 0–3 where every effect flag is zero.

**Globals** stay a small flat vector, `GDIM ≈ 16`: turn, is-my-turn,
phase one-hot, both life totals, library size, both graveyard sizes,
stack depth, consult budget remaining. Everything else moved into tokens.

## 2. Relations — an edge list, biased into attention

Passed as a list of `[src, dst, type]` over token indices. `RTYPES` for
rungs 0–3:

| type | edge |
|---|---|
| 0 | `blocks` — blocker → attacker |
| 1 | `blocked_by` — attacker → blocker (the reverse edge, typed separately) |
| 2 | `attacking_player` — attacker → defending player token |
| 3 | `targets` — stack object → its target |
| 4 | `controls` — player token → permanent |
| 5 | `attached_to` — aura/equipment → creature (rung where it appears) |

Server-side these become an additive attention bias: a learned
`Embedding(len(RTYPES)+1, heads)` scattered into a `(B, heads, E, E)`
tensor, reshaped to `(B*heads, E, E)` for `TransformerEncoder`'s
`mask` argument. Absent edges get bias 0, so an all-zero edge list
degrades exactly to plain self-attention — which is the natural ablation
arm (**R0: relations zeroed**) and should be built at the same time.

## 3. Tensor shapes

```
globals     (B, GDIM=16)
entities    (B, EMAX=24, EDIM=48)      ent_mask (B, 24) bool
relations   (B, heads, 24, 24)          built from the edge list
candidates  (B, MAX_K, CDIM=94)         cand_mask (B, MAX_K)   UNCHANGED
```

## 4. File-by-file

### 4a. `rl/xmage-src/StateEncoder.java`

- `ENCODER_V >= 6` gate, alongside the existing v1–v5 switch.
- `encodeGlobals(game, me, opp) -> float[GDIM]`.
- `encodeEntities(game, me, opp) -> float[][]` — battlefield both sides,
  my hand, stack, graveyards, two player tokens, in a **deterministic
  emission order** (zone, then body descending, then a stable non-name
  tiebreak). Order does not affect the pooled embedding — that is the
  point of sum-pooling — but it must be deterministic so relations index
  correctly and replays reproduce.
- `encodeRelations(game, index) -> int[][]` — needs the same index map
  the entity emission produced, so build both in one pass and return a
  small holder rather than calling the game twice.
- `entityKeywords(name)` — index into `CARD_FEATURES` for the fourteen
  `kw_*` columns. Unknown card → all zero plus the existing unknown flag.

### 4b. `rl/xmage-src/SocketPolicyClient.java` + `PolicyClient.java`

- New method on the interface:
  `choose(float[] globals, float[][] entities, int[][] relations, float[][] cands, float phi)`.
  Keep the old `choose(state, cands, phi)` so v1–v5 arms still run from
  one build, exactly as the encoder property already allows.
- Wire: `{"t":"consult","g":[…],"e":[[…],…],"r":[[s,d,t],…],"c":[[…],…],"phi":f}`.
- Hello advertises `gdim`, `edim`, `emax`, `rtypes` beside the existing
  `sdim`/`cdim`; server rejects a mismatch loudly at handshake rather
  than silently mispredicting — the failure mode `rung0_replay.sh`'s
  header already warns about.

### 4c. `rl/policy_server.py`

New `EntityAttnPolicy`, selected by `--arch entattn`:

```
ent_in    Linear(EDIM -> d)
rel_emb   Embedding(len(RTYPES)+1, heads)
ent_enc   TransformerEncoder(d, heads=4, layers=2)   # attn_mask = relation bias
pool      masked SUM over entity tokens  ->  Linear(d -> d)
glob_in   Linear(GDIM -> d)
state_tok = glob_in(globals) + pool(entities)
   ... from here the existing AttnPolicy path is unchanged:
       LSTMCell, cat([state_tok, cand_tokens]), enc, scorer, value_head
```

**SUM, not mean.** Mean-pooling one 2/2 and three 2/2s produces the
identical vector; that is `s[8..13]` rebuilt with extra steps. This is
the single easiest way to build the whole thing and fix nothing.

Also: `--edim/--emax/--gdim` args, the `k > MAX_K` guard extended to
entities, and the checkpoint dict gains the new dims so a mismatched
load fails loudly.

### 4d. `rl/position_probe.py`

The probe re-implements the encoder in Python and **faithfulness is the
whole risk** — its own docstring says so. Entity tokens and relations
must be ported, and `--validate` must be re-pointed at a committed v6
transcript. Budget real time for this; a probe that drifts from the Java
measures its own bug.

### 4e. Lanes

`rung0_lane.sh` / `rung0_replay.sh` / `attack_audit.sh`: `SDIM/CDIM`
selection becomes `GDIM/EDIM/EMAX/CDIM` for `ENC >= 6`. The driver-JVM
kill on arm switch stays mandatory — `rl.encoderV` is still read at
class-init.

## 5. The acceptance gate — a collision probe

Per §0 the audit cannot move. Build this instead, and build it **first**:

**5a. Invariance test (no policy).** Shuffle the emission order of a
board; the pooled entity embedding must be identical to float tolerance.
This is the v6 analogue of `CombatMathCheck` and it belongs in the repo
as a runnable file, because permutation-invariance is an *argument* until
it is a test.

**5b. Collision test (no policy).** The six W0Base boards from
`ATTACK-JOINT-RESULT.md` §6c — `{2/2+2/2+3/3}`, `{2/2+3/1+2/4}`,
`{2/2+2/3+3/2}`, `{3/1+2/3+2/3}`, `{2/3+3/3+2/1}`, `{3/2+2/4+2/1}`, all
count 3 / power 7 / toughness 7 — must produce **six distinct**
embeddings. Today they produce one. This is a pass/fail on the thing the
change exists to fix and it needs no training at all.

**5c. Behavioural pair (policy, trained).** Two constructed positions
that are byte-identical under v5 and require *different* attacks. Under
v5 the agent must answer them identically by construction; under v6 it
can differ. This is the only test that can show the encoding changed
behaviour, and it is worth writing before training so it cannot be
tuned to.

**5d. Regression floor.** Block-optimality and attack-optimality must
not FALL outside their intervals. They cannot rise (§0). A drop means
the extra width cost sample efficiency, which is the predicted risk.

## 6. What this invalidates

- **Every checkpoint.** `v4_ck512`, `v5_ck1024`, `v4ctl_ck1024`,
  `p10_final`, the whole v1–v5 ladder. New dims, new modules, no load
  path. Take this re-baseline once.
- **The E0/E2/E3 ablation numbers** are no longer comparable, since the
  card-feature table now enters through a different door.
- **`position_probe.py`'s validate case**, until re-pointed.
- Not invalidated: `CombatMath`, both audits, the afterstate candidates,
  the lane scripts' structure, and every finding in
  `ATTACK-JOINT-RESULT.md`, which is about the reference and the action
  space rather than the state.

## 7. Order of work

1. `encodeEntities` + `encodeRelations` + globals, Java side, no server
   changes — dump tokens to the replay log and eyeball one game.
2. Tests 5a and 5b. **Stop here if 5b fails**; nothing downstream is
   worth building on an encoder that still collides.
3. Wire protocol + handshake, both sides, with the loud mismatch error.
4. `EntityAttnPolicy` and `--arch entattn`, relations zeroed (arm R0).
5. Probe port (4d) and the behavioural pair (5c).
6. Train: v6 with relations, v6-R0 without, matched budget and seed. The
   R0 arm is what separates "entity rows helped" from "relations helped",
   and without it v6 repeats v5's confound of moving two things at once.
7. Only then, Option C behind its deck-diversity gate.

## 8. Known risks, stated in advance

- **Sample efficiency.** ~16× the input width on the same 512-episode
  budgets. If v6 underperforms v5 at matched budget, the first
  hypothesis is budget, not encoding — and resolving it costs a budget
  sweep, not another architecture.
- **Nothing here moves the audit** (§0). If the only reportable result is
  a collision test passing, that is still a real result, and it should be
  reported as exactly that rather than dressed up in a win rate that 100
  games cannot resolve.
- **Relations may do nothing at rung 0–3**, where the only live edges are
  `blocks` / `blocked_by` / `attacking_player` and the candidate already
  carries the resolved combat outcome. The R0 arm is what tells us,
  cheaply, and it is why R0 is not optional.
