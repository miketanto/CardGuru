# CardGuru mechanical-search query DSL

Queries are JSON objects evaluated against each card face's ability graph (nodes = abilities,
effects, SVar definitions, keywords; edges = the Forge DSL's explicit chain pointers such as
`Execute$`, `SubAbility$`, `StaticAbilities$`, `Chapter`, `AddTrigger`). Every hit returns
*evidence* — the matching nodes or paths — so results are explainable.

## Running queries

```bash
# one-time dataset build (record the Forge commit you parsed)
python -m cardguru build --cardsfolder <forge>/forge-gui/res/cardsfolder \
    --canonical <index.json> --pin <forge-commit> --out data/dataset.jsonl.gz

python -m cardguru search queries/q1_combat_damage_token.json --explain
python -m cardguru show "Ragavan, Nimble Pilferer"
python -m cardguru stats
```

A query file is either the query object itself or `{"description": ..., "query": {...}}`.

## Operators

| Form | Meaning |
|---|---|
| `{"all": [Q, …]}` | every subquery matches (evidence concatenated) |
| `{"any": [Q, …]}` | at least one matches (first match's evidence) |
| `{"not": Q}` | negation (no evidence) |
| `{"node": NodeSpec}` | some node in the graph matches |
| `{"chain": {"from": NodeSpec, "to": NodeSpec \| [NodeSpec…], "via": [edgeType…]?}}` | a node matching `from` reaches node(s) matching `to` along chain edges. A list of `to` specs must ALL be reachable from the SAME `from` node. `via` restricts edge types; by default all chain edges are followed and incidental `ref:*` edges are excluded |
| `{"keyword": name}` | card has a keyword node with that name |
| `{"card": {field: VP}}` | card-level attributes: `name`, `types`, `manaCost`, `oracle`, `pt` |
| `{"hook": name}` | semantic facet from the hook library (`cardguru.recommend.HOOKS`) — e.g. `makes_tokens`, `sac_outlet`, `gains_life` |
| `{"role": name}` | deckbuilding role (`cardguru.deck.ROLES`) — `card_draw`, `ramp`, `targeted_removal`, `sweepers`. Suffix `:engine` or `:one_shot` to require repeatability, e.g. `card_draw:engine` |

## NodeSpec

All fields optional, AND-ed. `VP` marks fields accepting value predicates.

| Field | Matches |
|---|---|
| `kind` (VP) | `A` spell/activated line, `T` trigger, `S` static, `R` replacement, `K` keyword, `SVar` ability/mode SVar, `SVarCount` Count$ SVar, `SVarValue` other |
| `api` (VP) | effect API name (`Token`, `DealDamage`, `ChangeZone`, …) |
| `apiKind` | `SP` spell, `AB` activated, `DB` sub-ability |
| `mode` (VP) | trigger/static mode (`DamageDone`, `Continuous`, …) |
| `keyword` (VP) | keyword name on `K` nodes |
| `count` (VP) | Count$ expression on `SVarCount` nodes |
| `value` (VP) | raw value string on `SVarValue` nodes |
| `params` | `{ParamName: VP}` — any pipe-parameter of the ability line |

### Why `value` matters: doubling is not a structural difference

Doubling Season and Hardened Scales have **identical graph shape** — both are
`R | Event$ AddCounter` → `ReplaceWith` → `api ReplaceCounter`. The arithmetic
operator exists only in the referenced `SVarValue`:

| Card | `SVarValue.value` |
|---|---|
| Doubling Season | `ReplaceCount$CounterNum/Twice` |
| Hardened Scales | `ReplaceCount$CounterNum/Plus.1` |
| Furnace of Rath | `ReplaceCount$DamageAmount/Twice` |
| Torbran | `ReplaceCount$DamageAmount/Plus.2` |

So "cards that **double** my counters" needs the operator, not just the shape:

```json
{"all": [
  {"node": {"kind": "R", "params": {"Event": "AddCounter"}}},
  {"node": {"kind": "SVar", "api": "ReplaceCounter"}},
  {"node": {"kind": "SVarValue", "value": {"contains": "/Twice"}}}
]}
```

Without `value` this is only reachable via a `card.oracle` text regex — which
would mean text search doing the discriminating work in a structural index.

## Value predicates (VP)

`"exact string"` · `{"contains": s}` · `{"icontains": s}` · `{"regex": r}` ·
`{"any": [VP, …]}` · `true` (parameter merely exists)

## Example: impulse exile

"One ability chain both exiles from the library and grants a may-play effect":

```json
{"chain": {
    "from": {"kind": {"any": ["A", "T", "S", "R"]}},
    "to": [
      {"api": {"any": ["Dig", "DigUntil", "Mill"]},
       "params": {"DestinationZone": {"contains": "Exile"}}},
      {"mode": "Continuous", "params": {"MayPlay": "True"}}
    ]}}
```

The multi-target `to` is what oracle-text search fundamentally cannot express: both effects
must hang off the *same* ability, not merely appear somewhere on the card.

## Vocabulary

Valid `api` / `mode` / `keyword` / param names are the mined ontology —
`research/data/ontology.json` with frequency counts. An NL→DSL compiler must emit only tokens
from that vocabulary; anything else is rejected before execution.

## Performance notes

The index builds postings over `api:`, `mode:`, `kw:`, `kind:`, `pk:` tokens and prunes
candidates from the query's exact-match fields before full evaluation (conservative: branches
it can't index scan everything). Whole-pool scans are ~1–2 s in pure Python; pruned queries
are milliseconds. Load once and reuse the `SearchIndex` for a server.
