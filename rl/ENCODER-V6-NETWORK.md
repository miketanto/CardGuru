# Encoder v6 — the network half (stream B)

What `ENCODER-V6-BUILD.md` §4c asked for, built and checked against
synthetic tensors. No engine, no Java, no training. `PARALLEL-SESSIONS.md`
stream B; the emission side (§4a, §4b's Java) is stream A's and is not
touched here.

---

## 0. What this is, and what it is not

Per §0 of the build plan, **attack- and block-optimality cannot improve
from a state-path change**, so nothing below is gated on them and none
of them was measured. Nor was a win rate. What is reported is what a
pooling operator can be checked to do on constructed inputs:

| claim | evidence |
|---|---|
| one 2/2 and three 2/2s are DIFFERENT states | `CHECK\|POOLING`, worst over 5 inits **3.12** |
| mean-pooling them is the SAME state | `CHECK\|MEANCOLLIDE`, worst **4.8e-7** — the bug, measured |
| the six 3/7/7 boards are six vectors | `CHECK\|COLLISION`, closest pair **0.0049** at token scale **6.67** |
| emission ORDER cannot change the state | `CHECK\|PERMUTE`, **1.4e-6** |
| R0 is plain self-attention, numerically | `CHECK\|R0-NOBIAS`, **0.000e+00** |
| padding changes nothing | `CHECK\|MASKING`, **0.000e+00** |
| the wire round-trips | `CHECK\|LOOPBACK` |
| a driver whose vectors mean something else is refused | `CHECK\|HANDSHAKE` ×4, `CHECK\|VALIDATE` (7 bad consults), `CHECK\|CKPTDIMS` |
| `rel_emb`'s no-edge row is still exactly 0 after a PPO update | `CHECK\|R0-STAYS0` |

`COLLISION` here is the NETWORK half only: it says that *given* correct
entity rows the pooled embedding separates boards that v5 fused. The
acceptance gate proper (§5b) is stream A's, against real emission from
`StateEncoder`. And the separation is an untrained-init number: the
claim it supports is "not identical", not "well separated". Size means
nothing until something is trained.

Run it:

```bash
python3 rl/entattn_check.py        # 23 checks, ~4 s, exit 1 on any failure
```

## 1. What landed

| file | what |
|---|---|
| `rl/policy_server.py` | `EntityAttnPolicy`, `EntityObs`, `--arch entattn`, the v6 wire, `--r0`, checkpoint dims |
| `rl/entattn_check.py` | the 23 checks above, runnable, no engine |

```
ent_in    Linear(48 -> 128)
rel_emb   Embedding(len(RTYPES)+1, 4)   padding_idx=0
ent_enc   TransformerEncoder(d=128, heads=4, layers=2)   mask = relation bias
pool      masked SUM over entity tokens -> Linear(128 -> 128)
glob_in   Linear(16 -> 128)             (the inherited state_in, renamed)
state_tok = glob_in(globals) + pool(entities)
```

From `state_tok` onward it is `AttnPolicy.from_state_token` — the same
LSTMCell, the same `cat([state_tok, cand_tokens])`, the same encoder,
scorer and value head, **shared rather than copied**, so the two arms
cannot drift. `forward()` on the flat arms was refactored to call it;
`e0`/`attn`/`lstmattn` are bit-identical before and after (verified:
identical init and 0.000e+00 output difference on the same seed).

716k parameters against `lstmattn`'s 430k. §8's sample-efficiency risk
is real and unaddressed here — it is a training question.

## 2. The wire, as implemented — the contract for stream A

Consult:

```json
{"t":"consult","g":[16 floats],"e":[[48 floats], ...],
 "r":[[src,dst,type], ...],"c":[[94 floats], ...],"phi":123.4}
```

Hello: `gdim`, `edim`, `emax`, `rtypes` **beside** the existing
`sdim`/`cdim`, exactly as §4b says. All four are required when the
server is `--arch entattn`.

Four details the Java side needs to agree with, none of them a change
to §4b — they are the parts §4b left to the implementation:

1. **Edge direction.** `[s, d, t]` biases the attention of QUERY `s`
   toward KEY `d`. §2's reverse edges (`blocks` / `blocked_by`) are
   typed separately precisely because the bias is directed. A repeated
   `(s,d)` pair keeps the last type written.
2. **`type` indexes `RTYPES`** in `policy_server.py`, in the order the
   build plan §2 lists them: `blocks, blocked_by, attacking_player,
   targets, controls, attached_to`. **The index is the contract** —
   reordering that list silently relabels every edge in every
   transcript. Append only.
3. **Edges index the EMITTED entities**, not the padded buffer. An edge
   naming a padding slot is rejected per consult, because that is the
   token-order/edge-list drift the handshake cannot catch.
4. **`sdim` is not enforced for `entattn`.** The flat state vector is
   not read by this arch, so enforcing its width would fail runs over a
   field that carries no meaning. `cdim` IS enforced — the candidate
   path is untouched by v6 and still reads it.

Rejected loudly, with the reason on stdout AND as `{"ok":0,"err":...}`
to the driver before the connection dies:

| case | why it matters |
|---|---|
| driver advertises no v6 dims to an `entattn` server | a v1–v5 driver against a v6 net is a whole run of silent mispredictions |
| driver advertises v6 dims to a flat server | the mirror image |
| `gdim` / `edim` / `rtypes` / `cdim` differ | the vectors mean something else |
| `emax` > server buffer | fixable without retraining; the message says `--emax N` |
| consult with `"s"` and no `"g"`/`"e"` | an arm switch mid-connection |
| entity row of the wrong width, relation type outside `RTYPES`, edge index past the emitted entities | per-consult drift |

`emax` below the server's buffer is fine and prints a note: padded
slots are masked.

## 3. Decisions taken here

- **`entattn` carries the LSTMCell**, matching `lstmattn` — the arm
  `rung0_lane.sh` trains and the one v6 will be A/B'd against. The
  point of the comparison is that the STATE PATH is the only
  difference; an arch that also dropped the memory would confound it,
  which is the mistake §8 and v5's write-up both warn about.
- **`EMAX` and `MAX_K` are buffers; `GDIM`, `EDIM`, `len(RTYPES)` are
  meaning.** Raising a buffer changes no weights and no checkpoint
  compatibility; changing a meaning invalidates both. The handshake and
  the checkpoint record treat the two differently on purpose.
- **`rel_emb` uses `padding_idx=0`**, so the "no edge" row is exactly
  zero and its gradient is zero, which is why R0 degrades to plain
  self-attention *numerically* and — checked — still does after a PPO
  update. Without that, R0 would be "approximately no relations" and
  the ablation would not separate what it exists to separate.
- **The PPO buffer stores the dense relation TYPE-INDEX matrix, not the
  computed bias.** A stored bias is computed under `no_grad` and would
  leave `rel_emb` untrained forever while looking fine.
- **`--r0` drops edges on arrival** (arm R0) and is recorded in the
  checkpoint; loading an R0 checkpoint with relations live is refused,
  because that is exactly the confound R0 exists to remove.
- **Checkpoints carry a `dims` record** and a mismatch raises at load.
  Pre-v6 checkpoints have no such record: they still load for their own
  arch, with a `WARN` saying the check did not run rather than
  implying it passed.

## 4. What is deliberately NOT done here

- **Any Java.** §4a/§4b's emitter is stream A's.
- **`§4e` lane scripts.** `rung0_lane.sh` and friends still pass
  `--sdim ... --arch lstmattn`; the `GDIM/EDIM/EMAX/CDIM` switch belongs
  with the wire-up commit, which needs both sides to exist.
- **`§4d` probe port and `§5c` behavioural pair** — both need stream A's
  emission format, and guessing at it is how a probe starts measuring
  its own bug.
- **Training.** No v6 arm has been trained, so there is no result about
  sample efficiency, win rate, or whether relations do anything at
  rung 0–3 (§8 says they may not; the R0 arm is how that gets answered).

## 5. Running the arms

```bash
# v6, relations live
python3 rl/policy_server.py --port 7960 --arch entattn --cdim 94 \
    --ckpt /tmp/rl_v6/agent.pt --max-k 64

# arm R0, matched in every other respect
python3 rl/policy_server.py --port 7961 --arch entattn --cdim 94 --r0 \
    --ckpt /tmp/rl_v6_r0/agent.pt --max-k 64
```

`--gdim/--edim/--emax` override the defaults (16 / 48 / 24). If stream
A's emitter ever exceeds 24 entities the handshake will say so and name
the flag; that is a buffer change, not a retrain.
