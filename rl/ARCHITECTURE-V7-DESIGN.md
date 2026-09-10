# Architecture v7 — design, not yet built

*2026-09-10. Companion to `ARCHITECTURE.md` (what exists). This records the
design as agreed in discussion; §6 lists the decisions still open. Nothing
here has been measured.*

## 0. Principles agreed

1. **Description, not prediction.** The encoder's job is to describe the
   game state faithfully; the policy does the heavy lifting. No auxiliary
   prediction heads on the policy trunk. Faithfulness is checked by
   *probes that are never trained into the net*: can a small readout
   recover every input field and every edge from the tokens after the
   encoder. **One exception, decided 2026-09-10:** a separate belief
   module (§8) predicts hidden cards from self-play labels; its outputs
   are features the policy consumes, and its loss never reaches the
   policy's parameters.
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

Objective (outside RL), **both, and deliberately GPU-intensive**: the
text encoder is fine-tuned jointly with a graph encoder over the ability
tree (not a frozen sentence encoder with a linear layer on top) on
text↔graph contrastive first, then masked-card-in-deck (shared with L1),
for hours on the local GPU over the 33k-card corpus. Tokens and unseen
cards go through the text channel. Gates before use: field recovery by linear probe; Spell Snare /
Force Spike apart, Cancel / Counterspell together, functional reprints
nearest; same probes on a 10% held-out card set.

Inside a run: **frozen**, plus one trainable `Linear(d_c -> d_c)` adapter
(decided; improved across runs, never within one).
Refit across runs on the aggregate of decklists and dumped game text; a
new version is a new artifact and every checkpoint records which one it
was trained against.

### L1. Deck context (once per game)

Transformer over the 60 `e_card` (copy count as a feature, no positions),
relation bias from the fingerprint's enabler→payoff edges. Outputs:

- `c'_i` per card: the card *in this deck*. Replaces `e_card` as the
  card's identity wherever it appears during the game.
- `D`: pooled deck vector, joins the game token.

Runs twice: my deck, and the opponent's deck as far as it is known (§8):
the open decklist, or the archetype posterior's candidate lists when the
list is closed. The opponent's remaining-deck tokens are its output.

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
stack depth · **decision-type embedding for this consult** (ByteRL §7) ·
`D_me` · `D_opp`.

**Candidate rows** (afterstates, as today, extended):

| type | operator output |
|---|---|
| cast / activate | mana left after · targets legal now · speed (instant / sorcery / flash) · goes on stack above N objects |
| target | the entity index (an edge, see below), nothing hand-rolled |
| attack subset | `CombatMath.AttackOption` as today |
| block assignment | `CombatMath.Outcome` as today |
| pass | pass afterstate: what resolves and what the engine would do next — **deferred** (§6), needs a simulation harness |

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

Each token type has its own **per-token MLP**, not a single linear
projection: a linear map can only re-weight channels, and "a 2/2 with a
+1/+1 counter, tapped, lethal damage marked" is a nonlinear fact that
should exist before attention sees it (ByteRL's per-zone fully connected
stage is the precedent).

**Shared identity in, zone-specific MLP out.** The identity input `c'`
is the same vector wherever the card is, so the net knows it is one card.
The MLP is **separate per zone** (hand, battlefield, stack, graveyard,
exile, known library), because the card *means* something different in
each: Lightning Bolt in hand is a potential 3 damage for R, on the stack
it is 3 damage committed to a target, in the graveyard it is an instant
that feeds delirium or a recursion target. One shared MLP with a zone
flag would have to carry all three meanings in one set of weights, and at
rungs where a zone never matters it would never learn that zone's
meaning at all. A card that changes zone is re-embedded by the new
zone's MLP from the same identity. Six zone branches ≈ 2.4 M params.

```
MLP_z(x) = Linear(512 → 256)( GELU( Linear(in → 512)( LN(x) ) ) )      one per zone z / token type

entity token    = MLP_zone [ c'_card | fields | operators ]              (d = 256)
player token    = MLP_p [ player fields ]
stack token     = MLP_s [ c'_source | modes | depth embedding ]
game token      = MLP_g [ globals | D_me | D_opp ]
candidate token = MLP_c [ type embedding | afterstate row ]              + refers_to edges
opp hand slot   = MLP_oh [ c' if known else unknown vector | origin | age | seen ]        (§8)
opp remaining   = MLP_od [ c'_opp | count remaining | castable with their open mana ]      (§8)
opp action      = MLP_oa [ action type | consult age ]                   + refers_to edges  (§8)
history token   = game token output from consult t−k, + relative-time embedding, k = 1..H
```

No sum, no mean, no pooling. Padding is masked. The faithfulness probe
(§L4) is applied after this stage too, so the MLP is shown not to discard
input fields.

### L4. State-graph encoder

One transformer over
`[game | players | entities | stack | candidates | opp hand slots | opp remaining deck | opp actions | history]`,
sequence ≈ 1 + 2 + 96 + 8 + 96 + 7 + 60 + 8 + 8 ≈ 290 tokens. `d` 256, 8 heads, 6
layers, FFN 1024, pre-LN. Attention bias = learned per-(edge type, head)
scalar as v6, plus a small edge-feature MLP if a graded relation is ever
needed. Stack order via `stack_above` edges and the depth embedding.

Faithfulness probe (not a loss): from the output tokens, recover every
input field and every edge with a linear readout, and from the game
token alone recover the count of candidates of each decision type (the
state must know what it can do this step, §7). This is the acceptance
gate for "describes the state well".

### L5. Memory

History tokens: the game token's output from the last H consults, with a
relative-time embedding, stored per session and reset per episode. This
replaces the LSTM cell. Inspectable (attention weights over history say
what the policy looked back at), bounded (H is a buffer), and trained by
the same PPO gradient through the current consult only.

**v7 keeps the LSTMCell on the game token** (decided; ByteRL's placement,
which worked at scale). History tokens are a later experiment, gated on
the LSTM arm.

### L6. Heads

- **Policy**: pointer scorer on each candidate token plus a bilinear
  state–action term (ByteRL §7):
  `score_k = MLP(d → 64 → 1)(c_k) + ⟨W_a c_k, W_s g⟩`, with `g` the game
  token's output; masked softmax over K. One head for every decision
  type, as today.
- **Value**: **separate trunk**, fully isolated: its **own copies of the
  L3 token builders** and a **4-layer** L4 over
  `[game | players | entities | stack | opponent tokens]` (no candidates),
  value head on the game token. Privileged rows (the true opponent hand,
  `-Drl.oracle`) enter here and only here, as today's `OracleCritic`.
  Separate so no value gradient reshapes any policy feature and no
  privileged bit reaches a logit.

### Parameter budget (estimate)

| part | params |
|---|---|
| L4 policy trunk, 6 × (4d² + 8d²) at d 256 | ≈ 4.7 M |
| L6 value trunk, 4 layers | ≈ 3.1 M |
| L3 per-zone / per-type MLPs (≈ 9), heads, edge bias | ≈ 3.0 M |
| L1 deck context, 2 layers at d_c 128 | ≈ 0.4 M |
| L0 card embedder | outside the run |
| **total inside a run** | **≈ 11 M** (v6: 0.72 M) |

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

## 6. Decisions (resolved 2026-09-10)

| # | question | decision |
|---|---|---|
| 1 | embedder inside a run | **frozen + linear adapter**; improved across runs, never within one |
| 2 | first pretraining objective | **both, GPU-intensive**: fine-tune the text encoder jointly with a graph encoder; contrastive first, then masked card in deck |
| 3 | opponent deck | **open decklist in v1**; archetype posterior for closed lists later |
| 4 | pass afterstate | **deferred** until a simulation harness exists |
| 5 | memory | **LSTM on the game token**; history tokens later, gated on the LSTM arm |
| 6 | value trunk | **fully separate**: own token-builder copies, 4 layers (recommendation, recorded pending objection) |
| 7 | target episode scale | **after the embedder succeeds**; throughput target and league design follow |
| 8 | belief | **learned hidden-card belief module** on self-play labels, reading the deck-context posterior and (later) the archetype posterior; a separate module whose outputs are policy features, §8a |

## 7. Mapping from the ByteRL Hearthstone BT policy (arXiv 2303.05197)

Read from the architecture figure the user supplied 2026-09-10.

| ByteRL | what it does | v7 |
|---|---|---|
| one `cards embed` for hand, board, deck, graveyard | shared card identity across zones | L0 embedder + L1 context; same object in every zone |
| `fc×2` per zone after the embed | per-card nonlinearity before the state, zone-specific | L3 per-zone MLP over a shared identity input (adopted as is; zones are token sets, not fixed slots) |
| deck / graveyards → `mean` | unbounded zones pooled | deck → L1 transformer + `D`; graveyards stay tokens |
| hand / board → concatenated slots | bounded at 10 / 7 | tokens with masking; Magic's board is unbounded |
| `decision type → fc → decision embed` into the state | state knows which decision this is | **added** to the game token |
| `action embed → masked mean → fc×2` into `BT embed` | state knows the legal action set | candidates are tokens in the same attention; **probe**: game token reports candidate counts per type |
| `BT embed → fc×3 → LSTM`; value off `LSTM embed` | memory on the state; shared value | LSTM on the game token in v7.0; value from a **separate** trunk (privileged rows) |
| `inner product(fc(action), fc(LSTM embed))` | bilinear state–action scorer | **added** as a term beside the pointer MLP |
| `BT embed` is one vector; actions see the state only through it | the single-token bottleneck | not adopted; `refers_to` edges give each candidate its entities' context |
| (type, target) autoregressive decomposition | conditions the target on the type | not needed: joint afterstate candidates + refers_to edges |
| 24 V100 · ~5,856 CPU cores | scale | the throughput programme (§2) |

## 8. Opponent modelling

The principle is unchanged: **the engine describes what the agent legally
knows; belief is what the policy computes by attending over that
evidence.** Most of "belief" has a descriptive sufficient statistic if the
right things are emitted.

| tier | what the agent knows | tokens |
|---|---|---|
| public zones | opponent battlefield, graveyard, exile, stack | entity tokens, as now |
| **opponent hand, per slot** | each card in their hand is an object with a history: kept from the opening hand, drawn this turn, returned from a public zone (known), revealed (known), tutored | one token per slot: `c'` if known else an unknown-identity vector · origin · age in turns · seen flag |
| **opponent deck, remaining** | open list: decklist minus every card seen so far, which is exactly the sufficient statistic for the belief over their hand and library. Closed list: seen cards → CardGuru metagame / fingerprint → archetype posterior → candidate lists | one token per distinct remaining card: `c'_opp` · count · **castable with their open mana now** (instant-speed threat as description, not a guess) |
| **opponent behaviour this game** | their recent decisions: cast X, attacked with Y, declined to block, passed with mana up | opponent-action history tokens with `refers_to` edges into the entities involved |

Behavioural modelling is within-game only. A cross-game opponent
embedding (league id) would be absent at evaluation against an unknown
opponent, so the policy is not allowed to depend on one.

**Engine side: a knowledge tracker** in the RL player that consumes game
events (reveals, zone changes into the hand from public zones, tutors,
look-at effects, known top of library, face-down objects) and keeps, per
card id, what the agent legally knows. XMage holds the ground truth, so the
emitter applies visibility rules and is **gated for leaks** exactly as the
oracle channel is (`oracle_gate.py` levels 1–2: policy logits invariant to
hidden information).

**Value trunk** keeps the privileged ground truth (`"oe"`). The policy gets
the tracked information state only.

**Faithfulness probe additions:** from the tokens, recover the set of known
opponent cards, the remaining-deck multiset, and the count of opponent
cards castable at instant speed with their current mana.

### 8a. The belief module (decided 2026-09-10: build it)

A **separate module**, not a head on the policy trunk, so principle 1
survives with one named exception.

| | |
|---|---|
| reads (legal information only) | the opponent's deck-context tokens (L1, open list in v1; the archetype posterior's candidates when the list is closed), the opponent hand-slot tokens, the opponent-action history, the game token |
| architecture | 2-layer transformer over those tokens, d 256 |
| outputs | per hand slot: a distribution over the remaining-deck tokens (pointer softmax, slot × card); per remaining card: P(in their hand) and P(next draw) |
| where the outputs go | attached as **features** to the opponent hand-slot and remaining-deck tokens before the L4 encoder (and to the value trunk's copies) |
| labels | the engine's ground truth from self-play (`-Drl.oracle` already emits the true hand); cross-entropy per slot, binary per card |
| training | its own optimiser; **stop-gradient** into the shared token builders, so its loss never reaches a policy parameter |
| leak gate | unchanged and still required: inputs are legal, labels touch only the belief loss; the policy's logits must be invariant to swapping the true hidden cards |
| lifecycle | versioned like the embedder; can be refit across runs on the aggregate of self-play games |
| probe | held-out log-likelihood of the true hand vs the uniform-over-remaining baseline; if it does not beat the baseline the features are noise and are masked out |

Published figure: https://claude.ai/code/artifact/65a42516-315d-4ae9-93b8-ef57f6003af0
