# WIRE-V7 — the consult schema between the engine (`-Drl.encoderV=7`) and the server (`--arch v7`)

*Contract, phase 0a (`V7-IMPLEMENTATION-PLAN.md` §2). Authored by Lane D;
consumed by Lane B (`StateEncoder` / `SocketPolicyClient`, emits) and
Lane C (`policy_server.py`, parses). A change to this file is a commit
that names both. Machine-checked by `rl/wire_validate.py`; synthetic
examples in `rl/fixtures/v7/` from `rl/wire_fixtures.py`. Derived from
`ARCHITECTURE-V7-DESIGN.md` §L2, §L3, §8 and the v6 wire
(`ARCHITECTURE.md` §1).*

## 0. Rules

1. **Framing is unchanged from v6:** one JSON object per line, UTF-8,
   `\n`-terminated; the engine writes `hello`, then per decision one
   `consult` and reads one reply `{"a": <candidate index>}`; at the end
   `{"t":"end","r":<reward>}`. `stats` as in v6.
2. **v6 keys keep their v6 meaning.** A v7 consult carries the v6 keys
   `g`, `e`, `r`, `c`, `oe`, `phi` exactly as `encoderV=6` emits them
   (3a: "v6 content plus identity"), so `entattn_check.py` and any v6
   server can consume a v7 stream by ignoring the new keys. v7 content
   lives under new keys, all prefixed `v7_`, except `wire`.
3. **Every index table in this file is append-only.** New fields go on
   the end of a row; new edge types get the next integer; new token
   groups get new keys. Widths are carried in the hello and checked.
4. **Card identity is by name.** The engine emits the XMage card name
   (plus a token flag); the server resolves it through
   `rl/artifacts/cards_v1/index.json` (`names`: normalised name → face
   id; `A // B` → front face; tokens by name, `token:<script>` exact).
   Unresolved → id −1 → the zero embedding row plus the unknown flag.
   The engine may additionally emit `id` when it has the map; the
   server trusts `id` over `name` when both are present and agree.
5. **Legal information only on the policy path.** Everything outside
   `oe` must be visible to the acting player under the game's rules
   (§8 tracker). `oe` is the critic-only privileged channel, as in v6.
6. **Numbers are floats, normalised as stated** in each table (÷ constant,
   clipped where marked). Booleans are 0/1 floats. Counts that can be
   large carry both a normalised value and, where the table says, a raw
   integer in a parallel integer array.

## 1. Hello

```json
{"t":"hello","mode":"train","episodes":512,
 "sdim":32,"cdim":94,"phi":0,"gdim":16,"edim":48,"emax":96,"rtypes":6,
 "wire":7,"card_emb":"card_emb_v8","d_c":128,
 "v7_dims":{"game":24,"player":16,"ent":64,"cand":40,"opp_hand":8,"opp_deck":6,"opp_action":8},
 "v7_rtypes":8,"v7_ctypes":8,"v7_zones":7,
 "v7_emax":160,"v7_kmax":96,"v7_ohmax":12,"v7_odmax":64,"v7_oamax":16}
```

- `wire` is **7**; a server started with `--arch v7` refuses any hello
  without `"wire":7` and any v7 hello whose `v7_dims`, `v7_rtypes`,
  `v7_ctypes`, `v7_zones` or `card_emb` disagree with its own, with the
  reason in the reply (`{"ok":0,"err":"..."}`), as v6 does.
- `card_emb` names the embedder artifact the server will look ids up
  in; the engine copies the value of `-Drl.cardEmb` (default
  `card_emb_v8`) so a mismatch is visible in one place.
- `v7_*max` are buffer sizes (padded, masked, no weights); `v7_dims`,
  `v7_rtypes`, `v7_ctypes`, `v7_zones` are meaning.
- v6 fields (`sdim … rtypes`) stay as they are.

## 2. Consult

```json
{"t":"consult",
 "g":[…16], "e":[[…48],…], "r":[[s,d,t],…], "c":[[…94],…], "oe":[[…],…], "phi":0.0,
 "wire":7,
 "v7_game":[…24],
 "v7_players":[[…16],[…16]],
 "v7_ent_name":["Lightning Bolt", …], "v7_ent_token":[0,…], "v7_ent_id":[…] ,
 "v7_ent":[[…64],…],
 "v7_edges":[[s,d,t],…],
 "v7_cand_type":[0,2,…], "v7_cand":[[…40],…], "v7_cand_refers":[[…],…],
 "v7_opp_hand":[[…8],…], "v7_opp_hand_name":[null,"Counterspell",…],
 "v7_opp_deck":[[…6],…], "v7_opp_deck_name":["Island",…],
 "v7_opp_actions":[[…8],…], "v7_opp_action_refers":[[…],…],
 "v7_ctr":{"entityTrunc":0,"unknownId":0}}
```

Array lengths: `v7_ent`, `v7_ent_name`, `v7_ent_token` (and `v7_ent_id`
if present) are equal, ≤ `v7_emax`; `v7_cand*` equal, ≥ 1, ≤ `v7_kmax`;
`v7_opp_hand*` equal, ≤ `v7_ohmax`; `v7_opp_deck*` equal, ≤ `v7_odmax`;
`v7_opp_actions` / `_refers` equal, ≤ `v7_oamax`. `v7_ent_id` is optional
(rule 4); `v7_opp_*` are optional until 3d lands (absent = empty).

### 2a. Token index space (for `v7_edges` and `*_refers`)

| index | token |
|---|---|
| 0 | game token |
| 1 | player token: me |
| 2 | player token: opponent |
| 3 … 2 + N_ent | entity tokens, in `v7_ent` order |

Candidates, opponent hand slots, remaining-deck and action tokens are
**not** edge endpoints; they reach entities through their own `*_refers`
lists (entity token indices in the same space, i.e. ≥ 3, or 1/2 for a
player).

### 2b. Game token `v7_game` — 24 floats

| idx | field | norm |
|---|---|---|
| 0 | turn | ÷ 30 |
| 1 | I am the active player | 0/1 |
| 2–9 | step one-hot: upkeep · draw · main1 · declare-attackers · declare-blockers · combat-damage · main2 · end | |
| 10 | I hold priority | 0/1 |
| 11 | stack depth | ÷ 4 |
| 12–19 | **decision-type one-hot for this consult**: PASS · LAND · SPELL · ACTIVATE · TARGET · ATTACK · BLOCK · OTHER | |
| 20 | candidates in this consult | ÷ 32 |
| 21 | consults so far this game | ÷ 200 |
| 22 | my deck known to opponent (open list) | 0/1 |
| 23 | opponent deck known to me (open list) | 0/1 |

`D_me` / `D_opp` (deck vectors, design §L1) are **server-side**: the
server computes them once per game from the decklists it is given at
hello time (`v7_decks`, §5) and appends them to the game token itself.

### 2c. Player tokens `v7_players` — 2 × 16 floats, row 0 = me, row 1 = opponent

| idx | field | norm |
|---|---|---|
| 0 | life | ÷ 20 |
| 1 | poison | ÷ 10 |
| 2 | hand size | ÷ 10 |
| 3 | library size | ÷ 60 |
| 4 | graveyard size | ÷ 30 |
| 5 | exile size | ÷ 10 |
| 6–10 | mana in pool W U B R G | ÷ 5 each |
| 11 | colourless / generic mana in pool | ÷ 5 |
| 12 | untapped mana sources | ÷ 10 |
| 13 | lands | ÷ 10 |
| 14 | cards drawn this turn | ÷ 3 |
| 15 | permanents controlled | ÷ 20 |

Untapped sources **by colour** (design L2) are appended in 3b as fields
16–20 (W U B R G, ÷ 5) and the hello `player` width becomes 21; until
then the width is 16.

### 2d. Entity tokens `v7_ent` — 64 floats per row, plus identity arrays

One row per: every permanent (both sides), every stack object, every
card in my hand, every card in both graveyards, every card in both
exiles that is face-up, every card in my library that I legally know
(top revealed etc.). Order: the v6 priority bands, then P/T/MV/order;
truncation from the bottom, counted in `v7_ctr.entityTrunc`.

| idx | group | field | norm |
|---|---|---|---|
| 0–6 | where | zone one-hot: battlefield · hand · stack · graveyard · exile · library-known · command | |
| 7 | | mine | 0/1 |
| 8 | | face-down (identity hidden; name is `"?"`) | 0/1 |
| 9 | | position in stack from the top (0 = top) | ÷ 4 |
| 10–13 | body now | power · toughness *after continuous effects* · damage marked · toughness remaining | ÷ 6 |
| 14–15 | body printed | printed power · printed toughness | ÷ 6 |
| 16 | | loyalty now | ÷ 6 |
| 17 | | mana value | ÷ 6 |
| 18–21 | counters | +1/+1 · −1/−1 · loyalty · other (count) | ÷ 4 |
| 22–29 | status | tapped · summoning-sick · attacking · blocking · entered-this-turn · token · turns on battlefield (÷ 10) · is-creature | |
| 30–33 | type | land · instant · sorcery · other permanent (artifact / enchantment / planeswalker / battle) | |
| 34–51 | abilities now | 18 keyword bits **after** granted/lost abilities, in `rl/e2_extract.py` KEYWORDS order: flying · haste · deathtouch · lifelink · first strike · double strike · trample · vigilance · flash · menace · reach · defender · ward · hexproof · shroud · protection · prowess · ninjutsu | 0/1 |
| 52–57 | operators | castable now · mana left if cast (÷ 6) · legal targets available (÷ 4) · can attack · can block · would die to SBA as-is | |
| 58–61 | stack only | X value (÷ 6) · modes chosen (count ÷ 3) · controller is me · is ability (vs spell) | |
| 62–63 | reserved (0) | | |

`v7_ent_name[i]`: the XMage name (`"?"` when face-down);
`v7_ent_token[i]`: 1 for tokens (the server resolves `name` under the
token namespace first); `v7_ent_id[i]`: optional cards_v1 face id or −1.

### 2e. Edges `v7_edges` — `[src, dst, type]` in the token index space

| type | edge | since |
|---|---|---|
| 0 | blocks: blocker → attacker | v6 |
| 1 | blocked_by: attacker → blocker | v6 |
| 2 | attacking_player: attacker → defending player token (1 or 2) | v6 |
| 3 | targets: stack object → its target (entity or player token) | v6 |
| 4 | controls: player token → permanent | v6 |
| 5 | attached_to: aura / equipment → host | v6 |
| 6 | can_block: legal blocker → attacker (engine legality; emitted only during declare-blockers consults) | v7 (3c) |
| 7 | stack_above: stack object → the object directly below it | v7 (3c) |

`v7_rtypes` in the hello is the count (8). Server-side the list becomes
a dense type matrix over all tokens (0 = none), as in v6.

### 2f. Candidates `v7_cand_type`, `v7_cand`, `v7_cand_refers`

`v7_cand_type[k]` ∈ 0..7: PASS · LAND · SPELL · ACTIVATE · TARGET ·
ATTACK · BLOCK · OTHER (`v7_ctypes` = 8). `v7_cand[k]` is 40 floats; the
first 8 repeat the type one-hot, the rest is the afterstate row for that
type, slots overloaded per type exactly as v6 (`ARCHITECTURE.md` §1d)
and extended:

| type | idx 8… | fields |
|---|---|---|
| LAND / SPELL / ACTIVATE | 8–15 | mana left after (÷ 6) · targets legal now (÷ 4) · instant-speed · sorcery-speed · flash · goes on stack above N objects (÷ 4) · X chosen (÷ 6) · reserved |
| TARGET | 8–15 | is player · is me · life if player (÷ 20) · is creature · power (÷ 6) · toughness (÷ 6) · mine · reserved |
| ATTACK | 8–23 | `CombatMath.AttackOption` as v6: damage dealt · their kills · my losses · lethal · attackers used · opp life after · bodies retained · power retained · toughness retained · crack-back · my life after · 5 reserved |
| BLOCK | 8–23 | `CombatMath.Outcome` as v6: damage taken · attackers killed · value killed · blockers lost · value lost · defender dies · blockers used · life after · 8 reserved |
| PASS / OTHER | 8–15 | reserved (0); the pass afterstate is **deferred** (design §6) |
| all | 24–39 | reserved (0) |

The 68-column card table and the unknown flag of v6's candidate row are
**not** repeated here: identity reaches the candidate through
`v7_cand_refers`.

`v7_cand_refers[k]` is the list of token indices the candidate acts on
(design: the `refers_to` edge): LAND / SPELL / ACTIVATE → the card or
permanent (and its chosen targets once known); TARGET → the target; ATTACK
→ every attacker in the subset; BLOCK → every blocker and the attacker
it is assigned to; PASS → empty. Gate 3c: coverage = 100 % of non-PASS
candidates.

### 2g. Opponent tokens (§8; emitted from 3d, optional until then)

`v7_opp_hand[j]` — 8 floats per slot in the opponent's hand:

| idx | field | norm |
|---|---|---|
| 0–3 | origin one-hot: opening hand · drawn · returned from a public zone · tutored/other | |
| 4 | age in turns | ÷ 10 |
| 5 | identity known (then `v7_opp_hand_name[j]` is the name, else null) | 0/1 |
| 6 | seen face-up at some point (reveal / look-at) | 0/1 |
| 7 | reserved | |

`v7_opp_deck[j]` — 6 floats per distinct card remaining in the
opponent's deck (open decklist minus every card seen), name in
`v7_opp_deck_name[j]`: count remaining (÷ 4) · fraction of their library
(raw count ÷ library size) · **castable with their open mana now** (0/1)
· mana value (÷ 6) · is instant-speed · reserved.

`v7_opp_actions[j]` — 8 floats per recent opponent decision (newest
first, ≤ `v7_oamax`): type one-hot (cast · activate · attack · block ·
declined to block · passed with mana up · other) (7) · consult age (÷
20); `v7_opp_action_refers[j]` = token indices of the entities involved.

**Leak gate:** the emitter of every `v7_opp_*` field and of every
`v7_ent` row in the opponent's hidden zones is subject to
`rl/probes/leak.py`: policy-path emission must be invariant to the true
hidden cards (design §8; gate 3d).

### 2h. Counters `v7_ctr`

`entityTrunc` (rows dropped by `v7_emax`), `unknownId` (names the engine
could not map, only when it emits ids). The server adds its own
`unresolvedName` per consult in its stats.

## 3. Reply, end, stats — unchanged from v6

`{"a": k}` with `0 ≤ k < len(v7_cand)`; `{"t":"end","r":±1.0}`; `stats`.

## 4. Privileged channel `oe` — unchanged semantics

Critic-only rows as v6 (`-Drl.oracle`). v7 adds nothing to `oe` in 3a–3c;
3d may append the **true** opponent hand as rows under `v7_oe_hand`
(names) for the belief module's labels (design §8a), critic/belief path
only, never read by the policy.

## 5. Decklists at hello (server-side deck context)

The engine adds to the hello, when it knows them:
`"v7_decks":{"me":[["Lightning Bolt",4],…],"opp":[…]|null}`. The server
runs `deck_ctx_v1` once per game per side (`c'_i`, `D`); `opp` is null
when the list is closed (design decision 3: open lists in v1, so it is
present in every v1 run).

## 6. Validation (`rl/wire_validate.py`)

Structural: JSON Schema (`rl/fixtures/v7/schema.json`, generated by the
validator from this file's tables) on hello and consult. Semantic, per
consult: array-length agreement; every float finite; every index in
`v7_edges` and `*_refers` inside the token index space; edge types <
`v7_rtypes`; candidate types < `v7_ctypes`; one-hots sum to 1 where the
tables say one-hot; `refers` non-empty for every non-PASS candidate; a
reply index within range. A failing consult is reported with the key
and position of the first violation.

## 7. What a consumer must not assume

- Entity order beyond the stated bands (padding/masking is the server's
  job; pooling is forbidden by design).
- That `v7_ent_id` is present (it is optional).
- That `v7_opp_*` keys are present before 3d.
- Any field marked reserved: read as 0, never as meaning.
