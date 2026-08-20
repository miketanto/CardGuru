# Encoding design — entities as rows, and consequences as candidates

Prompted by "we are not giving the agent enough nuanced information to
learn the nuances of the game", and specifically: a 2/2 with ability X
must not look like a 2/2 with ability Y, and the board has to be
readable as a set of distinct cards rather than a total.

This note does three things: reports what the comparable literature
actually encodes, records a finding about what this repo already has,
and proposes a design for the board, the stack and targeting.

**Sourcing.** `rl/COMBAT-LITERATURE.md` was written when the egress
policy blocked arxiv; it still does, along with `annals-csis.org`,
`huggingface.co` and `ronaldo.games`. GitHub is reachable, so the LOCM
numbers below are read from the **implementation source**, which is
authoritative for an encoding question. The Hearthstone numbers come
from search-engine summaries of papers I could not fetch and are marked
as such — treat them as the shape of the approach, not as quotable
figures.

---

## 1. What LOCM encodes (read from source, exact)

`gym-locm` — the reference environment for Legends of Code and Magic,
used by the competition agents.

**Every card is a row of 16 features** (17 in LOCM 1.5), in this order,
from `LOCMEnv.encode_card`:

| features | what |
|---|---|
| 4 | card type, one-hot: Creature / GreenItem / RedItem / BlueItem |
| 1 | `cost / 12` |
| 1 | `attack / 12` |
| 1 | `max(-12, defense) / 12` |
| **6** | **keywords, one binary flag each: Breakthrough, Charge, Drain, Guard, Lethal, Ward** |
| 1 | `player_hp / 12` |
| 1 | `enemy_hp / 12` |
| 1 | `card_draw / 2` |
| 1 | `area / 2` (1.5 only) |

The battle observation is **20 card slots × 16 features + 8 player
features** — the player's hand, the player's board and the opponent's
board, each card in its own row, **zero-padded with dummy rows** to a
fixed slot count.

`keywords = list(map(int, map(card.keywords.__contains__, "BCDGLW")))`

That single line is the thing being asked for: a 2/2 Guard and a 2/2
Lethal differ in the encoding by a bit that is always present, on the
card's own row, whether the card is in hand or on the board.

## 2. What Hearthstone work encodes (secondary sourcing)

Consistently described as a **flat vector built from per-entity
features**: for each minion on the board its HP, attack, and status
flags (taunt, charge, whether it can attack this turn); per player HP,
weapon, mana, hero; per card in hand type and cost; plus global features
(turn, cards in deck). One state-evaluation network is reported at
**750 input dimensions** feeding dense layers of 256 / 128 / 64 with
tanh.

The number to take from this is not 750. It is that **no one aggregates
the board.** Both games give every minion its own slots and every
keyword its own bit.

## 3. What we encode, and the finding

Our entire battlefield is **six scalars** — `s[8..13]`: creature count,
total power, total toughness, per side. On the W0Base pool that makes
86% of three-creature boards and 97% of five-creature boards share an
encoding with a *different* board (`ATTACK-JOINT-RESULT.md` §6c).

**But the per-card representation already exists in this repo and is
not wired to the board.**

`rl/e2_extract.py` emits `rl/e2_features.tsv`: a **68-dimension
mechanical feature vector per card**, a pure readout of the Forge
ability graph — no text embeddings, no learned parts. It carries:

- 9 answer-class flags,
- 20 effect-API flags (DealDamage, Destroy, Counter, ChangeZone, Pump,
  Draw, Token, DestroyAll, …),
- **18 keyword flags — Flying, Haste, Deathtouch, Lifelink, First
  Strike, Double Strike, Trample, Vigilance, Flash, Menace, Reach,
  Defender, Ward, Hexproof, Shroud, Protection, Prowess, Ninjutsu**,
- trigger flags (ETB, death, attacks, spellcast, damage, phase),
- static / replacement / activated flags,
- **targeting flags (`tgt_creature`, `tgt_player_or_any`, `tgt_spell`)**,
- damage and pump magnitudes, type flags, recursion, multi-face.

Where it is used: `identity()`, called from `forCard`, `forCombat` and
`forTargetPermanent` — i.e. **only to identify a single card inside a
candidate.** `encodeState` never calls it. Grep confirms zero
references in the state path.

So we are not missing the vocabulary that distinguishes a 2/2 Flier from
a 2/2 Deathtoucher. We built it, tested it as an encoder ablation, and
then described the board with sums anyway. **The gap is plumbing, not
research.**

One honest caveat before anyone over-invests: **at rung 0 every keyword
flag is zero.** W0Base is vanilla bodies, so per-card ability features
buy exactly nothing there. What per-creature ROWS buy at rung 0 is the
P/T multiset — the collision above — which is real but smaller. The
ability half of this work pays from **rung 1** (keywords) and the stack
half from **rung 4–5** (instants, tricks). Design now, validate where it
can actually move a number.

---

## 4. The design

One principle, applied three times, and half of it is already proven
here: **entities get rows; decisions get consequences.**

The afterstate half is the part this project already discovered —
`forAssignment` and `forAttackSet` describe a choice by its simulated
outcome rather than by its cards, and §6c shows that is why the lossy
state has cost nothing measurable so far. The half that is missing
everywhere is the first: nothing in the state is an entity.

### 4a. Board — per-creature rows

Two blocks of `N` slots (mine, theirs), each row:

| group | features | notes |
|---|---|---|
| body | power, toughness, damage marked, base P/T if modified | damage marked is currently invisible and decides every combat |
| status | tapped, summoning-sick, attacking, blocking, can-attack, can-block | `s[28]` today is a COUNT of untapped creatures |
| combat keywords | flying, reach, first strike, double strike, deathtouch, trample, vigilance, menace, defender, lifelink, indestructible, ward, hexproof | a subset of the 18 already extracted |
| identity | the E2 vector, or a learned embedding | see the open question below |
| occupancy | 1 if the slot holds a creature | zero-padding, as LOCM does |

`N = 8` per side covers rung 0–3 boards with headroom; overflow needs a
counted, documented rule, not silent truncation.

### 4b. Stack — ordered slots, described by what resolving does

Today the stack is 4 numbers: depth, top-is-mine, top mana value,
top-is-instant. A Lightning Bolt and a Wrath of God differ in one of
them.

Proposed: `K = 4` slots in LIFO order, each carrying the E2 vector of
the spell plus **resolution features** — who it targets (me / my
creature / their creature / a spell), and, at rungs where resolution is
deterministic, the simulated result: does the target die, how much
damage where, how much material is destroyed. That is the same
afterstate move that made blocks learnable, applied to the stack.

Order matters and is information: slot 0 resolves first.

### 4c. Targeting — the candidate is the effect, not the target

`forTargetPermanent` currently sends: is-creature, power, toughness,
is-mine, plus identity. It describes the **target** and says nothing
about what the spell does to it, and nothing about the spell at all.

Proposed: a target candidate carries the simulated consequence — target
dies / survives, material destroyed, damage prevented or dealt, whether
it removes a lethal attacker, whether it is my best creature — plus the
source spell's E2 vector, plus legality friction (ward cost, hexproof,
protection, shroud, all already extracted).

---

## 4d. The network, adapted from the ByteRL-style architecture

Working from the architecture diagram directly (the primary PDF is
behind the same egress block as arxiv, so this reads their figure, not
their text).

**What that design does, stripped to its load-bearing parts:**

1. **One shared card embedder, reused in every zone.** The same pink
   "cards embed" block feeds hand, board, deck and graveyard. A card is
   encoded the same way wherever it is — which is why a card in hand and
   the same card on the board are recognisably the same object.
2. **Per-zone pooling, then concatenate.** Each zone becomes one
   embedding (`mean` over the set for deck and graveyard), and the zone
   embeddings concatenate into one state embedding.
3. **Actions scored by inner product against the state embedding**, with
   a legality mask.
4. **An LSTM over the state embedding**, feeding the value head.
5. **An explicit decision-type embedding** as an input.

**We already have 3, 4 and 5.** The policy server scores
`[state_emb ‖ cand_emb]` per candidate over a masked variable-length
candidate set, `--arch lstmattn` is recurrent, and `T_PASS / T_LAND /
T_SPELL / T_TARGET / T_ATTACK / T_BLOCK` is a decision-type one-hot in
every candidate. **What we are missing is 1 and 2** — the entire left
half of that diagram. Our state path is hand-rolled scalars where theirs
is a set of embedded cards.

That is a good position to be in: the change is confined to the state
path, and the candidate/action path stays as it is.

### The mapping

| ByteRL (Hearthstone) | MTG / CardGuru |
|---|---|
| hero embed | player: life, lands, untapped mana |
| weapon embed | no analogue — nearest is equipment/auras, see relations below |
| hero power embed | nothing at rung 0 |
| my / oppo board cards | battlefield, per-permanent rows |
| my hand cards | my hand exact; **theirs is hidden — size only** |
| deck cards → mean | library. Note rungs 0–3 use a FIXED decklist, so this is nearly free information |
| graveyard → mean | graveyard, pooled |
| decision type embed | already have it |
| action embed → inner product | already have it (our candidates) |
| BT action mask | already have it (we only send legal candidates) |
| CB policy (pre-game card selection) | no analogue until deckbuilding; ignore |
| — | **the stack** — MTG-only, and ordered |
| — | **joint block / attack assignments** — our afterstate candidates |

### Three places the adaptation is not a copy

**Mean pooling would reintroduce the exact bug we are fixing.** The mean
of one 2/2 and the mean of three 2/2s are identical. Hearthstone can
pool a 7-slot board because board size is bounded and passed elsewhere;
if we pool an unbounded battlefield we must use **sum**, or mean
concatenated with a count. Getting this wrong rebuilds `s[8..13]` with
extra steps.

**The stack is ordered and pooling destroys the order.** Resolution is
LIFO and the order is the information — a removal spell on top of a pump
spell is a different position from the reverse. The stack wants a small
sequence encoder or explicit positional slots, not a set pool.

**MTG is relational in a way Hearthstone mostly is not.** Which creature
an aura is attached to, which attacker a blocker is assigned to, what a
spell on the stack is pointing at — these are POINTERS between entities,
and both pooling and concatenation flatten them away. This is the real
argument for **attention over the entity set** rather than per-card MLP
plus pool: attention can represent "this blocker relates to that
attacker" as a learned edge. Combat is the relational problem in this
game, so the relational structure should survive the encoder.

That also settles open question 1 below in favour of a set/attention
encoder over fixed ordered slots — with the caveat that attention is
strictly more machinery to get wrong, and the pooling variant is the
cheaper first step if we want a result sooner.

## 5. What this costs

- **Every existing checkpoint dies.** `STATE_DIM` moves from 32 to
  roughly 400–1000, so nothing trained at 32/94 loads. The whole v1–v5
  ladder becomes historical. That is a deliberate re-baseline and should
  be taken once, not twice.
- **Sample efficiency gets worse before it gets better.** A wider input
  with the same 512-episode budgets is a smaller signal per parameter.
  Budgets that were adequate for a 32-dim state are not obviously
  adequate for a 400-dim one.
- **The measurement problem does not go away.** §6c: a richer state
  changes nothing the current one-combat reference can see, because the
  reference's answer is a linear function of the candidate features. A
  better encoding needs the k-turn reference to be visible at all.

---

## 6. Open questions

1. **Slots or a set encoder?** Largely settled by §4d: a set encoder
   removes the ordering question by construction (no card-name sort for
   W0Twin to catch) and generalises past a fixed board size, and
   attention preserves the entity-to-entity relations that combat is
   made of. The live sub-question is whether to start with cheap
   sum-pooling and add attention later, or build attention once.
2. **Full 68-dim identity per creature, or a combat subset?** 68 × 16
   slots is 1088 dims of mostly-zero for rung 0–3, where the effect and
   answer flags are all zero. A ~20-dim combat subset now, widening at
   rung 4, is cheaper and testable sooner.
3. **Does the opponent's hand get anything beyond size?** At rungs 0–3
   there are no tricks, so their hand may genuinely be worth one
   integer. Mine is not — it decides whether a trade is cheap or
   ruinous, and it is one integer today.
4. **Which rung validates it?** Rung 0 cannot: every keyword flag is
   zero there. Rung 1 is the first place the ability half can move a
   number, and it needs `CombatMath` extended for keywords first —
   which is already flagged as a hard prerequisite.

---

## 7. Sources

- `gym-locm` (Vieira, Tavares, Chaimowicz) — `LOCMEnv.encode_card` and
  `_encode_state_battle`, read from source:
  https://github.com/ronaldosvieira/gym-locm
- Hearthstone state-evaluation and RL work — secondary summaries only,
  primary PDFs blocked by egress. Treat figures as indicative.
- `rl/e2_extract.py`, `rl/e2_features.tsv`, `rl/xmage-src/StateEncoder.java`
  — this repo.
- `rl/ATTACK-JOINT-RESULT.md` §6c — the collision measurements and the
  proof that the state is currently irrelevant to the measured objective.
