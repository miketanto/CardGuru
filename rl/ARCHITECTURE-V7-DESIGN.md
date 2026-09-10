# Architecture v7 — design, not yet built

*2026-09-10. Companion to `ARCHITECTURE.md` (what exists). This records the
design as agreed in discussion; §6 lists the decisions still open. Nothing
here has been measured.*

## 0. Principles agreed

1. **Description, not prediction.** The encoder's job is to describe the
   game state faithfully; the policy does the heavy lifting. No auxiliary
   prediction heads. Faithfulness is checked by *probes that are never
   trained into the net*: can a small readout recover every input field
   and every edge from the tokens after the encoder.
2. **Engine describes, policy decides.** Where a fact is computable, the
   engine computes it and emits it as a feature (the joint-block
   afterstates are the precedent that worked). The net is not asked to
   learn combat arithmetic from a win bit.
3. **Information-preserving until the decision point.** Tokens reach the
   scorer. No sum-pool into one vector, no single state token in front of
   the candidates. The only lossy summary is memory, and it is bounded
   and inspectable.
4. **One shared card embedder, learned outside the RL loop**, versioned,
   frozen inside a run, improved across runs. Same embedding for a card
   in hand, on the board, on the stack, and on the menu.
5. **"Not easily saturated" means the signal, not the width.** The
   policy is sized for a data regime two orders of magnitude above
   anything run here; the league, deck diversity and engine throughput
   are part of the same programme, not a later phase.

## 1. Layers

```
L0  card embedder        offline, versioned artifact   card -> e_card (d_c)
L1  deck context         once per game                 60 cards -> c'_i (contextual), D (deck vector)
L2  operators & fields   per consult, engine side      entity -> feature row; candidate -> afterstate row
L3  token builder        per consult, server side      [c' | fields | operators] -> d
L4  state-graph encoder  per consult                   one transformer, typed edges, no pooling
L5  memory               per consult                   last H game tokens as history tokens
L6  heads                per consult                   pointer scorer on candidates; separate value trunk
```

### L0. Card embedder (`card_emb_vN`)

Inputs, three channels concatenated then projected to `d_c` (128):

| channel | source | how |
|---|---|---|
| oracle text | Forge cardsfolder (33k cards) | sentence encoder; numbers bucketed, never left raw |
| graph fingerprint | CardGuru ability graph: answer classes, effect APIs, triggers, targets, synergy hooks | graph encoder over the ability tree, or the readout vector as v1 |
| printed fields | MV, colours, types, supertypes, P/T, loyalty | explicit channels, so a linear probe recovers them exactly |

Objective (outside RL): text↔graph contrastive first; masked-card-in-deck
second (shared with L1). Tokens and unseen cards go through the text
channel. Gates before use: field recovery by linear probe; Spell Snare /
Force Spike apart, Cancel / Counterspell together, functional reprints
nearest; same probes on a 10% held-out card set.

Inside a run: frozen, plus one trainable `Linear(d_c -> d_c)` adapter.
Refit across runs on the aggregate of decklists and dumped game text; a
new version is a new artifact and every checkpoint records which one it
was trained against.

### L1. Deck context (once per game)

Transformer over the 60 `e_card` (copy count as a feature, no positions),
relation bias from the fingerprint's enabler→payoff edges. Outputs:

- `c'_i` per card: the card *in this deck*. Replaces `e_card` as the
  card's identity wherever it appears during the game.
- `D`: pooled deck vector, joins the game token.

Opponent's deck: v1 = known decklist (true at every rung today).
Principled version = context over revealed cards, growing during the
game (§6).

Pretraining: masked-card-in-deck over the decklist corpus. Gate: a linear
head reads wincon / enabler / answer off `c'_i` against the fingerprint's
own role labels.

### L2. Operators and extracted fields (engine side, per consult)

"Operator" = an engine function applied to an entity or a candidate whose
result is emitted as a feature. All of these exist in XMage; the work is
emission, not computation.

**Entity fields** (every card-backed entity, any zone):

| group | fields |
|---|---|
| where | zone one-hot · mine/theirs · face-down · position in stack |
| body now | current P/T *after continuous effects* · printed P/T · damage · toughness remaining · loyalty |
| counters | +1/+1 · −1/−1 · loyalty · other (count) |
| status | tapped · summoning-sick · attacking · blocking · entered-this-turn · token · turns on battlefield |
| abilities now | keyword bits *after* granted/lost abilities (from the engine, not the card table) |
| operators | castable now · mana left if cast · legal targets available (count) · can attack · can block · would die to SBA as-is |
| stack only | chosen modes · X value · targets (as edges) · controller |

**Player tokens:** life · poison · hand size · library size · mana pool by
colour · untapped sources by colour · lands · cards drawn this turn.

**Game token:** turn · step one-hot · active player · priority holder ·
stack depth · `D_me` · `D_opp`.

**Candidate rows** (afterstates, as today, extended):

| type | operator output |
|---|---|
| cast / activate | mana left after · targets legal now · speed (instant / sorcery / flash) · goes on stack above N objects |
| target | the entity index (an edge, see below), nothing hand-rolled |
| attack subset | `CombatMath.AttackOption` as today |
| block assignment | `CombatMath.Outcome` as today |
| pass | pass afterstate: what resolves and what the engine would do next (§6, optional in v1) |

**Edges** (typed, directed; the index is the wire contract, append only):

| type | edge |
|---|---|
| controls | player → permanent |
| attached_to | aura / equipment → host |
| blocks · blocked_by | blocker ↔ attacker |
| attacking | attacker → defending player |
| targets | stack object → target |
| can_block | legal blocker → attacker (engine legality, during declare-blockers) |
| stack_above | stack object → the object directly below it |
| refers_to | **candidate → every entity it acts on** (the card to cast, the target, the attackers in the subset, the blockers in the assignment) |

`refers_to` is the edge that removes the single-token bottleneck: a
candidate token attends to the entities it would touch.

### L3. Token builder (server side)

```
entity token    = W_e [ c'_card | fields | operators ]           (d = 256)
player token    = W_p [ player fields ]
stack token     = W_s [ c'_source | modes | depth embedding ]
game token      = W_g [ globals | D_me | D_opp ]
candidate token = W_c [ type embedding | afterstate row ]          + refers_to edges
history token   = game token output from consult t−k, + relative-time embedding, k = 1..H
```

No sum, no mean, no pooling. Padding is masked.

### L4. State-graph encoder

One transformer over
`[game | players | entities | stack | candidates | history]`,
sequence ≈ 1 + 2 + 96 + 8 + 96 + 8 ≈ 210 tokens. `d` 256, 8 heads, 6
layers, FFN 1024, pre-LN. Attention bias = learned per-(edge type, head)
scalar as v6, plus a small edge-feature MLP if a graded relation is ever
needed. Stack order via `stack_above` edges and the depth embedding.

Faithfulness probe (not a loss): from the output tokens, recover every
input field and every edge with a linear readout. This is the acceptance
gate for "describes the state well".

### L5. Memory

History tokens: the game token's output from the last H consults, with a
relative-time embedding, stored per session and reset per episode. This
replaces the LSTM cell. Inspectable (attention weights over history say
what the policy looked back at), bounded (H is a buffer), and trained by
the same PPO gradient through the current consult only.

v7.0 may keep the LSTMCell on the game token while H is tuned.

### L6. Heads

- **Policy**: pointer scorer, `MLP(d → 64 → 1)` on each candidate token,
  masked softmax over K. One head for every decision type, as today.
- **Value**: **separate trunk**. A second, smaller copy of L3–L4 over
  `[game | players | entities | stack]` (no candidates), value head on the
  game token. Privileged rows (opponent hand, `-Drl.oracle`) enter here
  and only here, as today's `OracleCritic`. Separate so no value gradient
  reshapes the policy's features and no privileged bit reaches a logit.

### Parameter budget (estimate)

| part | params |
|---|---|
| L4 policy trunk, 6 × (4d² + 8d²) at d 256 | ≈ 4.7 M |
| L6 value trunk, 4 layers | ≈ 3.1 M |
| token builders, heads, edge bias | ≈ 0.3 M |
| L1 deck context, 2 layers at d_c 128 | ≈ 0.4 M |
| L0 card embedder | outside the run |
| **total inside a run** | **≈ 8.5 M** (v6: 0.72 M) |

Sequence ≈ 210 tokens at d 256 is trivial on the GPU; the play phase is
engine-bound (THROUGHPUT-LOCAL.md), so the net is not the cost.

## 2. Training

PPO (or V-trace) from terminal reward only. No shaping, no auxiliary
losses. What changes is the data regime, and it is part of this design:

- deck diversity from episode one (L1 is a constant otherwise);
- a league with opponent sampling, not a frozen opponent;
- episode counts two orders of magnitude above the current lanes, which
  makes engine throughput a prerequisite (`PHASE12-PERF-SCOPE.md`,
  `ENGINE-REWRITE-FEASIBILITY.md`).

## 3. What is engine-side vs server-side

| engine (Java, `StateEncoder` / `RLPlayer`) | server (Python, `policy_server.py`) |
|---|---|
| emit card *identity* (name or id) per entity, not features | look up `e_card` / `c'` by id |
| emit L2 fields and operator outputs | build tokens (L3) |
| emit edge list incl. `refers_to` and `stack_above` | encoder, heads, PPO |
| afterstate operators (`CombatMath`, pass afterstate) | deck context once per game, on the decklist |
| optional privileged rows | value trunk |

The wire changes from "features per row" to "identity + fields per row";
the card table leaves the JVM entirely.

## 4. Order of work

1. **L0** card embedder + gates (2–3 days). Needs the graph dataset
   regenerated (`data/dataset.jsonl.gz` is absent from the WSL checkout)
   and a sentence-encoder download path through the proxy.
2. **L1** deck context + masked-card pretraining + role probe (2 days).
   Needs the decklist corpus counted.
3. **L2** emission: identity, fields, operators, edges (3–4 days Java).
4. **L3–L6** server (3 days), with `entattn_check`-style invariance
   checks and the faithfulness probe as the gate.
5. Throughput and league work in parallel, because step 6 is pointless
   without them.
6. RL, with the behaviour-counter suite pre-registered.

## 5. Pre-registration (what v7 cannot do)

- Cannot move any existing checkpoint (new wire, new nets).
- Cannot beat v6 on rungs 0–3 by more than noise on win rate: those decks
  have nothing the extra description can act on. The v6 null is the
  prediction for v7 in that regime; a win-rate move there is a bug.
- The first honest readout is the faithfulness probe, then behaviour
  counters on a deck whose spells carry value, then win rate against the
  held-out XMage AI.

## 6. Open decisions

1. `d_c` and frozen-plus-adapter vs fine-tuned embedder inside a run.
2. First pretraining objective: text↔graph contrastive vs masked-card.
3. Opponent deck: known list (v1) vs revealed-only context.
4. Pass afterstate in v1, or deferred (needs a simulation harness).
5. LSTM kept for v7.0, or history tokens from the start.
6. Value trunk depth, and whether it shares L3 token builders.
7. Target episode scale, which sets the engine throughput target.
